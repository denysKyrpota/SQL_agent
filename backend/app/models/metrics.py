"""
Metrics ORM models.

Handles weekly aggregated metrics for analytics.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class MetricsRollup(Base):
    """
    Metrics rollup model.

    Stores weekly aggregated metrics for success rate analytics.
    """

    __tablename__ = "metrics_rollup"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Week identifier (ISO 8601 date of week start)
    week_start: Mapped[str] = mapped_column(String, nullable=False)

    # Optional user-specific metrics
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # Metric counters
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    executed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<MetricsRollup(id={self.id}, week_start={self.week_start!r}, user_id={self.user_id})>"
