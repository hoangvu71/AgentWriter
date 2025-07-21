"""
Characters agent for creating detailed character populations.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class CharactersAgent(BaseAgent):
    """Agent responsible for generating detailed character populations"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Characters Agent.

Create detailed character populations that serve the story and fit authentically within the established world.

Generate:
- Character count (number of main/supporting characters)
- World context integration (how characters fit the world)
- Detailed character profiles:
  - Protagonists: Main characters driving the story
  - Supporting characters: Aid or complicate the plot
  - Antagonists: Opposition with clear motivations
- Relationship networks and character dynamics

For each character ensure:
- Clear motivations and goals
- Strengths and meaningful flaws
- Unique voice fitting the world's culture
- Character arcs tied to plot themes
- Stakes (what they gain/lose)

World integration:
- Match world's cultural values and hierarchies
- Skills/occupations fit the economy
- Power access follows established rules
- Relationships reflect political/social tensions"""
        
        super().__init__(
            name="characters",
            description="Creates detailed character populations with relationships and development arcs",
            instruction=base_instruction,
            config=config
        )
    
    def _get_content_type(self) -> ContentType:
        return ContentType.CHARACTERS
    
    def _validate_request(self, request) -> None:
        """Validate character creation request"""
        super()._validate_request(request)
        
        # Additional validation for character creation
        content = request.content.lower()
        
        # Check if character-related elements are mentioned
        character_keywords = ["character", "protagonist", "cast", "people", "personality", "relationship"]
        if not any(keyword in content for keyword in character_keywords):
            self._logger.warning("Request may not be asking for character creation")
    
    def _prepare_message(self, request) -> str:
        """Prepare message with character-specific context"""
        message = super()._prepare_message(request)
        
        # Add character-specific guidance if context is available
        if request.context:
            plot_context = request.context.get("plot_context", "")
            world_context = request.context.get("world_context", "")
            genre_info = request.context.get("genre_context", "")
            
            if plot_context or world_context or genre_info:
                message += f"\n\nCHARACTER CREATION FOCUS:"
                if plot_context:
                    message += f"\nPlot Context: Create characters that serve this story: {plot_context}"
                if world_context:
                    message += f"\nWorld Context: Characters must fit authentically into this world: {world_context}"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                message += "\nEnsure characters feel like authentic inhabitants of their world while serving the plot's needs."
        
        return message