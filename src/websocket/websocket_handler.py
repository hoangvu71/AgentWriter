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
                 plot_repository=None, author_repository=None, world_building_repository=None, characters_repository=None):
        self.connection_manager = connection_manager
        self.agent_factory = agent_factory
        self.config = config
        self.validator = Validator()
        self.logger = get_logger("websocket.handler")
        
        # Store repositories
        self.plot_repository = plot_repository
        self.author_repository = author_repository
        self.world_building_repository = world_building_repository
        self.characters_repository = characters_repository
    
    async def _save_plot_data(self, session_id: str, user_id: str, plot_data: Dict[str, Any], 
                             orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Helper method to save plot data using repository if available, fallback to supabase_service
        Returns the saved plot data including the created ID for context passing"""
        if self.plot_repository is not None:
            try:
                # Transform dictionary data to Plot entity
                from ..models.entities import Plot
                plot_entity = Plot(
                    session_id=session_id,
                    user_id=user_id,
                    title=plot_data.get("title", ""),
                    plot_summary=plot_data.get("plot_summary", "")
                    # Note: author_id would come from orchestrator_params if available
                )
                
                # Save using repository
                plot_id = await self.plot_repository.create(plot_entity)
                
                # Return format compatible with existing code
                return {
                    "id": plot_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    **plot_data
                }
            except Exception as e:
                self.logger.warning(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_plot(session_id, user_id, plot_data, orchestrator_params)
    
    async def _save_author_data(self, session_id: str, user_id: str, author_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to save author data using repository if available, fallback to supabase_service
        Returns the saved author data including the created ID for context passing"""
        if self.author_repository is not None:
            try:
                # Transform dictionary data to Author entity
                from ..models.entities import Author
                author_entity = Author(
                    session_id=session_id,
                    user_id=user_id,
                    author_name=author_data.get("author_name", ""),
                    pen_name=author_data.get("pen_name"),
                    biography=author_data.get("biography", ""),
                    writing_style=author_data.get("writing_style", "")
                )
                
                # Save using repository
                author_id = await self.author_repository.create(author_entity)
                
                # Return format compatible with existing code
                return {
                    "id": author_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    **author_data
                }
            except Exception as e:
                self.logger.warning(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_author(session_id, user_id, author_data)
    
    async def _save_world_building_data(self, session_id: str, user_id: str, world_data: Dict[str, Any], 
                                       orchestrator_params: Dict[str, Any] = None, plot_id: str = None) -> Dict[str, Any]:
        """Helper method to save world building data using repository if available, fallback to supabase_service
        Returns the saved world building data including the created ID for context passing"""
        if self.world_building_repository is not None:
            try:
                # Transform dictionary data to WorldBuilding entity
                from ..models.entities import WorldBuilding
                
                # Extract world content - could be nested in various formats
                world_content = ""
                if isinstance(world_data.get("world_building"), str):
                    world_content = world_data["world_building"]
                elif isinstance(world_data.get("world_description"), str):
                    world_content = world_data["world_description"]
                else:
                    # Fallback to string representation of the whole data
                    world_content = str(world_data)
                
                world_entity = WorldBuilding(
                    session_id=session_id,
                    user_id=user_id,
                    plot_id=plot_id,
                    world_name=world_data.get("world_name", "Unnamed World"),
                    world_type=world_data.get("world_type", "unknown"),
                    world_content=world_content
                )
                
                # Save using repository
                world_id = await self.world_building_repository.create(world_entity)
                
                # Return format compatible with existing code
                return {
                    "id": world_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "plot_id": plot_id,
                    **world_data
                }
            except Exception as e:
                self.logger.warning(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_world_building(session_id, user_id, world_data, orchestrator_params, plot_id)
    
    async def _save_characters_data(self, session_id: str, user_id: str, characters_data: Dict[str, Any], 
                                   orchestrator_params: Dict[str, Any] = None, world_id: str = None, plot_id: str = None) -> Dict[str, Any]:
        """Helper method to save characters data using repository if available, fallback to supabase_service
        Returns the saved characters data including the created ID for context passing"""
        if self.characters_repository is not None:
            try:
                # Transform dictionary data to Characters entity
                from ..models.entities import Characters
                
                # Extract character list and relationships
                characters_list = characters_data.get("characters", [])
                if isinstance(characters_list, str):
                    # If it's a string, try to parse as JSON or treat as single character
                    import json
                    try:
                        characters_list = json.loads(characters_list)
                    except:
                        characters_list = [{"name": "Character", "description": characters_list}]
                
                characters_entity = Characters(
                    session_id=session_id,
                    user_id=user_id,
                    world_id=world_id,
                    plot_id=plot_id,
                    character_count=len(characters_list) if isinstance(characters_list, list) else 1,
                    world_context_integration=characters_data.get("world_context_integration", ""),
                    characters=characters_list,
                    relationship_networks=characters_data.get("relationship_networks", {}),
                    character_dynamics=characters_data.get("character_dynamics", {})
                )
                
                # Save using repository
                characters_id = await self.characters_repository.create(characters_entity)
                
                # Return format compatible with existing code
                return {
                    "id": characters_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "world_id": world_id,
                    "plot_id": plot_id,
                    **characters_data
                }
            except Exception as e:
                self.logger.warning(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_characters(session_id, user_id, characters_data, orchestrator_params, world_id, plot_id)
    
    async def _save_critique_data(self, iteration_id: str, critique_json: Dict[str, Any], agent_response: str) -> None:
        """Helper method to save critique data using repository if available, fallback to supabase_service"""
        # TODO: Implement repository-based saving when critique repository is available
        # For now, fallback to original method
        return await supabase_service.save_critique_data(iteration_id, critique_json, agent_response)
    
    async def _save_enhancement_data(self, iteration_id: str, enhanced_content: str, changes_made: Dict[str, Any], 
                                   rationale: str, confidence_score: float) -> None:
        """Helper method to save enhancement data using repository if available, fallback to supabase_service"""
        # TODO: Implement repository-based saving when enhancement repository is available
        # For now, fallback to original method
        return await supabase_service.save_enhancement_data(iteration_id, enhanced_content, changes_made, rationale, confidence_score)
    
    async def _save_score_data(self, iteration_id: str, overall_score: float, category_scores: Dict[str, Any], 
                             score_rationale: str, improvement_trajectory: str, recommendations: str) -> None:
        """Helper method to save score data using repository if available, fallback to supabase_service"""
        # TODO: Implement repository-based saving when scoring repository is available
        # For now, fallback to original method
        return await supabase_service.save_score_data(iteration_id, overall_score, category_scores, score_rationale, improvement_trajectory, recommendations)
    
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
        """Save agent response to appropriate database table with explicit context passing
        
        Args:
            context: Dictionary containing IDs from previous agents (plot_id, world_id, author_id)
            
        Returns:
            Dictionary containing the created record ID for use by subsequent agents
        """
        if context is None:
            context = {}
            
        created_context = {}
        
        try:
            if agent_name == "plot_generator":
                saved_plot = await self._save_plot_data(
                    session_id=session_id,
                    user_id=user_id,
                    plot_data=response_data,
                    orchestrator_params=orchestrator_data
                )
                # Extract plot ID for context passing
                created_context["plot_id"] = saved_plot.get("id")
                
            elif agent_name == "author_generator":
                saved_author = await self._save_author_data(
                    session_id=session_id,
                    user_id=user_id,
                    author_data=response_data
                )
                # Extract author ID for context passing
                created_context["author_id"] = saved_author.get("id")
                
            elif agent_name == "world_building":
                # FIXED: Use explicit plot_id from context instead of fetching "recent"
                plot_id = context.get("plot_id")
                if not plot_id:
                    self.logger.warning("No plot_id in context for world_building - using fallback")
                    plot_id = await self._get_recent_plot_id(session_id, user_id)
                    
                saved_world = await self._save_world_building_data(
                    session_id=session_id,
                    user_id=user_id,
                    world_data=response_data,
                    orchestrator_params=orchestrator_data,
                    plot_id=plot_id
                )
                # Extract world ID for context passing
                created_context["world_id"] = saved_world.get("id")
                
            elif agent_name == "characters":
                # FIXED: Use explicit IDs from context instead of fetching "recent"
                plot_id = context.get("plot_id")
                world_id = context.get("world_id")
                
                if not plot_id:
                    self.logger.warning("No plot_id in context for characters - using fallback")
                    plot_id = await self._get_recent_plot_id(session_id, user_id)
                    
                if not world_id:
                    self.logger.warning("No world_id in context for characters - using fallback")
                    world_id = await self._get_recent_world_id(session_id, user_id)
                    
                saved_characters = await self._save_characters_data(
                    session_id=session_id,
                    user_id=user_id,
                    characters_data=response_data,
                    orchestrator_params=orchestrator_data,
                    world_id=world_id,
                    plot_id=plot_id
                )
                # Extract characters ID for context passing
                created_context["characters_id"] = saved_characters.get("id")
                
            elif agent_name == "critique":
                # For critique, we'll create a basic improvement iteration
                try:
                    await self._save_critique_data(
                        iteration_id=f"{session_id}_{user_id}_{agent_name}",
                        critique_json=response_data,
                        agent_response=str(response_data)
                    )
                    self.logger.info(f"Saved {agent_name} to database")
                except Exception as e:
                    self.logger.error(f"Error saving {agent_name}: {e}")
                    
            elif agent_name == "enhancement":
                # For enhancement, we'll create a basic improvement iteration
                try:
                    await self._save_enhancement_data(
                        iteration_id=f"{session_id}_{user_id}_{agent_name}",
                        enhanced_content=response_data.get("enhanced_content", ""),
                        changes_made=response_data.get("improvements_made", {}),
                        rationale=response_data.get("enhancement_rationale", ""),
                        confidence_score=8  # Default confidence score
                    )
                    self.logger.info(f"Saved {agent_name} to database")
                except Exception as e:
                    self.logger.error(f"Error saving {agent_name}: {e}")
                    
            elif agent_name == "scoring":
                # For scoring, save scoring data
                try:
                    category_scores = {
                        "content_quality": float(response_data.get("content_quality_score", 0)),
                        "structure": float(response_data.get("structure_score", 0)),
                        "writing_style": float(response_data.get("writing_style_score", 0)),
                        "genre_appropriateness": float(response_data.get("genre_appropriateness_score", 0)),
                        "technical_execution": float(response_data.get("technical_execution_score", 0))
                    }
                    
                    await self._save_score_data(
                        iteration_id=f"{session_id}_{user_id}_{agent_name}",
                        overall_score=float(response_data.get("overall_score", 0)),
                        category_scores=category_scores,
                        score_rationale=response_data.get("scoring_rationale", ""),
                        improvement_trajectory="Initial scoring",
                        recommendations=response_data.get("improvement_suggestions", "")
                    )
                    self.logger.info(f"Saved {agent_name} to database")
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error parsing scores for {agent_name}: {e}")
                except Exception as e:
                    self.logger.error(f"Error saving {agent_name}: {e}")
                
            else:
                self.logger.warning(f"No database save method configured for agent: {agent_name}")
                
        except Exception as e:
            self.logger.error(f"Database save error for {agent_name}: {e}")
            raise
            
        return created_context
    
    async def _get_recent_plot_id(self, session_id: str, user_id: str) -> str:
        """Get the most recently created plot ID for this session
        
        DEPRECATED: This method is unsafe in concurrent environments and can cause race conditions.
        Use explicit context passing instead via the workflow_context parameter.
        """
        self.logger.warning("DEPRECATED: _get_recent_plot_id() called - use explicit context passing instead")
        try:
            session_data = await supabase_service.get_session_data(session_id)
            plots = session_data.get("plots", [])
            if plots:
                # Return the most recent plot ID
                return plots[-1]["id"]
        except Exception as e:
            self.logger.warning(f"Could not get recent plot ID: {e}")
        return None
    
    async def _get_recent_world_id(self, session_id: str, user_id: str) -> str:
        """Get the most recently created world ID for this session
        
        DEPRECATED: This method is unsafe in concurrent environments and can cause race conditions.
        Use explicit context passing instead via the workflow_context parameter.
        """
        self.logger.warning("DEPRECATED: _get_recent_world_id() called - use explicit context passing instead")
        try:
            session_data = await supabase_service.get_session_data(session_id)
            # Would need to add world_building to session data query
            # For now, try to get from user's recent worlds
            worlds = await supabase_service.get_user_world_building(user_id, limit=1)
            if worlds:
                return worlds[0]["id"]
        except Exception as e:
            self.logger.warning(f"Could not get recent world ID: {e}")
        return None
    
    async def _process_message(self, client_id: str, session_id: str, message_data: Dict[str, Any]):
        """Process an incoming WebSocket message"""
        message_type = message_data.get("type", "message")
        content = message_data.get("content", "")
        user_id = message_data.get("user_id", "anonymous")
        
        try:
            # Validate inputs
            validated_content = self.validator.validate_text(content, max_length=50000)
            validated_user_id = self.validator.validate_alphanumeric(user_id, max_length=50)
            
            if message_type == "message":
                await self._handle_agent_message(client_id, session_id, validated_user_id, validated_content)
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
    
    async def _handle_agent_message(self, client_id: str, session_id: str, user_id: str, content: str):
        """Handle a message that should be processed by the multi-agent system"""
        try:
            # Create agent request
            request = AgentRequest(
                content=content,
                user_id=user_id,
                session_id=session_id
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