"""
World building agent for creating detailed fictional worlds.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
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

Use the save_world_building tool with these CORRECT parameters:
- world_name: Compelling world name fitting the genre
- description: Complete world building description and content
- plot_id: Associated plot ID (REQUIRED if provided in context)
- session_id: Use the current session ID from context (optional)  
- user_id: Use the current user ID from context (optional)
- geography: Optional detailed geography information (Dict)
- culture: Optional cultural details (Dict)
- history: Optional historical background (Dict)
- magic_system: Optional magic/power system details (Dict)
- technology: Optional technology level and details (Dict)
"""
        
        # Initialize with tools
        tools = [save_world_building, get_plot]
        
        super().__init__(
            name="world_building",
            description="Creates intricate fictional worlds with detailed geography, politics, culture, and systems",
            instruction=base_instruction,
            config=config,
            tools=tools
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
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with world building specific context"""
        message = await super()._prepare_message(request)
        
        # Add world building specific guidance if context is available
        if request.context:
            # Handle both legacy and new structured context formats
            
            # Legacy format support
            plot_context = request.context.get("plot_context", "")
            genre_info = request.context.get("genre_context", "")
            
            # New structured format from frontend
            genre_hierarchy = request.context.get("genre_hierarchy", {})
            story_elements = request.context.get("story_elements", {})
            target_audience = request.context.get("target_audience", {})
            
            # Build world building focus from available context
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
            
            # Add plot context if available
            if plot_context:
                focus_parts.append(f"Plot Context: Create a world that supports this story: {plot_context}")
            
            # Build the final message
            if focus_parts:
                message += f"\n\nWORLD BUILDING FOCUS:"
                for part in focus_parts:
                    message += f"\n{part}"
                message += "\n\nEnsure the world building serves the narrative and enhances the plot's conflicts and themes."
        
        return message