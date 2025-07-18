"""
Plot-related API routes.
"""

from fastapi import APIRouter, Depends, Query, Path
from typing import Dict, Any
from ..controllers.plot_controller import PlotController
from ..repositories.plot_repository import PlotRepository

router = APIRouter()


def get_plot_controller() -> PlotController:
    """Dependency to get plot controller"""
    return PlotController()


def get_plot_repository() -> PlotRepository:
    """Dependency to get plot repository"""
    # This would be properly injected in a full implementation
    # For now, return None to maintain compatibility
    return None


@router.get("/plots")
async def get_all_plots(
    controller: PlotController = Depends(get_plot_controller),
    repository: PlotRepository = Depends(get_plot_repository)
) -> Dict[str, Any]:
    """Get all plots with metadata"""
    return await controller.get_all_plots(repository)


@router.get("/plots/user/{user_id}")
async def get_user_plots(
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100),
    controller: PlotController = Depends(get_plot_controller),
    repository: PlotRepository = Depends(get_plot_repository)
) -> Dict[str, Any]:
    """Get all plots for a specific user"""
    return await controller.get_user_plots(user_id, limit, repository)


@router.get("/plots/{plot_id}")
async def get_plot_by_id(
    plot_id: str = Path(..., description="Plot ID"),
    controller: PlotController = Depends(get_plot_controller),
    repository: PlotRepository = Depends(get_plot_repository)
) -> Dict[str, Any]:
    """Get a specific plot by ID"""
    return await controller.get_plot_by_id(plot_id, repository)


@router.get("/plots/user/{user_id}/search")
async def search_plots(
    user_id: str = Path(..., description="User ID"),
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    controller: PlotController = Depends(get_plot_controller),
    repository: PlotRepository = Depends(get_plot_repository)
) -> Dict[str, Any]:
    """Search plots by title or content"""
    return await controller.search_plots(user_id, q, limit, repository)


@router.get("/plots/user/{user_id}/recent")
async def get_recent_plots(
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(10, ge=1, le=20),
    controller: PlotController = Depends(get_plot_controller),
    repository: PlotRepository = Depends(get_plot_repository)
) -> Dict[str, Any]:
    """Get recent plots for a user"""
    return await controller.get_recent_plots(user_id, limit, repository)