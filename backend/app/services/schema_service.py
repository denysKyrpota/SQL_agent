"""
Schema Service for loading and filtering PostgreSQL database schema.

Handles loading the schema from JSON files, caching in memory,
and filtering by table names for optimized LLM context.
"""

import json
import logging
from pathlib import Path
from typing import Any, cast

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SchemaService:
    """
    Service for managing PostgreSQL database schema.

    Loads schema from data/schema/ JSON files and provides
    filtering capabilities for the two-stage LLM process.
    """

    def __init__(self):
        """Initialize the schema service with empty cache."""
        self._schema_cache: dict[str, Any] | None = None
        self._tables_cache: dict[str, dict[str, Any]] | None = None

    def load_schema(self) -> dict[str, Any]:
        """
        Load PostgreSQL schema from JSON file.

        Reads the all_in_one_schema_overview JSON file which contains
        table definitions, columns, primary keys, and foreign keys.

        Returns:
            dict: Schema data with structure:
                {
                    "tables": {
                        "table_name": {
                            "columns": [...],
                            "primary_keys": [...],
                            "foreign_keys": [...]
                        }
                    },
                    "table_names": ["table1", "table2", ...]
                }

        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If JSON file is malformed
        """
        logger.info("Loading PostgreSQL schema from JSON file")

        # Path to schema file
        schema_file = Path(
            "data/schema/all_in_one_schema_overview__tables__columns__pks__fks__descriptions.json"
        )

        if not schema_file.exists():
            error_msg = f"Schema file not found: {schema_file}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # Load raw JSON data
            with open(schema_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            logger.info(f"Loaded schema file with {len(raw_data)} rows")

            # Transform flat row structure into hierarchical table structure
            schema = self._transform_schema(raw_data)

            logger.info(
                f"Schema loaded successfully: {len(schema['tables'])} tables, "
                f"{sum(len(t['columns']) for t in schema['tables'].values())} total columns"
            )

            return schema

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading schema: {e}", exc_info=True)
            raise

    def _transform_schema(self, raw_data: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Transform flat JSON rows into hierarchical table structure.

        Input format (from JSON):
        [
            {
                "table_name": "users",
                "column_name": "id",
                "data_type": "integer",
                "is_nullable": false,
                "is_primary_key": "YES",
                "target_table": null,
                "target_column": null,
                ...
            },
            ...
        ]

        Output format:
        {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "integer", "nullable": false},
                        ...
                    ],
                    "primary_keys": ["id"],
                    "foreign_keys": [
                        {"column": "role_id", "references_table": "roles", "references_column": "id"}
                    ]
                },
                ...
            },
            "table_names": ["users", "roles", ...]
        }

        Args:
            raw_data: Flat list of column definitions

        Returns:
            Hierarchical schema structure
        """
        tables: dict[str, dict[str, Any]] = {}

        for row in raw_data:
            table_name = row.get("table_name")
            if not table_name:
                continue

            # Initialize table if not exists
            if table_name not in tables:
                tables[table_name] = {
                    "columns": [],
                    "primary_keys": [],
                    "foreign_keys": [],
                    "description": row.get("table_description"),
                }

            table = tables[table_name]

            # Add column information
            column_info = {
                "name": row.get("column_name"),
                "type": row.get("data_type"),
                "nullable": row.get("is_nullable", True),
                "description": row.get("column_description"),
            }
            table["columns"].append(column_info)

            # Track primary keys
            if row.get("is_primary_key") == "YES":
                table["primary_keys"].append(row.get("column_name"))

            # Track foreign keys
            if row.get("target_table") and row.get("target_column"):
                fk_info = {
                    "column": row.get("column_name"),
                    "references_table": row.get("target_table"),
                    "references_column": row.get("target_column"),
                }
                # Avoid duplicates
                if fk_info not in table["foreign_keys"]:
                    table["foreign_keys"].append(fk_info)

        # Create sorted list of table names
        table_names = sorted(tables.keys())

        return {"tables": tables, "table_names": table_names}

    def get_schema(self) -> dict[str, Any]:
        """
        Get cached schema, loading from disk if not cached.

        This method implements lazy loading and caching for performance.
        The schema is loaded once on first access and reused thereafter.

        Returns:
            dict: Complete schema data
        """
        if self._schema_cache is None:
            logger.info("Schema not cached, loading from disk")
            self._schema_cache = self.load_schema()
        else:
            logger.debug("Returning cached schema")

        return self._schema_cache

    def get_table_names(self) -> list[str]:
        """
        Get list of all table names in alphabetical order.

        This is used for Stage 1 of the LLM process where we ask
        the LLM to select relevant tables.

        Returns:
            list[str]: Sorted list of table names
        """
        schema = self.get_schema()
        return cast(list[str], schema["table_names"])

    def filter_schema_by_tables(self, table_names: list[str]) -> dict[str, Any]:
        """
        Filter schema to include only specified tables.

        This is used for Stage 2 of the LLM process where we send
        only the relevant tables selected in Stage 1.

        Args:
            table_names: List of table names to include

        Returns:
            dict: Filtered schema containing only specified tables

        Example:
            >>> service = SchemaService()
            >>> filtered = service.filter_schema_by_tables(["users", "orders"])
            >>> len(filtered["tables"])
            2
        """
        full_schema = self.get_schema()

        # Filter tables
        filtered_tables = {
            name: full_schema["tables"][name]
            for name in table_names
            if name in full_schema["tables"]
        }

        # Log warning if any requested tables not found
        missing_tables = set(table_names) - set(filtered_tables.keys())
        if missing_tables:
            logger.warning(f"Requested tables not found in schema: {missing_tables}")

        logger.info(
            f"Filtered schema: {len(filtered_tables)} tables out of "
            f"{len(full_schema['tables'])} total"
        )

        return {
            "tables": filtered_tables,
            "table_names": sorted(filtered_tables.keys()),
        }

    def format_schema_for_llm(
        self,
        schema: dict[str, Any],
        include_descriptions: bool = True,
        include_foreign_keys: bool = True,
    ) -> str:
        """
        Format schema as readable text for LLM consumption.

        Converts the schema dict into a human-readable format that
        works well as context for OpenAI's GPT models.

        Args:
            schema: Schema data (full or filtered)
            include_descriptions: Whether to include table/column descriptions
            include_foreign_keys: Whether to include foreign key relationships

        Returns:
            str: Formatted schema text

        Example output:
            Table: users
              Columns:
                - id (integer, NOT NULL, PRIMARY KEY)
                - name (varchar, NOT NULL)
                - email (varchar, NULL)
              Foreign Keys:
                - role_id → roles.id
        """
        lines = []

        for table_name in schema["table_names"]:
            table = schema["tables"][table_name]

            # Table header
            lines.append(f"\nTable: {table_name}")

            if include_descriptions and table.get("description"):
                lines.append(f"  Description: {table['description']}")

            # Columns
            lines.append("  Columns:")
            for col in table["columns"]:
                col_parts = [col["name"]]
                col_parts.append(f"({col['type']}")

                # Nullable
                if col["nullable"]:
                    col_parts.append("NULL")
                else:
                    col_parts.append("NOT NULL")

                # Primary key
                if col["name"] in table["primary_keys"]:
                    col_parts.append("PRIMARY KEY")

                col_parts.append(")")

                col_line = f"    - {' '.join(col_parts)}"

                # Column description
                if include_descriptions and col.get("description"):
                    col_line += f" -- {col['description']}"

                lines.append(col_line)

            # Foreign keys
            if include_foreign_keys and table["foreign_keys"]:
                lines.append("  Foreign Keys:")
                for fk in table["foreign_keys"]:
                    lines.append(
                        f"    - {fk['column']} → "
                        f"{fk['references_table']}.{fk['references_column']}"
                    )

        return "\n".join(lines)

    def refresh_schema(self) -> dict[str, Any]:
        """
        Reload schema from disk, clearing cache.

        This method is called by the admin endpoint to refresh
        the schema without restarting the application.

        Returns:
            dict: Newly loaded schema data
        """
        logger.info("Refreshing schema cache (admin request)")
        self._schema_cache = None
        return self.load_schema()

    def get_table_info(self, table_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a specific table.

        Args:
            table_name: Name of the table

        Returns:
            dict | None: Table information or None if not found
        """
        schema = self.get_schema()
        return cast(dict[str, Any] | None, schema["tables"].get(table_name))

    def search_tables_by_keyword(self, keyword: str) -> list[str]:
        """
        Search for tables containing a keyword in their name.

        Useful for debugging or admin interfaces.

        Args:
            keyword: Search keyword (case-insensitive)

        Returns:
            list[str]: Matching table names

        Example:
            >>> service.search_tables_by_keyword("activity")
            ['activity_activity', 'activity_allocation', ...]
        """
        schema = self.get_schema()
        keyword_lower = keyword.lower()

        matching_tables = [
            name for name in schema["table_names"] if keyword_lower in name.lower()
        ]

        logger.info(f"Search for '{keyword}' found {len(matching_tables)} tables")

        return matching_tables
