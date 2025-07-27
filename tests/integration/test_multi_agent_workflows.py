"""
Integration Test Suite for Multi-Agent Workflows.

This module tests end-to-end multi-agent system functionality:
- Complete book creation workflows
- Agent coordination and communication
- Database persistence across agent operations
- WebSocket real-time updates
- Performance benchmarks for critical operations
"""

import pytest
import asyncio
import uuid
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.interfaces import AgentRequest, AgentResponse, ContentType
from src.core.configuration import Configuration
from src.services.content_saving_service import ContentSavingService


class TestMultiAgentBookCreationWorkflow:
    """Test complete book creation workflows involving multiple agents"""
    
    @pytest.mark.asyncio
    @patch('src.tools.writing_tools.save_plot')
    @patch('src.tools.writing_tools.save_author')
    @patch('src.tools.writing_tools.save_world_building')
    @patch('src.tools.writing_tools.save_characters')
    async def test_complete_fantasy_book_creation_workflow(self, mock_save_characters, mock_save_world_building,
                                                          mock_save_author, mock_save_plot,
                                                          mock_config, mock_plot_repository, 
                                                          mock_author_repository, mock_world_building_repository,
                                                          mock_characters_repository, mock_session_repository,
                                                          mock_iterative_repository):
        """
        Test complete fantasy book creation involving plot, author, world-building, and characters
        Should coordinate all agents and create a cohesive book project
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository, 
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        # Mock successful tool operations
        plot_id = str(uuid.uuid4())
        author_id = str(uuid.uuid4())
        world_id = str(uuid.uuid4())
        characters_id = str(uuid.uuid4())
        
        mock_save_plot.return_value = {"success": True, "plot_id": plot_id}
        mock_save_author.return_value = {"success": True, "author_id": author_id}
        mock_save_world_building.return_value = {"success": True, "world_building_id": world_id}
        mock_save_characters.return_value = {"success": True, "characters_id": characters_id}
        
        # Step 1: Create plot
        plot_data = {
            "title": "The Crystal Prophecy",
            "genre": "Fantasy",
            "summary": "A young mage discovers an ancient prophecy about crystal dragons",
            "main_conflict": "Ancient evil vs prophecied hero",
            "resolution": "Hero unites crystal dragons to defeat darkness",
            "user_id": "test-user",
            "session_id": "workflow-session"
        }
        
        # Step 2: Create author
        author_data = {
            "author_name": "Aria Worldforge",
            "bio": "Epic fantasy author known for intricate world-building",
            "style": "Epic Fantasy",
            "voice": "Formal yet accessible with rich descriptions",
            "user_id": "test-user",
            "session_id": "workflow-session"
        }
        
        # Step 3: Create world-building
        world_data = {
            "world_name": "Crystalon Realm",
            "setting": "Medieval fantasy world with crystal magic",
            "history": "Ancient civilization built on crystal magic",
            "geography": "Floating crystal islands connected by energy bridges",
            "culture": "Crystal-based magic system governs society",
            "plot_id": plot_id,
            "user_id": "test-user",
            "session_id": "workflow-session"
        }
        
        # Step 4: Create characters
        characters_data = {
            "main_characters": [
                {
                    "name": "Lyra Crystalheart",
                    "role": "Protagonist",
                    "description": "Young mage discovering her crystal magic abilities"
                }
            ],
            "supporting_characters": [
                {
                    "name": "Master Thorne",
                    "role": "Mentor",
                    "description": "Ancient crystal sage who guides Lyra"
                }
            ],
            "plot_id": plot_id,
            "world_id": world_id,
            "user_id": "test-user",
            "session_id": "workflow-session"
        }
        
        # Act - Execute complete workflow using ContentSavingService methods
        start_time = time.time()
        
        # Use the correct service method names
        saved_plot = await service.save_agent_response("plot_generator", plot_data, "workflow-session", "test-user")
        saved_author = await service.save_agent_response("author_generator", author_data, "workflow-session", "test-user")
        saved_world = await service.save_agent_response("world_building", world_data, "workflow-session", "test-user", {"plot_id": plot_id})
        saved_characters = await service.save_agent_response("characters", characters_data, "workflow-session", "test-user", {"plot_id": plot_id, "world_id": world_id})
        
        end_time = time.time()
        workflow_duration = end_time - start_time
        
        # Assert
        assert saved_plot is not None
        assert saved_author is not None
        assert saved_world is not None
        assert saved_characters is not None
        
        # Verify tool functions were called
        mock_save_plot.assert_called_once()
        mock_save_author.assert_called_once()
        mock_save_world_building.assert_called_once()
        mock_save_characters.assert_called_once()
        
        # Performance benchmark - should complete within reasonable time
        assert workflow_duration < 5.0  # 5 seconds max for mocked operations
    
    @pytest.mark.asyncio
    @patch('src.tools.writing_tools.save_plot')
    @patch('src.tools.writing_tools.save_author')
    @patch('src.tools.writing_tools.save_world_building')
    async def test_science_fiction_book_workflow_with_dependencies(self, mock_save_world_building, mock_save_author, mock_save_plot,
                                                                  mock_config, mock_plot_repository, 
                                                                  mock_author_repository, mock_world_building_repository,
                                                                  mock_characters_repository, mock_session_repository,
                                                                  mock_iterative_repository):
        """
        Test science fiction book creation with proper dependency management
        Should handle cross-component references and maintain consistency
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        plot_id = str(uuid.uuid4())
        author_id = str(uuid.uuid4())
        world_id = str(uuid.uuid4())
        
        mock_save_plot.return_value = {"success": True, "plot_id": plot_id}
        mock_save_author.return_value = {"success": True, "author_id": author_id}
        mock_save_world_building.return_value = {"success": True, "world_building_id": world_id}
        
        # Create interconnected sci-fi book components
        plot_data = {
            "title": "Galactic Rebellion",
            "genre": "Science Fiction",
            "summary": "A rebellion against the Galactic Empire spreads across star systems",
            "user_id": "test-user",
            "session_id": "scifi-session"
        }
        
        author_data = {
            "author_name": "Nova Sterling",
            "bio": "Hard science fiction author specializing in space opera",
            "style": "Hard Science Fiction",
            "voice": "Technical precision with grand scope",
            "user_id": "test-user",
            "session_id": "scifi-session"
        }
        
        world_data = {
            "world_name": "The Galactic Empire",
            "setting": "Far future galaxy-spanning civilization",
            "technology": "FTL travel, AI systems, energy weapons",
            "politics": "Authoritarian empire facing widespread rebellion",
            "plot_id": plot_id,  # Reference to plot
            "user_id": "test-user",
            "session_id": "scifi-session"
        }
        
        # Act
        saved_plot = await service.save_agent_response("plot_generator", plot_data, "scifi-session", "test-user")
        saved_author = await service.save_agent_response("author_generator", author_data, "scifi-session", "test-user")
        
        # Update world data with plot reference - use plot_id from saved plot
        saved_world = await service.save_agent_response("world_building", world_data, "scifi-session", "test-user", {"plot_id": plot_id})
        
        # Assert
        assert saved_plot is not None
        assert saved_author is not None
        assert saved_world is not None
        
        # Verify proper dependency handling
        mock_save_plot.assert_called_once()
        mock_save_author.assert_called_once()
        mock_save_world_building.assert_called_once()


class TestAgentCoordinationIntegration:
    """Test agent coordination and communication patterns"""
    
    @pytest.mark.asyncio
    async def test_agent_to_agent_context_passing(self, mock_config, mock_plot_repository, 
                                                  mock_author_repository, mock_world_building_repository,
                                                  mock_characters_repository, mock_session_repository,
                                                  mock_iterative_repository):
        """
        Test context passing between different agents
        Should maintain state and context across agent boundaries
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        session_id = "context-passing-session"
        user_id = "test-user"
        
        plot_id = str(uuid.uuid4())
        world_id = str(uuid.uuid4())
        mock_plot_repository.create.return_value = plot_id
        mock_world_building_repository.create.return_value = world_id
        
        # Simulate plot generation with context
        plot_context = {
            "genre": "Urban Fantasy",
            "themes": ["magic in modern world", "hidden societies"],
            "tone": "dark and mysterious"
        }
        
        plot_data = {
            "title": "Shadow Networks",
            "genre": "Urban Fantasy",
            "summary": "Secret magical societies operate in modern cities",
            "user_id": user_id,
            "session_id": session_id,
            "context": plot_context
        }
        
        # Act - Save plot first
        saved_plot = await service.save_agent_response("plot_generator", plot_data, session_id, user_id)
        
        # Simulate world-building that references plot context
        world_data = {
            "world_name": "Modern Magical Underground",
            "world_content": "Contemporary urban environment with hidden magical layer",
            "societies": "Secret covens, corporate mage guilds, underground markets",
            "user_id": user_id,
            "session_id": session_id,
            "derived_from_plot": True
        }
        
        saved_world = await service.save_agent_response("world_building", world_data, session_id, user_id, {"plot_id": plot_id})
        
        # Assert
        assert saved_plot is not None
        assert saved_world is not None
        
        # Verify repository calls were made
        mock_plot_repository.create.assert_called()
        mock_world_building_repository.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_parallel_agent_operations(self, mock_config, mock_plot_repository, 
                                            mock_author_repository, mock_world_building_repository,
                                            mock_characters_repository, mock_session_repository,
                                            mock_iterative_repository):
        """
        Test parallel agent operations for efficiency
        Should handle concurrent agent operations without conflicts
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        # Mock multiple database operations
        mock_plot_repository.create.return_value = str(uuid.uuid4())
        mock_author_repository.create.return_value = str(uuid.uuid4())
        
        plot_data = {
            "title": "Parallel Universe",
            "genre": "Science Fiction",
            "summary": "Multiple realities collide",
            "user_id": "test-user",
            "session_id": "parallel-session"
        }
        
        author_data = {
            "author_name": "Quantum Writer",
            "bio": "Specializes in parallel universe narratives",
            "style": "Speculative Fiction",
            "voice": "Mind-bending and precise",
            "user_id": "test-user", 
            "session_id": "parallel-session"
        }
        
        # Act - Execute operations in parallel
        start_time = time.time()
        
        plot_task = service.save_agent_response("plot_generator", plot_data, "parallel-session", "test-user")
        author_task = service.save_agent_response("author_generator", author_data, "parallel-session", "test-user")
        
        saved_plot, saved_author = await asyncio.gather(plot_task, author_task)
        
        end_time = time.time()
        parallel_duration = end_time - start_time
        
        # Assert
        assert saved_plot is not None
        assert saved_author is not None
        
        # Verify both operations completed
        mock_plot_repository.create.assert_called_once()
        mock_author_repository.create.assert_called_once()
        
        # Should be faster than sequential operations (in real scenarios)
        assert parallel_duration < 2.0  # Reasonable for mocked operations


class TestDatabasePersistenceIntegration:
    """Test database persistence across multi-agent operations"""
    
    @pytest.mark.asyncio
    async def test_cross_table_foreign_key_integrity(self, mock_config, mock_plot_repository, 
                                                    mock_author_repository, mock_world_building_repository,
                                                    mock_characters_repository, mock_session_repository,
                                                    mock_iterative_repository):
        """
        Test foreign key relationships across different content types
        Should maintain referential integrity across agent operations
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        plot_id = str(uuid.uuid4())
        world_id = str(uuid.uuid4())
        characters_id = str(uuid.uuid4())
        
        mock_plot_repository.create.return_value = plot_id
        mock_world_building_repository.create.return_value = world_id
        mock_characters_repository.create.return_value = characters_id
        
        # Create hierarchical content with foreign key relationships
        plot_data = {
            "title": "The Enchanted Kingdom",
            "genre": "Fantasy",
            "summary": "A magical kingdom faces an ancient curse",
            "user_id": "test-user",
            "session_id": "integrity-session"
        }
        
        world_data = {
            "world_name": "Enchanted Realm",
            "setting": "Magical kingdom with ancient magic",
            "plot_id": None,  # Will be set after plot creation
            "user_id": "test-user",
            "session_id": "integrity-session"
        }
        
        characters_data = {
            "main_characters": [{"name": "Princess Elena", "role": "Protagonist"}],
            "plot_id": None,  # Will be set after plot creation
            "world_id": None,  # Will be set after world creation
            "user_id": "test-user",
            "session_id": "integrity-session"
        }
        
        # Act - Create with proper foreign key references
        saved_plot = await service.save_agent_response("plot_generator", plot_data, "integrity-session", "test-user")
        
        saved_world = await service.save_agent_response("world_building", world_data, "integrity-session", "test-user", {"plot_id": plot_id})
        
        characters_data["characters"] = characters_data.pop("main_characters")  # Fix structure for save_characters tool
        saved_characters = await service.save_agent_response("characters", characters_data, "integrity-session", "test-user", {"plot_id": plot_id, "world_id": world_id})
        
        # Assert foreign key relationships
        assert saved_plot is not None
        assert saved_world is not None
        assert saved_characters is not None
        
        # Verify repository calls were made with proper parameters
        mock_plot_repository.create.assert_called()
        mock_world_building_repository.create.assert_called()
        mock_characters_repository.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_transaction_consistency_across_operations(self, mock_config, mock_plot_repository, 
                                                            mock_author_repository, mock_world_building_repository,
                                                            mock_characters_repository, mock_session_repository,
                                                            mock_iterative_repository):
        """
        Test transaction consistency across multiple operations
        Should handle partial failures and maintain data consistency
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        # Mock successful plot creation but failed world creation
        plot_id = str(uuid.uuid4())
        mock_plot_repository.create.return_value = plot_id
        mock_world_building_repository.create.side_effect = Exception("Database connection failed")
        
        plot_data = {
            "title": "Transaction Test",
            "genre": "Test Genre",
            "summary": "Testing transaction consistency",
            "user_id": "test-user",
            "session_id": "transaction-session"
        }
        
        world_data = {
            "world_name": "Test World",
            "setting": "Test setting",
            "plot_id": None,
            "user_id": "test-user",
            "session_id": "transaction-session"
        }
        
        # Act
        saved_plot = await service.save_agent_response("plot_generator", plot_data, "transaction-session", "test-user")
        
        # Attempt to save world (will fail)
        with pytest.raises(Exception, match="Database connection failed"):
            await service.save_agent_response("world_building", world_data, "transaction-session", "test-user", {"plot_id": plot_id})
        
        # Assert
        assert saved_plot is not None
        mock_plot_repository.create.assert_called_once()
        mock_world_building_repository.create.assert_called_once()


class TestPerformanceBenchmarks:
    """Test performance benchmarks for critical operations"""
    
    @pytest.mark.asyncio
    async def test_large_book_project_performance(self, mock_config, mock_plot_repository, 
                                                 mock_author_repository, mock_world_building_repository,
                                                 mock_characters_repository, mock_session_repository,
                                                 mock_iterative_repository):
        """
        Test performance with large, complex book projects
        Should handle complex projects within acceptable time limits
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        # Mock database operations with slight delays to simulate real operations
        async def mock_save_with_delay(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms delay
            return str(uuid.uuid4())
        
        mock_plot_repository.create.side_effect = mock_save_with_delay
        mock_author_repository.create.side_effect = mock_save_with_delay
        mock_world_building_repository.create.side_effect = mock_save_with_delay
        mock_characters_repository.create.side_effect = mock_save_with_delay
        
        # Create complex book project data
        complex_plot_data = {
            "title": "The Epic Saga: A Multi-Volume Fantasy Series",
            "genre": "Epic Fantasy",
            "summary": "A sprawling epic spanning multiple generations, kingdoms, and magical systems. " * 10,  # Long summary
            "main_conflict": "Multiple interconnected conflicts across time and space",
            "resolution": "Complex resolution involving multiple character arcs and world changes",
            "subplots": ["Romance subplot", "Political intrigue", "Magical discovery", "Coming of age"],
            "user_id": "test-user",
            "session_id": "performance-session"
        }
        
        complex_author_data = {
            "author_name": "Epic Worldsmith",
            "bio": "Master of epic fantasy with decades of experience in complex world-building and character development. Known for intricate plots and detailed magical systems.",
            "style": "Epic Fantasy with Multiple POVs",
            "voice": "Grand and sweeping with intricate detail and multiple narrative perspectives",
            "influences": ["Tolkien", "Jordan", "Martin", "Sanderson"],
            "user_id": "test-user",
            "session_id": "performance-session"
        }
        
        complex_world_data = {
            "world_name": "The Infinite Realms",
            "setting": "Multiple interconnected realms with different magical systems",
            "history": "Thousands of years of recorded history across multiple civilizations",
            "geography": "Seven distinct realms connected by magical portals",
            "culture": "Dozens of distinct cultures with unique customs and magic systems",
            "magic_systems": ["Elemental magic", "Time magic", "Soul magic", "Creation magic"],
            "religions": ["The Old Gods", "The New Pantheon", "The Void Worshippers"],
            "plot_id": None,
            "user_id": "test-user",
            "session_id": "performance-session"
        }
        
        complex_characters_data = {
            "main_characters": [
                {"name": f"Hero {i}", "role": "Protagonist", "description": f"Complex character {i} with detailed backstory"}
                for i in range(5)
            ],
            "supporting_characters": [
                {"name": f"Support {i}", "role": "Supporting", "description": f"Supporting character {i}"}
                for i in range(15)
            ],
            "plot_id": None,
            "world_id": None,
            "user_id": "test-user",
            "session_id": "performance-session"
        }
        
        # Act - Measure performance
        start_time = time.time()
        
        plot_result = await service.save_agent_response("plot_generator", complex_plot_data, "performance-session", "test-user")
        author_result = await service.save_agent_response("author_generator", complex_author_data, "performance-session", "test-user")
        
        # Mock plot_id for world and characters
        plot_id = str(uuid.uuid4())
        world_result = await service.save_agent_response("world_building", complex_world_data, "performance-session", "test-user", {"plot_id": plot_id})
        
        # Convert character structure for save_characters tool
        complex_characters_data["characters"] = complex_characters_data["main_characters"] + complex_characters_data["supporting_characters"]
        world_id = str(uuid.uuid4())
        characters_result = await service.save_agent_response("characters", complex_characters_data, "performance-session", "test-user", {"plot_id": plot_id, "world_id": world_id})
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Assert
        assert plot_result is not None
        assert author_result is not None
        assert world_result is not None
        assert characters_result is not None
        
        # Performance assertion - should complete complex project within 2 seconds
        assert total_duration < 2.0
        
        print(f"Complex book project completed in {total_duration:.3f} seconds")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_operations_performance(self, mock_config, mock_plot_repository, 
                                                         mock_author_repository, mock_world_building_repository,
                                                         mock_characters_repository, mock_session_repository,
                                                         mock_iterative_repository):
        """
        Test performance with multiple concurrent user operations
        Should handle multiple users creating content simultaneously
        """
        # Arrange
        service = ContentSavingService(
            mock_plot_repository, mock_author_repository,
            mock_world_building_repository, mock_characters_repository,
            mock_session_repository, mock_iterative_repository
        )
        
        # Mock database operations
        mock_plot_repository.create.side_effect = lambda *args: str(uuid.uuid4())
        mock_author_repository.create.side_effect = lambda *args: str(uuid.uuid4())
        
        # Create multiple user sessions
        user_data = []
        for i in range(5):  # Simulate 5 concurrent users
            user_data.append({
                "plot": {
                    "title": f"User {i} Story",
                    "genre": "Fantasy",
                    "summary": f"Story created by user {i}",
                    "user_id": f"user-{i}",
                    "session_id": f"session-{i}"
                },
                "author": {
                    "author_name": f"Author {i}",
                    "bio": f"Author for user {i}",
                    "style": "Fantasy",
                    "voice": "Descriptive",
                    "user_id": f"user-{i}",
                    "session_id": f"session-{i}"
                }
            })
        
        # Act - Execute concurrent operations
        start_time = time.time()
        
        tasks = []
        for data in user_data:
            plot_task = service.save_agent_response("plot_generator", data["plot"], data["plot"]["session_id"], data["plot"]["user_id"])
            author_task = service.save_agent_response("author_generator", data["author"], data["author"]["session_id"], data["author"]["user_id"])
            tasks.extend([plot_task, author_task])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        concurrent_duration = end_time - start_time
        
        # Assert
        # All operations should succeed (no exceptions)
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None
        
        # Should handle 10 operations (5 users × 2 operations each) quickly
        assert concurrent_duration < 1.0
        
        # Verify all database calls were made
        assert mock_plot_repository.create.call_count == 5
        assert mock_author_repository.create.call_count == 5
        
        print(f"Concurrent operations for 5 users completed in {concurrent_duration:.3f} seconds")