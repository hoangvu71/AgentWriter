"""
Critique agent for providing detailed content analysis and feedback.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class CritiqueAgent(BaseAgent):
    """Agent responsible for providing detailed critique and analysis of content"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Critique Agent.

Provide comprehensive, constructive analysis of writing content (plots, characters, worlds, authors).

Analyze and generate:
- Content quality assessment
- Structure and organization evaluation
- Key strengths with specific examples
- Weaknesses that need improvement
- Specific, actionable recommendations
- Reader experience impact

Focus on:
- Constructive specificity over vague feedback
- How improvements enhance reader experience
- Genre conventions and expectations
- Internal consistency and logic
- Target audience appeal

Balance honest assessment with encouragement. Prioritize issues by impact."""
        
        super().__init__(
            name="critique",
            description="Provides detailed analysis and constructive feedback on writing content",
            instruction=base_instruction,
            config=config
        )
    
    def _get_content_type(self) -> ContentType:
        return ContentType.CRITIQUE
    
    def _validate_request(self, request) -> None:
        """Validate critique request"""
        super()._validate_request(request)
        
        # Additional validation for critique
        content = request.content.lower()
        
        # Check if critique-related elements are mentioned
        critique_keywords = ["critique", "analyze", "feedback", "review", "improve", "evaluate"]
        if not any(keyword in content for keyword in critique_keywords):
            self._logger.warning("Request may not be asking for critique")
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with critique-specific context"""
        message = await super()._prepare_message(request)
        
        # Add critique-specific guidance if context is available
        if request.context:
            content_type = request.context.get("content_type", "")
            target_audience = request.context.get("target_audience", "")
            genre_info = request.context.get("genre_context", "")
            
            if content_type or target_audience or genre_info:
                message += f"\n\nCRITIQUE FOCUS:"
                if content_type:
                    message += f"\nContent Type: Focus critique on {content_type}-specific elements"
                if target_audience:
                    message += f"\nTarget Audience: Consider appeal to {target_audience}"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                message += "\nProvide critique that helps optimize this content for its intended purpose and audience."
        
        return message