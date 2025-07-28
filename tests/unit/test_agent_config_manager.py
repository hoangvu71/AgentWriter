"""
TDD Test Suite for AgentConfigManager class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- Agent configuration and initialization
- Dynamic schema generation
- ADK agent and runner setup
- Tool configuration
- Observability and tracking initialization
"""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock Google ADK dependencies before importing
mock_google_adk = MagicMock()
mock_google_adk.agents = MagicMock()
mock_google_adk.agents.Agent = MagicMock()
mock_google_adk.runners = MagicMock()
mock_google_adk.runners.InMemoryRunner = MagicMock()

sys.modules['google.adk'] = mock_google_adk
sys.modules['google.adk.agents'] = mock_google_adk.agents
sys.modules['google.adk.runners'] = mock_google_adk.runners

from src.core.agent_modules.agent_config_manager import AgentConfigManager
from src.core.configuration import Configuration


class TestAgentConfigManagerInitialization:
    """Test AgentConfigManager initialization and configuration"""
    
    def test_agent_config_manager_basic_initialization(self, mock_config, mock_adk_services):
        """
        RED: Test basic AgentConfigManager initialization
        Should initialize with name, description, instruction, and config
        """
        # Arrange
        name = "test_agent"
        description = "Test agent for unit testing"
        instruction = "You are a test agent"
        tools = []
        
        # Act
        config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
        
        # Assert
        assert config_manager.name == name
        assert config_manager.description == description
        assert config_manager.base_instruction == instruction
        assert config_manager.config == mock_config
        assert config_manager.tools == tools
        assert config_manager.logger is not None
    
    def test_agent_config_manager_with_tools(self, mock_config, mock_adk_services):
        """
        RED: Test AgentConfigManager initialization with tools
        Should properly initialize with tools and avoid schema generation
        """
        # Arrange
        name = "tool_agent"
        description = "Agent with tools"
        instruction = "Use tools effectively"
        tools = [MagicMock(name="save_plot"), MagicMock(name="get_plot")]
        
        # Act
        config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
        
        # Assert
        assert config_manager.name == name
        assert config_manager.tools == tools
        assert len(config_manager.tools) == 2
        # Should use base instruction when tools are present
        assert config_manager.instruction == instruction
    
    def test_agent_config_manager_dynamic_schema_generation(self, mock_config, mock_adk_services):
        """
        RED: Test dynamic schema generation for agents without tools
        Should generate instruction with JSON schema for database operations
        """
        # Arrange
        name = "plot_generator"
        description = "Plot generation agent"
        instruction = "Generate plots"
        tools = []
        
        # Mock schema service to return schema
        with patch('src.core.agent_modules.agent_config_manager.schema_service') as mock_schema:
            mock_schema.get_content_type_from_agent.return_value = "plot"
            mock_schema._get_fallback_json_schema.return_value = {
                "title": {"type": "string"},
                "genre": {"type": "string"}
            }
            mock_schema.generate_json_schema_instruction.return_value = "\\n\\nUse JSON format: {\"title\": \"...\", \"genre\": \"...\"}"
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.dynamic_schema is not None
            assert "title" in config_manager.dynamic_schema
            assert "genre" in config_manager.dynamic_schema
            assert "Use JSON format" in config_manager.instruction


class TestAgentConfigManagerADKSetup:
    """Test ADK agent and runner setup"""
    
    def test_adk_agent_creation(self, mock_config, mock_adk_services):
        """
        RED: Test ADK Agent creation
        Should create Google ADK Agent with proper configuration
        """
        # Arrange
        name = "adk_agent"
        description = "ADK integration test"
        instruction = "Use ADK"
        tools = [MagicMock(name="test_tool")]
        
        # Mock the Agent constructor
        with patch('src.core.agent_modules.agent_config_manager.Agent') as mock_agent_class:
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.adk_agent is not None
            # Verify ADK Agent was created with correct parameters
            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args
            assert call_args[1]['name'] == name
            assert call_args[1]['model'] == mock_config.model_name
            assert call_args[1]['description'] == description
            assert call_args[1]['tools'] == tools
    
    def test_adk_runner_creation(self, mock_config, mock_adk_services):
        """
        RED: Test ADK Runner creation
        Should create runner with proper app_name and agent
        """
        # Arrange
        name = "runner_agent"
        description = "Runner test"
        instruction = "Create runner"
        tools = []
        
        # Mock ADK factory and services
        with patch('src.core.agent_modules.agent_config_manager.get_adk_service_factory') as mock_factory_func:
            mock_factory = MagicMock()
            mock_runner = MagicMock()
            mock_factory.create_runner.return_value = mock_runner
            mock_factory.service_mode.value = "test_mode"
            mock_factory_func.return_value = mock_factory
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.adk_runner is not None
            assert config_manager.adk_factory is not None
            # Verify runner was created through factory
            mock_factory.create_runner.assert_called_once()
            call_args = mock_factory.create_runner.call_args
            assert call_args[1]['app_name'] == f"{name}_app"
    
    def test_observability_initialization(self, mock_config, mock_adk_services):
        """
        RED: Test observability and tracking initialization
        Should initialize observability and agent tracker
        """
        # Arrange
        name = "observability_agent"
        description = "Observability test"
        instruction = "Track everything"
        tools = []
        
        # Act
        config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
        
        # Assert
        assert config_manager.observability is not None
        assert config_manager.agent_tracker is not None


class TestAgentConfigManagerSchemaHandling:
    """Test schema generation and handling"""
    
    def test_schema_generation_for_orchestrator(self, mock_config, mock_adk_services):
        """
        RED: Test special case for orchestrator agent
        Should skip schema generation for orchestrator
        """
        # Arrange
        name = "orchestrator"
        description = "Orchestrator agent"
        instruction = "Orchestrate workflows"
        tools = []
        
        # Mock schema service
        with patch('src.core.agent_modules.agent_config_manager.schema_service') as mock_schema:
            mock_schema.get_content_type_from_agent.return_value = "orchestrator"
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.instruction == instruction  # Should use base instruction
            assert config_manager.dynamic_schema is None
    
    def test_schema_generation_fallback(self, mock_config, mock_adk_services):
        """
        RED: Test schema generation fallback when schema is unavailable
        Should fall back to base instruction when schema cannot be generated
        """
        # Arrange
        name = "unknown_agent"
        description = "Unknown agent type"
        instruction = "Unknown agent"
        tools = []
        
        # Mock schema service to return None
        with patch('src.core.agent_modules.agent_config_manager.schema_service') as mock_schema:
            mock_schema.get_content_type_from_agent.return_value = "unknown"
            mock_schema._get_fallback_json_schema.return_value = None
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.instruction == instruction  # Should fall back to base
            assert config_manager.dynamic_schema is None
    
    def test_schema_generation_error_handling(self, mock_config, mock_adk_services):
        """
        RED: Test schema generation error handling
        Should handle errors gracefully and fall back to base instruction
        """
        # Arrange
        name = "error_agent"
        description = "Error test agent"
        instruction = "Handle errors"
        tools = []
        
        # Mock schema service to raise exception
        with patch('src.core.agent_modules.agent_config_manager.schema_service') as mock_schema:
            mock_schema.get_content_type_from_agent.side_effect = Exception("Schema error")
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.instruction == instruction  # Should fall back to base
            assert config_manager.dynamic_schema is None


class TestAgentConfigManagerProperties:
    """Test property accessors and getters"""
    
    def test_property_accessors(self, mock_config, mock_adk_services):
        """
        RED: Test all property accessors
        Should provide access to all configuration properties
        """
        # Arrange
        name = "property_agent"
        description = "Property test agent"
        instruction = "Test properties"
        tools = [MagicMock(name="test_tool")]
        
        # Act
        config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
        
        # Assert
        assert config_manager.name == name
        assert config_manager.description == description
        assert config_manager.base_instruction == instruction
        assert config_manager.instruction is not None
        assert config_manager.config == mock_config
        assert config_manager.tools == tools
        assert config_manager.logger is not None
        assert config_manager.adk_agent is not None
        assert config_manager.adk_runner is not None
        assert config_manager.adk_factory is not None
        assert config_manager.observability is not None
        assert config_manager.agent_tracker is not None
    
    def test_dynamic_schema_property(self, mock_config, mock_adk_services):
        """
        RED: Test dynamic_schema property
        Should return schema when available, None otherwise
        """
        # Arrange
        name = "schema_agent"
        description = "Schema test agent"
        instruction = "Test schema"
        tools = []
        
        # Mock schema service to return schema
        with patch('src.core.agent_modules.agent_config_manager.schema_service') as mock_schema:
            mock_schema.get_content_type_from_agent.return_value = "plot"
            expected_schema = {"title": {"type": "string"}}
            mock_schema._get_fallback_json_schema.return_value = expected_schema
            mock_schema.generate_json_schema_instruction.return_value = "Schema instruction"
            
            # Act
            config_manager = AgentConfigManager(name, description, instruction, mock_config, tools)
            
            # Assert
            assert config_manager.dynamic_schema == expected_schema