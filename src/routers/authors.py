"""
Author-related API routes - disabled.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/authors")
async def get_all_authors() -> Dict[str, Any]:
    """Get all authors - disabled"""
    return {"success": False, "error": "Library functionality disabled", "authors": []}


@router.get("/authors/user/{user_id}")
async def get_user_authors(user_id: str) -> Dict[str, Any]:
    """Get user authors - disabled"""
    return {"success": False, "error": "Library functionality disabled", "authors": []}