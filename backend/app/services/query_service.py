"""
Service layer for query attempt creation and SQL generation.

This service handles the two-stage SQL generation process:
1. Schema optimization: Select relevant tables from PostgreSQL schema
2. SQL generation: Generate SQL using selected tables and knowledge base examples
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.schemas.queries import CreateQueryRequest, QueryAttemptResponse
from backend.app.schemas.common import QueryStatus

logger = logging.getLogger(__name__)


class QueryAttempt:
    """
    Temporary ORM model representation for query_attempts table.
    TODO: Replace with proper SQLAlchemy model when models are created.
    """

    def __init__(
        self,
        id: int,
        user_id: int,
        natural_language_query: str,
        generated_sql: str | None,
        status: str,
        created_at: str,
        generated_at: str | None = None,
        generation_ms: int | None = None,
        error_message: str | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.natural_language_query = natural_language_query
        self.generated_sql = generated_sql
        self.status = status
        self.created_at = created_at
        self.generated_at = generated_at
        self.generation_ms = generation_ms
        self.error_message = error_message


class QueryService:
    """Service for managing query attempts and SQL generation workflow."""

    def __init__(self):
        """Initialize the query service."""
        # TODO: Inject dependencies (LLMService, KnowledgeBaseService, SchemaService)
        pass

    async def create_query_attempt(
        self, db: Session, user_id: int, request: CreateQueryRequest
    ) -> QueryAttemptResponse:
        """
        Create a new query attempt and generate SQL.

        This method performs the complete workflow:
        1. Create initial query attempt record with status 'not_executed'
        2. Call two-stage SQL generation process
        3. Update record with generated SQL or error message
        4. Return response

        Args:
            db: Database session
            user_id: ID of the authenticated user
            request: Query creation request with natural language query

        Returns:
            QueryAttemptResponse with query details and generated SQL

        Raises:
            HTTPException: For various error conditions (429 rate limit, 503 service unavailable)
        """
        logger.info(
            f"Creating query attempt for user {user_id}",
            extra={
                "user_id": user_id,
                "query_length": len(request.natural_language_query),
            },
        )

        # Record creation timestamp
        created_at = datetime.utcnow().isoformat() + "Z"

        try:
            # Step 1: Create initial query attempt record
            # TODO: Replace with actual database insert using SQLAlchemy model
            query_attempt = self._create_initial_attempt(
                db=db,
                user_id=user_id,
                natural_language_query=request.natural_language_query,
                created_at=created_at,
            )

            logger.info(
                f"Created initial query attempt {query_attempt.id}",
                extra={"attempt_id": query_attempt.id, "user_id": user_id},
            )

            # Step 2: Generate SQL using two-stage process
            generation_start = datetime.utcnow()

            try:
                generated_sql = await self._generate_sql(
                    natural_language_query=request.natural_language_query,
                    user_id=user_id,
                )

                generation_end = datetime.utcnow()
                generation_ms = int(
                    (generation_end - generation_start).total_seconds() * 1000
                )

                logger.info(
                    f"SQL generated successfully for attempt {query_attempt.id}",
                    extra={
                        "attempt_id": query_attempt.id,
                        "generation_ms": generation_ms,
                        "sql_length": len(generated_sql) if generated_sql else 0,
                    },
                )

                # Step 3: Update query attempt with success
                query_attempt = self._update_attempt_success(
                    db=db,
                    attempt_id=query_attempt.id,
                    generated_sql=generated_sql,
                    generation_ms=generation_ms,
                )

            except SQLGenerationError as e:
                # SQL generation failed - update with error
                generation_end = datetime.utcnow()
                generation_ms = int(
                    (generation_end - generation_start).total_seconds() * 1000
                )

                logger.warning(
                    f"SQL generation failed for attempt {query_attempt.id}: {e}",
                    extra={"attempt_id": query_attempt.id, "error": str(e)},
                )

                query_attempt = self._update_attempt_failure(
                    db=db,
                    attempt_id=query_attempt.id,
                    error_message=str(e),
                    generation_ms=generation_ms,
                )

            # Step 4: Return response
            return QueryAttemptResponse(
                id=query_attempt.id,
                natural_language_query=query_attempt.natural_language_query,
                generated_sql=query_attempt.generated_sql,
                status=QueryStatus(query_attempt.status),
                created_at=query_attempt.created_at,
                generated_at=query_attempt.generated_at,
                generation_ms=query_attempt.generation_ms,
                error_message=query_attempt.error_message,
            )

        except Exception as e:
            logger.error(
                f"Unexpected error creating query attempt for user {user_id}: {e}",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    def _create_initial_attempt(
        self,
        db: Session,
        user_id: int,
        natural_language_query: str,
        created_at: str,
    ) -> QueryAttempt:
        """
        Create initial query attempt record in database.

        TODO: Replace with actual SQLAlchemy model insert.

        Args:
            db: Database session
            user_id: User ID
            natural_language_query: Natural language query text
            created_at: ISO 8601 timestamp

        Returns:
            QueryAttempt object with initial state
        """
        # Placeholder implementation - replace with actual database insert
        # For now, return a mock object to demonstrate the flow
        return QueryAttempt(
            id=1,  # Would be auto-generated by database
            user_id=user_id,
            natural_language_query=natural_language_query,
            generated_sql=None,
            status=QueryStatus.NOT_EXECUTED.value,
            created_at=created_at,
            generated_at=None,
            generation_ms=None,
            error_message=None,
        )

    async def _generate_sql(
        self, natural_language_query: str, user_id: int
    ) -> str:
        """
        Generate SQL from natural language query using two-stage process.

        Stage 1: Schema optimization - Select relevant tables
        Stage 2: SQL generation - Generate SQL using selected tables and KB examples

        Args:
            natural_language_query: User's natural language query
            user_id: User ID for logging

        Returns:
            Generated SQL string

        Raises:
            SQLGenerationError: If SQL generation fails after retries
            LLMServiceUnavailableError: If OpenAI API is unavailable after retries
        """
        logger.info(
            f"Starting SQL generation for user {user_id}",
            extra={"user_id": user_id},
        )

        # TODO: Implement actual two-stage SQL generation
        # Stage 1: Call LLMService.select_relevant_tables(schema, question)
        # Stage 2: Call LLMService.generate_sql(question, filtered_schema, examples)
        # For now, raise error to simulate generation failure

        raise SQLGenerationError(
            "SQL generation not yet implemented - LLMService integration pending"
        )

    def _update_attempt_success(
        self,
        db: Session,
        attempt_id: int,
        generated_sql: str,
        generation_ms: int,
    ) -> QueryAttempt:
        """
        Update query attempt with successful SQL generation.

        TODO: Replace with actual SQLAlchemy update.

        Args:
            db: Database session
            attempt_id: Query attempt ID
            generated_sql: Generated SQL string
            generation_ms: Generation time in milliseconds

        Returns:
            Updated QueryAttempt object
        """
        generated_at = datetime.utcnow().isoformat() + "Z"

        # Placeholder - replace with actual update
        return QueryAttempt(
            id=attempt_id,
            user_id=1,  # Would come from database
            natural_language_query="",  # Would come from database
            generated_sql=generated_sql,
            status=QueryStatus.NOT_EXECUTED.value,
            created_at="",  # Would come from database
            generated_at=generated_at,
            generation_ms=generation_ms,
            error_message=None,
        )

    def _update_attempt_failure(
        self,
        db: Session,
        attempt_id: int,
        error_message: str,
        generation_ms: int,
    ) -> QueryAttempt:
        """
        Update query attempt with generation failure.

        TODO: Replace with actual SQLAlchemy update.

        Args:
            db: Database session
            attempt_id: Query attempt ID
            error_message: Error message describing the failure
            generation_ms: Time taken before failure in milliseconds

        Returns:
            Updated QueryAttempt object
        """
        # Placeholder - replace with actual update
        return QueryAttempt(
            id=attempt_id,
            user_id=1,  # Would come from database
            natural_language_query="",  # Would come from database
            generated_sql=None,
            status=QueryStatus.FAILED_GENERATION.value,
            created_at="",  # Would come from database
            generated_at=None,
            generation_ms=generation_ms,
            error_message=error_message,
        )


class SQLGenerationError(Exception):
    """Raised when SQL generation fails (e.g., invalid LLM response, validation failure)."""

    pass


class LLMServiceUnavailableError(Exception):
    """Raised when OpenAI API is unavailable after retries."""

    pass
