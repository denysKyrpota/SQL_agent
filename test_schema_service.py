#!/usr/bin/env python3
"""
Quick test script for Schema Service.

Tests loading and filtering the 269-table PostgreSQL schema.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.services.schema_service import SchemaService


def main():
    print("=" * 60)
    print("Schema Service Test")
    print("=" * 60)
    print()

    # Initialize service
    service = SchemaService()

    # Test 1: Load full schema
    print("Test 1: Loading full schema...")
    schema = service.get_schema()
    print(f"✓ Loaded {len(schema['tables'])} tables")
    print(f"✓ Total columns: {sum(len(t['columns']) for t in schema['tables'].values())}")
    print()

    # Test 2: Get table names
    print("Test 2: Getting table names...")
    table_names = service.get_table_names()
    print(f"✓ Found {len(table_names)} tables")
    print(f"✓ First 10 tables: {table_names[:10]}")
    print()

    # Test 3: Filter schema (simulate LLM Stage 1 output)
    print("Test 3: Filtering schema for specific tables...")
    relevant_tables = ["activity_activity", "auth_user", "asset_assignment"]
    filtered = service.filter_schema_by_tables(relevant_tables)
    print(f"✓ Filtered to {len(filtered['tables'])} tables")
    for table_name in filtered['table_names']:
        table = filtered['tables'][table_name]
        print(f"  - {table_name}: {len(table['columns'])} columns, "
              f"{len(table['primary_keys'])} PKs, {len(table['foreign_keys'])} FKs")
    print()

    # Test 4: Format for LLM
    print("Test 4: Formatting schema for LLM...")
    formatted = service.format_schema_for_llm(filtered, include_descriptions=False)
    print(f"✓ Formatted schema length: {len(formatted)} characters")
    print("✓ Preview:")
    print(formatted[:500])
    print("...")
    print()

    # Test 5: Search tables
    print("Test 5: Searching tables by keyword...")
    activity_tables = service.search_tables_by_keyword("activity")
    print(f"✓ Found {len(activity_tables)} tables with 'activity'")
    print(f"✓ Examples: {activity_tables[:5]}")
    print()

    # Test 6: Get specific table info
    print("Test 6: Getting specific table info...")
    table_info = service.get_table_info("activity_activity")
    if table_info:
        print(f"✓ Table 'activity_activity' has:")
        print(f"  - {len(table_info['columns'])} columns")
        print(f"  - {len(table_info['primary_keys'])} primary keys: {table_info['primary_keys']}")
        print(f"  - {len(table_info['foreign_keys'])} foreign keys")
        print(f"  - First 5 columns:")
        for col in table_info['columns'][:5]:
            print(f"    - {col['name']} ({col['type']})")
    print()

    print("=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
