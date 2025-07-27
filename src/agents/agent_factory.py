"""
Factory for creating agent instances.
"""

from typing import Dict, Type, List
from ..core.interfaces import IAgent, IAgentFactory
from ..core.configuration import Configuration
from .orchestrator import OrchestratorAgent
from .plot_generator import PlotGeneratorAgent
from .author_generator import AuthorGeneratorAgent
from .world_building import WorldBuildingAgent
from .characters import CharactersAgent
from .critique import CritiqueAgent
from .enhancement import EnhancementAgent
from .scoring import ScoringAgent
from .loregen import LoreGenAgent


class AgentFactory(IAgentFactory):
    """Factory for creating and managing agent instances"""
    
    def __init__(self, config: Configuration):
        self._config = config
        self._agent_registry: Dict[str, Type[IAgent]] = {
            "orchestrator": OrchestratorAgent,
            "plot_generator": PlotGeneratorAgent,
            "author_generator": AuthorGeneratorAgent,
            "world_building": WorldBuildingAgent,
            "characters": CharactersAgent,
            "critique": CritiqueAgent,
            "enhancement": EnhancementAgent,
            "scoring": ScoringAgent,
            "loregen": LoreGenAgent,
        }
        self._agent_cache: Dict[str, IAgent] = {}
    
    def create_agent(self, agent_type: str, config: Configuration = None) -> IAgent:
        """Create an agent of the specified type"""
        if config is None:
            config = self._config
        
        # Check cache first
        cache_key = f"{agent_type}_{id(config)}"
        if cache_key in self._agent_cache:
            return self._agent_cache[cache_key]
        
        # Get agent class from registry
        agent_class = self._agent_registry.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Create and cache the agent
        agent = agent_class(config)
        self._agent_cache[cache_key] = agent
        
        return agent
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        return list(self._agent_registry.keys())
    
    def register_agent(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """Register a new agent type"""
        self._agent_registry[agent_type] = agent_class
    
    def clear_cache(self) -> None:
        """Clear the agent cache"""
        self._agent_cache.clear()
    
    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all available agents"""
        agent_info = {}
        
        for agent_type in self._agent_registry.keys():
            try:
                agent = self.create_agent(agent_type)
                agent_info[agent_type] = {
                    "name": agent.name,
                    "description": agent.description,
                    "type": agent_type
                }
            except Exception as e:
                agent_info[agent_type] = {
                    "name": agent_type,
                    "description": f"Error loading agent: {str(e)}",
                    "type": agent_type
                }
        
        return agent_info
    
    def get_agent(self, agent_name: str) -> IAgent:
        """Get an agent by name (alias for create_agent)"""
        return self.create_agent(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all available agent names (alias for get_available_agents)"""
        return self.get_available_agents()