"""
Content management API routes.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from ..controllers.base_controller import BaseController
from ..database.supabase_service import SupabaseService

router = APIRouter()


class ContentController(BaseController):
    """Controller for content operations"""
    
    def __init__(self):
        super().__init__("content")
        self._db = SupabaseService()
    
    async def get_content_selection(self) -> Dict[str, Any]:
        """Get simplified content lists for selection in improvement workflow"""
        try:
            
            content = []
            
            # Get all plots
            try:
                plots = self._db.get_all_plots_with_metadata()
                for plot in plots:
                    content.append({
                        "id": plot["id"],
                        "type": "plot",
                        "title": plot.get("title", "Untitled Plot"),
                        "created_at": plot.get("created_at")
                    })
            except Exception:
                pass
            
            # Get all authors
            try:
                authors = await self._db.get_all_authors()
                for author in authors:
                    content.append({
                        "id": author["id"],
                        "type": "author",
                        "title": author.get("name", "Unnamed Author"),
                        "created_at": author.get("created_at")
                    })
            except Exception:
                pass
            
            # Sort by creation date (newest first)
            content.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return self.success_response({"content": content})
            
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve content selection")


def get_content_controller() -> ContentController:
    """Dependency to get content controller"""
    return ContentController()


@router.get("/content-selection")
async def get_content_selection(
    controller: ContentController = Depends(get_content_controller)
) -> Dict[str, Any]:
    """Get simplified content lists for selection in improvement workflow"""
    return await controller.get_content_selection()