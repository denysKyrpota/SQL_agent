"""
Application configuration using Pydantic settings.

Loads configuration from environment variables with sensible defaults.
Supports both development and production environments.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be defined in a .env file in the project root.
    All settings have defaults suitable for local development.
    """

    # =========================================================================
    # Database Configuration
    # =========================================================================

    # SQLite database file path
    # Default: sqlite.db in the project root
    database_url: str = "sqlite:///./sqlite.db"

    # Enable SQLAlchemy echo for debugging SQL queries
    # Set to True in development to see all SQL statements
    database_echo: bool = False

    # =========================================================================
    # PostgreSQL Target Database (for query execution)
    # =========================================================================

    # PostgreSQL database connection string
    # Format: postgresql://user:password@host:port/database
    postgres_url: str = ""

    # PostgreSQL query execution timeout in seconds
    postgres_timeout: int = 30

    # =========================================================================
    # OpenAI Configuration
    # =========================================================================

    # OpenAI API key for LLM-powered SQL generation
    openai_api_key: str = ""

    # OpenAI model to use for SQL generation
    openai_model: str = "gpt-4"

    # Maximum tokens for OpenAI API responses
    openai_max_tokens: int = 1000

    # Temperature for OpenAI API (0.0 = deterministic, 1.0 = creative)
    openai_temperature: float = 0.0

    # =========================================================================
    # Authentication Configuration
    # =========================================================================

    # Secret key for JWT token generation
    # IMPORTANT: Change this in production to a secure random string
    secret_key: str = "change-this-secret-key-in-production"

    # JWT algorithm
    jwt_algorithm: str = "HS256"

    # Session expiration time in hours
    session_expiration_hours: int = 8

    # =========================================================================
    # Application Configuration
    # =========================================================================

    # Application environment (development, staging, production)
    environment: str = "development"

    # Enable CORS for frontend development servers
    cors_enabled: bool = True

    # Allowed CORS origins (comma-separated string)
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"

    # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    # =========================================================================
    # Rate Limiting Configuration
    # =========================================================================

    # Maximum number of queries per minute per user
    rate_limit_queries_per_minute: int = 10

    # =========================================================================
    # File Storage Configuration
    # =========================================================================

    # Directory for storing CSV exports
    export_directory: Path = Path("./exports")

    # Directory for knowledge base SQL examples
    kb_directory: Path = Path("./knowledge_base")

    # =========================================================================
    # Pydantic Settings Configuration
    # =========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses functools.lru_cache to ensure settings are loaded only once
    and reused across the application.

    Returns:
        Settings: Application configuration
    """
    return Settings()
