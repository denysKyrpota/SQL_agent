"""
Service layer modules for SQL AI Agent.

This package contains all business logic services and provides
shared singleton instances to avoid creating multiple instances
with separate caches.

Services:
- llm_service: OpenAI/Azure OpenAI API integration
- schema_service: PostgreSQL schema management
- knowledge_base_service: KB example search with embeddings
- query_service: Query creation and SQL generation
- chat_service: Conversational SQL generation
- auth_service: Authentication and session management
- export_service: CSV export functionality
- postgres_service: PostgreSQL query execution
"""

from backend.app.services.llm_service import LLMService
from backend.app.services.schema_service import SchemaService
from backend.app.services.knowledge_base_service import KnowledgeBaseService

# Shared service singletons - use these instead of creating new instances
# This ensures caching works across the entire application
llm_service = LLMService()
schema_service = SchemaService()
kb_service = KnowledgeBaseService()

__all__ = [
    "LLMService",
    "SchemaService",
    "KnowledgeBaseService",
    "llm_service",
    "schema_service",
    "kb_service",
]
