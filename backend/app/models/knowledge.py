"""
Knowledge base and schema ORM models.

Handles schema snapshots and knowledge base example indexing.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class SchemaSnapshot(Base):
    """
    Schema snapshot model.

    Stores temporal history of PostgreSQL schema for caching and audit.
    """

    __tablename__ = "schema_snapshots"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Schema metadata
    source_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    table_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Schema data as JSON
    tables_json: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<SchemaSnapshot(id={self.id}, table_count={self.table_count}, loaded_at={self.loaded_at})>"


class KnowledgeBaseExample(Base):
    """
    Knowledge base example model.

    Indexes .sql example files for semantic search and retrieval.
    """

    __tablename__ = "kb_examples_index"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # File metadata
    file_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    last_loaded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Embedding vector for semantic search
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    def __repr__(self) -> str:
        return f"<KnowledgeBaseExample(id={self.id}, file_path={self.file_path!r})>"
