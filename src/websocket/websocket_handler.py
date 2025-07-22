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
from ..database.supabase_service import supabase_service


class WebSocketHandler:
    """Handles WebSocket messages and coordinates with multi-agent system"""
    
    def __init__(self, connection_manager: ConnectionManager, agent_factory: AgentFactory, config: Configuration,
                 content_saving_service):
        self.connection_manager = connection_manager
        self.agent_factory = agent_factory
        self.config = config
        self.validator = Validator()
        self.logger = get_logger("websocket.handler")
        
        # Require content saving service - no fallback to supabase_service
        if not content_saving_service:
            raise ValueError("ContentSavingService is required - no fallback to supabase_service allowed")
        self.content_saving_service = content_saving_service
    
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
        """Handle a new WebSocket connection"""
        try:
            # Validate session_id
            validated_session_id = self.validator.validate_alphanumeric(session_id)
            client_id = f"client_{validated_session_id}"
            
            await self.connection_manager.connect(websocket, client_id)
            
            # Send welcome message
            await self.connection_manager.send_json({
                "type": "connection_established",
                "session_id": validated_session_id,
                "available_agents": self.agent_factory.get_available_agents()
            }, client_id)
            
            # Handle messages
            await self._message_loop(client_id, validated_session_id)
            
        except ValidationError as e:
            await websocket.close(code=1008, reason=str(e))
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}", error=e)
            await websocket.close(code=1011, reason="Internal server error")
    
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
                    elif agent_name == "characters" or agent_name == "character_agent":
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
        """Handle a message that should be processed by the multi-agent system with structured context"""
        try:
            # Create agent request with structured context
            request = AgentRequest(
                content=content,
                user_id=user_id,
                session_id=session_id,
                context=context or {}  # Include structured context
            )
            
            # Get orchestrator agent
            orchestrator = self.agent_factory.create_agent("orchestrator")
            
            # Send orchestrator header
            await self.connection_manager.send_json({
                "type": "stream_chunk",
                "content": "\n[AI] Orchestrator:\n"
            }, client_id)
            
            # Check for direct routing first (e.g., LoreGen)
            agent_names = await orchestrator.route_request(request)
            orchestrator_response = None
            orchestrator_data = {}
            
            if agent_names == ['loregen']:
                # Direct LoreGen routing - skip orchestrator reasoning
                await self.connection_manager.send_json({
                    "type": "stream_chunk", 
                    "content": "LoreGen request detected - routing to RAG-based world building expansion.\n"
                }, client_id)
                orchestrator_decision = "LoreGen request detected - routing to RAG-based world building expansion."
            else:
                # Normal orchestrator processing with reasoning
                orchestrator_response = await orchestrator.process_request(request)
                
                # Send orchestrator's reasoning
                await self.connection_manager.send_json({
                    "type": "stream_chunk", 
                    "content": orchestrator_response.content
                }, client_id)
                
                # Extract agent names from response if route_request didn't provide them
                if orchestrator_response.parsed_json and "agents_to_invoke" in orchestrator_response.parsed_json:
                    agent_names = orchestrator_response.parsed_json["agents_to_invoke"]
                
                orchestrator_decision = orchestrator_response.content if orchestrator_response.content else "Multi-agent workflow initiated"
                orchestrator_data = orchestrator_response.parsed_json if orchestrator_response.parsed_json else {}
            
            # Send routing information
            await self.connection_manager.send_json({
                "type": "workflow_start",
                "agents_to_invoke": agent_names,
                "orchestrator_decision": orchestrator_decision
            }, client_id)
            
            # Save orchestrator decision to database
            try:
                if orchestrator_data:
                    await supabase_service.save_orchestrator_decision(
                        session_id=session_id,
                        user_id=user_id,
                        decision_data=orchestrator_data
                    )
            except Exception as e:
                self.logger.warning(f"Failed to save orchestrator decision: {e}")
            
            # Process through each agent with context passing
            workflow_context = {}  # Track created IDs across agents to prevent race conditions
            for agent_name in agent_names:
                try:
                    agent = self.agent_factory.create_agent(agent_name)
                    
                    # Send agent header
                    await self.connection_manager.send_json({
                        "type": "stream_chunk",
                        "content": f"\n[AI] {agent.name.replace('_', ' ').title()}:\n"
                    }, client_id)
                    
                    # LoreGen supports multiple cycles for iterative expansion
                    if agent_name == "loregen":
                        # Check if multiple cycles were requested
                        cycles_requested = request.context.get('expansion_cycles', 1) if request.context else 1
                        
                        if cycles_requested > 1:
                            await self.connection_manager.send_json({
                                "type": "stream_chunk",
                                "content": f"Running {cycles_requested} cycles of iterative expansion...\n\n"
                            }, client_id)
                        
                        final_response = None
                        for cycle in range(cycles_requested):
                            if cycles_requested > 1:
                                await self.connection_manager.send_json({
                                    "type": "stream_chunk",
                                    "content": f"--- Cycle {cycle + 1}/{cycles_requested} ---\n"
                                }, client_id)
                            
                            response = await agent.process_request(request)
                            final_response = response  # Keep the last response
                            
                            # Send cycle response content
                            await self.connection_manager.send_json({
                                "type": "stream_chunk",
                                "content": response.content + "\n"
                            }, client_id)
                            
                            if cycles_requested > 1 and cycle < cycles_requested - 1:
                                await self.connection_manager.send_json({
                                    "type": "stream_chunk",
                                    "content": "Preparing next cycle...\n\n"
                                }, client_id)
                        
                        # Send final structured response (from last cycle)
                        if final_response and final_response.parsed_json:
                            # Update the response to include cycle information
                            final_json = final_response.parsed_json.copy()
                            if cycles_requested > 1:
                                final_json['total_cycles_completed'] = cycles_requested
                                
                            await self.connection_manager.send_json({
                                "type": "structured_response",
                                "agent": agent_name,
                                "json_data": final_json,
                                "raw_content": final_response.content
                            }, client_id)
                            
                            # Save to database (only final result) with context passing
                            try:
                                created_context = await self._save_agent_response_to_database(
                                    agent_name, 
                                    final_json, 
                                    session_id, 
                                    user_id,
                                    orchestrator_data,
                                    workflow_context  # Pass accumulated context
                                )
                                # Update workflow context with newly created IDs
                                workflow_context.update(created_context)
                                
                                await self.connection_manager.send_json({
                                    "type": "database_saved",
                                    "agent": agent_name,
                                    "message": f"{agent_name.replace('_', ' ').title()} saved to database"
                                }, client_id)
                                
                            except Exception as db_error:
                                self.logger.error(f"Failed to save {agent_name} to database: {db_error}")
                                await self.connection_manager.send_json({
                                    "type": "database_error", 
                                    "agent": agent_name,
                                    "error": f"Failed to save to database: {str(db_error)}"
                                }, client_id)
                    
                    else:
                        # Process with streaming for other agents
                        full_response = ""
                        async for chunk in agent.process_request_streaming(request):
                            if chunk.chunk:
                                full_response += chunk.chunk
                                await self.connection_manager.send_json({
                                    "type": "stream_chunk",
                                    "content": chunk.chunk
                                }, client_id)
                            
                            if chunk.is_complete:
                                # Try to extract structured data
                                response = await agent.process_request(request)
                                if response.parsed_json:
                                    await self.connection_manager.send_json({
                                        "type": "structured_response",
                                        "agent": agent_name,
                                        "json_data": response.parsed_json,
                                        "raw_content": full_response
                                    }, client_id)
                                    
                                    # Save to database with context passing
                                    try:
                                        created_context = await self._save_agent_response_to_database(
                                            agent_name, 
                                            response.parsed_json, 
                                            session_id, 
                                            user_id,
                                            orchestrator_data,
                                            workflow_context  # Pass accumulated context
                                        )
                                        # Update workflow context with newly created IDs
                                        workflow_context.update(created_context)
                                        
                                        await self.connection_manager.send_json({
                                            "type": "database_saved",
                                            "agent": agent_name,
                                            "message": f"{agent_name.replace('_', ' ').title()} saved to database"
                                        }, client_id)
                                        
                                    except Exception as db_error:
                                        self.logger.error(f"Failed to save {agent_name} to database: {db_error}")
                                        await self.connection_manager.send_json({
                                            "type": "database_error", 
                                            "agent": agent_name,
                                            "error": f"Failed to save to database: {str(db_error)}"
                                        }, client_id)
                                break
                
                except Exception as e:
                    self.logger.error(f"Error processing with agent {agent_name}: {e}", error=e)
                    await self.connection_manager.send_json({
                        "type": "stream_chunk",
                        "content": f"[ERROR] Failed to process with {agent_name}: {str(e)}\n\n"
                    }, client_id)
            
            # Send completion signal
            await self.connection_manager.send_json({
                "type": "stream_end",
                "workflow_completed": True
            }, client_id)
            
        except Exception as e:
            self.logger.error(f"Error in agent message handling: {e}", error=e)
            await self.connection_manager.send_json({
                "type": "error",
                "error": "Failed to process message through multi-agent system"
            }, client_id)
    
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