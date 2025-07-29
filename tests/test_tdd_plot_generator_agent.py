"""
TDD Tests for PlotGeneratorAgent

These tests follow strict RED → GREEN → REFACTOR methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve implementation while keeping tests green

Phase 2: Agent Core Logic - PlotGeneratorAgent with context handling and author_id integration
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

from src.agents.plot_generator import PlotGeneratorAgent
from src.core.interfaces import AgentRequest, AgentResponse, ContentType
from src.core.configuration import Configuration
from src.core.base_agent import BaseAgent
from src.tools.writing_tools import save_plot


class TestPlotGeneratorAgentTDD:
    """TDD tests for PlotGeneratorAgent - focus on context handling and author_id integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Configuration for testing"""
        config = Mock(spec=Configuration)
        config.model_name = "gemini-1.5-pro"
        config.vertex_ai_project_id = "test-project"
        config.vertex_ai_location = "us-central1"
        config.service_mode = "vertex_ai_managed"
        return config
    
    @pytest.fixture
    def mock_adk_components(self):
        """Mock Google ADK components"""
        with patch('src.core.agent_modules.AgentConfigManager') as mock_config_mgr, \
             patch('src.core.agent_modules.AgentMessageHandler') as mock_msg_handler, \
             patch('src.core.agent_modules.AgentResponseProcessor') as mock_resp_proc, \
             patch('src.core.agent_modules.AgentToolManager') as mock_tool_mgr, \
             patch('src.core.agent_modules.AgentErrorHandler') as mock_error_handler:
            
            # Mock the agent modules for the new architecture
            mock_config_manager = Mock()
            mock_config_manager.name = "plot_generator"
            mock_config_manager.description = "Test plot generator"
            mock_config_manager.instruction = "Test instruction"
            mock_config_manager.dynamic_schema = None
            mock_config_manager.config = Mock()
            mock_config_manager.tools = [save_plot]
            mock_config_manager.logger = Mock()
            mock_config_mgr.return_value = mock_config_manager
            
            mock_message_handler = AsyncMock()
            mock_msg_handler.return_value = mock_message_handler
            
            mock_response_processor = Mock()
            mock_resp_proc.return_value = mock_response_processor
            
            mock_tool_manager = Mock()
            mock_tool_mgr.return_value = mock_tool_manager
            
            mock_error_handler = Mock()
            mock_error_handler.return_value = mock_error_handler
            
            yield {
                'config_manager': mock_config_manager,
                'message_handler': mock_message_handler,
                'response_processor': mock_response_processor,
                'tool_manager': mock_tool_manager,
                'error_handler': mock_error_handler
            }
    
    @pytest.fixture
    def plot_generator_agent(self, mock_config, mock_adk_components):
        """Create PlotGeneratorAgent with mocked dependencies"""
        agent = PlotGeneratorAgent(mock_config)
        
        # Store mocks for access in tests
        agent._mock_config_manager = mock_adk_components['config_manager']
        agent._mock_message_handler = mock_adk_components['message_handler']
        
        return agent
    
    # RED TESTS: These should expose PlotGeneratorAgent requirements
    
    @pytest.mark.asyncio
    async def test_initialization_includes_save_plot_tool(self, plot_generator_agent):
        """
        RED TEST: PlotGeneratorAgent should initialize with save_plot tool
        REQUIREMENT: Agent must have tools available for saving plot data
        """
        # Then: Should have tools initialized
        assert hasattr(plot_generator_agent, '_tools')
        assert len(plot_generator_agent._tools) == 1
        
        # And: Should contain save_plot tool
        tool = plot_generator_agent._tools[0]
        assert tool == save_plot
        
        # And: Should have correct agent properties
        assert plot_generator_agent.name == "plot_generator"
        assert "story plots" in plot_generator_agent.description
        assert plot_generator_agent._get_content_type() == ContentType.PLOT
    
    @pytest.mark.asyncio
    async def test_instruction_emphasizes_tool_usage_over_text_responses(self, plot_generator_agent):
        """
        RED TEST: Agent instruction should emphasize using tools over lengthy text responses
        REQUIREMENT: Agent should use save_plot tool immediately, not provide long text responses
        """
        # Given: The agent instruction
        instruction = plot_generator_agent.instruction
        
        # Then: Should emphasize tool usage over text responses
        assert "Do not provide lengthy text responses" in instruction
        assert "use the save_plot tool" in instruction
        assert "save your generated plot directly to the database" in instruction
        
        # And: Should emphasize immediate tool usage
        assert "Use the save_plot tool immediately" in instruction
        assert "brief confirmation" in instruction
        
        # And: Should include tool parameters guidance
        assert "save_plot tool with these parameters" in instruction
        assert "session_id" in instruction
        assert "user_id" in instruction
        assert "author_id" in instruction
    
    @pytest.mark.asyncio
    async def test_instruction_specifies_plot_quality_requirements(self, plot_generator_agent):
        """
        RED TEST: Agent instruction should specify plot quality requirements
        REQUIREMENT: Plots should have specific quality characteristics
        """
        # Given: The agent instruction
        instruction = plot_generator_agent.instruction
        
        # Then: Should specify plot structure requirements
        assert "2-3 paragraph summary" in instruction
        assert "clear beginning, middle, end" in instruction
        assert "Compelling title" in instruction
        
        # And: Should specify genre and audience requirements
        assert "genre elements" in instruction
        assert "trope integration" in instruction
        assert "Age-appropriate content" in instruction
        assert "target demographic" in instruction
        
        # And: Should specify engagement requirements
        assert "Hooks and conflicts" in instruction
        assert "engaging" in instruction
    
    @pytest.mark.asyncio
    async def test_process_request_handles_author_id_context(self, plot_generator_agent):
        """
        RED TEST: process_request() should handle author_id from context for plot-author linking
        REQUIREMENT: Plot generation should link to existing authors when author_id is provided
        """
        # Given: A request with author_id in context
        request = AgentRequest(
            content="Create a fantasy plot about dragons and magic",
            user_id="test-user-123",
            session_id="test-session-456",
            context={
                "author_id": "author-uuid-789",
                "genre_context": "high fantasy with magical systems",
                "audience_context": "young adult readers"
            }
        )
        
        # Mock ADK runner to simulate tool call with author_id
        mock_events = []
        
        # Simulate function call event with author_id
        mock_function_call = Mock()
        mock_function_call.name = "save_plot"
        mock_function_call.arguments = {
            "title": "The Dragon's Awakening",
            "plot_summary": "A young mage discovers an ancient dragon that has been sleeping for centuries...",
            "session_id": "test-session-456",
            "user_id": "test-user-123",
            "author_id": "author-uuid-789",  # Should preserve author_id from context
            "genre": "high fantasy"
        }
        
        mock_function_event = Mock()
        mock_function_event.function_call = mock_function_call
        mock_events.append(mock_function_event)
        
        # Simulate text response event
        mock_text_event = Mock()
        mock_text_event.content = "I've created 'The Dragon's Awakening' fantasy plot linked to the specified author."
        mock_events.append(mock_text_event)
        
        async def mock_run_async(*args, **kwargs):
            for event in mock_events:
                yield event
        
        plot_generator_agent._mock_runner.run_async = mock_run_async
        
        # Mock session service and creation
        mock_session_service = AsyncMock()
        mock_session = Mock()
        mock_session.session_id = "test-session-456"
        mock_session_service.create_session.return_value = mock_session
        
        plot_generator_agent._mock_runner.session_service = mock_session_service
        plot_generator_agent._sessions = {"test-session-456": mock_session}
        
        # Mock container for session context setting
        with patch('src.core.container.get_container') as mock_get_container:
            mock_container = Mock()
            mock_get_container.return_value = mock_container
            
            # When: Processing the request
            response = await plot_generator_agent.process_request(request)
        
        # Then: Should return successful response
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert response.agent_name == "plot_generator"
        assert response.content_type == ContentType.PLOT
        
        # And: Should contain tool call information with author_id in metadata
        assert "tool_calls" in response.metadata
        tool_calls = response.metadata["tool_calls"]
        assert len(tool_calls) == 1
        assert tool_calls[0]["tool"] == "save_plot"
        
        # And: Should preserve author_id from context
        tool_args = tool_calls[0]["args"]
        assert tool_args["author_id"] == "author-uuid-789"
    
    @pytest.mark.asyncio
    async def test_validate_request_checks_plot_keywords(self, plot_generator_agent):
        """
        RED TEST: _validate_request() should check for plot-related content
        REQUIREMENT: Validate that requests are actually asking for plot generation
        """
        # Given: Request with plot keywords
        valid_request = AgentRequest(
            content="Create a story plot for science fiction",
            user_id="test-user",
            session_id="test-session"
        )
        
        # When/Then: Should not raise exception for valid request
        try:
            plot_generator_agent._validate_request(valid_request)
        except Exception as e:
            pytest.fail(f"Should not raise exception for valid request: {e}")
        
        # Given: Request without plot keywords
        invalid_request = AgentRequest(
            content="Create an author profile for mystery novels",
            user_id="test-user", 
            session_id="test-session"
        )
        
        # When: Validating invalid request (should log warning but not fail)
        try:
            plot_generator_agent._validate_request(invalid_request)
            # Should complete without exception but log warning
        except Exception as e:
            pytest.fail(f"Should not raise exception even for non-plot requests: {e}")
    
    @pytest.mark.asyncio
    async def test_prepare_message_adds_plot_context(self, plot_generator_agent):
        """
        RED TEST: _prepare_message() should add plot-specific context
        REQUIREMENT: Context should be properly formatted for plot generation
        """
        # Given: Request with rich context
        request = AgentRequest(
            content="Create a thriller plot",
            user_id="test-user",
            session_id="test-session",
            context={
                "author_id": "author-123",  # Should be included in context
                "genre_context": "Psychological thriller with unreliable narrator",
                "audience_context": "Adult readers who enjoy complex narratives",
                "plot_context": "Should include plot twists and red herrings"
            }
        )
        
        # Mock conversation manager
        plot_generator_agent._conversation_manager = AsyncMock()
        plot_generator_agent._conversation_manager.get_conversation_context.return_value = {
            "has_conversation_history": False
        }
        
        # When: Preparing the message
        message = await plot_generator_agent._prepare_message(request)
        
        # Then: Should include original content
        assert "Create a thriller plot" in message
        
        # And: Should include session context (because agent has tools)
        assert "SESSION CONTEXT:" in message
        assert "session_id: test-session" in message
        assert "user_id: test-user" in message
        
        # And: Should include plot generation focus
        assert "PLOT GENERATION FOCUS:" in message
        assert "Genre Context:" in message
        assert "Psychological thriller with unreliable narrator" in message
        assert "Audience Context:" in message
        assert "Adult readers who enjoy complex narratives" in message
        
        # And: Should emphasize authentic integration
        assert "incorporates these specifications authentically" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_handles_missing_context_gracefully(self, plot_generator_agent):
        """
        RED TEST: _prepare_message() should handle requests without context
        REQUIREMENT: Agent should work even when context is minimal
        """
        # Given: Request without context
        request = AgentRequest(
            content="Create a romance plot",
            user_id="test-user",
            session_id="test-session"
            # No context provided
        )
        
        # Mock conversation manager
        plot_generator_agent._conversation_manager = AsyncMock()
        plot_generator_agent._conversation_manager.get_conversation_context.return_value = {
            "has_conversation_history": False
        }
        
        # When: Preparing the message
        message = await plot_generator_agent._prepare_message(request)
        
        # Then: Should include basic content
        assert "Create a romance plot" in message
        
        # And: Should include session context
        assert "SESSION CONTEXT:" in message
        assert "session_id: test-session" in message
        
        # And: Should NOT include plot generation focus section (no context)
        assert "PLOT GENERATION FOCUS:" not in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_includes_author_id_in_context(self, plot_generator_agent):
        """
        RED TEST: _prepare_message() should include author_id in context when available
        REQUIREMENT: Author ID should be passed to enable plot-author linking
        """
        # Given: Request with author_id in context
        request = AgentRequest(
            content="Create a mystery plot",
            user_id="test-user",
            session_id="test-session",
            context={
                "author_id": "author-uuid-456",
                "genre_context": "Cozy mystery with amateur detective"
            }
        )
        
        # Mock conversation manager
        plot_generator_agent._conversation_manager = AsyncMock()
        plot_generator_agent._conversation_manager.get_conversation_context.return_value = {
            "has_conversation_history": False
        }
        
        # When: Preparing the message
        message = await plot_generator_agent._prepare_message(request)
        
        # Then: Should include author_id in context
        assert "CONTEXT:" in message
        assert "AUTHOR_ID: author-uuid-456" in message
        
        # And: Should include other context elements
        assert "GENRE_CONTEXT: Cozy mystery with amateur detective" in message
    
    @pytest.mark.asyncio
    async def test_agent_uses_tool_based_instruction_not_json_schema(self, plot_generator_agent):
        """
        RED TEST: Agent should use tool-based instruction, not JSON schema
        REQUIREMENT: With tools, agent should skip JSON schema generation
        """
        # Then: Should use base instruction (not enhanced with JSON schema)
        instruction = plot_generator_agent.instruction
        
        # And: Should contain tool-specific guidance
        assert "save_plot tool" in instruction
        assert "session_id" in instruction
        assert "user_id" in instruction
        assert "author_id" in instruction
        
        # And: Should NOT contain JSON schema artifacts
        assert "```json" not in instruction
        assert "JSON format" not in instruction
        assert "required fields" not in instruction.lower()
        
        # And: Dynamic schema should be None (tools take precedence)
        assert plot_generator_agent.dynamic_schema is None


class TestPlotGeneratorAgentToolIntegration:
    """Test actual tool integration and execution"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock Configuration for testing"""
        config = Mock(spec=Configuration)
        config.model_name = "gemini-1.5-pro"
        return config
    
    @pytest.fixture
    def mock_save_plot_tool(self):
        """Mock save_plot tool function"""
        with patch('src.agents.plot_generator.save_plot') as mock_save:
            async def mock_save_plot(**kwargs):
                return {
                    "success": True,
                    "plot_id": str(uuid.uuid4()),
                    "message": "Plot saved successfully",
                    "plot_data": {
                        "title": kwargs.get("title", "Test Plot"),
                        "plot_summary": kwargs.get("plot_summary", "Test summary"),
                        "author_id": kwargs.get("author_id")  # Preserve author_id
                    }
                }
            
            mock_save.side_effect = mock_save_plot
            yield mock_save
    
    @pytest.fixture
    def plot_agent_with_mocked_tools(self, mock_config, mock_save_plot_tool):
        """Create PlotGeneratorAgent with mocked tool"""
        with patch('src.core.base_agent.Agent'), \
             patch('src.core.base_agent.get_adk_service_factory'), \
             patch('src.core.base_agent.get_logger'), \
             patch('src.core.base_agent.schema_service'), \
             patch('src.core.base_agent.get_conversation_manager'), \
             patch('src.core.base_agent.initialize_observability'), \
             patch('src.core.base_agent.get_agent_tracker'):
            
            agent = PlotGeneratorAgent(mock_config)
            return agent
    
    @pytest.mark.asyncio
    async def test_execute_tool_calls_save_plot_with_author_id_context(self, plot_agent_with_mocked_tools, mock_save_plot_tool):
        """
        RED TEST: _execute_tool() should call save_plot with author_id from context
        REQUIREMENT: Tool execution must preserve author_id for plot-author linking
        """
        # Given: A tool call for save_plot with author_id
        mock_tool_call = Mock()
        mock_tool_call.name = "save_plot"
        mock_tool_call.args = {
            "title": "The Mystery of Willowbrook",
            "plot_summary": "A small town mystery involving missing heirlooms and family secrets.",
            "author_id": "author-linked-uuid"  # Author ID should be preserved
        }
        
        request = AgentRequest(
            content="Create plot",
            user_id="test-user-789",
            session_id="test-session-012"
        )
        
        # When: Executing the tool
        result = await plot_agent_with_mocked_tools._execute_tool(mock_tool_call, request)
        
        # Then: Should call save_plot with author_id preserved
        mock_save_plot_tool.assert_called_once_with(
            title="The Mystery of Willowbrook",
            plot_summary="A small town mystery involving missing heirlooms and family secrets.",
            author_id="author-linked-uuid",  # Should preserve author_id
            session_id="test-session-012",
            user_id="test-user-789"
        )
        
        # And: Should return successful result with author_id preserved
        assert result["success"] is True
        assert "plot_id" in result
        assert result["plot_data"]["author_id"] == "author-linked-uuid"
    
    @pytest.mark.asyncio
    async def test_execute_tool_handles_plot_without_author_id(self, plot_agent_with_mocked_tools, mock_save_plot_tool):
        """
        RED TEST: _execute_tool() should handle plots without author_id gracefully
        REQUIREMENT: Plots can be created independently without requiring author linkage
        """
        # Given: A tool call for save_plot without author_id
        mock_tool_call = Mock()
        mock_tool_call.name = "save_plot"
        mock_tool_call.args = {
            "title": "Standalone Adventure",
            "plot_summary": "An epic adventure that stands on its own.",
            "genre": "adventure"
        }
        
        request = AgentRequest(
            content="Create plot",
            user_id="test-user-456",
            session_id="test-session-789"
        )
        
        # When: Executing the tool
        result = await plot_agent_with_mocked_tools._execute_tool(mock_tool_call, request)
        
        # Then: Should call save_plot without author_id
        mock_save_plot_tool.assert_called_once_with(
            title="Standalone Adventure",
            plot_summary="An epic adventure that stands on its own.",
            genre="adventure",
            session_id="test-session-789",
            user_id="test-user-456"
        )
        
        # And: Should return successful result
        assert result["success"] is True
        assert "plot_id" in result
        assert result["plot_data"]["author_id"] is None  # No author_id
    
    @pytest.mark.asyncio
    async def test_execute_tool_handles_tool_errors(self, plot_agent_with_mocked_tools):
        """
        RED TEST: _execute_tool() should handle tool execution errors
        REQUIREMENT: Tool errors should be caught and returned as error results
        """
        # Given: save_plot tool that raises exception
        with patch('src.agents.plot_generator.save_plot') as mock_save:
            mock_save.side_effect = Exception("Database connection failed")
            
            mock_tool_call = Mock()
            mock_tool_call.name = "save_plot"
            mock_tool_call.args = {"title": "Test Plot", "plot_summary": "Test summary"}
            
            request = AgentRequest(
                content="Create plot",
                user_id="test-user",
                session_id="test-session"
            )
            
            # When: Executing the tool
            result = await plot_agent_with_mocked_tools._execute_tool(mock_tool_call, request)
            
            # Then: Should return error result
            assert result["success"] is False
            assert "Database connection failed" in result["error"]
            assert result["message"] == "Failed to execute tool save_plot"


class TestPlotGeneratorAgentErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Configuration)
        config.model_name = "gemini-1.5-pro"
        return config
    
    @pytest.fixture 
    def error_agent(self, mock_config):
        """Create agent with error-prone mocks"""
        with patch('src.core.base_agent.Agent') as mock_agent_class, \
             patch('src.core.base_agent.get_adk_service_factory') as mock_factory, \
             patch('src.core.base_agent.get_logger'), \
             patch('src.core.base_agent.schema_service'), \
             patch('src.core.base_agent.get_conversation_manager'), \
             patch('src.core.base_agent.initialize_observability'), \
             patch('src.core.base_agent.get_agent_tracker'):
            
            # Mock runner that raises errors
            mock_runner = Mock()
            async def error_run_async(*args, **kwargs):
                raise Exception("ADK execution failed")
            mock_runner.run_async = error_run_async
            
            mock_adk_factory = Mock()
            mock_adk_factory.create_runner.return_value = mock_runner
            mock_adk_factory.service_mode.value = "vertex_ai_managed"
            mock_factory.return_value = mock_adk_factory
            
            agent = PlotGeneratorAgent(mock_config)
            return agent
    
    @pytest.mark.asyncio
    async def test_process_request_handles_adk_errors_gracefully(self, error_agent):
        """
        RED TEST: process_request() should handle ADK execution errors gracefully  
        REQUIREMENT: Agent errors should not crash the system
        """
        # Given: Request that will cause ADK error
        request = AgentRequest(
            content="Create plot",
            user_id="test-user",
            session_id="test-session"
        )
        
        # When: Processing request with error
        response = await error_agent.process_request(request)
        
        # Then: Should return error response instead of crashing
        assert isinstance(response, AgentResponse)
        assert response.success is False
        assert response.agent_name == "plot_generator"
        assert "ADK execution failed" in response.error
        
        # And: Content should be empty on error
        assert response.content == ""
    
    @pytest.mark.asyncio
    async def test_agent_handles_missing_required_fields_in_request(self, mock_config):
        """
        RED TEST: Agent should validate required fields in requests
        REQUIREMENT: Missing user_id or session_id should cause validation error
        """
        with patch('src.core.base_agent.Agent'), \
             patch('src.core.base_agent.get_adk_service_factory'), \
             patch('src.core.base_agent.get_logger'), \
             patch('src.core.base_agent.schema_service'), \
             patch('src.core.base_agent.get_conversation_manager'), \
             patch('src.core.base_agent.initialize_observability'), \
             patch('src.core.base_agent.get_agent_tracker'):
            
            agent = PlotGeneratorAgent(mock_config)
            
            # Given: Request missing user_id
            invalid_request = AgentRequest(
                content="Create plot",
                user_id="",  # Empty user_id
                session_id="test-session"
            )
            
            # When/Then: Should raise validation error
            with pytest.raises(ValueError, match="User ID is required"):
                await agent.process_request(invalid_request)


if __name__ == "__main__":
    print("🔴 Running PlotGeneratorAgent TDD tests - these will verify context handling and author linking!")
    print("These tests will check tool integration, author_id preservation, and context processing.")
    pytest.main([__file__, "-v", "-s"])