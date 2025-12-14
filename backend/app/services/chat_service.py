"""
Service layer for chat-based conversational SQL generation.

This service handles conversation management and context-aware SQL generation.
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.chat import Conversation, Message
from backend.app.models.query import QueryAttempt as QueryAttemptModel
from backend.app.schemas.chat import (
    CreateConversationRequest,
    ConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    MessageResponse,
    ConversationMessagesResponse,
    EditMessageRequest,
)
from backend.app.services.llm_service import LLMService
from backend.app.services.schema_service import SchemaService
from backend.app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing conversations and chat-based SQL generation."""

    # Maximum number of messages to include in conversation context
    MAX_CONTEXT_MESSAGES = 10

    def __init__(
        self,
        llm_service: LLMService | None = None,
        schema_service: SchemaService | None = None,
        kb_service: KnowledgeBaseService | None = None,
    ):
        """
        Initialize the chat service with dependencies.

        Args:
            llm_service: LLM service for SQL generation
            schema_service: Schema service for database schema
            kb_service: Knowledge base service for SQL examples
        """
        self.llm = llm_service or LLMService()
        self.schema = schema_service or SchemaService()
        self.kb = kb_service or KnowledgeBaseService()

        logger.info("Chat service initialized with all dependencies")

    def create_conversation(
        self, db: Session, user_id: int, request: CreateConversationRequest | None = None
    ) -> ConversationResponse:
        """
        Create a new conversation for the user.

        Args:
            db: Database session
            user_id: ID of the authenticated user
            request: Optional conversation creation request with title

        Returns:
            ConversationResponse with conversation details
        """
        title = request.title if request else None

        conversation = Conversation(
            user_id=user_id,
            title=title,
            is_active=True,
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        logger.info(
            f"Created conversation {conversation.id} for user {user_id}",
            extra={"conversation_id": conversation.id, "user_id": user_id},
        )

        return self._conversation_to_response(db, conversation)

    def get_user_conversations(
        self, db: Session, user_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[ConversationResponse], int]:
        """
        Get all conversations for a user with pagination.

        Args:
            db: Database session
            user_id: ID of the authenticated user
            page: Page number (1-indexed)
            page_size: Number of conversations per page

        Returns:
            Tuple of (list of conversations, total count)
        """
        offset = (page - 1) * page_size

        # Get total count
        total_count = db.query(func.count(Conversation.id)).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).scalar()

        # Get conversations
        conversations = (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.is_active == True
            )
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        conversation_responses = [
            self._conversation_to_response(db, conv) for conv in conversations
        ]

        return conversation_responses, total_count or 0

    def get_conversation_messages(
        self, db: Session, conversation_id: int, user_id: int
    ) -> ConversationMessagesResponse:
        """
        Get all messages in a conversation.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            user_id: ID of the authenticated user (for permission check)

        Returns:
            ConversationMessagesResponse with all messages

        Raises:
            ValueError: If conversation not found or user doesn't have access
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise ValueError("Conversation not found or access denied")

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        message_responses = [self._message_to_response(msg) for msg in messages]

        return ConversationMessagesResponse(
            conversation_id=conversation_id,
            messages=message_responses
        )

    async def send_message(
        self, db: Session, user_id: int, request: SendMessageRequest
    ) -> SendMessageResponse:
        """
        Send a message in a conversation and get AI response.

        This method:
        1. Creates or retrieves conversation
        2. Stores user message
        3. Gets conversation context (last N messages)
        4. Generates AI response with SQL (if applicable)
        5. Stores assistant message
        6. Returns both messages

        Args:
            db: Database session
            user_id: ID of the authenticated user
            request: Message content and optional conversation ID

        Returns:
            SendMessageResponse with user and assistant messages
        """
        # Step 1: Get or create conversation
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user_id
            ).first()

            if not conversation:
                raise ValueError("Conversation not found or access denied")
        else:
            # Create new conversation with title from first message preview
            title = request.content[:50] + "..." if len(request.content) > 50 else request.content
            conversation = Conversation(
                user_id=user_id,
                title=title,
                is_active=True,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            logger.info(
                f"Created new conversation {conversation.id} from message",
                extra={"conversation_id": conversation.id, "user_id": user_id},
            )

        # Step 2: Store user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.content,
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        logger.info(
            f"Stored user message {user_message.id}",
            extra={"message_id": user_message.id, "conversation_id": conversation.id},
        )

        # Step 3: Get conversation context
        context_messages = self._get_context_messages(db, conversation.id)

        # Step 4: Generate AI response with SQL
        generation_start = datetime.utcnow()

        try:
            # Stage 1: Select relevant tables
            all_tables = self.schema.get_table_names()
            logger.info(f"Schema has {len(all_tables)} tables total")

            selected_tables = await self.llm.select_relevant_tables(
                question=request.content,
                all_table_names=all_tables,
                conversation_history=context_messages,
            )

            logger.info(
                f"Selected {len(selected_tables)} relevant tables",
                extra={"selected_tables": selected_tables},
            )

            # Stage 2: Generate SQL with context
            filtered_schema = self.schema.filter_schema_by_tables(selected_tables)
            similar_examples = self.kb.find_similar_examples(request.content, top_k=3)

            generated_sql = await self.llm.generate_sql(
                question=request.content,
                schema=filtered_schema,
                examples=similar_examples,
                conversation_history=context_messages,
            )

            generation_ms = int((datetime.utcnow() - generation_start).total_seconds() * 1000)

            # Create QueryAttempt for the generated SQL
            query_attempt = QueryAttemptModel(
                user_id=user_id,
                natural_language_query=request.content,
                generated_sql=generated_sql,
                status="not_executed",
                generated_at=datetime.utcnow(),
                generation_ms=generation_ms,
            )
            db.add(query_attempt)
            db.commit()
            db.refresh(query_attempt)

            # Create assistant message with SQL
            assistant_content = f"I've generated the following SQL query:\n\n```sql\n{generated_sql}\n```"

            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_content,
                query_attempt_id=query_attempt.id,
                message_metadata=json.dumps({
                    "generation_ms": generation_ms,
                    "tables_used": selected_tables,
                    "model": self.llm.model,
                }),
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)

            logger.info(
                f"Generated SQL and stored assistant message {assistant_message.id}",
                extra={
                    "message_id": assistant_message.id,
                    "query_attempt_id": query_attempt.id,
                    "generation_ms": generation_ms,
                },
            )

        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}", exc_info=True)

            # Store error message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=f"I encountered an error while generating SQL: {str(e)}",
                message_metadata=json.dumps({"error": str(e)}),
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)

        return SendMessageResponse(
            conversation_id=conversation.id,
            user_message=self._message_to_response(user_message),
            assistant_message=self._message_to_response(assistant_message),
        )

    async def regenerate_message(
        self, db: Session, message_id: int, user_id: int
    ) -> MessageResponse:
        """
        Regenerate an assistant message.

        Args:
            db: Database session
            message_id: ID of the message to regenerate
            user_id: ID of the authenticated user (for permission check)

        Returns:
            MessageResponse with the new regenerated message

        Raises:
            ValueError: If message not found, not an assistant message, or access denied
        """
        # Get original message and verify permissions
        original_message = db.query(Message).filter(Message.id == message_id).first()

        if not original_message:
            raise ValueError("Message not found")

        conversation = db.query(Conversation).filter(
            Conversation.id == original_message.conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise ValueError("Access denied")

        if original_message.role != "assistant":
            raise ValueError("Can only regenerate assistant messages")

        # Get the user message that prompted this response
        user_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == original_message.conversation_id,
                Message.role == "user",
                Message.created_at < original_message.created_at
            )
            .order_by(Message.created_at.desc())
            .first()
        )

        if not user_messages:
            raise ValueError("No user message found to regenerate from")

        # Get conversation context (excluding the original message we're regenerating)
        context_messages = self._get_context_messages(
            db, conversation.id, exclude_message_id=message_id
        )

        # Generate new response
        generation_start = datetime.utcnow()

        try:
            all_tables = self.schema.get_table_names()
            selected_tables = await self.llm.select_relevant_tables(
                question=user_messages.content,
                all_table_names=all_tables,
                conversation_history=context_messages,
            )

            filtered_schema = self.schema.filter_schema_by_tables(selected_tables)
            similar_examples = self.kb.find_similar_examples(user_messages.content, top_k=3)

            generated_sql = await self.llm.generate_sql(
                question=user_messages.content,
                schema=filtered_schema,
                examples=similar_examples,
                conversation_history=context_messages,
            )

            generation_ms = int((datetime.utcnow() - generation_start).total_seconds() * 1000)

            # Create new QueryAttempt
            query_attempt = QueryAttemptModel(
                user_id=user_id,
                natural_language_query=user_messages.content,
                generated_sql=generated_sql,
                status="not_executed",
                generated_at=datetime.utcnow(),
                generation_ms=generation_ms,
            )
            db.add(query_attempt)
            db.commit()
            db.refresh(query_attempt)

            assistant_content = f"I've generated the following SQL query:\n\n```sql\n{generated_sql}\n```"

            new_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_content,
                query_attempt_id=query_attempt.id,
                parent_message_id=message_id,
                is_regenerated=True,
                message_metadata=json.dumps({
                    "generation_ms": generation_ms,
                    "tables_used": selected_tables,
                    "model": self.llm.model,
                }),
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            logger.info(
                f"Regenerated message {new_message.id} from original {message_id}",
                extra={"new_message_id": new_message.id, "original_message_id": message_id},
            )

            return self._message_to_response(new_message)

        except Exception as e:
            logger.error(f"Error regenerating message: {str(e)}", exc_info=True)
            raise

    def edit_message(
        self, db: Session, message_id: int, user_id: int, request: EditMessageRequest
    ) -> MessageResponse:
        """
        Edit a user message (creates new message, marks original as edited).

        Args:
            db: Database session
            message_id: ID of the message to edit
            user_id: ID of the authenticated user (for permission check)
            request: New message content

        Returns:
            MessageResponse with the new edited message

        Raises:
            ValueError: If message not found, not a user message, or access denied
        """
        # Get original message and verify permissions
        original_message = db.query(Message).filter(Message.id == message_id).first()

        if not original_message:
            raise ValueError("Message not found")

        conversation = db.query(Conversation).filter(
            Conversation.id == original_message.conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise ValueError("Access denied")

        if original_message.role != "user":
            raise ValueError("Can only edit user messages")

        # Create new message with edited content
        new_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.content,
            parent_message_id=message_id,
            is_edited=True,
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

        logger.info(
            f"Edited message {new_message.id} from original {message_id}",
            extra={"new_message_id": new_message.id, "original_message_id": message_id},
        )

        return self._message_to_response(new_message)

    def _get_context_messages(
        self, db: Session, conversation_id: int, exclude_message_id: int | None = None
    ) -> list[dict[str, str]]:
        """
        Get conversation context messages for LLM.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            exclude_message_id: Optional message ID to exclude from context

        Returns:
            List of message dicts with role and content
        """
        query = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
        )

        if exclude_message_id:
            query = query.filter(Message.id != exclude_message_id)

        messages = query.limit(self.MAX_CONTEXT_MESSAGES).all()

        # Reverse to get chronological order
        messages.reverse()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def _conversation_to_response(
        self, db: Session, conversation: Conversation
    ) -> ConversationResponse:
        """Convert Conversation model to ConversationResponse schema."""
        message_count = db.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation.id
        ).scalar()

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            is_active=conversation.is_active,
            created_at=conversation.created_at.isoformat() + "Z",
            updated_at=conversation.updated_at.isoformat() + "Z",
            message_count=message_count or 0,
        )

    def _message_to_response(self, message: Message) -> MessageResponse:
        """Convert Message model to MessageResponse schema."""
        metadata = None
        if message.message_metadata:
            try:
                metadata = json.loads(message.message_metadata)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse message_metadata for message {message.id}")

        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            query_attempt_id=message.query_attempt_id,
            parent_message_id=message.parent_message_id,
            is_edited=message.is_edited,
            is_regenerated=message.is_regenerated,
            created_at=message.created_at.isoformat() + "Z",
            metadata=metadata,
        )
