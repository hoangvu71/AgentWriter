"""pytest configuration file to set up Python path and fixtures"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# This ensures that imports like "from src.agents.agent_factory import ..." work correctly

# Import core interfaces and entities after path setup
from src.core.interfaces import (
    AgentRequest, AgentResponse, ContentType, IDatabase, IAgent, IConfiguration
)
from src.core.configuration import Configuration
from src.models.entities import Plot, Author, WorldBuilding, Characters


# Test Configuration Fixtures
@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = MagicMock(spec=Configuration)
    config.model_name = "gemini-1.5-flash-002"
    config.database_url = "sqlite:///:memory:"
    config.google_cloud_project = "test-project"
    config.google_cloud_location = "us-central1"
    config.supabase_url = None
    config.supabase_key = None
    config.use_supabase = False
    return config


# Database Fixtures
@pytest.fixture
def mock_database():
    """Mock database interface for testing BaseRepository"""
    db = AsyncMock()
    
    # Set up default mock responses for BaseRepository interface
    db.insert.return_value = str(uuid.uuid4())
    db.get_by_id.return_value = None
    db.update.return_value = True
    db.delete.return_value = True
    db.get_all.return_value = []
    db.search.return_value = []
    db.count.return_value = 0
    
    # Additional database methods used by the system
    db.save_plot.return_value = str(uuid.uuid4())
    db.save_author.return_value = str(uuid.uuid4())
    db.get_plot.return_value = None
    db.get_author.return_value = None
    db.search_content.return_value = []
    
    return db


# Repository Fixtures for ContentSavingService
@pytest.fixture
def mock_plot_repository():
    """Mock plot repository for ContentSavingService testing"""
    repo = AsyncMock()
    repo.create.return_value = str(uuid.uuid4())
    repo.get_by_id.return_value = None
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_author_repository():
    """Mock author repository for ContentSavingService testing"""
    repo = AsyncMock()
    repo.create.return_value = str(uuid.uuid4())
    repo.get_by_id.return_value = None
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_world_building_repository():
    """Mock world building repository for ContentSavingService testing"""
    repo = AsyncMock()
    repo.create.return_value = str(uuid.uuid4())
    repo.get_by_id.return_value = None
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_characters_repository():
    """Mock characters repository for ContentSavingService testing"""
    repo = AsyncMock()
    repo.create.return_value = str(uuid.uuid4())
    repo.get_by_id.return_value = None
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_session_repository():
    """Mock session repository for ContentSavingService testing"""
    repo = AsyncMock()
    repo.create.return_value = str(uuid.uuid4())
    repo.get_by_id.return_value = None
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def mock_iterative_repository():
    """Mock iterative repository for ContentSavingService testing"""
    repo = AsyncMock()
    repo.create.return_value = str(uuid.uuid4())
    repo.get_by_id.return_value = None
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


@pytest.fixture
def sample_plot_data():
    """Sample plot data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "title": "Test Adventure",
        "genre": "Fantasy",
        "summary": "A brave hero embarks on an epic quest",
        "main_conflict": "Hero vs Dark Lord",
        "resolution": "Good triumphs over evil",
        "user_id": "test-user",
        "session_id": "test-session",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_author_data():
    """Sample author data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "author_name": "J.R.R. TestAuthor",
        "bio": "A fictional author for testing",
        "style": "Epic Fantasy",
        "voice": "Formal and descriptive",
        "user_id": "test-user",
        "session_id": "test-session",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


# Agent Request Fixtures
@pytest.fixture
def basic_agent_request():
    """Basic agent request for testing"""
    return AgentRequest(
        content="Generate a fantasy plot",
        user_id="test-user",
        session_id="test-session",
        context={"genre": "fantasy"},
        metadata={"test": True}
    )


@pytest.fixture
def complex_agent_request():
    """Complex agent request with full context"""
    return AgentRequest(
        content="Create an epic fantasy adventure with dragons",
        user_id="test-user",
        session_id="test-session",
        context={
            "genre_hierarchy": {"primary": "Fantasy", "sub_genre": "Epic Fantasy"},
            "story_elements": ["dragons", "magic", "quest"],
            "target_audience": {"age_group": "young_adult", "interests": ["adventure"]},
            "content_selection": {"improve_plot": True, "enhance_characters": False}
        },
        metadata={"complexity": "high", "test": True}
    )


# Vertex AI / ADK Mocking Fixtures
@pytest.fixture
def mock_vertex_ai():
    """Mock Vertex AI components"""
    with patch('google.adk.agents.Agent') as mock_agent_class, \
         patch('google.adk.runners.InMemoryRunner') as mock_runner_class, \
         patch('google.genai.types.Content') as mock_content_class, \
         patch('google.genai.types.Part') as mock_part_class:
        
        # Mock Agent
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock Runner
        mock_runner = AsyncMock()
        mock_runner_class.return_value = mock_runner
        
        # Mock session service
        mock_session_service = AsyncMock()
        mock_session = AsyncMock()
        mock_session.session_id = "vertex-session-123"
        mock_session_service.create_session.return_value = mock_session
        mock_runner.session_service = mock_session_service
        
        # Mock async iterator for run_async
        async def mock_run_async(*args, **kwargs):
            # Simulate streaming response
            yield MagicMock(content="Part 1 of response")
            yield MagicMock(content="Part 2 of response")
            yield MagicMock(content="Final part")
        
        mock_runner.run_async = mock_run_async
        
        # Mock Content and Part
        mock_content_class.return_value = MagicMock()
        mock_part_class.return_value = MagicMock()
        
        yield {
            'agent_class': mock_agent_class,
            'agent': mock_agent,
            'runner_class': mock_runner_class,
            'runner': mock_runner,
            'session_service': mock_session_service,
            'session': mock_session,
            'content_class': mock_content_class,
            'part_class': mock_part_class
        }


# ADK Services Mocking
@pytest.fixture
def mock_adk_services():
    """Mock ADK services and dependencies"""
    with patch('src.core.adk_services.get_adk_service_factory') as mock_factory_func, \
         patch('src.core.conversation_manager.get_conversation_manager') as mock_conv_mgr, \
         patch('src.core.observability.initialize_observability') as mock_obs, \
         patch('src.core.agent_tracker.get_agent_tracker') as mock_tracker, \
         patch('src.core.schema_service.schema_service') as mock_schema:
        
        # Mock factory
        mock_factory = MagicMock()
        mock_factory.service_mode.value = "test"
        mock_factory.create_runner.return_value = AsyncMock()
        mock_factory_func.return_value = mock_factory
        
        # Mock conversation manager
        mock_cm = AsyncMock()
        mock_cm.get_conversation_context.return_value = {
            "has_conversation_history": False,
            "context_summary": "",
            "user_preferences": {}
        }
        mock_conv_mgr.return_value = mock_cm
        
        # Mock observability
        mock_observability = MagicMock()
        mock_observability.trace_agent_execution.return_value.__enter__.return_value = MagicMock()
        mock_observability.trace_llm_interaction.return_value.__enter__.return_value = MagicMock()
        mock_observability.trace_tool_execution.return_value.__enter__.return_value = MagicMock()
        mock_obs.return_value = mock_observability
        
        # Mock agent tracker
        mock_agent_tracker = MagicMock()
        mock_agent_tracker.start_invocation.return_value = MagicMock()
        mock_tracker.return_value = mock_agent_tracker
        
        # Mock schema service
        mock_schema.get_content_type_from_agent.return_value = "plot"
        mock_schema._get_fallback_json_schema.return_value = {"title": {"type": "string"}}
        mock_schema.generate_json_schema_instruction.return_value = "Use JSON format"
        
        yield {
            'factory': mock_factory,
            'conversation_manager': mock_cm,
            'observability': mock_observability,
            'agent_tracker': mock_agent_tracker,
            'schema_service': mock_schema
        }


# Container and Dependency Injection Mocking
@pytest.fixture
def mock_container():
    """Mock dependency injection container"""
    with patch('src.core.container.get_container') as mock_get_container:
        mock_container = MagicMock()
        mock_container.set_session_context = MagicMock()
        mock_get_container.return_value = mock_container
        yield mock_container


# Entity Fixtures
@pytest.fixture
def sample_plot_entity():
    """Sample Plot entity for testing"""
    return Plot(
        id=str(uuid.uuid4()),
        title="Test Adventure",
        genre="Fantasy",
        summary="A brave hero embarks on an epic quest",
        main_conflict="Hero vs Dark Lord",
        resolution="Good triumphs over evil",
        user_id="test-user",
        session_id="test-session",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_author_entity():
    """Sample Author entity for testing"""
    return Author(
        id=str(uuid.uuid4()),
        author_name="J.R.R. TestAuthor",
        bio="A fictional author for testing",
        style="Epic Fantasy",
        voice="Formal and descriptive",
        user_id="test-user",
        session_id="test-session",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


# Test Utilities
@pytest.fixture
def assert_async():
    """Utility for asserting async calls"""
    async def _assert_async_called(mock_func, *args, **kwargs):
        """Assert that an async mock was called with specific arguments"""
        mock_func.assert_called_with(*args, **kwargs)
    return _assert_async_called


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_environment():
    """Clean up environment variables and global state between tests"""
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ['TESTING'] = 'true'
    os.environ['LOG_LEVEL'] = 'ERROR'  # Reduce log noise during tests
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Async test markers
pytestmark = pytest.mark.asyncio