"""
Authentication service for user login, logout, and session management.

Handles password hashing, session creation, and validation.
"""

import logging
import secrets
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.user import Session as SessionModel
from backend.app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthService:
    """Service for handling user authentication and session management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            str: Bcrypt password hash
        """
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
        return password_hash.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against a bcrypt hash.

        Args:
            password: Plain text password to verify
            password_hash: Bcrypt hash to compare against

        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a secure random session token.

        Returns:
            str: Secure random token (64 characters)
        """
        return secrets.token_urlsafe(48)

    @staticmethod
    def create_user(
        db: Session, username: str, password: str, role: str = "user"
    ) -> User:
        """
        Create a new user account.

        Args:
            db: Database session
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role ('user' or 'admin')

        Returns:
            User: Created user object

        Raises:
            ValueError: If username already exists
        """
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        # Validate role
        if role not in ["user", "admin"]:
            raise ValueError(f"Invalid role: {role}")

        # Create user with hashed password
        password_hash = AuthService.hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"User created: {username} (role: {role})")
        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        """
        Authenticate a user by username and password.

        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password

        Returns:
            User: Authenticated user object

        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user by username
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            raise AuthenticationError("Invalid username or password")

        # Check if user is active
        if not user.active:
            logger.warning(f"Login attempt for inactive user: {username}")
            raise AuthenticationError("Account is disabled")

        # Verify password
        if not AuthService.verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for user: {username}")
            raise AuthenticationError("Invalid username or password")

        logger.info(f"User authenticated: {username}")
        return user

    @staticmethod
    def create_session(db: Session, user: User) -> SessionModel:
        """
        Create a new session for an authenticated user.

        Args:
            db: Database session
            user: Authenticated user

        Returns:
            SessionModel: Created session object
        """
        # Generate session token
        token = AuthService.generate_session_token()

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(
            hours=settings.session_expiration_hours
        )

        # Create session
        session = SessionModel(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            revoked=False,
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(
            f"Session created for user {user.username} (expires: {expires_at})"
        )
        return session

    @staticmethod
    def validate_session(db: Session, token: str) -> User | None:
        """
        Validate a session token and return the associated user.

        Args:
            db: Database session
            token: Session token to validate

        Returns:
            User | None: User object if session is valid, None otherwise
        """
        # Find session by token
        session = db.query(SessionModel).filter(SessionModel.token == token).first()

        if not session:
            return None

        # Check if session is valid
        if not session.is_valid():
            logger.debug(f"Invalid session token (expired or revoked)")
            return None

        # Get user
        user = db.query(User).filter(User.id == session.user_id).first()

        if not user or not user.active:
            return None

        return user

    @staticmethod
    def revoke_session(db: Session, token: str) -> bool:
        """
        Revoke a session (logout).

        Args:
            db: Database session
            token: Session token to revoke

        Returns:
            bool: True if session was revoked, False if not found
        """
        session = db.query(SessionModel).filter(SessionModel.token == token).first()

        if not session:
            return False

        session.revoked = True
        db.commit()

        logger.info(f"Session revoked for user_id={session.user_id}")
        return True

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: int) -> int:
        """
        Revoke all sessions for a user.

        Args:
            db: Database session
            user_id: User ID whose sessions should be revoked

        Returns:
            int: Number of sessions revoked
        """
        count = (
            db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.revoked == False)
            .update({"revoked": True})
        )
        db.commit()

        logger.info(f"Revoked {count} sessions for user_id={user_id}")
        return count
