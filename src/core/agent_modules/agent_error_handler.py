"""
Agent Error Handler for BaseAgent refactoring.

This module handles error handling, recovery, and logging
with clear single responsibility.
"""

from typing import Dict, Any, Optional
from ..interfaces import AgentRequest
from ..logging import get_logger


class AgentErrorHandler:
    """
    Manages agent error handling and recovery.
    
    Responsibilities:
    - Request validation
    - Error recovery strategies
    - Logging and error reporting
    - Graceful degradation handling
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize agent error handler.
        
        Args:
            agent_name: Name of the agent for logging
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name}.error_handler")
    
    def validate_request(self, request: AgentRequest) -> None:
        """
        Validate the incoming request.
        
        Args:
            request: Request to validate
            
        Raises:
            ValueError: If request is invalid
        """
        if not request.content:
            raise ValueError("Request content cannot be empty")
        
        if not request.user_id:
            raise ValueError("User ID is required")
        
        if not request.session_id:
            raise ValueError("Session ID is required")
    
    def handle_serialization_error(self, error: Exception, content_parts: list, tool_calls: list) -> str:
        """
        Handle ADK serialization errors and preserve content.
        
        Args:
            error: The serialization error
            content_parts: Content parts collected before error
            tool_calls: Tool calls collected before error
            
        Returns:
            Recovered content string
        """
        self.logger.error(f"ADK serialization error: {error}")
        
        # Log detailed debugging information
        self.logger.error(f"Content parts count: {len(content_parts)}")
        self.logger.error(f"Tool calls count: {len(tool_calls)}")
        
        # Log problematic objects for debugging
        for i, tc in enumerate(tool_calls):
            try:
                import json
                json.dumps(tc)
            except Exception as json_error:
                self.logger.error(f"Tool call {i} not serializable: {json_error}")
                self.logger.error(f"Problematic tool call: {tc}")
        
        # Preserve content and reconstruct meaningful response
        if content_parts:
            content = ''.join(content_parts)
            self.logger.info(f"Preserved {len(content)} characters of content despite serialization error")
            return content
        elif tool_calls:
            # If we have tool calls but no content, reconstruct from tool results
            tool_summaries = []
            for tc in tool_calls:
                tool_name = tc.get('tool', 'unknown')
                tool_result = tc.get('result', {})
                if tool_result.get('success'):
                    tool_summaries.append(f"✓ {tool_name} completed successfully")
                else:
                    tool_summaries.append(f"✗ {tool_name} failed: {tool_result.get('error', 'unknown error')}")
            
            content = f"I've completed the following operations:\n\n" + "\n".join(tool_summaries)
            if len(tool_summaries) > 0:
                content += f"\n\nTotal operations: {len(tool_summaries)}"
            
            self.logger.info(f"Reconstructed content from {len(tool_calls)} tool calls despite serialization error")
            return content
        else:
            # Last resort fallback
            return "I encountered a technical issue with the response format, but your request has been processed. The operation may have completed successfully despite this error."
    
    def handle_vertex_ai_error(self, error: Exception) -> str:
        """
        Handle Vertex AI/ADK communication errors.
        
        Args:
            error: The Vertex AI error
            
        Returns:
            Error message for the response
        """
        self.logger.error(f"Vertex AI error: {error}")
        
        # Classify error types and provide appropriate responses
        error_str = str(error).lower()
        
        if "session" in error_str:
            return f"Session management error occurred. Please try again with a new session."
        elif "timeout" in error_str:
            return f"Request timed out. The operation may be too complex. Please try a simpler request."
        elif "quota" in error_str or "limit" in error_str:
            return f"Service quota exceeded. Please wait a moment and try again."
        elif "authentication" in error_str or "permission" in error_str:
            return f"Authentication error. Please check your credentials and try again."
        else:
            return f"Error generating response: {str(error)}"
    
    def handle_general_error(self, error: Exception, context: Optional[str] = None) -> str:
        """
        Handle general errors with context.
        
        Args:
            error: The error that occurred
            context: Optional context about where the error occurred
            
        Returns:
            Error message for the response
        """
        context_str = f" during {context}" if context else ""
        self.logger.error(f"Error{context_str}: {error}")
        
        return f"An error occurred{context_str}: {str(error)}"
    
    def log_successful_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log successful operations for monitoring.
        
        Args:
            operation: Name of the operation
            details: Optional operation details
        """
        if details:
            self.logger.info(f"Successfully completed {operation}: {details}")
        else:
            self.logger.info(f"Successfully completed {operation}")
    
    def log_warning(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log warning messages.
        
        Args:
            message: Warning message
            details: Optional warning details
        """
        if details:
            self.logger.warning(f"{message}: {details}")
        else:
            self.logger.warning(message)