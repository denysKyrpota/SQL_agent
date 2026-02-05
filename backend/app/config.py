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

    # Choose between standard OpenAI or Azure OpenAI
    # If azure_openai_endpoint is set, Azure OpenAI will be used
    # Otherwise, standard OpenAI will be used

    # Standard OpenAI API key
    openai_api_key: str = ""

    # OpenAI model to use for SQL generation (standard OpenAI)
    openai_model: str = "gpt-4"

    # Maximum tokens for OpenAI API responses
    openai_max_tokens: int = 1000

    # Temperature for OpenAI API (0.0 = deterministic, 1.0 = creative)
    # Note: Some Azure deployments may not support all temperature values
    openai_temperature: float = 0.0

    # OpenAI model for embeddings
    openai_embedding_model: str = "text-embedding-3-small"

    # Similarity threshold for RAG (0.0 to 1.0)
    # If similarity is above this threshold, return the example directly
    rag_similarity_threshold: float = 0.85

    # =========================================================================
    # Azure OpenAI Configuration (Optional)
    # =========================================================================

    # Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com)
    # If set, Azure OpenAI will be used instead of standard OpenAI
    azure_openai_endpoint: str = ""

    # Azure OpenAI API key
    azure_openai_api_key: str = ""

    # Azure OpenAI deployment name for chat completions
    azure_openai_deployment: str = ""

    # Azure OpenAI API version
    azure_openai_api_version: str = "2024-02-15-preview"

    # Azure OpenAI deployment name for embeddings (optional, uses chat deployment if not set)
    azure_openai_embedding_deployment: str = ""

    # Separate Azure OpenAI endpoint for embeddings (if different from chat endpoint)
    # Use this when embeddings are on a different Azure resource
    azure_openai_embedding_endpoint: str = ""

    # Separate API key for embedding endpoint (if different from chat API key)
    azure_openai_embedding_api_key: str = ""

    # API version for embedding endpoint (if different from chat API version)
    azure_openai_embedding_api_version: str = "2023-05-15"

    # Whether Azure deployment supports temperature parameter (many don't)
    # Set to False to skip temperature and avoid 400 errors on first request
    azure_openai_supports_temperature: bool = False

    @property
    def has_separate_embedding_endpoint(self) -> bool:
        """Check if a separate embedding endpoint is configured."""
        return bool(
            self.azure_openai_embedding_endpoint
            and self.azure_openai_embedding_api_key
            and self.azure_openai_embedding_deployment
        )

    @property
    def use_azure_openai(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_deployment
        )

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
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

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
