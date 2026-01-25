"""
CSV Export Service for downloading query results.

Provides streaming CSV export with proper escaping and size limits.
"""

import csv
import io
import json
import logging
from typing import Any, Generator

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.models.query import QueryAttempt, QueryResultsManifest

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting query results to CSV format.

    Implements streaming to avoid loading large result sets into memory.
    """

    def __init__(self, max_rows: int = 10000):
        """
        Initialize export service.

        Args:
            max_rows: Maximum rows to export (default: 10,000)
        """
        self.max_rows = max_rows
        logger.info(f"Export service initialized (max rows: {max_rows})")

    async def export_to_csv(
        self, db: Session, query_attempt_id: int
    ) -> StreamingResponse:
        """
        Export query results as CSV file.

        Args:
            db: Database session
            query_attempt_id: Query attempt ID to export

        Returns:
            StreamingResponse: Streaming CSV response

        Raises:
            ValueError: If query not found or no results available
            ExportTooLargeError: If result set exceeds max_rows

        Example:
            >>> response = await service.export_to_csv(db, query_id=42)
            >>> # FastAPI will stream the CSV to the client
        """
        logger.info(f"Exporting query attempt {query_attempt_id} to CSV")

        # Get query attempt
        query_attempt = (
            db.query(QueryAttempt).filter(QueryAttempt.id == query_attempt_id).first()
        )

        if not query_attempt:
            raise ValueError(f"Query attempt {query_attempt_id} not found")

        # Get results manifest
        manifest = (
            db.query(QueryResultsManifest)
            .filter(QueryResultsManifest.attempt_id == query_attempt_id)
            .first()
        )

        if not manifest:
            raise ValueError(
                f"No results available for query {query_attempt_id}. "
                f"Query may not have been executed yet."
            )

        # Check size limit
        if manifest.total_rows is not None and manifest.total_rows > self.max_rows:
            raise ExportTooLargeError(
                f"Result set too large to export: {manifest.total_rows} rows. "
                f"Maximum is {self.max_rows} rows. "
                f"Please add filters to reduce the result set size."
            )

        # Load results
        if manifest.columns_json is None or manifest.results_json is None:
            raise ValueError(f"No results data available for query {query_attempt_id}.")
        columns = json.loads(manifest.columns_json)
        rows = json.loads(manifest.results_json)

        logger.info(f"Exporting {manifest.total_rows} rows × {len(columns)} columns")

        # Generate filename
        filename = (
            f"query_{query_attempt_id}_{int(query_attempt.created_at.timestamp())}.csv"
        )

        # Create streaming response
        return StreamingResponse(
            self._generate_csv_stream(columns, rows),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )

    def _generate_csv_stream(
        self, columns: list[str], rows: list[list[Any]]
    ) -> Generator[str, None, None]:
        """
        Generate CSV content as a stream.

        Uses Python's csv module for proper escaping of special characters.

        Args:
            columns: Column names
            rows: Result rows

        Yields:
            str: CSV chunks
        """
        # Create string buffer
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        # Write header
        writer.writerow(columns)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Write data rows
        for row in rows:
            # Convert None to empty string
            row_data = [self._format_value(val) for val in row]
            writer.writerow(row_data)

            # Yield buffer content
            chunk = output.getvalue()
            if chunk:
                yield chunk
                output.seek(0)
                output.truncate(0)

        logger.info("CSV generation complete")

    def _format_value(self, value: Any) -> str:
        """
        Format a value for CSV export.

        Handles:
        - None → empty string
        - Lists/dicts → JSON string
        - Other types → string representation

        Args:
            value: Value to format

        Returns:
            str: Formatted value
        """
        if value is None:
            return ""

        if isinstance(value, (list, dict)):
            # Serialize complex types as JSON
            return json.dumps(value)

        if isinstance(value, bool):
            # Boolean as Yes/No
            return "Yes" if value else "No"

        # Default: convert to string
        return str(value)

    async def get_export_info(
        self, db: Session, query_attempt_id: int
    ) -> dict[str, Any]:
        """
        Get information about exportability of a query.

        Useful for UI to show warnings before export.

        Args:
            db: Database session
            query_attempt_id: Query attempt ID

        Returns:
            dict: Export information

        Example:
            >>> info = await service.get_export_info(db, 42)
            >>> print(info)
            {
                "exportable": True,
                "total_rows": 523,
                "total_columns": 5,
                "estimated_size_mb": 0.05,
                "warning": None
            }
        """
        manifest = (
            db.query(QueryResultsManifest)
            .filter(QueryResultsManifest.attempt_id == query_attempt_id)
            .first()
        )

        if not manifest:
            return {"exportable": False, "error": "No results available"}

        if manifest.columns_json is None or manifest.results_json is None:
            return {"exportable": False, "error": "No results data available"}

        columns = json.loads(manifest.columns_json)
        json.loads(manifest.results_json)  # Verify JSON is valid

        total_rows = manifest.total_rows or 0

        # Estimate CSV size (rough approximation)
        # Assume average 20 bytes per cell
        estimated_size_bytes = total_rows * len(columns) * 20
        estimated_size_mb = estimated_size_bytes / (1024 * 1024)

        exportable = total_rows <= self.max_rows

        warning = None
        if total_rows > self.max_rows:
            warning = (
                f"Result set is too large ({total_rows} rows). "
                f"Maximum is {self.max_rows} rows. Please add filters."
            )

        return {
            "exportable": exportable,
            "total_rows": total_rows,
            "total_columns": len(columns),
            "estimated_size_mb": round(estimated_size_mb, 2),
            "warning": warning,
        }


class ExportTooLargeError(Exception):
    """Raised when export exceeds size limits."""

    pass
