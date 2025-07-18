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
        """Convert world building entity to database format matching actual schema"""
        data = {
            "session_id": world.session_id,  # UUID reference to sessions table
            "user_id": world.user_id,  # UUID reference to users table
            "plot_id": world.plot_id,  # UUID reference to plots table (nullable)
            "world_name": world.world_name,  # TEXT
            "world_type": world.world_type.value if isinstance(world.world_type, WorldType) else world.world_type,  # TEXT with CHECK constraint
            "overview": world.overview,  # TEXT
            
            # JSONB fields for complex world data
            "geography": world.geography,  # JSONB
            "political_landscape": world.political_landscape,  # JSONB
            "cultural_systems": world.cultural_systems,  # JSONB
            "economic_framework": world.economic_framework,  # JSONB
            "historical_timeline": world.historical_timeline,  # JSONB
            "power_systems": world.power_systems,  # JSONB
            "languages_and_communication": world.languages_and_communication,  # JSONB
            "religious_and_belief_systems": world.religious_and_belief_systems,  # JSONB
            "unique_elements": world.unique_elements,  # JSONB
        }
        
        # Remove None values to avoid issues
        return {k: v for k, v in data.items() if v is not None}
    
    def _deserialize(self, data: Dict[str, Any]) -> WorldBuilding:
        """Convert database data to world building entity"""
        # Parse world_type enum
        world_type_str = data.get("world_type", "other")
        try:
            world_type = WorldType(world_type_str)
        except ValueError:
            world_type = WorldType.OTHER
        
        return WorldBuilding(
            id=data.get("id"),
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            plot_id=data.get("plot_id"),
            world_name=data.get("world_name", ""),
            world_type=world_type,
            overview=data.get("overview", ""),
            geography=data.get("geography", {}),
            political_landscape=data.get("political_landscape", {}),
            cultural_systems=data.get("cultural_systems", {}),
            economic_framework=data.get("economic_framework", {}),
            historical_timeline=data.get("historical_timeline", {}),
            power_systems=data.get("power_systems", {}),
            languages_and_communication=data.get("languages_and_communication", {}),
            religious_and_belief_systems=data.get("religious_and_belief_systems", {}),
            unique_elements=data.get("unique_elements", {}),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at"))
        )
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
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