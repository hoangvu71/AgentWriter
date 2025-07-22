"""
Session management endpoints for tracking user sessions.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..database.supabase_service import supabase_service
from ..core.logging import get_logger

router = APIRouter(prefix="/api", tags=["sessions"])
logger = get_logger("sessions")


@router.get("/sessions")
async def get_sessions(limit: int = 50) -> Dict[str, Any]:
    """
    Get list of all sessions with basic statistics.
    
    Args:
        limit: Maximum number of sessions to return
        
    Returns:
        Dictionary containing sessions list and statistics
    """
    if not supabase_service.client:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # Get recent sessions
        response = supabase_service.client.table("plots").select(
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
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific session.
    
    Args:
        session_id: The session ID to lookup
        
    Returns:
        Detailed session information including all related content
    """
    if not supabase_service.client:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        session_data = await supabase_service.get_session_data(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate session statistics
        total_content = sum(len(v) if isinstance(v, list) else 0 
                          for v in session_data.values())
        
        # Get session timeline
        created_times = []
        for content_type, items in session_data.items():
            if isinstance(items, list):
                for item in items:
                    if "created_at" in item:
                        created_times.append(item["created_at"])
        
        created_times.sort()
        session_start = created_times[0] if created_times else None
        session_end = created_times[-1] if created_times else None
        
        return {
            "session_id": session_id,
            "statistics": {
                "total_content": total_content,
                "plots": len(session_data.get("plots", [])),
                "authors": len(session_data.get("authors", [])),
                "world_building": len(session_data.get("world_building", [])),
                "characters": len(session_data.get("characters", [])),
                "session_start": session_start,
                "session_end": session_end
            },
            "content": session_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")


@router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(session_id: str) -> List[Dict[str, Any]]:
    """
    Get a chronological timeline of all content created in a session.
    
    Args:
        session_id: The session ID to lookup
        
    Returns:
        List of timeline events in chronological order
    """
    if not supabase_service.client:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        session_data = await supabase_service.get_session_data(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build timeline
        timeline = []
        
        # Add plots to timeline
        for plot in session_data.get("plots", []):
            timeline.append({
                "timestamp": plot.get("created_at"),
                "type": "plot",
                "id": plot.get("id"),
                "title": plot.get("title"),
                "summary": plot.get("plot_summary", "")[:100] + "..."
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building timeline for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build timeline: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """
    Delete all content associated with a session.
    WARNING: This is a destructive operation that cannot be undone.
    
    Args:
        session_id: The session ID to delete
        
    Returns:
        Confirmation message
    """
    if not supabase_service.client:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    try:
        # For safety, we'll just return a message for now
        # In production, you'd want additional confirmation
        return {
            "message": "Session deletion endpoint - implement with caution",
            "session_id": session_id,
            "warning": "This operation would permanently delete all session content"
        }
        
    except Exception as e:
        logger.error(f"Error in delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process deletion: {str(e)}")