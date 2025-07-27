"""
Repository for characters entity operations.
Aligned with actual Supabase schema from migration 008.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..models.entities import Characters
from ..database.supabase_adapter import SupabaseAdapter


class CharactersRepository(BaseRepository[Characters]):
    """Repository for characters operations using actual Supabase schema"""
    
    def __init__(self, database: SupabaseAdapter):
        super().__init__(database, "characters")
    
    def _serialize(self, characters: Characters) -> Dict[str, Any]:
        """Convert characters entity to database format matching actual schema"""
        data = {
            "session_id": characters.session_id,  # UUID reference to sessions table
            "user_id": characters.user_id,  # UUID reference to users table
            "world_id": characters.world_id,  # UUID reference to world_building table (nullable)
            "plot_id": characters.plot_id,  # UUID reference to plots table (nullable)
            "character_count": characters.character_count,  # INTEGER
            "world_context_integration": characters.world_context_integration,  # TEXT (nullable)
            
            # JSONB fields for character data
            "characters": characters.characters,  # JSONB array
            "relationship_networks": characters.relationship_networks,  # JSONB
            "character_dynamics": characters.character_dynamics,  # JSONB
        }
        
        # Remove None values to avoid issues
        return {k: v for k, v in data.items() if v is not None}
    
    def _deserialize(self, data: Dict[str, Any]) -> Characters:
        """Convert database data to characters entity"""
        return Characters(
            id=data.get("id"),
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            world_id=data.get("world_id"),
            plot_id=data.get("plot_id"),
            character_count=data.get("character_count", 0),
            world_context_integration=data.get("world_context_integration"),
            characters=data.get("characters", []),
            relationship_networks=data.get("relationship_networks", {}),
            character_dynamics=data.get("character_dynamics", {}),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at"))
        )
    
    
    async def get_by_user_external(self, external_user_id: str, limit: int = 50) -> List[Characters]:
        """Get all characters for a user using external user_id (not UUID)"""
        try:
            # Use the adapter's method that handles external user IDs
            raw_characters = await self._database.service.get_user_characters(external_user_id, limit)
            return [self._deserialize(char_data) for char_data in raw_characters]
        except Exception as e:
            self._logger.error(f"Error getting characters for user {external_user_id}: {e}", error=e)
            raise
    
    async def get_by_plot(self, plot_id: str) -> List[Characters]:
        """Get all characters for a specific plot"""
        criteria = {"plot_id": plot_id}
        return await self.search(criteria, 100)
    
    async def get_by_world(self, world_id: str) -> List[Characters]:
        """Get all characters for a specific world"""
        try:
            # Use the existing service method
            raw_characters = await self._database.service.get_characters_by_world_id(world_id)
            return [self._deserialize(char_data) for char_data in raw_characters]
        except Exception as e:
            self._logger.error(f"Error getting characters for world {world_id}: {e}", error=e)
            raise
    
    async def search_by_character_name(self, user_id: str, name_query: str, limit: int = 20) -> List[Characters]:
        """Search characters by character names using external user_id"""
        try:
            # Get all user characters and filter in memory
            user_characters = await self.get_by_user_external(user_id, 100)
            
            name_query_lower = name_query.lower()
            matching_characters = []
            
            for char_entry in user_characters:
                # Search through the characters JSONB array for matching names
                for character in char_entry.characters:
                    if isinstance(character, dict) and "name" in character:
                        if name_query_lower in character["name"].lower():
                            matching_characters.append(char_entry)
                            break  # Found a match in this entry, move to next
            
            return matching_characters[:limit]
        except Exception as e:
            self._logger.error(f"Error searching characters by name: {e}", error=e)
            raise
    
    async def get_recent_characters(self, user_id: str, limit: int = 10) -> List[Characters]:
        """Get most recent characters for a user using external user_id"""
        try:
            # Get characters using external user ID (the adapter handles UUID conversion)
            characters = await self.get_by_user_external(user_id, limit)
            
            # Sort by created_at descending (should already be sorted from DB)
            sorted_characters = sorted(
                characters,
                key=lambda c: c.created_at or datetime.min,
                reverse=True
            )
            
            return sorted_characters[:limit]
        except Exception as e:
            self._logger.error(f"Error getting recent characters: {e}", error=e)
            raise
    
    async def get_user_characters(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all characters for a user in raw format (compatible with existing API)"""
        try:
            # Use the adapter's method that returns raw data for API compatibility
            return await self._database.service.get_user_characters(user_id, limit)
        except Exception as e:
            self._logger.error(f"Error getting characters for user {user_id}: {e}", error=e)
            raise
    
    async def get_characters_by_world(self, world_id: str) -> List[Dict[str, Any]]:
        """Get characters for a specific world in raw format"""
        try:
            # Get characters as entities and convert to raw format
            characters = await self.get_by_world(world_id)
            return [self._serialize(char) for char in characters]
        except Exception as e:
            self._logger.error(f"Error getting characters for world {world_id}: {e}", error=e)
            raise
    
    async def get_characters_with_world_context(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get characters with their world building context"""
        try:
            characters = await self.get_by_user_external(user_id, limit)
            
            # For each character entry, get associated world building data
            characters_with_context = []
            for char_entry in characters:
                char_data = {
                    "characters": char_entry,
                    "world_context": None
                }
                
                # Get world building context if world_id exists
                if char_entry.world_id:
                    world_data = await self._database.get_by_id("world_building", char_entry.world_id)
                    if world_data:
                        char_data["world_context"] = world_data
                
                characters_with_context.append(char_data)
            
            return characters_with_context
        except Exception as e:
            self._logger.error(f"Error getting characters with world context: {e}", error=e)
            raise