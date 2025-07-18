"""
Admin and genre management API routes.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from ..controllers.base_controller import BaseController

router = APIRouter()


class AdminController(BaseController):
    """Controller for admin operations"""
    
    def __init__(self):
        super().__init__("admin")
    
    async def get_all_genres(self) -> Dict[str, Any]:
        """Get complete hierarchy: genres, subgenres, microgenres, tropes, and tones"""
        try:
            self.log_request("get_all_genres")
            # TODO: Implement with repository pattern
            return self.error_response("Not yet implemented in refactored version")
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve genres")
    
    async def get_target_audiences(self) -> Dict[str, Any]:
        """Get all target audiences"""
        try:
            self.log_request("get_target_audiences")
            # TODO: Implement with repository pattern
            return self.error_response("Not yet implemented in refactored version")
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve target audiences")


def get_admin_controller() -> AdminController:
    """Dependency to get admin controller"""
    return AdminController()


@router.get("/genres")
async def get_all_genres(
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get complete hierarchy: genres, subgenres, microgenres, tropes, and tones"""
    return await controller.get_all_genres()


@router.get("/target-audiences")
async def get_target_audiences(
    controller: AdminController = Depends(get_admin_controller)
) -> Dict[str, Any]:
    """Get all target audiences"""
    return await controller.get_target_audiences()