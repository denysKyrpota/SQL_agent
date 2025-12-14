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
        self.model = settings.openai_model
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info(f"LLM Service initialized with model: {self.model}")

    async def select_relevant_tables(
        self,
        table_names: list[str],
        question: str,
        max_tables: int = 10,
        conversation_history: list[dict[str, str]] | None = None
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
            conversation_history: Optional conversation history for context

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
        prompt = self._build_table_selection_prompt(
            table_names, question, max_tables, conversation_history
        )

        # Build messages array with conversation history
        messages = [
            {
                "role": "system",
                "content": "You are a database expert. Your task is to select only the most relevant database tables needed to answer a given question."
            }
        ]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user prompt
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Call OpenAI with retry logic
        response_text = await self._call_openai_with_retry(
            messages=messages,
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
        max_tables: int,
        conversation_history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Build prompt for Stage 1: Table selection.

        Args:
            table_names: All available table names
            question: User's question
            max_tables: Maximum tables to select
            conversation_history: Optional conversation history for context

        Returns:
            str: Formatted prompt
        """
        # Format table names as a readable list
        tables_list = "\n".join(f"- {name}" for name in sorted(table_names))

        context_note = ""
        if conversation_history:
            context_note = "\nNote: Consider the conversation history above when selecting tables."

        prompt = f"""You are analyzing a PostgreSQL database to answer a question.

DATABASE TABLES ({len(table_names)} total):
{tables_list}

USER QUESTION:
"{question}"{context_note}

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
        examples: list[str],
        conversation_history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Stage 2: Generate SQL query using filtered schema and examples.

        Takes the user's question, a focused schema (from Stage 1), and
        similar examples from the knowledge base, then generates a SQL query.

        Args:
            question: User's natural language question
            schema_text: Formatted schema for selected tables only
            examples: List of similar SQL examples from knowledge base
            conversation_history: Optional conversation history for context

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

        # Log a warning if the question contains potentially confusing keywords
        question_upper = question.upper()
        confusing_keywords = ["DELETE", "INSERT", "UPDATE", "CREATE", "DROP", "ALTER", "TRUNCATE"]
        found_keywords = [kw for kw in confusing_keywords if kw in question_upper]
        if found_keywords:
            logger.warning(
                f"Question contains potentially confusing keywords: {found_keywords}. "
                f"These will be interpreted as column names/filters, not SQL commands."
            )

        # Build prompt for SQL generation
        prompt = self._build_sql_generation_prompt(
            question, schema_text, examples, conversation_history
        )

        # Build messages with conversation history
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert PostgreSQL developer who generates ONLY read-only SELECT queries. "
                    "ABSOLUTE RULE: Your response MUST start with 'SELECT' or 'WITH' (for CTEs). "
                    "FORBIDDEN WORDS IN YOUR RESPONSE: INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE. "
                    "These commands are COMPLETELY PROHIBITED - do not use them anywhere in your SQL. "
                    "\n\n"
                    "CRITICAL: When you see words like 'deleted', 'created', 'updated' in questions, these refer to:\n"
                    "- 'deleted' = a boolean column (deleted = true/false) or a timestamp (deleted_at)\n"
                    "- 'created' = a timestamp column (created_at) showing when records were created\n"
                    "- 'updated' = a timestamp column (updated_at) showing when records were updated\n"
                    "- 'deactivated' = a timestamp column (deactivated_at) or status field\n"
                    "\n"
                    "You are working with a READ-ONLY database. You can ONLY retrieve data, never modify it. "
                    "Every query must be a SELECT statement that reads existing data."
                )
            },
            {
                "role": "user",
                "content": "Show me all created customers"
            },
            {
                "role": "assistant",
                "content": "SELECT * FROM customers WHERE created_at IS NOT NULL;"
            },
            {
                "role": "user",
                "content": "Get deleted records from activities"
            },
            {
                "role": "assistant",
                "content": "SELECT * FROM activities WHERE deleted = true;"
            },
            {
                "role": "user",
                "content": "Deactivated created customers this month"
            },
            {
                "role": "assistant",
                "content": "SELECT * FROM customers WHERE deactivated_at IS NOT NULL AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE);"
            },
        ]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user prompt
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Call OpenAI with retry logic using few-shot examples to reinforce SELECT-only behavior
        response_text = await self._call_openai_with_retry(
            messages=messages,
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
        examples: list[str],
        conversation_history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Build prompt for Stage 2: SQL generation.

        Args:
            question: User's question
            schema_text: Filtered schema formatted for LLM
            examples: Knowledge base examples
            conversation_history: Optional conversation history for context

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

        context_note = ""
        if conversation_history:
            context_note = "\nNote: Consider the conversation history above when generating the SQL query. If the user is asking for modifications or refinements, build upon previous queries."

        prompt = f"""⚠️ MANDATORY INSTRUCTION: Generate ONLY a SELECT query. Do NOT use DELETE, INSERT, UPDATE, CREATE, DROP, ALTER, or TRUNCATE.

DATABASE SCHEMA:
{schema_text}
{examples_section}
USER QUESTION:
"{question}"{context_note}

⚠️ CRITICAL: Words like "deleted", "created", "updated", "deactivated" in questions refer to COLUMN NAMES, NOT SQL commands!

CORRECT INTERPRETATIONS (follow these patterns):
❌ WRONG: "show deleted records" → DELETE FROM records...
✅ CORRECT: "show deleted records" → SELECT * FROM records WHERE deleted = true;

❌ WRONG: "created customers" → CREATE TABLE customers...
✅ CORRECT: "created customers" → SELECT * FROM customers WHERE created_at IS NOT NULL;

❌ WRONG: "deactivated users" → DROP TABLE users...
✅ CORRECT: "deactivated users" → SELECT * FROM users WHERE deactivated_at IS NOT NULL;

❌ WRONG: "updated orders" → UPDATE orders...
✅ CORRECT: "updated orders" → SELECT * FROM orders WHERE updated_at IS NOT NULL;

CRITICAL REQUIREMENTS - READ CAREFULLY:
1. Generate ONLY a SELECT query - this is mandatory and non-negotiable
2. NEVER generate CREATE, INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any other data modification commands
3. Even if the question mentions words like "create", "add", "insert", "update", or "delete", you must interpret this as a request to QUERY existing data, not modify it
4. Use only tables and columns from the schema above
5. Follow best practices (proper JOINs, WHERE clauses, etc.)
6. Use descriptive column aliases where helpful
7. Return ONLY the SQL query, no explanations
8. Format the query for readability (line breaks and indentation)

IMPORTANT CLARIFICATIONS:
- "Show created customers" means SELECT customers WHERE created_at...
- "Get deleted activities" means SELECT activities WHERE deleted = true...
- "Find updated records" means SELECT records WHERE updated_at...
- You are ONLY querying a read-only database - you cannot modify anything

RESPONSE FORMAT:
Return ONLY the SQL query, starting with SELECT (or WITH for CTEs) and ending with semicolon.
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

        # Split by common delimiters (prioritize comma and newline over space)
        table_names = []
        for delimiter in [",", "\n", ";"]:
            if delimiter in cleaned:
                parts = [p.strip().lower() for p in cleaned.split(delimiter)]
                table_names = [p for p in parts if p and not p.isspace()]
                break

        # If no delimiter found, try splitting by spaces (but filter more strictly)
        if not table_names:
            parts = [p.strip().lower() for p in cleaned.split()]
            table_names = [p for p in parts if p and not p.isspace()]

        # Validate against actual table names
        valid_table_names_lower = {name.lower(): name for name in valid_table_names}
        validated = []

        for name in table_names:
            name_lower = name.lower().strip()
            # Check if this candidate matches a valid table name exactly
            if name_lower in valid_table_names_lower:
                validated.append(valid_table_names_lower[name_lower])
            else:
                # Also check if any valid table name is contained in this candidate
                # This handles cases like "i recommend: users" -> "users"
                for valid_name_lower, valid_name in valid_table_names_lower.items():
                    if valid_name_lower in name_lower.split():
                        validated.append(valid_name)
                        break
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

        # Basic validation - allow SELECT and WITH (for CTEs)
        cleaned_upper = cleaned.upper()
        if not (cleaned_upper.startswith("SELECT") or cleaned_upper.startswith("WITH")):
            logger.error(f"Response doesn't start with SELECT or WITH: {cleaned[:100]}")
            raise ValueError(
                "Generated query must be a SELECT statement or use WITH for CTEs. "
                "This system only supports read-only queries. Please rephrase your question to query existing data."
            )

        # Check for dangerous commands - use word boundary matching to avoid false positives
        # with column names like "created_at" or table names containing these words
        import re
        dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
        for keyword in dangerous_keywords:
            # Match as a standalone word (not part of column/table names)
            # Pattern: keyword followed by whitespace or common SQL tokens
            pattern = rf'\b{keyword}\s+(TABLE|INTO|FROM|SET|DATABASE|SCHEMA|INDEX|VIEW|TRIGGER|FUNCTION|PROCEDURE|\()'
            if re.search(pattern, cleaned_upper):
                logger.error(f"Response contains dangerous keyword '{keyword}' in DDL/DML context")
                raise ValueError(
                    f"The AI attempted to generate a {keyword} operation, which is not allowed. "
                    f"This system only supports SELECT queries to read data, not modify it. "
                    f"Please rephrase your question to ask about existing data (e.g., 'Show me customers that were created...' instead of 'Create customers...')."
                )
            # Also check for the keyword at the start of a statement
            elif cleaned_upper.strip().startswith(keyword + " ") or cleaned_upper.strip().startswith(keyword + "\n"):
                logger.error(f"Response starts with dangerous keyword '{keyword}'")
                raise ValueError(
                    f"The AI attempted to generate a {keyword} operation, which is not allowed. "
                    f"This system only supports SELECT queries to read data, not modify it. "
                    f"Please rephrase your question to ask about existing data (e.g., 'Show me customers that were created...' instead of 'Create customers...')."
                )

        return cleaned

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text using OpenAI embeddings API.

        Used for RAG-based similarity search in knowledge base.

        Args:
            text: Text to generate embedding for (SQL query or question)

        Returns:
            list[float]: Embedding vector (1536 dimensions for text-embedding-3-small)

        Raises:
            LLMServiceUnavailableError: If OpenAI API fails after retries

        Example:
            >>> service = LLMService()
            >>> embedding = await service.generate_embedding("SELECT * FROM users")
            >>> len(embedding)
            1536
        """
        if not self.client:
            raise LLMServiceUnavailableError("OpenAI API key not configured")

        logger.debug(f"Generating embedding for text ({len(text)} characters)")

        try:
            response = await self.client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text
            )

            embedding = response.data[0].embedding

            logger.debug(
                f"Generated embedding: {len(embedding)} dimensions, "
                f"{response.usage.total_tokens} tokens used"
            )

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise LLMServiceUnavailableError(
                f"Failed to generate embedding: {e}"
            ) from e


class LLMServiceUnavailableError(Exception):
    """Raised when OpenAI API is unavailable after retries."""
    pass


class SQLGenerationError(Exception):
    """Raised when SQL generation fails (invalid response, etc.)."""
    pass
