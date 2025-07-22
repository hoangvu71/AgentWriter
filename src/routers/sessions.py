"""
Session management endpoints for tracking user sessions.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.container import container
from ..core.logging import get_logger

router = APIRouter(prefix="/api", tags=["sessions"])
logger = get_logger("sessions")


def get_session_repository():
    """Dependency injection for SessionRepository"""
    try:
        return container.get("session_repository")
    except Exception as e:
        logger.error(f"Failed to get session repository: {e}")
        raise HTTPException(status_code=500, detail="Session service unavailable")


@router.get("/sessions")
async def get_sessions(
    limit: int = 50, 
    session_repository = Depends(get_session_repository)
) -> Dict[str, Any]:
    """
    Get list of all sessions with basic statistics.
    
    Args:
        limit: Maximum number of sessions to return
        session_repository: Injected session repository
        
    Returns:
        Dictionary containing sessions list and statistics
    """
    try:
        return await session_repository.get_recent_sessions(limit)
        
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    session_repository = Depends(get_session_repository)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific session.
    
    Args:
        session_id: The session ID to lookup
        session_repository: Injected session repository
        
    Returns:
        Detailed session information including all related content
    """
    try:
        session_details = await session_repository.get_session_statistics(session_id)
        
        if not session_details["exists"]:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")


@router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(
    session_id: str,
    session_repository = Depends(get_session_repository)
) -> List[Dict[str, Any]]:
    """
    Get a chronological timeline of all content created in a session.
    
    Args:
        session_id: The session ID to lookup
        session_repository: Injected session repository
        
    Returns:
        List of timeline events in chronological order
    """
    try:
        timeline = await session_repository.get_session_timeline(session_id)
        
        if not timeline:
            # Check if session exists
            session_details = await session_repository.get_session_statistics(session_id)
            if not session_details["exists"]:
                raise HTTPException(status_code=404, detail="Session not found")
        
        return timeline
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building timeline for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build timeline: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_repository = Depends(get_session_repository)
) -> Dict[str, str]:
    """
    Delete all content associated with a session.
    WARNING: This is a destructive operation that cannot be undone.
    
    Args:
        session_id: The session ID to delete
        session_repository: Injected session repository
        
    Returns:
        Confirmation message
    """
    try:
        return await session_repository.delete_session(session_id)
        
    except Exception as e:
        logger.error(f"Error in delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process deletion: {str(e)}")