"""
API route handlers for query workflow endpoints.

Handles:
- POST /queries - Create query attempt and generate SQL
- GET /queries/{id} - Retrieve query attempt details
- GET /queries - List query attempts with pagination
- POST /queries/{id}/execute - Execute generated SQL
- GET /queries/{id}/results - Get paginated results
- GET /queries/{id}/export - Export results as CSV
- POST /queries/{id}/rerun - Re-run historical query
"""

import json
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_current_user, get_db
from backend.app.models.query import QueryAttempt, QueryResultsManifest
from backend.app.models.user import User
from backend.app.schemas.common import PaginationMetadata, QueryStatus
from backend.app.schemas.queries import (
    CreateQueryRequest,
    ExecuteQueryResponse,
    QueryAttemptDetailResponse,
    QueryAttemptResponse,
    QueryListResponse,
    QueryResults,
    QueryResultsResponse,
    RerunQueryResponse,
    SimplifiedQueryAttempt,
)
from backend.app.services.export_service import ExportService, ExportTooLargeError
from backend.app.services.postgres_execution_service import (
    DatabaseExecutionError,
    PostgresExecutionService,
    QueryTimeoutError,
)
from backend.app.services.query_service import (
    LLMServiceUnavailableError,
    QueryService,
)
from backend.app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queries", tags=["Queries"])

# Initialize services
query_service = QueryService()
postgres_service = PostgresExecutionService()
export_service = ExportService()

kb_service = KnowledgeBaseService()


# ============================================================================
# Route Handlers
# ============================================================================


@router.get(
    "/examples",
    response_model=dict,
    summary="Get example questions from knowledge base",
    responses={
        200: {
            "description": "Example questions retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "examples": [
                            {
                                "title": "Drivers With Current Availability",
                                "description": "Show all drivers and their current availability status",
                            },
                            {
                                "title": "Current Year Delayed Activities",
                                "description": "Find activities delayed by more than 3 hours this year",
                            },
                        ]
                    }
                }
            },
        },
    },
)
async def get_example_questions(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get example questions from knowledge base.

    Retrieves example SQL questions based on the knowledge base .sql files.
    Each example includes a title derived from the filename and an optional description.

    Returns:
        ExampleQuestionsResponse: List of example questions
    """
    logger.info(
        f"User {current_user.id} requesting example questions",
        extra={"user_id": current_user.id},
    )

    try:
        # Get all examples from knowledge base
        examples = kb_service.get_examples()

        # Convert to response format
        example_questions = [
            {
                "title": example.title,
                "description": example.description,
                "sql": example.sql,
                "filename": example.filename,
            }
            for example in examples
        ]

        logger.info(
            f"Returning {len(example_questions)} example questions",
            extra={"count": len(example_questions)},
        )

        return {"examples": example_questions}

    except Exception as e:
        logger.error(
            f"Failed to load example questions: {e}",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load example questions",
        )


@router.post(
    "",
    response_model=QueryAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create query attempt and generate SQL",
    responses={
        201: {
            "description": "Query attempt created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 42,
                        "natural_language_query": "Show me all active users",
                        "generated_sql": "SELECT * FROM users WHERE active = 1",
                        "status": "not_executed",
                        "created_at": "2025-10-29T12:00:00Z",
                        "generated_at": "2025-10-29T12:00:02Z",
                        "generation_ms": 2150,
                        "error_message": None,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request - empty query or validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Query cannot be only whitespace",
                        "error_code": "VALIDATION_ERROR",
                    }
                }
            },
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session token is missing or invalid",
                        "error_code": "AUTH_SESSION_INVALID",
                    }
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Try again in 60 seconds.",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                    }
                }
            },
        },
        503: {
            "description": "LLM service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "AI service temporarily unavailable. Please try again later.",
                        "error_code": "LLM_SERVICE_UNAVAILABLE",
                    }
                }
            },
        },
    },
)
async def create_query(
    request: CreateQueryRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> QueryAttemptResponse:
    """
    Submit a natural language query and generate SQL.

    This endpoint performs a two-stage SQL generation process:
    1. **Schema Optimization**: Selects relevant tables from PostgreSQL schema
    2. **SQL Generation**: Generates SQL using selected tables and 3 most similar
       knowledge base examples (via cosine similarity)

    The endpoint returns immediately after SQL generation (or failure), with status:
    - `not_executed`: SQL generated successfully, ready for execution
    - `failed_generation`: SQL generation failed (see error_message)

    **Rate Limiting**: 10 requests per minute per user

    **Performance**: Target <2 minutes for 95% of queries (includes retries)

    Args:
        request: Query creation request with natural language query
        user: Authenticated user (from session cookie)
        db: Database session

    Returns:
        QueryAttemptResponse with query details and generated SQL (or error)

    Raises:
        HTTPException 400: Invalid input (empty query, validation failed)
        HTTPException 401: Not authenticated
        HTTPException 429: Rate limit exceeded
        HTTPException 503: LLM service unavailable after 3 retries
    """
    logger.info(
        f"POST /queries - User {user.id} creating query",
        extra={
            "user_id": user.id,
            "username": user.username,
            "query_length": len(request.natural_language_query),
        },
    )

    try:
        # TODO: Add rate limiting check here
        # rate_limiter.check_limit(user.id, endpoint="/queries")

        # Create query attempt and generate SQL
        result = await query_service.create_query_attempt(
            db=db, user_id=user.id, request=request
        )

        logger.info(
            f"Query attempt {result.id} created successfully",
            extra={
                "attempt_id": result.id,
                "user_id": user.id,
                "status": (
                    result.status
                    if isinstance(result.status, str)
                    else result.status.value
                ),
                "generation_ms": result.generation_ms,
            },
        )

        return result

    except LLMServiceUnavailableError as e:
        logger.error(
            f"LLM service unavailable for user {user.id}: {e}",
            extra={"user_id": user.id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again later.",
        ) from e

    except ValueError as e:
        # Validation errors from service layer
        logger.warning(
            f"Validation error for user {user.id}: {e}",
            extra={"user_id": user.id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error creating query for user {user.id}: {e}",
            extra={"user_id": user.id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again later.",
        ) from e


# ============================================================================
# Additional Endpoints (Stubs)
# TODO: Implement these endpoints following the same pattern
# ============================================================================


@router.get(
    "/{id}",
    response_model=QueryAttemptDetailResponse,
    summary="Get query attempt details",
)
async def get_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> QueryAttemptDetailResponse:
    """
    Retrieve detailed information about a specific query attempt.

    Includes all query attempt fields plus execution details.

    Authorization:
    - Users can only access their own queries
    - Admins can access any query

    Args:
        id: Query attempt ID
        user: Authenticated user
        db: Database session

    Returns:
        QueryAttemptDetailResponse with full query details

    Raises:
        HTTPException 404: Query not found
        HTTPException 403: Not authorized to access this query
    """
    query = db.query(QueryAttempt).filter(QueryAttempt.id == id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query attempt {id} not found",
        )

    # Authorization check
    if query.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this query",
        )

    logger.info(f"GET /queries/{id} - User {user.id} retrieved query")

    # Note: created_at is always set, but provide fallback for type safety
    created_at_str = (
        query.created_at.isoformat() + "Z"
        if query.created_at
        else datetime.utcnow().isoformat() + "Z"
    )
    return QueryAttemptDetailResponse(
        id=query.id,
        natural_language_query=query.natural_language_query,
        generated_sql=query.generated_sql,
        status=(
            QueryStatus(query.status) if isinstance(query.status, str) else query.status
        ),
        created_at=created_at_str,
        generated_at=(
            query.generated_at.isoformat() + "Z" if query.generated_at else None
        ),
        generation_ms=query.generation_ms,
        error_message=query.error_message,
        executed_at=query.executed_at.isoformat() + "Z" if query.executed_at else None,
        execution_ms=query.execution_ms,
        original_attempt_id=(
            query.original_attempt_id if hasattr(query, "original_attempt_id") else None
        ),
    )


@router.get("", response_model=QueryListResponse, summary="List query attempts")
async def list_queries(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
) -> QueryListResponse:
    """
    List user's query attempts with pagination and optional filtering.

    Authorization:
    - Users see only their own queries
    - Admins see all queries

    Args:
        user: Authenticated user
        db: Database session
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        status_filter: Optional status filter (e.g., "success", "failed_generation")

    Returns:
        QueryListResponse with paginated list of queries

    Raises:
        HTTPException 400: Invalid pagination parameters
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100",
        )

    # Build query
    query = db.query(QueryAttempt)

    # Filter by user (unless admin)
    if user.role != "admin":
        query = query.filter(QueryAttempt.user_id == user.id)

    # Filter by status
    if status_filter:
        query = query.filter(QueryAttempt.status == status_filter)

    # Order by most recent first
    query = query.order_by(QueryAttempt.created_at.desc())

    # Get total count
    total_count = query.count()

    # Paginate
    offset = (page - 1) * page_size
    query_attempts = query.offset(offset).limit(page_size).all()

    # Convert to simplified responses
    simplified_queries = [
        SimplifiedQueryAttempt(
            id=q.id,
            natural_language_query=q.natural_language_query,
            status=QueryStatus(q.status) if isinstance(q.status, str) else q.status,
            created_at=(
                q.created_at.isoformat() + "Z"
                if q.created_at
                else datetime.utcnow().isoformat() + "Z"
            ),
            executed_at=q.executed_at.isoformat() + "Z" if q.executed_at else None,
        )
        for q in query_attempts
    ]

    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size

    logger.info(
        f"GET /queries - User {user.id} listed queries "
        f"(page {page}, total {total_count})"
    )

    return QueryListResponse(
        queries=simplified_queries,
        pagination=PaginationMetadata(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
        ),
    )


@router.post(
    "/{id}/execute",
    response_model=ExecuteQueryResponse,
    summary="Execute generated SQL",
)
async def execute_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExecuteQueryResponse:
    """
    Execute the generated SQL against PostgreSQL database.

    Executes the SQL query with a 30-second timeout and stores results
    in the QueryResultsManifest for pagination.

    Authorization:
    - Users can only execute their own queries
    - Admins can execute any query

    Args:
        id: Query attempt ID
        user: Authenticated user
        db: Database session

    Returns:
        ExecuteQueryResponse with execution results or error

    Raises:
        HTTPException 404: Query not found
        HTTPException 403: Not authorized
        HTTPException 400: Query cannot be executed (no SQL or already executed)
        HTTPException 408: Query timeout
        HTTPException 500: Database error
    """
    # Get query attempt
    query_attempt = db.query(QueryAttempt).filter(QueryAttempt.id == id).first()

    if not query_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query attempt {id} not found",
        )

    # Authorization check
    if query_attempt.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to execute this query",
        )

    # Validation checks
    if not query_attempt.generated_sql:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot execute query: SQL generation failed or is pending",
        )

    if query_attempt.status == QueryStatus.SUCCESS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query has already been executed successfully",
        )

    logger.info(f"POST /queries/{id}/execute - User {user.id} executing query")

    try:
        # Execute query using PostgresExecutionService
        result = await postgres_service.execute_query_attempt(db, query_attempt)

        # Refresh to get updated values
        db.refresh(query_attempt)

        logger.info(
            f"Query {id} executed successfully: {result.total_rows} rows in {result.execution_ms}ms"
        )

        # executed_at and execution_ms should be set after execution, provide fallbacks
        executed_at_str = (
            query_attempt.executed_at.isoformat() + "Z"
            if query_attempt.executed_at
            else datetime.utcnow().isoformat() + "Z"
        )
        execution_ms = query_attempt.execution_ms or 0

        return ExecuteQueryResponse(
            id=query_attempt.id,
            status=QueryStatus(query_attempt.status),
            executed_at=executed_at_str,
            execution_ms=execution_ms,
            results=QueryResults(
                total_rows=result.total_rows,
                page_size=500,
                page_count=(result.total_rows + 500 - 1) // 500,
                columns=result.columns,
                rows=result.rows[:500],  # Return first page
            ),
            error_message=None,
        )

    except QueryTimeoutError as e:
        logger.warning(f"Query {id} execution timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e),
        ) from e

    except ValueError as e:
        logger.error(f"Query {id} validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except DatabaseExecutionError as e:
        logger.error(f"Query {id} database execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Query {id} execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during execution: {str(e)}",
        ) from e


@router.get(
    "/{id}/results",
    response_model=QueryResultsResponse,
    summary="Get paginated results",
)
async def get_query_results(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
) -> QueryResultsResponse:
    """
    Retrieve paginated results for an executed query.

    Results are paginated at 500 rows per page. This endpoint returns
    the requested page from the stored results.

    Authorization:
    - Users can only access their own query results
    - Admins can access any query results

    Args:
        id: Query attempt ID
        user: Authenticated user
        db: Database session
        page: Page number (default: 1)

    Returns:
        QueryResultsResponse with paginated results

    Raises:
        HTTPException 404: Query not found or no results available
        HTTPException 403: Not authorized
        HTTPException 400: Invalid page number
    """
    # Get query attempt
    query_attempt = db.query(QueryAttempt).filter(QueryAttempt.id == id).first()

    if not query_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query attempt {id} not found",
        )

    # Authorization check
    if query_attempt.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these results",
        )

    # Get results manifest
    manifest = (
        db.query(QueryResultsManifest)
        .filter(QueryResultsManifest.attempt_id == id)
        .first()
    )

    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results available for query {id}. Query may not have been executed yet.",
        )

    # Validate page number
    page_count = manifest.page_count or 1
    if page < 1 or page > page_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid page number. Must be between 1 and {page_count}.",
        )

    # Get results from JSON
    if manifest.columns_json is None or manifest.results_json is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results data available for query {id}.",
        )
    columns = json.loads(manifest.columns_json)
    all_rows = json.loads(manifest.results_json)

    # Calculate pagination
    page_size = manifest.page_size
    offset = (page - 1) * page_size
    page_rows = all_rows[offset : offset + page_size]

    logger.info(
        f"GET /queries/{id}/results?page={page} - User {user.id} retrieved results"
    )

    return QueryResultsResponse(
        attempt_id=id,
        total_rows=manifest.total_rows or 0,
        page_size=page_size,
        page_count=page_count,
        current_page=page,
        columns=columns,
        rows=page_rows,
    )


@router.get("/{id}/export", summary="Export results as CSV")
async def export_query_results(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Export query results as CSV file (up to 10,000 rows).

    Returns a streaming CSV response with proper escaping and UTF-8 encoding.

    Authorization:
    - Users can only export their own query results
    - Admins can export any query results

    Args:
        id: Query attempt ID
        user: Authenticated user
        db: Database session

    Returns:
        StreamingResponse with CSV file

    Raises:
        HTTPException 404: Query not found or no results available
        HTTPException 403: Not authorized
        HTTPException 413: Result set too large (> 10,000 rows)
    """
    # Get query attempt
    query_attempt = db.query(QueryAttempt).filter(QueryAttempt.id == id).first()

    if not query_attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query attempt {id} not found",
        )

    # Authorization check
    if query_attempt.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export these results",
        )

    logger.info(f"GET /queries/{id}/export - User {user.id} exporting results")

    try:
        return await export_service.export_to_csv(db, id)

    except ExportTooLargeError as e:
        logger.warning(f"Export too large for query {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        ) from e

    except ValueError as e:
        logger.error(f"Export error for query {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(f"Unexpected export error for query {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        ) from e


@router.post(
    "/{id}/rerun",
    response_model=RerunQueryResponse,
    summary="Re-run historical query",
    status_code=status.HTTP_201_CREATED,
)
async def rerun_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RerunQueryResponse:
    """
    Create a new query attempt by re-running a historical query.

    Creates a new query attempt with the same natural language query,
    but generates fresh SQL (may differ from original due to schema changes
    or LLM improvements).

    Authorization:
    - Users can only re-run their own queries
    - Admins can re-run any query

    Args:
        id: Original query attempt ID to re-run
        user: Authenticated user
        db: Database session

    Returns:
        RerunQueryResponse with new query attempt details

    Raises:
        HTTPException 404: Original query not found
        HTTPException 403: Not authorized
        HTTPException 503: LLM service unavailable
    """
    # Get original query attempt
    original_query = db.query(QueryAttempt).filter(QueryAttempt.id == id).first()

    if not original_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query attempt {id} not found",
        )

    # Authorization check
    if original_query.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to re-run this query",
        )

    logger.info(f"POST /queries/{id}/rerun - User {user.id} re-running query")

    try:
        # Create new query attempt with same natural language query
        request = CreateQueryRequest(
            natural_language_query=original_query.natural_language_query
        )

        new_attempt = await query_service.create_query_attempt(
            db=db, user_id=user.id, request=request
        )

        # Update with original_attempt_id for lineage tracking
        query_model = (
            db.query(QueryAttempt).filter(QueryAttempt.id == new_attempt.id).first()
        )
        if query_model:
            query_model.original_attempt_id = id
            db.commit()
            db.refresh(query_model)

        logger.info(f"Query {id} re-run successfully, new attempt ID: {new_attempt.id}")

        return RerunQueryResponse(
            id=new_attempt.id,
            original_attempt_id=id,
            natural_language_query=new_attempt.natural_language_query,
            generated_sql=new_attempt.generated_sql,
            status=new_attempt.status,
            created_at=new_attempt.created_at,
            generated_at=new_attempt.generated_at,
            generation_ms=new_attempt.generation_ms,
            error_message=new_attempt.error_message,
        )

    except LLMServiceUnavailableError as e:
        logger.error(f"LLM service unavailable for re-run: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Please try again later.",
        ) from e

    except Exception as e:
        logger.error(f"Error re-running query {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-run query: {str(e)}",
        ) from e
