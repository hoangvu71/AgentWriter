"""
Core framework components for the multi-agent system.
Contains base classes, interfaces, and fundamental services.
"""

# Core interfaces
from .interfaces import (
    IAgent, IAgentFactory, IOrchestrator, IDatabase,
    IConnectionManager, IConfiguration, IValidator, ILogger,
    ContentType, AgentRequest, AgentResponse, StreamChunk
)

# Base classes
from .base_agent import BaseAgent
from .configuration import Configuration

# Essential services
from .container import container

__all__ = [
    # Interfaces
    "IAgent",
    "IAgentFactory", 
    "IOrchestrator",
    "IDatabase",
    "IConnectionManager",
    "IConfiguration",
    "IValidator",
    "ILogger",
    
    # Data classes and enums
    "ContentType",
    "AgentRequest",
    "AgentResponse", 
    "StreamChunk",
    
    # Base classes
    "BaseAgent",
    "Configuration",
    
    # Services
    "container",
]