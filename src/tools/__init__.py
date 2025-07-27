"""
Tools module for agent tool definitions
"""

from .writing_tools import (
    save_plot,
    save_author,
    save_world_building,
    save_characters,
    get_plot,
    get_author,
    list_plots,
    list_authors
)

from .agent_tools import (
    invoke_agent,
    get_agent_context,
    update_workflow_context,
    list_available_agents
)

__all__ = [
    # Writing tools (functions)
    'save_plot',
    'save_author', 
    'save_world_building',
    'save_characters',
    'get_plot',
    'get_author',
    'list_plots',
    'list_authors',
    
    # Agent coordination tools (functions)
    'invoke_agent',
    'get_agent_context',
    'update_workflow_context',
    'list_available_agents'
]