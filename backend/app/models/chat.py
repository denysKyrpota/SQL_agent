"""
Chat ORM models.

Handles conversational SQL generation with message history.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.query import QueryAttempt
    from backend.app.models.user import User


class Conversation(Base):
    """
    Conversation thread model.

    Stores conversation metadata for chat-based SQL generation.
    Each user can have multiple conversations, and each conversation
    contains multiple messages.
    """

    __tablename__ = "conversations"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to users
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Conversation metadata
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title!r})>"


class Message(Base):
    """
    Chat message model.

    Stores individual messages in a conversation thread.
    Messages can be from user, assistant, or system.
    Can be linked to QueryAttempt when SQL is generated.
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to conversations
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )

    # Message content
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional link to query attempt (when SQL is generated)
    query_attempt_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("query_attempts.id", ondelete="SET NULL"), nullable=True
    )

    # Message editing/regeneration tracking
    parent_message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    is_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_regenerated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Metadata (JSON stored as text) - renamed to avoid conflict with SQLAlchemy's metadata
    message_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
    query_attempt: Mapped[Optional["QueryAttempt"]] = relationship(
        "QueryAttempt", back_populates="message"
    )
    parent_message: Mapped[Optional["Message"]] = relationship(
        "Message", remote_side=[id], backref="child_messages"
    )

    # Table-level constraints
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role!r})>"
