"""
User and Session ORM models.

Handles user authentication and session management.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class User(Base):
    """
    User account model.

    Stores user credentials and role-based access control.
    Password hashes are stored using bcrypt.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication fields
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Role-based access control
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")

    # Account status
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    query_attempts: Mapped[list["QueryAttempt"]] = relationship(
        "QueryAttempt", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r}, role={self.role!r})>"


class Session(Base):
    """
    User session model.

    Tracks active user sessions with expiration and revocation support.
    Sessions expire after 8 hours by default.
    """

    __tablename__ = "sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to users
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Session token (JWT or secure random string)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Revocation flag for manual logout
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"

    def is_valid(self) -> bool:
        """Check if session is still valid (not expired and not revoked)."""
        return not self.revoked and datetime.utcnow() < self.expires_at
