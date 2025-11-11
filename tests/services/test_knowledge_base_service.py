"""
Tests for KnowledgeBaseService - SQL example loading and search.

Tests:
- Loading SQL examples from files
- Title extraction
- Description extraction
- SQL extraction and cleaning
- Keyword search
- Example caching
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from backend.app.services.knowledge_base_service import KnowledgeBaseService, KBExample


class TestExtractTitle:
    """Tests for title extraction from SQL files."""

    def test_extract_title_from_first_line(self):
        """Test extracting title from first line of file."""
        service = KnowledgeBaseService()

        lines = [
            "Active Users Query",
            "SELECT * FROM users WHERE active = true;"
        ]

        title = service._extract_title(lines, "active_users")

        assert title == "Active Users Query"

    def test_extract_title_from_filename(self):
        """Test generating title from filename."""
        service = KnowledgeBaseService()

        lines = ["SELECT * FROM users;"]  # No title line

        title = service._extract_title(lines, "drivers_with_current_availability")

        assert title == "Drivers With Current Availability"

    def test_extract_title_skips_sql_lines(self):
        """Test that SQL SELECT lines are not used as titles."""
        service = KnowledgeBaseService()

        lines = ["SELECT * FROM users;"]

        title = service._extract_title(lines, "user_query")

        # Should fall back to filename
        assert title == "User Query"

    def test_extract_title_skips_comments(self):
        """Test that comment lines are not used as titles."""
        service = KnowledgeBaseService()

        lines = ["-- This is a comment", "SELECT * FROM users;"]

        title = service._extract_title(lines, "users_list")

        # Should fall back to filename
        assert title == "Users List"


class TestExtractDescription:
    """Tests for description extraction from SQL files."""

    def test_extract_description_with_description_keyword(self):
        """Test extracting description with 'Description:' keyword."""
        service = KnowledgeBaseService()

        content = """
-- Description: Gets all active users from the system
SELECT * FROM users WHERE active = true;
"""

        description = service._extract_description(content)

        assert description == "Gets all active users from the system"

    def test_extract_description_with_question_keyword(self):
        """Test extracting description with 'Question:' keyword."""
        service = KnowledgeBaseService()

        content = """
-- Question: Show me all active users
SELECT * FROM users WHERE active = true;
"""

        description = service._extract_description(content)

        assert description == "Show me all active users"

    def test_extract_description_none_found(self):
        """Test when no description is found."""
        service = KnowledgeBaseService()

        content = "SELECT * FROM users;"

        description = service._extract_description(content)

        assert description is None

    def test_extract_description_case_insensitive(self):
        """Test description extraction is case-insensitive."""
        service = KnowledgeBaseService()

        content = "-- DESCRIPTION: Test query\nSELECT 1;"

        description = service._extract_description(content)

        assert description == "Test query"


class TestExtractSQL:
    """Tests for SQL extraction and cleaning."""

    def test_extract_sql_basic(self):
        """Test extracting basic SQL query."""
        service = KnowledgeBaseService()

        content = "SELECT * FROM users WHERE active = true;"

        sql = service._extract_sql(content)

        assert sql == "SELECT * FROM users WHERE active = true;"

    def test_extract_sql_removes_markdown(self):
        """Test removing markdown code blocks."""
        service = KnowledgeBaseService()

        content = """
```sql
SELECT * FROM users;
```
"""

        sql = service._extract_sql(content)

        assert "```" not in sql
        assert sql.strip() == "SELECT * FROM users;"

    def test_extract_sql_removes_title_line(self):
        """Test removing title line from SQL."""
        service = KnowledgeBaseService()

        content = """
Active Users Query
SELECT * FROM users WHERE active = true;
"""

        sql = service._extract_sql(content)

        assert "Active Users Query" not in sql
        assert "SELECT * FROM users WHERE active = true;" in sql

    def test_extract_sql_adds_semicolon(self):
        """Test adding semicolon if missing."""
        service = KnowledgeBaseService()

        content = "SELECT * FROM users"

        sql = service._extract_sql(content)

        assert sql.endswith(";")

    def test_extract_sql_multiline(self):
        """Test extracting multiline SQL query."""
        service = KnowledgeBaseService()

        content = """
```sql
SELECT
    id,
    username
FROM users
WHERE active = true;
```
"""

        sql = service._extract_sql(content)

        assert "SELECT" in sql
        assert "FROM users" in sql
        assert "WHERE active = true;" in sql


class TestLoadExampleFile:
    """Tests for loading individual SQL example files."""

    def test_load_example_file_success(self, tmp_path):
        """Test successfully loading a SQL example file."""
        service = KnowledgeBaseService()

        # Create temporary SQL file
        sql_file = tmp_path / "test_query.sql"
        sql_file.write_text("""
Test Query Title
-- Description: A test query
SELECT * FROM users;
""")

        example = service._load_example_file(sql_file)

        assert example.filename == "test_query.sql"
        assert example.title == "Test Query Title"
        assert example.description == "A test query"
        assert "SELECT * FROM users" in example.sql
        assert example.embedding is None

    def test_load_example_file_minimal(self, tmp_path):
        """Test loading file with minimal content."""
        service = KnowledgeBaseService()

        sql_file = tmp_path / "minimal.sql"
        sql_file.write_text("SELECT 1;")

        example = service._load_example_file(sql_file)

        assert example.filename == "minimal.sql"
        assert example.title == "Minimal"  # Generated from filename
        assert example.sql == "SELECT 1;"


class TestLoadExamples:
    """Tests for loading all examples from directory."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_load_examples_success(self, mock_glob, mock_exists):
        """Test loading multiple SQL example files."""
        from pathlib import Path

        mock_exists.return_value = True

        # Use real Path objects for sorting to work
        mock_file1 = Path("query1.sql")
        mock_file2 = Path("query2.sql")

        mock_glob.return_value = [mock_file1, mock_file2]

        service = KnowledgeBaseService()

        # Mock _load_example_file to return test examples
        service._load_example_file = MagicMock(side_effect=[
            KBExample(
                filename="query1.sql",
                title="Query 1",
                description="Test query 1",
                sql="SELECT * FROM table1;",
            ),
            KBExample(
                filename="query2.sql",
                title="Query 2",
                description="Test query 2",
                sql="SELECT * FROM table2;",
            ),
        ])

        examples = service.load_examples()

        assert len(examples) == 2
        assert examples[0].filename == "query1.sql"
        assert examples[1].filename == "query2.sql"

    @patch('pathlib.Path.exists')
    def test_load_examples_directory_not_found(self, mock_exists):
        """Test error when KB directory doesn't exist."""
        mock_exists.return_value = False

        service = KnowledgeBaseService()

        with pytest.raises(FileNotFoundError, match="Knowledge base directory not found"):
            service.load_examples()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_load_examples_skips_invalid_files(self, mock_glob, mock_exists):
        """Test that invalid files are skipped with warning."""
        from pathlib import Path

        mock_exists.return_value = True

        # Use real Path objects for sorting to work
        mock_file1 = Path("valid.sql")
        mock_file2 = Path("invalid.sql")

        mock_glob.return_value = [mock_file1, mock_file2]

        service = KnowledgeBaseService()

        # First file succeeds, second fails
        service._load_example_file = MagicMock(side_effect=[
            Exception("File read error"),  # invalid.sql comes first alphabetically
            KBExample(
                filename="valid.sql",
                title="Valid",
                description="Valid query",
                sql="SELECT 1;",
            ),
        ])

        examples = service.load_examples()

        # Should only return valid example
        assert len(examples) == 1
        assert examples[0].filename == "valid.sql"


class TestGetExamples:
    """Tests for get_examples method with caching."""

    @patch.object(KnowledgeBaseService, 'load_examples')
    def test_get_examples_loads_once(self, mock_load):
        """Test that examples are loaded once and cached."""
        mock_load.return_value = [
            KBExample(
                filename="test.sql",
                title="Test",
                description="Test",
                sql="SELECT 1;",
            )
        ]

        service = KnowledgeBaseService()

        # First call should load
        examples1 = service.get_examples()
        assert mock_load.call_count == 1

        # Second call should use cache
        examples2 = service.get_examples()
        assert mock_load.call_count == 1  # Still just 1

        # Both should return same data
        assert examples1 == examples2


class TestGetAllExamplesText:
    """Tests for get_all_examples_text method."""

    @patch.object(KnowledgeBaseService, 'load_examples')
    def test_get_all_examples_text(self, mock_load):
        """Test getting all examples as SQL text."""
        mock_load.return_value = [
            KBExample(
                filename="query1.sql",
                title="Query 1",
                description="Test 1",
                sql="SELECT * FROM users;",
            ),
            KBExample(
                filename="query2.sql",
                title="Query 2",
                description="Test 2",
                sql="SELECT * FROM orders;",
            ),
        ]

        service = KnowledgeBaseService()

        sql_texts = service.get_all_examples_text()

        assert len(sql_texts) == 2
        assert "SELECT * FROM users;" in sql_texts
        assert "SELECT * FROM orders;" in sql_texts


class TestFindExamplesByKeyword:
    """Tests for keyword search functionality."""

    @patch.object(KnowledgeBaseService, 'load_examples')
    def test_find_examples_by_keyword_in_title(self, mock_load):
        """Test finding examples by keyword in title."""
        mock_load.return_value = [
            KBExample(
                filename="active_users.sql",
                title="Active Users Query",
                description="Get active users",
                sql="SELECT * FROM users WHERE active = true;",
            ),
            KBExample(
                filename="orders.sql",
                title="Orders Query",
                description="Get orders",
                sql="SELECT * FROM orders;",
            ),
        ]

        service = KnowledgeBaseService()

        results = service.find_examples_by_keyword("user")

        assert len(results) == 1
        assert results[0].title == "Active Users Query"

    @patch.object(KnowledgeBaseService, 'load_examples')
    def test_find_examples_by_keyword_in_sql(self, mock_load):
        """Test finding examples by keyword in SQL."""
        mock_load.return_value = [
            KBExample(
                filename="query1.sql",
                title="Query 1",
                description="Test",
                sql="SELECT * FROM users JOIN orders ON users.id = orders.user_id;",
            ),
            KBExample(
                filename="query2.sql",
                title="Query 2",
                description="Test",
                sql="SELECT * FROM products;",
            ),
        ]

        service = KnowledgeBaseService()

        results = service.find_examples_by_keyword("orders")

        assert len(results) == 1
        assert "orders" in results[0].sql.lower()

    @patch.object(KnowledgeBaseService, 'load_examples')
    def test_find_examples_case_insensitive(self, mock_load):
        """Test keyword search is case-insensitive."""
        mock_load.return_value = [
            KBExample(
                filename="users.sql",
                title="Users Query",
                description="Get all users",
                sql="SELECT * FROM Users;",
            ),
        ]

        service = KnowledgeBaseService()

        results = service.find_examples_by_keyword("USERS")

        assert len(results) == 1

    @patch.object(KnowledgeBaseService, 'load_examples')
    def test_find_examples_no_match(self, mock_load):
        """Test keyword search with no matches."""
        mock_load.return_value = [
            KBExample(
                filename="users.sql",
                title="Users",
                description="Users",
                sql="SELECT * FROM users;",
            ),
        ]

        service = KnowledgeBaseService()

        results = service.find_examples_by_keyword("nonexistent")

        assert len(results) == 0


class TestServiceInitialization:
    """Tests for service initialization."""

    def test_init_empty_cache(self):
        """Test service initializes with empty cache."""
        service = KnowledgeBaseService()

        assert service._examples_cache is None
        assert service._kb_directory == Path("data/knowledge_base")
