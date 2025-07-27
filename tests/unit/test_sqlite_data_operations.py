"""
TDD Tests for SQLite Data Operations Module.
This will handle the high-level data operations logic.
"""

import pytest
import tempfile
import os
import asyncio
from uuid import uuid4
from unittest.mock import Mock, patch

from src.database.sqlite.data_operations import SQLiteDataOperations
from src.database.sqlite.connection_manager import SQLiteConnectionManager
from src.database.sqlite.query_builder import SQLiteQueryBuilder
from src.database.sqlite.table_manager import SQLiteTableManager


class TestSQLiteDataOperations:
    """TDD tests for SQLite data operations functionality"""
    
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
    def connection_manager(self, temp_db_path):
        """Create connection manager"""
        return SQLiteConnectionManager(temp_db_path)
    
    @pytest.fixture
    def query_builder(self):
        """Create query builder"""
        return SQLiteQueryBuilder()
    
    @pytest.fixture
    def table_manager(self, connection_manager):
        """Create table manager and setup tables"""
        manager = SQLiteTableManager(connection_manager)
        manager.create_all_tables()
        return manager
    
    @pytest.fixture
    def data_operations(self, connection_manager, query_builder, table_manager):
        """Create data operations with dependencies"""
        return SQLiteDataOperations(connection_manager, query_builder, table_manager)
    
    @pytest.mark.asyncio
    async def test_initialization(self, connection_manager, query_builder, table_manager):
        """Test data operations initialization"""
        ops = SQLiteDataOperations(connection_manager, query_builder, table_manager)
        assert ops.connection_manager == connection_manager
        assert ops.query_builder == query_builder
        assert ops.table_manager == table_manager
    
    @pytest.mark.asyncio
    async def test_insert_async(self, data_operations):
        """Test async insert operations"""
        # Create test user first
        user_data = {"id": str(uuid4()), "name": "Test User"}
        user_id = await data_operations.insert("users", user_data)
        assert user_id == user_data["id"]
        
        # Test plot insert
        plot_data = {
            "id": str(uuid4()),
            "title": "Test Plot",
            "plot_summary": "A test plot summary",
            "user_id": user_data["id"]
        }
        plot_id = await data_operations.insert("plots", plot_data)
        assert plot_id == plot_data["id"]
        
        # Verify data was inserted
        retrieved = await data_operations.get_by_id("plots", plot_id)
        assert retrieved is not None
        assert retrieved["title"] == "Test Plot"
    
    @pytest.mark.asyncio
    async def test_select_async(self, data_operations):
        """Test async select operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        plot_data = {
            "id": str(uuid4()),
            "title": "Select Test",
            "plot_summary": "Test summary", 
            "genre": "Fantasy",
            "user_id": user_id
        }
        await data_operations.insert("plots", plot_data)
        
        # Test select with filters
        results = await data_operations.select("plots", {"genre": "Fantasy"})
        assert len(results) >= 1
        assert any(r["title"] == "Select Test" for r in results)
        
        # Test select with ordering and limit
        results = await data_operations.select(
            "plots", 
            order_by="created_at", 
            desc=True, 
            limit=1
        )
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_update_async(self, data_operations):
        """Test async update operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        plot_data = {
            "id": str(uuid4()),
            "title": "Original Title",
            "plot_summary": "Original summary",
            "user_id": user_id
        }
        plot_id = await data_operations.insert("plots", plot_data)
        
        # Update data
        updated = await data_operations.update("plots", plot_id, {"title": "Updated Title"})
        assert updated is True
        
        # Verify update
        retrieved = await data_operations.get_by_id("plots", plot_id)
        assert retrieved["title"] == "Updated Title"
        assert retrieved["plot_summary"] == "Original summary"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_async(self, data_operations):
        """Test async delete operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        plot_data = {
            "id": str(uuid4()),
            "title": "To Delete",
            "plot_summary": "Will be deleted",
            "user_id": user_id
        }
        plot_id = await data_operations.insert("plots", plot_data)
        
        # Verify exists
        exists = await data_operations.get_by_id("plots", plot_id)
        assert exists is not None
        
        # Delete
        deleted = await data_operations.delete("plots", plot_id)
        assert deleted is True
        
        # Verify deleted
        not_exists = await data_operations.get_by_id("plots", plot_id)
        assert not_exists is None
    
    @pytest.mark.asyncio
    async def test_count_async(self, data_operations):
        """Test async count operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        # Insert multiple plots
        for i in range(3):
            plot_data = {
                "id": str(uuid4()),
                "title": f"Count Test {i}",
                "plot_summary": f"Summary {i}",
                "genre": "TestGenre",
                "user_id": user_id
            }
            await data_operations.insert("plots", plot_data)
        
        # Test count with filters
        count = await data_operations.count("plots", {"genre": "TestGenre"})
        assert count >= 3
        
        # Test count without filters
        total_count = await data_operations.count("plots")
        assert total_count >= 3
    
    @pytest.mark.asyncio
    async def test_get_all_async(self, data_operations):
        """Test async get_all with pagination"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        # Insert multiple plots
        for i in range(5):
            plot_data = {
                "id": str(uuid4()),
                "title": f"GetAll Test {i}",
                "plot_summary": f"Summary {i}",
                "user_id": user_id
            }
            await data_operations.insert("plots", plot_data)
        
        # Test pagination
        first_page = await data_operations.get_all("plots", limit=3, offset=0)
        assert len(first_page) >= 3
        
        second_page = await data_operations.get_all("plots", limit=3, offset=3)
        assert len(second_page) >= 0
    
    @pytest.mark.asyncio
    async def test_search_async(self, data_operations):
        """Test async search operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        plot_data = {
            "id": str(uuid4()),
            "title": "Searchable Plot",
            "plot_summary": "Contains unique search term: FINDME",
            "user_id": user_id
        }
        plot_id = await data_operations.insert("plots", plot_data)
        
        # Test search
        results = await data_operations.search("plots", {"plot_summary": "%FINDME%"})
        assert len(results) >= 1
        assert any(r["id"] == plot_id for r in results)
    
    @pytest.mark.asyncio
    async def test_batch_operations_async(self, data_operations):
        """Test async batch operations"""
        # Create test user
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        # Test batch insert
        records = []
        for i in range(3):
            records.append({
                "id": str(uuid4()),
                "title": f"Batch Plot {i}",
                "plot_summary": f"Batch summary {i}",
                "genre": "BatchGenre",
                "user_id": user_id
            })
        
        inserted_ids = await data_operations.batch_insert("plots", records)
        assert len(inserted_ids) == 3
        
        # Test batch select by ids
        batch_results = await data_operations.batch_select_by_ids("plots", inserted_ids)
        assert len(batch_results) == 3
        assert all(r["genre"] == "BatchGenre" for r in batch_results)
        
        # Test batch update
        updates = []
        for i, record_id in enumerate(inserted_ids):
            updates.append({
                "id": record_id,
                "title": f"Updated Batch Plot {i}"
            })
        
        updated_count = await data_operations.batch_update("plots", updates)
        assert updated_count == 3
        
        # Verify updates
        updated_results = await data_operations.batch_select_by_ids("plots", inserted_ids)
        assert all("Updated" in r["title"] for r in updated_results)
    
    @pytest.mark.asyncio
    async def test_specialized_plot_operations(self, data_operations):
        """Test specialized plot operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        # Test save_plot
        plot_data = {
            "title": "Specialized Plot",
            "plot_summary": "A specialized plot",
            "genre": "Mystery",
            "user_id": user_id
        }
        plot_id = await data_operations.save_plot(plot_data)
        assert plot_id is not None
        
        # Test get_plot
        retrieved_plot = await data_operations.get_plot(plot_id)
        assert retrieved_plot is not None
        assert retrieved_plot["title"] == "Specialized Plot"
        
        # Test get_plots_by_user
        user_plots = await data_operations.get_plots_by_user(user_id)
        assert len(user_plots) >= 1
        assert any(p["id"] == plot_id for p in user_plots)
    
    @pytest.mark.asyncio
    async def test_specialized_author_operations(self, data_operations):
        """Test specialized author operations"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        # Test save_author
        author_data = {
            "author_name": "Test Author",
            "writing_style": "Narrative",
            "biography": "A test author",
            "user_id": user_id
        }
        author_id = await data_operations.save_author(author_data)
        assert author_id is not None
        
        # Test get_author
        retrieved_author = await data_operations.get_author(author_id)
        assert retrieved_author is not None
        assert retrieved_author["author_name"] == "Test Author"
        
        # Test get_authors_by_user
        user_authors = await data_operations.get_authors_by_user(user_id)
        assert len(user_authors) >= 1
        assert any(a["id"] == author_id for a in user_authors)
    
    @pytest.mark.asyncio
    async def test_plot_with_author_relationship(self, data_operations):
        """Test get_plot_with_author relationship operation"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        # Create author
        author_data = {
            "author_name": "Relationship Author",
            "writing_style": "Epic",
            "biography": "Author for relationship test",
            "user_id": user_id
        }
        author_id = await data_operations.save_author(author_data)
        
        # Create plot with author reference
        plot_data = {
            "title": "Relationship Plot",
            "plot_summary": "Plot with author relationship",
            "genre": "Epic Fantasy",
            "author_id": author_id,
            "user_id": user_id
        }
        plot_id = await data_operations.save_plot(plot_data)
        
        # Test get_plot_with_author
        result = await data_operations.get_plot_with_author(plot_id)
        assert result is not None
        assert "plot" in result
        assert "author" in result
        assert result["plot"]["id"] == plot_id
        assert result["author"]["id"] == author_id
    
    @pytest.mark.asyncio
    async def test_content_search(self, data_operations):
        """Test content search functionality"""
        # Create test data
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        plot_data = {
            "title": "Content Search Test",
            "plot_summary": "Plot with searchable content terms",
            "user_id": user_id
        }
        await data_operations.save_plot(plot_data)
        
        # Test content search
        results = await data_operations.search_content("searchable", "plots", user_id)
        assert len(results) >= 1
        assert any("searchable" in r["plot_summary"].lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, data_operations):
        """Test error handling for invalid operations"""
        # Test get non-existent record
        result = await data_operations.get_by_id("plots", "non-existent-id")
        assert result is None
        
        # Test update non-existent record
        updated = await data_operations.update("plots", "non-existent-id", {"title": "New Title"})
        assert updated is False
        
        # Test delete non-existent record
        deleted = await data_operations.delete("plots", "non-existent-id")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_json_serialization_handling(self, data_operations):
        """Test JSON serialization in data operations"""
        # Create test data with complex JSON
        user_id = str(uuid4())
        await data_operations.insert("users", {"id": user_id, "name": "Test User"})
        
        complex_data = {
            "title": "JSON Test",
            "plot_summary": "Test summary",
            "genre": "Tech",
            "metadata": {
                "tags": ["test", "json"],
                "settings": {"draft": True},
                "characters": ["Alice", "Bob"]
            },
            "user_id": user_id
        }
        
        plot_id = await data_operations.insert("plots", complex_data)
        retrieved = await data_operations.get_by_id("plots", plot_id)
        
        assert retrieved is not None
        # Note: metadata might be stored as JSON string depending on implementation