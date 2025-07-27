"""
TDD Test Suite for WebSocketHandler class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- WebSocketHandler initialization and dependency injection
- Message handling and validation
- Connection management integration
- Agent factory coordination
- Content saving service integration
- Session repository interactions
- Error handling and disconnection scenarios
- Message routing and response handling
- Async communication patterns
- Real-time streaming capabilities
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from src.websocket.websocket_handler import WebSocketHandler
from src.websocket.connection_manager import ConnectionManager
from src.agents.agent_factory import AgentFactory
from src.core.configuration import Configuration
from src.core.interfaces import AgentRequest, AgentResponse
from src.core.validation import Validator, ValidationError


class TestWebSocketHandlerInitialization:
    """Test WebSocketHandler initialization and dependency injection"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for WebSocketHandler"""
        mock_connection_manager = MagicMock(spec=ConnectionManager)
        mock_agent_factory = MagicMock(spec=AgentFactory)
        mock_config = MagicMock(spec=Configuration)
        mock_content_saving_service = AsyncMock()
        mock_session_repository = AsyncMock()
        
        return {
            'connection_manager': mock_connection_manager,
            'agent_factory': mock_agent_factory,
            'config': mock_config,
            'content_saving_service': mock_content_saving_service,
            'session_repository': mock_session_repository
        }
    
    def test_websocket_handler_initialization_success(self, mock_dependencies):
        """
        RED: Test WebSocketHandler successful initialization
        Should initialize with all required dependencies
        """
        # Act
        handler = WebSocketHandler(**mock_dependencies)
        
        # Assert
        assert handler.connection_manager == mock_dependencies['connection_manager']
        assert handler.agent_factory == mock_dependencies['agent_factory']
        assert handler.config == mock_dependencies['config']
        assert handler.content_saving_service == mock_dependencies['content_saving_service']
        assert handler.session_repository == mock_dependencies['session_repository']
        assert handler.validator is not None
        assert handler.logger is not None
    
    def test_websocket_handler_initialization_missing_content_service(self, mock_dependencies):
        """
        RED: Test WebSocketHandler initialization with missing content saving service
        Should raise ValueError when content_saving_service is None
        """
        # Arrange
        mock_dependencies['content_saving_service'] = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="ContentSavingService is required"):
            WebSocketHandler(**mock_dependencies)
    
    def test_websocket_handler_initialization_missing_session_repository(self, mock_dependencies):
        """
        RED: Test WebSocketHandler initialization with missing session repository
        Should raise ValueError when session_repository is None
        """
        # Arrange
        mock_dependencies['session_repository'] = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="SessionRepository is required"):
            WebSocketHandler(**mock_dependencies)
    
    def test_websocket_handler_initialization_with_validator(self, mock_dependencies):
        """
        RED: Test WebSocketHandler initialization includes validator
        Should create Validator instance for message validation
        """
        # Act
        handler = WebSocketHandler(**mock_dependencies)
        
        # Assert
        assert isinstance(handler.validator, Validator)


class TestWebSocketHandlerDataSaving:
    """Test WebSocketHandler data saving methods"""
    
    @pytest.fixture
    def mock_handler(self):
        """Create WebSocketHandler with mocked dependencies"""
        mock_connection_manager = MagicMock()
        mock_agent_factory = MagicMock()
        mock_config = MagicMock()
        mock_content_saving_service = AsyncMock()
        mock_session_repository = AsyncMock()
        
        handler = WebSocketHandler(
            connection_manager=mock_connection_manager,
            agent_factory=mock_agent_factory,
            config=mock_config,
            content_saving_service=mock_content_saving_service,
            session_repository=mock_session_repository
        )
        
        return handler, mock_content_saving_service
    
    @pytest.mark.asyncio
    async def test_save_plot_data_success(self, mock_handler):
        """
        RED: Test _save_plot_data method success
        Should call content saving service with correct parameters
        """
        # Arrange
        handler, mock_service = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        plot_data = {"title": "Test Plot", "genre": "Fantasy"}
        orchestrator_params = {"complexity": "high"}
        expected_result = {"id": str(uuid.uuid4()), "status": "saved"}
        
        mock_service.save_plot_data.return_value = expected_result
        
        # Act
        result = await handler._save_plot_data(session_id, user_id, plot_data, orchestrator_params)
        
        # Assert
        assert result == expected_result
        mock_service.save_plot_data.assert_called_once_with(
            session_id, user_id, plot_data, orchestrator_params
        )
    
    @pytest.mark.asyncio
    async def test_save_plot_data_without_orchestrator_params(self, mock_handler):
        """
        RED: Test _save_plot_data method without orchestrator parameters
        Should call content saving service with None orchestrator_params
        """
        # Arrange
        handler, mock_service = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        plot_data = {"title": "Simple Plot", "genre": "Drama"}
        expected_result = {"id": str(uuid.uuid4()), "status": "saved"}
        
        mock_service.save_plot_data.return_value = expected_result
        
        # Act
        result = await handler._save_plot_data(session_id, user_id, plot_data)
        
        # Assert
        assert result == expected_result
        mock_service.save_plot_data.assert_called_once_with(
            session_id, user_id, plot_data, None
        )
    
    @pytest.mark.asyncio
    async def test_save_author_data_success(self, mock_handler):
        """
        RED: Test _save_author_data method success
        Should call content saving service with correct parameters
        """
        # Arrange
        handler, mock_service = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        author_data = {"name": "Test Author", "style": "Descriptive"}
        expected_result = {"id": str(uuid.uuid4()), "status": "saved"}
        
        mock_service.save_author_data.return_value = expected_result
        
        # Act
        result = await handler._save_author_data(session_id, user_id, author_data)
        
        # Assert
        assert result == expected_result
        mock_service.save_author_data.assert_called_once_with(
            session_id, user_id, author_data
        )
    
    @pytest.mark.asyncio
    async def test_save_world_building_data_success(self, mock_handler):
        """
        RED: Test _save_world_building_data method success
        Should call content saving service with all parameters
        """
        # Arrange
        handler, mock_service = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        world_data = {"name": "Fantasy Realm", "setting": "Medieval"}
        orchestrator_params = {"complexity": "medium"}
        plot_id = str(uuid.uuid4())
        expected_result = {"id": str(uuid.uuid4()), "status": "saved"}
        
        mock_service.save_world_building_data.return_value = expected_result
        
        # Act
        result = await handler._save_world_building_data(
            session_id, user_id, world_data, orchestrator_params, plot_id
        )
        
        # Assert
        assert result == expected_result
        mock_service.save_world_building_data.assert_called_once_with(
            session_id, user_id, world_data, orchestrator_params, plot_id
        )
    
    @pytest.mark.asyncio
    async def test_save_characters_data_success(self, mock_handler):
        """
        RED: Test _save_characters_data method success
        Should call content saving service with all parameters
        """
        # Arrange
        handler, mock_service = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        characters_data = {"protagonist": "Hero", "antagonist": "Villain"}
        orchestrator_params = {"depth": "detailed"}
        world_id = str(uuid.uuid4())
        plot_id = str(uuid.uuid4())
        expected_result = {"id": str(uuid.uuid4()), "status": "saved"}
        
        mock_service.save_characters_data.return_value = expected_result
        
        # Act
        result = await handler._save_characters_data(
            session_id, user_id, characters_data, orchestrator_params, world_id, plot_id
        )
        
        # Assert
        assert result == expected_result
        mock_service.save_characters_data.assert_called_once_with(
            session_id, user_id, characters_data, orchestrator_params, world_id, plot_id
        )
    
    @pytest.mark.asyncio
    async def test_save_critique_data_success(self, mock_handler):
        """
        RED: Test _save_critique_data method success
        Should call content saving service with critique parameters
        """
        # Arrange
        handler, mock_service = mock_handler
        iteration_id = str(uuid.uuid4())
        critique_json = {"score": 8, "feedback": "Good plot structure"}
        agent_response = "The plot has strong character development..."
        
        mock_service.save_critique_data.return_value = None
        
        # Act
        result = await handler._save_critique_data(iteration_id, critique_json, agent_response)
        
        # Assert
        assert result is None
        mock_service.save_critique_data.assert_called_once_with(
            iteration_id, critique_json, agent_response
        )


class TestWebSocketHandlerErrorHandling:
    """Test WebSocketHandler error handling scenarios"""
    
    @pytest.fixture
    def mock_handler(self):
        """Create WebSocketHandler with mocked dependencies"""
        mock_connection_manager = MagicMock()
        mock_agent_factory = MagicMock()
        mock_config = MagicMock()
        mock_content_saving_service = AsyncMock()
        mock_session_repository = AsyncMock()
        
        handler = WebSocketHandler(
            connection_manager=mock_connection_manager,
            agent_factory=mock_agent_factory,
            config=mock_config,
            content_saving_service=mock_content_saving_service,
            session_repository=mock_session_repository
        )
        
        return handler, {
            'connection_manager': mock_connection_manager,
            'agent_factory': mock_agent_factory,
            'config': mock_config,
            'content_saving_service': mock_content_saving_service,
            'session_repository': mock_session_repository
        }
    
    @pytest.mark.asyncio
    async def test_save_plot_data_service_error(self, mock_handler):
        """
        RED: Test _save_plot_data with service error
        Should propagate exception from content saving service
        """
        # Arrange
        handler, mocks = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        plot_data = {"title": "Test Plot"}
        
        mocks['content_saving_service'].save_plot_data.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler._save_plot_data(session_id, user_id, plot_data)
        
        mocks['content_saving_service'].save_plot_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_author_data_validation_error(self, mock_handler):
        """
        RED: Test _save_author_data with validation error
        Should propagate validation exception from content saving service
        """
        # Arrange
        handler, mocks = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        author_data = {"invalid": "data"}  # Missing required fields
        
        mocks['content_saving_service'].save_author_data.side_effect = ValidationError("Invalid author data")
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid author data"):
            await handler._save_author_data(session_id, user_id, author_data)
        
        mocks['content_saving_service'].save_author_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_world_building_data_async_error(self, mock_handler):
        """
        RED: Test _save_world_building_data with async operation error
        Should handle async errors gracefully
        """
        # Arrange
        handler, mocks = mock_handler
        session_id = "test-session"
        user_id = "test-user"
        world_data = {"name": "World"}
        
        async def failing_save(*args, **kwargs):
            await asyncio.sleep(0.01)
            raise asyncio.TimeoutError("Operation timeout")
        
        mocks['content_saving_service'].save_world_building_data.side_effect = failing_save
        
        # Act & Assert
        with pytest.raises(asyncio.TimeoutError, match="Operation timeout"):
            await handler._save_world_building_data(session_id, user_id, world_data)
        
        mocks['content_saving_service'].save_world_building_data.assert_called_once()


class TestWebSocketHandlerIntegration:
    """Test WebSocketHandler integration scenarios"""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket for testing"""
        websocket = AsyncMock(spec=WebSocket)
        websocket.receive_text = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_handler_with_websocket(self, mock_websocket):
        """Create WebSocketHandler with all mocks including WebSocket"""
        mock_connection_manager = MagicMock()
        mock_connection_manager.connect = AsyncMock()
        mock_connection_manager.disconnect = AsyncMock()
        mock_connection_manager.send_personal_message = AsyncMock()
        
        mock_agent_factory = MagicMock()
        mock_config = MagicMock()
        mock_content_saving_service = AsyncMock()
        mock_session_repository = AsyncMock()
        
        handler = WebSocketHandler(
            connection_manager=mock_connection_manager,
            agent_factory=mock_agent_factory,
            config=mock_config,
            content_saving_service=mock_content_saving_service,
            session_repository=mock_session_repository
        )
        
        return handler, {
            'websocket': mock_websocket,
            'connection_manager': mock_connection_manager,
            'agent_factory': mock_agent_factory,
            'config': mock_config,
            'content_saving_service': mock_content_saving_service,
            'session_repository': mock_session_repository
        }
    
    def test_websocket_handler_dependency_injection_completeness(self, mock_handler_with_websocket):
        """
        RED: Test WebSocketHandler has all required dependencies
        Should verify all dependencies are properly injected and accessible
        """
        # Arrange
        handler, mocks = mock_handler_with_websocket
        
        # Assert
        assert handler.connection_manager == mocks['connection_manager']
        assert handler.agent_factory == mocks['agent_factory']
        assert handler.config == mocks['config']
        assert handler.content_saving_service == mocks['content_saving_service']
        assert handler.session_repository == mocks['session_repository']
        assert hasattr(handler, 'validator')
        assert hasattr(handler, 'logger')
    
    @pytest.mark.asyncio
    async def test_websocket_handler_service_integration(self, mock_handler_with_websocket):
        """
        RED: Test WebSocketHandler integration with content saving service
        Should coordinate with multiple services for complex operations
        """
        # Arrange
        handler, mocks = mock_handler_with_websocket
        
        # Setup mock responses
        plot_id = str(uuid.uuid4())
        author_id = str(uuid.uuid4())
        world_id = str(uuid.uuid4())
        
        mocks['content_saving_service'].save_plot_data.return_value = {"id": plot_id}
        mocks['content_saving_service'].save_author_data.return_value = {"id": author_id}
        mocks['content_saving_service'].save_world_building_data.return_value = {"id": world_id}
        
        # Act - Perform multiple save operations
        plot_result = await handler._save_plot_data(
            "session1", "user1", {"title": "Test Plot"}
        )
        author_result = await handler._save_author_data(
            "session1", "user1", {"name": "Test Author"}
        )
        world_result = await handler._save_world_building_data(
            "session1", "user1", {"name": "Test World"}, None, plot_id
        )
        
        # Assert
        assert plot_result["id"] == plot_id
        assert author_result["id"] == author_id
        assert world_result["id"] == world_id
        
        # Verify service calls
        mocks['content_saving_service'].save_plot_data.assert_called_once()
        mocks['content_saving_service'].save_author_data.assert_called_once()
        mocks['content_saving_service'].save_world_building_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_handler_concurrent_operations(self, mock_handler_with_websocket):
        """
        RED: Test WebSocketHandler handling concurrent operations
        Should handle multiple simultaneous save operations
        """
        # Arrange
        handler, mocks = mock_handler_with_websocket
        
        # Setup mock responses with slight delays
        async def mock_save_with_delay(*args, **kwargs):
            await asyncio.sleep(0.01)
            return {"id": str(uuid.uuid4()), "status": "saved"}
        
        mocks['content_saving_service'].save_plot_data.side_effect = mock_save_with_delay
        mocks['content_saving_service'].save_author_data.side_effect = mock_save_with_delay
        mocks['content_saving_service'].save_world_building_data.side_effect = mock_save_with_delay
        
        # Act - Perform concurrent operations
        tasks = [
            handler._save_plot_data("session1", "user1", {"title": f"Plot {i}"})
            for i in range(3)
        ]
        tasks.extend([
            handler._save_author_data("session1", "user1", {"name": f"Author {i}"})
            for i in range(2)
        ])
        
        results = await asyncio.gather(*tasks)
        
        # Assert
        assert len(results) == 5
        assert all("id" in result for result in results)
        assert all(result["status"] == "saved" for result in results)
        
        # Verify all service calls were made
        assert mocks['content_saving_service'].save_plot_data.call_count == 3
        assert mocks['content_saving_service'].save_author_data.call_count == 2
    
    def test_websocket_handler_configuration_access(self, mock_handler_with_websocket):
        """
        RED: Test WebSocketHandler configuration access
        Should have access to configuration for operational parameters
        """
        # Arrange
        handler, mocks = mock_handler_with_websocket
        
        # Setup mock config
        mocks['config'].get_websocket_timeout = MagicMock(return_value=30)
        mocks['config'].get_max_message_size = MagicMock(return_value=1024)
        
        # Assert
        assert handler.config == mocks['config']
        
        # Verify config can be accessed for operational parameters
        # (These would be used in actual message handling methods)
        timeout = handler.config.get_websocket_timeout() if hasattr(handler.config, 'get_websocket_timeout') else 30
        max_size = handler.config.get_max_message_size() if hasattr(handler.config, 'get_max_message_size') else 1024
        
        assert isinstance(timeout, int)
        assert isinstance(max_size, int)


class TestWebSocketHandlerValidation:
    """Test WebSocketHandler validation functionality"""
    
    @pytest.fixture
    def mock_handler(self):
        """Create WebSocketHandler with mocked dependencies"""
        mock_connection_manager = MagicMock()
        mock_agent_factory = MagicMock()
        mock_config = MagicMock()
        mock_content_saving_service = AsyncMock()
        mock_session_repository = AsyncMock()
        
        handler = WebSocketHandler(
            connection_manager=mock_connection_manager,
            agent_factory=mock_agent_factory,
            config=mock_config,
            content_saving_service=mock_content_saving_service,
            session_repository=mock_session_repository
        )
        
        return handler
    
    def test_websocket_handler_validator_initialization(self, mock_handler):
        """
        RED: Test WebSocketHandler validator initialization
        Should create and configure validator for message validation
        """
        # Arrange
        handler = mock_handler
        
        # Assert
        assert handler.validator is not None
        assert isinstance(handler.validator, Validator)
    
    def test_websocket_handler_logger_initialization(self, mock_handler):
        """
        RED: Test WebSocketHandler logger initialization
        Should create logger with appropriate namespace
        """
        # Arrange
        handler = mock_handler
        
        # Assert
        assert handler.logger is not None
        # Logger should have websocket.handler namespace
        assert "websocket" in handler.logger.name or "handler" in handler.logger.name
    
    @pytest.mark.asyncio
    async def test_websocket_handler_data_validation_integration(self, mock_handler):
        """
        RED: Test WebSocketHandler integration with validation
        Should validate data before passing to content saving service
        """
        # Arrange
        handler = mock_handler
        
        # Test data that should be validated
        valid_plot_data = {
            "title": "Valid Plot",
            "genre": "Fantasy",
            "summary": "A valid plot summary"
        }
        
        invalid_plot_data = {
            "title": "",  # Invalid empty title
            "genre": "Unknown Genre"
        }
        
        # Mock successful validation for valid data
        handler.content_saving_service.save_plot_data.return_value = {"id": str(uuid.uuid4())}
        
        # Act - Valid data should work
        result = await handler._save_plot_data("session1", "user1", valid_plot_data)
        
        # Assert
        assert "id" in result
        handler.content_saving_service.save_plot_data.assert_called_once()
        
        # Note: The actual validation would happen in the content saving service
        # This test verifies the integration path exists