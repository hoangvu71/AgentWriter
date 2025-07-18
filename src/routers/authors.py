"""
Author-related API routes.
"""

from fastapi import APIRouter, Depends, Query, Path
from typing import Dict, Any
from ..controllers.base_controller import BaseController

router = APIRouter()


class AuthorController(BaseController):
    """Controller for author operations"""
    
    def __init__(self):
        super().__init__("authors")
    
    async def get_all_authors(self) -> Dict[str, Any]:
        """Get all authors"""
        try:
            self.log_request("get_all_authors")
            # TODO: Implement with repository pattern
            return self.error_response("Not yet implemented in refactored version")
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve authors")
    
    async def get_user_authors(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get all authors for a specific user"""
        try:
            self.log_request("get_user_authors", user_id=user_id, limit=limit)
            # TODO: Implement with repository pattern
            return self.error_response("Not yet implemented in refactored version")
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve user authors")


def get_author_controller() -> AuthorController:
    """Dependency to get author controller"""
    return AuthorController()


@router.get("/authors")
async def get_all_authors(
    controller: AuthorController = Depends(get_author_controller)
) -> Dict[str, Any]:
    """Get all authors"""
    return await controller.get_all_authors()


@router.get("/authors/user/{user_id}")
async def get_user_authors(
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100),
    controller: AuthorController = Depends(get_author_controller)
) -> Dict[str, Any]:
    """Get all authors for a specific user"""
    return await controller.get_user_authors(user_id, limit)