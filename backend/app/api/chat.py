"""
API route handlers for chat-based conversational SQL generation.

Handles:
- POST /chat/conversations - Create new conversation
- GET /chat/conversations - List user's conversations
- GET /chat/conversations/{id}/messages - Get conversation messages
- POST /chat/messages - Send message and get AI response
- PUT /chat/messages/{id}/regenerate - Regenerate assistant message
- PUT /chat/messages/{id} - Edit user message
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.chat import (
    CreateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
    SendMessageRequest,
    SendMessageResponse,
    ConversationMessagesResponse,
    RegenerateMessageRequest,
    EditMessageRequest,
    MessageResponse,
)
from backend.app.schemas.common import PaginationMetadata
from backend.app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize chat service
chat_service = ChatService()


# ============================================================================
# Route Handlers
# ============================================================================


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    responses={
        201: {
            "description": "Conversation created successfully",
        },
        401: {"description": "Not authenticated"},
    },
)
async def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: CreateConversationRequest | None = None,
):
    """
    Create a new conversation thread.

    Args:
        request: Optional conversation creation request with title
        current_user: Authenticated user (from dependency)
        db: Database session (from dependency)

    Returns:
        ConversationResponse with created conversation details
    """
    logger.info(
        f"Creating conversation for user {current_user.id}",
        extra={"user_id": current_user.id},
    )

    conversation = chat_service.create_conversation(db, current_user.id, request)

    return conversation


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List user's conversations",
    responses={
        200: {"description": "Conversations retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all conversations for the authenticated user with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of conversations per page (default 20)
        current_user: Authenticated user (from dependency)
        db: Database session (from dependency)

    Returns:
        ConversationListResponse with paginated conversations
    """
    logger.info(
        f"Listing conversations for user {current_user.id}",
        extra={"user_id": current_user.id, "page": page, "page_size": page_size},
    )

    conversations, total_count = chat_service.get_user_conversations(
        db, current_user.id, page, page_size
    )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

    return ConversationListResponse(
        conversations=conversations,
        pagination=PaginationMetadata(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
    summary="Get conversation messages",
    responses={
        200: {"description": "Messages retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Conversation not found or access denied"},
    },
)
async def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all messages in a conversation.

    Args:
        conversation_id: ID of the conversation
        current_user: Authenticated user (from dependency)
        db: Database session (from dependency)

    Returns:
        ConversationMessagesResponse with all messages

    Raises:
        HTTPException 404: If conversation not found or user doesn't have access
    """
    logger.info(
        f"Getting messages for conversation {conversation_id}",
        extra={"conversation_id": conversation_id, "user_id": current_user.id},
    )

    try:
        messages = chat_service.get_conversation_messages(
            db, conversation_id, current_user.id
        )
        return messages
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message and get AI response",
    responses={
        201: {"description": "Message sent and response generated"},
        400: {"description": "Invalid request"},
        401: {"description": "Not authenticated"},
        404: {"description": "Conversation not found"},
        503: {"description": "LLM service unavailable"},
    },
)
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message in a conversation and receive AI-generated response with SQL.

    This endpoint:
    1. Creates or retrieves conversation
    2. Stores user message
    3. Generates AI response with SQL using conversation context
    4. Returns both user message and AI response

    Args:
        request: Message content and optional conversation ID
        current_user: Authenticated user (from dependency)
        db: Database session (from dependency)

    Returns:
        SendMessageResponse with user and assistant messages

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 503: If LLM service unavailable
    """
    logger.info(
        f"Sending message for user {current_user.id}",
        extra={
            "user_id": current_user.id,
            "conversation_id": request.conversation_id,
            "message_length": len(request.content),
        },
    )

    try:
        response = await chat_service.send_message(db, current_user.id, request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to generate response: {str(e)}",
        )


@router.put(
    "/messages/{message_id}/regenerate",
    response_model=MessageResponse,
    summary="Regenerate an assistant message",
    responses={
        200: {"description": "Message regenerated successfully"},
        400: {"description": "Can only regenerate assistant messages"},
        401: {"description": "Not authenticated"},
        404: {"description": "Message not found or access denied"},
        503: {"description": "LLM service unavailable"},
    },
)
async def regenerate_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: RegenerateMessageRequest | None = None,
):
    """
    Regenerate an assistant message (creates new message with is_regenerated=True).

    Args:
        message_id: ID of the assistant message to regenerate
        request: Empty request body
        current_user: Authenticated user (from dependency)
        db: Database session (from dependency)

    Returns:
        MessageResponse with the new regenerated message

    Raises:
        HTTPException 400: If trying to regenerate non-assistant message
        HTTPException 404: If message not found or access denied
        HTTPException 503: If LLM service unavailable
    """
    logger.info(
        f"Regenerating message {message_id}",
        extra={"message_id": message_id, "user_id": current_user.id},
    )

    try:
        new_message = await chat_service.regenerate_message(
            db, message_id, current_user.id
        )
        return new_message
    except ValueError as e:
        if "access denied" in str(e).lower() or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Error regenerating message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to regenerate message: {str(e)}",
        )


@router.put(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Edit a user message",
    responses={
        200: {"description": "Message edited successfully"},
        400: {"description": "Can only edit user messages"},
        401: {"description": "Not authenticated"},
        404: {"description": "Message not found or access denied"},
    },
)
async def edit_message(
    message_id: int,
    request: EditMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Edit a user message (creates new message with is_edited=True).

    Note: This creates a new message and marks the original as having a child.
    Subsequent messages in the conversation are not automatically invalidated.

    Args:
        message_id: ID of the user message to edit
        request: New message content
        current_user: Authenticated user (from dependency)
        db: Database session (from dependency)

    Returns:
        MessageResponse with the new edited message

    Raises:
        HTTPException 400: If trying to edit non-user message
        HTTPException 404: If message not found or access denied
    """
    logger.info(
        f"Editing message {message_id}",
        extra={"message_id": message_id, "user_id": current_user.id},
    )

    try:
        new_message = chat_service.edit_message(
            db, message_id, current_user.id, request
        )
        return new_message
    except ValueError as e:
        if "access denied" in str(e).lower() or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
