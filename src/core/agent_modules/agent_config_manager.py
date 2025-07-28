"""
Agent Configuration Manager for BaseAgent refactoring.

This module handles agent initialization, ADK setup, schema generation,
and configuration management with clear single responsibility.
"""

from typing import Dict, Any, Optional, List
from google.adk.agents import Agent

from ..interfaces import IAgent
from ..configuration import Configuration
from ..logging import get_logger
from ..schema_service import schema_service
from ..adk_services import get_adk_service_factory
from ..observability import initialize_observability
from ..agent_tracker import get_agent_tracker


class AgentConfigManager:
    """
    Manages agent configuration, initialization, and ADK setup.
    
    Responsibilities:
    - Agent initialization and configuration
    - Dynamic schema generation for database operations
    - ADK agent and runner setup
    - Observability and tracking initialization
    """
    
    def __init__(self, name: str, description: str, instruction: str, config: Configuration, tools: Optional[List] = None):
        """
        Initialize agent configuration manager.
        
        Args:
            name: Agent name
            description: Agent description
            instruction: Base instruction for the agent
            config: Configuration object
            tools: Optional list of tools for the agent
        """
        # Store basic configuration
        self._name = name
        self._description = description
        self._base_instruction = instruction
        self._config = config
        self._tools = tools or []
        self._dynamic_schema = None
        
        # Initialize logging
        self._logger = get_logger(f"agent.{name}")
        
        # Generate dynamic instruction with schema
        self._instruction = self._generate_dynamic_instruction()
        
        # Initialize ADK components
        self._setup_adk_components()
        
        # Initialize observability and tracking
        self._setup_observability()
        
        # Log the service mode being used
        self._logger.info(f"Initialized with ADK service mode: {self._adk_factory.service_mode.value}")
    
    def _generate_dynamic_instruction(self) -> str:
        """Generate instruction with dynamic schema based on database structure"""
        try:
            # Use fallback schema since database introspection might not be available
            content_type = schema_service.get_content_type_from_agent(self._name)
            
            # Special case for orchestrator - it doesn't need database schema
            if content_type == "orchestrator":
                return self._base_instruction
            
            # If agent has tools, skip JSON schema generation and use tools instead
            if self._tools:
                self._logger.info(f"Agent {self._name} has {len(self._tools)} tools - using tool-based instruction without JSON schema")
                return self._base_instruction
            
            # Get fallback schema directly (only for agents without tools)
            schema = schema_service._get_fallback_json_schema(content_type)
            
            if schema:
                self._dynamic_schema = schema
                
                # Generate schema instruction
                schema_instruction = schema_service.generate_json_schema_instruction(content_type, schema)
                
                # Combine base instruction with dynamic schema
                enhanced_instruction = self._base_instruction + "\n\n" + schema_instruction
                
                self._logger.info(f"Generated dynamic instruction with {len(schema)} schema fields for {self._name}")
                return enhanced_instruction
            else:
                self._logger.warning(f"No schema available for {content_type}, using base instruction")
                return self._base_instruction
            
        except Exception as e:
            self._logger.warning(f"Failed to generate dynamic schema for {self._name}: {e}")
            return self._base_instruction
    
    def _setup_adk_components(self) -> None:
        """Initialize Google ADK agent and runner components"""
        # Initialize Google ADK agent
        self._adk_agent = Agent(
            name=self._name,
            model=self._config.model_name,
            instruction=self._instruction,
            description=self._description,
            tools=self._tools
        )
        
        # Create ADK runner based on service configuration
        self._adk_factory = get_adk_service_factory(self._config)
        self._adk_runner = self._adk_factory.create_runner(
            self._adk_agent, 
            app_name=f"{self._name}_app"
        )
    
    def _setup_observability(self) -> None:
        """Initialize observability and tracking components"""
        self._observability = initialize_observability()
        self._agent_tracker = get_agent_tracker()
    
    # Property accessors
    @property
    def name(self) -> str:
        """Get agent name"""
        return self._name
    
    @property
    def description(self) -> str:
        """Get agent description"""
        return self._description
    
    @property
    def base_instruction(self) -> str:
        """Get base instruction (before schema enhancement)"""
        return self._base_instruction
    
    @property
    def instruction(self) -> str:
        """Get final instruction (with schema if applicable)"""
        return self._instruction
    
    @property
    def config(self) -> Configuration:
        """Get configuration object"""
        return self._config
    
    @property
    def tools(self) -> List:
        """Get agent tools"""
        return self._tools
    
    @property
    def dynamic_schema(self) -> Optional[Dict[str, Any]]:
        """Get the dynamic schema for this agent"""
        return self._dynamic_schema
    
    @property
    def logger(self):
        """Get agent logger"""
        return self._logger
    
    @property
    def adk_agent(self) -> Agent:
        """Get ADK agent instance"""
        return self._adk_agent
    
    @property
    def adk_runner(self):
        """Get ADK runner instance"""
        return self._adk_runner
    
    @property
    def adk_factory(self):
        """Get ADK service factory"""
        return self._adk_factory
    
    @property
    def observability(self):
        """Get observability instance"""
        return self._observability
    
    @property
    def agent_tracker(self):
        """Get agent tracker instance"""
        return self._agent_tracker