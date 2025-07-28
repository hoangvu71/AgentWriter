"""
Agent Response Processor for BaseAgent refactoring.

This module handles response parsing, JSON extraction, content type handling,
and response validation with clear single responsibility.
"""

from typing import Dict, Any, Optional

from ..interfaces import ContentType
from ..logging import get_logger
from ...utils.json_parser import parse_llm_json


class AgentResponseProcessor:
    """
    Manages agent response processing and validation.
    
    Responsibilities:
    - Response parsing and JSON extraction
    - Content type determination based on agent type
    - Response validation
    - Error handling for malformed responses
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize agent response processor.
        
        Args:
            agent_name: Name of the agent for content type mapping
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name}.response_processor")
    
    def parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from agent response using robust parsing.
        
        Args:
            content: Response content to parse
            
        Returns:
            Parsed JSON dictionary or None if no valid JSON found
        """
        result = parse_llm_json(content)
        if result is None:
            self.logger.debug("Could not parse JSON from response")
        
        return result
    
    def get_content_type(self) -> ContentType:
        """
        Get the content type this agent produces based on agent name.
        
        Returns:
            ContentType enum value for the agent
        """
        # Map agent names to content types
        agent_type_mapping = {
            'plot_generator': ContentType.PLOT,
            'author_generator': ContentType.AUTHOR,
            'world_building': ContentType.WORLD_BUILDING,
            'characters': ContentType.CHARACTERS,
        }
        
        # Return mapped content type or default to PLOT
        return agent_type_mapping.get(self.agent_name, ContentType.PLOT)
    
    def validate_response(self, content: Optional[str]) -> bool:
        """
        Validate that the response content is valid and non-empty.
        
        Args:
            content: Response content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        if content is None:
            return False
        
        if not isinstance(content, str):
            return False
        
        # Check if content is empty or only whitespace
        if not content.strip():
            return False
        
        return True