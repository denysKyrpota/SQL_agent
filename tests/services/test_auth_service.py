"""
Tests for AuthService - authentication and session management.

Tests:
- Password hashing and verification
- Session token generation
- User creation
- User authentication
- Session creation and validation
- Session revocation
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.app.models.user import User, Session as SessionModel
from backend.app.services.auth_service import AuthService, AuthenticationError


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing creates unique hashes."""
        password = "testpassword123"

        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify the same password
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "correctpassword"
        password_hash = AuthService.hash_password(password)

        assert AuthService.verify_password(password, password_hash) is True

    def test_verify_password_failure(self):
        """Test password verification with wrong password."""
        password = "correctpassword"
        password_hash = AuthService.hash_password(password)

        assert AuthService.verify_password("wrongpassword", password_hash) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        result = AuthService.verify_password("anypassword", "not-a-valid-bcrypt-hash")

        assert result is False

    def test_hash_password_empty_string(self):
        """Test hashing empty password."""
        password_hash = AuthService.hash_password("")

        # Should create a valid hash
        assert password_hash
        assert AuthService.verify_password("", password_hash)


class TestSessionToken:
    """Tests for session token generation."""

    def test_generate_session_token(self):
        """Test session token generation."""
        token1 = AuthService.generate_session_token()
        token2 = AuthService.generate_session_token()

        # Tokens should be unique
        assert token1 != token2

        # Tokens should be strings
        assert isinstance(token1, str)
        assert isinstance(token2, str)

        # Tokens should be at least 40 characters
        assert len(token1) >= 40
        assert len(token2) >= 40


class TestCreateUser:
    """Tests for user creation."""

    def test_create_user_success(self, test_db: Session):
        """Test successful user creation."""
        user = AuthService.create_user(
            db=test_db,
            username="newuser",
            password="password123",
            role="user"
        )

        assert user.id is not None
        assert user.username == "newuser"
        assert user.role == "user"
        assert user.active is True
        assert user.password_hash is not None
        # Password should be hashed, not stored in plain text
        assert user.password_hash != "password123"
        # Should be able to verify the password
        assert AuthService.verify_password("password123", user.password_hash)

    def test_create_admin_user(self, test_db: Session):
        """Test admin user creation."""
        admin = AuthService.create_user(
            db=test_db,
            username="adminuser",
            password="admin123",
            role="admin"
        )

        assert admin.role == "admin"
        assert admin.active is True

    def test_create_user_duplicate_username(self, test_db: Session, test_user: User):
        """Test creating user with duplicate username."""
        with pytest.raises(ValueError, match="already exists"):
            AuthService.create_user(
                db=test_db,
                username=test_user.username,  # Same username
                password="differentpass",
                role="user"
            )

    def test_create_user_invalid_role(self, test_db: Session):
        """Test creating user with invalid role."""
        with pytest.raises(ValueError, match="Invalid role"):
            AuthService.create_user(
                db=test_db,
                username="invalidrole",
                password="password123",
                role="superadmin"  # Invalid role
            )

    def test_create_user_default_role(self, test_db: Session):
        """Test user creation with default role."""
        user = AuthService.create_user(
            db=test_db,
            username="defaultuser",
            password="password123"
            # role defaults to "user"
        )

        assert user.role == "user"


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_user_success(self, test_db: Session, test_user: User):
        """Test successful user authentication."""
        user = AuthService.authenticate_user(
            db=test_db,
            username="testuser",
            password="testpassword123"
        )

        assert user.id == test_user.id
        assert user.username == test_user.username

    def test_authenticate_user_wrong_password(self, test_db: Session, test_user: User):
        """Test authentication with wrong password."""
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            AuthService.authenticate_user(
                db=test_db,
                username="testuser",
                password="wrongpassword"
            )

    def test_authenticate_user_nonexistent(self, test_db: Session):
        """Test authentication with non-existent username."""
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            AuthService.authenticate_user(
                db=test_db,
                username="nonexistent",
                password="anypassword"
            )

    def test_authenticate_inactive_user(self, test_db: Session):
        """Test authentication with inactive user."""
        # Create inactive user
        password_hash = AuthService.hash_password("password123")
        inactive_user = User(
            username="inactive",
            password_hash=password_hash,
            role="user",
            active=False
        )
        test_db.add(inactive_user)
        test_db.commit()

        with pytest.raises(AuthenticationError, match="disabled"):
            AuthService.authenticate_user(
                db=test_db,
                username="inactive",
                password="password123"
            )


class TestCreateSession:
    """Tests for session creation."""

    def test_create_session_success(self, test_db: Session, test_user: User):
        """Test successful session creation."""
        session = AuthService.create_session(
            db=test_db,
            user=test_user
        )

        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.token is not None
        assert len(session.token) >= 40
        assert session.expires_at is not None
        assert session.revoked is False

        # Session should expire in the future
        assert session.expires_at > datetime.utcnow()

    def test_create_session_expiration_time(self, test_db: Session, test_user: User):
        """Test session expiration is set correctly."""
        from unittest.mock import patch, MagicMock

        # Mock settings to use 1 hour expiration
        mock_settings = MagicMock()
        mock_settings.session_expiration_hours = 1

        with patch('backend.app.services.auth_service.settings', mock_settings):
            before_creation = datetime.utcnow()
            session = AuthService.create_session(
                db=test_db,
                user=test_user
            )
            after_creation = datetime.utcnow()

            # Session should expire approximately 1 hour from now
            expected_min = before_creation + timedelta(hours=0, minutes=59)
            expected_max = after_creation + timedelta(hours=1, minutes=1)

            assert expected_min <= session.expires_at <= expected_max


class TestValidateSession:
    """Tests for session validation."""

    def test_validate_session_success(self, test_db: Session, test_user: User):
        """Test validating a valid session."""
        session = AuthService.create_session(db=test_db, user=test_user)

        validated_user = AuthService.validate_session(db=test_db, token=session.token)

        assert validated_user is not None
        assert validated_user.id == test_user.id
        assert validated_user.username == test_user.username

    def test_validate_session_invalid_token(self, test_db: Session):
        """Test validation with invalid token."""
        result = AuthService.validate_session(db=test_db, token="invalid-token-12345")

        assert result is None

    def test_validate_session_revoked(self, test_db: Session, test_user: User):
        """Test validation with revoked session."""
        session = AuthService.create_session(db=test_db, user=test_user)

        # Revoke the session
        session.revoked = True
        test_db.commit()

        result = AuthService.validate_session(db=test_db, token=session.token)

        assert result is None

    def test_validate_session_expired(self, test_db: Session, test_user: User):
        """Test validation with expired session."""
        session = AuthService.create_session(db=test_db, user=test_user)

        # Manually expire the session
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        test_db.commit()

        result = AuthService.validate_session(db=test_db, token=session.token)

        assert result is None

    def test_validate_session_inactive_user(self, test_db: Session, test_user: User):
        """Test validation when user becomes inactive."""
        session = AuthService.create_session(db=test_db, user=test_user)

        # Deactivate user
        test_user.active = False
        test_db.commit()

        result = AuthService.validate_session(db=test_db, token=session.token)

        assert result is None


class TestRevokeSession:
    """Tests for session revocation."""

    def test_revoke_session_success(self, test_db: Session, test_user: User):
        """Test successful session revocation."""
        session = AuthService.create_session(db=test_db, user=test_user)

        result = AuthService.revoke_session(db=test_db, token=session.token)

        assert result is True

        # Verify session is actually revoked
        test_db.refresh(session)
        assert session.revoked is True

    def test_revoke_session_invalid_token(self, test_db: Session):
        """Test revoking non-existent session."""
        result = AuthService.revoke_session(db=test_db, token="invalid-token")

        assert result is False

    def test_revoke_session_already_revoked(self, test_db: Session, test_user: User):
        """Test revoking already revoked session."""
        session = AuthService.create_session(db=test_db, user=test_user)

        # Revoke once
        AuthService.revoke_session(db=test_db, token=session.token)

        # Revoke again
        result = AuthService.revoke_session(db=test_db, token=session.token)

        # Should still return True
        assert result is True


class TestRevokeAllUserSessions:
    """Tests for revoking all sessions for a user."""

    def test_revoke_all_user_sessions(self, test_db: Session, test_user: User):
        """Test revoking all sessions for a user."""
        # Create multiple sessions
        session1 = AuthService.create_session(db=test_db, user=test_user)
        session2 = AuthService.create_session(db=test_db, user=test_user)
        session3 = AuthService.create_session(db=test_db, user=test_user)

        count = AuthService.revoke_all_user_sessions(db=test_db, user_id=test_user.id)

        assert count == 3

        # Verify all sessions are revoked
        test_db.refresh(session1)
        test_db.refresh(session2)
        test_db.refresh(session3)

        assert session1.revoked is True
        assert session2.revoked is True
        assert session3.revoked is True

    def test_revoke_all_user_sessions_no_sessions(self, test_db: Session, test_user: User):
        """Test revoking sessions when user has no active sessions."""
        count = AuthService.revoke_all_user_sessions(db=test_db, user_id=test_user.id)

        assert count == 0

    def test_revoke_all_user_sessions_already_revoked(self, test_db: Session, test_user: User):
        """Test revoking when all sessions already revoked."""
        session = AuthService.create_session(db=test_db, user=test_user)
        session.revoked = True
        test_db.commit()

        count = AuthService.revoke_all_user_sessions(db=test_db, user_id=test_user.id)

        assert count == 0

    def test_revoke_all_user_sessions_mixed(self, test_db: Session, test_user: User):
        """Test revoking when some sessions already revoked."""
        session1 = AuthService.create_session(db=test_db, user=test_user)
        session2 = AuthService.create_session(db=test_db, user=test_user)

        # Revoke one manually
        session1.revoked = True
        test_db.commit()

        count = AuthService.revoke_all_user_sessions(db=test_db, user_id=test_user.id)

        # Should only revoke the one active session
        assert count == 1

        test_db.refresh(session2)
        assert session2.revoked is True
