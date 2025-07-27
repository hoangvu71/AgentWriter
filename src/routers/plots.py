"""
Plot-related API routes using repository pattern.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from ..core.container import container
from ..repositories.plot_repository import PlotRepository
from ..core.logging import get_logger

router = APIRouter()
logger = get_logger("api.plots")


def get_plot_repository() -> PlotRepository:
    """Dependency injection for PlotRepository"""
    try:
        return container.get("plot_repository")
    except Exception as e:
        logger.error(f"Failed to get plot repository: {e}")
        raise HTTPException(status_code=500, detail="Plot service unavailable")


@router.get("/plots")
async def get_all_plots(plot_repo: PlotRepository = Depends(get_plot_repository)) -> Dict[str, Any]:
    """Get all plots with pagination"""
    try:
        plots = await plot_repo.get_all(limit=100)
        return {
            "success": True,
            "plots": [plot_repo._serialize(plot) for plot in plots],
            "total": len(plots)
        }
    except Exception as e:
        logger.error(f"Error getting all plots: {e}")
        return {"success": False, "error": "Failed to retrieve plots", "plots": []}


@router.get("/plots/user/{user_id}")
async def get_user_plots(user_id: str, plot_repo: PlotRepository = Depends(get_plot_repository)) -> Dict[str, Any]:
    """Get plots for a specific user"""
    try:
        plots = await plot_repo.get_user_plots(user_id)
        return {
            "success": True,
            "plots": plots,  # get_user_plots returns raw data for API compatibility
            "user_id": user_id,
            "total": len(plots)
        }
    except Exception as e:
        logger.error(f"Error getting plots for user {user_id}: {e}")
        return {"success": False, "error": "Failed to retrieve user plots", "plots": []}


@router.get("/plots/{plot_id}")
async def get_plot_by_id(plot_id: str, plot_repo: PlotRepository = Depends(get_plot_repository)) -> Dict[str, Any]:
    """Get plot by ID"""
    try:
        plot = await plot_repo.get_by_id(plot_id)
        if not plot:
            return {"success": False, "error": "Plot not found", "plot": None}
        
        return {
            "success": True,
            "plot": plot_repo._serialize(plot)
        }
    except Exception as e:
        logger.error(f"Error getting plot {plot_id}: {e}")
        return {"success": False, "error": "Failed to retrieve plot", "plot": None}


@router.get("/plots/user/{user_id}/search")
async def search_plots(user_id: str, q: str, plot_repo: PlotRepository = Depends(get_plot_repository)) -> Dict[str, Any]:
    """Search plots for a user"""
    try:
        # Search by title containing the query
        plots = await plot_repo.search({"user_id": user_id}, limit=50)
        
        # Filter results by query string in title or summary
        filtered_plots = []
        query_lower = q.lower()
        for plot in plots:
            plot_data = plot_repo._serialize(plot)
            title = plot_data.get("title", "").lower()
            summary = plot_data.get("plot_summary", "").lower()
            if query_lower in title or query_lower in summary:
                filtered_plots.append(plot_data)
        
        return {
            "success": True,
            "plots": filtered_plots,
            "query": q,
            "user_id": user_id,
            "total": len(filtered_plots)
        }
    except Exception as e:
        logger.error(f"Error searching plots for user {user_id}: {e}")
        return {"success": False, "error": "Failed to search plots", "plots": []}


@router.get("/plots/user/{user_id}/recent")
async def get_recent_plots(user_id: str, limit: int = 10, plot_repo: PlotRepository = Depends(get_plot_repository)) -> Dict[str, Any]:
    """Get recent plots for a user"""
    try:
        plots = await plot_repo.get_user_plots(user_id, limit)
        return {
            "success": True,
            "plots": plots,  # Already sorted by creation date
            "user_id": user_id,
            "limit": limit,
            "total": len(plots)
        }
    except Exception as e:
        logger.error(f"Error getting recent plots for user {user_id}: {e}")
        return {"success": False, "error": "Failed to retrieve recent plots", "plots": []}