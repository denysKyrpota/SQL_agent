"""
Pytest configuration and shared fixtures for all tests.

Provides:
- Test database setup/teardown
- Test client with authentication
- Mock services for unit tests
- Sample data fixtures
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import Settings, get_settings
from backend.app.database import Base
from backend.app.dependencies import get_current_user, get_db
from backend.app.main import app
from backend.app.models.query import QueryAttempt, QueryResultsManifest
from backend.app.models.user import User
from backend.app.services.auth_service import AuthService


# =============================================================================
# Test Database Setup
# =============================================================================


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a fresh test database for each test function.

    Uses in-memory SQLite with StaticPool to ensure the database
    persists for the duration of the test.
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    FastAPI test client with test database dependency override.
    """

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def test_user(test_db: Session) -> User:
    """
    Create a test user (non-admin).
    """
    auth_service = AuthService()
    password_hash = auth_service.hash_password("testpassword123")

    user = User(
        username="testuser",
        password_hash=password_hash,
        role="user",
        active=True,
    )

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def test_admin(test_db: Session) -> User:
    """
    Create a test admin user.
    """
    auth_service = AuthService()
    password_hash = auth_service.hash_password("adminpassword123")

    admin = User(
        username="adminuser",
        password_hash=password_hash,
        role="admin",
        active=True,
    )

    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)

    return admin


@pytest.fixture
def authenticated_client(client: TestClient, test_user: User, test_db: Session) -> TestClient:
    """
    Test client with authenticated user (non-admin).
    """
    # Override get_current_user to return test_user
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    return client


@pytest.fixture
def admin_client(client: TestClient, test_admin: User, test_db: Session) -> TestClient:
    """
    Test client with authenticated admin user.
    """
    # Override get_current_user to return test_admin
    def override_get_current_user():
        return test_admin

    app.dependency_overrides[get_current_user] = override_get_current_user

    return client


# =============================================================================
# Query Fixtures
# =============================================================================


@pytest.fixture
def sample_query_attempt(test_db: Session, test_user: User) -> QueryAttempt:
    """
    Create a sample query attempt with generated SQL.
    """
    query = QueryAttempt(
        user_id=test_user.id,
        natural_language_query="Show me all active users",
        generated_sql="SELECT * FROM users WHERE active = true;",
        status="not_executed",
        created_at=datetime.utcnow(),
        generated_at=datetime.utcnow(),
        generation_ms=1500,
        error_message=None,
    )

    test_db.add(query)
    test_db.commit()
    test_db.refresh(query)

    return query


@pytest.fixture
def executed_query_with_results(
    test_db: Session, test_user: User
) -> tuple[QueryAttempt, QueryResultsManifest]:
    """
    Create an executed query with results manifest.
    """
    # Create query attempt
    query = QueryAttempt(
        user_id=test_user.id,
        natural_language_query="List all users",
        generated_sql="SELECT id, username, email FROM users;",
        status="success",
        created_at=datetime.utcnow(),
        generated_at=datetime.utcnow(),
        executed_at=datetime.utcnow(),
        generation_ms=1200,
        execution_ms=150,
        error_message=None,
    )

    test_db.add(query)
    test_db.commit()
    test_db.refresh(query)

    # Create results manifest
    columns = ["id", "username", "email"]
    rows = [
        [1, "alice", "alice@example.com"],
        [2, "bob", "bob@example.com"],
        [3, "charlie", "charlie@example.com"],
    ]

    manifest = QueryResultsManifest(
        attempt_id=query.id,
        columns_json=json.dumps(columns),
        results_json=json.dumps(rows),
        total_rows=3,
        page_size=500,
        page_count=1,
        created_at=datetime.utcnow(),
    )

    test_db.add(manifest)
    test_db.commit()
    test_db.refresh(manifest)

    return query, manifest


@pytest.fixture
def failed_query(test_db: Session, test_user: User) -> QueryAttempt:
    """
    Create a query attempt that failed during generation.
    """
    query = QueryAttempt(
        user_id=test_user.id,
        natural_language_query="Invalid query that will fail",
        generated_sql=None,
        status="failed_generation",
        created_at=datetime.utcnow(),
        generated_at=None,
        generation_ms=2000,
        error_message="LLM service unavailable",
    )

    test_db.add(query)
    test_db.commit()
    test_db.refresh(query)

    return query


# =============================================================================
# Mock Service Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_response():
    """
    Sample LLM response for testing.
    """
    return {
        "stage1_tables": ["users", "sessions"],
        "stage2_sql": "SELECT u.id, u.username FROM users u WHERE u.active = true;",
    }


@pytest.fixture
def mock_schema_data():
    """
    Sample schema data for testing.
    """
    return {
        "tables": {
            "users": {
                "columns": [
                    {"name": "id", "type": "integer", "nullable": False},
                    {"name": "username", "type": "varchar", "nullable": False},
                    {"name": "email", "type": "varchar", "nullable": False},
                    {"name": "active", "type": "boolean", "nullable": False},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
            },
            "sessions": {
                "columns": [
                    {"name": "id", "type": "integer", "nullable": False},
                    {"name": "user_id", "type": "integer", "nullable": False},
                    {"name": "token", "type": "varchar", "nullable": False},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [
                    {"column": "user_id", "references_table": "users", "references_column": "id"}
                ],
            },
        },
        "table_names": ["users", "sessions"],
    }


@pytest.fixture
def mock_kb_examples():
    """
    Sample knowledge base examples for testing.
    """
    return [
        {
            "filename": "active_users.sql",
            "title": "Active Users",
            "sql": "SELECT * FROM users WHERE active = true;",
        },
        {
            "filename": "user_sessions.sql",
            "title": "User Sessions",
            "sql": "SELECT u.username, s.token FROM users u JOIN sessions s ON u.id = s.user_id;",
        },
    ]


# =============================================================================
# Environment Override
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def test_settings():
    """
    Override settings for testing.
    """
    test_settings = Settings(
        database_url="sqlite:///:memory:",
        secret_key="test-secret-key-for-testing-only",
        openai_api_key="test-openai-key",  # Will be mocked
        postgres_url="postgresql://test:test@localhost:5432/test",  # Will be mocked
        session_expiration_hours=1,
    )

    app.dependency_overrides[get_settings] = lambda: test_settings

    return test_settings
