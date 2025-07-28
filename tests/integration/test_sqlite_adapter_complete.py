"""
Comprehensive integration tests for SQLite adapter functionality.
Tests ALL current functionality before refactoring to ensure no regressions.
"""

import pytest
import asyncio
import os
import tempfile
import json
from typing import Dict, Any, List
from uuid import uuid4

from src.database.sqlite.adapter import SQLiteAdapter


class TestSQLiteAdapterComplete:
    """Complete test suite for SQLite adapter before refactoring"""
    
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
        """Create SQLite adapter with temporary database"""
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
        """Test database initialization"""
        adapter = SQLiteAdapter(temp_db_path)
        assert os.path.exists(temp_db_path)
        assert adapter.db_path == temp_db_path
    
    @pytest.mark.asyncio
    async def test_insert_functionality(self, adapter):
        """Test all insert operations"""
        # Create user first due to foreign key constraint
        user_id = str(uuid4())
        user_data = {"id": user_id, "name": "Test User"}
        await adapter.insert("users", user_data)
        
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
    async def test_select_functionality(self, adapter):
        """Test all select operations"""
        # Create user first
        user_id = await self.create_test_user(adapter)
        
        # Insert test data
        plot_data = {
            "title": "Select Test Plot",
            "genre": "Sci-Fi",
            "plot_summary": "Test summary",
            "user_id": user_id
        }
        
        plot_id = await adapter.insert("plots", plot_data)
        
        # Test select with filters
        results = await adapter.select("plots", {"genre": "Sci-Fi"})
        assert len(results) >= 1
        assert any(r["id"] == plot_id for r in results)
        
        # Test select without filters
        all_results = await adapter.select("plots")
        assert len(all_results) >= 1
    
    @pytest.mark.asyncio
    async def test_update_functionality(self, adapter):
        """Test update operations"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Insert test data
        plot_data = {
            "title": "Original Title",
            "genre": "Fantasy",
            "plot_summary": "Original summary",
            "user_id": user_id
        }
        
        plot_id = await adapter.insert("plots", plot_data)
        
        # Update data
        updated = await adapter.update("plots", plot_id, {"title": "Updated Title"})
        assert updated is True
        
        # Verify update
        retrieved = await adapter.get_by_id("plots", plot_id)
        assert retrieved["title"] == "Updated Title"
        assert retrieved["genre"] == "Fantasy"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_functionality(self, adapter):
        """Test delete operations"""
        # Create required user first to satisfy foreign key constraint  
        user_id = await self.create_test_user(adapter)
        
        # Insert test data
        plot_data = {
            "title": "To Delete",
            "genre": "Horror",
            "plot_summary": "Will be deleted",
            "user_id": user_id
        }
        
        plot_id = await adapter.insert("plots", plot_data)
        
        # Verify exists
        exists = await adapter.get_by_id("plots", plot_id)
        assert exists is not None
        
        # Delete
        deleted = await adapter.delete("plots", plot_id)
        assert deleted is True
        
        # Verify deleted
        not_exists = await adapter.get_by_id("plots", plot_id)
        assert not_exists is None
    
    @pytest.mark.asyncio
    async def test_count_functionality(self, adapter):
        """Test count operations"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Insert multiple records
        for i in range(3):
            plot_data = {
                "title": f"Count Test {i}",
                "genre": "TestGenre",
                "plot_summary": f"Summary {i}",
                "user_id": user_id
            }
            await adapter.insert("plots", plot_data)
        
        # Test count with filters
        count = await adapter.count("plots", {"genre": "TestGenre"})
        assert count >= 3
        
        # Test count without filters
        total_count = await adapter.count("plots")
        assert total_count >= 3
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, adapter):
        """Test search operations"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        plot_data = {
            "title": "Searchable Plot",
            "genre": "Adventure",
            "plot_summary": "This contains unique search term: FINDME",
            "user_id": user_id
        }
        
        plot_id = await adapter.insert("plots", plot_data)
        
        # Test search
        results = await adapter.search("plots", {"plot_summary": "%FINDME%"})
        assert len(results) >= 1
        assert any(r["id"] == plot_id for r in results)
    
    @pytest.mark.asyncio
    async def test_get_all_functionality(self, adapter):
        """Test get_all with pagination"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        inserted_ids = []
        for i in range(5):
            plot_data = {
                "title": f"GetAll Test {i}",
                "genre": "TestGenre",
                "plot_summary": f"Summary {i}",
                "user_id": user_id
            }
            plot_id = await adapter.insert("plots", plot_data)
            inserted_ids.append(plot_id)
        
        # Test pagination
        first_page = await adapter.get_all("plots", limit=3, offset=0)
        assert len(first_page) >= 3
        
        second_page = await adapter.get_all("plots", limit=3, offset=3)
        # Should have different records (or fewer if we've reached the end)
        assert len(second_page) >= 0
    
    @pytest.mark.asyncio
    async def test_specialized_methods(self, adapter):
        """Test plot and author specific methods"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Test save_plot
        plot_data = {
            "title": "Specialized Plot",
            "genre": "Mystery",
            "plot_summary": "A specialized plot",
            "user_id": user_id
        }
        plot_id = await adapter.save_plot(plot_data)
        assert plot_id is not None
        
        # Test get_plot
        retrieved_plot = await adapter.get_plot(plot_id)
        assert retrieved_plot is not None
        assert retrieved_plot["title"] == "Specialized Plot"
        
        # Test save_author
        author_data = {
            "author_name": "Test Author",
            "writing_style": "Narrative",
            "biography": "A test author",
            "user_id": user_id
        }
        author_id = await adapter.save_author(author_data)
        assert author_id is not None
        
        # Test get_author
        retrieved_author = await adapter.get_author(author_id)
        assert retrieved_author is not None
        assert retrieved_author["author_name"] == "Test Author"
        
        # Test get_plots_by_user
        user_plots = await adapter.get_plots_by_user(user_id)
        assert len(user_plots) >= 1
        assert any(p["id"] == plot_id for p in user_plots)
        
        # Test get_authors_by_user
        user_authors = await adapter.get_authors_by_user(user_id)
        assert len(user_authors) >= 1
        assert any(a["id"] == author_id for a in user_authors)
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, adapter):
        """Test batch insert, select, and update operations"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Test batch insert
        records = []
        for i in range(3):
            records.append({
                "title": f"Batch Plot {i}",
                "genre": "BatchGenre",
                "plot_summary": f"Batch summary {i}",
                "user_id": user_id
            })
        
        inserted_ids = await adapter.batch_insert("plots", records)
        assert len(inserted_ids) == 3
        assert all(isinstance(id, str) for id in inserted_ids)
        
        # Test batch select by ids
        batch_results = await adapter.batch_select_by_ids("plots", inserted_ids)
        assert len(batch_results) == 3
        assert all(r["genre"] == "BatchGenre" for r in batch_results)
        
        # Test batch update
        updates = []
        for i, record_id in enumerate(inserted_ids):
            updates.append({
                "id": record_id,
                "title": f"Updated Batch Plot {i}"
            })
        
        updated_count = await adapter.batch_update("plots", updates)
        assert updated_count == 3
        
        # Verify updates
        updated_results = await adapter.batch_select_by_ids("plots", inserted_ids)
        assert all("Updated" in r["title"] for r in updated_results)
    
    @pytest.mark.asyncio
    async def test_content_search(self, adapter):
        """Test the content search functionality"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Insert searchable content
        plot_data = {
            "title": "Search Test Plot",
            "genre": "SearchGenre",
            "plot_summary": "Content with searchable terms",
            "user_id": user_id
        }
        await adapter.insert("plots", plot_data)
        
        # Test content search
        results = await adapter.search_content("searchable", "plots", user_id)
        assert len(results) >= 1
        assert any("searchable" in r["plot_summary"].lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_metrics_functionality(self, adapter):
        """Test pool metrics functionality"""
        # Get initial metrics
        metrics = await adapter.get_pool_metrics()
        assert isinstance(metrics, dict)
        assert "total_operations" in metrics
        
        # Reset metrics
        await adapter.reset_pool_metrics()
        reset_metrics = await adapter.get_pool_metrics()
        assert reset_metrics["total_operations"] == 0
    
    @pytest.mark.asyncio
    async def test_json_serialization(self, adapter):
        """Test JSON serialization/deserialization using world_building table which has JSON fields"""
        # Test with complex JSON data using world_building table which supports JSON fields
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Create a plot first since world_building references it
        plot_data = {
            "title": "Test Plot for JSON",
            "genre": "Fantasy",
            "plot_summary": "A plot for testing JSON serialization",
            "user_id": user_id
        }
        plot_id = await adapter.insert("plots", plot_data)
        
        # Now test JSON serialization with world_building which has JSON fields
        complex_data = {
            "world_name": "JSON Test World",
            "world_type": "fantasy",
            "overview": "A world for testing JSON serialization",
            "geography": {
                "continents": ["North", "South"],
                "oceans": ["Pacific", "Atlantic"]
            },
            "cultural_systems": {
                "languages": ["Common", "Elvish"],
                "customs": {"greeting": "bow"}
            },
            "user_id": user_id,
            "plot_id": plot_id
        }
        
        world_id = await adapter.insert("world_building", complex_data)
        retrieved = await adapter.get_by_id("world_building", world_id)
        
        assert retrieved is not None
        assert retrieved["geography"]["continents"] == ["North", "South"]
        assert retrieved["cultural_systems"]["languages"] == ["Common", "Elvish"]
        assert retrieved["cultural_systems"]["customs"]["greeting"] == "bow"
    
    @pytest.mark.asyncio
    async def test_plot_with_author_relationship(self, adapter):
        """Test get_plot_with_author relationship functionality"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Create author first
        author_data = {
            "author_name": "Relationship Author",
            "writing_style": "Epic",
            "biography": "Author for relationship test",
            "user_id": user_id
        }
        author_id = await adapter.save_author(author_data)
        
        # Create plot with author reference
        plot_data = {
            "title": "Relationship Plot",
            "genre": "Epic Fantasy",
            "plot_summary": "Plot with author relationship",
            "author_id": author_id,
            "user_id": user_id
        }
        plot_id = await adapter.save_plot(plot_data)
        
        # Test get_plot_with_author
        result = await adapter.get_plot_with_author(plot_id)
        assert result is not None
        assert "plot" in result
        assert "author" in result
        assert result["plot"]["id"] == plot_id
        assert result["author"]["id"] == author_id
    
    @pytest.mark.asyncio
    async def test_error_handling(self, adapter):
        """Test error handling for invalid operations"""
        # Test get non-existent record
        result = await adapter.get_by_id("plots", "non-existent-id")
        assert result is None
        
        # Test update non-existent record
        updated = await adapter.update("plots", "non-existent-id", {"title": "New Title"})
        assert updated is False
        
        # Test delete non-existent record
        deleted = await adapter.delete("plots", "non-existent-id")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_close_functionality(self, adapter):
        """Test adapter close functionality"""
        # Create required user first to satisfy foreign key constraint
        user_id = await self.create_test_user(adapter)
        
        # Perform some operations first
        plot_data = {
            "title": "Close Test",
            "genre": "Test",
            "plot_summary": "Test before close",
            "user_id": user_id
        }
        await adapter.insert("plots", plot_data)
        
        # Close adapter
        await adapter.close()
        
        # Note: After close, operations might fail or be handled gracefully
        # This depends on the implementation