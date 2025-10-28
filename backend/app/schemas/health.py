"""
Health check schemas for system monitoring.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ServiceStatusEnum(str, Enum):
    """Status of a service."""

    UP = "up"
    DOWN = "down"


class ServiceStatus(BaseModel):
    """Status information for individual services."""

    database: ServiceStatusEnum = Field(description="SQLite database status")
    postgresql: ServiceStatusEnum = Field(description="PostgreSQL database status")
    llm_api: ServiceStatusEnum = Field(description="LLM API status")


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""

    status: str = Field(description="Overall health status")
    timestamp: str = Field(description="ISO 8601 timestamp of health check")
    services: ServiceStatus = Field(description="Status of individual services")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-28T12:00:00Z",
                "services": {
                    "database": "up",
                    "postgresql": "up",
                    "llm_api": "up",
                },
            }
        }
