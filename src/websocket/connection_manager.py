"""
WebSocket connection manager for handling client connections.
"""

from typing import Dict
import time
import asyncio
from fastapi import WebSocket
from ..core.interfaces import IConnectionManager
from ..core.logging import get_logger


class ConnectionManager(IConnectionManager):
    """Manages WebSocket connections with reconnection support"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_metadata: Dict[str, Dict] = {}  # Track session data for recovery
        self.logger = get_logger("websocket.manager")
        self._cleanup_task = None
        self._start_cleanup_task()
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a new WebSocket client with reconnection support"""
        await websocket.accept()
        
        # Check if this is a reconnection
        is_reconnection = client_id in self.session_metadata
        
        self.active_connections[client_id] = websocket
        
        # Initialize or restore session metadata
        current_time = time.time()
        if not is_reconnection:
            self.session_metadata[client_id] = {
                "connected_at": current_time,
                "reconnection_count": 0,
                "last_activity": current_time
            }
            self.logger.info(f"New client {client_id} connected", client_id=client_id)
        else:
            self.session_metadata[client_id]["reconnection_count"] += 1
            self.session_metadata[client_id]["last_activity"] = current_time
            self.logger.info(f"Client {client_id} reconnected (attempt #{self.session_metadata[client_id]['reconnection_count']})", 
                           client_id=client_id)
    
    def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client while preserving session metadata for reconnection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # Keep session metadata for potential reconnection - don't delete it here
            self.logger.info(f"Client {client_id} disconnected (session preserved for reconnection)", client_id=client_id)
    
    def cleanup_session(self, client_id: str) -> None:
        """Permanently clean up a session (call when session expires)"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.session_metadata:
            del self.session_metadata[client_id]
        self.logger.info(f"Session {client_id} permanently cleaned up", client_id=client_id)
    
    def get_session_metadata(self, client_id: str) -> Dict:
        """Get session metadata for reconnection purposes"""
        return self.session_metadata.get(client_id, {})
    
    async def send_message(self, message: str, client_id: str) -> None:
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                self.logger.error(f"Error sending message to {client_id}: {e}", client_id=client_id, error=e)
                self.disconnect(client_id)
    
    async def send_json(self, data: Dict, client_id: str) -> None:
        """Send JSON data to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                self.logger.error(f"Error sending JSON to {client_id}: {e}", client_id=client_id, error=e)
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: str) -> None:
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting to {client_id}: {e}", client_id=client_id, error=e)
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_json(self, data: Dict) -> None:
        """Broadcast JSON data to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                self.logger.error(f"Error broadcasting JSON to {client_id}: {e}", client_id=client_id, error=e)
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def get_connected_clients(self) -> list[str]:
        """Get list of connected client IDs"""
        return list(self.active_connections.keys())
    
    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected"""
        return client_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def _start_cleanup_task(self):
        """Start the background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodically clean up stale sessions (older than 1 hour)"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                current_time = time.time()
                stale_sessions = []
                
                for client_id, metadata in self.session_metadata.items():
                    # Clean up sessions older than 1 hour with no activity
                    if current_time - metadata.get('last_activity', 0) > 3600:
                        stale_sessions.append(client_id)
                
                for client_id in stale_sessions:
                    self.cleanup_session(client_id)
                    
                if stale_sessions:
                    self.logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
    
    def update_activity(self, client_id: str):
        """Update last activity timestamp for a client"""
        if client_id in self.session_metadata:
            self.session_metadata[client_id]['last_activity'] = time.time()
    
    def shutdown(self):
        """Shutdown the connection manager and cleanup resources"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        self.active_connections.clear()
        self.session_metadata.clear()