"""
SQLAlchemy ORM models for the application.

All models are imported here for convenient access.
"""

from backend.app.models.base import Base
from backend.app.models.user import User, Session
from backend.app.models.query import QueryAttempt, QueryResultsManifest
from backend.app.models.knowledge import SchemaSnapshot, KnowledgeBaseExample
from backend.app.models.metrics import MetricsRollup
from backend.app.models.chat import Conversation, Message

__all__ = [
    "Base",
    "User",
    "Session",
    "QueryAttempt",
    "QueryResultsManifest",
    "SchemaSnapshot",
    "KnowledgeBaseExample",
    "MetricsRollup",
    "Conversation",
    "Message",
]
