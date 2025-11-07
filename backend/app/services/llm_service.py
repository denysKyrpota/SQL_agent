"""
LLM Service for OpenAI integration and SQL generation.

Implements a two-stage SQL generation process:
1. Schema Optimization: Select relevant tables from 279 tables
2. SQL Generation: Generate SQL using filtered schema and KB examples
"""

import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI, RateLimitError, APIError, APIConnectionError

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """
    Service for interacting with OpenAI's GPT models to generate SQL queries.

    Uses a two-stage approach to handle large schemas efficiently:
    - Stage 1: Table selection (reduce 279 tables to ~5-10 relevant ones)
    - Stage 2: SQL generation (focused context with examples)
    """

    def __init__(self):
        """Initialize the LLM service with OpenAI client."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info(f"LLM Service initialized with model: {settings.openai_model}")

    async def select_relevant_tables(
        self,
        table_names: list[str],
        question: str,
        max_tables: int = 10
    ) -> list[str]:
        """
        Stage 1: Select relevant tables from full table list.

        Uses LLM to analyze the user's question and select only the tables
        that are likely needed to answer it. This dramatically reduces the
        context size for Stage 2.

        Args:
            table_names: List of all available table names (279 tables)
            question: User's natural language question
            max_tables: Maximum number of tables to select (default: 10)

        Returns:
            list[str]: Selected table names (typically 5-10 tables)

        Raises:
            LLMServiceUnavailableError: If OpenAI API fails after retries
            ValueError: If response format is invalid

        Example:
            >>> service = LLMService()
            >>> tables = await service.select_relevant_tables(
            ...     table_names=["users", "orders", "products", "activities", ...],
            ...     question="Show me activities finished today with driver names"
            ... )
            >>> print(tables)
            ['activity_activity', 'auth_user', 'asset_assignment']
        """
        if not self.client:
            raise LLMServiceUnavailableError("OpenAI API key not configured")

        logger.info(
            f"Stage 1: Selecting relevant tables from {len(table_names)} total tables"
        )

        # Build prompt for table selection
        prompt = self._build_table_selection_prompt(table_names, question, max_tables)

        # Call OpenAI with retry logic
        response_text = await self._call_openai_with_retry(
            messages=[
                {
                    "role": "system",
                    "content": "You are a database expert. Your task is to select only the most relevant database tables needed to answer a given question."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,  # Table names only, should be short
            temperature=0.0  # Deterministic selection
        )

        # Parse table names from response
        selected_tables = self._parse_table_names(response_text, table_names)

        logger.info(
            f"Stage 1 complete: Selected {len(selected_tables)} tables: {selected_tables}"
        )

        return selected_tables

    def _build_table_selection_prompt(
        self,
        table_names: list[str],
        question: str,
        max_tables: int
    ) -> str:
        """
        Build prompt for Stage 1: Table selection.

        Args:
            table_names: All available table names
            question: User's question
            max_tables: Maximum tables to select

        Returns:
            str: Formatted prompt
        """
        # Format table names as a readable list
        tables_list = "\n".join(f"- {name}" for name in sorted(table_names))

        prompt = f"""You are analyzing a PostgreSQL database to answer a question.

DATABASE TABLES ({len(table_names)} total):
{tables_list}

USER QUESTION:
"{question}"

TASK:
Select the {max_tables} most relevant tables needed to answer this question.
Consider:
1. Tables directly mentioned or implied by the question
2. Junction tables that connect the main tables
3. Tables containing foreign keys to the main entities

RESPONSE FORMAT:
Return ONLY a comma-separated list of table names, nothing else.
Example: "activity_activity, auth_user, asset_assignment"

Your response:"""

        return prompt

    async def generate_sql(
        self,
        question: str,
        schema_text: str,
        examples: list[str]
    ) -> str:
        """
        Stage 2: Generate SQL query using filtered schema and examples.

        Takes the user's question, a focused schema (from Stage 1), and
        similar examples from the knowledge base, then generates a SQL query.

        Args:
            question: User's natural language question
            schema_text: Formatted schema for selected tables only
            examples: List of similar SQL examples from knowledge base

        Returns:
            str: Generated PostgreSQL SELECT query

        Raises:
            LLMServiceUnavailableError: If OpenAI API fails after retries
            ValueError: If response doesn't contain valid SQL

        Example:
            >>> sql = await service.generate_sql(
            ...     question="Show activities finished today",
            ...     schema_text="Table: activity_activity\\n  Columns: ...",
            ...     examples=["SELECT * FROM activity_activity WHERE ..."]
            ... )
            >>> print(sql)
            'SELECT id, name FROM activity_activity WHERE DATE(finished_datetime) = CURRENT_DATE'
        """
        if not self.client:
            raise LLMServiceUnavailableError("OpenAI API key not configured")

        logger.info("Stage 2: Generating SQL query")

        # Build prompt for SQL generation
        prompt = self._build_sql_generation_prompt(question, schema_text, examples)

        # Call OpenAI with retry logic
        response_text = await self._call_openai_with_retry(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert PostgreSQL developer. Generate correct, efficient SQL queries based on the provided schema and examples."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature
        )

        # Extract SQL from response
        sql = self._extract_sql_from_response(response_text)

        logger.info(f"Stage 2 complete: Generated SQL ({len(sql)} characters)")
        logger.debug(f"Generated SQL: {sql}")

        return sql

    def _build_sql_generation_prompt(
        self,
        question: str,
        schema_text: str,
        examples: list[str]
    ) -> str:
        """
        Build prompt for Stage 2: SQL generation.

        Args:
            question: User's question
            schema_text: Filtered schema formatted for LLM
            examples: Knowledge base examples

        Returns:
            str: Formatted prompt
        """
        # Format examples
        examples_text = ""
        if examples:
            examples_text = "\n\n".join(
                f"Example {i+1}:\n{example}"
                for i, example in enumerate(examples[:3])  # Limit to 3 examples
            )
            examples_section = f"""
SIMILAR EXAMPLES FROM KNOWLEDGE BASE:
{examples_text}
"""
        else:
            examples_section = ""

        prompt = f"""You are generating a PostgreSQL SELECT query to answer a user's question.

DATABASE SCHEMA:
{schema_text}
{examples_section}
USER QUESTION:
"{question}"

REQUIREMENTS:
1. Generate a valid PostgreSQL SELECT query
2. Use only tables and columns from the schema above
3. Follow best practices (proper JOINs, WHERE clauses, etc.)
4. Use descriptive column aliases where helpful
5. Return ONLY the SQL query, no explanations
6. Do NOT use INSERT, UPDATE, DELETE, DROP, or other modification commands
7. Format the query for readability (line breaks and indentation)

RESPONSE FORMAT:
Return ONLY the SQL query, starting with SELECT and ending with semicolon.
Do not include markdown code blocks (```sql) or any explanation.

Your SQL query:"""

        return prompt

    async def _call_openai_with_retry(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> str:
        """
        Call OpenAI API with exponential backoff retry logic.

        Handles transient errors like rate limits and network issues.

        Args:
            messages: Chat messages for the API
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0.0 = deterministic)
            max_retries: Maximum number of retry attempts

        Returns:
            str: Response text from OpenAI

        Raises:
            LLMServiceUnavailableError: If all retries fail
        """
        if not self.client:
            raise LLMServiceUnavailableError("OpenAI client not initialized")

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Calling OpenAI API (attempt {attempt + 1}/{max_retries})"
                )

                response = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                response_text = response.choices[0].message.content

                logger.info(
                    f"OpenAI API call successful: {response.usage.total_tokens} tokens used"
                )

                return response_text

            except RateLimitError as e:
                # Rate limit hit - use exponential backoff
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}). "
                    f"Waiting {wait_time}s before retry. Error: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise LLMServiceUnavailableError(
                        "Rate limit exceeded after maximum retries"
                    ) from e

            except APIConnectionError as e:
                # Network error - retry
                wait_time = 2 ** attempt
                logger.warning(
                    f"API connection error (attempt {attempt + 1}). "
                    f"Waiting {wait_time}s before retry. Error: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise LLMServiceUnavailableError(
                        "API connection failed after maximum retries"
                    ) from e

            except APIError as e:
                # General API error - retry once
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise LLMServiceUnavailableError(
                        f"OpenAI API error: {e}"
                    ) from e

            except Exception as e:
                # Unexpected error - don't retry
                logger.error(f"Unexpected error calling OpenAI: {e}", exc_info=True)
                raise LLMServiceUnavailableError(
                    f"Unexpected error: {e}"
                ) from e

        # Should never reach here
        raise LLMServiceUnavailableError("Maximum retries exceeded")

    def _parse_table_names(
        self,
        response_text: str,
        valid_table_names: list[str]
    ) -> list[str]:
        """
        Parse table names from LLM response.

        Handles various response formats and validates against actual tables.

        Args:
            response_text: Raw response from LLM
            valid_table_names: List of valid table names for validation

        Returns:
            list[str]: Parsed and validated table names

        Raises:
            ValueError: If no valid table names found
        """
        # Clean response
        cleaned = response_text.strip()

        # Remove common prefixes/suffixes
        for remove_str in ["```", "sql", "SELECT", "FROM"]:
            cleaned = cleaned.replace(remove_str, "")

        # Split by common delimiters
        table_names = []
        for delimiter in [",", "\n", ";", " "]:
            if delimiter in cleaned:
                parts = [p.strip().lower() for p in cleaned.split(delimiter)]
                table_names = [p for p in parts if p and not p.isspace()]
                break

        if not table_names:
            # Try treating whole response as single table name
            table_names = [cleaned.lower()]

        # Validate against actual table names
        valid_table_names_lower = {name.lower(): name for name in valid_table_names}
        validated = []

        for name in table_names:
            name_lower = name.lower().strip()
            if name_lower in valid_table_names_lower:
                validated.append(valid_table_names_lower[name_lower])
            else:
                logger.warning(f"LLM suggested invalid table name: '{name}'")

        if not validated:
            logger.error(f"No valid table names found in response: {response_text}")
            raise ValueError(
                "LLM did not return valid table names. Please try rephrasing your question."
            )

        # Remove duplicates while preserving order
        seen = set()
        unique_validated = []
        for name in validated:
            if name not in seen:
                seen.add(name)
                unique_validated.append(name)

        return unique_validated

    def _extract_sql_from_response(self, response_text: str) -> str:
        """
        Extract SQL query from LLM response.

        Handles various response formats (plain SQL, markdown code blocks, etc.)

        Args:
            response_text: Raw response from LLM

        Returns:
            str: Extracted SQL query

        Raises:
            ValueError: If no valid SQL found
        """
        cleaned = response_text.strip()

        # Remove markdown code blocks
        if "```sql" in cleaned.lower():
            # Extract content between ```sql and ```
            parts = cleaned.split("```")
            for part in parts:
                if part.strip().lower().startswith("sql"):
                    cleaned = part[3:].strip()  # Remove 'sql' prefix
                    break
        elif "```" in cleaned:
            # Generic code block
            parts = cleaned.split("```")
            if len(parts) >= 2:
                cleaned = parts[1].strip()

        # Ensure ends with semicolon
        if not cleaned.endswith(";"):
            cleaned += ";"

        # Basic validation
        if not cleaned.upper().startswith("SELECT"):
            logger.error(f"Response doesn't start with SELECT: {cleaned[:100]}")
            raise ValueError(
                "Generated query is not a SELECT statement. Please try again."
            )

        # Check for dangerous commands
        dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
        cleaned_upper = cleaned.upper()
        for keyword in dangerous_keywords:
            if keyword in cleaned_upper:
                logger.error(f"Response contains dangerous keyword '{keyword}'")
                raise ValueError(
                    f"Generated query contains forbidden operation: {keyword}"
                )

        return cleaned


class LLMServiceUnavailableError(Exception):
    """Raised when OpenAI API is unavailable after retries."""
    pass


class SQLGenerationError(Exception):
    """Raised when SQL generation fails (invalid response, etc.)."""
    pass
