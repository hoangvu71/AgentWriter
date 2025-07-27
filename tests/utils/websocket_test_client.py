"""
WebSocket testing utilities for real-time communication testing.
Provides infrastructure for testing WebSocket endpoints and handlers.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, List, Optional
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from src.app import app
from src.routers.websocket import get_websocket_handler


class WebSocketTestClient:
    """
    Enhanced WebSocket test client for testing real-time communication.
    Provides mock WebSocket handler setup and message simulation.
    """
    
    def __init__(self):
        self.client = TestClient(app)
        self.mock_handler = None
        self.connection_messages = []
        self.sent_messages = []
        self.received_messages = []
    
    def setup_websocket_handler_mock(self) -> AsyncMock:
        """Setup mock WebSocketHandler with message tracking"""
        self.mock_handler = AsyncMock()
        self.mock_handler.logger = Mock()
        
        # Track connection handling
        async def mock_handle_connection(websocket, session_id):
            self.connection_messages.append({
                "action": "connection_start",
                "session_id": session_id,
                "websocket": websocket
            })
            
            # Simulate some message exchange
            await self._simulate_message_flow(websocket, session_id)
        
        self.mock_handler.handle_connection.side_effect = mock_handle_connection
        
        # Set dependency override
        app.dependency_overrides[get_websocket_handler] = lambda: self.mock_handler
        
        return self.mock_handler
    
    async def _simulate_message_flow(self, websocket, session_id):
        """Simulate typical WebSocket message flow"""
        try:
            # Simulate accepting connection
            await websocket.accept()
            
            # Simulate receiving and sending messages
            while True:
                # This would normally listen for messages
                # In testing, we can simulate specific message patterns
                await asyncio.sleep(0.1)  # Prevent tight loop
                
        except WebSocketDisconnect:
            self.connection_messages.append({
                "action": "disconnect",
                "session_id": session_id
            })
    
    def simulate_user_message(self, message: str, session_id: str = "test-session"):
        """Simulate receiving a user message"""
        message_data = {
            "type": "user_message",
            "content": message,
            "session_id": session_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        self.received_messages.append(message_data)
        return message_data
    
    def simulate_agent_response(self, agent_name: str, response: str, session_id: str = "test-session"):
        """Simulate an agent response"""
        response_data = {
            "type": "agent_response",
            "agent": agent_name,
            "content": response,
            "session_id": session_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        self.sent_messages.append(response_data)
        return response_data
    
    def simulate_websocket_disconnect(self):
        """Simulate WebSocket disconnect"""
        if self.mock_handler:
            self.mock_handler.handle_connection.side_effect = WebSocketDisconnect()
    
    def simulate_websocket_error(self, error_message: str = "Test error"):
        """Simulate WebSocket error"""
        if self.mock_handler:
            self.mock_handler.handle_connection.side_effect = Exception(error_message)
    
    def get_connection_count(self) -> int:
        """Get number of connection attempts"""
        return len([msg for msg in self.connection_messages if msg["action"] == "connection_start"])
    
    def get_disconnect_count(self) -> int:
        """Get number of disconnections"""
        return len([msg for msg in self.connection_messages if msg["action"] == "disconnect"])
    
    def was_handler_called(self) -> bool:
        """Check if WebSocket handler was called"""
        return self.mock_handler and self.mock_handler.handle_connection.called
    
    def get_last_session_id(self) -> Optional[str]:
        """Get the last session ID used in connection"""
        if self.connection_messages:
            return self.connection_messages[-1].get("session_id")
        return None
    
    def cleanup(self):
        """Clean up mock overrides"""
        app.dependency_overrides.clear()
        self.connection_messages.clear()
        self.sent_messages.clear()
        self.received_messages.clear()


class MockWebSocket:
    """
    Mock WebSocket for testing WebSocket handlers directly.
    Simulates WebSocket interface without actual network connection.
    """
    
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.sent_messages = []
        self.received_messages = []
        self.disconnect_on_receive = False
        self.error_on_receive = None
    
    async def accept(self):
        """Simulate accepting WebSocket connection"""
        self.accepted = True
    
    async def send_text(self, data: str):
        """Simulate sending text message"""
        if self.closed:
            raise WebSocketDisconnect()
        
        message = {
            "type": "text",
            "data": data,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        self.sent_messages.append(message)
    
    async def send_json(self, data: Dict[str, Any]):
        """Simulate sending JSON message"""
        if self.closed:
            raise WebSocketDisconnect()
        
        message = {
            "type": "json",
            "data": data,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        self.sent_messages.append(message)
    
    async def receive_text(self) -> str:
        """Simulate receiving text message"""
        if self.disconnect_on_receive:
            raise WebSocketDisconnect()
        
        if self.error_on_receive:
            raise Exception(self.error_on_receive)
        
        if self.received_messages:
            message = self.received_messages.pop(0)
            return message["data"] if isinstance(message, dict) else message
        
        # Default test message
        return "test message"
    
    async def receive_json(self) -> Dict[str, Any]:
        """Simulate receiving JSON message"""
        if self.disconnect_on_receive:
            raise WebSocketDisconnect()
        
        if self.error_on_receive:
            raise Exception(self.error_on_receive)
        
        if self.received_messages:
            message = self.received_messages.pop(0)
            return message["data"] if isinstance(message, dict) else json.loads(message)
        
        # Default test message
        return {"type": "test", "content": "test message"}
    
    async def close(self, code: int = 1000):
        """Simulate closing WebSocket connection"""
        self.closed = True
    
    def queue_message(self, message: str):
        """Queue a message to be received"""
        self.received_messages.append(message)
    
    def queue_json_message(self, data: Dict[str, Any]):
        """Queue a JSON message to be received"""
        self.received_messages.append({"type": "json", "data": data})
    
    def set_disconnect_on_receive(self):
        """Configure to disconnect when receiving next message"""
        self.disconnect_on_receive = True
    
    def set_error_on_receive(self, error_message: str):
        """Configure to raise error when receiving next message"""
        self.error_on_receive = error_message


@pytest.fixture
def websocket_test_client():
    """Pytest fixture providing WebSocketTestClient with automatic cleanup"""
    client = WebSocketTestClient()
    yield client
    client.cleanup()


@pytest.fixture
def mock_websocket():
    """Pytest fixture providing MockWebSocket for direct handler testing"""
    return MockWebSocket()


@pytest.fixture
def websocket_with_handler(websocket_test_client):
    """Pytest fixture with WebSocket handler mock setup"""
    mock_handler = websocket_test_client.setup_websocket_handler_mock()
    return websocket_test_client, mock_handler


# WebSocket message validation utilities
def validate_websocket_message(message: Dict[str, Any]) -> bool:
    """Validate WebSocket message structure"""
    required_fields = ["type", "timestamp"]
    return all(field in message for field in required_fields)


def validate_agent_response_message(message: Dict[str, Any]) -> bool:
    """Validate agent response message structure"""
    required_fields = ["type", "agent", "content", "session_id", "timestamp"]
    return (
        all(field in message for field in required_fields) and
        message["type"] == "agent_response" and
        isinstance(message["content"], str) and
        len(message["content"]) > 0
    )


def validate_error_message(message: Dict[str, Any]) -> bool:
    """Validate error message structure"""
    required_fields = ["type", "error", "timestamp"]
    return (
        all(field in message for field in required_fields) and
        message["type"] == "error" and
        isinstance(message["error"], str)
    )