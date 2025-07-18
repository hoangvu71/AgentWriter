"""
WebSocket connection manager for handling client connections.
"""

from typing import Dict
from fastapi import WebSocket
from ..core.interfaces import IConnectionManager
from ..core.logging import get_logger


class ConnectionManager(IConnectionManager):
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = get_logger("websocket.manager")
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.logger.info(f"Client {client_id} connected", client_id=client_id)
    
    def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"Client {client_id} disconnected", client_id=client_id)
    
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