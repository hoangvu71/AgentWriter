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
    
    def _create_database_adapter(self):
        """Create database adapter instance with automatic fallback"""
        from ..database.database_factory import db_factory
        import asyncio
        
        # Try to get adapter asynchronously if possible
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, return sync adapter
                return db_factory.get_sync_adapter()
            else:
                # If no loop is running, create one to check connectivity
                return asyncio.run(db_factory.get_adapter())
        except RuntimeError:
            # Fallback to sync adapter if async not available
            return db_factory.get_sync_adapter()
    
    def _create_plot_repository(self):
        """Create plot repository instance"""
        from ..repositories.plot_repository import PlotRepository
        database = self.get("database")
        return PlotRepository(database)
    
    def _create_author_repository(self):
        """Create author repository instance"""
        from ..repositories.author_repository import AuthorRepository
        database = self.get("database")
        return AuthorRepository(database)
    
    def _create_world_building_repository(self):
        """Create world building repository instance"""
        from ..repositories.world_building_repository import WorldBuildingRepository
        database = self.get("database")
        return WorldBuildingRepository(database)
    
    def _create_characters_repository(self):
        """Create characters repository instance"""
        from ..repositories.characters_repository import CharactersRepository
        database = self.get("database")
        return CharactersRepository(database)
    
    def _create_session_repository(self):
        """Create session repository instance"""
        from ..repositories.session_repository import SessionRepository
        database = self.get("database")
        return SessionRepository(database)
    
    def _create_orchestrator_repository(self):
        """Create orchestrator repository instance"""
        from ..repositories.orchestrator_repository import OrchestratorRepository
        database = self.get("database")
        return OrchestratorRepository(database)
    
    def _create_iterative_repository(self):
        """Create iterative repository instance"""
        from ..repositories.iterative_repository import IterativeRepository
        database = self.get("database")
        return IterativeRepository(database)
    
    def _create_content_saving_service(self):
        """Create content saving service instance"""
        from ..services.content_saving_service import ContentSavingService
        return ContentSavingService(
            plot_repository=self.get("plot_repository"),
            author_repository=self.get("author_repository"),
            world_building_repository=self.get("world_building_repository"),
            characters_repository=self.get("characters_repository"),
            session_repository=self.get("session_repository"),
            iterative_repository=self.get("iterative_repository")
        )
    
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
                       "orchestrator_repository", "iterative_repository", "content_saving_service"]:  # Known singletons
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
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._register_core_services()
        self._validate_core_services()


# Global container instance
container = ServiceContainer()