"""
Test startup utilities for E2E testing.
Provides graceful handling of service initialization in test mode.
"""

import os
import logging
import json
import time
import asyncio
from typing import Dict, Any
from .core.configuration import config
from .core.container import container
from .core.logging import get_logger
from .websocket.connection_manager import ConnectionManager

logger = get_logger("test_startup")

class MockAgentFactory:
    """Mock agent factory for testing"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Mock AgentFactory initialized for testing")
    
    def create_agent(self, agent_type: str, config=None):
        """Create a mock agent"""
        logger.info(f"Creating mock agent: {agent_type}")
        return MockAgent(agent_type)
    
    def get_available_agents(self):
        """Return list of available agents"""
        return [
            "orchestrator", "plot_generator", "author_generator",
            "world_building", "characters", "critique", "enhancement",
            "scoring", "loregen"
        ]

class MockAgent:
    """Mock agent for testing"""
    
    def __init__(self, agent_type: str):
        self.name = agent_type
        self.agent_type = agent_type
        logger.info(f"Mock agent {agent_type} initialized")
    
    async def process_request(self, request):
        """Mock request processing"""
        return {
            "agent_name": self.name,
            "content": f"Mock response from {self.name}",
            "success": True
        }

class MockWebSocketHandler:
    """Mock WebSocket handler for testing"""
    
    def __init__(self, connection_manager, agent_factory, config, content_saving_service, session_repository):
        self.connection_manager = connection_manager
        self.agent_factory = agent_factory
        self.config = config
        self.content_saving_service = content_saving_service
        self.session_repository = session_repository
        logger.info("Mock WebSocketHandler initialized for testing")
    
    async def handle_connection(self, websocket, session_id: str):
        """Mock WebSocket connection handling"""
        try:
            await websocket.accept()
            logger.info(f"Mock WebSocket connection accepted for session: {session_id}")
            
            while True:
                # Wait for messages
                try:
                    data = await websocket.receive_text()
                    logger.info(f"Mock WebSocket received message: {data}")
                    
                    # Parse message
                    try:
                        message = json.loads(data)
                    except json.JSONDecodeError:
                        message = {"type": "text", "content": data}
                    
                    # Mock response
                    response = await self.handle_message(websocket, message)
                    await websocket.send_text(json.dumps(response))
                    
                except Exception as e:
                    logger.error(f"Mock WebSocket message error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Mock WebSocket connection error: {e}")
            try:
                await websocket.close()
            except:
                pass
    
    async def handle_message(self, websocket, message):
        """Mock message handling"""
        import json
        
        message_type = message.get("type", "unknown")
        
        # Mock different message types
        if message_type == "ping":
            return {"type": "pong", "timestamp": time.time()}
        elif message_type == "agent_request":
            agent_type = message.get("agent_type", "plot_generator")
            content = message.get("content", "Test request")
            
            # Simulate agent processing
            await asyncio.sleep(0.1)  # Simulate processing time
            
            return {
                "type": "agent_response",
                "agent_type": agent_type,
                "content": f"Mock {agent_type} response for: {content}",
                "success": True,
                "timestamp": time.time()
            }
        else:
            return {
                "type": "response",
                "content": f"Mock response to {message_type}",
                "timestamp": time.time()
            }

async def test_startup_event():
    """Test-friendly startup event"""
    logger.info("Starting Multi-Agent Book Writer application (TEST MODE)")
    
    # Check if we're in test mode
    is_testing = os.getenv('TESTING_MODE', 'false').lower() == 'true'
    
    if is_testing:
        logger.info("Test mode detected - using mock services")
        
        # Use mock services in test mode
        try:
            # Try to get content saving service, but don't fail if it's not available
            try:
                content_saving_service = container.get("content_saving_service")
                logger.info("ContentSavingService loaded successfully")
            except Exception as e:
                logger.warning(f"ContentSavingService not available in test mode: {e}")
                content_saving_service = None
            
            # Register mock services
            container.register_instance("connection_manager", ConnectionManager())
            container.register_instance("agent_factory", MockAgentFactory(config))
            
            # Use mock WebSocket handler if content service is not available
            if content_saving_service is None:
                logger.info("Using mock WebSocketHandler for testing")
                mock_handler = MockWebSocketHandler(
                    connection_manager=container.get("connection_manager"),
                    agent_factory=container.get("agent_factory"),
                    config=config,
                    content_saving_service=None,
                    session_repository=None
                )
                container.register_instance("websocket_handler", mock_handler)
            else:
                # Use real WebSocket handler if services are available
                from .websocket.websocket_handler import WebSocketHandler
                websocket_handler = WebSocketHandler(
                    connection_manager=container.get("connection_manager"),
                    agent_factory=container.get("agent_factory"),
                    config=config,
                    content_saving_service=content_saving_service,
                    session_repository=container.get("session_repository")
                )
                container.register_instance("websocket_handler", websocket_handler)
            
            logger.info("Test mode startup complete")
            
        except Exception as e:
            logger.error(f"Test startup failed: {e}")
            # Don't raise in test mode - allow app to start with limited functionality
            logger.warning("Continuing startup with limited functionality")
    
    else:
        # Regular startup logic
        from .app import startup_event
        await startup_event()

def create_test_health_response() -> Dict[str, Any]:
    """Create test-friendly health response"""
    
    is_testing = os.getenv('TESTING_MODE', 'false').lower() == 'true'
    
    try:
        agent_factory = container.get("agent_factory")
        available_agents = agent_factory.get_available_agents()
    except Exception:
        available_agents = ["test_agent"] if is_testing else []
    
    return {
        "status": "healthy",
        "service": "multi_agent_book_writer",
        "version": "2.0.0",
        "mode": "test" if is_testing else "production",
        "config": {
            "model": config.model_name,
            "supabase_enabled": config.is_supabase_enabled(),
            "google_cloud_enabled": config.is_google_cloud_enabled(),
            "testing_mode": is_testing
        },
        "agents": available_agents
    }