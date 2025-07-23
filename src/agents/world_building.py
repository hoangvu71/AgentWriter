"""
World building agent for creating detailed fictional worlds.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
from ..core.persistence_strategies import WorldBuildingPersistenceStrategy
from ..tools.writing_tools import save_world_building, get_plot


class WorldBuildingAgent(BaseAgent):
    """Agent responsible for generating detailed fictional worlds"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the World Building Agent.

Create fictional worlds that support the story's plot with whatever depth and scope the genre requires.

Generate:
- Compelling world name fitting the genre
- World type (high_fantasy, urban_fantasy, science_fiction, historical_fiction, contemporary, dystopian, other)
- Complete world content as a single comprehensive piece

Create the world content with whatever structure, depth, and detail serves the story best. Let the genre and plot context guide you - some worlds need vast histories and countless locations, others need focused contemporary settings. Build exactly what the story needs.

When provided with a plot_id, use get_plot tool to retrieve plot context first.
When you have created a complete world, use save_world_building tool to save it to the database.

IMPORTANT: Always include session_id and user_id in your tool calls for proper data association.

Use the save_world_building tool with these parameters:
- world_name: Compelling world name fitting the genre
- world_content: Complete world building content 
- session_id: Use the current session ID from context
- user_id: Use the current user ID from context
- plot_id: Associated plot ID if provided
- world_type: Type of world (high_fantasy, urban_fantasy, etc.)
        
        # Initialize with tools
        tools = [save_world_building, get_plot]
        
        super().__init__(
            name="world_building",
            description="Creates intricate fictional worlds with detailed geography, politics, culture, and systems",
            instruction=base_instruction,
            config=config,
            tools=tools
        )
        
        # Set persistence strategy for world building
        self.set_persistence_strategy(WorldBuildingPersistenceStrategy())
    
    def _get_content_type(self) -> ContentType:
        return ContentType.WORLD_BUILDING
    
    def _validate_request(self, request) -> None:
        """Validate world building request"""
        super()._validate_request(request)
        
        # Additional validation for world building
        content = request.content.lower()
        
        # Check if world building elements are mentioned
        world_keywords = ["world", "setting", "geography", "culture", "politics", "magic", "society"]
        if not any(keyword in content for keyword in world_keywords):
            self._logger.warning("Request may not be asking for world building")
    
    def _prepare_message(self, request) -> str:
        """Prepare message with world building specific context"""
        message = super()._prepare_message(request)
        
        # Add world building specific guidance if context is available
        if request.context:
            plot_context = request.context.get("plot_context", "")
            genre_info = request.context.get("genre_context", "")
            
            if plot_context or genre_info:
                message += f"\n\nWORLD BUILDING FOCUS:"
                if plot_context:
                    message += f"\nPlot Context: Create a world that supports this story: {plot_context}"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                message += "\nEnsure the world building serves the narrative and enhances the plot's conflicts and themes."
        
        return message