#!/usr/bin/env python3
"""
Create New Migration Script

This script helps you create a new migration file with proper naming and structure.

Usage:
    python scripts/create_migration.py "add user preferences"
    python scripts/create_migration.py "create audit log table"
"""

import sys
from datetime import datetime
from pathlib import Path


MIGRATION_TEMPLATE = """-- =============================================================================
-- Migration: {description_title}
-- Created: {timestamp_readable}
-- Description: TODO: Add detailed description here
--
-- Tables/Changes:
--   - TODO: List tables created/modified
--   - TODO: List key changes made
-- =============================================================================

-- Enable foreign key constraints
pragma foreign_keys = on;

-- TODO: Add your SQL statements here

-- Example: Creating a new table
-- create table example (
--     id integer primary key autoincrement not null,
--     name text not null,
--     created_at text not null default (datetime('now'))
-- );

-- Example: Adding an index
-- create index idx_example_name on example(name);

-- Example: Adding a column to existing table
-- alter table users add column email text;

-- =============================================================================
-- Migration Complete
-- =============================================================================
"""


def create_migration(description: str) -> str:
    """
    Create a new migration file with proper timestamp and template
    
    Args:
        description: Short description of the migration (e.g., "add user preferences")
        
    Returns:
        Path to the created migration file
    """
    # Generate UTC timestamp
    now = datetime.utcnow()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    timestamp_readable = now.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Sanitize description for filename
    description_clean = description.lower()
    description_clean = description_clean.replace(' ', '_')
    description_clean = ''.join(c for c in description_clean if c.isalnum() or c == '_')
    
    # Create filename
    filename = f"{timestamp}_{description_clean}.sql"
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    migrations_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = migrations_dir / filename
    
    # Check if file already exists
    if filepath.exists():
        print(f"✗ Migration file already exists: {filepath}")
        sys.exit(1)
    
    # Create description title (capitalize first letter of each word)
    description_title = ' '.join(word.capitalize() for word in description.split())
    
    # Write migration file
    content = MIGRATION_TEMPLATE.format(
        description_title=description_title,
        timestamp_readable=timestamp_readable
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(filepath)


def main():
    if len(sys.argv) < 2:
        print("""
Create New Migration Script

Usage:
    python scripts/create_migration.py "description"
    
Examples:
    python scripts/create_migration.py "add user preferences"
    python scripts/create_migration.py "create audit log table"
    python scripts/create_migration.py "add email to users"

The script will:
1. Generate a UTC timestamp for the migration version
2. Create a properly named migration file
3. Fill in the migration template
4. Open the file for editing

Migration files are created in: migrations/YYYYMMDDHHmmss_description.sql
        """)
        sys.exit(1)
    
    description = sys.argv[1]
    
    if not description.strip():
        print("✗ Description cannot be empty")
        sys.exit(1)
    
    try:
        filepath = create_migration(description)
        
        print("\n" + "="*60)
        print("✓ Migration file created successfully!")
        print("="*60)
        print(f"\nFile: {filepath}")
        print("\nNext steps:")
        print("1. Edit the migration file to add your SQL statements")
        print("2. Test the migration:")
        print("   make db-dry-run")
        print("3. Apply the migration:")
        print("   make db-migrate")
        print("4. Commit the migration file to version control")
        print()
        
    except Exception as e:
        print(f"\n✗ Failed to create migration: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()