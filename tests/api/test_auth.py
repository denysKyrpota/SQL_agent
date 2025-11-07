"""
Tests for authentication API endpoints.

Tests:
- POST /api/auth/login
- POST /api/auth/logout
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User


class TestAuthLogin:
    """Tests for POST /api/auth/login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "session" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["role"] == "user"
        assert data["session"]["token"] is not None

    def test_login_invalid_username(self, client: TestClient):
        """Test login with non-existent username."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "anypassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_missing_credentials(self, client: TestClient):
        """Test login with missing fields."""
        response = client.post("/api/auth/login", json={})

        assert response.status_code == 422  # Validation error

    def test_login_inactive_user(self, client: TestClient, test_db: Session):
        """Test login with inactive user account."""
        from backend.app.services.auth_service import AuthService

        auth_service = AuthService()
        hashed_password = auth_service.hash_password("password123")

        inactive_user = User(
            username="inactive",
            password_hash=hashed_password,
            role="user",
            active=False,
        )

        test_db.add(inactive_user)
        test_db.commit()

        response = client.post(
            "/api/auth/login",
            json={"username": "inactive", "password": "password123"},
        )

        assert response.status_code == 401


class TestAuthLogout:
    """Tests for POST /api/auth/logout endpoint."""

    def test_logout_success(self, client: TestClient, test_user: User, test_db: Session):
        """Test successful logout."""
        from backend.app.services.auth_service import AuthService

        # Create a session for the user
        auth_service = AuthService()
        session = auth_service.create_session(db=test_db, user=test_user)

        # Set the session cookie
        client.cookies.set("session_token", session.token)

        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_logout_unauthenticated(self, client: TestClient):
        """Test logout without authentication."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401
