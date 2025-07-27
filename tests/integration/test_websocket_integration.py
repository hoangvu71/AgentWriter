"""
Integration Test Suite for WebSocket Real-Time Communication.

This module tests end-to-end WebSocket functionality:
- Real-time agent response streaming
- Session management through WebSocket connections
- Error handling and recovery in WebSocket context
- Multi-user WebSocket coordination
- Performance under load
"""

# Install mocks before any imports that might need them
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mocks'))

from google_adk import install_mocks as install_adk_mocks
from observability import install_mocks as install_observability_mocks

install_adk_mocks()
install_observability_mocks()

import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.websocket.websocket_handler import WebSocketHandler
from src.core.interfaces import AgentRequest, AgentResponse, ContentType
from src.core.configuration import Configuration


class TestWebSocketAgentIntegration:
    """Test WebSocket integration with agent system"""
    
    @pytest.mark.asyncio
    async def test_websocket_plot_generation_streaming(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        Test real-time plot generation through WebSocket
        Should stream plot generation progress to client
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        
        session_id = "websocket-plot-session"
        user_id = "websocket-user"
        
        # Mock streaming plot generation response
        async def mock_streaming_response(*args, **kwargs):
            yield MagicMock(content='{"title": "The Crystal')
            yield MagicMock(content=' Quest", "genre": "Fantasy"')
            yield MagicMock(content=', "summary": "A young hero seeks magical crystals"}')
        
        mock_vertex_ai['runner'].run_async = mock_streaming_response
        
        message_data = {
            "type": "generate_plot",
            "content": "Create a fantasy adventure plot",
            "session_id": session_id,
            "user_id": user_id,
            "stream": True
        }
        
        # Act
        await handler.handle_message(mock_websocket, json.dumps(message_data))
        
        # Assert
        # Verify multiple WebSocket sends for streaming
        assert mock_websocket.send.call_count >= 2  # At least start and progress messages
        
        # Check that streaming messages were sent
        sent_messages = [call.args[0] for call in mock_websocket.send.call_args_list]
        assert any("status" in msg for msg in sent_messages)
    
    @pytest.mark.asyncio
    async def test_websocket_multi_agent_coordination(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        Test multi-agent coordination through WebSocket
        Should handle complex workflows with real-time updates
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        
        session_id = "multi-agent-session"
        user_id = "coordination-user"
        
        # Mock orchestrator response for multi-agent workflow
        async def mock_orchestrator_response(*args, **kwargs):
            yield MagicMock(content="Starting multi-agent book creation workflow")
            yield MagicMock(content="Step 1: Generating plot")
            yield MagicMock(content="Step 2: Creating author profile")
            yield MagicMock(content="Step 3: Building world details")
            yield MagicMock(content="Workflow completed successfully")
        
        mock_vertex_ai['runner'].run_async = mock_orchestrator_response
        
        message_data = {
            "type": "create_book",
            "content": "Create a complete fantasy book project",
            "session_id": session_id,
            "user_id": user_id,
            "workflow": "multi_agent",
            "stream": True
        }
        
        # Act
        await handler.handle_message(mock_websocket, json.dumps(message_data))
        
        # Assert
        assert mock_websocket.send.call_count >= 3  # Multiple workflow steps
        
        # Verify workflow progress messages
        sent_messages = [call.args[0] for call in mock_websocket.send.call_args_list]
        workflow_messages = [msg for msg in sent_messages if "Step" in msg or "workflow" in msg.lower()]
        assert len(workflow_messages) > 0


class TestWebSocketSessionManagement:
    """Test WebSocket session management and state persistence"""
    
    @pytest.mark.asyncio
    async def test_websocket_session_continuity(self, mock_config, mock_adk_services):
        """
        Test session continuity across WebSocket connections
        Should maintain context across reconnections
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        session_id = "continuity-session"
        user_id = "persistent-user"
        
        # First connection - establish session
        message1_data = {
            "type": "start_session",
            "session_id": session_id,
            "user_id": user_id,
            "context": {"project_type": "fantasy_novel"}
        }
        
        # Second connection - continue session
        message2_data = {
            "type": "generate_plot",
            "content": "Continue working on the fantasy novel",
            "session_id": session_id,
            "user_id": user_id
        }
        
        # Act
        await handler.handle_message(mock_websocket1, json.dumps(message1_data))
        await handler.handle_message(mock_websocket2, json.dumps(message2_data))
        
        # Assert
        # Both connections should have received responses
        assert mock_websocket1.send.called
        assert mock_websocket2.send.called
        
        # Session should be maintained
        assert session_id in handler._sessions
    
    @pytest.mark.asyncio
    async def test_websocket_multi_user_isolation(self, mock_config, mock_adk_services):
        """
        Test isolation between different user sessions
        Should prevent cross-user data leakage
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        
        # Two different users
        user1_websocket = AsyncMock()
        user2_websocket = AsyncMock()
        
        user1_data = {
            "type": "generate_plot",
            "content": "Create a sci-fi plot",
            "session_id": "user1-session",
            "user_id": "user1"
        }
        
        user2_data = {
            "type": "generate_plot", 
            "content": "Create a fantasy plot",
            "session_id": "user2-session",
            "user_id": "user2"
        }
        
        # Act
        await handler.handle_message(user1_websocket, json.dumps(user1_data))
        await handler.handle_message(user2_websocket, json.dumps(user2_data))
        
        # Assert
        # Both users should receive responses
        assert user1_websocket.send.called
        assert user2_websocket.send.called
        
        # Sessions should be separate
        assert "user1-session" in handler._sessions
        assert "user2-session" in handler._sessions
        assert handler._sessions["user1-session"] != handler._sessions["user2-session"]


class TestWebSocketErrorHandling:
    """Test WebSocket error handling and recovery"""
    
    @pytest.mark.asyncio
    async def test_websocket_agent_error_handling(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        Test error handling when agents fail during WebSocket operations
        Should provide graceful error responses
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        
        # Mock agent failure
        async def mock_agent_failure(*args, **kwargs):
            raise Exception("Agent processing failed")
        
        mock_vertex_ai['runner'].run_async = mock_agent_failure
        
        message_data = {
            "type": "generate_plot",
            "content": "Create a plot",
            "session_id": "error-session", 
            "user_id": "error-user"
        }
        
        # Act
        await handler.handle_message(mock_websocket, json.dumps(message_data))
        
        # Assert
        assert mock_websocket.send.called
        
        # Check that error message was sent
        sent_message = mock_websocket.send.call_args[0][0]
        assert "error" in sent_message.lower() or "failed" in sent_message.lower()
    
    @pytest.mark.asyncio
    async def test_websocket_malformed_message_handling(self, mock_config, mock_adk_services):
        """
        Test handling of malformed WebSocket messages
        Should reject invalid messages gracefully
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        
        # Malformed JSON message
        malformed_message = '{"type": "generate_plot", "content": incomplete json'
        
        # Act
        await handler.handle_message(mock_websocket, malformed_message)
        
        # Assert
        assert mock_websocket.send.called
        
        # Should send error response
        sent_message = mock_websocket.send.call_args[0][0]
        error_data = json.loads(sent_message)
        assert error_data.get("status") == "error"
    
    @pytest.mark.asyncio
    async def test_websocket_connection_recovery(self, mock_config, mock_adk_services):
        """
        Test WebSocket connection recovery after network issues
        Should handle reconnections gracefully
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        
        session_id = "recovery-session"
        user_id = "recovery-user"
        
        # Simulate connection drop during operation
        mock_websocket.send.side_effect = [None, ConnectionError("Connection lost"), None]
        
        message_data = {
            "type": "generate_plot",
            "content": "Create a plot",
            "session_id": session_id,
            "user_id": user_id
        }
        
        # Act - Multiple attempts
        try:
            await handler.handle_message(mock_websocket, json.dumps(message_data))
        except ConnectionError:
            pass  # Expected for connection drop simulation
        
        # Reconnect attempt
        mock_websocket.send.side_effect = None  # Reset to normal
        await handler.handle_message(mock_websocket, json.dumps(message_data))
        
        # Assert
        # Should handle reconnection gracefully
        assert mock_websocket.send.call_count >= 2


class TestWebSocketPerformance:
    """Test WebSocket performance under various conditions"""
    
    @pytest.mark.asyncio
    async def test_websocket_high_message_volume(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        Test WebSocket performance with high message volume
        Should handle multiple rapid messages efficiently
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        
        # Mock fast responses
        async def mock_fast_response(*args, **kwargs):
            yield MagicMock(content="Quick response")
        
        mock_vertex_ai['runner'].run_async = mock_fast_response
        
        # Create multiple rapid messages
        messages = []
        for i in range(10):
            messages.append({
                "type": "generate_plot",
                "content": f"Create plot {i}",
                "session_id": f"rapid-session-{i}",
                "user_id": "rapid-user"
            })
        
        # Act - Send messages rapidly
        import time
        start_time = time.time()
        
        tasks = []
        for message in messages:
            task = handler.handle_message(mock_websocket, json.dumps(message))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Assert
        # Should handle all messages quickly
        assert total_duration < 5.0  # 5 seconds for 10 messages
        assert mock_websocket.send.call_count >= 10  # At least one response per message
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_users_performance(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        Test WebSocket performance with multiple concurrent users
        Should handle multiple users simultaneously
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        
        # Create multiple user connections
        user_websockets = [AsyncMock() for _ in range(5)]
        
        # Mock responses
        async def mock_user_response(*args, **kwargs):
            yield MagicMock(content="User response")
        
        mock_vertex_ai['runner'].run_async = mock_user_response
        
        # Create messages for different users
        user_messages = []
        for i, websocket in enumerate(user_websockets):
            message = {
                "type": "generate_plot",
                "content": f"Create plot for user {i}",
                "session_id": f"user-session-{i}",
                "user_id": f"user-{i}"
            }
            user_messages.append((websocket, message))
        
        # Act - Handle concurrent users
        import time
        start_time = time.time()
        
        tasks = []
        for websocket, message in user_messages:
            task = handler.handle_message(websocket, json.dumps(message))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        concurrent_duration = end_time - start_time
        
        # Assert
        # Should handle all users efficiently
        assert concurrent_duration < 3.0  # 3 seconds for 5 users
        
        # All users should receive responses
        for websocket in user_websockets:
            assert websocket.send.called
    
    @pytest.mark.asyncio
    async def test_websocket_large_response_handling(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        Test WebSocket handling of large responses
        Should efficiently stream large content
        """
        # Arrange
        handler = WebSocketHandler(mock_config)
        mock_websocket = AsyncMock()
        
        # Mock large response
        large_content = "This is a very long response. " * 100  # 3000+ characters
        
        async def mock_large_response(*args, **kwargs):
            # Split large content into chunks
            chunk_size = 100
            for i in range(0, len(large_content), chunk_size):
                chunk = large_content[i:i + chunk_size]
                yield MagicMock(content=chunk)
        
        mock_vertex_ai['runner'].run_async = mock_large_response
        
        message_data = {
            "type": "generate_plot",
            "content": "Create a very detailed plot",
            "session_id": "large-response-session",
            "user_id": "large-response-user",
            "stream": True
        }
        
        # Act
        import time
        start_time = time.time()
        
        await handler.handle_message(mock_websocket, json.dumps(message_data))
        
        end_time = time.time()
        large_response_duration = end_time - start_time
        
        # Assert
        # Should handle large response efficiently
        assert large_response_duration < 2.0  # Should stream quickly
        
        # Should have sent multiple chunks
        assert mock_websocket.send.call_count >= 5  # Multiple chunks for large content