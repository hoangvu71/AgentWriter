"""
Base agent implementation for the multi-agent book writing system.
"""

import json
import re
import os
from typing import Dict, Any, Optional, AsyncGenerator, List
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from .interfaces import IAgent, AgentRequest, AgentResponse, StreamChunk, ContentType
from .configuration import Configuration
from .logging import get_logger
from .schema_service import schema_service
from .persistence_strategies import PersistenceStrategy, NoOpPersistenceStrategy
from .adk_services import get_adk_service_factory
from .conversation_manager import get_conversation_manager
from .observability import initialize_observability
from .agent_tracker import get_agent_tracker


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
        
        # Create ADK runner based on service configuration
        self._adk_factory = get_adk_service_factory(config)
        self._runner = self._adk_factory.create_runner(self._agent, app_name=f"{name}_app")
        self._sessions = {}
        
        # Log the service mode being used
        self._logger.info(f"Initialized with ADK service mode: {self._adk_factory.service_mode.value}")
        
        # Initialize conversation manager for persistent memory
        self._conversation_manager = None  # Will be initialized when needed
        
        # Initialize observability and tracking
        self._observability = initialize_observability()
        self._agent_tracker = get_agent_tracker()
        
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
        # Generate unique invocation ID
        import uuid
        import time
        invocation_id = f"{self._name}_{uuid.uuid4().hex[:8]}"
        
        # Start comprehensive tracking
        start_time = time.time()
        invocation = self._agent_tracker.start_invocation(
            invocation_id=invocation_id,
            agent_name=self._name,
            user_id=request.user_id,
            session_id=request.session_id,
            request_content=request.content,
            request_context=request.context
        )
        
        # Start observability trace
        with self._observability.trace_agent_execution(
            self._name, request.user_id, request.session_id, request.content
        ) as span:
            try:
                self._logger.info(f"Processing request for user {request.user_id} (invocation: {invocation_id})")
                
                # Set session context for tools
                from ..core.container import get_container
                container = get_container()
                container.set_session_context(request.session_id, request.user_id)
                self._logger.info(f"Set session context: session_id={request.session_id}, user_id={request.user_id}")
                
                # Prepare the message with context
                message = await self._prepare_message(request)
                
                # Execute the agent with LLM interaction tracking
                llm_start_time = time.time()
                try:
                    # Import Google GenAI types
                    from google.genai import types
                    
                    # Ensure session exists
                    await self._ensure_session(request.user_id, request.session_id)
                    
                    # Create proper message content object
                    content_obj = types.Content(
                        role='user',
                        parts=[types.Part(text=message)]
                    )
                    
                    # Track LLM interaction start
                    with self._observability.trace_llm_interaction(
                        self._name, self._config.model_name, message
                    ) as llm_span:
                        # Collect all response chunks and tool calls
                        content_parts = []
                        tool_calls = []
                        
                        async for event in self._runner.run_async(
                            user_id=request.user_id,
                            session_id=request.session_id,
                            new_message=content_obj
                        ):
                            # Log every event we receive
                            self._logger.info(f"Received ADK event: {type(event).__name__}")
                            
                            # Check for function calls or tool usage in any form
                            if hasattr(event, 'function_call'):
                                self._logger.info(f"Function call found: {event.function_call}")
                                # Try to record the tool call
                                try:
                                    tool_call_data = {
                                        'tool': getattr(event.function_call, 'name', 'unknown'),
                                        'args': getattr(event.function_call, 'arguments', {}),
                                        'result': {'success': True, 'message': 'Tool detected in event'}
                                    }
                                    tool_calls.append(tool_call_data)
                                    
                                    # Track individual tool execution
                                    with self._observability.trace_tool_execution(
                                        tool_call_data['tool'], self._name, tool_call_data['args']
                                    ) as tool_span:
                                        tool_span.set_attribute("tool.success", True)
                                        
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
                        self._agent_tracker.record_llm_interaction(
                            invocation_id=invocation_id,
                            model=self._config.model_name,
                            prompt=message,
                            response=content,
                            prompt_tokens=estimated_prompt_tokens,
                            completion_tokens=estimated_completion_tokens,
                            latency_ms=llm_latency
                        )
                        
                except Exception as e:
                    self._logger.error(f"Error generating response: {e}")
                    content = f"Error generating response: {str(e)}"
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                
                # Record tool usage if any tools were called
                if tool_calls:
                    tool_results = [tc.get('result', {}) for tc in tool_calls]
                    self._agent_tracker.record_tool_usage(
                        invocation_id=invocation_id,
                        tool_calls=tool_calls,
                        tool_results=tool_results
                    )
                
                # Parse the response
                parsed_response = self._parse_response(content)
                
                # Prepare response metadata
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
                    
                    # Save successful tool interactions to memory
                    await self._save_interaction_to_memory(request, tool_calls, content)
                
                # Complete the invocation tracking
                self._agent_tracker.complete_invocation(
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
                    agent_name=self._name,
                    content=content,
                    content_type=self._get_content_type(),
                    parsed_json=parsed_response,
                    metadata=metadata,
                    success=True
                )
                
            except Exception as e:
                # Complete invocation with error
                self._agent_tracker.complete_invocation(
                    invocation_id=invocation_id,
                    success=False,
                    error_message=str(e)
                )
                
                # Set span error attributes
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
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
            message = await self._prepare_message(request)
            
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
    
    async def _prepare_message(self, request: AgentRequest) -> str:
        """Prepare the message to send to the agent"""
        message = request.content
        
        # Initialize conversation manager if needed
        if self._conversation_manager is None:
            self._conversation_manager = await get_conversation_manager(self._adk_factory)
        
        # Add conversation continuity context for persistent sessions
        conversation_context = await self._conversation_manager.get_conversation_context(
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
    
    async def _save_interaction_to_memory(self, request: AgentRequest, tool_calls: List[Dict], response_content: str) -> None:
        """Save interaction to ADK memory service for conversation continuity"""
        if self._conversation_manager is None:
            return
        
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
                "type": f"{self._name}_interaction",
                "summary": interaction_summary,
                "entities": key_entities,
                "generated_content": generated_content,
                "agent_name": self._name,
                "user_request": request.content,
                "tool_calls_count": len(tool_calls)
            }
            
            # Save to memory
            await self._conversation_manager.save_interaction_to_memory(
                request.session_id, request.user_id, interaction_data
            )
            
            self._logger.debug(f"Saved interaction to memory: {len(key_entities)} entities")
            
        except Exception as e:
            self._logger.error(f"Error saving interaction to memory: {e}")