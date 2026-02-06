"""
Database session management and initialization.

Provides SQLAlchemy engine, session factory, and database initialization utilities.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.models.base import Base

logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.database_url else {}
    ),
)


# Enable foreign key constraints for SQLite
# Only listen to our specific SQLite engine, not all engines globally
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    # Check if this is actually a SQLite connection
    if hasattr(dbapi_conn, "execute"):
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            # Not a SQLite connection, ignore
            pass


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Yields a SQLAlchemy session and ensures it's closed after use.

    Yields:
        Session: SQLAlchemy database session

    Example:
        ```python
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function should be called on application startup if tables don't exist.
    In production, use Alembic migrations instead.

    Note:
        This only creates tables if they don't exist. It doesn't perform migrations.
    """
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data! Only use in development/testing.
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")


def reset_db() -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data! Only use in development/testing.
    """
    logger.warning("Resetting database...")
    drop_db()
    init_db()
    logger.info("Database reset complete")
