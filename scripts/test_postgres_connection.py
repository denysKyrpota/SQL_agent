#!/usr/bin/env python3
"""
Test PostgreSQL connection and query execution.

This script tests:
1. Database connectivity
2. Basic query execution
3. Schema introspection
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.config import get_settings
from backend.app.services.postgres_execution_service import PostgresExecutionService
from backend.app.services.schema_service import SchemaService


async def test_connection():
    """Test PostgreSQL connection and basic functionality."""
    settings = get_settings()

    print("=" * 80)
    print("PostgreSQL Connection Test")
    print("=" * 80)
    print(f"Database URL: {settings.postgres_url}")
    print()

    # Test 1: Connection
    print("Test 1: Testing database connection...")
    execution_service = PostgresExecutionService()

    try:
        # Try a simple query
        test_query = "SELECT version();"
        result = await execution_service.execute_query_raw(test_query)
        print("✓ Connection successful!")
        print(f"  PostgreSQL version: {result['rows'][0][0]}")
        print()
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

    # Test 2: Schema introspection
    print("Test 2: Testing schema introspection...")
    schema_service = SchemaService()

    try:
        # Get table count
        table_names = await schema_service.get_table_names()
        print(f"✓ Schema introspection successful!")
        print(f"  Found {len(table_names)} tables")
        print(f"  First 10 tables: {', '.join(table_names[:10])}")
        print()
    except Exception as e:
        print(f"✗ Schema introspection failed: {e}")
        return False

    # Test 3: Simple SELECT query
    print("Test 3: Testing simple SELECT query...")

    try:
        # Get a table to query
        if not table_names:
            print("✗ No tables found to query")
            return False

        # Try to query the first table
        first_table = table_names[0]
        test_query = f"SELECT * FROM {first_table} LIMIT 5;"

        result = await execution_service.execute_query_raw(test_query)
        print(f"✓ Query execution successful!")
        print(f"  Table: {first_table}")
        print(f"  Columns: {len(result['columns'])}")
        print(f"  Rows returned: {len(result['rows'])}")

        if result['columns']:
            print(f"  Column names: {', '.join(result['columns'][:5])}")

        print()
    except Exception as e:
        print(f"✗ Query execution failed: {e}")
        return False

    # Test 4: Full schema snapshot
    print("Test 4: Testing full schema snapshot...")

    try:
        schema = await schema_service.get_full_schema()

        total_columns = sum(len(table.get('columns', [])) for table in schema.values())
        print(f"✓ Full schema snapshot successful!")
        print(f"  Tables: {len(schema)}")
        print(f"  Total columns: {total_columns}")
        print()
    except Exception as e:
        print(f"✗ Schema snapshot failed: {e}")
        return False

    print("=" * 80)
    print("All tests passed! ✓")
    print("=" * 80)
    print()
    print("Your PostgreSQL connection is working correctly.")
    print("You can now:")
    print("  1. Start the backend server: python -m backend.app.main")
    print("  2. Access the frontend at: http://localhost:3000")
    print("  3. Submit natural language queries to generate and execute SQL")
    print()

    return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
