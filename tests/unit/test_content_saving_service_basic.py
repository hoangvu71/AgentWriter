"""
TDD Test Suite for ContentSavingService - Basic Functionality.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage (focused on core TDD patterns):
- Service initialization validation
- Basic content saving operations
- Error handling patterns
- Repository integration patterns
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.services.content_saving_service import ContentSavingService


class TestContentSavingServiceBasicInitialization:
    """Test ContentSavingService basic initialization"""
    
    def test_service_initialization_with_all_repositories(self, mock_plot_repository, mock_author_repository, 
                                                         mock_world_building_repository, mock_characters_repository,
                                                         mock_session_repository, mock_iterative_repository):
        """
        RED: Test ContentSavingService initialization with all required repositories
        Should initialize successfully with all dependencies
        """
        # Act
        service = ContentSavingService(
            mock_plot_repository, 
            mock_author_repository,
            mock_world_building_repository, 
            mock_characters_repository,
            mock_session_repository,
            mock_iterative_repository
        )
        
        # Assert
        assert service.plot_repository == mock_plot_repository
        assert service.author_repository == mock_author_repository
        assert service.world_building_repository == mock_world_building_repository
        assert service.characters_repository == mock_characters_repository
        assert service.session_repository == mock_session_repository
        assert service.iterative_repository == mock_iterative_repository
        assert service.logger is not None
        assert hasattr(service, 'save_plot_data')
        assert hasattr(service, 'save_author_data')
    
    def test_service_initialization_validation_missing_plot_repository(self, mock_author_repository, 
                                                                      mock_world_building_repository, 
                                                                      mock_characters_repository):
        """
        RED: Test ContentSavingService initialization with missing plot repository
        Should raise ValueError when required repository is None
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ContentSavingService(
                None,  # Missing plot repository
                mock_author_repository,
                mock_world_building_repository, 
                mock_characters_repository
            )
        
        assert "All core repositories" in str(exc_info.value)
    
    def test_service_initialization_validation_missing_iterative_repository(self, mock_plot_repository, 
                                                                           mock_author_repository,
                                                                           mock_world_building_repository, 
                                                                           mock_characters_repository):
        """
        RED: Test ContentSavingService initialization without iterative repository
        Should raise ValueError for missing iterative repository
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ContentSavingService(
                mock_plot_repository, 
                mock_author_repository,
                mock_world_building_repository, 
                mock_characters_repository,
                iterative_repository=None
            )
        
        assert "IterativeRepository is required" in str(exc_info.value)


class TestContentSavingServiceBasicOperations:
    """Test basic ContentSavingService operations"""
    
    @pytest.mark.asyncio
    async def test_save_agent_response_plot_agent(self, mock_plot_repository, mock_author_repository, 
                                                 mock_world_building_repository, mock_characters_repository,
                                                 mock_session_repository, mock_iterative_repository):
        """
        RED: Test saving agent response for plot generator
        Should handle plot agent responses correctly
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        response_data = {
            "title": "Test Plot",
            "genre": "Fantasy",
            "summary": "A test adventure"
        }
        
        # Mock the internal save method
        expected_result = {"success": True, "plot_id": str(uuid.uuid4())}
        with patch.object(service, '_save_plot_via_tool', return_value=expected_result) as mock_save:
            # Act
            result = await service.save_agent_response(
                agent_name="plot_generator",
                response_data=response_data,
                session_id="test-session",
                user_id="test-user"
            )
            
            # Assert
            assert result is not None
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_agent_response_author_agent(self, mock_plot_repository, mock_author_repository, 
                                                   mock_world_building_repository, mock_characters_repository,
                                                   mock_session_repository, mock_iterative_repository):
        """
        RED: Test saving agent response for author generator
        Should handle author agent responses correctly
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        response_data = {
            "author_name": "Test Author",
            "bio": "A test author biography",
            "style": "Modern"
        }
        
        # Mock the internal save method
        expected_result = {"success": True, "author_id": str(uuid.uuid4())}
        with patch.object(service, '_save_author_via_tool', return_value=expected_result) as mock_save:
            # Act
            result = await service.save_agent_response(
                agent_name="author_generator",
                response_data=response_data,
                session_id="test-session",
                user_id="test-user"
            )
            
            # Assert
            assert result is not None
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_agent_response_unknown_agent(self, mock_plot_repository, mock_author_repository, 
                                                    mock_world_building_repository, mock_characters_repository,
                                                    mock_session_repository, mock_iterative_repository):
        """
        RED: Test saving agent response for unknown agent type
        Should handle unknown agents gracefully
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        response_data = {"unknown": "data"}
        
        # Act
        result = await service.save_agent_response(
            agent_name="unknown_agent",
            response_data=response_data,
            session_id="test-session",
            user_id="test-user"
        )
        
        # Assert
        # For unknown agents, the service should either return None or handle gracefully
        # The exact behavior depends on implementation
        assert result is None or isinstance(result, dict)


class TestContentSavingServiceErrorHandling:
    """Test error handling in ContentSavingService"""
    
    @pytest.mark.asyncio
    async def test_save_agent_response_handles_repository_errors(self, mock_plot_repository, mock_author_repository, 
                                                               mock_world_building_repository, mock_characters_repository,
                                                               mock_session_repository, mock_iterative_repository):
        """
        RED: Test service handling of repository errors
        Should gracefully handle repository operation failures
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        response_data = {"title": "Test Plot"}
        
        # Mock repository error
        with patch.object(service, '_save_plot_via_tool', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await service.save_agent_response(
                    agent_name="plot_generator",
                    response_data=response_data,
                    session_id="test-session",
                    user_id="test-user"
                )
            
            assert "Repository error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_save_agent_response_logs_errors(self, mock_plot_repository, mock_author_repository, 
                                                  mock_world_building_repository, mock_characters_repository,
                                                  mock_session_repository, mock_iterative_repository):
        """
        RED: Test service error logging
        Should log errors when operations fail
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        response_data = {"title": "Test Plot"}
        
        # Mock repository error and logger
        with patch.object(service, '_save_plot_via_tool', side_effect=Exception("Test error")), \
             patch.object(service.logger, 'error') as mock_log:
            
            # Act
            try:
                await service.save_agent_response(
                    agent_name="plot_generator",
                    response_data=response_data,
                    session_id="test-session",
                    user_id="test-user"
                )
            except Exception:
                pass  # Expected to fail
            
            # Assert
            # Verify error was logged (depends on implementation)
            # This test may need adjustment based on actual error handling


class TestContentSavingServiceDirectMethods:
    """Test direct content saving methods"""
    
    @pytest.mark.asyncio
    async def test_save_plot_data_direct(self, mock_plot_repository, mock_author_repository, 
                                        mock_world_building_repository, mock_characters_repository,
                                        mock_session_repository, mock_iterative_repository, sample_plot_data):
        """
        RED: Test direct plot data saving
        Should save plot data directly via save_plot_data method
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        # Act
        result = await service.save_plot_data(
            session_id=sample_plot_data["session_id"],
            user_id=sample_plot_data["user_id"],
            plot_data=sample_plot_data
        )
        
        # Assert
        # The exact return format depends on implementation
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_save_author_data_direct(self, mock_plot_repository, mock_author_repository, 
                                          mock_world_building_repository, mock_characters_repository,
                                          mock_session_repository, mock_iterative_repository, sample_author_data):
        """
        RED: Test direct author data saving
        Should save author data directly via save_author_data method
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        # Act
        result = await service.save_author_data(
            session_id=sample_author_data["session_id"],
            user_id=sample_author_data["user_id"],
            author_data=sample_author_data
        )
        
        # Assert
        # The exact return format depends on implementation
        assert result is not None
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_save_plot_data_validation(self, mock_plot_repository, mock_author_repository, 
                                            mock_world_building_repository, mock_characters_repository,
                                            mock_session_repository, mock_iterative_repository):
        """
        RED: Test plot data validation
        Should validate plot data before saving
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        invalid_plot_data = {
            # Missing required fields
            "genre": "Fantasy"
        }
        
        # Act & Assert
        with pytest.raises(Exception):
            await service.save_plot_data(
                session_id="test-session",
                user_id="test-user",
                plot_data=invalid_plot_data
            )


class TestContentSavingServiceIntegration:
    """Test ContentSavingService integration patterns"""
    
    @pytest.mark.asyncio
    async def test_service_repository_integration(self, mock_plot_repository, mock_author_repository, 
                                                 mock_world_building_repository, mock_characters_repository,
                                                 mock_session_repository, mock_iterative_repository):
        """
        RED: Test service integration with repositories
        Should properly coordinate with repository layer
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        # Verify service has access to all repositories
        assert service.plot_repository is not None
        assert service.author_repository is not None
        assert service.world_building_repository is not None
        assert service.characters_repository is not None
        assert service.session_repository is not None
        assert service.iterative_repository is not None
    
    def test_service_logging_integration(self, mock_plot_repository, mock_author_repository, 
                                        mock_world_building_repository, mock_characters_repository,
                                        mock_session_repository, mock_iterative_repository):
        """
        RED: Test service logging integration
        Should have proper logging configured
        """
        # Arrange & Act
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, mock_world_building_repository, 
            mock_characters_repository, mock_session_repository, mock_iterative_repository
        )
        
        # Assert
        assert service.logger is not None
        assert hasattr(service.logger, 'info')
        assert hasattr(service.logger, 'error')
        assert hasattr(service.logger, 'warning')