#!/usr/bin/env python3
"""
User Management Script

Manage users for the SQL AI Agent application.

Usage:
    python scripts/manage_users.py change-password <username>
    python scripts/manage_users.py list
    python scripts/manage_users.py create <username> --role user
"""

import sys
import getpass
import argparse
from pathlib import Path

# Add the parent directory to the Python path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.services.auth_service import AuthService


def change_password(args):
    """Change a user's password."""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=args.username).first()
        if not user:
            print(f"Error: user '{args.username}' not found.")
            sys.exit(1)

        password = getpass.getpass(f"New password for '{args.username}': ")
        if len(password) < 8:
            print("Error: password must be at least 8 characters.")
            sys.exit(1)

        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: passwords do not match.")
            sys.exit(1)

        user.password_hash = AuthService.hash_password(password)
        db.commit()
        print(f"Password updated for '{args.username}'.")
    finally:
        db.close()


def list_users(args):
    """List all users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("No users found.")
            return

        print(f"\n{'Username':<20} {'Role':<10} {'Active':<8} {'Created'}")
        print("-" * 65)
        for u in users:
            created = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "—"
            print(f"{u.username:<20} {u.role:<10} {str(u.active):<8} {created}")
        print()
    finally:
        db.close()


def create_user(args):
    """Create a new user."""
    db = SessionLocal()
    auth = AuthService()
    try:
        password = getpass.getpass(f"Password for '{args.username}': ")
        if len(password) < 8:
            print("Error: password must be at least 8 characters.")
            sys.exit(1)

        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: passwords do not match.")
            sys.exit(1)

        auth.create_user(db=db, username=args.username, password=password, role=args.role)
        print(f"User '{args.username}' created with role '{args.role}'.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="SQL AI Agent - User Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/manage_users.py change-password admin
    python scripts/manage_users.py list
    python scripts/manage_users.py create newuser --role admin
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # change-password
    cp = sub.add_parser("change-password", help="Change a user's password")
    cp.add_argument("username")
    cp.set_defaults(func=change_password)

    # list
    ls = sub.add_parser("list", help="List all users")
    ls.set_defaults(func=list_users)

    # create
    cr = sub.add_parser("create", help="Create a new user")
    cr.add_argument("username")
    cr.add_argument("--role", default="user", choices=["user", "admin"])
    cr.set_defaults(func=create_user)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
