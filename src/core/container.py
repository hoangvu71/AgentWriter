"""
Dependency injection container for the multi-agent book writing system.
"""

from typing import Dict, Any, Type, TypeVar, Callable, Optional
from .interfaces import IConfiguration, IDatabase, ILogger, IValidator
from .configuration import Configuration
from .logging import get_logger
from .validation import Validator

T = TypeVar('T')


class ServiceContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        
        # Session context for tool usage
        self._current_session_id: Optional[str] = None
        self._current_user_id: Optional[str] = None
        
        # Register core services
        self._register_core_services()
        
        # Add fail-fast error handling for required services
        self._validate_core_services()
    
    def _register_core_services(self):
        """Register core system services"""
        # Configuration
        self.register_singleton("config", lambda: Configuration())
        
        # Logger factory
        self.register_factory("logger", lambda name: get_logger(name))
        
        # Validator
        self.register_singleton("validator", lambda: Validator())
        
        # Database services
        self.register_singleton("database", self._create_database_adapter)
        self.register_singleton("plot_repository", self._create_plot_repository)
        self.register_singleton("author_repository", self._create_author_repository)
        self.register_singleton("world_building_repository", self._create_world_building_repository)
        self.register_singleton("characters_repository", self._create_characters_repository)
        self.register_singleton("session_repository", self._create_session_repository)
        
        # Additional repositories
        self.register_singleton("orchestrator_repository", self._create_orchestrator_repository)
        self.register_singleton("iterative_repository", self._create_iterative_repository)
        
        # Content saving service
        self.register_singleton("content_saving_service", self._create_content_saving_service)
        
        # Agent factory
        self.register_singleton("agent_factory", self._create_agent_factory)
    
    def _create_database_adapter(self):
        """Create database adapter instance with connection pooling"""
        from src.database.database_factory import DatabaseFactory
        from src.database.connection_pool import ConnectionPoolConfig
        from src.core.configuration import config
        import os
        
        # Connection pool configuration
        pool_config = ConnectionPoolConfig(
            min_connections=int(os.getenv("DB_POOL_MIN_CONNECTIONS", "3")),
            max_connections=int(os.getenv("DB_POOL_MAX_CONNECTIONS", "15")),
            max_idle_time=int(os.getenv("DB_POOL_MAX_IDLE_TIME", "300")),
            connection_timeout=int(os.getenv("DB_POOL_CONNECTION_TIMEOUT", "30")),
            health_check_interval=int(os.getenv("DB_POOL_HEALTH_CHECK_INTERVAL", "60")),
            enable_metrics=os.getenv("DB_POOL_ENABLE_METRICS", "true").lower() == "true"
        )
        
        # Force Supabase when DATABASE_MODE is set to supabase
        database_mode = os.getenv("DATABASE_MODE", "supabase").lower()
        
        if database_mode == "supabase" and config.supabase_config.get("url") and config.supabase_config.get("anon_key"):
            # Create Supabase adapter with connection pooling
            from src.database.supabase_adapter import SupabaseAdapter
            import logging
            logger = logging.getLogger("container")
            logger.info("Creating Supabase adapter with connection pooling for database")
            adapter = SupabaseAdapter(
                url=config.supabase_config["url"],
                key=config.supabase_config["anon_key"],
                pool_config=pool_config
            )
            # Start background tasks
            import asyncio
            asyncio.create_task(adapter.start_background_tasks())
            return adapter
        else:
            # Fallback to SQLite with connection pooling
            from src.database.sqlite.adapter import SQLiteAdapter
            import logging
            logger = logging.getLogger("container")
            logger.info("Creating SQLite adapter with connection pooling for database")
            db_path = os.getenv("SQLITE_DB_PATH", "development.db")
            adapter = SQLiteAdapter(db_path, pool_config)
            return adapter
    
    def _create_plot_repository(self):
        """Create plot repository instance"""
        from src.repositories.plot_repository import PlotRepository
        database = self.get("database")
        return PlotRepository(database)
    
    def _create_author_repository(self):
        """Create author repository instance"""
        from src.repositories.author_repository import AuthorRepository
        database = self.get("database")
        return AuthorRepository(database)
    
    def _create_world_building_repository(self):
        """Create world building repository instance"""
        from src.repositories.world_building_repository import WorldBuildingRepository
        database = self.get("database")
        return WorldBuildingRepository(database)
    
    def _create_characters_repository(self):
        """Create characters repository instance"""
        from src.repositories.characters_repository import CharactersRepository
        database = self.get("database")
        return CharactersRepository(database)
    
    def _create_session_repository(self):
        """Create session repository instance"""
        from src.repositories.session_repository import SessionRepository
        database = self.get("database")
        return SessionRepository(database)
    
    def _create_orchestrator_repository(self):
        """Create orchestrator repository instance"""
        from src.repositories.orchestrator_repository import OrchestratorRepository
        database = self.get("database")
        return OrchestratorRepository(database)
    
    def _create_iterative_repository(self):
        """Create iterative repository instance"""
        from src.repositories.iterative_repository import IterativeRepository
        database = self.get("database")
        return IterativeRepository(database)
    
    def _create_content_saving_service(self):
        """Create content saving service instance"""
        from src.services.content_saving_service import ContentSavingService
        return ContentSavingService(
            plot_repository=self.get("plot_repository"),
            author_repository=self.get("author_repository"),
            world_building_repository=self.get("world_building_repository"),
            characters_repository=self.get("characters_repository"),
            session_repository=self.get("session_repository"),
            iterative_repository=self.get("iterative_repository")
        )
    
    def _create_agent_factory(self):
        """Create agent factory instance"""
        from src.agents.agent_factory import AgentFactory
        config = self.get("config")
        return AgentFactory(config)
    
    def register_singleton(self, name: str, factory: Callable[[], T]) -> None:
        """Register a singleton service"""
        self._factories[name] = factory
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function"""
        self._factories[name] = factory
    
    def register_instance(self, name: str, instance: Any) -> None:
        """Register a pre-created instance"""
        self._services[name] = instance
    
    def get(self, name: str, *args, **kwargs) -> Any:
        """Get a service instance"""
        # Check for pre-registered instances
        if name in self._services:
            return self._services[name]
        
        # Check for singletons
        if name in self._singletons:
            return self._singletons[name]
        
        # Check for factories
        if name in self._factories:
            factory = self._factories[name]
            
            # For singletons, cache the result
            if name in ["config", "validator", "database", "plot_repository", "author_repository", 
                       "world_building_repository", "characters_repository", "session_repository", 
                       "orchestrator_repository", "iterative_repository", "content_saving_service",
                       "agent_factory"]:  # Known singletons
                instance = factory()
                self._singletons[name] = instance
                return instance
            
            # For factories, create new instance each time
            return factory(*args, **kwargs)
        
        raise KeyError(f"Service '{name}' not registered")
    
    def get_config(self) -> Configuration:
        """Get configuration instance"""
        return self.get("config")
    
    def get_logger(self, name: str):
        """Get logger instance"""
        return self.get("logger", name)
    
    def get_validator(self):
        """Get validator instance"""
        return self.get("validator")
    
    def has_service(self, name: str) -> bool:
        """Check if a service is registered"""
        return (name in self._services or 
                name in self._singletons or 
                name in self._factories)
    
    def _validate_core_services(self) -> None:
        """Validate that all required core services are properly registered"""
        required_services = [
            "database", "plot_repository", "author_repository", 
            "world_building_repository", "characters_repository", 
            "session_repository", "orchestrator_repository", "iterative_repository",
            "content_saving_service"
        ]
        
        for service_name in required_services:
            if not self.has_service(service_name):
                raise ValueError(f"Required service '{service_name}' is not registered in container")
    
    def clear(self) -> None:
        """Clear all services (useful for testing)"""
        # Close database adapter if it has connection pools
        if "database" in self._singletons:
            adapter = self._singletons["database"]
            if hasattr(adapter, 'close'):
                import asyncio
                asyncio.create_task(adapter.close())
        
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._current_session_id = None
        self._current_user_id = None
        self._register_core_services()
        self._validate_core_services()
    
    def set_session_context(self, session_id: str, user_id: str) -> None:
        """Set current session context for tools"""
        self._current_session_id = session_id
        self._current_user_id = user_id
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self._current_session_id
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self._current_user_id
    
    def clear_session_context(self) -> None:
        """Clear session context"""
        self._current_session_id = None
        self._current_user_id = None
    
    # Convenience methods for common services
    def plot_repository(self):
        """Get plot repository instance"""
        return self.get("plot_repository")
    
    def author_repository(self):
        """Get author repository instance"""
        return self.get("author_repository")
    
    def world_building_repository(self):
        """Get world building repository instance"""
        return self.get("world_building_repository")
    
    def characters_repository(self):
        """Get characters repository instance"""
        return self.get("characters_repository")
    
    def session_repository(self):
        """Get session repository instance"""
        return self.get("session_repository")
    
    def agent_factory(self):
        """Get agent factory instance"""
        return self.get("agent_factory")
    
    async def get_database_metrics(self) -> Dict[str, Any]:
        """Get database connection pool metrics"""
        try:
            database = self.get("database")
            if hasattr(database, 'get_pool_metrics'):
                return await database.get_pool_metrics()
            return {}
        except Exception as e:
            logger = get_logger("container")
            logger.error(f"Error getting database metrics: {e}")
            return {}
    
    async def reset_database_metrics(self):
        """Reset database connection pool metrics"""
        try:
            database = self.get("database")
            if hasattr(database, 'reset_pool_metrics'):
                await database.reset_pool_metrics()
        except Exception as e:
            logger = get_logger("container")
            logger.error(f"Error resetting database metrics: {e}")
    
    async def close_database_connections(self):
        """Close all database connections gracefully"""
        try:
            database = self.get("database")
            if hasattr(database, 'close'):
                await database.close()
        except Exception as e:
            logger = get_logger("container")
            logger.error(f"Error closing database connections: {e}")


# Global container instance
container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global container instance"""
    return container