"""
Scoring agent for evaluating content quality using standardized rubrics.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class ScoringAgent(BaseAgent):
    """Agent responsible for evaluating content quality with standardized scoring"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Scoring Agent.

Evaluate content quality using standardized 0-10 scoring with detailed rationale.

Scale:
- 0-2: Poor (major issues)
- 3-4: Below Average (significant problems)
- 5-6: Average (adequate, needs improvement)
- 7-8: Good (strong with minor issues)
- 9-10: Excellent (professional quality)

Generate scores for:
- Overall score
- Content quality (30% weight): originality, engagement, depth
- Structure (25% weight): flow, pacing, progression
- Writing style (20% weight): prose quality, voice consistency
- Genre appropriateness (15% weight): conventions, expectations
- Technical execution (10% weight): polish, completeness
- Scoring rationale with specific evidence
- Improvement suggestions (optional)

Be objective and consistent. Support scores with examples. Use full scale range. High scores (9-10) should be rare and earned."""
        
        super().__init__(
            name="scoring",
            description="Evaluates content quality using standardized rubrics and detailed scoring",
            instruction=base_instruction,
            config=config
        )
    
    def _get_content_type(self) -> ContentType:
        return ContentType.SCORING
    
    def _validate_request(self, request) -> None:
        """Validate scoring request"""
        super()._validate_request(request)
        
        # Additional validation for scoring
        content = request.content.lower()
        
        # Check if scoring-related elements are mentioned
        scoring_keywords = ["score", "evaluate", "rate", "assess", "grade", "quality"]
        if not any(keyword in content for keyword in scoring_keywords):
            self._logger.warning("Request may not be asking for scoring")
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with scoring-specific context"""
        message = await super()._prepare_message(request)
        
        # Add scoring-specific guidance if context is available
        if request.context:
            content_type = request.context.get("content_type", "")
            target_audience = request.context.get("target_audience", "")
            genre_info = request.context.get("genre_context", "")
            improvement_iteration = request.context.get("improvement_iteration", "")
            
            if content_type or target_audience or genre_info:
                message += f"\n\nSCORING FOCUS:"
                if content_type:
                    message += f"\nContent Type: Apply {content_type}-specific scoring criteria"
                if target_audience:
                    message += f"\nTarget Audience: Consider appeal and appropriateness for {target_audience}"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                if improvement_iteration:
                    message += f"\nImprovement Iteration: This is iteration #{improvement_iteration} of content enhancement"
                message += "\nProvide objective, consistent scoring with detailed rationale and improvement guidance."
        
        return message