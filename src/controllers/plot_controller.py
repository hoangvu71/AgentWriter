"""
Controller for plot-related API endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import Query, Path, Depends
from ..controllers.base_controller import BaseController
from ..repositories.plot_repository import PlotRepository
from ..core.validation import Validator
from ..core.container import container


class PlotController(BaseController):
    """Controller for plot operations"""
    
    def __init__(self):
        super().__init__("plots")
        self.validator = container.get_validator()
        # Repository will be injected via dependency injection
    
    async def get_all_plots(self, repository: PlotRepository = None) -> Dict[str, Any]:
        """Get all plots with metadata"""
        try:
            self.log_request("get_all_plots")
            
            if not repository:
                # Get repository from container
                from ..core.container import container
                repository = container.get("plot_repository")
            
            plots = await repository.get_all(limit=200)
            
            # Convert to dict format for API response
            plots_data = []
            for plot in plots:
                plots_data.append({
                    "id": plot.id,
                    "title": plot.title,
                    "plot_summary": plot.plot_summary,
                    "user_id": plot.user_id,
                    "author_id": plot.author_id,
                    "genre_id": plot.genre_id,
                    "subgenre_id": plot.subgenre_id,
                    "microgenre_id": plot.microgenre_id,
                    "trope_id": plot.trope_id,
                    "tone_id": plot.tone_id,
                    "target_audience_id": plot.target_audience_id,
                    "created_at": plot.created_at.isoformat() if plot.created_at else None
                })
            
            return self.success_response({"plots": plots_data})
            
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve plots")
    
    async def get_user_plots(
        self, 
        user_id: str = Path(..., description="User ID"),
        limit: int = Query(50, ge=1, le=100),
        repository: PlotRepository = None
    ) -> Dict[str, Any]:
        """Get all plots for a specific user"""
        try:
            self.log_request("get_user_plots", user_id=user_id, limit=limit)
            
            # Validate inputs
            validated_user_id = self.validator.validate_alphanumeric(user_id)
            
            if not repository:
                # Get repository from container
                from ..core.container import container
                repository = container.get("plot_repository")
            
            # Use external user ID method
            plots = await repository.get_by_user_external(validated_user_id, limit)
            
            # Convert to response format
            plots_data = []
            for plot in plots:
                plots_data.append({
                    "id": plot.id,
                    "title": plot.title,
                    "plot_summary": plot.plot_summary,
                    "genre_id": plot.genre_id,
                    "subgenre_id": plot.subgenre_id,
                    "microgenre_id": plot.microgenre_id,
                    "trope_id": plot.trope_id,
                    "tone_id": plot.tone_id,
                    "target_audience_id": plot.target_audience_id,
                    "author_id": plot.author_id,
                    "created_at": plot.created_at.isoformat() if plot.created_at else None
                })
            
            return self.success_response({"plots": plots_data})
            
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve user plots")
    
    async def get_plot_by_id(
        self,
        plot_id: str = Path(..., description="Plot ID"),
        repository: PlotRepository = None
    ) -> Dict[str, Any]:
        """Get a specific plot by ID"""
        try:
            self.log_request("get_plot_by_id", plot_id=plot_id)
            
            # Validate plot ID
            validated_plot_id = self.validator.validate_uuid(plot_id)
            
            if not repository:
                from ..core.container import container
                try:
                    repository = container.get("plot_repository")
                except Exception as e:
                    return self.handle_error(e, "Repository not available")
            
            plot = await repository.get_by_id(validated_plot_id)
            
            if not plot:
                raise ValueError("Plot not found")
            
            plot_data = {
                "id": plot.id,
                "title": plot.title,
                "plot_summary": plot.plot_summary,
                "user_id": plot.user_id,
                "session_id": plot.session_id,
                "author_id": plot.author_id,
                "genre_elements": plot.genre_elements,
                "conflict_type": plot.conflict_type,
                "story_structure": plot.story_structure,
                "created_at": plot.created_at.isoformat() if plot.created_at else None,
                "updated_at": plot.updated_at.isoformat() if plot.updated_at else None
            }
            
            return self.success_response({"plot": plot_data})
            
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve plot")
    
    async def search_plots(
        self,
        user_id: str = Path(..., description="User ID"),
        q: str = Query(..., description="Search query"),
        limit: int = Query(20, ge=1, le=50),
        repository: PlotRepository = None
    ) -> Dict[str, Any]:
        """Search plots by title or content"""
        try:
            self.log_request("search_plots", user_id=user_id, query=q, limit=limit)
            
            # Validate inputs
            validated_user_id = self.validator.validate_alphanumeric(user_id)
            validated_query = self.validator.validate_text(q, max_length=200)
            
            if not repository:
                from ..core.container import container
                try:
                    repository = container.get("plot_repository")
                except Exception as e:
                    return self.handle_error(e, "Repository not available")
            
            plots = await repository.search_by_title(validated_user_id, validated_query, limit)
            
            # Convert to response format
            plots_data = []
            for plot in plots:
                plots_data.append({
                    "id": plot.id,
                    "title": plot.title,
                    "plot_summary": plot.plot_summary[:200] + "..." if len(plot.plot_summary) > 200 else plot.plot_summary,
                    "genre_elements": plot.genre_elements,
                    "created_at": plot.created_at.isoformat() if plot.created_at else None
                })
            
            return self.success_response({"plots": plots_data})
            
        except Exception as e:
            return self.handle_error(e, "Failed to search plots")
    
    async def get_recent_plots(
        self,
        user_id: str = Path(..., description="User ID"),
        limit: int = Query(10, ge=1, le=20),
        repository: PlotRepository = None
    ) -> Dict[str, Any]:
        """Get recent plots for a user"""
        try:
            self.log_request("get_recent_plots", user_id=user_id, limit=limit)
            
            # Validate inputs
            validated_user_id = self.validator.validate_alphanumeric(user_id)
            
            if not repository:
                from ..core.container import container
                try:
                    repository = container.get("plot_repository")
                except Exception as e:
                    return self.handle_error(e, "Repository not available")
            
            plots = await repository.get_recent_plots(validated_user_id, limit)
            
            # Convert to response format
            plots_data = []
            for plot in plots:
                plots_data.append({
                    "id": plot.id,
                    "title": plot.title,
                    "plot_summary": plot.plot_summary[:150] + "..." if len(plot.plot_summary) > 150 else plot.plot_summary,
                    "created_at": plot.created_at.isoformat() if plot.created_at else None
                })
            
            return self.success_response({"plots": plots_data})
            
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve recent plots")