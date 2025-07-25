"""
FastAPI test client utilities for API testing infrastructure.
Provides consistent TestClient setup with dependency injection overrides.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, List, Optional

from src.app import app
from src.routers.plots import get_plot_repository
from src.routers.authors import get_author_repository
from src.routers.content import get_repositories
from src.routers.websocket import get_websocket_handler


class APITestClient:
    """
    Enhanced TestClient wrapper with dependency injection support.
    Provides easy mock repository setup and consistent test patterns.
    """
    
    def __init__(self):
        self.client = TestClient(app)
        self.dependency_overrides = {}
        self.original_overrides = {}
    
    def setup_plot_repository_mock(self) -> AsyncMock:
        """Setup mock PlotRepository with default responses"""
        mock_repo = AsyncMock()
        
        # Default mock responses
        mock_repo.get_all.return_value = [
            {"id": "plot-1", "title": "Fantasy Adventure", "user_id": "user-1"},
            {"id": "plot-2", "title": "Sci-Fi Epic", "user_id": "user-1"}
        ]
        
        mock_repo._serialize.side_effect = lambda x: x
        
        mock_repo.get_user_plots.return_value = [
            {"id": "plot-1", "title": "Fantasy Adventure", "user_id": "user-1"}
        ]
        
        mock_repo.get_by_id.return_value = {
            "id": "plot-1", "title": "Fantasy Adventure", "plot_summary": "Epic quest"
        }
        
        mock_repo.search.return_value = [
            {"id": "plot-1", "title": "Fantasy Adventure", "plot_summary": "Epic quest"}
        ]
        
        # Set dependency override
        self.dependency_overrides["plot_repository"] = mock_repo
        app.dependency_overrides[get_plot_repository] = lambda: mock_repo
        
        return mock_repo
    
    def setup_author_repository_mock(self) -> AsyncMock:
        """Setup mock AuthorRepository with default responses"""
        mock_repo = AsyncMock()
        
        # Default mock responses
        mock_repo.get_all.return_value = [
            {"id": "author-1", "author_name": "J.R.R. Tolkien", "user_id": "user-1"},
            {"id": "author-2", "author_name": "Isaac Asimov", "user_id": "user-1"}
        ]
        
        mock_repo._serialize.side_effect = lambda x: x
        
        mock_repo.get_user_authors.return_value = [
            {"id": "author-1", "author_name": "J.R.R. Tolkien", "user_id": "user-1"}
        ]
        
        # Set dependency override
        self.dependency_overrides["author_repository"] = mock_repo
        app.dependency_overrides[get_author_repository] = lambda: mock_repo
        
        return mock_repo
    
    def setup_content_repositories_mock(self) -> Dict[str, AsyncMock]:
        """Setup all content repositories for content router testing"""
        mock_repos = {
            "plot_repo": AsyncMock(),
            "author_repo": AsyncMock(),
            "world_repo": AsyncMock(),
            "characters_repo": AsyncMock()
        }
        
        # Setup default responses
        mock_repos["plot_repo"].count.return_value = 10
        mock_repos["author_repo"].count.return_value = 5
        mock_repos["world_repo"].count.return_value = 8
        mock_repos["characters_repo"].count.return_value = 12
        
        mock_repos["plot_repo"].search.return_value = [
            {"id": "plot-1", "title": "Fantasy Adventure", "type": "plot"}
        ]
        mock_repos["author_repo"].search.return_value = [
            {"id": "author-1", "author_name": "J.R.R. Tolkien", "type": "author"}
        ]
        mock_repos["world_repo"].search.return_value = []
        mock_repos["characters_repo"].search.return_value = []
        
        # Set dependency override
        def mock_get_repositories():
            return {
                "plot_repository": mock_repos["plot_repo"],
                "author_repository": mock_repos["author_repo"],
                "world_building_repository": mock_repos["world_repo"],
                "characters_repository": mock_repos["characters_repo"]
            }
        
        app.dependency_overrides[get_repositories] = mock_get_repositories
        self.dependency_overrides["content_repositories"] = mock_repos
        
        return mock_repos
    
    def setup_websocket_handler_mock(self) -> AsyncMock:
        """Setup mock WebSocketHandler for WebSocket testing"""
        mock_handler = AsyncMock()
        mock_handler.logger = Mock()
        
        # Set dependency override
        app.dependency_overrides[get_websocket_handler] = lambda: mock_handler
        self.dependency_overrides["websocket_handler"] = mock_handler
        
        return mock_handler
    
    def cleanup_dependency_overrides(self):
        """Clean up all dependency overrides"""
        app.dependency_overrides.clear()
        self.dependency_overrides.clear()
    
    def get_mock_repository(self, repo_name: str) -> Optional[AsyncMock]:
        """Get a specific mock repository"""
        return self.dependency_overrides.get(repo_name)


@pytest.fixture
def api_client():
    """Pytest fixture providing APITestClient with automatic cleanup"""
    client = APITestClient()
    yield client
    client.cleanup_dependency_overrides()


@pytest.fixture
def plots_client(api_client):
    """Pytest fixture with plot repository mock setup"""
    mock_repo = api_client.setup_plot_repository_mock()
    return api_client, mock_repo


@pytest.fixture
def authors_client(api_client):
    """Pytest fixture with author repository mock setup"""
    mock_repo = api_client.setup_author_repository_mock()
    return api_client, mock_repo


@pytest.fixture
def content_client(api_client):
    """Pytest fixture with all content repositories mock setup"""
    mock_repos = api_client.setup_content_repositories_mock()
    return api_client, mock_repos


@pytest.fixture
def websocket_client(api_client):
    """Pytest fixture with WebSocket handler mock setup"""
    mock_handler = api_client.setup_websocket_handler_mock()
    return api_client, mock_handler


# Response validation utilities
def validate_success_response(response_data: Dict[str, Any], data_key: str) -> bool:
    """Validate standard success response structure"""
    required_fields = ["success", data_key]
    return (
        all(field in response_data for field in required_fields) and
        response_data["success"] is True and
        isinstance(response_data[data_key], list)
    )


def validate_error_response(response_data: Dict[str, Any], data_key: str) -> bool:
    """Validate standard error response structure"""
    required_fields = ["success", "error", data_key]
    return (
        all(field in response_data for field in required_fields) and
        response_data["success"] is False and
        isinstance(response_data["error"], str) and
        len(response_data["error"]) > 0
    )


def validate_user_specific_response(response_data: Dict[str, Any], user_id: str, data_key: str) -> bool:
    """Validate user-specific endpoint response structure"""
    return (
        validate_success_response(response_data, data_key) and
        response_data.get("user_id") == user_id and
        "total" in response_data
    )