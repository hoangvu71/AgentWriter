"""
Base agent implementation for the multi-agent book writing system.
REFACTORED VERSION using modular architecture.
"""

import uuid
import time
from typing import Dict, Any, Optional, AsyncGenerator, List
from google.genai import types

from .interfaces import IAgent, AgentRequest, AgentResponse, StreamChunk, ContentType
from .configuration import Configuration
from .mcp_agent_mixin import MCPAgentMixin

# Import new modular components
from .agent_modules import (
    AgentConfigManager,
    AgentMessageHandler, 
    AgentResponseProcessor,
    AgentToolManager,
    AgentErrorHandler
)


class BaseAgent(MCPAgentMixin, IAgent):
    """
    Refactored base implementation for all agents using modular architecture.
    
    This refactored version maintains 100% API compatibility while using
    specialized modules for different responsibilities.
    """
    
    def __init__(self, name: str, description: str, instruction: str, config: Configuration, tools=None):
        """
        Initialize BaseAgent with modular architecture.
        
        Args:
            name: Agent name
            description: Agent description  
            instruction: Base instruction
            config: Configuration object
            tools: Optional list of tools
        """
        # Initialize configuration manager (handles ADK setup, schema generation)
        self._config_manager = AgentConfigManager(name, description, instruction, config, tools)
        
        # Initialize specialized handlers
        self._message_handler = AgentMessageHandler(name, self._config_manager.adk_factory, tools)
        self._response_processor = AgentResponseProcessor(name)
        self._tool_manager = AgentToolManager(name)
        self._error_handler = AgentErrorHandler(name)
        
        # Session management (maintain compatibility)
        self._sessions = {}
    
    # Public API Properties (maintain exact compatibility)
    @property
    def name(self) -> str:
        return self._config_manager.name
    
    @property
    def description(self) -> str:
        return self._config_manager.description
    
    @property
    def instruction(self) -> str:
        return self._config_manager.instruction
    
    @property 
    def dynamic_schema(self) -> Optional[Dict[str, Any]]:
        """Get the dynamic schema for this agent"""
        return self._config_manager.dynamic_schema
    
    # Main processing methods
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process a request and return a response"""
        # Generate unique invocation ID
        invocation_id = f"{self.name}_{uuid.uuid4().hex[:8]}"
        
        # Start comprehensive tracking
        start_time = time.time()
        invocation = self._config_manager.agent_tracker.start_invocation(
            invocation_id=invocation_id,
            agent_name=self.name,
            user_id=request.user_id,
            session_id=request.session_id,
            request_content=request.content,
            request_context=request.context
        )
        
        # Start observability trace
        with self._config_manager.observability.trace_agent_execution(
            self.name, request.user_id, request.session_id, request.content
        ) as span:
            try:
                self._config_manager.logger.info(f"Processing request for user {request.user_id} (invocation: {invocation_id})")
                
                # Validate request
                self._error_handler.validate_request(request)
                
                # Set session context for tools
                from ..core.container import get_container
                container = get_container()
                container.set_session_context(request.session_id, request.user_id)
                self._config_manager.logger.info(f"Set session context: session_id={request.session_id}, user_id={request.user_id}")
                
                # Prepare the message with context
                message = await self._message_handler.prepare_message(request)
                
                # Execute the agent with LLM interaction tracking
                llm_start_time = time.time()
                tool_calls = []  # Initialize before try block
                
                try:
                    # Ensure session exists
                    await self._ensure_session(request.user_id, request.session_id)
                    
                    # Create proper message content object
                    content_obj = types.Content(
                        role='user',
                        parts=[types.Part(text=message)]
                    )
                    
                    # Track LLM interaction start
                    with self._config_manager.observability.trace_llm_interaction(
                        self.name, self._config_manager.config.model_name, message
                    ) as llm_span:
                        # Collect all response chunks and tool calls
                        content_parts = []
                        tool_calls = []
                        
                        # Get the actual session (might be different for VertexAI)
                        actual_session = self._sessions.get(request.session_id)
                        actual_session_id = getattr(actual_session, 'session_id', request.session_id) if actual_session else request.session_id
                        
                        # Handle ADK async iterator with error handling for serialization issues
                        try:
                            async for event in self._config_manager.adk_runner.run_async(
                                user_id=request.user_id,
                                session_id=actual_session_id,
                                new_message=content_obj
                            ):
                                # Log every event we receive
                                self._config_manager.logger.info(f"Received ADK event: {type(event).__name__}")
                                
                                # Check for function calls or tool usage in any form
                                if hasattr(event, 'function_call'):
                                    function_call = event.function_call
                                    function_name = getattr(function_call, 'name', 'unknown')
                                    
                                    # Validate that this is a legitimate tool call, not malformed instruction text
                                    if self._tool_manager.is_valid_tool_call(function_name):
                                        self._config_manager.logger.info(f"Valid function call found: {function_name}")
                                        # Try to record the tool call
                                        try:
                                            tool_call_data = {
                                                'tool': function_name,
                                                'args': getattr(function_call, 'arguments', {}),
                                                'result': {'success': True, 'message': 'Tool detected in event'}
                                            }
                                            tool_calls.append(tool_call_data)
                                            
                                            # Track individual tool execution
                                            with self._config_manager.observability.trace_tool_execution(
                                                tool_call_data['tool'], self.name, tool_call_data['args']
                                            ) as tool_span:
                                                tool_span.set_attribute("tool.success", True)
                                                
                                        except Exception as e:
                                            self._config_manager.logger.error(f"Error processing function call: {e}")
                                    else:
                                        self._config_manager.logger.warning(f"Malformed or invalid function call detected: {function_name} - ignoring")
                            
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
                        
                        except Exception as serialization_error:
                            if "Unable to serialize" in str(serialization_error):
                                # Use error handler for serialization recovery
                                content = self._error_handler.handle_serialization_error(
                                    serialization_error, content_parts, tool_calls
                                )
                            else:
                                raise serialization_error
                        else:
                            # Only join content_parts if no serialization error occurred
                            content = ''.join(content_parts)
                        
                        # Record LLM interaction metrics
                        llm_latency = (time.time() - llm_start_time) * 1000
                        llm_span.set_attribute("llm.latency_ms", llm_latency)
                        llm_span.set_attribute("llm.response_length", len(content))
                        
                        # Estimate token usage (rough approximation)
                        estimated_prompt_tokens = len(message.split())
                        estimated_completion_tokens = len(content.split())
                        total_tokens = estimated_prompt_tokens + estimated_completion_tokens
                        
                        llm_span.set_attribute("llm.prompt_tokens", estimated_prompt_tokens)
                        llm_span.set_attribute("llm.completion_tokens", estimated_completion_tokens)
                        llm_span.set_attribute("llm.total_tokens", total_tokens)
                        
                        # Record detailed LLM interaction in agent tracker
                        self._config_manager.agent_tracker.record_llm_interaction(
                            invocation_id=invocation_id,
                            model=self._config_manager.config.model_name,
                            prompt=message,
                            response=content,
                            prompt_tokens=estimated_prompt_tokens,
                            completion_tokens=estimated_completion_tokens,
                            latency_ms=llm_latency
                        )
                        
                except Exception as e:
                    content = self._error_handler.handle_vertex_ai_error(e)
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                
                # Record tool usage if any tools were called
                if tool_calls:
                    tool_results = [tc.get('result', {}) for tc in tool_calls]
                    self._config_manager.agent_tracker.record_tool_usage(
                        invocation_id=invocation_id,
                        tool_calls=tool_calls,
                        tool_results=tool_results
                    )
                
                # Parse the response
                parsed_response = self._response_processor.parse_response(content)
                
                # Prepare response metadata (ensure serializable)
                metadata = request.metadata or {}
                if tool_calls:
                    # Clean tool_calls to ensure they're serializable
                    serializable_tool_calls = self._tool_manager.clean_tool_calls_for_serialization(tool_calls)
                    metadata['tool_calls'] = serializable_tool_calls
                    # Also update parsed_json with tool results if applicable
                    if parsed_response is None and serializable_tool_calls:
                        # Use tool results as parsed response
                        parsed_response = {
                            'tool_results': serializable_tool_calls,
                            'success': all(tc.get('result', {}).get('success', False) for tc in serializable_tool_calls)
                        }
                    
                    # Save successful tool interactions to memory
                    await self._save_interaction_to_memory(request, tool_calls, content)
                
                # Complete the invocation tracking
                self._config_manager.agent_tracker.complete_invocation(
                    invocation_id=invocation_id,
                    success=True,
                    response_content=content,
                    parsed_json=parsed_response
                )
                
                # Set span success attributes
                span.set_attribute("success", True)
                span.set_attribute("response.content_length", len(content))
                span.set_attribute("tools.called_count", len(tool_calls))
                
                return AgentResponse(
                    agent_name=self.name,
                    content=content,
                    content_type=self._response_processor.get_content_type(),
                    parsed_json=parsed_response,
                    metadata=metadata,
                    success=True
                )
                
            except Exception as e:
                # Complete invocation with error
                self._config_manager.agent_tracker.complete_invocation(
                    invocation_id=invocation_id,
                    success=False,
                    error_message=str(e)
                )
                
                # Set span error attributes
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                error_content = self._error_handler.handle_general_error(e, "request processing")
                return AgentResponse(
                    agent_name=self.name,
                    content="",
                    content_type=self._response_processor.get_content_type(),
                    success=False,
                    error=error_content
                )
    
    async def process_request_streaming(self, request: AgentRequest) -> AsyncGenerator[StreamChunk, None]:
        """Process a request with streaming response"""
        try:
            self._config_manager.logger.info(f"Processing streaming request for user {request.user_id}")
            
            # Prepare the message with context
            message = await self._message_handler.prepare_message(request)
            
            # Execute the agent with streaming
            try:
                # Ensure session exists
                await self._ensure_session(request.user_id, request.session_id)
                
                # Create proper message content object
                content = types.Content(
                    role='user',
                    parts=[types.Part(text=message)]
                )
                
                async for event in self._config_manager.adk_runner.run_async(
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
                            agent_name=self.name,
                            is_complete=False
                        )
                        
            except Exception as e:
                # Error handling
                error_message = self._error_handler.handle_general_error(e, "streaming")
                yield StreamChunk(
                    chunk=error_message,
                    agent_name=self.name,
                    is_complete=True
                )
            
            # Send completion signal
            yield StreamChunk(
                chunk="",
                agent_name=self.name,
                is_complete=True
            )
            
        except Exception as e:
            error_message = self._error_handler.handle_general_error(e, "streaming request")
            yield StreamChunk(
                chunk=error_message,
                agent_name=self.name,
                is_complete=True
            )
    
    async def _ensure_session(self, user_id: str, session_id: str) -> None:
        """Ensure a session exists for the user"""
        if session_id not in self._sessions:
            try:
                # Create new session - must match runner's app_name
                # For VertexAI, don't pass session_id as it generates its own
                try:
                    session = await self._config_manager.adk_runner.session_service.create_session(
                        app_name=f"{self.name}_app",  # Must match runner app_name
                        user_id=user_id,
                        session_id=session_id
                    )
                except Exception as vertex_error:
                    if "User-provided Session id is not supported" in str(vertex_error):
                        # VertexAI generates its own session IDs
                        session = await self._config_manager.adk_runner.session_service.create_session(
                            app_name=f"{self.name}_app",
                            user_id=user_id
                        )
                        self._config_manager.logger.info(f"Created VertexAI session with auto-generated ID for user {user_id}")
                    else:
                        raise vertex_error
                self._sessions[session_id] = session
                self._config_manager.logger.info(f"Created new session {session_id} for user {user_id}")
            except Exception as e:
                self._config_manager.logger.error(f"Failed to create session: {e}")
                raise  # Don't continue without session - it's required
    
    async def _save_interaction_to_memory(self, request: AgentRequest, tool_calls: List[Dict], response_content: str) -> None:
        """Save interaction to ADK memory service for conversation continuity"""
        try:
            # Extract relevant information from tool calls
            generated_content = {}
            key_entities = []
            
            for tool_call in tool_calls:
                tool_name = tool_call.get('tool', '')
                tool_result = tool_call.get('result', {})
                
                if tool_result.get('success'):
                    # Extract generated content based on tool type
                    if 'plot' in tool_name:
                        plot_info = tool_result.get('plot_id', {})
                        if isinstance(plot_info, dict) and 'title' in plot_info:
                            generated_content['plot'] = {
                                'title': plot_info.get('title'),
                                'id': plot_info.get('id')
                            }
                            key_entities.append(f"plot:{plot_info.get('title', '')}")
                    
                    elif 'author' in tool_name:
                        author_info = tool_result.get('author_id', {})
                        if isinstance(author_info, dict) and 'author_name' in author_info:
                            generated_content['author'] = {
                                'name': author_info.get('author_name'),
                                'id': author_info.get('id')
                            }
                            key_entities.append(f"author:{author_info.get('author_name', '')}")
                    
                    elif 'world' in tool_name:
                        world_info = tool_result.get('world_id', {})
                        if isinstance(world_info, dict) and 'world_name' in world_info:
                            generated_content['world'] = {
                                'name': world_info.get('world_name'),
                                'id': world_info.get('id')
                            }
                            key_entities.append(f"world:{world_info.get('world_name', '')}")
            
            # Create interaction summary
            interaction_summary = f"User requested: {request.content[:100]}..."
            if generated_content:
                content_types = list(generated_content.keys())
                interaction_summary += f" Generated: {', '.join(content_types)}"
            
            # Prepare interaction data for memory
            interaction_data = {
                "type": f"{self.name}_interaction",
                "summary": interaction_summary,
                "entities": key_entities,
                "generated_content": generated_content,
                "agent_name": self.name,
                "user_request": request.content,
                "tool_calls_count": len(tool_calls)
            }
            
            # Save to memory through message handler
            await self._message_handler._get_conversation_manager().save_interaction_to_memory(
                request.session_id, request.user_id, interaction_data
            )
            
            self._config_manager.logger.debug(f"Saved interaction to memory: {len(key_entities)} entities")
            
        except Exception as e:
            self._error_handler.log_warning(f"Error saving interaction to memory: {e}")