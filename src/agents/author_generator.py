"""
Author generator agent for creating detailed author profiles.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
from ..tools.writing_tools import save_author


class AuthorGeneratorAgent(BaseAgent):
    """Agent responsible for generating detailed author profiles"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Author Generator Agent.

Create believable author profiles matching the specified genre and target audience.

CRITICAL: Generate UNIQUE, VARIED author names. Never repeat the same name combinations. Use diverse:
- First names (avoid Jake, Rex, common repeating names)
- Last names (mix ethnicities, regions, unique surnames) 
- Cultural backgrounds and origins
- Personal histories and career paths

Generate:
- UNIQUE realistic author name and pen name (never repeat previous names)
- Comprehensive biography with relevant background and experience
- Writing style description that matches the genre
- Genre expertise that feels authentic

Ensure the author:
- Has a COMPLETELY UNIQUE name combination not used before
- Feels like a real person who could write in this genre
- Has background that logically supports their expertise
- Appeals to the target audience
- Avoids stereotypes while maintaining authenticity
- Represents diverse backgrounds, ethnicities, and experiences

When you have generated a complete author profile, use the save_author tool to save it to the database.

IMPORTANT: Always include session_id and user_id in your tool calls for proper data association.

Use the save_author tool with these parameters:
- author_name: Full name of the author
- author_bio: Comprehensive biography
- writing_style: Description of writing style and voice
- session_id: Use the current session ID from context
- user_id: Use the current user ID from context  
- pen_name: Optional pen name or pseudonym
- genres: Optional list of genres"""
        
        # Initialize with tools
        tools = [save_author]
        
        super().__init__(
            name="author_generator",
            description="Creates detailed author profiles matching genre and audience specifications",
            instruction=base_instruction,
            config=config,
            tools=tools
        )
        
    
    def _get_content_type(self) -> ContentType:
        return ContentType.AUTHOR
    
    def _validate_request(self, request) -> None:
        """Validate author generation request"""
        super()._validate_request(request)
        
        # Additional validation for author generation
        content = request.content.lower()
        
        # Check if author-related elements are mentioned
        author_keywords = ["author", "writer", "biography", "pen name", "writing style"]
        if not any(keyword in content for keyword in author_keywords):
            self._logger.warning("Request may not be asking for author generation")
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with author-specific context"""
        message = await super()._prepare_message(request)
        
        # Add author-specific guidance if context is available
        if request.context:
            # Handle both legacy and new structured context formats
            
            # Legacy format support
            plot_context = request.context.get("plot_context", "")
            genre_info = request.context.get("genre_context", "")
            audience_info = request.context.get("audience_context", "")
            
            # New structured format from frontend
            genre_hierarchy = request.context.get("genre_hierarchy", {})
            story_elements = request.context.get("story_elements", {})
            target_audience = request.context.get("target_audience", {})
            
            # Build author generation focus from available context
            focus_parts = []
            
            # Handle genre hierarchy
            if genre_hierarchy:
                genre_parts = []
                if "genre" in genre_hierarchy:
                    genre_parts.append(f"Genre: {genre_hierarchy['genre']['name']}")
                if "subgenre" in genre_hierarchy:
                    genre_parts.append(f"Subgenre: {genre_hierarchy['subgenre']['name']}")
                if "microgenre" in genre_hierarchy:
                    genre_parts.append(f"Microgenre: {genre_hierarchy['microgenre']['name']}")
                if genre_parts:
                    focus_parts.append("Genre Context: " + ", ".join(genre_parts))
            elif genre_info:
                focus_parts.append(f"Genre Context: {genre_info}")
            
            # Handle story elements
            if story_elements:
                story_parts = []
                if "trope" in story_elements:
                    story_parts.append(f"Trope: {story_elements['trope']['name']}")
                if "tone" in story_elements:
                    story_parts.append(f"Tone: {story_elements['tone']['name']}")
                if story_parts:
                    focus_parts.append("Story Elements: " + ", ".join(story_parts))
            
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
            elif audience_info:
                focus_parts.append(f"Audience Context: {audience_info}")
            
            # Add plot context if available
            if plot_context:
                focus_parts.append(f"Plot Context: Create an author who could believably write this type of story: {plot_context}")
            
            # Build the final message
            if focus_parts:
                message += f"\n\nAUTHOR GENERATION FOCUS:"
                for part in focus_parts:
                    message += f"\n{part}"
                message += "\n\nEnsure the author profile aligns with these specifications and could authentically write for this genre and audience."
        
        return message