"""
Tests for SchemaService - PostgreSQL schema loading and filtering.

Tests:
- Schema loading from JSON files
- Schema transformation
- Schema caching
- Table filtering
- Schema formatting for LLM
- Table search
"""

import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from backend.app.services.schema_service import SchemaService


@pytest.fixture
def sample_raw_schema():
    """Sample raw schema data (flat format from JSON file)."""
    return [
        {
            "table_name": "users",
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": False,
            "is_primary_key": "YES",
            "target_table": None,
            "target_column": None,
            "table_description": "User accounts",
            "column_description": "User ID"
        },
        {
            "table_name": "users",
            "column_name": "username",
            "data_type": "varchar",
            "is_nullable": False,
            "is_primary_key": "NO",
            "target_table": None,
            "target_column": None,
            "table_description": "User accounts",
            "column_description": "Unique username"
        },
        {
            "table_name": "orders",
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": False,
            "is_primary_key": "YES",
            "target_table": None,
            "target_column": None,
            "table_description": "Customer orders",
            "column_description": "Order ID"
        },
        {
            "table_name": "orders",
            "column_name": "user_id",
            "data_type": "integer",
            "is_nullable": False,
            "is_primary_key": "NO",
            "target_table": "users",
            "target_column": "id",
            "table_description": "Customer orders",
            "column_description": "Reference to user"
        }
    ]


class TestTransformSchema:
    """Tests for schema transformation logic."""

    def test_transform_schema_basic(self, sample_raw_schema):
        """Test transforming flat schema to hierarchical structure."""
        service = SchemaService()

        result = service._transform_schema(sample_raw_schema)

        assert "tables" in result
        assert "table_names" in result
        assert len(result["tables"]) == 2
        assert "users" in result["tables"]
        assert "orders" in result["tables"]
        assert result["table_names"] == ["orders", "users"]  # Sorted

    def test_transform_schema_columns(self, sample_raw_schema):
        """Test column information transformation."""
        service = SchemaService()

        result = service._transform_schema(sample_raw_schema)

        users_table = result["tables"]["users"]
        assert len(users_table["columns"]) == 2

        # Check first column
        id_column = users_table["columns"][0]
        assert id_column["name"] == "id"
        assert id_column["type"] == "integer"
        assert id_column["nullable"] == False
        assert id_column["description"] == "User ID"

    def test_transform_schema_primary_keys(self, sample_raw_schema):
        """Test primary key extraction."""
        service = SchemaService()

        result = service._transform_schema(sample_raw_schema)

        users_table = result["tables"]["users"]
        assert "id" in users_table["primary_keys"]
        assert "username" not in users_table["primary_keys"]

        orders_table = result["tables"]["orders"]
        assert "id" in orders_table["primary_keys"]

    def test_transform_schema_foreign_keys(self, sample_raw_schema):
        """Test foreign key extraction."""
        service = SchemaService()

        result = service._transform_schema(sample_raw_schema)

        orders_table = result["tables"]["orders"]
        assert len(orders_table["foreign_keys"]) == 1

        fk = orders_table["foreign_keys"][0]
        assert fk["column"] == "user_id"
        assert fk["references_table"] == "users"
        assert fk["references_column"] == "id"

    def test_transform_schema_empty_data(self):
        """Test transforming empty schema data."""
        service = SchemaService()

        result = service._transform_schema([])

        assert result["tables"] == {}
        assert result["table_names"] == []

    def test_transform_schema_invalid_rows(self):
        """Test transforming with some invalid rows."""
        service = SchemaService()

        raw_data = [
            {
                "table_name": None,  # Invalid: no table name
                "column_name": "id",
                "data_type": "integer"
            },
            {
                "table_name": "valid_table",
                "column_name": "id",
                "data_type": "integer",
                "is_nullable": False,
                "is_primary_key": "YES"
            }
        ]

        result = service._transform_schema(raw_data)

        # Should skip invalid row and process valid one
        assert len(result["tables"]) == 1
        assert "valid_table" in result["tables"]


class TestFilterSchemaByTables:
    """Tests for schema filtering."""

    @patch.object(SchemaService, 'load_schema')
    def test_filter_schema_by_tables(self, mock_load, mock_schema_data):
        """Test filtering schema to specific tables."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        # Filter to just 'users' table
        filtered = service.filter_schema_by_tables(["users"])

        assert len(filtered["tables"]) == 1
        assert "users" in filtered["tables"]
        assert "sessions" not in filtered["tables"]
        assert filtered["table_names"] == ["users"]

    @patch.object(SchemaService, 'load_schema')
    def test_filter_schema_multiple_tables(self, mock_load, mock_schema_data):
        """Test filtering to multiple tables."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        filtered = service.filter_schema_by_tables(["users", "sessions"])

        assert len(filtered["tables"]) == 2
        assert "users" in filtered["tables"]
        assert "sessions" in filtered["tables"]

    @patch.object(SchemaService, 'load_schema')
    def test_filter_schema_nonexistent_table(self, mock_load, mock_schema_data):
        """Test filtering with non-existent table name."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        filtered = service.filter_schema_by_tables(["users", "nonexistent"])

        # Should include only existing table
        assert len(filtered["tables"]) == 1
        assert "users" in filtered["tables"]
        assert "nonexistent" not in filtered["tables"]

    @patch.object(SchemaService, 'load_schema')
    def test_filter_schema_empty_list(self, mock_load, mock_schema_data):
        """Test filtering with empty table list."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        filtered = service.filter_schema_by_tables([])

        assert len(filtered["tables"]) == 0
        assert filtered["table_names"] == []


class TestFormatSchemaForLLM:
    """Tests for LLM-friendly schema formatting."""

    def test_format_schema_basic(self, mock_schema_data):
        """Test basic schema formatting."""
        service = SchemaService()

        formatted = service.format_schema_for_llm(mock_schema_data)

        assert "Table: users" in formatted
        assert "Table: sessions" in formatted
        assert "Columns:" in formatted

    def test_format_schema_column_details(self, mock_schema_data):
        """Test column details in formatted output."""
        service = SchemaService()

        formatted = service.format_schema_for_llm(mock_schema_data)

        # Check for column information
        assert "id" in formatted
        assert "integer" in formatted
        assert "NOT NULL" in formatted
        assert "PRIMARY KEY" in formatted

    def test_format_schema_foreign_keys(self, mock_schema_data):
        """Test foreign key formatting."""
        service = SchemaService()

        formatted = service.format_schema_for_llm(
            mock_schema_data,
            include_foreign_keys=True
        )

        assert "Foreign Keys:" in formatted
        assert "user_id → users.id" in formatted

    def test_format_schema_without_foreign_keys(self, mock_schema_data):
        """Test formatting without foreign keys."""
        service = SchemaService()

        formatted = service.format_schema_for_llm(
            mock_schema_data,
            include_foreign_keys=False
        )

        assert "Foreign Keys:" not in formatted

    def test_format_schema_without_descriptions(self, mock_schema_data):
        """Test formatting without descriptions."""
        service = SchemaService()

        formatted = service.format_schema_for_llm(
            mock_schema_data,
            include_descriptions=False
        )

        # Should not include descriptions
        lines = formatted.split('\n')
        description_lines = [l for l in lines if "Description:" in l]
        assert len(description_lines) == 0


class TestGetTableNames:
    """Tests for get_table_names method."""

    @patch.object(SchemaService, 'load_schema')
    def test_get_table_names(self, mock_load, mock_schema_data):
        """Test retrieving table names list."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        table_names = service.get_table_names()

        assert isinstance(table_names, list)
        assert "users" in table_names
        assert "sessions" in table_names
        assert len(table_names) == len(mock_schema_data["table_names"])


class TestGetTableInfo:
    """Tests for get_table_info method."""

    @patch.object(SchemaService, 'load_schema')
    def test_get_table_info_success(self, mock_load, mock_schema_data):
        """Test getting info for existing table."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        info = service.get_table_info("users")

        assert info is not None
        assert "columns" in info
        assert "primary_keys" in info
        assert "foreign_keys" in info

    @patch.object(SchemaService, 'load_schema')
    def test_get_table_info_not_found(self, mock_load, mock_schema_data):
        """Test getting info for non-existent table."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        info = service.get_table_info("nonexistent")

        assert info is None


class TestSearchTablesByKeyword:
    """Tests for table search functionality."""

    @patch.object(SchemaService, 'load_schema')
    def test_search_tables_by_keyword_match(self, mock_load):
        """Test searching tables with matching keyword."""
        mock_load.return_value = {
            "tables": {
                "activity_activity": {},
                "activity_allocation": {},
                "user_activity": {},
                "users": {}
            },
            "table_names": ["activity_activity", "activity_allocation", "user_activity", "users"]
        }
        service = SchemaService()

        results = service.search_tables_by_keyword("activity")

        assert len(results) == 3
        assert "activity_activity" in results
        assert "activity_allocation" in results
        assert "user_activity" in results
        assert "users" not in results

    @patch.object(SchemaService, 'load_schema')
    def test_search_tables_case_insensitive(self, mock_load):
        """Test search is case-insensitive."""
        mock_load.return_value = {
            "tables": {
                "Users": {},
                "ORDERS": {},
                "products": {}
            },
            "table_names": ["Users", "ORDERS", "products"]
        }
        service = SchemaService()

        results = service.search_tables_by_keyword("USER")

        assert len(results) == 1
        assert "Users" in results

    @patch.object(SchemaService, 'load_schema')
    def test_search_tables_no_match(self, mock_load, mock_schema_data):
        """Test searching with no matches."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        results = service.search_tables_by_keyword("nonexistent")

        assert len(results) == 0


class TestCaching:
    """Tests for schema caching behavior."""

    @patch.object(SchemaService, 'load_schema')
    def test_get_schema_loads_once(self, mock_load, mock_schema_data):
        """Test schema is loaded once and cached."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        # First call should load
        schema1 = service.get_schema()
        assert mock_load.call_count == 1

        # Second call should use cache
        schema2 = service.get_schema()
        assert mock_load.call_count == 1  # Still just 1

        # Both should return same data
        assert schema1 == schema2

    @patch.object(SchemaService, 'load_schema')
    def test_refresh_schema_clears_cache(self, mock_load, mock_schema_data):
        """Test refresh_schema clears cache and reloads."""
        mock_load.return_value = mock_schema_data
        service = SchemaService()

        # Load schema
        service.get_schema()
        assert mock_load.call_count == 1

        # Refresh should reload
        service.refresh_schema()
        assert mock_load.call_count == 2


class TestLoadSchema:
    """Tests for schema file loading."""

    @patch('builtins.open', new_callable=mock_open, read_data='[]')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_schema_file_not_found(self, mock_exists, mock_file):
        """Test loading when file doesn't exist."""
        mock_exists.return_value = False
        service = SchemaService()

        with pytest.raises(FileNotFoundError, match="Schema file not found"):
            service.load_schema()

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_schema_invalid_json(self, mock_exists, mock_file):
        """Test loading with invalid JSON."""
        service = SchemaService()

        with pytest.raises(json.JSONDecodeError):
            service.load_schema()


class TestServiceInitialization:
    """Tests for SchemaService initialization."""

    def test_init_empty_cache(self):
        """Test service initializes with empty cache."""
        service = SchemaService()

        assert service._schema_cache is None
        assert service._tables_cache is None
