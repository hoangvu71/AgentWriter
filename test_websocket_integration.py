import pytest
import asyncio
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import websockets


class TestWebSocketIntegration:
    """Integration tests for FastAPI WebSocket endpoint with ADK agent"""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app"""
        from main import app  # Will implement this later
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_websocket_connection(self, client):
        """Test basic WebSocket connection"""
        # Act & Assert
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None
    
    def test_websocket_message_exchange(self, client):
        """Test sending and receiving messages via WebSocket"""
        # Arrange
        test_message = {
            "type": "message",
            "content": "Hello, agent!"
        }
        
        # Act & Assert
        with client.websocket_connect("/ws") as websocket:
            # Send message
            websocket.send_json(test_message)
            
            # Receive response
            response = websocket.receive_json()
            
            # Assert
            assert response is not None
            assert "content" in response
            assert isinstance(response["content"], str)
            assert len(response["content"]) > 0
    
    def test_websocket_search_request(self, client):
        """Test search functionality via WebSocket"""
        # Arrange
        search_request = {
            "type": "search",
            "content": "What is the weather in Paris?"
        }
        
        # Act & Assert
        with client.websocket_connect("/ws") as websocket:
            # Send search request
            websocket.send_json(search_request)
            
            # Receive response
            response = websocket.receive_json()
            
            # Assert
            assert response is not None
            assert "content" in response
            # Should contain weather-related or Paris-related content
            assert any(word in response["content"].lower() 
                      for word in ["paris", "weather", "temperature", "degrees"])
    
    def test_websocket_streaming_response(self, client):
        """Test that responses can be streamed"""
        # Arrange
        request = {
            "type": "message",
            "content": "Tell me a short story",
            "stream": True
        }
        
        # Act
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(request)
            
            # Collect streamed chunks
            chunks = []
            while True:
                response = websocket.receive_json()
                if response.get("type") == "stream_end":
                    break
                if response.get("type") == "stream_chunk":
                    chunks.append(response.get("content", ""))
            
            # Assert
            assert len(chunks) > 0
            full_response = "".join(chunks)
            assert len(full_response) > 0
    
    def test_websocket_session_memory(self, client):
        """Test that WebSocket maintains session memory"""
        # Act & Assert
        with client.websocket_connect("/ws") as websocket:
            # First message
            websocket.send_json({
                "type": "message",
                "content": "My favorite color is blue"
            })
            response1 = websocket.receive_json()
            
            # Second message referencing first
            websocket.send_json({
                "type": "message",
                "content": "What is my favorite color?"
            })
            response2 = websocket.receive_json()
            
            # Assert memory retention
            assert "blue" in response2["content"].lower()
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self, client):
        """Test multiple concurrent WebSocket connections"""
        # Arrange
        async def connect_and_send(session_id: int):
            uri = "ws://localhost:8000/ws"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({
                    "type": "message",
                    "content": f"Hello from session {session_id}"
                }))
                response = await websocket.recv()
                return json.loads(response)
        
        # Act - Create multiple connections
        tasks = [connect_and_send(i) for i in range(3)]
        responses = await asyncio.gather(*tasks)
        
        # Assert
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert response is not None
            assert "content" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])