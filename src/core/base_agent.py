"""
Base agent implementation for the multi-agent book writing system.
"""

import json
import re
import os
from typing import Dict, Any, Optional, AsyncGenerator
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from .interfaces import IAgent, AgentRequest, AgentResponse, StreamChunk, ContentType
from .configuration import Configuration
from .logging import get_logger
from .schema_service import schema_service
from .persistence_strategies import PersistenceStrategy, NoOpPersistenceStrategy


class BaseAgent(IAgent):
    """Base implementation for all agents"""
    
    def __init__(self, name: str, description: str, instruction: str, config: Configuration, tools=None):
        self._name = name
        self._description = description
        self._base_instruction = instruction
        self._config = config
        self._logger = get_logger(f"agent.{name}")
        self._dynamic_schema = None
        self._tools = tools or []
        
        # Generate dynamic instruction with schema
        self._instruction = self._generate_dynamic_instruction()
        
        # Initialize Google ADK agent
        self._agent = Agent(
            name=name,
            model=config.model_name,
            instruction=self._instruction,
            description=description,
            tools=self._tools  # Add tools to agent
        )
        self._runner = InMemoryRunner(self._agent, app_name=f"{name}_app")
        self._sessions = {}
        
        # Initialize persistence strategy (default to no-op, override in subclasses)
        self._persistence_strategy = NoOpPersistenceStrategy()
    
    def _generate_dynamic_instruction(self) -> str:
        """Generate instruction with dynamic schema based on database structure"""
        try:
            # Use fallback schema since database introspection might not be available
            content_type = schema_service.get_content_type_from_agent(self._name)
            
            # Special case for orchestrator - it doesn't need database schema
            if content_type == "orchestrator":
                return self._base_instruction
            
            # If agent has tools, skip JSON schema generation and use tools instead
            if self._tools:
                self._logger.info(f"Agent {self._name} has {len(self._tools)} tools - using tool-based instruction without JSON schema")
                return self._base_instruction
            
            # Get fallback schema directly (only for agents without tools)
            schema = schema_service._get_fallback_json_schema(content_type)
            
            if schema:
                self._dynamic_schema = schema
                
                # Generate schema instruction
                schema_instruction = schema_service.generate_json_schema_instruction(content_type, schema)
                
                # Combine base instruction with dynamic schema
                enhanced_instruction = self._base_instruction + "\n\n" + schema_instruction
                
                self._logger.info(f"Generated dynamic instruction with {len(schema)} schema fields for {self._name}")
                return enhanced_instruction
            else:
                self._logger.warning(f"No schema available for {content_type}, using base instruction")
                return self._base_instruction
            
        except Exception as e:
            self._logger.warning(f"Failed to generate dynamic schema for {self._name}: {e}")
            return self._base_instruction
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def instruction(self) -> str:
        return self._instruction
    
    @property 
    def dynamic_schema(self) -> Optional[Dict[str, Any]]:
        """Get the dynamic schema for this agent"""
        return self._dynamic_schema
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process a request and return a response"""
        try:
            self._logger.info(f"Processing request for user {request.user_id}")
            
            # Set session context for tools
            from ..core.container import get_container
            container = get_container()
            container.set_session_context(request.session_id, request.user_id)
            self._logger.info(f"Set session context: session_id={request.session_id}, user_id={request.user_id}")
            
            # Prepare the message with context
            message = self._prepare_message(request)
            
            # Execute the agent
            try:
                # Import Google GenAI types
                from google.genai import types
                
                # Ensure session exists
                await self._ensure_session(request.user_id, request.session_id)
                
                # Create proper message content object
                content = types.Content(
                    role='user',
                    parts=[types.Part(text=message)]
                )
                
                # Collect all response chunks and tool calls
                content_parts = []
                tool_calls = []
                
                async for event in self._runner.run_async(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    new_message=content
                ):
                    # Log every event we receive
                    self._logger.info(f"Received ADK event: {type(event).__name__}")
                    
                    # Check for function calls or tool usage in any form
                    if hasattr(event, 'function_call'):
                        self._logger.info(f"Function call found: {event.function_call}")
                        # Try to record the tool call
                        try:
                            tool_calls.append({
                                'tool': getattr(event.function_call, 'name', 'unknown'),
                                'args': getattr(event.function_call, 'arguments', {}),
                                'result': {'success': True, 'message': 'Tool detected in event'}
                            })
                        except Exception as e:
                            self._logger.error(f"Error processing function call: {e}")
                    
                    # Extract text content from events (primary response)
                    if hasattr(event, 'content') and event.content:
                        content_parts.append(str(event.content))
                    elif hasattr(event, 'text') and event.text:
                        content_parts.append(event.text)
                    elif hasattr(event, 'delta') and event.delta:
                        content_parts.append(event.delta)
                    elif hasattr(event, 'message') and hasattr(event.message, 'content'):
                        content_parts.append(str(event.message.content))
                    elif str(event):
                        # Fallback: convert event to string if it has meaningful content
                        event_str = str(event)
                        if event_str and event_str != repr(event):
                            content_parts.append(event_str)
                
                content = ''.join(content_parts)
                    
            except Exception as e:
                self._logger.error(f"Error generating response: {e}")
                content = f"Error generating response: {str(e)}"
            
            # Parse the response
            parsed_response = self._parse_response(content)
            
            # If we had tool calls, include them in metadata
            metadata = request.metadata or {}
            if tool_calls:
                metadata['tool_calls'] = tool_calls
                # Also update parsed_json with tool results if applicable
                if parsed_response is None and tool_calls:
                    # Use tool results as parsed response
                    parsed_response = {
                        'tool_results': tool_calls,
                        'success': all(tc.get('result', {}).get('success', False) for tc in tool_calls)
                    }
            
            return AgentResponse(
                agent_name=self._name,
                content=content,
                content_type=self._get_content_type(),
                parsed_json=parsed_response,
                metadata=metadata,
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
            try:
                # Import Google GenAI types
                from google.genai import types
                
                # Ensure session exists
                await self._ensure_session(request.user_id, request.session_id)
                
                # Create proper message content object
                content = types.Content(
                    role='user',
                    parts=[types.Part(text=message)]
                )
                
                async for event in self._runner.run_async(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    new_message=content
                ):
                    # Extract text content from events
                    chunk_text = None
                    if hasattr(event, 'content') and event.content:
                        chunk_text = str(event.content)
                    elif hasattr(event, 'text') and event.text:
                        chunk_text = event.text
                    elif hasattr(event, 'delta') and event.delta:
                        chunk_text = event.delta
                    
                    if chunk_text:
                        yield StreamChunk(
                            chunk=chunk_text,
                            agent_name=self._name,
                            is_complete=False
                        )
                        
            except Exception as e:
                # Error handling
                self._logger.error(f"Error in streaming: {e}")
                yield StreamChunk(
                    chunk=f"Error: {str(e)}",
                    agent_name=self._name,
                    is_complete=True
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
        
        # Add session context for tools
        if self._tools:
            message = f"{message}\n\nSESSION CONTEXT:\n"
            message = f"{message}session_id: {request.session_id}\n"
            message = f"{message}user_id: {request.user_id}"
        
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
        """Parse JSON from agent response using robust parsing"""
        from ..utils.json_parser import parse_llm_json
        
        result = parse_llm_json(content)
        if result is None:
            self._logger.debug("Could not parse JSON from response")
        
        return result
    
    def _get_content_type(self) -> ContentType:
        """Get the content type this agent produces"""
        # Override in subclasses
        return ContentType.PLOT
    
    async def _execute_tool(self, tool_call, request: AgentRequest) -> Optional[Dict[str, Any]]:
        """Execute a tool call dynamically"""
        try:
            # Add session context to tool args if not present
            tool_args = dict(tool_call.args)
            if 'session_id' not in tool_args:
                tool_args['session_id'] = request.session_id
            if 'user_id' not in tool_args:
                tool_args['user_id'] = request.user_id
            
            # Map of tool names to functions
            tool_map = {
                'save_plot': 'save_plot',
                'save_author': 'save_author',
                'save_world_building': 'save_world_building',
                'save_characters': 'save_characters',
                'get_plot': 'get_plot',
                'get_author': 'get_author',
                'list_plots': 'list_plots',
                'list_authors': 'list_authors',
                'invoke_agent': 'invoke_agent',
                'get_agent_context': 'get_agent_context',
                'update_workflow_context': 'update_workflow_context'
            }
            
            # Get the tool function
            tool_func_name = tool_map.get(tool_call.name)
            if not tool_func_name:
                self._logger.warning(f"Unknown tool: {tool_call.name}")
                return None
            
            # Import and execute the tool
            if tool_call.name.startswith('save_') or tool_call.name in ['get_plot', 'get_author', 'list_plots', 'list_authors']:
                from ..tools import writing_tools
                tool_func = getattr(writing_tools, tool_func_name)
            else:
                from ..tools import agent_tools
                tool_func = getattr(agent_tools, tool_func_name)
            
            # Execute the tool
            result = await tool_func(**tool_args)
            return result
            
        except Exception as e:
            self._logger.error(f"Error executing tool {tool_call.name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to execute tool {tool_call.name}"
            }
    
    def _validate_request(self, request: AgentRequest) -> None:
        """Validate the incoming request"""
        if not request.content:
            raise ValueError("Request content cannot be empty")
        
        if not request.user_id:
            raise ValueError("User ID is required")
        
        if not request.session_id:
            raise ValueError("Session ID is required")
    
    async def _ensure_session(self, user_id: str, session_id: str) -> None:
        """Ensure a session exists for the user"""
        if session_id not in self._sessions:
            try:
                # Create new session - must match runner's app_name
                session = await self._runner.session_service.create_session(
                    app_name=f"{self._name}_app",  # Must match runner app_name
                    user_id=user_id,
                    session_id=session_id
                )
                self._sessions[session_id] = session
                self._logger.info(f"Created new session {session_id} for user {user_id}")
            except Exception as e:
                self._logger.error(f"Failed to create session: {e}")
                raise  # Don't continue without session - it's required
    
    def get_persistence_strategy(self) -> PersistenceStrategy:
        """Get the persistence strategy for this agent"""
        return self._persistence_strategy
    
    def set_persistence_strategy(self, strategy: PersistenceStrategy) -> None:
        """Set the persistence strategy for this agent"""
        self._persistence_strategy = strategy
        self._logger.info(f"Set persistence strategy to {strategy.__class__.__name__}")