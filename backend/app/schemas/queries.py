"""
Query-related schemas for natural language query workflow.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import PaginationMetadata, QueryStatus


class CreateQueryRequest(BaseModel):
    """Request payload for creating a new query attempt."""

    natural_language_query: str = Field(
        min_length=1,
        max_length=5000,
        description="Natural language query to convert to SQL",
    )

    @field_validator("natural_language_query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate query is not only whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be only whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "natural_language_query": "Show me all users who registered in the last 30 days"
            }
        }


class QueryAttemptResponse(BaseModel):
    """Response for a query attempt (creation or retrieval)."""

    id: int = Field(description="Query attempt ID")
    natural_language_query: str = Field(description="Original natural language query")
    generated_sql: str | None = Field(
        default=None, description="Generated SQL query (null if generation failed)"
    )
    status: QueryStatus = Field(description="Current status of the query attempt")
    created_at: str = Field(description="ISO 8601 timestamp when query was created")
    generated_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp when SQL was generated (null if not generated)",
    )
    generation_ms: int | None = Field(
        default=None, description="Time taken to generate SQL in milliseconds"
    )
    error_message: str | None = Field(
        default=None, description="Error message if generation failed"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 42,
                "natural_language_query": "Show me all active users",
                "generated_sql": "SELECT * FROM users WHERE active = 1",
                "status": "not_executed",
                "created_at": "2025-10-28T12:00:00Z",
                "generated_at": "2025-10-28T12:00:02Z",
                "generation_ms": 2150,
                "error_message": None,
            }
        }


class QueryAttemptDetailResponse(QueryAttemptResponse):
    """Detailed response for a query attempt (includes execution details)."""

    executed_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp when query was executed (null if not executed)",
    )
    execution_ms: int | None = Field(
        default=None, description="Time taken to execute query in milliseconds"
    )
    original_attempt_id: int | None = Field(
        default=None, description="ID of original query if this is a re-run"
    )

    class Config:
        from_attributes = True


class SimplifiedQueryAttempt(BaseModel):
    """Simplified query attempt for list views."""

    id: int = Field(description="Query attempt ID")
    natural_language_query: str = Field(description="Original natural language query")
    status: QueryStatus = Field(description="Current status")
    created_at: str = Field(description="ISO 8601 timestamp when created")
    executed_at: str | None = Field(
        default=None, description="ISO 8601 timestamp when executed"
    )

    class Config:
        from_attributes = True


class QueryListResponse(BaseModel):
    """Response for listing query attempts with pagination."""

    queries: list[SimplifiedQueryAttempt] = Field(description="List of query attempts")
    pagination: PaginationMetadata = Field(description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "queries": [
                    {
                        "id": 42,
                        "natural_language_query": "Show me all active users",
                        "status": "success",
                        "created_at": "2025-10-28T12:00:00Z",
                        "executed_at": "2025-10-28T12:00:05Z",
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_count": 100,
                    "total_pages": 5,
                },
            }
        }


class ExecuteQueryRequest(BaseModel):
    """Request payload for executing a query (empty, uses path parameter)."""

    pass


class QueryResults(BaseModel):
    """Query execution results structure."""

    total_rows: int = Field(description="Total number of rows in result set")
    page_size: int = Field(description="Number of rows per page")
    page_count: int = Field(description="Total number of pages")
    columns: list[str] = Field(description="Column names in result set")
    rows: list[list[Any]] = Field(
        description="Result rows (array of arrays with mixed types)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_rows": 150,
                "page_size": 500,
                "page_count": 1,
                "columns": ["id", "username", "email"],
                "rows": [[1, "john_doe", "john@example.com"]],
            }
        }


class ExecuteQueryResponse(BaseModel):
    """Response for query execution."""

    id: int = Field(description="Query attempt ID")
    status: QueryStatus = Field(
        description="Execution status (success, failed_execution, or timeout)"
    )
    executed_at: str = Field(description="ISO 8601 timestamp when executed")
    execution_ms: int = Field(description="Execution time in milliseconds")
    results: QueryResults | None = Field(
        default=None, description="Query results (null if execution failed)"
    )
    error_message: str | None = Field(
        default=None, description="Error message if execution failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 42,
                "status": "success",
                "executed_at": "2025-10-28T12:00:05Z",
                "execution_ms": 342,
                "results": {
                    "total_rows": 150,
                    "page_size": 500,
                    "page_count": 1,
                    "columns": ["id", "username"],
                    "rows": [[1, "john_doe"]],
                },
                "error_message": None,
            }
        }


class QueryResultsResponse(BaseModel):
    """Response for paginated query results retrieval."""

    attempt_id: int = Field(description="Query attempt ID")
    total_rows: int = Field(description="Total number of rows")
    page_size: int = Field(description="Rows per page (fixed at 500)")
    page_count: int = Field(description="Total number of pages")
    current_page: int = Field(description="Current page number")
    columns: list[str] = Field(description="Column names")
    rows: list[list[Any]] = Field(description="Result rows for current page")

    class Config:
        json_schema_extra = {
            "example": {
                "attempt_id": 42,
                "total_rows": 1500,
                "page_size": 500,
                "page_count": 3,
                "current_page": 1,
                "columns": ["id", "username", "created_at"],
                "rows": [[1, "john_doe", "2025-01-01T00:00:00Z"]],
            }
        }


class RerunQueryResponse(QueryAttemptResponse):
    """Response for re-running a historical query."""

    original_attempt_id: int = Field(description="ID of the original query attempt")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 43,
                "original_attempt_id": 42,
                "natural_language_query": "Show me all active users",
                "generated_sql": "SELECT * FROM users WHERE active = true",
                "status": "not_executed",
                "created_at": "2025-10-28T13:00:00Z",
                "generated_at": "2025-10-28T13:00:02Z",
                "generation_ms": 1890,
                "error_message": None,
            }
        }


class ExampleQuestion(BaseModel):
    """Example question from knowledge base."""

    title: str = Field(description="Human-readable title for the example")
    description: str | None = Field(
        default=None, description="Optional description of what the query does"
    )
    sql: str = Field(description="Pre-existing SQL query from knowledge base")
    filename: str = Field(description="KB example filename identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Drivers With Current Availability",
                "description": "Show all drivers and their current availability status",
                "sql": "SELECT d.id, d.name, da.status FROM drivers d JOIN driver_availability da ON d.id = da.driver_id;",
                "filename": "drivers_with_current_availability.sql",
            }
        }


class ExampleQuestionsResponse(BaseModel):
    """Response containing example questions from knowledge base."""

    examples: list[ExampleQuestion] = Field(
        description="List of example questions from knowledge base"
    )

    class Config:
        json_schema_extra = {
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
