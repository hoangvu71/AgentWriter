"""
Characters agent for creating detailed character populations.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
from ..tools.writing_tools import save_characters, get_plot


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
- Relationships reflect political/social tensions

When provided with plot_id and world_building_id, use get_plot tool to retrieve context first.
When you have created a complete character population, use save_characters tool to save it.

CRITICAL: You MUST provide plot_id and world_building_id to save_characters - these are REQUIRED parameters.
IMPORTANT: Always include session_id and user_id in your tool calls for proper data association.

Use the save_characters tool with these CORRECT parameters:
- plot_id: The associated plot ID (REQUIRED - get from context)
- world_building_id: The associated world building ID (REQUIRED - get from context)  
- characters: List of character dictionaries with detailed profiles
- session_id: Use the current session ID from context (optional)
- user_id: Use the current user ID from context (optional)

Character format for the characters parameter (List of Dict):
Each character should be a dictionary containing:
- name: Character's full name
- role: "protagonist", "supporting", "antagonist", etc.
- background: Personal history and origin
- motivations: What drives this character
- skills: Abilities and talents
- relationships: Connections to other characters
- character_arc: How they change throughout the story
"""
        
        # Initialize with tools
        tools = [save_characters, get_plot]
        
        super().__init__(
            name="characters",
            description="Creates detailed character populations with relationships and development arcs",
            instruction=base_instruction,
            config=config,
            tools=tools
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
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with character-specific context"""
        message = await super()._prepare_message(request)
        
        # Add character-specific guidance if context is available
        if request.context:
            # Handle both legacy and new structured context formats
            
            # Legacy format support
            plot_context = request.context.get("plot_context", "")
            world_context = request.context.get("world_context", "")
            genre_info = request.context.get("genre_context", "")
            
            # New structured format from frontend
            genre_hierarchy = request.context.get("genre_hierarchy", {})
            story_elements = request.context.get("story_elements", {})
            target_audience = request.context.get("target_audience", {})
            
            # Build character creation focus from available context
            focus_parts = []
            
            # Handle genre hierarchy
            if genre_hierarchy:
                genre_parts = []
                if "genre" in genre_hierarchy:
                    genre_parts.append(f"Genre: {genre_hierarchy['genre']['name']}")
                    if "description" in genre_hierarchy['genre']:
                        genre_parts.append(f"Genre Description: {genre_hierarchy['genre']['description']}")
                if "subgenre" in genre_hierarchy:
                    genre_parts.append(f"Subgenre: {genre_hierarchy['subgenre']['name']}")
                if "microgenre" in genre_hierarchy:
                    genre_parts.append(f"Microgenre: {genre_hierarchy['microgenre']['name']}")
                if genre_parts:
                    focus_parts.append("Genre Context:\n" + "\n".join(genre_parts))
            elif genre_info:
                focus_parts.append(f"Genre Context: {genre_info}")
            
            # Handle story elements
            if story_elements:
                story_parts = []
                if "trope" in story_elements:
                    story_parts.append(f"Trope: {story_elements['trope']['name']}")
                    if "description" in story_elements['trope']:
                        story_parts.append(f"Trope Description: {story_elements['trope']['description']}")
                if "tone" in story_elements:
                    story_parts.append(f"Tone: {story_elements['tone']['name']}")
                    if "description" in story_elements['tone']:
                        story_parts.append(f"Tone Description: {story_elements['tone']['description']}")
                if story_parts:
                    focus_parts.append("Story Elements:\n" + "\n".join(story_parts))
            
            # Handle target audience
            if target_audience:
                audience_parts = []
                if "age_group" in target_audience:
                    audience_parts.append(f"Age Group: {target_audience['age_group']}")
                if "gender" in target_audience:
                    audience_parts.append(f"Gender: {target_audience['gender']}")
                if "sexual_orientation" in target_audience:
                    audience_parts.append(f"Sexual Orientation: {target_audience['sexual_orientation']}")
                if audience_parts:
                    focus_parts.append("Target Audience: " + ", ".join(audience_parts))
            
            # Add plot and world context if available
            if plot_context:
                focus_parts.append(f"Plot Context: Create characters that serve this story: {plot_context}")
            if world_context:
                focus_parts.append(f"World Context: Characters must fit authentically into this world: {world_context}")
            
            # Build the final message
            if focus_parts:
                message += f"\n\nCHARACTER CREATION FOCUS:"
                for part in focus_parts:
                    message += f"\n{part}"
                message += "\n\nEnsure characters feel like authentic inhabitants of their world while serving the plot's needs."
        
        return message