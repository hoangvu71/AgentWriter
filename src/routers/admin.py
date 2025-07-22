"""
Admin API routes - disabled.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/genres")
async def get_all_genres() -> Dict[str, Any]:
    """Get genres - disabled"""
    return {
        "success": False, 
        "error": "Admin functionality disabled",
        "genres": [],
        "subgenres": [],
        "microgenres": [],
        "tropes": [],
        "tones": []
    }


@router.get("/target-audiences")
async def get_target_audiences() -> Dict[str, Any]:
    """Get target audiences - disabled"""
    return {
        "success": False,
        "error": "Admin functionality disabled",
        "target_audiences": []
    }