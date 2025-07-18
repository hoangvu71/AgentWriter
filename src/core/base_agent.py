"""
Base agent implementation for the multi-agent book writing system.
"""

import json
import re
from typing import Dict, Any, Optional, AsyncGenerator
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from .interfaces import IAgent, AgentRequest, AgentResponse, StreamChunk, ContentType
from .configuration import Configuration
from .logging import get_logger


class BaseAgent(IAgent):
    """Base implementation for all agents"""
    
    def __init__(self, name: str, description: str, instruction: str, config: Configuration):
        self._name = name
        self._description = description
        self._instruction = instruction
        self._config = config
        self._logger = get_logger(f"agent.{name}")
        
        # Initialize Google ADK agent
        self._agent = Agent(
            name=name,
            model=config.model_name,
            instruction=instruction,
            description=description
        )
        self._runner = InMemoryRunner(self._agent)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def instruction(self) -> str:
        return self._instruction
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process a request and return a response"""
        try:
            self._logger.info(f"Processing request for user {request.user_id}")
            
            # Prepare the message with context
            message = self._prepare_message(request)
            
            # Execute the agent
            async with self._runner.run(
                user_id=request.user_id,
                session_id=request.session_id,
                new_message=message
            ) as session:
                response = await session.send(message, user=request.user_id)
            
            # Parse the response
            parsed_response = self._parse_response(response.content)
            
            return AgentResponse(
                agent_name=self._name,
                content=response.content,
                content_type=self._get_content_type(),
                parsed_json=parsed_response,
                metadata=request.metadata or {},
                success=True
            )
            
        except Exception as e:
            self._logger.error(f"Error processing request: {e}", error=e)
            return AgentResponse(
                agent_name=self._name,
                content="",
                content_type=self._get_content_type(),
                success=False,
                error=str(e)
            )
    
    async def process_request_streaming(self, request: AgentRequest) -> AsyncGenerator[StreamChunk, None]:
        """Process a request with streaming response"""
        try:
            self._logger.info(f"Processing streaming request for user {request.user_id}")
            
            # Prepare the message with context
            message = self._prepare_message(request)
            
            # Execute the agent with streaming
            async with self._runner.run(
                user_id=request.user_id,
                session_id=request.session_id,
                new_message=message
            ) as session:
                async for chunk in session.send_streaming(message, user=request.user_id):
                    yield StreamChunk(
                        chunk=chunk.content,
                        agent_name=self._name,
                        is_complete=False
                    )
            
            # Send completion signal
            yield StreamChunk(
                chunk="",
                agent_name=self._name,
                is_complete=True
            )
            
        except Exception as e:
            self._logger.error(f"Error in streaming request: {e}", error=e)
            yield StreamChunk(
                chunk=f"Error: {str(e)}",
                agent_name=self._name,
                is_complete=True
            )
    
    def _prepare_message(self, request: AgentRequest) -> str:
        """Prepare the message to send to the agent"""
        message = request.content
        
        # Add context if available
        if request.context:
            context_str = self._format_context(request.context)
            message = f"{message}\n\nCONTEXT:\n{context_str}"
        
        return message
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable string"""
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
    
    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from agent response"""
        try:
            # Look for JSON blocks in the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to parse the entire content as JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                return json.loads(content.strip())
            
            return None
            
        except json.JSONDecodeError:
            self._logger.debug("Could not parse JSON from response")
            return None
    
    def _get_content_type(self) -> ContentType:
        """Get the content type this agent produces"""
        # Override in subclasses
        return ContentType.PLOT
    
    def _validate_request(self, request: AgentRequest) -> None:
        """Validate the incoming request"""
        if not request.content:
            raise ValueError("Request content cannot be empty")
        
        if not request.user_id:
            raise ValueError("User ID is required")
        
        if not request.session_id:
            raise ValueError("Session ID is required")