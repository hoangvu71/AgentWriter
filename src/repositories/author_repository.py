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
            "session_id": author.session_id,
            "genre_expertise": author.genre_expertise,
            "target_audience_appeal": author.target_audience_appeal,
            "credentials": author.credentials,
            "personal_influences": author.personal_influences,
            "current_projects": author.current_projects,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Only include created_at for new authors
        if author.id is None:
            data["created_at"] = datetime.utcnow().isoformat()
        
        return data
    
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
            genre_expertise=data.get("genre_expertise", ""),
            target_audience_appeal=data.get("target_audience_appeal", ""),
            credentials=data.get("credentials", ""),
            personal_influences=data.get("personal_influences", ""),
            current_projects=data.get("current_projects", ""),
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
                name_query_lower in author.pen_name.lower())
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