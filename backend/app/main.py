"""
FastAPI application entry point for SQL AI Agent.

This module initializes the FastAPI application with:
- CORS middleware for frontend communication
- Security headers
- API route registration
- Exception handlers
- Logging configuration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api import queries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown operations:
    - Database connection initialization
    - Cache warming (schema, knowledge base)
    - Cleanup on shutdown
    """
    logger.info("Starting SQL AI Agent API server")

    # Startup
    from backend.app.database import init_db

    # Initialize database (create tables if they don't exist)
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # TODO: Load schema snapshot into memory
    # TODO: Load knowledge base examples and embeddings

    yield

    # Shutdown
    logger.info("Shutting down SQL AI Agent API server")
    # Database connections are automatically closed by SQLAlchemy
    # TODO: Clear caches


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="SQL AI Agent API",
    description="REST API for natural language to SQL generation and execution",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS Configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:5173",  # Vite development server (alternative)
    ],
    allow_credentials=True,  # Allow cookies for session authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions as 400 Bad Request."""
    logger.warning(f"ValueError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_code": "VALIDATION_ERROR"},
    )


# ============================================================================
# Route Registration
# ============================================================================

# Authentication endpoints
from backend.app.api import auth

app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# Query workflow endpoints
app.include_router(queries.router, prefix="/api", tags=["Queries"])

# TODO: Add admin endpoints
# from backend.app.api import admin
# app.include_router(admin.router, prefix="/api", tags=["Admin"])

# TODO: Add health check endpoint
# from backend.app.api import health
# app.include_router(health.router, prefix="/api", tags=["Health"])


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint - redirects to API documentation.

    Returns:
        Simple welcome message with links to documentation
    """
    return {
        "message": "SQL AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server on http://localhost:8000")

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info",
    )
