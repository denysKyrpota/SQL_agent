"""
LLM Service for OpenAI integration and SQL generation.

Implements a two-stage SQL generation process:
1. Schema Optimization: Select relevant tables from 279 tables
2. SQL Generation: Generate SQL using filtered schema and KB examples
"""

import asyncio
import logging
import re
from typing import Any

from openai import AsyncOpenAI, AsyncAzureOpenAI, RateLimitError, APIError, APIConnectionError

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
        """Initialize the LLM service with OpenAI or Azure OpenAI client."""
        self.is_azure = settings.use_azure_openai
        self._azure_supports_temperature = True  # Will be set to False if we detect it's not supported

        if self.is_azure:
            # Azure OpenAI configuration
            if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
                logger.warning("Azure OpenAI endpoint or API key not configured")
                self.client = None
            else:
                self.client = AsyncAzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version
                )
                self.model = settings.azure_openai_deployment
                self.embedding_model = settings.azure_openai_embedding_deployment or settings.azure_openai_deployment
                logger.info(f"LLM Service initialized with Azure OpenAI deployment: {self.model}")
        else:
            # Standard OpenAI configuration
            self.model = settings.openai_model
            self.embedding_model = settings.openai_embedding_model
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured")
                self.client = None
            else:
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info(f"LLM Service initialized with OpenAI model: {self.model}")

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
                "content": "You are a helpful database expert. Return only table names, comma-separated, no explanations."
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

        # Call OpenAI with retry logic - try up to 3 times if we get empty/invalid response
        response_text = ""
        selected_tables = []
        last_error = None

        for attempt in range(3):
            try:
                response_text = await self._call_openai_with_retry(
                    messages=messages,
                    max_tokens=500,  # Table names only, should be short
                    temperature=0.0  # Deterministic selection
                )

                if not response_text or not response_text.strip():
                    logger.warning(f"LLM returned empty response for table selection (attempt {attempt + 1}/3)")
                    if attempt < 2:
                        await asyncio.sleep(1.0)  # Brief pause before retry
                    continue

                # Parse table names from response
                # Log the full response for debugging (up to 1000 chars)
                logger.info(f"Stage 1 raw LLM response (attempt {attempt + 1}): {response_text[:1000]}")
                selected_tables = self._parse_table_names(response_text, table_names)

                if selected_tables:
                    break  # Success!

            except ValueError as e:
                last_error = e
                logger.warning(f"Table selection parsing failed (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(1.0)  # Brief pause before retry
                continue

        # Handle failure after all retries
        if not selected_tables:
            error_detail = f" Last error: {last_error}" if last_error else ""
            logger.error(f"Failed to select tables after 3 attempts for question: {question}.{error_detail}")
            raise ValueError(
                f"Could not identify relevant tables for your question. "
                f"This database contains logistics/transportation data (activities, drivers, vehicles, customers, contracts). "
                f"Try rephrasing with domain-specific terms."
            )

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

        prompt = f"""Given these database tables for a logistics company:
{tables_list}

Question: "{question}"{context_note}

Select up to {max_tables} relevant tables. Common mappings:
- activities/tasks → activity_activity
- trucks/vehicles → asset_truck, asset_assignment
- drivers → asset_driver
- customers → customer_customer

Return ONLY comma-separated table names from the list above, nothing else.
Example: activity_activity, asset_truck, asset_assignment"""

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

        # Build prompt for SQL generation
        prompt = self._build_sql_generation_prompt(
            question, schema_text, examples, conversation_history
        )

        # Build messages with conversation history
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a PostgreSQL expert. Generate SELECT queries based on the schema provided. "
                    "Return only the SQL query, no explanations or markdown."
                )
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

        # Call OpenAI with retry logic using few-shot examples to reinforce SELECT-only behavior
        response_text = await self._call_openai_with_retry(
            messages=messages,
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature
        )

        # Log raw response for debugging
        logger.info(f"Stage 2 raw LLM response: {response_text[:1500] if response_text else 'EMPTY'}")

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

        prompt = f"""DATABASE SCHEMA:
{schema_text}
{examples_section}
QUESTION: "{question}"{context_note}

Write a PostgreSQL SELECT query to answer this question.
Use proper JOINs based on foreign keys in the schema.
Return only the SQL, no explanations."""

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
        Automatically handles differences between Azure and standard OpenAI.

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
                    f"Calling {'Azure ' if self.is_azure else ''}OpenAI API (attempt {attempt + 1}/{max_retries})"
                )

                # Build API call parameters
                api_params = {
                    "model": self.model,
                    "messages": messages,
                }

                # Handle parameter differences between Azure and standard OpenAI
                if self.is_azure:
                    # Azure OpenAI uses max_completion_tokens for newer API versions
                    api_params["max_completion_tokens"] = max_tokens
                    # Only add temperature if the deployment supports it
                    if self._azure_supports_temperature:
                        api_params["temperature"] = temperature
                else:
                    # Standard OpenAI uses max_tokens
                    api_params["max_tokens"] = max_tokens
                    api_params["temperature"] = temperature

                response = await self.client.chat.completions.create(**api_params)

                response_text = response.choices[0].message.content

                logger.info(
                    f"{'Azure ' if self.is_azure else ''}OpenAI API call successful: {response.usage.total_tokens} tokens used"
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
                error_str = str(e)

                # Check if this is a "temperature not supported" error from Azure
                if self.is_azure and "temperature" in error_str.lower() and "unsupported" in error_str.lower():
                    logger.warning(
                        f"Azure deployment does not support temperature parameter. "
                        f"Disabling temperature and retrying. This may result in less deterministic responses."
                    )
                    self._azure_supports_temperature = False
                    # Immediate retry without temperature (don't count as failed attempt)
                    continue

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

        logger.debug(f"Parsing table names from response: {cleaned[:500]}")

        # Check for refusal patterns that indicate LLM didn't understand
        refusal_patterns = [
            "i cannot", "i can't", "i don't know", "i'm not sure",
            "unable to", "no tables", "not possible", "cannot determine",
            "insufficient information", "need more context"
        ]
        if any(pattern in cleaned.lower() for pattern in refusal_patterns):
            logger.warning(f"LLM appears to have refused or been uncertain: {cleaned[:200]}")
            raise ValueError(f"LLM could not determine tables: {cleaned[:100]}")

        # Remove common prefixes/suffixes and markdown formatting
        for remove_str in ["```", "sql", "SELECT", "FROM", "*", "-", "•", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."]:
            cleaned = cleaned.replace(remove_str, " ")

        # Remove numbered list patterns like "1) " or "1. "
        cleaned = re.sub(r'\d+[\.\)]\s*', ' ', cleaned)

        # Build a map of valid table names (case-insensitive)
        valid_table_names_lower = {name.lower(): name for name in valid_table_names}

        # Method 1: Try to find valid table names directly in the response using regex
        # This handles cases where table names are mixed with other text
        validated = []
        for valid_name_lower, valid_name in valid_table_names_lower.items():
            # Look for the table name as a whole word
            pattern = rf'\b{re.escape(valid_name_lower)}\b'
            if re.search(pattern, cleaned.lower()):
                if valid_name not in validated:
                    validated.append(valid_name)
                    logger.debug(f"Found valid table via regex: {valid_name}")

        # If we found tables via regex, return them
        if validated:
            logger.info(f"Parsed {len(validated)} table names via regex matching")
            return validated

        # Method 2: Traditional delimiter-based parsing as fallback
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
        for name in table_names:
            name_lower = name.lower().strip()
            # Check if this candidate matches a valid table name exactly
            if name_lower in valid_table_names_lower:
                if valid_table_names_lower[name_lower] not in validated:
                    validated.append(valid_table_names_lower[name_lower])
            else:
                # Also check if any valid table name is contained in this candidate
                # This handles cases like "i recommend: users" -> "users"
                for valid_name_lower, valid_name in valid_table_names_lower.items():
                    if valid_name_lower in name_lower.split():
                        if valid_name not in validated:
                            validated.append(valid_name)
                        break
                else:
                    if name and len(name) > 2:  # Only log for non-trivial strings
                        logger.debug(f"LLM suggested invalid table name: '{name}'")

        if not validated:
            logger.error(
                f"No valid table names found in response.\n"
                f"Raw response: {response_text[:200]}\n"
                f"Parsed candidates: {table_names}\n"
                f"Available tables sample: {list(valid_table_names_lower.keys())[:10]}"
            )
            raise ValueError(
                f"LLM did not return valid table names. Response was: '{response_text[:100]}...'. "
                f"Please try rephrasing your question."
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

        logger.debug(f"Raw LLM response for SQL extraction: {cleaned[:500]}")

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

        # If still doesn't start with SELECT/WITH, try to find it in the response
        cleaned_upper = cleaned.upper()
        if not (cleaned_upper.startswith("SELECT") or cleaned_upper.startswith("WITH")):
            # Try to find SELECT or WITH statement in the response
            # Look for SELECT or WITH at the start of a line
            select_match = re.search(r'(?:^|\n)(SELECT\s)', cleaned, re.IGNORECASE)
            with_match = re.search(r'(?:^|\n)(WITH\s)', cleaned, re.IGNORECASE)

            if select_match:
                start_pos = select_match.start(1)
                cleaned = cleaned[start_pos:].strip()
                logger.debug(f"Found SELECT at position {start_pos}, extracted SQL")
            elif with_match:
                start_pos = with_match.start(1)
                cleaned = cleaned[start_pos:].strip()
                logger.debug(f"Found WITH at position {start_pos}, extracted SQL")

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
        Works with both standard OpenAI and Azure OpenAI.

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
                model=self.embedding_model,
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
