"""
Pydantic schemas for request/response DTOs.

This package contains all data transfer objects used in the API endpoints.
"""

from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionResponse,
    SessionInfo,
    UserResponse,
)
from backend.app.schemas.common import (
    ErrorResponse,
    PaginationMetadata,
    PaginationParams,
    QueryStatus,
    UserRole,
)
from backend.app.schemas.queries import (
    CreateQueryRequest,
    ExecuteQueryRequest,
    ExecuteQueryResponse,
    QueryAttemptDetailResponse,
    QueryAttemptResponse,
    QueryListResponse,
    QueryResultsResponse,
    RerunQueryResponse,
    SimplifiedQueryAttempt,
)
from backend.app.schemas.admin import (
    MetricsRequest,
    MetricsResponse,
    MetricRow,
    MetricsSummary,
    RefreshSchemaResponse,
    ReloadKBResponse,
    KBReloadStats,
    SchemaSnapshotInfo,
)
from backend.app.schemas.health import (
    HealthCheckResponse,
    ServiceStatus,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "LogoutResponse",
    "SessionResponse",
    "SessionInfo",
    "UserResponse",
    # Common
    "ErrorResponse",
    "PaginationMetadata",
    "PaginationParams",
    "QueryStatus",
    "UserRole",
    # Queries
    "CreateQueryRequest",
    "ExecuteQueryRequest",
    "ExecuteQueryResponse",
    "QueryAttemptDetailResponse",
    "QueryAttemptResponse",
    "QueryListResponse",
    "QueryResultsResponse",
    "RerunQueryResponse",
    "SimplifiedQueryAttempt",
    # Admin
    "MetricsRequest",
    "MetricsResponse",
    "MetricRow",
    "MetricsSummary",
    "RefreshSchemaResponse",
    "ReloadKBResponse",
    "KBReloadStats",
    "SchemaSnapshotInfo",
    # Health
    "HealthCheckResponse",
    "ServiceStatus",
]
