"""
Agent Message Handler for BaseAgent refactoring.

This module handles message preparation, context formatting, and conversation
history integration with clear single responsibility.
"""

import json
from typing import Dict, Any, Optional, List

from ..interfaces import AgentRequest
from ..logging import get_logger
from ..conversation_manager import get_conversation_manager


class AgentMessageHandler:
    """
    Manages agent message preparation and context handling.
    
    Responsibilities:
    - Message preparation with context integration
    - Conversation history management
    - Session context handling for tools
    - Context formatting and serialization
    """
    
    def __init__(self, agent_name: str, adk_factory, tools: Optional[List] = None):
        """
        Initialize agent message handler.
        
        Args:
            agent_name: Name of the agent
            adk_factory: ADK service factory for conversation management
            tools: Optional list of tools for the agent
        """
        self.agent_name = agent_name
        self.adk_factory = adk_factory
        self.tools = tools or []
        self.logger = get_logger(f"agent.{agent_name}.message_handler")
        self.conversation_manager = None  # Lazy initialization
    
    async def prepare_message(self, request: AgentRequest) -> str:
        """
        Prepare the message to send to the agent.
        
        Combines the original content with conversation history, context,
        and session information as needed.
        
        Args:
            request: The agent request to prepare
            
        Returns:
            Prepared message string with all context
        """
        message = request.content
        
        # Add conversation continuity context for persistent sessions
        try:
            conversation_context = await self._get_conversation_context(
                request.session_id, request.user_id
            )
            
            if conversation_context.get("has_conversation_history"):
                message = f"{message}\n\nCONVERSATION HISTORY:\n"
                message = f"{message}{conversation_context.get('context_summary', '')}"
                
                # Add user preferences if available
                preferences = conversation_context.get("user_preferences", {})
                if preferences:
                    pref_str = ", ".join([f"{k}: {v}" for k, v in preferences.items()])
                    message = f"{message}\nUser Preferences: {pref_str}"
        
        except Exception as e:
            self.logger.warning(f"Failed to get conversation context: {e}")
            # Continue without conversation context
        
        # Add session context for tools
        if self.tools:
            message = f"{message}\n\nSESSION CONTEXT:\n"
            message = f"{message}session_id: {request.session_id}\n"
            message = f"{message}user_id: {request.user_id}"
        
        # Add context if available
        if request.context:
            context_str = self.format_context(request.context)
            message = f"{message}\n\nCONTEXT:\n{context_str}"
        
        return message
    
    def format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary into readable string.
        
        Args:
            context: Dictionary of context information
            
        Returns:
            Formatted context string
        """
        if not context:
            return ""
        
        formatted_parts = []
        
        for key, value in context.items():
            if isinstance(value, dict):
                value_str = json.dumps(value, indent=2)
            elif isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)
            
            formatted_parts.append(f"{key.upper()}: {value_str}")
        
        return "\n".join(formatted_parts)
    
    async def _get_conversation_context(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get conversation context for the session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Dictionary containing conversation context
        """
        conversation_manager = await self._get_conversation_manager()
        
        return await conversation_manager.get_conversation_context(
            session_id, user_id
        )
    
    async def _get_conversation_manager(self):
        """
        Get conversation manager with lazy initialization.
        
        Returns:
            Conversation manager instance
        """
        if self.conversation_manager is None:
            self.conversation_manager = await get_conversation_manager(self.adk_factory)
        
        return self.conversation_manager