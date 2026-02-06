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

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import queries
from backend.app.config import get_settings

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

# CORS Configuration - uses CORS_ORIGINS_STR from settings (.env)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
from backend.app.api import auth  # noqa: E402

app.include_router(auth.router, prefix="/api", tags=["Authentication"])

# Query workflow endpoints
app.include_router(queries.router, prefix="/api", tags=["Queries"])

# Chat endpoints
from backend.app.api import chat  # noqa: E402

app.include_router(chat.router, prefix="/api", tags=["Chat"])

# Admin endpoints
from backend.app.api import admin  # noqa: E402

app.include_router(admin.router, prefix="/api", tags=["Admin"])

# TODO: Add health check endpoint
# from backend.app.api import health
# app.include_router(health.router, prefix="/api", tags=["Health"])


# ============================================================================
# Static File Serving (Production Deployment)
# ============================================================================

if settings.serve_frontend:
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        logger.info(f"Serving frontend from {frontend_dist}")
        app.mount(
            "/assets",
            StaticFiles(directory=frontend_dist / "assets"),
            name="static-assets",
        )

        @app.get("/{path:path}", include_in_schema=False)
        async def serve_spa(path: str):
            """Serve the React SPA. Returns index.html for all non-API, non-asset routes."""
            file = frontend_dist / path
            if file.exists() and file.is_file():
                return FileResponse(file)
            return FileResponse(frontend_dist / "index.html")
    else:
        logger.warning(
            f"SERVE_FRONTEND=true but {frontend_dist} not found. "
            "Run 'npm run build' in frontend/ first."
        )

        @app.get("/", include_in_schema=False)
        async def root():
            return {"error": "Frontend not built. Run 'npm run build' in frontend/."}
else:

    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint - API info when frontend serving is disabled."""
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
