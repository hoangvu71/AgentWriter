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

Generate:
- Realistic author name and pen name
- Comprehensive biography with relevant background and experience
- Writing style description that matches the genre
- Genre expertise that feels authentic

Ensure the author:
- Feels like a real person who could write in this genre
- Has background that logically supports their expertise
- Appeals to the target audience
- Avoids stereotypes while maintaining authenticity

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
    
    def _prepare_message(self, request) -> str:
        """Prepare message with author-specific context"""
        message = super()._prepare_message(request)
        
        # Add author-specific guidance if context is available
        if request.context:
            plot_context = request.context.get("plot_context", "")
            genre_info = request.context.get("genre_context", "")
            audience_info = request.context.get("audience_context", "")
            
            if plot_context or genre_info or audience_info:
                message += f"\n\nAUTHOR GENERATION FOCUS:"
                if plot_context:
                    message += f"\nPlot Context: Create an author who could believably write this type of story: {plot_context}"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                if audience_info:
                    message += f"\nAudience Context: {audience_info}"
                message += "\nEnsure the author profile aligns with these specifications and could authentically write for this genre and audience."
        
        return message