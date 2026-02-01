"""
Tests for chat API endpoints.

Tests the conversational SQL generation endpoints including:
- POST /chat/messages - Send message and get AI response
- POST /chat/messages/from-example - Load KB example into chat
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.chat import Conversation
from backend.app.models.query import QueryAttempt


class TestLoadExampleEndpoint:
    """Tests for POST /chat/messages/from-example endpoint."""

    def test_load_example_success(
        self, authenticated_client: TestClient, test_user: User, test_db: Session
    ):
        """Test successfully loading a KB example into chat."""
        # Use an actual KB example file
        response = authenticated_client.post(
            "/api/chat/messages/from-example",
            json={"filename": "drivers_with_current_availability.sql"},
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "conversation_id" in data
        assert "user_message" in data
        assert "assistant_message" in data

        # Verify user message content
        assert data["user_message"]["role"] == "user"
        assert "Show me:" in data["user_message"]["content"]

        # Verify assistant message contains SQL
        assert data["assistant_message"]["role"] == "assistant"
        assert "SELECT" in data["assistant_message"]["content"]
        assert "```sql" in data["assistant_message"]["content"]

        # Verify assistant message has query_attempt_id
        assert data["assistant_message"]["query_attempt_id"] is not None

    def test_load_example_not_found(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test loading a non-existent KB example returns 404."""
        response = authenticated_client.post(
            "/api/chat/messages/from-example",
            json={"filename": "nonexistent_example.sql"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_load_example_into_existing_conversation(
        self, authenticated_client: TestClient, test_user: User, test_db: Session
    ):
        """Test loading KB example into an existing conversation."""
        # Create existing conversation
        conversation = Conversation(
            user_id=test_user.id,
            title="Existing Conversation",
            is_active=True,
        )
        test_db.add(conversation)
        test_db.commit()
        test_db.refresh(conversation)

        response = authenticated_client.post(
            "/api/chat/messages/from-example",
            json={
                "filename": "drivers_with_current_availability.sql",
                "conversation_id": conversation.id,
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify conversation ID matches
        assert data["conversation_id"] == conversation.id

    def test_load_example_wrong_conversation_returns_404(
        self, authenticated_client: TestClient, test_user: User, test_db: Session
    ):
        """Test loading into another user's conversation returns 404."""
        # Create conversation for different user
        other_user = User(
            username="otheruser",
            password_hash="hash",
            role="user",
            active=True,
        )
        test_db.add(other_user)
        test_db.commit()
        test_db.refresh(other_user)

        conversation = Conversation(
            user_id=other_user.id,
            title="Other User's Conversation",
            is_active=True,
        )
        test_db.add(conversation)
        test_db.commit()
        test_db.refresh(conversation)

        response = authenticated_client.post(
            "/api/chat/messages/from-example",
            json={
                "filename": "drivers_with_current_availability.sql",
                "conversation_id": conversation.id,
            },
        )

        assert response.status_code == 404
        detail = response.json()["detail"].lower()
        assert "not found" in detail or "access denied" in detail

    def test_load_example_creates_query_attempt_with_zero_generation_ms(
        self, authenticated_client: TestClient, test_user: User, test_db: Session
    ):
        """Test that pre-loaded examples have generation_ms=0."""
        response = authenticated_client.post(
            "/api/chat/messages/from-example",
            json={"filename": "drivers_with_current_availability.sql"},
        )

        assert response.status_code == 201
        data = response.json()

        # Get the query attempt from DB
        query_attempt_id = data["assistant_message"]["query_attempt_id"]
        query_attempt = (
            test_db.query(QueryAttempt).filter(QueryAttempt.id == query_attempt_id).first()
        )

        # Verify generation_ms is 0 (pre-loaded)
        assert query_attempt is not None
        assert query_attempt.generation_ms == 0

    def test_load_example_unauthenticated(self, client: TestClient):
        """Test that unauthenticated requests are rejected."""
        response = client.post(
            "/api/chat/messages/from-example",
            json={"filename": "drivers_with_current_availability.sql"},
        )

        # Should return 401 or 403
        assert response.status_code in [401, 403]
