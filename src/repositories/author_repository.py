"""
Repository for author entity operations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..models.entities import Author
from ..core.interfaces import IDatabase


class AuthorRepository(BaseRepository[Author]):
    """Repository for author operations"""
    
    def __init__(self, database: IDatabase):
        super().__init__(database, "authors")
    
    def _serialize(self, author: Author) -> Dict[str, Any]:
        """Convert author entity to database format"""
        data = {
            "author_name": author.author_name,
            "pen_name": author.pen_name,
            "biography": author.biography,
            "writing_style": author.writing_style,
            "user_id": author.user_id,
            "session_id": author.session_id
        }
        
        # Remove timestamp fields - let database handle them
        # (created_at and updated_at may not exist in actual schema)
        
        # Remove None values to avoid database issues
        return {k: v for k, v in data.items() if v is not None}
    
    async def create(self, entity: Author) -> str:
        """Override create to use specialized save_author method if available"""
        try:
            self._logger.info(f"Creating author: {entity.author_name}")
            
            # Check if database has specialized save_author method
            if hasattr(self._database, 'save_author'):
                return await self._database.save_author(self._serialize(entity))
            else:
                # Use standard create method
                return await super().create(entity)
                
        except Exception as e:
            self._logger.error(f"Error creating author: {e}", error=e)
            raise
    
    def _deserialize(self, data: Dict[str, Any]) -> Author:
        """Convert database data to author entity"""
        return Author(
            id=data.get("id"),
            author_name=data.get("author_name", ""),
            pen_name=data.get("pen_name", ""),
            biography=data.get("biography", ""),
            writing_style=data.get("writing_style", ""),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            created_at=self._parse_datetime(data.get("created_at"))
        )
    
    
    async def get_by_user(self, user_id: str, limit: int = 50) -> List[Author]:
        """Get all authors for a specific user"""
        criteria = {"user_id": user_id}
        return await self.search(criteria, limit)
    
    async def get_by_session(self, session_id: str) -> List[Author]:
        """Get all authors for a specific session"""
        criteria = {"session_id": session_id}
        return await self.search(criteria, 100)
    
    async def search_by_name(self, user_id: str, name_query: str, limit: int = 20) -> List[Author]:
        """Search authors by name"""
        # Get all user authors and filter in memory
        user_authors = await self.get_by_user(user_id, 100)
        
        name_query_lower = name_query.lower()
        matching_authors = [
            author for author in user_authors
            if (name_query_lower in author.author_name.lower() or
                (author.pen_name and name_query_lower in author.pen_name.lower()))
        ]
        
        return matching_authors[:limit]
    
    async def get_recent_authors(self, user_id: str, limit: int = 10) -> List[Author]:
        """Get most recent authors for a user"""
        user_authors = await self.get_by_user(user_id, limit)
        
        # Sort by created_at descending
        sorted_authors = sorted(
            user_authors,
            key=lambda a: a.created_at or datetime.min,
            reverse=True
        )
        
        return sorted_authors[:limit]
    
    async def get_user_authors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all authors for a user in raw format (compatible with existing API)"""
        try:
            # Get authors as entities and convert to raw format for API compatibility
            authors = await self.get_by_user(user_id, limit)
            return [self._serialize(author) for author in authors]
        except Exception as e:
            self._logger.error(f"Error getting authors for user {user_id}: {e}", error=e)
            raise
    
    async def get_authors_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all authors for a session in raw format"""
        try:
            # Get authors as entities and convert to raw format
            authors = await self.get_by_session(session_id)
            return [self._serialize(author) for author in authors]
        except Exception as e:
            self._logger.error(f"Error getting authors for session {session_id}: {e}", error=e)
            raise
    
    async def get_authors_with_plot_counts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get authors with count of associated plots"""
        # This would require a more complex query with joins
        # For now, return basic author data
        authors = await self.get_by_user(user_id, 100)
        
        # Convert to dict format with placeholder plot counts
        authors_with_counts = []
        for author in authors:
            authors_with_counts.append({
                "id": author.id,
                "author_name": author.author_name,
                "pen_name": author.pen_name,
                "biography": author.biography,
                "writing_style": author.writing_style,
                "plot_count": 0,  # This would be calculated from actual plot relationships
                "created_at": author.created_at
            })
        
        return authors_with_counts