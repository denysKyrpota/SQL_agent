#!/usr/bin/env python3
"""
Simple PostgreSQL connection test.
Tests database connectivity and basic query execution.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from backend.app.config import get_settings


def test_connection():
    """Test PostgreSQL connection with a simple query."""
    settings = get_settings()

    print("=" * 80)
    print("PostgreSQL Connection Test")
    print("=" * 80)

    # Check if POSTGRES_URL is configured
    if not settings.postgres_url:
        print("✗ ERROR: POSTGRES_URL not configured in .env file")
        print()
        print("Please add this line to your .env file:")
        print("POSTGRES_URL=postgresql://user:password@host:port/dbname")
        return False

    # Mask password for display
    masked_url = settings.postgres_url.replace(
        settings.postgres_url.split(':')[2].split('@')[0],
        '***'
    )
    print(f"Database URL: {masked_url}")
    print()

    # Test 1: Connection
    print("Test 1: Testing database connection...")

    try:
        engine = create_engine(settings.postgres_url, pool_pre_ping=True)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]

            print("✓ Connection successful!")
            print(f"  PostgreSQL version: {version[:50]}...")
            print()
    except Exception as e:
        print(f"✗ Connection failed!")
        print(f"  Error: {e}")
        print()
        print("Please verify:")
        print("  1. PostgreSQL server is running at 192.168.3.25:5432")
        print("  2. Database 'boekestijn' exists")
        print("  3. User 'readonly_boekestijn' has access")
        print("  4. Password is correct")
        print("  5. Network allows connection to 192.168.3.25")
        return False

    # Test 2: List tables
    print("Test 2: Listing database tables...")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                LIMIT 10;
            """))

            tables = [row[0] for row in result]

            print(f"✓ Found {len(tables)} tables (showing first 10):")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
            print()
    except Exception as e:
        print(f"✗ Failed to list tables!")
        print(f"  Error: {e}")
        return False

    # Test 3: Query a table
    if tables:
        print(f"Test 3: Querying table '{tables[0]}'...")

        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT *
                    FROM {tables[0]}
                    LIMIT 3;
                """))

                rows = result.fetchall()
                columns = result.keys()

                print(f"✓ Query successful!")
                print(f"  Columns: {len(columns)} - {', '.join(list(columns)[:5])}{'...' if len(columns) > 5 else ''}")
                print(f"  Rows returned: {len(rows)}")
                print()
        except Exception as e:
            print(f"✗ Query failed!")
            print(f"  Error: {e}")
            return False

    # Success summary
    print("=" * 80)
    print("All tests passed! ✓")
    print("=" * 80)
    print()
    print("Your PostgreSQL connection is working correctly.")
    print()
    print("Next steps:")
    print("  1. Make sure backend server is running:")
    print("     python -m backend.app.main")
    print()
    print("  2. Access the frontend at:")
    print("     http://localhost:3000")
    print()
    print("  3. Try submitting a natural language query like:")
    print("     'Show me the first 10 rows from the largest table'")
    print()

    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
