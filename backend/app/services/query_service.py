"""
Service layer for query attempt creation and SQL generation.

This service handles the two-stage SQL generation process:
1. Schema optimization: Select relevant tables from PostgreSQL schema
2. SQL generation: Generate SQL using selected tables and knowledge base examples
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.schemas.queries import CreateQueryRequest, QueryAttemptResponse
from backend.app.schemas.common import QueryStatus
from backend.app.models.query import QueryAttempt as QueryAttemptModel
from backend.app.services.llm_service import LLMService, LLMServiceUnavailableError
from backend.app.services.schema_service import SchemaService
from backend.app.services.knowledge_base_service import KnowledgeBaseService
from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryService:
    """Service for managing query attempts and SQL generation workflow."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        schema_service: SchemaService | None = None,
        kb_service: KnowledgeBaseService | None = None,
    ):
        """
        Initialize the query service with dependencies.

        Args:
            llm_service: LLM service for SQL generation
            schema_service: Schema service for database schema
            kb_service: Knowledge base service for SQL examples
        """
        self.llm = llm_service or LLMService()
        self.schema = schema_service or SchemaService()
        self.kb = kb_service or KnowledgeBaseService()

        logger.info("Query service initialized with all dependencies")

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
            # Note: created_at is always set, but mypy needs assurance
            created_at_str = (
                query_attempt.created_at.isoformat() + "Z"
                if query_attempt.created_at
                else datetime.utcnow().isoformat() + "Z"
            )
            return QueryAttemptResponse(
                id=query_attempt.id,
                natural_language_query=query_attempt.natural_language_query,
                generated_sql=query_attempt.generated_sql,
                status=QueryStatus(query_attempt.status),
                created_at=created_at_str,
                generated_at=(
                    query_attempt.generated_at.isoformat() + "Z"
                    if query_attempt.generated_at
                    else None
                ),
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
    ) -> QueryAttemptModel:
        """
        Create initial query attempt record in database.

        Args:
            db: Database session
            user_id: User ID
            natural_language_query: Natural language query text
            created_at: ISO 8601 timestamp

        Returns:
            QueryAttemptModel object with initial state
        """
        # Create new query attempt
        query_attempt = QueryAttemptModel(
            user_id=user_id,
            natural_language_query=natural_language_query,
            generated_sql=None,
            status=QueryStatus.NOT_EXECUTED.value,
            created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
            generated_at=None,
            generation_ms=None,
            error_message=None,
        )

        db.add(query_attempt)
        db.commit()
        db.refresh(query_attempt)

        logger.debug(f"Created query attempt ID {query_attempt.id}")

        return query_attempt

    async def _generate_sql(self, natural_language_query: str, user_id: int) -> str:
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
            f"Starting two-stage SQL generation for user {user_id}",
            extra={"user_id": user_id},
        )

        try:
            # Stage 1: Schema optimization - Select relevant tables
            logger.info("Stage 1: Selecting relevant tables from schema")
            table_names = self.schema.get_table_names()
            logger.debug(f"Total tables available: {len(table_names)}")

            selected_tables = await self.llm.select_relevant_tables(
                table_names=table_names, question=natural_language_query, max_tables=10
            )

            logger.info(
                f"Stage 1 complete: Selected {len(selected_tables)} tables: {selected_tables}"
            )

            # Filter schema to selected tables
            filtered_schema = self.schema.filter_schema_by_tables(selected_tables)
            schema_text = self.schema.format_schema_for_llm(
                filtered_schema, include_descriptions=True, include_foreign_keys=True
            )

            logger.debug(f"Filtered schema size: {len(schema_text)} characters")

            # Stage 2: Generate question embedding and find similar KB examples
            logger.info(
                "Stage 2: Generating question embedding and finding similar examples"
            )

            # Generate embedding for the user's question
            question_embedding = await self.llm.generate_embedding(
                natural_language_query
            )

            # Find similar examples using embedding-based search
            kb_examples, max_similarity = await self.kb.find_similar_examples(
                question=natural_language_query,
                question_embedding=question_embedding,
                top_k=3,
            )

            logger.info(
                f"Found {len(kb_examples)} similar KB examples. "
                f"Max similarity: {max_similarity:.3f}"
            )

            # Check if we have a high-similarity match
            if max_similarity >= settings.rag_similarity_threshold and kb_examples:
                logger.info(
                    f"High similarity match found ({max_similarity:.3f} >= {settings.rag_similarity_threshold}). "
                    f"Returning KB example: {kb_examples[0].title}"
                )
                return kb_examples[0].sql

            # Stage 3: Generate SQL using LLM if no exact match
            example_sqls = [ex.sql for ex in kb_examples]
            logger.info(
                f"No exact match. Generating SQL with LLM using {len(example_sqls)} examples as context"
            )

            generated_sql = await self.llm.generate_sql(
                question=natural_language_query,
                schema_text=schema_text,
                examples=example_sqls,
            )

            logger.info(
                f"SQL generation complete: {len(generated_sql)} characters",
                extra={"sql_length": len(generated_sql)},
            )

            return generated_sql

        except LLMServiceUnavailableError:
            # Re-raise LLM errors as-is
            raise

        except ValueError as e:
            # LLM returned invalid response
            logger.error(f"SQL generation failed: {e}")
            raise SQLGenerationError(str(e)) from e

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in SQL generation: {e}", exc_info=True)
            raise SQLGenerationError(
                "An unexpected error occurred during SQL generation"
            ) from e

    def _update_attempt_success(
        self,
        db: Session,
        attempt_id: int,
        generated_sql: str,
        generation_ms: int,
    ) -> QueryAttemptModel:
        """
        Update query attempt with successful SQL generation.

        Args:
            db: Database session
            attempt_id: Query attempt ID
            generated_sql: Generated SQL string
            generation_ms: Generation time in milliseconds

        Returns:
            Updated QueryAttemptModel object
        """
        # Get query attempt
        query_attempt = (
            db.query(QueryAttemptModel)
            .filter(QueryAttemptModel.id == attempt_id)
            .first()
        )

        if not query_attempt:
            raise ValueError(f"Query attempt {attempt_id} not found")

        # Update fields
        query_attempt.generated_sql = generated_sql
        query_attempt.status = QueryStatus.NOT_EXECUTED.value
        query_attempt.generated_at = datetime.utcnow()
        query_attempt.generation_ms = generation_ms
        query_attempt.error_message = None

        db.commit()
        db.refresh(query_attempt)

        logger.debug(f"Updated query attempt {attempt_id} with success")

        return query_attempt

    def _update_attempt_failure(
        self,
        db: Session,
        attempt_id: int,
        error_message: str,
        generation_ms: int,
    ) -> QueryAttemptModel:
        """
        Update query attempt with generation failure.

        Args:
            db: Database session
            attempt_id: Query attempt ID
            error_message: Error message describing the failure
            generation_ms: Time taken before failure in milliseconds

        Returns:
            Updated QueryAttemptModel object
        """
        # Get query attempt
        query_attempt = (
            db.query(QueryAttemptModel)
            .filter(QueryAttemptModel.id == attempt_id)
            .first()
        )

        if not query_attempt:
            raise ValueError(f"Query attempt {attempt_id} not found")

        # Update fields
        query_attempt.generated_sql = None
        query_attempt.status = QueryStatus.FAILED_GENERATION.value
        query_attempt.generated_at = None
        query_attempt.generation_ms = generation_ms
        query_attempt.error_message = error_message

        db.commit()
        db.refresh(query_attempt)

        logger.debug(f"Updated query attempt {attempt_id} with failure")

        return query_attempt


class SQLGenerationError(Exception):
    """Raised when SQL generation fails (e.g., invalid LLM response, validation failure)."""

    pass
