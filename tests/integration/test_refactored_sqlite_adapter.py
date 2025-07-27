"""
Integration test for the refactored SQLite adapter.
Ensures it maintains full compatibility with the original adapter.
"""

import pytest
import asyncio
import os
import tempfile
import json
from typing import Dict, Any, List
from uuid import uuid4

from src.database.sqlite.adapter import SQLiteAdapter


class TestRefactoredSQLiteAdapter:
    """Test the refactored SQLite adapter maintains all original functionality"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def adapter(self, temp_db_path):
        """Create refactored SQLite adapter with temporary database"""
        return SQLiteAdapter(temp_db_path)
    
    async def create_test_user(self, adapter, user_id=None):
        """Helper to create a test user"""
        if user_id is None:
            user_id = str(uuid4())
        user_data = {"id": user_id, "name": "Test User"}
        await adapter.insert("users", user_data)
        return user_id
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_db_path):
        """Test adapter initialization"""
        adapter = SQLiteAdapter(temp_db_path)
        assert os.path.exists(temp_db_path)
        assert adapter.db_path == temp_db_path
        assert adapter.connection_manager is not None
        assert adapter.query_builder is not None
        assert adapter.table_manager is not None
        assert adapter.data_operations is not None
    
    @pytest.mark.asyncio
    async def test_insert_functionality(self, adapter):
        """Test all insert operations"""
        # Create user first
        user_id = await self.create_test_user(adapter)
        
        # Test basic insert
        plot_data = {
            "title": "Test Plot",
            "genre": "Fantasy",
            "plot_summary": "A test plot summary",
            "user_id": user_id
        }
        
        plot_id = await adapter.insert("plots", plot_data)
        assert plot_id is not None
        assert isinstance(plot_id, str)
        
        # Verify data was inserted
        retrieved = await adapter.get_by_id("plots", plot_id)
        assert retrieved is not None
        assert retrieved["title"] == "Test Plot"
    
    @pytest.mark.asyncio
    async def test_all_original_functionality(self, adapter):
        """Test all functionality from the original comprehensive test"""
        # Create user first
        user_id = await self.create_test_user(adapter)
        
        # Test insert
        plot_data = {
            "title": "Comprehensive Test",
            "plot_summary": "Testing all functionality", 
            "genre": "Test",
            "user_id": user_id
        }
        plot_id = await adapter.insert("plots", plot_data)
        
        # Test select
        results = await adapter.select("plots", {"genre": "Test"})
        assert len(results) >= 1
        
        # Test update
        updated = await adapter.update("plots", plot_id, {"title": "Updated Title"})
        assert updated is True
        
        # Test count
        count = await adapter.count("plots", {"genre": "Test"})
        assert count >= 1
        
        # Test search
        search_results = await adapter.search("plots", {"plot_summary": "%functionality%"})
        assert len(search_results) >= 1
        
        # Test specialized methods
        author_data = {
            "author_name": "Test Author",
            "writing_style": "Narrative", 
            "biography": "A test author",
            "user_id": user_id
        }
        author_id = await adapter.save_author(author_data)
        retrieved_author = await adapter.get_author(author_id)
        assert retrieved_author["author_name"] == "Test Author"
        
        # Test batch operations
        batch_records = []
        for i in range(3):
            batch_records.append({
                "title": f"Batch Plot {i}",
                "plot_summary": f"Batch summary {i}",
                "genre": "BatchTest",
                "user_id": user_id
            })
        
        batch_ids = await adapter.batch_insert("plots", batch_records)
        assert len(batch_ids) == 3
        
        batch_results = await adapter.batch_select_by_ids("plots", batch_ids)
        assert len(batch_results) == 3
        
        # Test content search
        content_results = await adapter.search_content("functionality", "plots", user_id)
        assert len(content_results) >= 1
        
        # Test metrics (should not fail)
        metrics = await adapter.get_pool_metrics()
        assert isinstance(metrics, dict)
        
        await adapter.reset_pool_metrics()
        
        # Test delete (at the end)
        deleted = await adapter.delete("plots", plot_id)
        assert deleted is True
        
        not_found = await adapter.get_by_id("plots", plot_id)
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_modular_component_access(self, adapter):
        """Test that modular components are properly accessible"""
        # Test connection manager
        assert adapter.connection_manager is not None
        conn = adapter.connection_manager.get_connection()
        assert conn is not None
        conn.close()
        
        # Test query builder
        assert adapter.query_builder is not None
        query, params = adapter.query_builder.build_select("test_table")
        assert "SELECT * FROM test_table" == query
        
        # Test table manager
        assert adapter.table_manager is not None
        assert adapter.table_manager.table_exists("users")
        
        # Test data operations
        assert adapter.data_operations is not None
    
    @pytest.mark.asyncio
    async def test_performance_comparison(self, adapter):
        """Basic performance test to ensure no significant degradation"""
        import time
        
        # Create test user
        user_id = await self.create_test_user(adapter)
        
        # Time a series of operations
        start_time = time.time()
        
        # Insert multiple records
        for i in range(10):
            plot_data = {
                "title": f"Performance Test {i}",
                "plot_summary": f"Summary {i}",
                "genre": "Performance",
                "user_id": user_id
            }
            await adapter.insert("plots", plot_data)
        
        # Select records
        results = await adapter.select("plots", {"genre": "Performance"})
        assert len(results) == 10
        
        # Count records
        count = await adapter.count("plots", {"genre": "Performance"})
        assert count == 10
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete reasonably quickly (adjust threshold as needed)
        assert elapsed < 5.0  # 5 seconds should be more than enough
        
        print(f"Performance test completed in {elapsed:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_error_handling_compatibility(self, adapter):
        """Test error handling matches original behavior"""
        # Test operations on non-existent records
        result = await adapter.get_by_id("plots", "non-existent-id")
        assert result is None
        
        updated = await adapter.update("plots", "non-existent-id", {"title": "New"})
        assert updated is False
        
        deleted = await adapter.delete("plots", "non-existent-id")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_close_functionality(self, adapter):
        """Test adapter cleanup"""
        # Perform operations first
        user_id = await self.create_test_user(adapter)
        
        plot_data = {
            "title": "Close Test",
            "plot_summary": "Test before close",
            "user_id": user_id
        }
        await adapter.insert("plots", plot_data)
        
        # Close adapter
        await adapter.close()
        
        # Should not raise errors on close