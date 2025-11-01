"""
Query-related ORM models.

Handles query attempts and results metadata.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class QueryAttempt(Base):
    """
    Query attempt model.

    Stores the complete history of natural language queries,
    generated SQL, and execution results.
    """

    __tablename__ = "query_attempts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to users
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # Query fields
    natural_language_query: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String, nullable=False, default="not_executed")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Performance metrics
    generation_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Retry/re-run lineage
    original_attempt_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("query_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Error message for failed attempts
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="query_attempts")
    results_manifest: Mapped["QueryResultsManifest | None"] = relationship(
        "QueryResultsManifest",
        back_populates="query_attempt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    original_attempt: Mapped["QueryAttempt | None"] = relationship(
        "QueryAttempt",
        remote_side=[id],
        foreign_keys=[original_attempt_id],
    )

    def __repr__(self) -> str:
        return f"<QueryAttempt(id={self.id}, user_id={self.user_id}, status={self.status!r})>"


class QueryResultsManifest(Base):
    """
    Query results manifest model.

    Stores metadata for query results pagination and CSV export.
    Actual result rows are NOT stored in the database.
    """

    __tablename__ = "query_results_manifest"

    # Primary key (1-to-1 with query_attempts)
    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("query_attempts.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Result metadata
    total_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_size: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Export metadata
    export_row_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    export_truncated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    export_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    query_attempt: Mapped["QueryAttempt"] = relationship(
        "QueryAttempt", back_populates="results_manifest"
    )

    def __repr__(self) -> str:
        return f"<QueryResultsManifest(attempt_id={self.attempt_id}, total_rows={self.total_rows})>"
