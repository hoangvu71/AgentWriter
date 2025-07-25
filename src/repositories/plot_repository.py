"""
Repository for plot entity operations.
Aligned with actual Supabase schema.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from .batch_operations import BatchOperationsMixin
from ..models.entities import Plot
from ..database.supabase_adapter import SupabaseAdapter


class PlotRepository(BaseRepository[Plot]):
    """Repository for plot operations using actual Supabase schema with batch operations"""
    
    def __init__(self, database: SupabaseAdapter):
        super().__init__(database, "plots")
        self.batch_ops = BatchOperationsMixin(database, "plots")
    
    def _serialize(self, plot: Plot) -> Dict[str, Any]:
        """Convert plot entity to database format matching actual schema"""
        data = {
            "title": plot.title,
            "plot_summary": plot.plot_summary,
            "session_id": plot.session_id,  # UUID reference to sessions table
            "user_id": plot.user_id,  # UUID reference to users table
            "genre_id": plot.genre_id,  # UUID reference to genres table
            "subgenre_id": plot.subgenre_id,  # UUID reference to subgenres table
            "microgenre_id": plot.microgenre_id,  # UUID reference to microgenres table
            "trope_id": plot.trope_id,  # UUID reference to tropes table
            "tone_id": plot.tone_id,  # UUID reference to tones table
            "target_audience_id": plot.target_audience_id,  # UUID reference to target_audiences table
            "author_id": plot.author_id,  # UUID reference to authors table (nullable)
        }
        
        # Remove None values to avoid issues
        return {k: v for k, v in data.items() if v is not None}
    
    def _deserialize(self, data: Dict[str, Any]) -> Plot:
        """Convert database data to plot entity"""
        return Plot(
            id=data.get("id"),
            title=data.get("title", ""),
            plot_summary=data.get("plot_summary", ""),
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            genre_id=data.get("genre_id"),
            subgenre_id=data.get("subgenre_id"),
            microgenre_id=data.get("microgenre_id"),
            trope_id=data.get("trope_id"),
            tone_id=data.get("tone_id"),
            target_audience_id=data.get("target_audience_id"),
            author_id=data.get("author_id"),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at"))
        )
    
    async def create(self, entity: Plot) -> str:
        """Override create to use specialized save_plot method"""
        try:
            self._logger.info(f"Creating plot: {entity.title}")
            
            # Use the specialized save_plot method that handles session UUID conversion
            return await self._database.save_plot(self._serialize(entity))
            
        except Exception as e:
            self._logger.error(f"Error creating plot: {e}", error=e)
            raise
    
    
    async def get_by_user_external(self, external_user_id: str, limit: int = 50) -> List[Plot]:
        """Get all plots for a user using external user_id (not UUID)"""
        try:
            # Use the adapter's method that handles external user IDs
            raw_plots = await self._database.get_plots_by_user(external_user_id, limit)
            return [self._deserialize(plot_data) for plot_data in raw_plots]
        except Exception as e:
            self._logger.error(f"Error getting plots for user {external_user_id}: {e}", error=e)
            raise
    
    async def get_plots_with_authors_batch(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get plots with their authors using batch operations to avoid N+1 queries"""
        try:
            # Get all plots for user
            plots_data = await self._database.get_plots_by_user(user_id, limit)
            if not plots_data:
                return []
            
            # Extract unique author IDs
            author_ids = list(set([plot.get("author_id") for plot in plots_data if plot.get("author_id")]))
            
            # Batch get all authors
            authors_data = []
            if author_ids:
                authors_data = await self.batch_ops.batch_get_by_ids(author_ids)
            
            # Create author lookup map
            author_map = {author['id']: author for author in authors_data}
            
            # Combine plots with authors
            enriched_plots = []
            for plot_data in plots_data:
                author_id = plot_data.get("author_id")
                if author_id and author_id in author_map:
                    plot_data['author'] = author_map[author_id]
                enriched_plots.append(plot_data)
            
            return enriched_plots
            
        except Exception as e:
            self._logger.error(f"Error getting plots with authors batch: {e}", error=e)
            raise
    
    async def create_multiple_plots(self, plots: List[Plot]) -> List[str]:
        """Create multiple plots efficiently using batch operations"""
        try:
            # Use batch operations for better performance
            return await self.batch_ops.batch_create(plots)
        except Exception as e:
            self._logger.error(f"Error creating multiple plots: {e}", error=e)
            raise
    
    async def search_plots_with_related_data(
        self, 
        criteria: Dict[str, Any], 
        include_authors: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search plots with optional related data and pagination"""
        try:
            related_tables = []
            if include_authors:
                related_tables.append("authors")
            
            return await self.batch_ops.search_with_pagination_and_related(
                criteria, related_tables, limit, offset
            )
        except Exception as e:
            self._logger.error(f"Error searching plots with related data: {e}", error=e)
            raise
    
    async def get_by_session_external(self, external_session_id: str) -> List[Plot]:
        """Get all plots for a session using external session_id (not UUID)"""
        try:
            # This would need to be implemented in the adapter
            # For now, return empty list
            return []
        except Exception as e:
            self._logger.error(f"Error getting plots for session {external_session_id}: {e}", error=e)
            raise
    
    async def get_by_author(self, author_id: str) -> List[Plot]:
        """Get all plots by a specific author"""
        criteria = {"author_id": author_id}
        return await self.search(criteria, 100)
    
    async def search_by_title(self, user_id: str, title_query: str, limit: int = 20) -> List[Plot]:
        """Search plots by title using external user_id"""
        try:
            # Use the Supabase adapter's search method
            raw_plots = await self._database.service.search_plots(user_id, title_query, limit)
            return [self._deserialize(plot_data) for plot_data in raw_plots]
        except Exception as e:
            self._logger.error(f"Error searching plots by title: {e}", error=e)
            raise
    
    async def get_recent_plots(self, user_id: str, limit: int = 10) -> List[Plot]:
        """Get most recent plots for a user using external user_id"""
        try:
            # Get plots using external user ID (the adapter handles UUID conversion)
            plots = await self.get_by_user_external(user_id, limit)
            
            # Sort by created_at descending (should already be sorted from DB)
            sorted_plots = sorted(
                plots,
                key=lambda p: p.created_at or datetime.min,
                reverse=True
            )
            
            return sorted_plots[:limit]
        except Exception as e:
            self._logger.error(f"Error getting recent plots: {e}", error=e)
            raise
    
    async def get_plot_with_author(self, plot_id: str) -> Dict[str, Any]:
        """Get plot with associated author information"""
        try:
            return await self._database.get_plot_with_author(plot_id)
        except Exception as e:
            self._logger.error(f"Error getting plot with author: {e}", error=e)
            raise
    
    async def get_user_plots(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all plots for a user in raw format (compatible with existing API)"""
        try:
            # Use the adapter's method that returns raw data for API compatibility
            return await self._database.get_plots_by_user(user_id, limit)
        except Exception as e:
            self._logger.error(f"Error getting plots for user {user_id}: {e}", error=e)
            raise
    
    async def get_plots_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all plots for a session in raw format"""
        try:
            # Note: This would need to be implemented in the adapter if not already available
            # For now, we'll use the existing external method
            plots = await self.get_by_session_external(session_id)
            # Convert to raw format for API compatibility
            return [self._serialize(plot) for plot in plots]
        except Exception as e:
            self._logger.error(f"Error getting plots for session {session_id}: {e}", error=e)
            raise