"""
FastAPI dependencies for authentication and database access.

Provides reusable dependencies for:
- Database session management
- User authentication
- Admin role checking
"""

import logging
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
auth_service = AuthService()


async def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """
    Get the currently authenticated user from session token.

    This dependency validates the session token from the cookie
    and returns the authenticated user.

    Args:
        db: Database session
        session_token: Session token from HTTP-only cookie

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException 401: If session token is missing, invalid, or expired
    """
    if not session_token:
        logger.debug("Authentication failed: No session token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is missing or invalid",
        )

    # Validate session and get user
    user = auth_service.validate_session(db, session_token)

    if not user:
        logger.debug("Authentication failed: Invalid or expired session token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is missing or invalid",
        )

    logger.debug(f"User authenticated: {user.username}")
    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get the currently authenticated user and verify they have admin role.

    This dependency extends get_current_user to also check for admin privileges.

    Args:
        current_user: Authenticated user from get_current_user dependency

    Returns:
        User: Authenticated admin user

    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != "admin":
        logger.warning(
            f"User {current_user.username} attempted admin-only action without admin role"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    logger.debug(f"Admin user authenticated: {current_user.username}")
    return current_user


# Export get_db for convenience
__all__ = ["get_db", "get_current_user", "get_current_admin_user"]
