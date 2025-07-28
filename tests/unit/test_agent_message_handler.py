"""
TDD Test Suite for AgentMessageHandler class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- Message preparation with context
- Conversation history integration
- Session context handling
- Context formatting
- Tool-specific message preparation
"""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Mock Google dependencies before importing
mock_google_adk = MagicMock()
sys.modules['google.adk'] = mock_google_adk

from src.core.agent_modules.agent_message_handler import AgentMessageHandler
from src.core.interfaces import AgentRequest


class TestAgentMessageHandlerInitialization:
    """Test AgentMessageHandler initialization"""
    
    def test_message_handler_basic_initialization(self):
        """
        RED: Test basic AgentMessageHandler initialization
        Should initialize with logger and conversation manager
        """
        # Arrange
        agent_name = "test_agent"
        adk_factory = MagicMock()
        tools = []
        
        # Act
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Assert
        assert message_handler.agent_name == agent_name
        assert message_handler.adk_factory == adk_factory
        assert message_handler.tools == tools
        assert message_handler.logger is not None
        assert message_handler.conversation_manager is None  # Lazy initialization
    
    def test_message_handler_with_tools(self):
        """
        RED: Test AgentMessageHandler initialization with tools
        Should properly initialize with tools list
        """
        # Arrange
        agent_name = "tool_agent"
        adk_factory = MagicMock()
        tools = [MagicMock(name="save_plot"), MagicMock(name="get_plot")]
        
        # Act
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Assert
        assert message_handler.agent_name == agent_name
        assert message_handler.tools == tools
        assert len(message_handler.tools) == 2


class TestAgentMessageHandlerBasicPreparation:
    """Test basic message preparation functionality"""
    
    @pytest.mark.asyncio
    async def test_prepare_message_basic(self, basic_agent_request):
        """
        RED: Test basic message preparation
        Should handle basic AgentRequest and return prepared message
        """
        # Arrange
        agent_name = "test_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Mock conversation manager to return no history
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {"has_conversation_history": False}
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(basic_agent_request)
            
            # Assert
            assert basic_agent_request.content in message
            assert "Generate a fantasy plot" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_context(self, complex_agent_request):
        """
        RED: Test message preparation with complex context
        Should include context information in prepared message
        """
        # Arrange
        agent_name = "context_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Mock conversation manager to return no history
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {"has_conversation_history": False}
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(complex_agent_request)
            
            # Assert
            assert complex_agent_request.content in message
            assert "CONTEXT:" in message
            assert "GENRE_HIERARCHY" in message.upper()
            assert "Epic Fantasy" in message
            assert "dragons" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_tools_adds_session_context(self, basic_agent_request):
        """
        RED: Test message preparation for agents with tools
        Should add session context for tool execution
        """
        # Arrange
        agent_name = "tool_agent"
        adk_factory = MagicMock()
        tools = [MagicMock(name="save_plot")]
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Mock conversation manager to return no history
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {"has_conversation_history": False}
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(basic_agent_request)
            
            # Assert
            assert "SESSION CONTEXT:" in message
            assert f"session_id: {basic_agent_request.session_id}" in message
            assert f"user_id: {basic_agent_request.user_id}" in message


class TestAgentMessageHandlerConversationHistory:
    """Test conversation history integration"""
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_conversation_history(self, basic_agent_request):
        """
        RED: Test message preparation with conversation history
        Should include conversation context when available
        """
        # Arrange
        agent_name = "conv_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Mock conversation manager to return history
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {
                "has_conversation_history": True,
                "context_summary": "Previously discussed fantasy themes",
                "user_preferences": {"genre": "fantasy", "style": "epic"}
            }
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(basic_agent_request)
            
            # Assert
            assert "CONVERSATION HISTORY:" in message
            assert "Previously discussed fantasy themes" in message
            assert "User Preferences:" in message
            assert "genre: fantasy" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_conversation_manager_lazy_initialization(self, basic_agent_request):
        """
        RED: Test conversation manager lazy initialization
        Should initialize conversation manager only when needed
        """
        # Arrange
        agent_name = "lazy_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Initially should be None
        assert message_handler.conversation_manager is None
        
        # Mock get_conversation_manager function
        with patch('src.core.agent_modules.agent_message_handler.get_conversation_manager') as mock_get_conv_func:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {"has_conversation_history": False}
            mock_get_conv_func.return_value = mock_conv
            
            # Act
            await message_handler.prepare_message(basic_agent_request)
            
            # Assert
            assert message_handler.conversation_manager is not None
            mock_get_conv_func.assert_called_once_with(adk_factory)


class TestAgentMessageHandlerContextFormatting:
    """Test context formatting functionality"""
    
    def test_format_context_with_simple_values(self):
        """
        RED: Test context formatting with simple values
        Should format simple key-value pairs correctly
        """
        # Arrange
        agent_name = "format_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        context = {
            "genre": "fantasy",
            "length": "novel",
            "target_age": "adult"
        }
        
        # Act
        formatted = message_handler.format_context(context)
        
        # Assert
        assert "GENRE: fantasy" in formatted
        assert "LENGTH: novel" in formatted
        assert "TARGET_AGE: adult" in formatted
    
    def test_format_context_with_complex_values(self):
        """
        RED: Test context formatting with complex values
        Should handle dictionaries, lists, and nested structures
        """
        # Arrange
        agent_name = "complex_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        context = {
            "genre_hierarchy": {
                "main": "fantasy",
                "sub": "epic fantasy"
            },
            "themes": ["heroism", "magic", "adventure"],
            "settings": {"primary": "medieval", "secondary": "magical"}
        }
        
        # Act
        formatted = message_handler.format_context(context)
        
        # Assert
        assert "GENRE_HIERARCHY:" in formatted
        assert "main" in formatted
        assert "epic fantasy" in formatted
        assert "THEMES:" in formatted
        assert "heroism" in formatted
        assert "magic" in formatted
        assert "SETTINGS:" in formatted
    
    def test_format_context_empty(self):
        """
        RED: Test context formatting with empty context
        Should handle empty context gracefully
        """
        # Arrange
        agent_name = "empty_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        context = {}
        
        # Act
        formatted = message_handler.format_context(context)
        
        # Assert
        assert formatted == ""


class TestAgentMessageHandlerEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_none_context(self):
        """
        RED: Test message preparation with None context
        Should handle None context gracefully
        """
        # Arrange
        agent_name = "none_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Create request with None context
        request = AgentRequest(
            content="Test message",
            user_id="test-user",
            session_id="test-session",
            context=None
        )
        
        # Mock conversation manager
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {"has_conversation_history": False}
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(request)
            
            # Assert
            assert "Test message" in message
            assert "CONTEXT:" not in message  # Should not add context section
    
    @pytest.mark.asyncio
    async def test_prepare_message_conversation_manager_error_handling(self, basic_agent_request):
        """
        RED: Test conversation manager error handling
        Should gracefully handle conversation manager errors
        """
        # Arrange
        agent_name = "error_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Mock conversation manager to raise error
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.side_effect = Exception("Conversation error")
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(basic_agent_request)
            
            # Assert
            # Should still return the basic message even if conversation manager fails
            assert basic_agent_request.content in message
            assert "CONVERSATION HISTORY:" not in message
    
    def test_format_context_with_none_values(self):
        """
        RED: Test context formatting with None values
        Should handle None values in context gracefully
        """
        # Arrange
        agent_name = "none_values_agent"
        adk_factory = MagicMock()
        tools = []
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        context = {
            "genre": "fantasy",
            "theme": None,
            "setting": "medieval"
        }
        
        # Act
        formatted = message_handler.format_context(context)
        
        # Assert
        assert "GENRE: fantasy" in formatted
        assert "THEME: None" in formatted
        assert "SETTING: medieval" in formatted


class TestAgentMessageHandlerIntegration:
    """Integration tests for AgentMessageHandler"""
    
    @pytest.mark.asyncio
    async def test_full_message_preparation_workflow(self):
        """
        RED: Test complete message preparation workflow
        Should handle all components: content, context, history, session info
        """
        # Arrange
        agent_name = "integration_agent"
        adk_factory = MagicMock()
        tools = [MagicMock(name="save_plot")]
        message_handler = AgentMessageHandler(agent_name, adk_factory, tools)
        
        # Create complex request
        request = AgentRequest(
            content="Create an epic fantasy plot",
            user_id="user-123",
            session_id="session-456",
            context={
                "genre": "fantasy",
                "themes": ["magic", "heroism"],
                "target_length": "novel"
            }
        )
        
        # Mock conversation manager with rich history
        with patch.object(message_handler, '_get_conversation_manager') as mock_get_conv:
            mock_conv = AsyncMock()
            mock_conv.get_conversation_context.return_value = {
                "has_conversation_history": True,
                "context_summary": "User prefers complex world-building",
                "user_preferences": {"writing_style": "descriptive", "complexity": "high"}
            }
            mock_get_conv.return_value = mock_conv
            
            # Act
            message = await message_handler.prepare_message(request)
            
            # Assert
            # Should contain all components
            assert "Create an epic fantasy plot" in message
            assert "CONVERSATION HISTORY:" in message
            assert "User prefers complex world-building" in message
            assert "User Preferences:" in message
            assert "writing_style: descriptive" in message
            assert "SESSION CONTEXT:" in message
            assert "session_id: session-456" in message
            assert "user_id: user-123" in message
            assert "CONTEXT:" in message
            assert "GENRE: fantasy" in message
            assert "magic" in message
            assert "heroism" in message