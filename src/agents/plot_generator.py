"""
Plot generator agent for creating detailed story plots.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
from ..tools.writing_tools import save_plot


class PlotGeneratorAgent(BaseAgent):
    """Agent responsible for generating detailed story plots"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Plot Generator Agent.

Your role is to create engaging plots and save them using the available tools.

IMPORTANT: Do not provide lengthy text responses. Instead, use the save_plot tool to save your generated plot directly to the database.

Generate plots with:
- Compelling title  
- 2-3 paragraph summary with clear beginning, middle, end
- Authentic genre elements and natural trope integration
- Age-appropriate content matching specified tone
- Hooks and conflicts that engage the target demographic

Process:
1. Think about the requested plot elements
2. Generate the title and plot summary  
3. Use the save_plot tool immediately to save it
4. Provide only a brief confirmation of what was saved

IMPORTANT: Always include session_id and user_id in your tool calls to ensure proper data association.

Use the save_plot tool with these parameters:
- title: The compelling story title
- plot_summary: Detailed 2-3 paragraph plot summary  
- session_id: Use the current session ID from context
- user_id: Use the current user ID from context
- author_id: Use the author_id from context if available (for linking plot to author)
- genre: Genre if specified
- themes: List of themes if applicable"""
        
        # Initialize with tools
        tools = [save_plot]
        
        super().__init__(
            name="plot_generator",
            description="Creates detailed story plots based on genre and audience specifications",
            instruction=base_instruction,
            config=config,
            tools=tools
        )
        
    
    def _get_content_type(self) -> ContentType:
        return ContentType.PLOT
    
    def _validate_request(self, request) -> None:
        """Validate plot generation request"""
        super()._validate_request(request)
        
        # Additional validation for plot generation
        content = request.content.lower()
        
        # Check if basic plot elements are mentioned
        plot_keywords = ["plot", "story", "novel", "book", "narrative"]
        if not any(keyword in content for keyword in plot_keywords):
            self._logger.warning("Request may not be asking for plot generation")
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with plot-specific context"""
        message = await super()._prepare_message(request)
        
        # Add plot-specific guidance if context is available
        if request.context:
            # Handle both legacy and new structured context formats
            
            # Legacy format support
            genre_info = request.context.get("genre_context", "")
            audience_info = request.context.get("audience_context", "")
            author_id = request.context.get("author_id", "")
            
            # New structured format from frontend
            genre_hierarchy = request.context.get("genre_hierarchy", {})
            story_elements = request.context.get("story_elements", {})
            target_audience = request.context.get("target_audience", {})
            
            # Build plot generation focus from available context
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
            elif audience_info:
                focus_parts.append(f"Audience Context: {audience_info}")
            
            # Build the final message
            if focus_parts:
                message += f"\n\nPLOT GENERATION FOCUS:"
                for part in focus_parts:
                    message += f"\n{part}"
                message += "\n\nEnsure the plot incorporates these specifications authentically."
            
            # Always add author_id to context if present for tool linking
            if author_id:
                if "CONTEXT:" not in message:  # Add context section if not already there
                    message += f"\n\nCONTEXT:"
                # Add author_id in the format expected by tests
                context_lines = []
                if author_id:
                    context_lines.append(f"AUTHOR_ID: {author_id}")
                # Add other context items formatted properly
                for key, value in request.context.items():
                    if key not in ["author_id", "genre_hierarchy", "story_elements", "target_audience"] and value:
                        context_lines.append(f"{key.upper()}: {value}")
                
                if context_lines:
                    message += "\n" + "\n".join(context_lines)
        
        return message