"""
TDD Test Suite for BaseAgent class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- BaseAgent initialization
- Async message preparation with context
- Tool validation and execution
- Error handling and recovery
- Vertex AI integration
- Session management
- Memory and conversation continuity
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.base_agent import BaseAgent
from src.core.interfaces import AgentRequest, AgentResponse, ContentType
from src.core.configuration import Configuration


class TestBaseAgentInitialization:
    """Test BaseAgent initialization and configuration"""
    
    def test_base_agent_initialization_with_basic_config(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test basic BaseAgent initialization
        Should initialize with name, description, instruction, and config
        """
        # Arrange
        name = "test_agent"
        description = "Test agent for unit testing"
        instruction = "You are a test agent"
        
        # Act
        agent = BaseAgent(name, description, instruction, mock_config)
        
        # Assert
        assert agent.name == name
        assert agent.description == description
        assert agent.instruction is not None  # May be enhanced with schema
        assert agent._config == mock_config
        assert agent._tools == []
        assert agent._sessions == {}
    
    def test_base_agent_initialization_with_tools(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test BaseAgent initialization with tools
        Should properly initialize with tools and not add JSON schema
        """
        # Arrange
        name = "plot_agent"
        description = "Plot generation agent"
        instruction = "Generate creative plots"
        tools = [MagicMock(name="save_plot"), MagicMock(name="get_plot")]
        
        # Act
        agent = BaseAgent(name, description, instruction, mock_config, tools=tools)
        
        # Assert
        assert agent.name == name
        assert agent._tools == tools
        assert len(agent._tools) == 2
        # Should use base instruction when tools are present
        assert "Generate creative plots" in agent.instruction
    
    def test_base_agent_dynamic_schema_generation(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test dynamic schema generation for agents without tools
        Should generate instruction with JSON schema for database operations
        """
        # Arrange
        name = "plot_generator"
        description = "Plot generation agent"
        instruction = "Generate plots"
        
        # Mock schema service to return schema
        with patch('src.core.schema_service.schema_service') as mock_schema:
            mock_schema.get_content_type_from_agent.return_value = "plot"
            mock_schema._get_fallback_json_schema.return_value = {
                "title": {"type": "string"},
                "genre": {"type": "string"}
            }
            mock_schema.generate_json_schema_instruction.return_value = "\\n\\nUse JSON format: {\"title\": \"...\", \"genre\": \"...\"}"
            
            # Act
            agent = BaseAgent(name, description, instruction, mock_config)
            
            # Assert
            assert agent.dynamic_schema is not None
            assert "title" in agent.dynamic_schema
            assert "genre" in agent.dynamic_schema
            assert "Use JSON format" in agent.instruction
    
    def test_base_agent_vertex_ai_integration(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test Vertex AI / Google ADK integration
        Should properly initialize ADK agent and runner
        """
        # Arrange
        name = "vertex_agent"
        description = "Vertex AI integrated agent"
        instruction = "Use Vertex AI"
        
        # Act
        agent = BaseAgent(name, description, instruction, mock_config)
        
        # Assert
        # Verify ADK Agent was created
        mock_vertex_ai['agent_class'].assert_called_once()
        call_args = mock_vertex_ai['agent_class'].call_args
        assert call_args[1]['name'] == name
        assert call_args[1]['model'] == mock_config.model_name
        assert call_args[1]['description'] == description
        
        # Verify runner was created
        assert agent._runner is not None
        assert agent._adk_factory is not None


class TestBaseAgentMessagePreparation:
    """Test async message preparation functionality"""
    
    @pytest.mark.asyncio
    async def test_prepare_message_basic(self, mock_config, mock_adk_services, mock_vertex_ai, basic_agent_request):
        """
        RED: Test basic message preparation
        Should handle basic AgentRequest and return prepared message
        """
        # Arrange
        agent = BaseAgent("test_agent", "Test", "Test instruction", mock_config)
        
        # Act
        message = await agent._prepare_message(basic_agent_request)
        
        # Assert
        assert basic_agent_request.content in message
        assert "Generate a fantasy plot" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_context(self, mock_config, mock_adk_services, mock_vertex_ai, complex_agent_request):
        """
        RED: Test message preparation with complex context
        Should include context information in prepared message
        """
        # Arrange
        agent = BaseAgent("context_agent", "Context Test", "Handle context", mock_config)
        
        # Act
        message = await agent._prepare_message(complex_agent_request)
        
        # Assert
        assert complex_agent_request.content in message
        assert "CONTEXT:" in message
        assert "GENRE_HIERARCHY" in message.upper()
        assert "Epic Fantasy" in message
        assert "dragons" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_tools_adds_session_context(self, mock_config, mock_adk_services, mock_vertex_ai, basic_agent_request):
        """
        RED: Test message preparation for agents with tools
        Should add session context for tool execution
        """
        # Arrange
        tools = [MagicMock(name="save_plot")]
        agent = BaseAgent("tool_agent", "Tool Test", "Use tools", mock_config, tools=tools)
        
        # Act
        message = await agent._prepare_message(basic_agent_request)
        
        # Assert
        assert "SESSION CONTEXT:" in message
        assert f"session_id: {basic_agent_request.session_id}" in message
        assert f"user_id: {basic_agent_request.user_id}" in message
    
    @pytest.mark.asyncio
    async def test_prepare_message_with_conversation_history(self, mock_config, mock_adk_services, mock_vertex_ai, basic_agent_request):
        """
        RED: Test message preparation with conversation history
        Should include conversation context when available
        """
        # Arrange
        agent = BaseAgent("conv_agent", "Conversation Test", "Remember context", mock_config)
        
        # Mock conversation manager to return history
        mock_adk_services['conversation_manager'].get_conversation_context.return_value = {
            "has_conversation_history": True,
            "context_summary": "Previously discussed fantasy themes",
            "user_preferences": {"genre": "fantasy", "style": "epic"}
        }
        
        # Act
        message = await agent._prepare_message(basic_agent_request)
        
        # Assert
        assert "CONVERSATION HISTORY:" in message
        assert "Previously discussed fantasy themes" in message
        assert "User Preferences:" in message
        assert "genre: fantasy" in message


class TestBaseAgentToolValidation:
    """Test tool validation and execution"""
    
    def test_is_valid_tool_call_with_valid_tools(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test tool call validation with valid tool names
        Should return True for legitimate tool calls
        """
        # Arrange
        agent = BaseAgent("tool_agent", "Tool Test", "Use tools", mock_config)
        
        # Act & Assert
        assert agent._is_valid_tool_call("save_plot") is True
        assert agent._is_valid_tool_call("save_author") is True
        assert agent._is_valid_tool_call("get_plot") is True
        assert agent._is_valid_tool_call("invoke_agent") is True
        assert agent._is_valid_tool_call("search_content") is True
    
    def test_is_valid_tool_call_with_invalid_patterns(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test tool call validation with malformed patterns
        Should return False for malformed instruction text mistaken as tool calls
        """
        # Arrange
        agent = BaseAgent("validation_agent", "Validation Test", "Validate tools", mock_config)
        
        # Act & Assert - Common malformed patterns
        assert agent._is_valid_tool_call("print") is False
        assert agent._is_valid_tool_call("console.log") is False
        assert agent._is_valid_tool_call("str(uuid.uuid4())") is False
        assert agent._is_valid_tool_call("import uuid") is False
        assert agent._is_valid_tool_call("def function") is False
    
    def test_is_valid_tool_call_with_multiline_code_blocks(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test tool call validation with multi-line code blocks
        Should reject multi-line instruction examples mistaken as function calls
        """
        # Arrange
        agent = BaseAgent("multiline_agent", "Multiline Test", "Handle multiline", mock_config)
        
        # Act & Assert
        multiline_code = "import uuid\\nworkflow_id = str(uuid.uuid4())\\nprint(f'Generated: {workflow_id}')"
        assert agent._is_valid_tool_call(multiline_code) is False
        
        workflow_example = "workflow_id = str(uuid.uuid4())\\nprint(workflow_id)"
        assert agent._is_valid_tool_call(workflow_example) is False
    
    def test_is_valid_tool_call_logs_unknown_tools(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test that unknown tool calls are logged but allowed
        Should log unknown tools for investigation but not reject them
        """
        # Arrange
        agent = BaseAgent("unknown_agent", "Unknown Test", "Handle unknown", mock_config)
        
        # Act & Assert
        with patch.object(agent._logger, 'info') as mock_log:
            result = agent._is_valid_tool_call("unknown_custom_tool")
            assert result is True
            mock_log.assert_called_once()
            assert "Unknown tool call detected" in mock_log.call_args[0][0]


class TestBaseAgentSessionManagement:
    """Test session creation and management"""
    
    @pytest.mark.asyncio
    async def test_ensure_session_creates_new_session(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test session creation for new users
        Should create new session when one doesn't exist
        """
        # Arrange
        agent = BaseAgent("session_agent", "Session Test", "Manage sessions", mock_config)
        user_id = "new-user"
        session_id = "new-session"
        
        # Act
        await agent._ensure_session(user_id, session_id)
        
        # Assert
        assert session_id in agent._sessions
        mock_vertex_ai['session_service'].create_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_session_handles_vertex_ai_session_id_restrictions(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test session creation with Vertex AI restrictions
        Should handle Vertex AI's auto-generated session IDs gracefully
        """
        # Arrange
        agent = BaseAgent("vertex_session_agent", "Vertex Session Test", "Handle Vertex sessions", mock_config)
        user_id = "vertex-user"
        session_id = "custom-session"
        
        # Mock Vertex AI error for custom session IDs
        mock_vertex_ai['session_service'].create_session.side_effect = [
            Exception("User-provided Session id is not supported"),
            mock_vertex_ai['session']  # Second call succeeds
        ]
        
        # Act
        await agent._ensure_session(user_id, session_id)
        
        # Assert
        assert session_id in agent._sessions
        assert mock_vertex_ai['session_service'].create_session.call_count == 2
    
    @pytest.mark.asyncio
    async def test_ensure_session_reuses_existing_session(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test session reuse for existing sessions
        Should not create new session if one already exists
        """
        # Arrange
        agent = BaseAgent("reuse_agent", "Reuse Test", "Reuse sessions", mock_config)
        user_id = "existing-user"
        session_id = "existing-session"
        
        # Pre-populate session
        agent._sessions[session_id] = mock_vertex_ai['session']
        
        # Act
        await agent._ensure_session(user_id, session_id)
        
        # Assert
        mock_vertex_ai['session_service'].create_session.assert_not_called()


class TestBaseAgentErrorHandling:
    """Test error handling and recovery mechanisms"""
    
    @pytest.mark.asyncio
    async def test_process_request_handles_validation_errors(self, mock_config, mock_adk_services, mock_vertex_ai, mock_container):
        """
        RED: Test request processing with validation errors
        Should return error response for invalid requests
        """
        # Arrange
        agent = BaseAgent("error_agent", "Error Test", "Handle errors", mock_config)
        
        # Create invalid request (missing required fields)
        invalid_request = AgentRequest(
            content="",  # Empty content should cause validation error
            user_id="",  # Empty user_id should cause validation error
            session_id="test-session"
        )
        
        # Act
        with patch.object(agent, '_validate_request', side_effect=ValueError("Invalid request")):
            response = await agent.process_request(invalid_request)
        
        # Assert
        assert response.success is False
        assert "Invalid request" in response.error
        assert response.agent_name == "error_agent"
    
    @pytest.mark.asyncio
    async def test_process_request_handles_vertex_ai_errors(self, mock_config, mock_adk_services, mock_vertex_ai, mock_container, basic_agent_request):
        """
        RED: Test request processing with Vertex AI errors
        Should gracefully handle ADK/Vertex AI communication errors
        """
        # Arrange
        agent = BaseAgent("vertex_error_agent", "Vertex Error Test", "Handle Vertex errors", mock_config)
        
        # Mock Vertex AI failure
        async def failing_run_async(*args, **kwargs):
            raise Exception("Vertex AI connection failed")
        
        mock_vertex_ai['runner'].run_async = failing_run_async
        
        # Act
        response = await agent.process_request(basic_agent_request)
        
        # Assert
        assert response.success is False
        assert "Error generating response" in response.content
        assert response.agent_name == "vertex_error_agent"
    
    @pytest.mark.asyncio
    async def test_process_request_handles_serialization_errors(self, mock_config, mock_adk_services, mock_vertex_ai, mock_container, basic_agent_request):
        """
        RED: Test request processing with serialization errors
        Should handle ADK serialization issues and preserve content
        """
        # Arrange
        agent = BaseAgent("serialization_agent", "Serialization Test", "Handle serialization", mock_config)
        
        # Mock serialization error in ADK
        async def serialization_error_run_async(*args, **kwargs):
            # Yield content first, then raise serialization error
            yield MagicMock(content="Response content")
            raise Exception("Unable to serialize response")
        
        mock_vertex_ai['runner'].run_async = serialization_error_run_async
        
        # Act
        response = await agent.process_request(basic_agent_request)
        
        # Assert
        assert response.success is True  # Should still succeed
        assert "Response content" in response.content
        assert response.agent_name == "serialization_agent"


class TestBaseAgentResponseParsing:
    """Test response parsing and JSON extraction"""
    
    def test_parse_response_with_valid_json(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test response parsing with valid JSON content
        Should extract JSON from agent response
        """
        # Arrange
        agent = BaseAgent("json_agent", "JSON Test", "Parse JSON", mock_config)
        
        # Mock JSON parser
        with patch('src.utils.json_parser.parse_llm_json') as mock_parser:
            expected_json = {"title": "Test Plot", "genre": "Fantasy"}
            mock_parser.return_value = expected_json
            
            # Act
            result = agent._parse_response("Some text with JSON: {\"title\": \"Test Plot\", \"genre\": \"Fantasy\"}")
            
            # Assert
            assert result == expected_json
            mock_parser.assert_called_once()
    
    def test_parse_response_with_no_json(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test response parsing with no JSON content
        Should return None when no JSON is found
        """
        # Arrange
        agent = BaseAgent("no_json_agent", "No JSON Test", "No JSON", mock_config)
        
        # Mock JSON parser to return None
        with patch('src.utils.json_parser.parse_llm_json') as mock_parser:
            mock_parser.return_value = None
            
            # Act
            result = agent._parse_response("Plain text response with no JSON")
            
            # Assert
            assert result is None
            mock_parser.assert_called_once()
    
    def test_get_content_type_default(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test default content type
        Should return PLOT as default content type
        """
        # Arrange
        agent = BaseAgent("content_type_agent", "Content Type Test", "Content type", mock_config)
        
        # Act
        content_type = agent._get_content_type()
        
        # Assert
        assert content_type == ContentType.PLOT


class TestBaseAgentToolCallCleaning:
    """Test tool call serialization and cleaning"""
    
    def test_clean_tool_calls_for_serialization_basic(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test basic tool call cleaning for serialization
        Should clean tool calls to be JSON serializable
        """
        # Arrange
        agent = BaseAgent("clean_agent", "Clean Test", "Clean tools", mock_config)
        
        tool_calls = [
            {
                "tool": "save_plot",
                "args": {"title": "Test", "genre": "Fantasy"},
                "result": {"success": True, "plot_id": "123"}
            }
        ]
        
        # Act
        cleaned = agent._clean_tool_calls_for_serialization(tool_calls)
        
        # Assert
        assert len(cleaned) == 1
        assert cleaned[0]["tool"] == "save_plot"
        assert cleaned[0]["args"]["title"] == "Test"
        assert cleaned[0]["result"]["success"] is True
    
    def test_clean_tool_calls_handles_non_serializable_objects(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test tool call cleaning with non-serializable objects
        Should convert non-serializable objects to safe representations
        """
        # Arrange
        agent = BaseAgent("non_serializable_agent", "Non-Serializable Test", "Handle non-serializable", mock_config)
        
        # Create non-serializable object
        class NonSerializable:
            def __str__(self):
                return "NonSerializable object"
        
        tool_calls = [
            {
                "tool": "complex_tool",
                "args": {"callback": NonSerializable()},
                "result": {"data": NonSerializable()}
            }
        ]
        
        # Act
        cleaned = agent._clean_tool_calls_for_serialization(tool_calls)
        
        # Assert
        assert len(cleaned) == 1
        assert cleaned[0]["tool"] == "complex_tool"
        # Non-serializable objects should be converted to safe representations
        assert isinstance(cleaned[0]["args"], dict)
        assert isinstance(cleaned[0]["result"], dict)
    
    def test_clean_tool_calls_handles_missing_fields(self, mock_config, mock_adk_services, mock_vertex_ai):
        """
        RED: Test tool call cleaning with missing required fields
        Should add missing required fields with defaults
        """
        # Arrange
        agent = BaseAgent("missing_fields_agent", "Missing Fields Test", "Handle missing fields", mock_config)
        
        tool_calls = [
            {"args": {"title": "Test"}},  # Missing tool name and result
            {"tool": "save_author"}       # Missing result
        ]
        
        # Act
        cleaned = agent._clean_tool_calls_for_serialization(tool_calls)
        
        # Assert
        assert len(cleaned) == 2
        
        # First tool call should get default tool name and result
        assert "tool" in cleaned[0] or "name" in cleaned[0]
        assert "result" in cleaned[0]
        assert cleaned[0]["result"]["success"] is True
        
        # Second tool call should get default result
        assert cleaned[1]["tool"] == "save_author"
        assert "result" in cleaned[1]
        assert cleaned[1]["result"]["success"] is True


class TestBaseAgentIntegration:
    """Integration tests for BaseAgent with all components"""
    
    @pytest.mark.asyncio
    async def test_full_request_processing_with_tools(self, mock_config, mock_adk_services, mock_vertex_ai, mock_container, basic_agent_request):
        """
        RED: Test complete request processing with tool execution
        Should handle full request lifecycle including tool calls
        """
        # Arrange
        tools = [MagicMock(name="save_plot")]
        agent = BaseAgent("integration_agent", "Integration Test", "Full integration", mock_config, tools=tools)
        
        # Mock tool execution in response
        async def mock_run_with_tools(*args, **kwargs):
            # Simulate tool call event
            tool_call_event = MagicMock()
            tool_call_event.function_call.name = "save_plot"
            tool_call_event.function_call.arguments = {"title": "Test Plot"}
            yield tool_call_event
            
            # Simulate content response
            content_event = MagicMock()
            content_event.content = "Successfully saved plot"
            yield content_event
        
        mock_vertex_ai['runner'].run_async = mock_run_with_tools
        
        # Act
        response = await agent.process_request(basic_agent_request)
        
        # Assert
        assert response.success is True
        assert response.agent_name == "integration_agent"
        assert response.content is not None
        assert "tool_calls" in response.metadata
    
    @pytest.mark.asyncio
    async def test_streaming_request_processing(self, mock_config, mock_adk_services, mock_vertex_ai, basic_agent_request):
        """
        RED: Test streaming request processing
        Should yield stream chunks and complete properly
        """
        # Arrange
        agent = BaseAgent("streaming_agent", "Streaming Test", "Stream responses", mock_config)
        
        # Mock streaming response
        async def mock_streaming_run(*args, **kwargs):
            yield MagicMock(content="First chunk")
            yield MagicMock(content="Second chunk")
            yield MagicMock(content="Final chunk")
        
        mock_vertex_ai['runner'].run_async = mock_streaming_run
        
        # Act
        chunks = []
        async for chunk in agent.process_request_streaming(basic_agent_request):
            chunks.append(chunk)
        
        # Assert
        assert len(chunks) >= 3  # At least content chunks
        assert chunks[-1].is_complete is True  # Final chunk should be marked complete
        assert all(chunk.agent_name == "streaming_agent" for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_memory_interaction_saving(self, mock_config, mock_adk_services, mock_vertex_ai, mock_container, basic_agent_request):
        """
        RED: Test saving interactions to memory
        Should save successful tool interactions to conversation memory
        """
        # Arrange
        tools = [MagicMock(name="save_plot")]
        agent = BaseAgent("memory_agent", "Memory Test", "Save to memory", mock_config, tools=tools)
        
        tool_calls = [
            {
                "tool": "save_plot",
                "result": {
                    "success": True,
                    "plot_id": {"title": "Test Plot", "id": "plot-123"}
                }
            }
        ]
        
        # Act
        await agent._save_interaction_to_memory(basic_agent_request, tool_calls, "Plot saved successfully")
        
        # Assert
        mock_adk_services['conversation_manager'].save_interaction_to_memory.assert_called_once()
        call_args = mock_adk_services['conversation_manager'].save_interaction_to_memory.call_args
        
        assert call_args[0][0] == basic_agent_request.session_id
        assert call_args[0][1] == basic_agent_request.user_id
        interaction_data = call_args[0][2]
        assert interaction_data["agent_name"] == "memory_agent"
        assert interaction_data["tool_calls_count"] == 1
        assert "plot" in interaction_data["generated_content"]