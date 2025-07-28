"""
Multi-agent system for AI-powered book writing.
Contains specialized agents for different aspects of creative writing.
"""

# Agent factory (primary interface)
from .agent_factory import AgentFactory

# Core agents
from .orchestrator import OrchestratorAgent
from .plot_generator import PlotGeneratorAgent
from .author_generator import AuthorGeneratorAgent
from .world_building import WorldBuildingAgent
from .characters import CharactersAgent

# Enhancement and analysis agents  
from .enhancement import EnhancementAgent
from .critique import CritiqueAgent
from .scoring import ScoringAgent
from .loregen import LoreGenAgent

__all__ = [
    # Factory (primary interface)
    "AgentFactory",
    
    # Core agents
    "OrchestratorAgent",
    "PlotGeneratorAgent", 
    "AuthorGeneratorAgent",
    "WorldBuildingAgent",
    "CharactersAgent",
    
    # Enhancement agents
    "EnhancementAgent",
    "CritiqueAgent", 
    "ScoringAgent",
    "LoreGenAgent",
]