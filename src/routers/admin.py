"""
Admin and genre management API routes.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from ..controllers.base_controller import BaseController
from ..database.supabase_service import SupabaseService

router = APIRouter()


class AdminController(BaseController):
    """Controller for admin operations"""
    
    def __init__(self):
        super().__init__("admin")
        self._db = SupabaseService()
    
    async def get_all_genres(self) -> Dict[str, Any]:
        """Get complete hierarchy: genres, subgenres, microgenres, tropes, and tones"""
        try:
            
            # Get hierarchical data from database
            hierarchical_genres = await self._db.get_all_genres()
            
            # Flatten into separate arrays for frontend
            genres = []
            subgenres = []
            microgenres = []
            tropes = []
            tones = []
            
            for genre in hierarchical_genres:
                genres.append({
                    "id": genre["id"],
                    "name": genre["name"],
                    "description": genre["description"]
                })
                
                for subgenre in genre.get("subgenres", []):
                    subgenres.append({
                        "id": subgenre["id"],
                        "name": subgenre["name"],
                        "description": subgenre["description"],
                        "genre_id": genre["id"]
                    })
                    
                    for microgenre in subgenre.get("microgenres", []):
                        microgenres.append({
                            "id": microgenre["id"],
                            "name": microgenre["name"],
                            "description": microgenre["description"],
                            "subgenre_id": subgenre["id"]
                        })
            
            # Get tropes and tones from database tables directly
            try:
                tropes_response = self._db.client.table("tropes").select("*").order("name").execute()
                for trope in tropes_response.data:
                    tropes.append({
                        "id": trope["id"],
                        "name": trope["name"],
                        "description": trope.get("description", ""),
                        "microgenre_id": trope.get("microgenre_id")
                    })
            except Exception:
                pass  # Tropes table might not exist yet
            
            try:
                tones_response = self._db.client.table("tones").select("*").order("name").execute()
                for tone in tones_response.data:
                    tones.append({
                        "id": tone["id"],
                        "name": tone["name"],
                        "description": tone.get("description", ""),
                        "trope_id": tone.get("trope_id")
                    })
            except Exception:
                pass  # Tones table might not exist yet
            
            return self.success_response({
                "genres": genres,
                "subgenres": subgenres,
                "microgenres": microgenres,
                "tropes": tropes,
                "tones": tones
            })
            
        except Exception as e:
            return self.handle_error(e, "Failed to retrieve genres")
    
    async def get_target_audiences(self) -> Dict[str, Any]:
        """Get all target audiences"""
        try:
            audiences = await self._db.get_all_target_audiences()
            return self.success_response(audiences)
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