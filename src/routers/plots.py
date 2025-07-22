"""
Plot-related API routes - disabled.
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/plots")
async def get_all_plots() -> Dict[str, Any]:
    """Get all plots - disabled"""
    return {"success": False, "error": "Library functionality disabled", "plots": []}


@router.get("/plots/user/{user_id}")
async def get_user_plots(user_id: str) -> Dict[str, Any]:
    """Get user plots - disabled"""
    return {"success": False, "error": "Library functionality disabled", "plots": []}


@router.get("/plots/{plot_id}")
async def get_plot_by_id(plot_id: str) -> Dict[str, Any]:
    """Get plot by ID - disabled"""
    return {"success": False, "error": "Library functionality disabled", "plot": None}


@router.get("/plots/user/{user_id}/search")
async def search_plots(user_id: str, q: str) -> Dict[str, Any]:
    """Search plots - disabled"""
    return {"success": False, "error": "Library functionality disabled", "plots": []}


@router.get("/plots/user/{user_id}/recent")
async def get_recent_plots(user_id: str) -> Dict[str, Any]:
    """Get recent plots - disabled"""
    return {"success": False, "error": "Library functionality disabled", "plots": []}