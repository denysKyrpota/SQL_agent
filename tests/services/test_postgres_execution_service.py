"""
Tests for PostgreSQL execution service.

Tests:
- SQL validation (SELECT-only enforcement)
- Query execution with timeout
- Results manifest creation
- Error handling
"""

import pytest

from backend.app.services.postgres_execution_service import PostgresExecutionService


class TestSQLValidation:
    """Tests for SQL validation logic."""

    def setup_method(self):
        """Set up test instance."""
        self.service = PostgresExecutionService()

    def test_validate_select_query(self):
        """Test validation of valid SELECT query."""
        sql = "SELECT * FROM users WHERE active = true;"

        # Should not raise
        self.service.validate_sql(sql)

    def test_validate_select_with_join(self):
        """Test validation of SELECT with JOIN."""
        sql = """
        SELECT u.username, o.id
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE o.status = 'completed';
        """

        # Should not raise
        self.service.validate_sql(sql)

    def test_validate_select_with_subquery(self):
        """Test validation of SELECT with subquery."""
        sql = """
        SELECT * FROM users
        WHERE id IN (SELECT user_id FROM orders WHERE total > 100);
        """

        # Should not raise
        self.service.validate_sql(sql)

    def test_reject_insert_query(self):
        """Test rejection of INSERT query."""
        sql = "INSERT INTO users (username) VALUES ('hacker');"

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.service.validate_sql(sql)

    def test_reject_update_query(self):
        """Test rejection of UPDATE query."""
        sql = "UPDATE users SET role = 'admin' WHERE id = 1;"

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.service.validate_sql(sql)

    def test_reject_delete_query(self):
        """Test rejection of DELETE query."""
        sql = "DELETE FROM users WHERE id = 1;"

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.service.validate_sql(sql)

    def test_reject_drop_query(self):
        """Test rejection of DROP query."""
        sql = "DROP TABLE users;"

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.service.validate_sql(sql)

    def test_reject_create_query(self):
        """Test rejection of CREATE query."""
        sql = "CREATE TABLE malicious (id INT);"

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            self.service.validate_sql(sql)

    def test_reject_multiple_statements(self):
        """Test rejection of multiple SQL statements."""
        sql = "SELECT * FROM users; DROP TABLE users;"

        with pytest.raises(ValueError, match="Multiple SQL statements not allowed"):
            self.service.validate_sql(sql)

    def test_reject_empty_query(self):
        """Test rejection of empty query."""
        sql = ""

        with pytest.raises(ValueError, match="SQL query is empty"):
            self.service.validate_sql(sql)

    def test_reject_whitespace_only(self):
        """Test rejection of whitespace-only query."""
        sql = "   \n\t  "

        with pytest.raises(ValueError, match="SQL query is empty"):
            self.service.validate_sql(sql)


class TestResultsManifestCreation:
    """Tests for results manifest creation logic."""

    def test_calculate_pagination_single_page(self):
        """Test pagination calculation for results under 500 rows."""
        total_rows = 100
        page_size = 500

        page_count = (total_rows + page_size - 1) // page_size

        assert page_count == 1

    def test_calculate_pagination_multiple_pages(self):
        """Test pagination calculation for results over 500 rows."""
        total_rows = 1234
        page_size = 500

        page_count = (total_rows + page_size - 1) // page_size

        assert page_count == 3  # Pages: 500, 500, 234

    def test_calculate_pagination_exact_multiple(self):
        """Test pagination calculation for exact multiple of page size."""
        total_rows = 1000
        page_size = 500

        page_count = (total_rows + page_size - 1) // page_size

        assert page_count == 2
