"""
Authentication-related schemas for login, logout, and session management.
"""

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import UserRole


class LoginRequest(BaseModel):
    """Request payload for user login."""

    username: str = Field(
        min_length=1, max_length=255, description="Username for authentication"
    )
    password: str = Field(
        min_length=8, max_length=255, description="User password"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username is not empty or only whitespace."""
        if not v or not v.strip():
            raise ValueError("Username cannot be empty or only whitespace")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets minimum requirements."""
        if not v or not v.strip():
            raise ValueError("Password cannot be empty or only whitespace")
        return v

    class Config:
        json_schema_extra = {
            "example": {"username": "john_doe", "password": "SecurePass123"}
        }


class UserResponse(BaseModel):
    """User information in API responses (excludes sensitive data)."""

    id: int = Field(description="User ID")
    username: str = Field(description="Username")
    role: UserRole = Field(description="User role (admin or user)")
    active: bool = Field(description="Whether user account is active")

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models


class SessionInfo(BaseModel):
    """Session information in API responses."""

    token: str = Field(description="Session token")
    expires_at: str = Field(description="ISO 8601 timestamp when session expires")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "a1b2c3d4e5f6...",
                "expires_at": "2025-10-28T20:30:00Z",
            }
        }


class SessionInfoWithoutToken(BaseModel):
    """Session information without token (for session validation responses)."""

    expires_at: str = Field(description="ISO 8601 timestamp when session expires")


class LoginResponse(BaseModel):
    """Response payload for successful login."""

    user: UserResponse = Field(description="Authenticated user information")
    session: SessionInfo = Field(description="Session details including token")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "role": "user",
                    "active": True,
                },
                "session": {
                    "token": "a1b2c3d4e5f6...",
                    "expires_at": "2025-10-28T20:30:00Z",
                },
            }
        }


class LogoutResponse(BaseModel):
    """Response payload for logout."""

    message: str = Field(default="Logged out successfully")


class SessionResponse(BaseModel):
    """Response payload for session validation."""

    user: UserResponse = Field(description="Current user information")
    session: SessionInfoWithoutToken = Field(
        description="Session details (without token)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "role": "user",
                    "active": True,
                },
                "session": {"expires_at": "2025-10-28T20:30:00Z"},
            }
        }
