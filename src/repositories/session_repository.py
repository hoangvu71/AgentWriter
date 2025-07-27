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
            # Aggregate data from all content tables using repository pattern
            session_data = {
                "session_id": session_id,
                "plots": [],
                "authors": [],
                "world_building": [],
                "characters": [],
                "orchestrator_decisions": [],
                "critiques": [],
                "enhancements": [],
                "scores": []
            }
            
            # Get data from each table
            plots = await self._database.search("plots", criteria={"session_id": session_id})
            authors = await self._database.search("authors", criteria={"session_id": session_id})
            world_building = await self._database.search("world_building", criteria={"session_id": session_id})
            characters = await self._database.search("characters", criteria={"session_id": session_id})
            orchestrator_decisions = await self._database.search("orchestrator_decisions", criteria={"session_id": session_id})
            
            # Get iterative improvement data
            # Note: These tables are keyed by iteration_id, need to join through plots/content
            if plots:
                plot_ids = [plot.get("id") for plot in plots]
                for plot_id in plot_ids:
                    critiques = await self._database.search("critiques", criteria={"iteration_id": f"plot_{plot_id}"})
                    enhancements = await self._database.search("enhancements", criteria={"iteration_id": f"plot_{plot_id}"})
                    scores = await self._database.search("scores", criteria={"iteration_id": f"plot_{plot_id}"})
                    
                    session_data["critiques"].extend(critiques)
                    session_data["enhancements"].extend(enhancements)
                    session_data["scores"].extend(scores)
            
            # Populate session data
            session_data["plots"] = plots
            session_data["authors"] = authors
            session_data["world_building"] = world_building
            session_data["characters"] = characters
            session_data["orchestrator_decisions"] = orchestrator_decisions
            
            self._logger.info(f"Retrieved session data for {session_id} with {len(plots)} plots, {len(authors)} authors, {len(world_building)} worlds, {len(characters)} characters")
            
            return session_data
            
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
            plots = await self._database.search(
                "plots",
                criteria={},  # Get all plots
                limit=limit * 2  # Get more records to ensure enough unique sessions
            )
            
            # Group by session to get unique sessions
            sessions_map = {}
            for record in plots:
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
            
            # Limit to requested number of sessions
            sessions = list(sessions_map.values())[:limit]
            
            return {
                "sessions": sessions,
                "total_sessions": len(sessions),
                "limit": limit
            }
            
        except Exception as e:
            self._logger.error(f"Error getting recent sessions: {e}", error=e)
            raise
    
    async def save_orchestrator_decision(self, session_id: str, user_id: str, 
                                       decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save orchestrator routing decision for analysis and debugging.
        
        Args:
            session_id: Session identifier
            user_id: User identifier  
            decision_data: Orchestrator decision details
            
        Returns:
            Dictionary containing the saved decision record
        """
        try:
            # Prepare decision record using repository pattern
            decision_record = {
                "session_id": session_id,
                "user_id": user_id,
                "request_content": decision_data.get("request_content", ""),
                "routing_decision": decision_data.get("routing_decision", ""),
                "agents_selected": decision_data.get("agents_selected", []),
                "reasoning": decision_data.get("reasoning", ""),
                "confidence_score": decision_data.get("confidence_score", 0.0),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save using repository pattern
            response = await self._database.insert("orchestrator_decisions", decision_record)
            
            self._logger.info(f"Saved orchestrator decision for session {session_id}")
            return response
            
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
    
    async def ensure_session_exists(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Ensure a session exists in the database, create if it doesn't.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Dictionary containing session information
        """
        try:
            # Check if session exists
            existing_sessions = await self._database.search(
                "sessions", 
                criteria={"session_id": session_id}
            )
            
            if existing_sessions:
                self._logger.debug(f"Session {session_id} already exists")
                return existing_sessions[0]
            
            # Ensure user exists first (foreign key requirement) and get their UUID
            user_data = await self._ensure_user_exists(user_id)
            user_uuid = user_data["id"]  # Get the actual UUID for foreign key
            
            # Create new session
            session_data = {
                "session_id": session_id,    # external session identifier
                "user_id": user_uuid,        # internal user UUID for foreign key
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            session_record_id = await self._database.insert("sessions", session_data)
            self._logger.info(f"Created new session {session_id} for user {user_id}")
            
            return {
                "id": session_record_id,
                **session_data
            }
            
        except Exception as e:
            self._logger.error(f"Error ensuring session exists {session_id}: {e}", error=e)
            raise
    
    async def _ensure_user_exists(self, user_id: str) -> Dict[str, Any]:
        """
        Ensure a user exists in the database, create if it doesn't.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing user information
        """
        try:
            # Check if user exists (using correct field name)
            existing_users = await self._database.search(
                "users", 
                criteria={"user_id": user_id}
            )
            
            if existing_users:
                self._logger.debug(f"User {user_id} already exists")
                return existing_users[0]
            
            # Create new user (matching actual database schema)
            user_data = {
                "user_id": user_id,  # external user identifier
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            user_record_id = await self._database.insert("users", user_data)
            self._logger.info(f"Created new user {user_id}")
            
            return {
                "id": user_record_id,
                **user_data
            }
            
        except Exception as e:
            self._logger.error(f"Error ensuring user exists {user_id}: {e}", error=e)
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