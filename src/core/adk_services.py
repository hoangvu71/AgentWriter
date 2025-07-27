"""
ADK service configuration for persistent runners and memory management.
"""

import os
from typing import Optional, Any
from enum import Enum
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from .logging import get_logger
from .configuration import Configuration

logger = get_logger("adk_services")


class ServiceMode(Enum):
    """ADK service modes for different deployment scenarios"""
    DEVELOPMENT = "development"  # In-memory services for local dev
    DATABASE = "database"        # Database-backed persistent services
    VERTEX_AI = "vertex_ai"      # Cloud-based Vertex AI services


class ADKServiceFactory:
    """Factory for creating ADK services based on configuration"""
    
    def __init__(self, config: Configuration):
        self.config = config
        self.service_mode = self._determine_service_mode()
        logger.info(f"ADK Service Mode: {self.service_mode.value}")
    
    def _determine_service_mode(self) -> ServiceMode:
        """Determine which service mode to use based on environment"""
        
        # Check environment variables first
        mode = os.getenv("ADK_SERVICE_MODE", "").lower()
        if mode in [m.value for m in ServiceMode]:
            return ServiceMode(mode)
        
        # Check if we're in production (has database config)
        # Enable database mode for persistence
        if hasattr(self.config, 'database_url') and self.config.database_url:
            return ServiceMode.DATABASE
        
        # Check if Vertex AI is configured
        vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        vertex_location = os.getenv("GOOGLE_CLOUD_LOCATION")
        if vertex_project and vertex_location:
            return ServiceMode.VERTEX_AI
        
        # Default to development mode
        return ServiceMode.DEVELOPMENT
    
    def create_session_service(self):
        """Create appropriate session service based on mode"""
        
        if self.service_mode == ServiceMode.DEVELOPMENT:
            logger.info("Using InMemorySessionService for development")
            return InMemorySessionService()
        
        elif self.service_mode == ServiceMode.DATABASE:
            logger.info("Using DatabaseSessionService for persistence")
            return self._create_database_session_service()
        
        elif self.service_mode == ServiceMode.VERTEX_AI:
            logger.info("Using VertexAiSessionService for cloud persistence")
            return self._create_vertex_session_service()
        
        else:
            logger.warning(f"Unknown service mode {self.service_mode}, falling back to in-memory")
            return InMemorySessionService()
    
    def create_memory_service(self):
        """Create appropriate memory service based on mode"""
        
        if self.service_mode == ServiceMode.DEVELOPMENT:
            logger.info("Using InMemoryMemoryService for development")
            return InMemoryMemoryService()
        
        elif self.service_mode == ServiceMode.DATABASE:
            logger.info("Using DatabaseMemoryService for persistence")
            return self._create_database_memory_service()
        
        elif self.service_mode == ServiceMode.VERTEX_AI:
            logger.info("Using VertexAiMemoryBankService for cloud persistence")
            return self._create_vertex_memory_service()
        
        else:
            logger.warning(f"Unknown service mode {self.service_mode}, falling back to in-memory")
            return InMemoryMemoryService()
    
    def create_runner(self, agent, app_name: str):
        """Create appropriate runner with configured services"""
        
        if self.service_mode == ServiceMode.DEVELOPMENT:
            # Use simple InMemoryRunner for development
            logger.info("Creating InMemoryRunner for development")
            return InMemoryRunner(agent, app_name=app_name)
        
        else:
            # Use full Runner with persistent services
            logger.info("Creating persistent Runner with session and memory services")
            return self._create_persistent_runner(agent, app_name)
    
    def _create_database_session_service(self):
        """Create database-backed session service"""
        try:
            # Try to import database session service
            from google.adk.sessions import DatabaseSessionService
            
            # ADK services need a proper database URL, not HTTP endpoint
            # For now, use SQLite for ADK persistence
            database_url = "sqlite:///adk_sessions.db"
            
            return DatabaseSessionService(db_url=database_url)
            
        except ImportError:
            logger.warning("DatabaseSessionService not available, falling back to in-memory")
            return InMemorySessionService()
        except Exception as e:
            logger.error(f"Failed to create DatabaseSessionService: {e}")
            return InMemorySessionService()
    
    def _create_database_memory_service(self):
        """Create database-backed memory service"""
        try:
            # Try to import database memory service (if available)
            from google.adk.memory import DatabaseMemoryService
            
            database_url = "sqlite:///adk_sessions.db"
            
            return DatabaseMemoryService(db_url=database_url)
            
        except ImportError:
            logger.info("DatabaseMemoryService not available in this ADK version, using in-memory")
            return InMemoryMemoryService()
        except Exception as e:
            logger.info(f"DatabaseMemoryService not configured, using in-memory: {e}")
            return InMemoryMemoryService()
    
    def _create_vertex_session_service(self):
        """Create Vertex AI session service"""
        try:
            from google.adk.sessions import VertexAiSessionService
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            
            if not project_id:
                logger.warning("No Google Cloud project configured, falling back to in-memory")
                return InMemorySessionService()
            
            return VertexAiSessionService(
                project=project_id,
                location=location
            )
            
        except ImportError:
            logger.warning("VertexAiSessionService not available, falling back to in-memory")
            return InMemorySessionService()
        except Exception as e:
            logger.error(f"Failed to create VertexAiSessionService: {e}")
            return InMemorySessionService()
    
    def _create_vertex_memory_service(self):
        """Create Vertex AI Memory Bank service"""
        try:
            from google.adk.memory import VertexAiMemoryBankService
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            agent_engine_id = os.getenv("VERTEX_AI_AGENT_ENGINE_ID")
            
            if not all([project_id, agent_engine_id]):
                logger.warning("Vertex AI not fully configured, falling back to in-memory")
                return InMemoryMemoryService()
            
            return VertexAiMemoryBankService(
                project=project_id,
                location=location,
                agent_engine_id=agent_engine_id
            )
            
        except ImportError:
            logger.warning("VertexAiMemoryBankService not available, falling back to in-memory")
            return InMemoryMemoryService()
        except Exception as e:
            logger.error(f"Failed to create VertexAiMemoryBankService: {e}")
            return InMemoryMemoryService()
    
    def _create_persistent_runner(self, agent, app_name: str):
        """Create runner with persistent services"""
        try:
            from google.adk.runners import Runner
            
            session_service = self.create_session_service()
            memory_service = self.create_memory_service()
            
            return Runner(
                agent=agent,
                session_service=session_service,
                memory_service=memory_service,
                app_name=app_name
            )
            
        except ImportError:
            logger.warning("Persistent Runner not available, falling back to InMemoryRunner")
            return InMemoryRunner(agent, app_name=app_name)
        except Exception as e:
            logger.error(f"Failed to create persistent Runner: {e}")
            return InMemoryRunner(agent, app_name=app_name)


def get_adk_service_factory(config: Configuration) -> ADKServiceFactory:
    """Get global ADK service factory instance"""
    return ADKServiceFactory(config)