"""
Author-related API routes using repository pattern.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from ..core.container import container
from ..repositories.author_repository import AuthorRepository
from ..core.logging import get_logger

router = APIRouter()
logger = get_logger("api.authors")


def get_author_repository() -> AuthorRepository:
    """Dependency injection for AuthorRepository"""
    try:
        return container.get("author_repository")
    except Exception as e:
        logger.error(f"Failed to get author repository: {e}")
        raise HTTPException(status_code=500, detail="Author service unavailable")


@router.get("/authors")
async def get_all_authors(author_repo: AuthorRepository = Depends(get_author_repository)) -> Dict[str, Any]:
    """Get all authors with pagination"""
    try:
        authors = await author_repo.get_all(limit=100)
        return {
            "success": True,
            "authors": [author_repo._serialize(author) for author in authors],
            "total": len(authors)
        }
    except Exception as e:
        logger.error(f"Error getting all authors: {e}")
        return {"success": False, "error": "Failed to retrieve authors", "authors": []}


@router.get("/authors/user/{user_id}")
async def get_user_authors(user_id: str, author_repo: AuthorRepository = Depends(get_author_repository)) -> Dict[str, Any]:
    """Get authors for a specific user"""
    try:
        authors = await author_repo.get_user_authors(user_id)
        return {
            "success": True,
            "authors": authors,  # get_user_authors returns raw data for API compatibility
            "user_id": user_id,
            "total": len(authors)
        }
    except Exception as e:
        logger.error(f"Error getting authors for user {user_id}: {e}")
        return {"success": False, "error": "Failed to retrieve user authors", "authors": []}