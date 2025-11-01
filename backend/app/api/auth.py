"""
API route handlers for authentication endpoints.

Handles:
- POST /auth/login - User login with username/password
- POST /auth/logout - User logout (revoke session)
- GET /auth/session - Validate current session
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionInfo,
    SessionInfoWithoutToken,
    SessionResponse,
    UserResponse,
)
from backend.app.services.auth_service import AuthenticationError, AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "role": "user",
                            "active": True,
                        },
                        "session": {
                            "token": "a1b2c3d4e5f6...",
                            "expires_at": "2025-10-28T20:30:00Z",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials or account disabled",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid username or password",
                        "error_code": "AUTH_INVALID_CREDENTIALS",
                    }
                }
            },
        },
    },
)
async def login(
    request: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    """
    Authenticate user with username and password.

    Sets a secure HTTP-only cookie with the session token.

    Args:
        request: Login credentials (username and password)
        response: FastAPI response object (for setting cookies)
        db: Database session

    Returns:
        LoginResponse: User information and session details

    Raises:
        HTTPException 401: Invalid credentials or account disabled
    """
    logger.info(f"Login attempt for username: {request.username}")

    try:
        # Authenticate user
        user = auth_service.authenticate_user(db, request.username, request.password)

        # Create session
        session = auth_service.create_session(db, user)

        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=session.token,
            httponly=True,  # Prevents JavaScript access (XSS protection)
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",  # CSRF protection
            max_age=8 * 60 * 60,  # 8 hours in seconds
        )

        logger.info(f"Login successful for user: {request.username}")

        return LoginResponse(
            user=UserResponse(
                id=user.id,
                username=user.username,
                role=user.role,
                active=user.active,
            ),
            session=SessionInfo(
                token=session.token,
                expires_at=session.expires_at.isoformat() + "Z",
            ),
        )

    except AuthenticationError as e:
        logger.warning(
            f"Login failed for username {request.username}: {e}",
            extra={"username": request.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(
            f"Unexpected error during login for {request.username}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during login",
        ) from e


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    responses={
        200: {
            "description": "Logout successful",
            "content": {
                "application/json": {
                    "example": {"message": "Logged out successfully"}
                }
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session token is missing or invalid",
                        "error_code": "AUTH_SESSION_INVALID",
                    }
                }
            },
        },
    },
)
async def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> LogoutResponse:
    """
    Logout user by revoking their session.

    Clears the session cookie.

    Args:
        response: FastAPI response object (for clearing cookies)
        db: Database session
        session_token: Session token from cookie

    Returns:
        LogoutResponse: Success message

    Raises:
        HTTPException 401: Session token missing or invalid
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is missing",
        )

    # Revoke session
    revoked = auth_service.revoke_session(db, session_token)

    if not revoked:
        logger.warning(f"Logout attempt with invalid session token")

    # Clear cookie regardless of whether session was found
    response.delete_cookie(key="session_token")

    logger.info("User logged out successfully")

    return LogoutResponse(message="Logged out successfully")


@router.get(
    "/session",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate current session",
    responses={
        200: {
            "description": "Session is valid",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 1,
                            "username": "john_doe",
                            "role": "user",
                            "active": True,
                        },
                        "session": {"expires_at": "2025-10-28T20:30:00Z"},
                    }
                }
            },
        },
        401: {
            "description": "Session is invalid or expired",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Session token is missing or invalid",
                        "error_code": "AUTH_SESSION_INVALID",
                    }
                }
            },
        },
    },
)
async def validate_session(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> SessionResponse:
    """
    Validate the current session and return user information.

    Useful for frontend to check if user is still authenticated.

    Args:
        db: Database session
        session_token: Session token from cookie

    Returns:
        SessionResponse: User and session information

    Raises:
        HTTPException 401: Session token missing, invalid, or expired
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is missing",
        )

    # Validate session
    user = auth_service.validate_session(db, session_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is invalid or expired",
        )

    # Get session details
    from backend.app.models.user import Session as SessionModel

    session = db.query(SessionModel).filter(SessionModel.token == session_token).first()

    return SessionResponse(
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            active=user.active,
        ),
        session=SessionInfoWithoutToken(
            expires_at=session.expires_at.isoformat() + "Z"
        ),
    )
