"""
WebSocket router for real-time communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..core.container import container
from ..websocket.websocket_handler import WebSocketHandler

router = APIRouter()


def get_websocket_handler() -> WebSocketHandler:
    """Dependency to get WebSocket handler"""
    return container.get("websocket_handler")


@router.websocket("/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str,
    handler: WebSocketHandler = Depends(get_websocket_handler)
):
    """WebSocket endpoint for real-time chat with the multi-agent system"""
    try:
        await handler.handle_connection(websocket, session_id)
    except WebSocketDisconnect:
        # Connection closed normally
        pass
    except Exception as e:
        # Log error but don't raise to avoid unhandled WebSocket errors
        handler.logger.error(f"WebSocket error for session {session_id}: {e}", error=e)