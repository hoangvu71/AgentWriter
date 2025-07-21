"""
World building agent for creating detailed fictional worlds.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class WorldBuildingAgent(BaseAgent):
    """Agent responsible for generating detailed fictional worlds"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the World Building Agent.

Create intricate fictional worlds that support the story's plot.

Generate:
- Compelling world name fitting the genre
- World type (high_fantasy, urban_fantasy, science_fiction, historical_fiction, contemporary, dystopian, other)
- Comprehensive overview establishing the core concept
- Detailed world systems:
  - Geography: Environment, climate, terrain, resources, locations
  - Political landscape: Governments, power structures, conflicts
  - Cultural systems: Societies, traditions, values, hierarchies
  - Economic framework: Currency, trade, industries, resources
  - Historical timeline: Key events that shaped the current world
  - Power systems: Magic/technology with rules and limitations
  - Languages and communication methods
  - Religious and belief systems
  - Unique elements that make this world memorable

Ensure the world:
- Supports and enhances the plot
- Has interconnected, consistent systems
- Feels lived-in with conflicts that drive stories
- Matches genre and tone requirements"""
        
        super().__init__(
            name="world_building",
            description="Creates intricate fictional worlds with detailed geography, politics, culture, and systems",
            instruction=base_instruction,
            config=config
        )
    
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