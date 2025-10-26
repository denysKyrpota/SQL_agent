"""
SQLite Migration Runner

This module provides functionality to run SQL migrations in order,
tracking which migrations have been applied to avoid re-running them.

Usage:
    python backend/app/migrations_runner.py
    
Or from another module:
    from backend.app.migrations_runner import run_migrations
    run_migrations(db_path='./data/app_data/app.db')
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple
import re
from datetime import datetime


class MigrationRunner:
    """Handles database migrations for SQLite"""
    
    def __init__(self, db_path: str = './data/app_data/app.db', migrations_dir: str = './migrations'):
        """
        Initialize the migration runner
        
        Args:
            db_path: Path to the SQLite database file
            migrations_dir: Directory containing migration SQL files
        """
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def _ensure_migrations_table(self, conn: sqlite3.Connection):
        """
        Create the schema_migrations table if it doesn't exist
        
        This table tracks which migrations have been applied
        """
        conn.execute("""
            create table if not exists schema_migrations (
                id integer primary key autoincrement,
                version text not null unique,
                name text not null,
                applied_at text not null default (datetime('now'))
            )
        """)
        conn.commit()
        
    def _get_applied_migrations(self, conn: sqlite3.Connection) -> set:
        """
        Get the set of migration versions that have already been applied
        
        Returns:
            Set of migration version strings (e.g., '20251026155227')
        """
        cursor = conn.execute("select version from schema_migrations order by version")
        return {row[0] for row in cursor.fetchall()}
        
    def _get_pending_migrations(self) -> List[Tuple[str, str, Path]]:
        """
        Get list of migration files that haven't been applied yet
        
        Returns:
            List of tuples: (version, name, file_path)
            Sorted by version (oldest first)
        """
        if not self.migrations_dir.exists():
            return []
            
        # Migration filename pattern: YYYYMMDDHHmmss_description.sql
        migration_pattern = re.compile(r'^(\d{14})_(.+)\.sql$')
        
        migrations = []
        for file_path in self.migrations_dir.glob('*.sql'):
            match = migration_pattern.match(file_path.name)
            if match:
                version = match.group(1)
                name = match.group(2)
                migrations.append((version, name, file_path))
                
        # Sort by version (timestamp)
        migrations.sort(key=lambda x: x[0])
        return migrations
        
    def _execute_migration(self, conn: sqlite3.Connection, version: str, name: str, file_path: Path):
        """
        Execute a single migration file
        
        Args:
            conn: Database connection
            version: Migration version string
            name: Migration name
            file_path: Path to the migration SQL file
        """
        print(f"  → Running migration {version}_{name}...")
        
        # Read the migration file
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        try:
            # Execute the migration SQL
            conn.executescript(sql_content)
            
            # Record that this migration has been applied
            conn.execute(
                "insert into schema_migrations (version, name) values (?, ?)",
                (version, name)
            )
            conn.commit()
            
            print(f"  ✓ Migration {version}_{name} completed successfully")
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"  ✗ Migration {version}_{name} failed: {e}")
            raise
            
    def run_migrations(self, dry_run: bool = False) -> int:
        """
        Run all pending migrations
        
        Args:
            dry_run: If True, show what would be run without executing
            
        Returns:
            Number of migrations applied
        """
        print(f"\n{'='*60}")
        print("SQLite Migration Runner")
        print(f"{'='*60}")
        print(f"Database: {self.db_path}")
        print(f"Migrations directory: {self.migrations_dir}")
        print(f"{'='*60}\n")
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Ensure the migrations tracking table exists
            self._ensure_migrations_table(conn)
            
            # Get applied and pending migrations
            applied = self._get_applied_migrations(conn)
            all_migrations = self._get_pending_migrations()
            
            # Filter to only pending migrations
            pending = [m for m in all_migrations if m[0] not in applied]
            
            print(f"Applied migrations: {len(applied)}")
            print(f"Pending migrations: {len(pending)}\n")
            
            if not pending:
                print("✓ Database is up to date - no pending migrations\n")
                return 0
                
            if dry_run:
                print("DRY RUN - Would apply the following migrations:")
                for version, name, _ in pending:
                    print(f"  - {version}_{name}")
                print()
                return len(pending)
                
            # Apply each pending migration
            for version, name, file_path in pending:
                self._execute_migration(conn, version, name, file_path)
                
            print(f"\n✓ Successfully applied {len(pending)} migration(s)\n")
            return len(pending)
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}\n")
            raise
            
        finally:
            conn.close()
            
    def get_migration_status(self):
        """
        Display the current migration status
        """
        print(f"\n{'='*60}")
        print("Migration Status")
        print(f"{'='*60}\n")
        
        if not os.path.exists(self.db_path):
            print("Database does not exist yet - needs initialization\n")
            return
            
        conn = sqlite3.connect(self.db_path)
        
        try:
            self._ensure_migrations_table(conn)
            applied = self._get_applied_migrations(conn)
            all_migrations = self._get_pending_migrations()
            
            print(f"Database: {self.db_path}")
            print(f"Total migrations available: {len(all_migrations)}")
            print(f"Applied migrations: {len(applied)}\n")
            
            if not all_migrations:
                print("No migration files found in migrations/\n")
                return
                
            print("Migration History:")
            print("-" * 60)
            
            for version, name, _ in all_migrations:
                status = "✓ Applied" if version in applied else "⧗ Pending"
                print(f"{status:12} | {version}_{name}")
                
            print()
            
        finally:
            conn.close()


def run_migrations(db_path: str = './data/app_data/app.db', dry_run: bool = False) -> int:
    """
    Convenience function to run migrations
    
    Args:
        db_path: Path to the SQLite database file
        dry_run: If True, show what would be run without executing
        
    Returns:
        Number of migrations applied
    """
    runner = MigrationRunner(db_path=db_path)
    return runner.run_migrations(dry_run=dry_run)


def get_status(db_path: str = './data/app_data/app.db'):
    """
    Convenience function to check migration status
    
    Args:
        db_path: Path to the SQLite database file
    """
    runner = MigrationRunner(db_path=db_path)
    runner.get_migration_status()


if __name__ == '__main__':
    import sys
    
    # Simple CLI
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            get_status()
        elif command == 'dry-run':
            run_migrations(dry_run=True)
        elif command == 'help':
            print("""
SQLite Migration Runner

Commands:
    python backend/app/migrations_runner.py           Run all pending migrations
    python backend/app/migrations_runner.py status    Show migration status
    python backend/app/migrations_runner.py dry-run   Show what would be run
    python backend/app/migrations_runner.py help      Show this help message

The runner automatically:
- Creates the database if it doesn't exist
- Tracks which migrations have been applied
- Runs migrations in order based on their timestamp
- Ensures migrations are only run once
            """)
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' to see available commands")
            sys.exit(1)
    else:
        # Default: run migrations
        run_migrations()