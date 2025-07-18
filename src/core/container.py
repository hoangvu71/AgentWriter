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
    
    def _create_database_adapter(self):
        """Create database adapter instance"""
        from ..database.supabase_adapter import supabase_adapter
        return supabase_adapter
    
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
            if name in ["config", "validator"]:  # Known singletons
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
    
    def clear(self) -> None:
        """Clear all services (useful for testing)"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._register_core_services()


# Global container instance
container = ServiceContainer()