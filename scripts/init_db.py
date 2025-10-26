#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the SQLite database for the SQL AI Agent MVP.
It runs all migrations and optionally creates default users.

Usage:
    python scripts/init_db.py                    # Initialize with default users
    python scripts/init_db.py --no-defaults      # Initialize without default users
    python scripts/init_db.py --reset            # Reset database (WARNING: deletes all data)
"""

import os
import sys
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the Python path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.migrations_runner import run_migrations


def create_default_users(db_path: str):
    """
    Create default admin and regular users
    
    Default credentials:
        Admin: username='admin', password='admin123'
        User: username='user', password='user123'
    
    WARNING: These are development defaults and should be changed in production!
    """
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    except ImportError:
        print("\n⚠ Warning: passlib not installed. Install it with: pip install passlib[bcrypt]")
        print("Skipping default user creation.\n")
        return
    
    print("\n" + "="*60)
    print("Creating Default Users")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Check if users already exist
        cursor = conn.execute("select count(*) from users")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"\n✓ Database already has {user_count} user(s)")
            print("Skipping default user creation.\n")
            return
            
        # Create admin user
        admin_password = pwd_context.hash("admin123")
        conn.execute("""
            insert into users (username, password_hash, role, active)
            values (?, ?, ?, ?)
        """, ("admin", admin_password, "admin", 1))
        print("  ✓ Created admin user (username: admin, password: admin123)")
        
        # Create regular user
        user_password = pwd_context.hash("user123")
        conn.execute("""
            insert into users (username, password_hash, role, active)
            values (?, ?, ?, ?)
        """, ("user", user_password, "user", 1))
        print("  ✓ Created regular user (username: user, password: user123)")
        
        conn.commit()
        
        print("\n⚠  SECURITY WARNING:")
        print("   Default passwords are for development only!")
        print("   Change these passwords immediately in production.\n")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"\n✗ Failed to create default users: {e}\n")
        raise
        
    finally:
        conn.close()


def reset_database(db_path: str):
    """
    Reset the database by deleting it
    
    WARNING: This permanently deletes all data!
    """
    if os.path.exists(db_path):
        print("\n" + "="*60)
        print("⚠  WARNING: DATABASE RESET")
        print("="*60)
        print(f"\nThis will permanently delete: {db_path}")
        response = input("Are you sure you want to continue? (yes/no): ")
        
        if response.lower() == 'yes':
            os.remove(db_path)
            print(f"\n✓ Database deleted: {db_path}\n")
        else:
            print("\n✗ Database reset cancelled\n")
            sys.exit(0)
    else:
        print(f"\n✓ Database does not exist: {db_path}\n")


def verify_database(db_path: str):
    """
    Verify that the database was initialized correctly
    """
    print("\n" + "="*60)
    print("Verifying Database")
    print("="*60)
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Check for required tables
        cursor = conn.execute("""
            select name from sqlite_master 
            where type='table' 
            order by name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'users',
            'sessions',
            'query_attempts',
            'query_results_manifest',
            'schema_snapshots',
            'kb_examples_index',
            'metrics_rollup',
            'schema_migrations'
        ]
        
        print("\nTables:")
        for table in expected_tables:
            if table in tables:
                # Get row count
                cursor = conn.execute(f"select count(*) from {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table:30} ({count} rows)")
            else:
                print(f"  ✗ {table:30} (MISSING)")
        
        # Check foreign keys are enabled
        cursor = conn.execute("pragma foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        
        print(f"\nForeign Keys: {'✓ Enabled' if fk_enabled else '✗ Disabled'}")
        
        # Count migrations
        cursor = conn.execute("select count(*) from schema_migrations")
        migration_count = cursor.fetchone()[0]
        print(f"Applied Migrations: {migration_count}")
        
        print("\n✓ Database verification complete\n")
        
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Initialize the SQL AI Agent database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Initialize database with default users
    python scripts/init_db.py
    
    # Initialize without default users
    python scripts/init_db.py --no-defaults
    
    # Reset and reinitialize database
    python scripts/init_db.py --reset
        """
    )
    
    parser.add_argument(
        '--db-path',
        default='./data/app_data/app.db',
        help='Path to SQLite database file (default: ./data/app_data/app.db)'
    )
    
    parser.add_argument(
        '--no-defaults',
        action='store_true',
        help='Skip creating default users'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database before initialization (WARNING: deletes all data)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("SQL AI Agent - Database Initialization")
    print("="*60)
    print(f"Database: {args.db_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    try:
        # Reset database if requested
        if args.reset:
            reset_database(args.db_path)
        
        # Run migrations
        print("Running migrations...")
        migration_count = run_migrations(db_path=args.db_path)
        
        if migration_count == 0 and os.path.exists(args.db_path):
            print("Database already initialized and up to date.\n")
        
        # Create default users unless --no-defaults specified
        if not args.no_defaults:
            create_default_users(args.db_path)
        
        # Verify the database
        verify_database(args.db_path)
        
        print("="*60)
        print("✓ Database initialization complete!")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print("✗ Database initialization failed!")
        print("="*60)
        print(f"\nError: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()