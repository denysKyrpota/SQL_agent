"""
Chat-related schemas for conversational SQL generation.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.common import PaginationMetadata


class CreateConversationRequest(BaseModel):
    """Request payload for creating a new conversation."""

    title: str | None = Field(
        default=None,
        max_length=200,
        description="Optional title for the conversation",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Customer Analytics Queries"
            }
        }


class ConversationResponse(BaseModel):
    """Response for a conversation."""

    id: int = Field(description="Conversation ID")
    user_id: int = Field(description="User ID who owns this conversation")
    title: str | None = Field(default=None, description="Conversation title")
    is_active: bool = Field(description="Whether conversation is active")
    created_at: str = Field(description="ISO 8601 timestamp when created")
    updated_at: str = Field(description="ISO 8601 timestamp when last updated")
    message_count: int = Field(default=0, description="Number of messages in conversation")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "Customer Analytics",
                "is_active": True,
                "created_at": "2025-12-07T10:00:00Z",
                "updated_at": "2025-12-07T10:15:00Z",
                "message_count": 5,
            }
        }


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: list[ConversationResponse] = Field(
        description="List of conversations"
    )
    pagination: PaginationMetadata = Field(description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "title": "Customer Analytics",
                        "is_active": True,
                        "created_at": "2025-12-07T10:00:00Z",
                        "updated_at": "2025-12-07T10:15:00Z",
                        "message_count": 5,
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_count": 1,
                    "total_pages": 1,
                },
            }
        }


class MessageResponse(BaseModel):
    """Response for a chat message."""

    id: int = Field(description="Message ID")
    conversation_id: int = Field(description="Conversation ID")
    role: str = Field(description="Message role (user, assistant, or system)")
    content: str = Field(description="Message content")
    query_attempt_id: int | None = Field(
        default=None,
        description="Query attempt ID if SQL was generated in this message"
    )
    parent_message_id: int | None = Field(
        default=None,
        description="Parent message ID if this is an edited or regenerated message"
    )
    is_edited: bool = Field(
        default=False,
        description="Whether this message was edited"
    )
    is_regenerated: bool = Field(
        default=False,
        description="Whether this message was regenerated"
    )
    created_at: str = Field(description="ISO 8601 timestamp when created")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata (e.g., token count, model)"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "conversation_id": 1,
                "role": "user",
                "content": "Show me all active customers",
                "query_attempt_id": None,
                "parent_message_id": None,
                "is_edited": False,
                "is_regenerated": False,
                "created_at": "2025-12-07T10:00:00Z",
                "metadata": None,
            }
        }


class SendMessageRequest(BaseModel):
    """Request payload for sending a message in a conversation."""

    content: str = Field(
        min_length=1,
        max_length=5000,
        description="Message content"
    )
    conversation_id: int | None = Field(
        default=None,
        description="Conversation ID (if None, creates new conversation)"
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Validate content is not only whitespace."""
        if not v.strip():
            raise ValueError("Message content cannot be only whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Show me all active customers from the last month",
                "conversation_id": 1,
            }
        }


class SendMessageResponse(BaseModel):
    """Response for sending a message (includes user message and assistant response)."""

    conversation_id: int = Field(description="Conversation ID")
    user_message: MessageResponse = Field(description="User's message")
    assistant_message: MessageResponse = Field(description="Assistant's response")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": 1,
                "user_message": {
                    "id": 1,
                    "conversation_id": 1,
                    "role": "user",
                    "content": "Show me all active customers",
                    "query_attempt_id": None,
                    "parent_message_id": None,
                    "is_edited": False,
                    "is_regenerated": False,
                    "created_at": "2025-12-07T10:00:00Z",
                    "metadata": None,
                },
                "assistant_message": {
                    "id": 2,
                    "conversation_id": 1,
                    "role": "assistant",
                    "content": "I'll generate a SQL query to show all active customers.",
                    "query_attempt_id": 42,
                    "parent_message_id": None,
                    "is_edited": False,
                    "is_regenerated": False,
                    "created_at": "2025-12-07T10:00:02Z",
                    "metadata": {"tokens": 250, "model": "gpt-4"},
                },
            }
        }


class ConversationMessagesResponse(BaseModel):
    """Response for getting all messages in a conversation."""

    conversation_id: int = Field(description="Conversation ID")
    messages: list[MessageResponse] = Field(description="List of messages")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": 1,
                "messages": [
                    {
                        "id": 1,
                        "conversation_id": 1,
                        "role": "user",
                        "content": "Show me all active customers",
                        "query_attempt_id": None,
                        "parent_message_id": None,
                        "is_edited": False,
                        "is_regenerated": False,
                        "created_at": "2025-12-07T10:00:00Z",
                        "metadata": None,
                    }
                ],
            }
        }


class RegenerateMessageRequest(BaseModel):
    """Request payload for regenerating an assistant message."""

    pass


class EditMessageRequest(BaseModel):
    """Request payload for editing a user message."""

    content: str = Field(
        min_length=1,
        max_length=5000,
        description="New message content"
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Validate content is not only whitespace."""
        if not v.strip():
            raise ValueError("Message content cannot be only whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Show me all active customers from the last 30 days"
            }
        }
