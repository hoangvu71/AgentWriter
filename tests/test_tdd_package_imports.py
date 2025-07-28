"""
TDD tests for package import cleanup.

This test file follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to pass tests  
3. REFACTOR: Improve while keeping tests green

Tests ensure that:
- All entity classes can be imported from src.models
- All agent classes can be imported from src.agents
- Core interfaces and base classes can be imported from src.core
- Service classes can be imported from src.services
- Repository classes can be imported from src.repositories
- Backward compatibility is maintained
"""

import pytest
import sys
import importlib
from typing import Any


class TestPackageImportsBeforeChanges:
    """
    Tests to validate current import behavior before making changes.
    These tests document the current state and ensure we don't break anything.
    """
    
    def test_current_direct_imports_work(self):
        """Test that current direct imports still work."""
        # These imports should work as they do now
        from src.models.entities import Plot, Author, WorldBuilding, Characters, User, Session
        from src.agents.agent_factory import AgentFactory
        from src.agents.plot_generator import PlotGeneratorAgent
        from src.core.base_agent import BaseAgent
        from src.core.interfaces import IAgent
        
        # Verify classes are accessible
        assert Plot is not None
        assert Author is not None
        assert AgentFactory is not None
        assert PlotGeneratorAgent is not None
        assert BaseAgent is not None
        assert IAgent is not None


class TestModelsPackageImports:
    """
    TDD tests for src.models package imports.
    
    RED phase: These tests will fail initially since __init__.py is empty.
    GREEN phase: Populate __init__.py to make tests pass.
    """
    
    def test_models_package_exposes_main_entities(self):
        """Test that main entity classes can be imported from src.models package."""
        # This will fail initially - this is the RED phase
        from src.models import Plot, Author, WorldBuilding, Characters
        
        # Verify classes are the correct types
        assert Plot.__name__ == 'Plot'
        assert Author.__name__ == 'Author'
        assert WorldBuilding.__name__ == 'WorldBuilding'
        assert Characters.__name__ == 'Characters'
    
    def test_models_package_exposes_user_session_entities(self):
        """Test that user and session entities can be imported from src.models."""
        from src.models import User, Session
        
        assert User.__name__ == 'User'
        assert Session.__name__ == 'Session'
    
    def test_models_package_exposes_genre_entities(self):
        """Test that genre-related entities can be imported from src.models."""
        from src.models import Genre, Subgenre, Microgenre, Trope, Tone, TargetAudience
        
        assert Genre.__name__ == 'Genre'
        assert Subgenre.__name__ == 'Subgenre'
        assert Microgenre.__name__ == 'Microgenre'
        assert Trope.__name__ == 'Trope'
        assert Tone.__name__ == 'Tone'
        assert TargetAudience.__name__ == 'TargetAudience'
    
    def test_models_package_exposes_system_entities(self):
        """Test that system entities can be imported from src.models."""
        from src.models import OrchestratorDecision, ImprovementSession, Iteration
        
        assert OrchestratorDecision.__name__ == 'OrchestratorDecision'
        assert ImprovementSession.__name__ == 'ImprovementSession'
        assert Iteration.__name__ == 'Iteration'
    
    def test_models_package_exposes_enums(self):
        """Test that enums can be imported from src.models."""
        from src.models import WorldType
        
        assert WorldType.__name__ == 'WorldType'
        # Test enum values
        assert hasattr(WorldType, 'HIGH_FANTASY')
        assert hasattr(WorldType, 'SCIENCE_FICTION')
    
    def test_models_package_has_all_list(self):
        """Test that src.models has __all__ defined with all entities."""
        import src.models as models
        
        # Should have __all__ defined
        assert hasattr(models, '__all__')
        
        # Should contain all main entities
        expected_entities = [
            'User', 'Session', 'Plot', 'Author', 'WorldBuilding', 'Characters',
            'Genre', 'Subgenre', 'Microgenre', 'Trope', 'Tone', 'TargetAudience',
            'OrchestratorDecision', 'ImprovementSession', 'Iteration', 'WorldType'
        ]
        
        for entity in expected_entities:
            assert entity in models.__all__, f"{entity} missing from __all__"


class TestAgentsPackageImports:
    """
    TDD tests for src.agents package imports.
    
    RED phase: These tests will fail initially since __init__.py is empty.
    GREEN phase: Populate __init__.py to make tests pass.
    """
    
    def test_agents_package_exposes_factory(self):
        """Test that AgentFactory can be imported from src.agents package."""
        from src.agents import AgentFactory
        
        assert AgentFactory.__name__ == 'AgentFactory'
    
    def test_agents_package_exposes_core_agents(self):
        """Test that core agent classes can be imported from src.agents."""
        from src.agents import (
            OrchestratorAgent, PlotGeneratorAgent, AuthorGeneratorAgent,
            WorldBuildingAgent, CharactersAgent
        )
        
        assert OrchestratorAgent.__name__ == 'OrchestratorAgent'
        assert PlotGeneratorAgent.__name__ == 'PlotGeneratorAgent'
        assert AuthorGeneratorAgent.__name__ == 'AuthorGeneratorAgent'
        assert WorldBuildingAgent.__name__ == 'WorldBuildingAgent'
        assert CharactersAgent.__name__ == 'CharactersAgent'
    
    def test_agents_package_exposes_enhancement_agents(self):
        """Test that enhancement agent classes can be imported from src.agents."""
        from src.agents import EnhancementAgent, CritiqueAgent, ScoringAgent, LoreGenAgent
        
        assert EnhancementAgent.__name__ == 'EnhancementAgent'
        assert CritiqueAgent.__name__ == 'CritiqueAgent'
        assert ScoringAgent.__name__ == 'ScoringAgent'
        assert LoreGenAgent.__name__ == 'LoreGenAgent'
    
    def test_agents_package_has_all_list(self):
        """Test that src.agents has __all__ defined with all agents."""
        import src.agents as agents
        
        # Should have __all__ defined
        assert hasattr(agents, '__all__')
        
        # Should contain all agents
        expected_agents = [
            'AgentFactory', 'OrchestratorAgent', 'PlotGeneratorAgent',
            'AuthorGeneratorAgent', 'WorldBuildingAgent', 'CharactersAgent',
            'EnhancementAgent', 'CritiqueAgent', 'ScoringAgent', 'LoreGenAgent'
        ]
        
        for agent in expected_agents:
            assert agent in agents.__all__, f"{agent} missing from __all__"


class TestCorePackageImports:
    """
    TDD tests for src.core package imports.
    
    RED phase: These tests will fail initially since __init__.py is empty.
    GREEN phase: Populate __init__.py to make tests pass.
    """
    
    def test_core_package_exposes_interfaces(self):
        """Test that core interfaces can be imported from src.core."""
        from src.core import IAgent, IAgentFactory, IOrchestrator, IDatabase
        
        assert IAgent.__name__ == 'IAgent'
        assert IAgentFactory.__name__ == 'IAgentFactory'
        assert IOrchestrator.__name__ == 'IOrchestrator'
        assert IDatabase.__name__ == 'IDatabase'
    
    def test_core_package_exposes_base_classes(self):
        """Test that base classes can be imported from src.core."""
        from src.core import BaseAgent, Configuration
        
        assert BaseAgent.__name__ == 'BaseAgent'
        assert Configuration.__name__ == 'Configuration'
    
    def test_core_package_exposes_container(self):
        """Test that container can be imported from src.core."""
        from src.core import container
        
        assert container is not None
    
    def test_core_package_has_all_list(self):
        """Test that src.core has __all__ defined."""
        import src.core as core
        
        # Should have __all__ defined
        assert hasattr(core, '__all__')
        
        # Should contain core components
        expected_core = [
            'IAgent', 'IAgentFactory', 'IOrchestrator', 'IDatabase',
            'BaseAgent', 'Configuration', 'container', 'ContentType'
        ]
        
        for component in expected_core:
            assert component in core.__all__, f"{component} missing from __all__"


class TestServicesPackageImports:
    """
    TDD tests for src.services package imports.
    """
    
    def test_services_package_exposes_service_classes(self):
        """Test that service classes can be imported from src.services."""
        from src.services import (
            ContentSavingService, ContextInjectionService, 
            ClusteringService, VertexRAGService
        )
        
        assert ContentSavingService.__name__ == 'ContentSavingService'
        assert ContextInjectionService.__name__ == 'ContextInjectionService'
        assert ClusteringService.__name__ == 'ClusteringService'
        assert VertexRAGService.__name__ == 'VertexRAGService'


class TestRepositoriesPackageImports:
    """
    TDD tests for src.repositories package imports.
    """
    
    def test_repositories_package_exposes_repository_classes(self):
        """Test that repository classes can be imported from src.repositories."""
        from src.repositories import (
            BaseRepository, PlotRepository, AuthorRepository,
            WorldBuildingRepository, CharactersRepository,
            SessionRepository, OrchestratorRepository
        )
        
        assert BaseRepository.__name__ == 'BaseRepository'
        assert PlotRepository.__name__ == 'PlotRepository'
        assert AuthorRepository.__name__ == 'AuthorRepository'
        assert WorldBuildingRepository.__name__ == 'WorldBuildingRepository'
        assert CharactersRepository.__name__ == 'CharactersRepository'
        assert SessionRepository.__name__ == 'SessionRepository'
        assert OrchestratorRepository.__name__ == 'OrchestratorRepository'


class TestBackwardCompatibility:
    """
    Tests to ensure backward compatibility is maintained.
    All existing imports should continue to work after changes.
    """
    
    def test_existing_direct_imports_still_work(self):
        """Test that existing direct imports continue to work."""
        # These are actual imports from the codebase that should continue working
        from src.models.entities import Plot, Author, WorldBuilding, Characters
        from src.agents.agent_factory import AgentFactory
        from src.agents.plot_generator import PlotGeneratorAgent
        from src.core.base_agent import BaseAgent
        from src.core.interfaces import IAgent, IAgentFactory, IOrchestrator
        from src.services.content_saving_service import ContentSavingService
        from src.repositories.plot_repository import PlotRepository
        
        # Verify all imports successful
        assert all([
            Plot, Author, WorldBuilding, Characters, AgentFactory,
            PlotGeneratorAgent, BaseAgent, IAgent, IAgentFactory, IOrchestrator,
            ContentSavingService, PlotRepository
        ])
    
    def test_package_imports_coexist_with_direct_imports(self):
        """Test that new package imports don't interfere with direct imports."""
        # Import same class both ways
        from src.models import Plot as PackagePlot
        from src.models.entities import Plot as DirectPlot
        
        # Should be the same class
        assert PackagePlot is DirectPlot
        
        # Same for agents
        from src.agents import AgentFactory as PackageAgentFactory
        from src.agents.agent_factory import AgentFactory as DirectAgentFactory
        
        assert PackageAgentFactory is DirectAgentFactory


class TestPackageDocumentation:
    """
    Tests to ensure packages have proper documentation.
    """
    
    def test_models_package_has_docstring(self):
        """Test that src.models package has meaningful docstring."""
        import src.models as models
        
        assert models.__doc__ is not None
        assert len(models.__doc__.strip()) > 0
        assert 'entities' in models.__doc__.lower() or 'domain' in models.__doc__.lower()
    
    def test_agents_package_has_docstring(self):
        """Test that src.agents package has meaningful docstring."""
        import src.agents as agents
        
        assert agents.__doc__ is not None
        assert len(agents.__doc__.strip()) > 0
        assert 'agent' in agents.__doc__.lower()
    
    def test_core_package_has_docstring(self):
        """Test that src.core package has meaningful docstring."""
        import src.core as core
        
        assert core.__doc__ is not None
        assert len(core.__doc__.strip()) > 0
        assert 'core' in core.__doc__.lower() or 'base' in core.__doc__.lower()