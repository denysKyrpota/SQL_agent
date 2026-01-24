"""
Admin API endpoints for system management.

Provides endpoints for:
- Generating embeddings for knowledge base
- Refreshing schema cache
- System health checks
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.dependencies import get_current_user, get_db
from backend.app.services.llm_service import LLMService
from backend.app.services.knowledge_base_service import KnowledgeBaseService
from backend.app.services.schema_service import SchemaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/embeddings/generate")
async def generate_embeddings(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Generate embeddings for all knowledge base examples.

    This endpoint should be called:
    - Initially when setting up the knowledge base
    - When new examples are added to the knowledge base
    - If embeddings become corrupted or outdated

    Requires admin role.

    Returns:
        dict: Statistics about embedding generation
            - total_examples: Number of examples in KB
            - embeddings_generated: Number of new embeddings created
            - embeddings_skipped: Number of examples that already had embeddings
            - embeddings_available: Total examples with embeddings after generation
    """
    # Check if user is admin
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Only admins can generate embeddings"
        )

    logger.info(
        f"Admin {user['username']} (ID: {user['id']}) requested embedding generation"
    )

    try:
        # Initialize services
        llm_service = LLMService()
        kb_service = KnowledgeBaseService()

        # Generate embeddings
        stats = await kb_service.generate_embeddings(llm_service)

        logger.info(
            f"Embedding generation complete: {stats}",
            extra={"admin_user_id": user["id"], "stats": stats},
        )

        return {
            "success": True,
            "message": "Embeddings generated successfully",
            "stats": stats,
        }

    except Exception as e:
        logger.error(
            f"Failed to generate embeddings: {e}",
            extra={"admin_user_id": user["id"]},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.post("/schema/refresh")
async def refresh_schema(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Refresh the database schema cache.

    Forces reload of the PostgreSQL schema from disk.
    Use this after updating the schema JSON file.

    Requires admin role.

    Returns:
        dict: Statistics about the refreshed schema
    """
    # Check if user is admin
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can refresh schema")

    logger.info(f"Admin {user['username']} (ID: {user['id']}) requested schema refresh")

    try:
        schema_service = SchemaService()
        schema = schema_service.refresh_schema()

        stats = {
            "total_tables": len(schema["tables"]),
            "total_columns": sum(len(t["columns"]) for t in schema["tables"].values()),
        }

        logger.info(
            f"Schema refreshed: {stats}",
            extra={"admin_user_id": user["id"], "stats": stats},
        )

        return {
            "success": True,
            "message": "Schema refreshed successfully",
            "stats": stats,
        }

    except Exception as e:
        logger.error(
            f"Failed to refresh schema: {e}",
            extra={"admin_user_id": user["id"]},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh schema: {str(e)}"
        )


@router.post("/kb/refresh")
async def refresh_knowledge_base(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Refresh the knowledge base cache.

    Forces reload of SQL examples from disk.
    Use this after adding or modifying knowledge base examples.

    Requires admin role.

    Returns:
        dict: Statistics about the refreshed knowledge base
    """
    # Check if user is admin
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Only admins can refresh knowledge base"
        )

    logger.info(f"Admin {user['username']} (ID: {user['id']}) requested KB refresh")

    try:
        kb_service = KnowledgeBaseService()
        examples = kb_service.refresh_examples()

        stats = kb_service.get_stats()

        logger.info(
            f"Knowledge base refreshed: {stats}",
            extra={"admin_user_id": user["id"], "stats": stats},
        )

        return {
            "success": True,
            "message": "Knowledge base refreshed successfully",
            "stats": stats,
        }

    except Exception as e:
        logger.error(
            f"Failed to refresh knowledge base: {e}",
            extra={"admin_user_id": user["id"]},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh knowledge base: {str(e)}"
        )


@router.get("/kb/stats")
async def get_kb_stats(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Get knowledge base statistics.

    Returns information about the knowledge base including:
    - Number of examples
    - Embeddings status
    - Average query length

    Requires admin role.

    Returns:
        dict: Knowledge base statistics
    """
    # Check if user is admin
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view KB stats")

    try:
        kb_service = KnowledgeBaseService()
        stats = kb_service.get_stats()

        # Add embeddings info
        examples = kb_service.get_examples()
        embeddings_count = sum(1 for ex in examples if ex.embedding is not None)

        stats["embeddings_available"] = embeddings_count
        stats["embeddings_missing"] = len(examples) - embeddings_count

        return stats

    except Exception as e:
        logger.error(
            f"Failed to get KB stats: {e}",
            extra={"admin_user_id": user["id"]},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get KB stats: {str(e)}")
