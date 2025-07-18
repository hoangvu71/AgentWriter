"""
WebSocket message handler for multi-agent system communication.
"""

import json
from typing import Dict, Any
from fastapi import WebSocket
from ..core.interfaces import AgentRequest
from ..core.configuration import Configuration
from ..core.validation import Validator, ValidationError
from ..core.logging import get_logger
from ..websocket.connection_manager import ConnectionManager
from ..agents.agent_factory import AgentFactory


class WebSocketHandler:
    """Handles WebSocket messages and coordinates with multi-agent system"""
    
    def __init__(self, connection_manager: ConnectionManager, agent_factory: AgentFactory, config: Configuration):
        self.connection_manager = connection_manager
        self.agent_factory = agent_factory
        self.config = config
        self.validator = Validator()
        self.logger = get_logger("websocket.handler")
    
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
            except Exception as e:
                self.logger.error(f"Error in message loop for {client_id}: {e}", error=e)
                await self.connection_manager.send_json({
                    "type": "error",
                    "error": "Message processing failed"
                }, client_id)
                break
        
        # Clean up connection
        self.connection_manager.disconnect(client_id)
    
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
            
            # Route the request
            agent_names = await orchestrator.route_request(request)
            
            # Send routing information
            await self.connection_manager.send_json({
                "type": "workflow_start",
                "agents_to_invoke": agent_names,
                "orchestrator_decision": "Multi-agent workflow initiated"
            }, client_id)
            
            # Process through each agent
            for agent_name in agent_names:
                try:
                    agent = self.agent_factory.create_agent(agent_name)
                    
                    # Send agent header
                    await self.connection_manager.send_json({
                        "type": "stream_chunk",
                        "content": f"\n[AI] {agent.name.replace('_', ' ').title()}:\n"
                    }, client_id)
                    
                    # Process with streaming
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