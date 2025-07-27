"""
WebSocket message handler for multi-agent system communication.
"""

import json
from typing import Dict, Any
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from ..core.interfaces import AgentRequest
from ..core.configuration import Configuration
from ..core.validation import Validator, ValidationError
from ..core.logging import get_logger
from ..websocket.connection_manager import ConnectionManager
from ..agents.agent_factory import AgentFactory


class WebSocketHandler:
    """Handles WebSocket messages and coordinates with multi-agent system"""
    
    def __init__(self, connection_manager: ConnectionManager, agent_factory: AgentFactory, config: Configuration,
                 content_saving_service, session_repository=None):
        self.connection_manager = connection_manager
        self.agent_factory = agent_factory
        self.config = config
        self.validator = Validator()
        self.logger = get_logger("websocket.handler")
        
        # Require content saving service - no fallback to supabase_service
        if not content_saving_service:
            raise ValueError("ContentSavingService is required - no fallback to supabase_service allowed")
        self.content_saving_service = content_saving_service
        
        # Session repository for orchestrator decisions
        if not session_repository:
            raise ValueError("SessionRepository is required for orchestrator decision tracking")
        self.session_repository = session_repository
    
    async def _save_plot_data(self, session_id: str, user_id: str, plot_data: Dict[str, Any], 
                             orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save plot data using centralized ContentSavingService"""
        return await self.content_saving_service.save_plot_data(session_id, user_id, plot_data, orchestrator_params)
    
    async def _save_author_data(self, session_id: str, user_id: str, author_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save author data using centralized ContentSavingService"""
        return await self.content_saving_service.save_author_data(session_id, user_id, author_data)
    
    async def _save_world_building_data(self, session_id: str, user_id: str, world_data: Dict[str, Any], 
                                       orchestrator_params: Dict[str, Any] = None, plot_id: str = None) -> Dict[str, Any]:
        """Save world building data using centralized ContentSavingService"""
        return await self.content_saving_service.save_world_building_data(session_id, user_id, world_data, orchestrator_params, plot_id)
    
    async def _save_characters_data(self, session_id: str, user_id: str, characters_data: Dict[str, Any], 
                                   orchestrator_params: Dict[str, Any] = None, world_id: str = None, plot_id: str = None) -> Dict[str, Any]:
        """Save characters data using centralized ContentSavingService"""
        return await self.content_saving_service.save_characters_data(session_id, user_id, characters_data, orchestrator_params, world_id, plot_id)
    
    async def _save_critique_data(self, iteration_id: str, critique_json: Dict[str, Any], agent_response: str) -> None:
        """Save critique data using centralized ContentSavingService"""
        return await self.content_saving_service.save_critique_data(iteration_id, critique_json, agent_response)
    
    async def _save_enhancement_data(self, iteration_id: str, enhanced_content: str, changes_made: Dict[str, Any], 
                                   rationale: str, confidence_score: float) -> None:
        """Save enhancement data using centralized ContentSavingService"""
        return await self.content_saving_service.save_enhancement_data(iteration_id, enhanced_content, changes_made, rationale, confidence_score)
    
    async def _save_score_data(self, iteration_id: str, overall_score: float, category_scores: Dict[str, Any], 
                             score_rationale: str, improvement_trajectory: str, recommendations: str) -> None:
        """Save score data using centralized ContentSavingService"""
        return await self.content_saving_service.save_score_data(iteration_id, overall_score, category_scores, score_rationale, improvement_trajectory, recommendations)
    
    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """Handle a new WebSocket connection with enhanced error context"""
        client_id = None
        try:
            # Validate session_id
            validated_session_id = self.validator.validate_alphanumeric(session_id)
            client_id = f"client_{validated_session_id}"
            
            self.logger.info(f"Establishing WebSocket connection for session {validated_session_id}", 
                           session_id=validated_session_id, client_id=client_id)
            
            await self.connection_manager.connect(websocket, client_id)
            
            # Send welcome message with enhanced context
            await self.connection_manager.send_json({
                "type": "connection_established",
                "session_id": validated_session_id,
                "client_id": client_id,
                "available_agents": self.agent_factory.get_available_agents(),
                "server_info": {
                    "version": "1.0.0",
                    "supports_reconnection": True,
                    "max_message_size": 50000
                }
            }, client_id)
            
            # Handle messages
            await self._message_loop(client_id, validated_session_id)
            
        except ValidationError as e:
            self.logger.warning(f"WebSocket validation error for session {session_id}: {e}", 
                              session_id=session_id, error=e)
            await websocket.close(code=1008, reason=f"Validation error: {str(e)}")
        except Exception as e:
            self.logger.error(f"WebSocket connection error for session {session_id}: {e}", 
                             session_id=session_id, client_id=client_id, error=e)
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except Exception:
                # WebSocket may already be closed
                pass
        finally:
            # Ensure cleanup
            if client_id:
                self.connection_manager.disconnect(client_id)
                self.logger.info(f"WebSocket connection cleanup completed for {client_id}", 
                               client_id=client_id)
    
    async def _message_loop(self, client_id: str, session_id: str):
        """Main message processing loop"""
        while self.connection_manager.is_connected(client_id):
            try:
                # Get WebSocket from connection manager
                websocket = self.connection_manager.active_connections.get(client_id)
                if not websocket:
                    break
                
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process the message
                await self._process_message(client_id, session_id, message_data)
                
            except json.JSONDecodeError as e:
                await self.connection_manager.send_json({
                    "type": "error",
                    "error": "Invalid JSON format"
                }, client_id)
            except WebSocketDisconnect:
                # Client disconnected - don't try to send messages
                self.logger.info(f"Client {client_id} disconnected", client_id=client_id)
                break
            except Exception as e:
                self.logger.error(f"Error in message loop for {client_id}: {e}", error=e)
                # Only try to send error message if connection is still active
                if client_id in self.connection_manager.active_connections:
                    try:
                        await self.connection_manager.send_json({
                            "type": "error",
                            "error": "Message processing failed"
                        }, client_id)
                    except Exception:
                        # If sending fails, the connection is dead anyway
                        break
                break
        
        # Clean up connection
        self.connection_manager.disconnect(client_id)
    
    async def _save_agent_response_to_database(
        self, 
        agent_name: str, 
        response_data: Dict[str, Any], 
        session_id: str, 
        user_id: str,
        orchestrator_data: Dict[str, Any] = None,
        context: Dict[str, str] = None
    ) -> Dict[str, str]:
        """Save agent response to appropriate database using centralized ContentSavingService
        
        Args:
            context: Dictionary containing IDs from previous agents (plot_id, world_id, author_id)
            
        Returns:
            Dictionary containing the created record ID for use by subsequent agents
        """
        if context is None:
            context = {}
            
        created_context = {}
        
        try:
            # SECURITY FIX: Merge context into orchestrator_data for dependency validation
            merged_params = orchestrator_data.copy() if orchestrator_data else {}
            if context:
                merged_params.update(context)
            
            saved_data = await self.content_saving_service.save_agent_response(
                agent_name, response_data, session_id, user_id, merged_params
            )
            if saved_data:
                # Extract relevant IDs for context passing
                if "id" in saved_data:
                    if agent_name == "plot_generator":
                        created_context["plot_id"] = saved_data["id"]
                    elif agent_name == "author_generator":
                        created_context["author_id"] = saved_data["id"]
                    elif agent_name == "world_building":
                        created_context["world_id"] = saved_data["id"]
                    elif agent_name == "characters":
                        created_context["characters_id"] = saved_data["id"]
            else:
                self.logger.info(f"No data returned from save operation for agent: {agent_name}")
                
        except Exception as e:
            self.logger.error(f"Database save error for {agent_name}: {e}")
            raise
            
        return created_context
    
    
    async def _process_message(self, client_id: str, session_id: str, message_data: Dict[str, Any]):
        """Process an incoming WebSocket message with structured context support"""
        message_type = message_data.get("type", "message")
        content = message_data.get("content", "")
        user_id = message_data.get("user_id", "anonymous")
        context = message_data.get("context", {})  # NEW: Extract structured context
        
        try:
            # Handle legacy format for backward compatibility
            if not context and "DETAILED CONTENT SPECIFICATIONS" in content:
                from ..services.context_service import ContextInjectionService
                context_service = ContextInjectionService(self.logger)
                context = context_service.create_structured_context(content)
                content = context_service.remove_legacy_context_injection(content)
                self.logger.info("Converted legacy context injection to structured format")
            
            # Validate inputs
            validated_content = self.validator.validate_text(content, max_length=50000)
            validated_user_id = self.validator.validate_alphanumeric(user_id, max_length=50)
            
            if message_type == "message":
                await self._handle_agent_message(client_id, session_id, validated_user_id, validated_content, context)
            elif message_type == "search":
                await self._handle_search_message(client_id, session_id, validated_user_id, validated_content)
            else:
                await self.connection_manager.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                }, client_id)
        
        except ValidationError as e:
            await self.connection_manager.send_json({
                "type": "error",
                "error": str(e)
            }, client_id)
    
    async def _handle_agent_message(self, client_id: str, session_id: str, user_id: str, content: str, context: Dict[str, Any] = None):
        """Handle a message using the new tool-based orchestrator approach"""
        try:
            # Set session context for tools
            from ..core.container import get_container
            container = get_container()
            container.set_session_context(session_id, user_id)
            
            # Create agent request with structured context
            request = AgentRequest(
                content=content,
                user_id=user_id,
                session_id=session_id,
                context=context or {}
            )
            
            # Get orchestrator agent (now tool-enabled)
            orchestrator = self.agent_factory.create_agent("orchestrator")
            
            # Send orchestrator header
            await self.connection_manager.send_json({
                "type": "stream_chunk",
                "content": "\n[AI] Orchestrator coordinating workflow...\n"
            }, client_id)
            
            # Let the orchestrator handle everything through tools with enhanced error recovery
            orchestrator_response = await orchestrator.process_request(request)
            
            # Send orchestrator's reasoning and tool execution results
            await self.connection_manager.send_json({
                "type": "stream_chunk", 
                "content": orchestrator_response.content
            }, client_id)
            
            # If there were tool calls, analyze results for failures and recovery
            if orchestrator_response.metadata and 'tool_calls' in orchestrator_response.metadata:
                tool_calls = orchestrator_response.metadata['tool_calls']
                
                # Analyze tool execution results
                successful_tools = [tc for tc in tool_calls if tc.get('result', {}).get('success', False)]
                failed_tools = [tc for tc in tool_calls if not tc.get('result', {}).get('success', False)]
                
                await self.connection_manager.send_json({
                    "type": "workflow_complete",
                    "tool_calls": tool_calls,
                    "results": [tc.get('result', {}) for tc in tool_calls],
                    "summary": {
                        "total_operations": len(tool_calls),
                        "successful": len(successful_tools),
                        "failed": len(failed_tools)
                    }
                }, client_id)
                
                # Handle successful operations
                if successful_tools:
                    success_msg = f"\n✅ Successfully completed {len(successful_tools)} operations:\n"
                    for tc in successful_tools:
                        result = tc.get('result', {})
                        success_msg += f"- {tc['tool']}: {result.get('message', 'Success')}\n"
                    
                    await self.connection_manager.send_json({
                        "type": "stream_chunk",
                        "content": success_msg
                    }, client_id)
                
                # Handle failed operations with recovery options
                if failed_tools:
                    failure_msg = f"\n⚠️ {len(failed_tools)} operations encountered issues:\n"
                    recovery_options = []
                    
                    for tc in failed_tools:
                        result = tc.get('result', {})
                        error_msg = result.get('error', 'Unknown error')
                        failure_msg += f"- {tc['tool']}: {error_msg}\n"
                        
                        # Suggest recovery based on tool type
                        if tc['tool'] == 'save_plot':
                            recovery_options.append("You can try creating the plot again with different parameters")
                        elif tc['tool'] == 'save_world_building':
                            recovery_options.append("World building requires an existing plot - create a plot first")
                        elif tc['tool'] == 'save_characters':
                            recovery_options.append("Character creation requires both plot and world - ensure both exist")
                    
                    if recovery_options:
                        failure_msg += f"\n💡 Recovery suggestions:\n"
                        for option in recovery_options:
                            failure_msg += f"- {option}\n"
                    
                    await self.connection_manager.send_json({
                        "type": "stream_chunk",
                        "content": failure_msg
                    }, client_id)
                    
                    # Send recovery prompt to user
                    await self.connection_manager.send_json({
                        "type": "recovery_prompt",
                        "failed_operations": failed_tools,
                        "recovery_options": recovery_options,
                        "message": "Some operations failed. Would you like to retry or modify your request?"
                    }, client_id)
            else:
                # Fallback for agents that don't use tools yet
                await self.connection_manager.send_json({
                    "type": "workflow_complete",
                    "message": "Request processed successfully"
                }, client_id)
            
            # Clear session context
            container.clear_session_context()
            
            # Legacy agent processing for backward compatibility
            # TODO: Remove this once all agents are migrated to tools
            # await self._handle_legacy_agent_processing(client_id, session_id, user_id, content, context)
            
        except Exception as e:
            self.logger.error(f"Error in tool-based agent processing: {e}", error=e)
            await self.connection_manager.send_json({
                "type": "error",
                "error": f"Failed to process message: {str(e)}"
            }, client_id)
            
            # Clear session context on error
            try:
                from ..core.container import get_container
                container = get_container()
                container.clear_session_context()
            except:
                pass
    
    async def _handle_legacy_agent_processing(self, client_id: str, session_id: str, user_id: str, content: str, context: Dict[str, Any] = None):
        """Legacy agent processing method - to be removed after full migration"""
        # This method would contain the old loop-based agent processing
        # For now, we'll skip it since the new tool-based approach should handle everything
        pass
    
    async def _handle_search_message(self, client_id: str, session_id: str, user_id: str, content: str):
        """Handle a search request"""
        try:
            # For now, implement basic search response
            # This would be replaced with actual search functionality
            await self.connection_manager.send_json({
                "type": "stream_chunk",
                "content": f"Search functionality for '{content}' is not yet implemented in the refactored version.\n"
            }, client_id)
            
            await self.connection_manager.send_json({
                "type": "stream_end",
                "full_response": f"Search for '{content}' completed."
            }, client_id)
            
        except Exception as e:
            self.logger.error(f"Error in search handling: {e}", error=e)
            await self.connection_manager.send_json({
                "type": "error",
                "error": "Search functionality failed"
            }, client_id)
