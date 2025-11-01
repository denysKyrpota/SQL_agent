#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the SQLite database for the SQL AI Agent MVP.
Creates database tables using SQLAlchemy and optionally creates default users.

Usage:
    python scripts/init_db.py                    # Initialize with default users
    python scripts/init_db.py --no-defaults      # Initialize without default users
    python scripts/init_db.py --reset            # Reset database (WARNING: deletes all data)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to the Python path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.config import get_settings
from backend.app.database import init_db, reset_db, SessionLocal
from backend.app.services.auth_service import AuthService

logging.basicConfig(level=logging.INFO)


def create_default_users():
    """
    Create default admin and regular users using SQLAlchemy.

    Default credentials:
        Admin: username='admin', password='admin123'
        User: username='testuser', password='testpass123'

    WARNING: These are development defaults and should be changed in production!
    """
    print("\n" + "="*60)
    print("Creating Default Users")
    print("="*60)

    db = SessionLocal()
    auth_service = AuthService()

    try:
        from backend.app.models.user import User

        # Check if users already exist
        user_count = db.query(User).count()

        if user_count > 0:
            print(f"\n✓ Database already has {user_count} user(s)")
            print("Skipping default user creation.\n")
            return

        # Create admin user
        auth_service.create_user(
            db=db,
            username="admin",
            password="admin123",
            role="admin"
        )
        print("  ✓ Created admin user (username: admin, password: admin123)")

        # Create regular user
        auth_service.create_user(
            db=db,
            username="testuser",
            password="testpass123",
            role="user"
        )
        print("  ✓ Created regular user (username: testuser, password: testpass123)")

        print("\n⚠  SECURITY WARNING:")
        print("   Default passwords are for development only!")
        print("   Change these passwords immediately in production.\n")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Failed to create default users: {e}\n")
        raise

    finally:
        db.close()


def reset_database_confirm():
    """
    Reset the database after user confirmation.

    WARNING: This permanently deletes all data!
    """
    settings = get_settings()
    db_file = settings.database_url.replace("sqlite:///", "")

    if os.path.exists(db_file):
        print("\n" + "="*60)
        print("⚠  WARNING: DATABASE RESET")
        print("="*60)
        print(f"\nThis will permanently delete: {db_file}")
        response = input("Are you sure you want to continue? (yes/no): ")

        if response.lower() == 'yes':
            reset_db()
            print(f"\n✓ Database reset complete\n")
        else:
            print("\n✗ Database reset cancelled\n")
            sys.exit(0)
    else:
        print(f"\n✓ Database does not exist\n")


def verify_database():
    """
    Verify that the database was initialized correctly using SQLAlchemy.
    """
    print("\n" + "="*60)
    print("Verifying Database")
    print("="*60)

    db = SessionLocal()

    try:
        from backend.app.models.user import User
        from backend.app.models.query import QueryAttempt

        # Check users table
        user_count = db.query(User).count()
        print(f"\n  ✓ users table: {user_count} rows")

        # Check query_attempts table
        query_count = db.query(QueryAttempt).count()
        print(f"  ✓ query_attempts table: {query_count} rows")

        print("\n✓ Database verification complete\n")

    except Exception as e:
        print(f"\n✗ Database verification failed: {e}\n")
        raise

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Initialize the SQL AI Agent database using SQLAlchemy',
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

    settings = get_settings()

    print("\n" + "="*60)
    print("SQL AI Agent - Database Initialization")
    print("="*60)
    print(f"Database: {settings.database_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    try:
        # Reset database if requested
        if args.reset:
            reset_database_confirm()

        # Initialize database (create tables)
        print("Creating database tables...")
        init_db()
        print("✓ Database tables created\n")

        # Create default users unless --no-defaults specified
        if not args.no_defaults:
            create_default_users()

        # Verify the database
        verify_database()

        print("="*60)
        print("✓ Database initialization complete!")
        print("="*60)
        print("\nYou can now:")
        print("  1. Start the server: python -m backend.app.main")
        print("  2. Test login:")
        print('     curl -X POST http://localhost:8000/api/auth/login \\')
        print('       -H "Content-Type: application/json" \\')
        print('       -d \'{"username": "testuser", "password": "testpass123"}\'')
        print()

    except Exception as e:
        print("\n" + "="*60)
        print("✗ Database initialization failed!")
        print("="*60)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()