"""
Admin-related schemas for administrative operations.
"""

from pydantic import BaseModel, Field


class SchemaSnapshotInfo(BaseModel):
    """Information about a schema snapshot."""

    id: int = Field(description="Snapshot ID")
    loaded_at: str = Field(description="ISO 8601 timestamp when schema was loaded")
    source_hash: str = Field(description="Hash of source schema files")
    table_count: int = Field(description="Number of tables in schema")
    column_count: int = Field(description="Total number of columns across all tables")

    class Config:
        from_attributes = True


class RefreshSchemaResponse(BaseModel):
    """Response for schema refresh operation."""

    message: str = Field(default="Schema refreshed successfully")
    snapshot: SchemaSnapshotInfo = Field(description="Information about new snapshot")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Schema refreshed successfully",
                "snapshot": {
                    "id": 5,
                    "loaded_at": "2025-10-28T12:00:00Z",
                    "source_hash": "a1b2c3d4...",
                    "table_count": 42,
                    "column_count": 256,
                },
            }
        }


class KBReloadStats(BaseModel):
    """Statistics from knowledge base reload operation."""

    files_loaded: int = Field(description="Number of .sql files loaded")
    embeddings_generated: int = Field(
        description="Number of embeddings generated/updated"
    )
    load_time_ms: int = Field(description="Total load time in milliseconds")


class ReloadKBResponse(BaseModel):
    """Response for knowledge base reload operation."""

    message: str = Field(default="Knowledge base reloaded successfully")
    stats: KBReloadStats = Field(description="Reload statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Knowledge base reloaded successfully",
                "stats": {
                    "files_loaded": 25,
                    "embeddings_generated": 25,
                    "load_time_ms": 3450,
                },
            }
        }


class MetricsRequest(BaseModel):
    """Query parameters for metrics endpoint."""

    weeks: int = Field(
        default=4, ge=1, le=52, description="Number of weeks to retrieve metrics for"
    )


class MetricRow(BaseModel):
    """Single row of metrics data."""

    week_start: str = Field(description="ISO 8601 date for start of week")
    user_id: int | None = Field(
        default=None, description="User ID (null for aggregated metrics)"
    )
    username: str | None = Field(
        default=None, description="Username (null for aggregated metrics)"
    )
    attempts_count: int = Field(description="Number of query attempts")
    executed_count: int = Field(description="Number of queries executed")
    success_count: int = Field(description="Number of successful executions")

    class Config:
        from_attributes = True


class MetricsSummary(BaseModel):
    """Summary statistics across all metrics."""

    total_attempts: int = Field(description="Total query attempts")
    total_executed: int = Field(description="Total queries executed")
    total_success: int = Field(description="Total successful executions")
    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Success rate (success_count / executed_count), 0-1",
    )
    acceptance_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Acceptance rate (executed_count / attempts_count), 0-1",
    )


class MetricsResponse(BaseModel):
    """Response for metrics endpoint."""

    metrics: list[MetricRow] = Field(description="List of metric rows")
    summary: MetricsSummary = Field(description="Summary statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "metrics": [
                    {
                        "week_start": "2025-10-21",
                        "user_id": 1,
                        "username": "john_doe",
                        "attempts_count": 45,
                        "executed_count": 40,
                        "success_count": 38,
                    }
                ],
                "summary": {
                    "total_attempts": 150,
                    "total_executed": 135,
                    "total_success": 120,
                    "success_rate": 0.889,
                    "acceptance_rate": 0.900,
                },
            }
        }
