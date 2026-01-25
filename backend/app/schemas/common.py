"""
Common schemas and shared types used across the API.
"""

from enum import Enum

from pydantic import BaseModel, Field


class QueryStatus(str, Enum):
    """Status of a query attempt."""

    NOT_EXECUTED = "not_executed"
    FAILED_GENERATION = "failed_generation"
    FAILED_EXECUTION = "failed_execution"
    SUCCESS = "success"
    TIMEOUT = "timeout"


class UserRole(str, Enum):
    """User role types."""

    ADMIN = "admin"
    USER = "user"


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total_count: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")


class ErrorResponse(BaseModel):
    """Standard error response structure."""

    detail: str = Field(description="Error message")
    error_code: str | None = Field(
        default=None, description="Machine-readable error code"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "error_code": "AUTH_INVALID_CREDENTIALS",
            }
        }


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(description="Response message")
