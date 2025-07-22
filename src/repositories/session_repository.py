"""
Repository for session-related operations.
Handles session data aggregation, orchestrator decisions, and session management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..database.supabase_adapter import SupabaseAdapter
from ..core.logging import get_logger


class SessionRepository:
    """Repository for session operations and data aggregation"""
    
    def __init__(self, database: SupabaseAdapter):
        self._database = database
        self._logger = get_logger("session_repository")
    
    async def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        Aggregate all content for a session across all tables.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary containing all session content grouped by type
        """
        try:
            # Use the existing service method for session data aggregation
            return await self._database.service.get_session_data(session_id)
        except Exception as e:
            self._logger.error(f"Error getting session data for {session_id}: {e}", error=e)
            raise
    
    async def get_session_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of all content created in a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of timeline events sorted by creation time
        """
        try:
            # Get session data first
            session_data = await self.get_session_data(session_id)
            
            if not session_data:
                return []
            
            # Build timeline from all content types
            timeline = []
            
            # Add plots to timeline
            for plot in session_data.get("plots", []):
                timeline.append({
                    "timestamp": plot.get("created_at"),
                    "type": "plot",
                    "id": plot.get("id"),
                    "title": plot.get("title"),
                    "summary": plot.get("plot_summary", "")[:100] + "..." if plot.get("plot_summary") else ""
                })
            
            # Add authors to timeline
            for author in session_data.get("authors", []):
                timeline.append({
                    "timestamp": author.get("created_at"),
                    "type": "author",
                    "id": author.get("id"),
                    "name": author.get("author_name"),
                    "pen_name": author.get("pen_name")
                })
            
            # Add world building to timeline
            for world in session_data.get("world_building", []):
                timeline.append({
                    "timestamp": world.get("created_at"),
                    "type": "world_building",
                    "id": world.get("id"),
                    "name": world.get("world_name"),
                    "plot_id": world.get("plot_id")
                })
            
            # Add characters to timeline
            for char_set in session_data.get("characters", []):
                timeline.append({
                    "timestamp": char_set.get("created_at"),
                    "type": "characters",
                    "id": char_set.get("id"),
                    "count": char_set.get("character_count"),
                    "plot_id": char_set.get("plot_id")
                })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x.get("timestamp", ""))
            
            return timeline
            
        except Exception as e:
            self._logger.error(f"Error building timeline for session {session_id}: {e}", error=e)
            raise
    
    async def get_recent_sessions(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get list of recent sessions with basic statistics.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            Dictionary containing sessions list and statistics
        """
        try:
            # Query plots table to get unique sessions (most common content type)
            response = self._database.service.client.table("plots").select(
                "session_id, user_id, created_at"
            ).order("created_at", desc=True).limit(limit).execute()
            
            # Group by session to get unique sessions
            sessions_map = {}
            for record in response.data:
                session_id = record.get("session_id")
                if session_id and session_id not in sessions_map:
                    sessions_map[session_id] = {
                        "session_id": session_id,
                        "user_id": record.get("user_id"),
                        "created_at": record.get("created_at"),
                        "content_count": 0
                    }
                if session_id:
                    sessions_map[session_id]["content_count"] += 1
            
            sessions = list(sessions_map.values())
            
            return {
                "sessions": sessions,
                "total_sessions": len(sessions),
                "limit": limit
            }
            
        except Exception as e:
            self._logger.error(f"Error getting recent sessions: {e}", error=e)
            raise
    
    async def save_orchestrator_decision(self, session_id: str, user_id: str, 
                                       decision_data: Dict[str, Any]) -> None:
        """
        Save orchestrator routing decision for analysis and debugging.
        
        Args:
            session_id: Session identifier
            user_id: User identifier  
            decision_data: Orchestrator decision details
        """
        try:
            # Use the existing service method
            await self._database.service.save_orchestrator_decision(
                session_id=session_id,
                user_id=user_id,
                **decision_data
            )
        except Exception as e:
            self._logger.error(f"Error saving orchestrator decision: {e}", error=e)
            raise
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary containing session statistics
        """
        try:
            session_data = await self.get_session_data(session_id)
            
            if not session_data:
                return {
                    "session_id": session_id,
                    "exists": False,
                    "statistics": {}
                }
            
            # Calculate statistics
            stats = {
                "total_content": 0,
                "plots": len(session_data.get("plots", [])),
                "authors": len(session_data.get("authors", [])),
                "world_building": len(session_data.get("world_building", [])),
                "characters": len(session_data.get("characters", [])),
            }
            
            stats["total_content"] = sum(stats[key] for key in ["plots", "authors", "world_building", "characters"])
            
            # Get timeline for session duration
            timeline = await self.get_session_timeline(session_id)
            if timeline:
                stats["session_start"] = timeline[0]["timestamp"]
                stats["session_end"] = timeline[-1]["timestamp"]
                stats["duration_items"] = len(timeline)
            
            return {
                "session_id": session_id,
                "exists": True,
                "statistics": stats,
                "content": session_data
            }
            
        except Exception as e:
            self._logger.error(f"Error getting session statistics for {session_id}: {e}", error=e)
            raise
    
    async def delete_session(self, session_id: str) -> Dict[str, str]:
        """
        Delete all content associated with a session.
        WARNING: This is a destructive operation.
        
        Args:
            session_id: Session identifier to delete
            
        Returns:
            Confirmation message
        """
        try:
            # For safety, we'll just return a warning message for now
            # In production, this would need additional confirmation mechanisms
            return {
                "message": "Session deletion endpoint - implement with caution",
                "session_id": session_id,
                "warning": "This operation would permanently delete all session content",
                "status": "not_implemented"
            }
        except Exception as e:
            self._logger.error(f"Error in delete session {session_id}: {e}", error=e)
            raise
    
    async def search_sessions(self, user_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search sessions with optional user filter.
        
        Args:
            user_id: Optional user filter
            limit: Maximum results to return
            
        Returns:
            List of matching sessions
        """
        try:
            if user_id:
                # Get sessions for specific user
                response = self._database.service.client.table("plots").select(
                    "session_id, user_id, created_at"
                ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            else:
                # Get all sessions
                response = self._database.service.client.table("plots").select(
                    "session_id, user_id, created_at"
                ).order("created_at", desc=True).limit(limit).execute()
            
            # Group by session
            sessions_map = {}
            for record in response.data:
                session_id = record.get("session_id")
                if session_id and session_id not in sessions_map:
                    sessions_map[session_id] = {
                        "session_id": session_id,
                        "user_id": record.get("user_id"),
                        "created_at": record.get("created_at"),
                        "content_count": 0
                    }
                if session_id:
                    sessions_map[session_id]["content_count"] += 1
            
            return list(sessions_map.values())
            
        except Exception as e:
            self._logger.error(f"Error searching sessions: {e}", error=e)
            raise