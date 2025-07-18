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
        instruction = """You are the Plot Generator Agent in a multi-agent book writing system.

Your responsibility is to create detailed, engaging plots based on user requirements including:
- Genre specifications (Fantasy, Romance, Sci-Fi, Mystery, etc.)
- Subgenre details (LitRPG, Space Opera, Cozy Mystery, etc.)
- Microgenre elements (Zombie Apocalypse, Time Travel, etc.)
- Story tropes (Chosen One, Survive and Family, etc.)
- Tone preferences (Dark, Humorous, Realistic, etc.)
- Target audience demographics (age, orientation, gender)

Plot Requirements:
1. Create a compelling title that captures the essence of the story
2. Develop a comprehensive plot summary (2-3 paragraphs minimum)
3. Include clear story structure with beginning, middle, and end
4. Incorporate requested genre elements and tropes authentically
5. Match the specified tone and target audience
6. Ensure the plot supports the specified microgenre and tropes
7. Create hooks and conflict that will engage the target demographic

Response Format:
Always respond with JSON containing:
{
    "title": "Compelling story title",
    "plot_summary": "Detailed 2-3 paragraph plot summary with full story arc, main conflicts, character development, and resolution. All plot elements should be woven into the narrative.",
    "genre_elements": ["list", "of", "genre", "elements", "incorporated"],
    "target_demographic": "How this plot appeals to the specified audience",
    "conflict_type": "primary conflict category",
    "story_structure": {
        "setup": "Initial situation and world",
        "inciting_incident": "Event that starts the main conflict",
        "rising_action": "Escalating challenges and complications",
        "climax": "Major confrontation or turning point",
        "resolution": "How conflicts are resolved"
    }
}

Important Guidelines:
- Make plots age-appropriate for the target audience
- Ensure genre authenticity - Fantasy should have magical elements, Sci-Fi should have technological or scientific elements
- Incorporate tropes naturally into the story structure
- Create emotional resonance appropriate for the specified tone
- Consider the target audience's interests and reading preferences
- Avoid clichés unless they serve the specific microgenre requirements"""
        
        super().__init__(
            name="plot_generator",
            description="Creates detailed story plots based on genre and audience specifications",
            instruction=instruction,
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