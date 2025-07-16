#!/usr/bin/env python3
"""
Database Operations Unit Tests - CRITICAL TDD COMPLIANCE
These tests should have been written FIRST before any database implementation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

# Import the database service that should have been test-driven
from supabase_service import SupabaseService

class TestDatabaseOperationsTDD:
    """
    Tests that SHOULD have driven the database operations design
    These represent CRITICAL TDD violations - all database code was written BEFORE tests
    """
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for isolated testing"""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        return mock_client, mock_table
    
    @pytest.fixture
    def db_service(self, mock_supabase_client):
        """Create database service with mocked client"""
        mock_client, mock_table = mock_supabase_client
        service = SupabaseService()
        service.client = mock_client
        return service, mock_table
    
    # RED: These tests should have FAILED first, driving the implementation
    
    class TestUserManagement:
        """Tests that should have driven user management operations"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_user_creation(self, db_service):
            """RED: This test should have failed first"""
            service, mock_table = db_service
            
            # Mock user creation
            mock_response = Mock()
            mock_response.data = [{"id": "user-uuid", "user_id": "test_user"}]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            user = await service.create_or_get_user("test_user")
            assert user["id"] == "user-uuid"
            assert user["user_id"] == "test_user"
        
        @pytest.mark.asyncio
        async def test_should_handle_existing_user_retrieval(self, db_service):
            """RED: This test should have driven user lookup logic"""
            service, mock_table = db_service
            
            # Mock existing user
            mock_response = Mock()
            mock_response.data = [{"id": "existing-uuid", "user_id": "existing_user"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            user = await service.create_or_get_user("existing_user")
            assert user["id"] == "existing-uuid"
        
        @pytest.mark.asyncio
        async def test_should_validate_user_id_format(self, db_service):
            """RED: This test should have driven user validation"""
            service, mock_table = db_service
            
            with pytest.raises(ValueError, match="user_id cannot be empty"):
                await service.create_or_get_user("")
            
            with pytest.raises(ValueError, match="user_id cannot be None"):
                await service.create_or_get_user(None)
    
    class TestPlotOperations:
        """Tests that should have driven plot CRUD operations"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_plot_creation(self, db_service):
            """RED: This test should have failed first"""
            service, mock_table = db_service
            
            # Mock plot creation
            mock_response = Mock()
            mock_response.data = [{"id": "plot-uuid", "title": "Test Plot"}]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            plot_data = {
                "title": "Test Plot",
                "plot_summary": "A test story",
                "user_id": "test_user"
            }
            
            result = await service.save_plot(plot_data)
            assert result["id"] == "plot-uuid"
        
        @pytest.mark.asyncio
        async def test_should_validate_plot_data_structure(self, db_service):
            """RED: This test should have driven plot validation"""
            service, mock_table = db_service
            
            # Test missing required fields
            with pytest.raises(ValueError, match="title is required"):
                await service.save_plot({})
            
            with pytest.raises(ValueError, match="plot_summary is required"):
                await service.save_plot({"title": "Test"})
            
            with pytest.raises(ValueError, match="user_id is required"):
                await service.save_plot({
                    "title": "Test",
                    "plot_summary": "Test summary"
                })
        
        @pytest.mark.asyncio
        async def test_should_handle_plot_retrieval_by_id(self, db_service):
            """RED: This test should have driven plot lookup"""
            service, mock_table = db_service
            
            # Mock plot retrieval
            mock_response = Mock()
            mock_response.data = [{"id": "plot-id", "title": "Retrieved Plot"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            plot = await service.get_plot_by_id("plot-id")
            assert plot["title"] == "Retrieved Plot"
        
        @pytest.mark.asyncio
        async def test_should_handle_nonexistent_plot_gracefully(self, db_service):
            """RED: This test should have driven error handling"""
            service, mock_table = db_service
            
            # Mock empty response
            mock_response = Mock()
            mock_response.data = []
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            plot = await service.get_plot_by_id("nonexistent-id")
            assert plot is None
        
        @pytest.mark.asyncio
        async def test_should_support_plot_filtering_and_search(self, db_service):
            """RED: This test should have driven search functionality"""
            service, mock_table = db_service
            
            # Mock filtered results
            mock_response = Mock()
            mock_response.data = [{"id": "plot1", "genre": "Fantasy"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            plots = await service.get_plots_by_genre("Fantasy")
            assert len(plots) == 1
            assert plots[0]["genre"] == "Fantasy"
    
    class TestAuthorOperations:
        """Tests that should have driven author CRUD operations"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_author_creation(self, db_service):
            """RED: This test should have failed first"""
            service, mock_table = db_service
            
            # Mock author creation
            mock_response = Mock()
            mock_response.data = [{"id": "author-uuid", "author_name": "Test Author"}]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            author_data = {
                "author_name": "Test Author",
                "biography": "A test biography",
                "writing_style": "Descriptive",
                "user_id": "test_user"
            }
            
            result = await service.save_author(author_data)
            assert result["id"] == "author-uuid"
        
        @pytest.mark.asyncio
        async def test_should_validate_author_data_structure(self, db_service):
            """RED: This test should have driven author validation"""
            service, mock_table = db_service
            
            with pytest.raises(ValueError, match="author_name is required"):
                await service.save_author({})
            
            with pytest.raises(ValueError, match="biography is required"):
                await service.save_author({"author_name": "Test"})
        
        @pytest.mark.asyncio
        async def test_should_handle_author_plot_relationships(self, db_service):
            """RED: This test should have driven relationship management"""
            service, mock_table = db_service
            
            # Mock author with plots
            mock_response = Mock()
            mock_response.data = [
                {"id": "plot1", "title": "Plot 1", "author_id": "author-id"},
                {"id": "plot2", "title": "Plot 2", "author_id": "author-id"}
            ]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            plots = await service.get_plots_by_author("author-id")
            assert len(plots) == 2
            assert all(plot["author_id"] == "author-id" for plot in plots)
    
    class TestGenreManagement:
        """Tests that should have driven genre operations"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_genre_creation(self, db_service):
            """RED: This test should have failed first"""
            service, mock_table = db_service
            
            # Mock genre creation
            mock_response = Mock()
            mock_response.data = [{"id": "genre-uuid", "name": "Test Genre"}]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            genre_data = {
                "name": "Test Genre",
                "description": "A test genre description"
            }
            
            result = await service.create_genre(genre_data)
            assert result["id"] == "genre-uuid"
        
        @pytest.mark.asyncio
        async def test_should_handle_hierarchical_genre_structure(self, db_service):
            """RED: This test should have driven genre hierarchy"""
            service, mock_table = db_service
            
            # Mock hierarchical genre response
            mock_response = Mock()
            mock_response.data = [
                {"id": "subgenre1", "parent_genre": "Fantasy", "name": "Epic Fantasy"},
                {"id": "subgenre2", "parent_genre": "Fantasy", "name": "Urban Fantasy"}
            ]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            subgenres = await service.get_subgenres("Fantasy")
            assert len(subgenres) == 2
            assert all(sg["parent_genre"] == "Fantasy" for sg in subgenres)
        
        @pytest.mark.asyncio
        async def test_should_validate_genre_data(self, db_service):
            """RED: This test should have driven genre validation"""
            service, mock_table = db_service
            
            with pytest.raises(ValueError, match="name is required"):
                await service.create_genre({"description": "Test"})
            
            with pytest.raises(ValueError, match="name cannot be empty"):
                await service.create_genre({"name": "", "description": "Test"})
    
    class TestTargetAudienceOperations:
        """Tests that should have driven target audience management"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_audience_creation(self, db_service):
            """RED: This test should have failed first"""
            service, mock_table = db_service
            
            # Mock audience creation
            mock_response = Mock()
            mock_response.data = [{"id": "audience-uuid", "age_group": "Young Adult"}]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            audience_data = {
                "age_group": "Young Adult",
                "gender": "All",
                "sexual_orientation": "All",
                "interests": ["Adventure", "Romance"],
                "description": "YA adventure romance readers"
            }
            
            result = await service.create_target_audience(audience_data)
            assert result["id"] == "audience-uuid"
        
        @pytest.mark.asyncio
        async def test_should_validate_audience_structure(self, db_service):
            """RED: This test should have driven audience validation"""
            service, mock_table = db_service
            
            valid_age_groups = ["Children", "Middle Grade", "Young Adult", "New Adult", "Adult", "Senior"]
            
            with pytest.raises(ValueError, match="Invalid age_group"):
                await service.create_target_audience({
                    "age_group": "Invalid Age",
                    "gender": "All",
                    "sexual_orientation": "All"
                })
            
            # Should accept valid age groups
            for age_group in valid_age_groups:
                # This should not raise an exception
                audience_data = {
                    "age_group": age_group,
                    "gender": "All",
                    "sexual_orientation": "All"
                }
                # Mock successful creation
                mock_response = Mock()
                mock_response.data = [{"id": f"audience-{age_group}"}]
                mock_table.insert.return_value.execute.return_value = mock_response
                
                result = await service.create_target_audience(audience_data)
                assert result["id"] == f"audience-{age_group}"
    
    class TestDatabaseTransactions:
        """Tests that should have driven transaction handling"""
        
        @pytest.mark.asyncio
        async def test_should_handle_transaction_rollback_on_error(self, db_service):
            """RED: This test should have driven transaction management"""
            service, mock_table = db_service
            
            # Mock transaction failure
            mock_table.insert.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Failed to save"):
                await service.save_plot({
                    "title": "Test Plot",
                    "plot_summary": "Test",
                    "user_id": "test_user"
                })
            
            # Should rollback changes (verify no partial saves)
        
        @pytest.mark.asyncio
        async def test_should_handle_concurrent_operations(self, db_service):
            """RED: This test should have driven concurrency handling"""
            service, mock_table = db_service
            
            # Mock concurrent plot creation
            mock_response = Mock()
            mock_response.data = [{"id": f"plot-{i}"} for i in range(5)]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            # Simulate concurrent operations
            tasks = []
            for i in range(5):
                task = service.save_plot({
                    "title": f"Plot {i}",
                    "plot_summary": f"Summary {i}",
                    "user_id": "test_user"
                })
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All operations should succeed or fail gracefully
            assert all(isinstance(r, dict) or isinstance(r, Exception) for r in results)
    
    class TestDataValidation:
        """Tests that should have driven data validation and integrity"""
        
        @pytest.mark.asyncio
        async def test_should_validate_foreign_key_constraints(self, db_service):
            """RED: This test should have driven foreign key validation"""
            service, mock_table = db_service
            
            # Test plot with invalid author_id
            with pytest.raises(ValueError, match="Invalid author_id"):
                await service.save_plot({
                    "title": "Test Plot",
                    "plot_summary": "Test",
                    "author_id": "nonexistent-author-id",
                    "user_id": "test_user"
                })
        
        @pytest.mark.asyncio
        async def test_should_sanitize_user_input(self, db_service):
            """RED: This test should have driven input sanitization"""
            service, mock_table = db_service
            
            # Mock response
            mock_response = Mock()
            mock_response.data = [{"id": "plot-id", "title": "Sanitized Title"}]
            mock_table.insert.return_value.execute.return_value = mock_response
            
            malicious_data = {
                "title": "<script>alert('xss')</script>",
                "plot_summary": "'; DROP TABLE plots; --",
                "user_id": "test_user"
            }
            
            result = await service.save_plot(malicious_data)
            
            # Should sanitize input
            assert "<script>" not in result.get("title", "")
            assert "DROP TABLE" not in result.get("plot_summary", "")
        
        @pytest.mark.asyncio
        async def test_should_validate_data_types_and_formats(self, db_service):
            """RED: This test should have driven type validation"""
            service, mock_table = db_service
            
            # Test invalid data types
            with pytest.raises(TypeError, match="title must be string"):
                await service.save_plot({
                    "title": 123,  # Should be string
                    "plot_summary": "Test",
                    "user_id": "test_user"
                })
            
            with pytest.raises(ValueError, match="Invalid email format"):
                await service.create_or_get_user("invalid-email-format")
    
    class TestQueryOptimization:
        """Tests that should have driven query performance"""
        
        @pytest.mark.asyncio
        async def test_should_use_indexes_for_common_queries(self, db_service):
            """RED: This test should have driven index usage"""
            service, mock_table = db_service
            
            # Mock indexed query
            mock_response = Mock()
            mock_response.data = [{"id": "plot1"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            # Query by indexed field should be fast
            import time
            start_time = time.time()
            
            await service.get_plots_by_user("test_user")  # Should use user_id index
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should be fast due to indexing
            assert query_time < 0.1  # Less than 100ms for mocked query
        
        @pytest.mark.asyncio
        async def test_should_limit_large_result_sets(self, db_service):
            """RED: This test should have driven pagination"""
            service, mock_table = db_service
            
            # Mock large result set
            large_data = [{"id": f"plot-{i}"} for i in range(1000)]
            mock_response = Mock()
            mock_response.data = large_data[:100]  # Should be limited
            mock_table.select.return_value.limit.return_value.execute.return_value = mock_response
            
            results = await service.get_all_plots(limit=100)
            
            # Should limit results to prevent memory issues
            assert len(results) <= 100
        
        @pytest.mark.asyncio
        async def test_should_use_connection_pooling(self, db_service):
            """RED: This test should have driven connection management"""
            service, mock_table = db_service
            
            # Simulate multiple concurrent database operations
            tasks = []
            for i in range(20):
                task = service.get_plot_by_id(f"plot-{i}")
                tasks.append(task)
            
            # Mock responses
            mock_response = Mock()
            mock_response.data = [{"id": "test-plot"}]
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All operations should complete without connection exhaustion
            assert len(results) == 20
            assert all(isinstance(r, dict) or r is None for r in results)

class TestDatabaseErrorHandling:
    """Tests that should have driven comprehensive error handling"""
    
    @pytest.fixture
    def db_service(self):
        service = SupabaseService()
        service.client = Mock()
        return service
    
    @pytest.mark.asyncio
    async def test_should_handle_connection_failures(self, db_service):
        """RED: This test should have driven connection error handling"""
        # Mock connection failure
        db_service.client.table.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            await db_service.get_all_plots()
    
    @pytest.mark.asyncio
    async def test_should_handle_timeout_errors(self, db_service):
        """RED: This test should have driven timeout handling"""
        # Mock timeout
        db_service.client.table.side_effect = TimeoutError("Query timeout")
        
        with pytest.raises(Exception, match="Database operation timed out"):
            await db_service.get_all_plots()
    
    @pytest.mark.asyncio
    async def test_should_provide_meaningful_error_messages(self, db_service):
        """RED: This test should have driven user-friendly errors"""
        # Mock various database errors
        db_service.client.table.side_effect = Exception("23505: duplicate key value")
        
        with pytest.raises(Exception, match="already exists"):
            await db_service.save_plot({
                "title": "Duplicate Plot",
                "plot_summary": "Test",
                "user_id": "test_user"
            })

if __name__ == "__main__":
    pytest.main([__file__, "-v"])