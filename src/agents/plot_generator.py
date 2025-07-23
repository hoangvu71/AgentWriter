"""
Plot generator agent for creating detailed story plots.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
from ..core.persistence_strategies import PlotPersistenceStrategy
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
        
        # Set persistence strategy for plot generation
        self.set_persistence_strategy(PlotPersistenceStrategy())
    
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