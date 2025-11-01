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

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.queries import (
    CreateQueryRequest,
    QueryAttemptResponse,
)
from backend.app.services.query_service import (
    QueryService,
    LLMServiceUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queries", tags=["Queries"])
query_service = QueryService()


# ============================================================================
# Route Handlers
# ============================================================================


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
                "status": result.status.value,
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
    response_model=QueryAttemptResponse,
    summary="Get query attempt details",
)
async def get_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> QueryAttemptResponse:
    """
    Retrieve detailed information about a specific query attempt.

    TODO: Implement query retrieval with authorization checks.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented",
    )


@router.get("", summary="List query attempts")
async def list_queries(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
):
    """
    List user's query attempts with pagination.

    TODO: Implement query listing with pagination and filtering.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented",
    )


@router.post("/{id}/execute", summary="Execute generated SQL")
async def execute_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Execute the generated SQL against PostgreSQL database.

    TODO: Implement query execution with timeout handling.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented",
    )


@router.get("/{id}/results", summary="Get paginated results")
async def get_query_results(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
):
    """
    Retrieve paginated results for an executed query.

    TODO: Implement results retrieval with pagination.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented",
    )


@router.get("/{id}/export", summary="Export results as CSV")
async def export_query_results(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Export query results as CSV file (up to 10,000 rows).

    TODO: Implement CSV export with streaming response.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented",
    )


@router.post("/{id}/rerun", summary="Re-run historical query")
async def rerun_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new query attempt by re-running a historical query.

    TODO: Implement query re-run with lineage tracking.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented",
    )
