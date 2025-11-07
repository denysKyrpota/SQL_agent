"""
PostgreSQL Execution Service for running generated SQL queries.

Validates and executes SELECT-only queries against the target PostgreSQL database
with timeout handling and result pagination.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import sqlparse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError, DatabaseError
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.query import QueryAttempt, ResultsManifest
from backend.app.schemas.common import QueryStatus

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class QueryResult:
    """
    Query execution result.

    Attributes:
        columns: List of column names
        rows: List of result rows (each row is a list of values)
        total_rows: Total number of rows returned
        execution_ms: Execution time in milliseconds
    """
    columns: list[str]
    rows: list[list[Any]]
    total_rows: int
    execution_ms: int


class PostgresExecutionService:
    """
    Service for executing SQL queries against PostgreSQL target database.

    Handles validation, execution with timeout, and result storage.
    """

    def __init__(self):
        """Initialize the PostgreSQL execution service."""
        self._engine: Engine | None = None
        logger.info("PostgreSQL execution service initialized")

    def _get_engine(self) -> Engine:
        """
        Get or create PostgreSQL engine.

        Returns:
            Engine: SQLAlchemy engine for PostgreSQL

        Raises:
            ValueError: If POSTGRES_URL not configured
        """
        if self._engine is None:
            if not settings.postgres_url:
                raise ValueError(
                    "POSTGRES_URL not configured in environment. "
                    "Set POSTGRES_URL in .env file."
                )

            logger.info(f"Creating PostgreSQL engine: {self._mask_password(settings.postgres_url)}")

            self._engine = create_engine(
                settings.postgres_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,  # MVP: 5 connections
                max_overflow=10,  # Allow up to 15 total connections
                pool_recycle=3600,  # Recycle connections after 1 hour
                execution_options={
                    "postgresql_readonly": True  # Read-only mode
                }
            )

        return self._engine

    def _mask_password(self, url: str) -> str:
        """Mask password in connection string for logging."""
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)

    def validate_sql(self, sql: str) -> None:
        """
        Validate SQL query to ensure it's safe to execute.

        Checks:
        1. Must be SELECT statement only
        2. No multiple statements (semicolon-separated)
        3. No DDL/DML operations (CREATE, DROP, INSERT, UPDATE, DELETE, etc.)

        Args:
            sql: SQL query to validate

        Raises:
            ValueError: If SQL fails validation

        Example:
            >>> service = PostgresExecutionService()
            >>> service.validate_sql("SELECT * FROM users")  # OK
            >>> service.validate_sql("DELETE FROM users")  # Raises ValueError
        """
        if not sql or not sql.strip():
            raise ValueError("SQL query is empty")

        # Parse SQL
        try:
            parsed = sqlparse.parse(sql)
        except Exception as e:
            raise ValueError(f"Invalid SQL syntax: {e}")

        if len(parsed) == 0:
            raise ValueError("No SQL statement found")

        if len(parsed) > 1:
            raise ValueError(
                "Multiple SQL statements not allowed. Only single SELECT queries are supported."
            )

        stmt = parsed[0]

        # Get statement type
        stmt_type = stmt.get_type()

        if stmt_type != 'SELECT':
            raise ValueError(
                f"Only SELECT queries are allowed. Found: {stmt_type}. "
                f"INSERT, UPDATE, DELETE, CREATE, DROP, and other modification commands are forbidden."
            )

        # Additional check: scan for dangerous keywords in uppercase
        sql_upper = sql.upper()
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                # Check if it's part of SELECT statement (e.g., in a string literal)
                # Simple heuristic: if it appears before SELECT or after ;
                if sql_upper.index(keyword) < sql_upper.index('SELECT') if 'SELECT' in sql_upper else True:
                    raise ValueError(
                        f"Forbidden SQL keyword detected: {keyword}. "
                        f"Only SELECT queries are allowed."
                    )

        logger.debug("SQL validation passed")

    async def execute_query(
        self,
        sql: str,
        timeout: int | None = None
    ) -> QueryResult:
        """
        Execute SQL query against PostgreSQL database.

        Args:
            sql: Validated SQL query to execute
            timeout: Timeout in seconds (default: from settings)

        Returns:
            QueryResult: Execution results

        Raises:
            ValueError: If SQL is invalid
            QueryTimeoutError: If query exceeds timeout
            DatabaseError: If database error occurs

        Example:
            >>> result = await service.execute_query("SELECT * FROM users LIMIT 10")
            >>> print(f"Returned {result.total_rows} rows in {result.execution_ms}ms")
        """
        # Validate SQL first
        self.validate_sql(sql)

        timeout = timeout or settings.postgres_timeout

        logger.info(f"Executing query with {timeout}s timeout")
        logger.debug(f"SQL: {sql[:200]}...")

        start_time = datetime.utcnow()

        try:
            engine = self._get_engine()

            # Execute query with timeout
            with engine.connect().execution_options(
                timeout=timeout
            ) as connection:
                result = connection.execute(text(sql))

                # Fetch all rows
                rows = result.fetchall()

                # Get column names
                columns = list(result.keys())

                # Convert rows to list of lists
                rows_data = [list(row) for row in rows]

        except OperationalError as e:
            if "timeout" in str(e).lower():
                logger.warning(f"Query timeout after {timeout}s")
                raise QueryTimeoutError(
                    f"Query execution exceeded {timeout} second timeout. "
                    f"Try narrowing your search or adding more filters."
                ) from e
            else:
                logger.error(f"Database operational error: {e}")
                raise DatabaseError(
                    f"Database connection error: {e}"
                ) from e

        except ProgrammingError as e:
            logger.error(f"SQL programming error: {e}")
            raise ValueError(
                f"SQL syntax error: {e}"
            ) from e

        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}", exc_info=True)
            raise DatabaseError(
                f"Unexpected database error: {e}"
            ) from e

        # Calculate execution time
        end_time = datetime.utcnow()
        execution_ms = int((end_time - start_time).total_seconds() * 1000)

        total_rows = len(rows_data)

        logger.info(
            f"Query executed successfully: {total_rows} rows in {execution_ms}ms"
        )

        return QueryResult(
            columns=columns,
            rows=rows_data,
            total_rows=total_rows,
            execution_ms=execution_ms
        )

    async def execute_query_attempt(
        self,
        db: Session,
        query_attempt: QueryAttempt
    ) -> QueryResult:
        """
        Execute a query attempt and store results.

        This method:
        1. Validates the generated SQL
        2. Executes the query
        3. Updates query_attempt status
        4. Creates ResultsManifest for pagination
        5. Returns results

        Args:
            db: SQLite database session (for storing results)
            query_attempt: QueryAttempt model with generated_sql

        Returns:
            QueryResult: Execution results

        Raises:
            ValueError: If query_attempt has no generated_sql
            QueryTimeoutError: If execution times out
            DatabaseError: If database error occurs
        """
        if not query_attempt.generated_sql:
            raise ValueError("Query attempt has no generated SQL")

        logger.info(f"Executing query attempt ID {query_attempt.id}")

        try:
            # Execute query
            result = await self.execute_query(query_attempt.generated_sql)

            # Update query attempt status
            query_attempt.status = QueryStatus.SUCCESS.value
            query_attempt.executed_at = datetime.utcnow()
            query_attempt.execution_ms = result.execution_ms

            # Create results manifest for pagination
            manifest = self._create_results_manifest(
                db=db,
                query_attempt_id=query_attempt.id,
                result=result
            )

            db.commit()

            logger.info(
                f"Query attempt {query_attempt.id} executed successfully: "
                f"{result.total_rows} rows"
            )

            return result

        except QueryTimeoutError:
            query_attempt.status = QueryStatus.FAILED_EXECUTION.value
            query_attempt.error_message = "Query execution timeout"
            db.commit()
            raise

        except DatabaseError as e:
            query_attempt.status = QueryStatus.FAILED_EXECUTION.value
            query_attempt.error_message = str(e)
            db.commit()
            raise

        except Exception as e:
            query_attempt.status = QueryStatus.FAILED_EXECUTION.value
            query_attempt.error_message = f"Unexpected error: {e}"
            db.commit()
            raise

    def _create_results_manifest(
        self,
        db: Session,
        query_attempt_id: int,
        result: QueryResult
    ) -> ResultsManifest:
        """
        Create ResultsManifest for paginated results.

        Stores full results as JSON for later retrieval.

        Args:
            db: Database session
            query_attempt_id: Query attempt ID
            result: Query execution result

        Returns:
            ResultsManifest: Created manifest
        """
        # Calculate pagination
        page_size = 500  # As per spec
        page_count = (result.total_rows + page_size - 1) // page_size

        # Serialize results
        columns_json = json.dumps(result.columns)
        rows_json = json.dumps(result.rows)

        # Create manifest
        manifest = ResultsManifest(
            query_attempt_id=query_attempt_id,
            columns_json=columns_json,
            results_json=rows_json,
            total_rows=result.total_rows,
            page_size=page_size,
            page_count=page_count,
            created_at=datetime.utcnow()
        )

        db.add(manifest)

        logger.debug(
            f"Created results manifest: {result.total_rows} rows, "
            f"{page_count} pages"
        )

        return manifest

    def close(self):
        """Close database connection pool."""
        if self._engine:
            self._engine.dispose()
            logger.info("PostgreSQL connection pool closed")


class QueryTimeoutError(Exception):
    """Raised when query execution exceeds timeout."""
    pass
