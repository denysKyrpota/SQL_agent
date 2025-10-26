# Database Migrations Guide

This guide explains how to use the SQLite migration system for the SQL AI Agent MVP.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Migration Workflow](#migration-workflow)
4. [Creating Migrations](#creating-migrations)
5. [Running Migrations](#running-migrations)
6. [Migration Commands](#migration-commands)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The migration system uses timestamped SQL files to version and manage database schema changes. Each migration:

- Has a unique timestamp-based version (YYYYMMDDHHmmss)
- Contains pure SQL statements
- Is tracked in the `schema_migrations` table
- Runs exactly once in chronological order

### Key Components

- **Migrations Directory**: `migrations/` - Contains all migration SQL files
- **Migration Runner**: `backend/app/migrations_runner.py` - Executes migrations
- **Init Script**: `scripts/init_db.py` - Initializes new databases
- **Database**: `data/app_data/app.db` - SQLite application database

---

## Quick Start

### 1. Initialize a New Database

```bash
# Initialize database with default users (admin/admin123, user/user123)
python scripts/init_db.py

# Initialize without default users
python scripts/init_db.py --no-defaults

# Reset and reinitialize (WARNING: deletes all data)
python scripts/init_db.py --reset
```

### 2. Check Migration Status

```bash
python backend/app/migrations_runner.py status
```

### 3. Run Pending Migrations

```bash
# See what would be run without executing
python backend/app/migrations_runner.py dry-run

# Run all pending migrations
python backend/app/migrations_runner.py
```

---

## Migration Workflow

### Typical Development Flow

1. **Plan Schema Changes** - Document what needs to change in your database
2. **Create Migration File** - Write a new migration with timestamp prefix
3. **Test Migration** - Run migration on development database
4. **Verify Changes** - Check that tables/indexes were created correctly
5. **Commit Migration** - Add migration file to version control
6. **Deploy** - Run migrations on other environments

### Migration Lifecycle

```
Migration File Created
         ↓
   Pending Status
         ↓
  Migration Executed
         ↓
   Recorded in schema_migrations
         ↓
    Applied Status
```

---

## Creating Migrations

### Naming Convention

Migration files **must** follow this format:

```
YYYYMMDDHHmmss_short_description.sql
```

- `YYYY` - Four-digit year (e.g., 2025)
- `MM` - Two-digit month (01-12)
- `DD` - Two-digit day (01-31)
- `HH` - Two-digit hour in 24h format (00-23)
- `mm` - Two-digit minute (00-59)
- `ss` - Two-digit second (00-59)
- `short_description` - Lowercase with underscores

**Examples:**
```
20251026155227_initial_schema.sql
20251027120000_add_user_preferences.sql
20251028093045_create_audit_log.sql
```

### Migration File Structure

```sql
-- =============================================================================
-- Migration: Brief Description
-- Created: YYYY-MM-DD HH:MM:SS UTC
-- Description: Detailed explanation of what this migration does
--
-- Tables/Changes:
--   - List of tables created/modified
--   - Key changes made
-- =============================================================================

-- Enable foreign key constraints
pragma foreign_keys = on;

-- Your SQL statements here
create table example (
    id integer primary key autoincrement not null,
    name text not null
);

-- Add indexes
create index idx_example_name on example(name);

-- =============================================================================
-- Migration Complete
-- =============================================================================
```

### SQL Guidelines

1. **Use Lowercase Keywords**: Write `create table` not `CREATE TABLE`
2. **Comment Extensively**: Explain the purpose of each table and column
3. **Enable Foreign Keys**: Always start with `pragma foreign_keys = on;`
4. **Use SQLite Types**: TEXT, INTEGER, REAL, BLOB, NUMERIC
5. **Add Metadata**: Include creation date and description in header
6. **Destructive Operations**: Add warnings for DROP, DELETE, or ALTER statements

### Example: Adding a New Table

```sql
-- =============================================================================
-- Migration: Add User Preferences Table
-- Created: 2025-10-27 12:00:00 UTC
-- Description: Creates a user_preferences table to store UI settings
--
-- Tables Created:
--   - user_preferences: Stores per-user UI preferences
-- =============================================================================

pragma foreign_keys = on;

-- Create user preferences table
create table user_preferences (
    -- Primary key links to users table
    user_id integer primary key not null references users(id) on delete cascade,
    
    -- UI theme preference
    theme text not null default 'light' check (theme in ('light', 'dark')),
    
    -- Preferred page size for results
    results_per_page integer not null default 500 check (results_per_page > 0),
    
    -- Timestamp tracking
    created_at text not null default (datetime('now')),
    updated_at text not null default (datetime('now'))
);

-- Index for efficient lookups (though primary key already covers this)
-- Included for consistency with other tables
create index idx_user_prefs_user_id on user_preferences(user_id);
```

### Example: Modifying Existing Tables

```sql
-- =============================================================================
-- Migration: Add Email to Users
-- Created: 2025-10-28 09:30:45 UTC
-- Description: Adds optional email field to users table
--
-- Tables Modified:
--   - users: Added email column
-- =============================================================================

pragma foreign_keys = on;

-- Add email column to users table
-- NOTE: SQLite's ALTER TABLE is limited; cannot add NOT NULL columns without default
alter table users add column email text;

-- Create index for email lookups
create index idx_users_email on users(email);
```

---

## Running Migrations

### Using the Migration Runner

The migration runner (`backend/app/migrations_runner.py`) provides several commands:

#### Run All Pending Migrations

```bash
python backend/app/migrations_runner.py
```

Output:
```
============================================================
SQLite Migration Runner
============================================================
Database: ./data/app_data/app.db
Migrations directory: ./migrations
============================================================

Applied migrations: 1
Pending migrations: 2

  → Running migration 20251027120000_add_user_preferences...
  ✓ Migration 20251027120000_add_user_preferences completed successfully
  → Running migration 20251028093045_add_email_to_users...
  ✓ Migration 20251028093045_add_email_to_users completed successfully

✓ Successfully applied 2 migration(s)
```

#### Check Status

```bash
python backend/app/migrations_runner.py status
```

Output:
```
============================================================
Migration Status
============================================================

Database: ./data/app_data/app.db
Total migrations available: 3
Applied migrations: 3

Migration History:
------------------------------------------------------------
✓ Applied    | 20251026155227_initial_schema
✓ Applied    | 20251027120000_add_user_preferences
✓ Applied    | 20251028093045_add_email_to_users
```

#### Dry Run (Preview)

```bash
python backend/app/migrations_runner.py dry-run
```

Output:
```
============================================================
SQLite Migration Runner
============================================================
Database: ./data/app_data/app.db
Migrations directory: ./migrations
============================================================

Applied migrations: 1
Pending migrations: 2

DRY RUN - Would apply the following migrations:
  - 20251027120000_add_user_preferences
  - 20251028093045_add_email_to_users
```

### Using from Python Code

```python
from backend.app.migrations_runner import run_migrations, get_status

# Run migrations programmatically
count = run_migrations(db_path='./data/app_data/app.db')
print(f"Applied {count} migration(s)")

# Check status
get_status(db_path='./data/app_data/app.db')
```

### Integration with Application Startup

Add to your FastAPI application startup:

```python
# backend/app/main.py
from fastapi import FastAPI
from backend.app.migrations_runner import run_migrations
from backend.app.config import settings

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Run migrations on application startup"""
    try:
        count = run_migrations(db_path=settings.SQLITE_URL)
        if count > 0:
            print(f"Applied {count} database migration(s)")
    except Exception as e:
        print(f"Migration error: {e}")
        # Decide whether to continue or fail based on your requirements
```

---

## Migration Commands

### Command Reference

| Command | Description |
|---------|-------------|
| `python backend/app/migrations_runner.py` | Run all pending migrations |
| `python backend/app/migrations_runner.py status` | Show migration status |
| `python backend/app/migrations_runner.py dry-run` | Preview pending migrations |
| `python backend/app/migrations_runner.py help` | Show help message |
| `python scripts/init_db.py` | Initialize database with migrations |
| `python scripts/init_db.py --reset` | Reset and reinitialize database |

### Database Initialization Script

The `init_db.py` script provides a complete database setup:

```bash
# Full initialization with defaults
python scripts/init_db.py

# Options
python scripts/init_db.py --no-defaults      # Skip default users
python scripts/init_db.py --reset            # Delete and recreate
python scripts/init_db.py --db-path /path    # Custom database path
```

The script:
1. Creates the database directory if needed
2. Runs all pending migrations
3. Creates default users (unless `--no-defaults`)
4. Verifies the database structure

---

## Best Practices

### DO ✓

1. **Always Use Timestamps**: Use UTC time for migration filenames
2. **One Purpose Per Migration**: Each migration should do one logical thing
3. **Comment Thoroughly**: Explain why changes are made, not just what
4. **Test Before Committing**: Run migrations on development database first
5. **Keep Migrations Immutable**: Never modify an applied migration
6. **Use Transactions**: SQLite handles this automatically via `executescript()`
7. **Enable Foreign Keys**: Start every migration with `pragma foreign_keys = on;`
8. **Version Control**: Commit migration files to git

### DON'T ✗

1. **Don't Modify Applied Migrations**: Create a new migration instead
2. **Don't Delete Migrations**: They're part of your schema history
3. **Don't Use Application Code**: Migrations should be pure SQL
4. **Don't Assume Order**: Migrations run chronologically by timestamp
5. **Don't Skip Testing**: Always test migrations before production
6. **Don't Use Database-Specific Features**: Stick to SQLite-compatible SQL

### Handling Data Migrations

If you need to migrate data, create a separate Python script:

```python
# scripts/migrate_data_v2.py
import sqlite3

def migrate_data():
    conn = sqlite3.connect('./data/app_data/app.db')
    try:
        # Your data migration logic here
        conn.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_data()
```

---

## Troubleshooting

### Common Issues

#### Migration File Not Found

**Problem**: Migration file exists but isn't detected

**Solution**:
- Check filename follows exact format: `YYYYMMDDHHmmss_description.sql`
- Ensure file is in `migrations/` directory
- Verify file has `.sql` extension

#### Foreign Key Constraint Failed

**Problem**: Migration fails with foreign key error

**Solution**:
```sql
-- Ensure foreign keys are enabled at the start
pragma foreign_keys = on;

-- Check that referenced tables exist first
-- Create parent tables before child tables with foreign keys
```

#### Migration Already Applied

**Problem**: Migration shows as applied but you want to re-run it

**Solution**:
```bash
# Option 1: Create a new migration with the fixes
python scripts/init_db.py  # This won't re-run old migrations

# Option 2: Reset database (WARNING: deletes all data)
python scripts/init_db.py --reset
```

#### SQLite Locked

**Problem**: "database is locked" error

**Solution**:
- Close all database connections
- Check if another process is using the database
- Ensure your application isn't running during migrations

#### Column Already Exists

**Problem**: `ALTER TABLE ADD COLUMN` fails because column exists

**Solution**:
```sql
-- SQLite doesn't have IF NOT EXISTS for columns
-- Instead, handle this in your migration by checking first:

-- Option 1: Create new migration that's idempotent
-- Option 2: Document that this migration requires fresh database
```

### Debugging Migrations

Enable verbose output:

```python
import sqlite3

conn = sqlite3.connect('./data/app_data/app.db')
conn.set_trace_callback(print)  # Print all SQL statements
```

Check migration table:

```bash
sqlite3 data/app_data/app.db "SELECT * FROM schema_migrations ORDER BY applied_at"
```

### Recovery Procedures

#### Recover from Failed Migration

1. Check error message to identify issue
2. Fix the migration file
3. Manually remove failed migration from tracking:

```bash
sqlite3 data/app_data/app.db
> DELETE FROM schema_migrations WHERE version = '20251027120000';
> .quit
```

4. Re-run migrations:

```bash
python backend/app/migrations_runner.py
```

#### Complete Database Reset

If database is corrupted:

```bash
# Backup existing database (optional)
cp data/app_data/app.db data/app_data/app.db.backup

# Reset and reinitialize
python scripts/init_db.py --reset
```

---

## Advanced Topics

### Custom Migration Path

```python
from backend.app.migrations_runner import MigrationRunner

runner = MigrationRunner(
    db_path='./custom/path/database.db',
    migrations_dir='./custom/migrations'
)
runner.run_migrations()
```

### Programmatic Migration Creation

```python
from datetime import datetime

def create_migration(description: str, sql_content: str):
    """Helper to create a new migration file"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"migrations/{timestamp}_{description}.sql"
    
    with open(filename, 'w') as f:
        f.write(sql_content)
    
    print(f"Created migration: {filename}")
```

### Testing Migrations

```python
# tests/test_migrations.py
import pytest
import sqlite3
from backend.app.migrations_runner import MigrationRunner

def test_initial_migration():
    """Test that initial migration creates all tables"""
    db_path = ':memory:'  # In-memory database for testing
    runner = MigrationRunner(db_path=db_path)
    
    count = runner.run_migrations()
    assert count > 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = {row[0] for row in cursor.fetchall()}
    
    assert 'users' in tables
    assert 'sessions' in tables
    assert 'query_attempts' in tables
```

---

## Summary

The migration system provides:

- ✓ **Version Control**: Track database schema changes over time
- ✓ **Reproducibility**: Apply same changes across environments
- ✓ **Safety**: Run migrations exactly once, in order
- ✓ **Simplicity**: Pure SQL files, no complex tools needed
- ✓ **Transparency**: Clear audit trail in `schema_migrations` table

For questions or issues, refer to the project documentation or create an issue in the repository.