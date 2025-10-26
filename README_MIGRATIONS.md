# Database Migration Quick Reference

Quick guide for working with database migrations in the SQL AI Agent project.

## Quick Start

```bash
# Initialize database (first time setup)
make db-init

# Check migration status
make db-status

# Run new migrations
make db-migrate
```

## Common Commands

### Using Make (Recommended)

```bash
make db-init          # Initialize database with default users
make db-status        # Check migration status
make db-migrate       # Run pending migrations
make db-reset         # Reset database (deletes all data)
make db-shell         # Open SQLite shell
```

### Using Python Scripts Directly

```bash
# Initialize database
python scripts/init_db.py

# Run migrations
python backend/app/migrations_runner.py

# Check status
python backend/app/migrations_runner.py status

# Preview migrations
python backend/app/migrations_runner.py dry-run
```

## Default Users

After running `make db-init`, these users are created:

| Username | Password  | Role  |
|----------|-----------|-------|
| admin    | admin123  | admin |
| user     | user123   | user  |

⚠️ **Change these passwords in production!**

## Creating a New Migration

1. **Generate timestamp** (UTC):
   ```bash
   date -u +"%Y%m%d%H%M%S"
   # Output: 20251026155227
   ```

2. **Create file**: `migrations/YYYYMMDDHHmmss_description.sql`

3. **Write migration**:
   ```sql
   pragma foreign_keys = on;
   
   create table example (
       id integer primary key autoincrement not null,
       name text not null
   );
   ```

4. **Test migration**:
   ```bash
   make db-dry-run  # Preview
   make db-migrate  # Apply
   ```

## File Structure

```
project/
├── migrations/                          # Migration SQL files
│   └── 20251026155227_initial_schema.sql
├── backend/app/
│   └── migrations_runner.py            # Migration execution engine
├── scripts/
│   └── init_db.py                      # Database initialization
├── data/app_data/
│   └── app.db                          # SQLite database (created at runtime)
├── docs/
│   └── migrations.md                   # Full documentation
├── Makefile                            # Convenient commands
└── README_MIGRATIONS.md                # This file
```

## Database Schema

The initial migration creates these tables:

- **users** - User accounts with authentication
- **sessions** - Session tracking with 8-hour expiration
- **query_attempts** - Query history and audit log
- **query_results_manifest** - Result pagination metadata
- **schema_snapshots** - PostgreSQL schema cache
- **kb_examples_index** - Knowledge base file index
- **metrics_rollup** - Weekly analytics
- **schema_migrations** - Migration tracking (auto-created)

## Troubleshooting

### Database locked
```bash
# Close all connections and retry
make db-migrate
```

### Migration failed
```bash
# Check error, fix migration file, then:
sqlite3 data/app_data/app.db
> DELETE FROM schema_migrations WHERE version = 'YYYYMMDDHHmmss';
> .quit
make db-migrate
```

### Start fresh
```bash
make db-reset  # Deletes everything
make db-init   # Recreates from scratch
```

## Documentation

For detailed information, see [`docs/migrations.md`](docs/migrations.md)

## Tips

- ✓ Always use UTC timestamps for migration filenames
- ✓ Test migrations on development database first
- ✓ Never modify an applied migration (create new one instead)
- ✓ Use `make db-status` frequently to check state
- ✓ Commit migration files to version control
- ✓ Start migrations with `pragma foreign_keys = on;`