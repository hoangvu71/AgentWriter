"""
Enhancement agent for improving content based on critique feedback.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class EnhancementAgent(BaseAgent):
    """Agent responsible for improving content based on critique feedback"""
    
    def __init__(self, config: Configuration):
        base_instruction = """You are the Enhancement Agent.

Systematically improve content based on critique feedback while preserving successful elements.

Enhancement process:
1. Analyze original content and its purpose
2. Review critique to identify improvements
3. Address each point while maintaining integrity
4. Amplify strengths and fix weaknesses

Generate:
- Enhanced content addressing all critique points
- Summary of improvements made
- Enhancement rationale (optional)

Guidelines:
- Address every significant critique issue
- Preserve working elements
- Maintain original intent
- Add depth where gaps identified
- Improve flow and pacing
- Strengthen genre conventions
- Enhance reader experience

Make substantial improvements that:
- Eliminate contradictions
- Deepen character/world elements
- Strengthen emotional impact
- Improve prose quality
- Exceed the original in every dimension"""
        
        super().__init__(
            name="enhancement",
            description="Improves content systematically based on detailed critique feedback",
            instruction=base_instruction,
            config=config
        )
    
    def _get_content_type(self) -> ContentType:
        return ContentType.ENHANCEMENT
    
    def _validate_request(self, request) -> None:
        """Validate enhancement request"""
        super()._validate_request(request)
        
        # Additional validation for enhancement
        content = request.content.lower()
        
        # Check if enhancement-related elements are mentioned
        enhancement_keywords = ["enhance", "improve", "rewrite", "better", "fix", "upgrade"]
        if not any(keyword in content for keyword in enhancement_keywords):
            self._logger.warning("Request may not be asking for enhancement")
    
    async def _prepare_message(self, request) -> str:
        """Prepare message with enhancement-specific context"""
        message = await super()._prepare_message(request)
        
        # Add enhancement-specific guidance if context is available
        if request.context:
            original_content = request.context.get("original_content", "")
            critique_data = request.context.get("critique_data", "")
            content_type = request.context.get("content_type", "")
            
            if original_content or critique_data or content_type:
                message += f"\n\nENHANCEMENT FOCUS:"
                if original_content:
                    message += f"\nOriginal Content: {original_content[:500]}..."
                if critique_data:
                    message += f"\nCritique Feedback: {critique_data}"
                if content_type:
                    message += f"\nContent Type: Focus on {content_type}-specific enhancements"
                message += "\nSystematically address all critique points while preserving successful elements."
        
        return message