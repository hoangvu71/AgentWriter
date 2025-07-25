"""
Repository for world building entity operations.
Aligned with actual Supabase schema from migration 008.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..models.entities import WorldBuilding, WorldType
from ..database.supabase_adapter import SupabaseAdapter


class WorldBuildingRepository(BaseRepository[WorldBuilding]):
    """Repository for world building operations using actual Supabase schema"""
    
    def __init__(self, database: SupabaseAdapter):
        super().__init__(database, "world_building")
    
    def _serialize(self, world: WorldBuilding) -> Dict[str, Any]:
        """Convert world building entity to database format matching simplified schema"""
        data = {
            "session_id": world.session_id,  # UUID reference to sessions table
            "user_id": world.user_id,  # UUID reference to users table
            "plot_id": world.plot_id,  # UUID reference to plots table (nullable)
            "world_name": world.world_name,  # TEXT
            "world_type": world.world_type,  # TEXT
            "world_content": world.world_content  # TEXT - Complete world building content
        }
        
        # Remove timestamp fields - let database handle them
        
        # Remove None values to avoid issues
        return {k: v for k, v in data.items() if v is not None}
    
    async def create(self, entity: WorldBuilding) -> str:
        """Override create to use specialized save_world_building method if available"""
        try:
            self._logger.info(f"Creating world: {entity.world_name}")
            
            # Check if database has specialized save_world_building method
            if hasattr(self._database, 'save_world_building'):
                return await self._database.save_world_building(self._serialize(entity))
            else:
                # Use standard create method
                return await super().create(entity)
                
        except Exception as e:
            self._logger.error(f"Error creating world building: {e}", error=e)
            raise
    
    async def get_world_building_by_plot(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Get world building data for a specific plot ID"""
        try:
            worlds = await self._database.select(
                self._table_name,
                filters={"plot_id": plot_id},
                order_by="created_at",
                desc=True,
                limit=1
            )
            
            return worlds[0] if worlds else None
            
        except Exception as e:
            self._logger.error(f"Error getting world building for plot {plot_id}: {e}")
            raise
    
    def _deserialize(self, data: Dict[str, Any]) -> WorldBuilding:
        """Convert database data to world building entity"""        
        return WorldBuilding(
            id=data.get("id"),
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            plot_id=data.get("plot_id"),
            world_name=data.get("world_name", ""),
            world_type=data.get("world_type", ""),
            world_content=data.get("world_content", ""),
            created_at=self._parse_datetime(data.get("created_at"))
        )
    
    
    async def get_by_user_external(self, external_user_id: str, limit: int = 50) -> List[WorldBuilding]:
        """Get all world building for a user using external user_id (not UUID)"""
        try:
            # Use the adapter's method that handles external user IDs
            raw_worlds = await self._database.service.get_user_world_building(external_user_id, limit)
            return [self._deserialize(world_data) for world_data in raw_worlds]
        except Exception as e:
            self._logger.error(f"Error getting world building for user {external_user_id}: {e}", error=e)
            raise
    
    async def get_by_plot(self, plot_id: str) -> List[WorldBuilding]:
        """Get all world building for a specific plot"""
        criteria = {"plot_id": plot_id}
        return await self.search(criteria, 100)
    
    async def get_by_world_type(self, world_type: WorldType, limit: int = 20) -> List[WorldBuilding]:
        """Get world building by world type"""
        criteria = {"world_type": world_type.value}
        return await self.search(criteria, limit)
    
    async def search_by_name(self, user_id: str, name_query: str, limit: int = 20) -> List[WorldBuilding]:
        """Search world building by name using external user_id"""
        try:
            # Get all user world building and filter in memory
            user_worlds = await self.get_by_user_external(user_id, 100)
            
            name_query_lower = name_query.lower()
            matching_worlds = [
                world for world in user_worlds
                if name_query_lower in world.world_name.lower()
            ]
            
            return matching_worlds[:limit]
        except Exception as e:
            self._logger.error(f"Error searching world building by name: {e}", error=e)
            raise
    
    async def get_recent_worlds(self, user_id: str, limit: int = 10) -> List[WorldBuilding]:
        """Get most recent world building for a user using external user_id"""
        try:
            # Get worlds using external user ID (the adapter handles UUID conversion)
            worlds = await self.get_by_user_external(user_id, limit)
            
            # Sort by created_at descending (should already be sorted from DB)
            sorted_worlds = sorted(
                worlds,
                key=lambda w: w.created_at or datetime.min,
                reverse=True
            )
            
            return sorted_worlds[:limit]
        except Exception as e:
            self._logger.error(f"Error getting recent world building: {e}", error=e)
            raise
    
    async def get_user_world_building(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all world building for a user in raw format (compatible with existing API)"""
        try:
            # Use the adapter's method that returns raw data for API compatibility
            return await self._database.service.get_user_world_building(user_id, limit)
        except Exception as e:
            self._logger.error(f"Error getting world building for user {user_id}: {e}", error=e)
            raise
    
    async def get_world_by_plot(self, plot_id: str) -> List[Dict[str, Any]]:
        """Get world building for a specific plot in raw format"""
        try:
            # Get worlds as entities and convert to raw format
            worlds = await self.get_by_plot(plot_id)
            return [self._serialize(world) for world in worlds]
        except Exception as e:
            self._logger.error(f"Error getting world building for plot {plot_id}: {e}", error=e)
            raise