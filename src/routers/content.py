"""
Content management API routes - disabled.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/content-selection")
async def get_content_selection() -> Dict[str, Any]:
    """Get content selection - disabled"""
    return {"success": False, "error": "Library functionality disabled", "content": []}