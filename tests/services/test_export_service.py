"""
Tests for ExportService - CSV export functionality.

Tests:
- CSV export with proper formatting
- Export size limits
- Value formatting (None, bool, JSON)
- Export metadata and info
- Streaming functionality
"""

import json
import pytest
from sqlalchemy.orm import Session

from backend.app.models.query import QueryAttempt, QueryResultsManifest
from backend.app.models.user import User
from backend.app.services.export_service import ExportService, ExportTooLargeError


class TestExportToCSV:
    """Tests for CSV export functionality."""

    @pytest.mark.asyncio
    async def test_export_to_csv_success(
        self,
        test_db: Session,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest]
    ):
        """Test successful CSV export."""
        query, manifest = executed_query_with_results
        service = ExportService(max_rows=10000)

        response = await service.export_to_csv(db=test_db, query_attempt_id=query.id)

        assert response.status_code == 200
        assert response.media_type == "text/csv"
        assert "attachment" in response.headers["content-disposition"]

        # Read CSV content
        csv_content = ""
        async for chunk in response.body_iterator:
            csv_content += chunk

        # Verify CSV structure
        lines = csv_content.strip().split('\n')
        assert len(lines) == 4  # 1 header + 3 data rows
        assert "id,username,email" in lines[0]
        assert "alice" in csv_content
        assert "bob" in csv_content

    @pytest.mark.asyncio
    async def test_export_query_not_found(self, test_db: Session):
        """Test exporting non-existent query."""
        service = ExportService()

        with pytest.raises(ValueError, match="not found"):
            await service.export_to_csv(db=test_db, query_attempt_id=99999)

    @pytest.mark.asyncio
    async def test_export_no_results(
        self,
        test_db: Session,
        sample_query_attempt: QueryAttempt
    ):
        """Test exporting query that hasn't been executed."""
        service = ExportService()

        with pytest.raises(ValueError, match="No results available"):
            await service.export_to_csv(db=test_db, query_attempt_id=sample_query_attempt.id)

    @pytest.mark.asyncio
    async def test_export_too_large(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test export size limit enforcement."""
        # Create query with large result set
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Large query",
            generated_sql="SELECT * FROM big_table;",
            status="success"
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with 15000 rows (exceeds limit)
        columns = ["id", "value"]
        rows = [[i, f"value_{i}"] for i in range(15000)]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=15000,
            page_size=500,
            page_count=30
        )
        test_db.add(manifest)
        test_db.commit()

        service = ExportService(max_rows=10000)

        with pytest.raises(ExportTooLargeError, match="too large"):
            await service.export_to_csv(db=test_db, query_attempt_id=query.id)

    @pytest.mark.asyncio
    async def test_export_filename_format(
        self,
        test_db: Session,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest]
    ):
        """Test CSV filename format."""
        query, _ = executed_query_with_results
        service = ExportService()

        response = await service.export_to_csv(db=test_db, query_attempt_id=query.id)

        content_disposition = response.headers["content-disposition"]
        assert f"query_{query.id}_" in content_disposition
        assert content_disposition.endswith('.csv"')


class TestValueFormatting:
    """Tests for CSV value formatting."""

    def test_format_value_none(self):
        """Test formatting None values."""
        service = ExportService()

        result = service._format_value(None)

        assert result == ""

    def test_format_value_string(self):
        """Test formatting string values."""
        service = ExportService()

        result = service._format_value("test string")

        assert result == "test string"

    def test_format_value_number(self):
        """Test formatting numeric values."""
        service = ExportService()

        assert service._format_value(123) == "123"
        assert service._format_value(45.67) == "45.67"

    def test_format_value_boolean(self):
        """Test formatting boolean values."""
        service = ExportService()

        assert service._format_value(True) == "Yes"
        assert service._format_value(False) == "No"

    def test_format_value_list(self):
        """Test formatting list values as JSON."""
        service = ExportService()

        result = service._format_value([1, 2, 3])

        assert result == "[1, 2, 3]"

    def test_format_value_dict(self):
        """Test formatting dict values as JSON."""
        service = ExportService()

        result = service._format_value({"key": "value", "num": 42})

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["num"] == 42


class TestCSVGeneration:
    """Tests for CSV streaming generation."""

    @pytest.mark.asyncio
    async def test_csv_with_special_characters(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test CSV export with special characters (quotes, commas, newlines)."""
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Special chars query",
            generated_sql="SELECT * FROM users;",
            status="success"
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with special characters
        columns = ["id", "name", "description"]
        rows = [
            [1, 'John "Johnny" Doe', "Has, commas, in, text"],
            [2, "Jane\nNewline", "Quote: \"test\""],
            [3, "Normal", "Regular text"]
        ]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=3,
            page_size=500,
            page_count=1
        )
        test_db.add(manifest)
        test_db.commit()

        service = ExportService()
        response = await service.export_to_csv(db=test_db, query_attempt_id=query.id)

        # Read CSV content
        csv_content = ""
        async for chunk in response.body_iterator:
            csv_content += chunk

        # CSV should properly escape special characters
        assert csv_content
        lines = csv_content.strip().split('\n')
        assert len(lines) >= 4  # Header + 3 rows (may be more due to embedded newlines)

    @pytest.mark.asyncio
    async def test_csv_with_null_values(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test CSV export with NULL values."""
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="NULL values query",
            generated_sql="SELECT * FROM users;",
            status="success"
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with None values
        columns = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob", None],  # NULL email
            [3, None, "charlie@example.com"]  # NULL name
        ]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=3,
            page_size=500,
            page_count=1
        )
        test_db.add(manifest)
        test_db.commit()

        service = ExportService()
        response = await service.export_to_csv(db=test_db, query_attempt_id=query.id)

        # Read CSV content
        csv_content = ""
        async for chunk in response.body_iterator:
            csv_content += chunk

        # NULL values should be empty strings in CSV
        lines = csv_content.strip().split('\n')
        assert len(lines) == 4


class TestExportInfo:
    """Tests for export metadata retrieval."""

    @pytest.mark.asyncio
    async def test_get_export_info_success(
        self,
        test_db: Session,
        executed_query_with_results: tuple[QueryAttempt, QueryResultsManifest]
    ):
        """Test getting export info for exportable query."""
        query, manifest = executed_query_with_results
        service = ExportService(max_rows=10000)

        info = await service.get_export_info(db=test_db, query_attempt_id=query.id)

        assert info["exportable"] is True
        assert info["total_rows"] == 3
        assert info["total_columns"] == 3
        assert info["estimated_size_mb"] > 0
        assert info["warning"] is None

    @pytest.mark.asyncio
    async def test_get_export_info_no_results(
        self,
        test_db: Session,
        sample_query_attempt: QueryAttempt
    ):
        """Test getting export info for query without results."""
        service = ExportService()

        info = await service.get_export_info(db=test_db, query_attempt_id=sample_query_attempt.id)

        assert info["exportable"] is False
        assert "error" in info

    @pytest.mark.asyncio
    async def test_get_export_info_too_large(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test export info for query exceeding size limit."""
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Large query",
            generated_sql="SELECT * FROM big_table;",
            status="success"
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with 15000 rows
        columns = ["id", "value"]
        rows = [[i, f"value_{i}"] for i in range(15000)]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=15000,
            page_size=500,
            page_count=30
        )
        test_db.add(manifest)
        test_db.commit()

        service = ExportService(max_rows=10000)

        info = await service.get_export_info(db=test_db, query_attempt_id=query.id)

        assert info["exportable"] is False
        assert info["total_rows"] == 15000
        assert info["warning"] is not None
        assert "too large" in info["warning"]

    @pytest.mark.asyncio
    async def test_get_export_info_size_estimation(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test CSV size estimation accuracy."""
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Size test",
            generated_sql="SELECT * FROM users;",
            status="success"
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with known data
        columns = ["id", "name"]
        rows = [[i, f"user_{i}"] for i in range(1000)]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=1000,
            page_size=500,
            page_count=2
        )
        test_db.add(manifest)
        test_db.commit()

        service = ExportService()

        info = await service.get_export_info(db=test_db, query_attempt_id=query.id)

        # Size should be positive and reasonable
        assert info["estimated_size_mb"] > 0
        assert info["estimated_size_mb"] < 1.0  # Should be less than 1MB for 1000 rows


class TestCustomMaxRows:
    """Tests for custom max_rows configuration."""

    @pytest.mark.asyncio
    async def test_custom_max_rows(
        self,
        test_db: Session,
        test_user: User
    ):
        """Test ExportService with custom max_rows limit."""
        query = QueryAttempt(
            user_id=test_user.id,
            natural_language_query="Custom limit test",
            generated_sql="SELECT * FROM users;",
            status="success"
        )
        test_db.add(query)
        test_db.commit()
        test_db.refresh(query)

        # Create manifest with 150 rows
        columns = ["id"]
        rows = [[i] for i in range(150)]

        manifest = QueryResultsManifest(
            attempt_id=query.id,
            columns_json=json.dumps(columns),
            results_json=json.dumps(rows),
            total_rows=150,
            page_size=500,
            page_count=1
        )
        test_db.add(manifest)
        test_db.commit()

        # Set custom limit to 100 rows
        service = ExportService(max_rows=100)

        # Should raise error because 150 > 100
        with pytest.raises(ExportTooLargeError):
            await service.export_to_csv(db=test_db, query_attempt_id=query.id)

    @pytest.mark.asyncio
    async def test_default_max_rows(self):
        """Test ExportService default max_rows value."""
        service = ExportService()

        assert service.max_rows == 10000
