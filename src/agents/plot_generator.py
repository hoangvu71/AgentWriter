"""
Plot generator agent for creating detailed story plots.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class PlotGeneratorAgent(BaseAgent):
    """Agent responsible for generating detailed story plots"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Plot Generator Agent.

Generate engaging plots based on:
- Genre/subgenre/microgenre specifications
- Story tropes and tone preferences  
- Target audience demographics

Create plots with:
- Compelling title
- 2-3 paragraph summary with clear beginning, middle, end
- Authentic genre elements and natural trope integration
- Age-appropriate content matching specified tone
- Hooks and conflicts that engage the target demographic"""
        
        super().__init__(
            name="plot_generator",
            description="Creates detailed story plots based on genre and audience specifications",
            instruction=base_instruction,
            config=config
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
    
    def _prepare_message(self, request) -> str:
        """Prepare message with plot-specific context"""
        message = super()._prepare_message(request)
        
        # Add plot-specific guidance if context is available
        if request.context:
            genre_info = request.context.get("genre_context", "")
            audience_info = request.context.get("audience_context", "")
            
            if genre_info or audience_info:
                message += f"\n\nPLOT GENERATION FOCUS:"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                if audience_info:
                    message += f"\nAudience Context: {audience_info}"
                message += "\nEnsure the plot incorporates these specifications authentically."
        
        return message