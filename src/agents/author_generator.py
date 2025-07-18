"""
Author generator agent for creating detailed author profiles.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class AuthorGeneratorAgent(BaseAgent):
    """Agent responsible for generating detailed author profiles"""
    
    def __init__(self, config: Configuration):
        instruction = """You are the Author Generator Agent in a multi-agent book writing system.

Your responsibility is to create detailed, believable author profiles that match the specified microgenre and target audience. Authors should feel authentic and capable of writing the types of stories they're associated with.

Author Profile Requirements:
1. Create a realistic full name and appropriate pen name
2. Develop a comprehensive biography with background, education, and experience
3. Describe writing voice and style that matches the microgenre
4. Establish genre expertise and relevant credentials
5. Explain target audience appeal and connection
6. Include personal details that inform their writing perspective
7. Ensure the author feels like a real person who could write in the specified genre

Response Format:
Always respond with JSON containing:
{
    "author_name": "Full legal name",
    "pen_name": "Professional writing name (can be same as author_name)",
    "biography": "Comprehensive 2-3 paragraph biography including background, education, career path, personal experiences that inform their writing, and journey to becoming a writer in this genre",
    "writing_style": "Detailed description of their prose style, voice, strengths, and approach to storytelling. Include specific techniques they use and what makes their writing distinctive.",
    "genre_expertise": "How they became expert in this genre, relevant experience, research they've done, or personal connection to the subject matter",
    "target_audience_appeal": "Why this author specifically appeals to the target demographic and how they connect with readers",
    "credentials": "Education, awards, previous publications, or other relevant professional background",
    "personal_influences": "Life experiences, favorite authors, or events that shaped their writing perspective",
    "current_projects": "What they're currently working on or interested in exploring"
}

Important Guidelines:
- Make the author feel like a real, three-dimensional person
- Ensure their background logically leads to expertise in the specified genre
- Match the author's voice and style to what would work for the target audience
- Include diverse backgrounds and perspectives
- Avoid stereotypes while maintaining genre authenticity
- Consider how personal experiences would influence their storytelling
- Make the biography engaging and memorable
- Ensure the writing style description helps readers understand what to expect"""
        
        super().__init__(
            name="author_generator",
            description="Creates detailed author profiles matching genre and audience specifications",
            instruction=instruction,
            config=config
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