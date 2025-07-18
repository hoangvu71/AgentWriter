"""
Content management API routes.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from ..controllers.base_controller import BaseController

router = APIRouter()


class ContentController(BaseController):
    """Controller for content operations"""
    
    def __init__(self):
        super().__init__("content")
    
    async def get_content_selection(self) -> Dict[str, Any]:
        """Get simplified content lists for selection in improvement workflow"""
        try:
            self.log_request("get_content_selection")
            # TODO: Implement with repository pattern
            return self.error_response("Not yet implemented in refactored version")
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