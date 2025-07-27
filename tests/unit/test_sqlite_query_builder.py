"""
TDD Tests for SQLite Query Builder Module.
This will be extracted from SQLiteAdapter for better modularity.
"""

import pytest
from typing import Dict, Any, List, Optional

from src.database.sqlite.query_builder import SQLiteQueryBuilder


class TestSQLiteQueryBuilder:
    """TDD tests for SQLite query building functionality"""
    
    @pytest.fixture
    def query_builder(self):
        """Create query builder instance"""
        return SQLiteQueryBuilder()
    
    def test_build_insert_query(self, query_builder):
        """Test building INSERT queries"""
        data = {"id": "test-id", "name": "Test Name", "value": 123}
        
        query, params = query_builder.build_insert("test_table", data)
        
        expected_query = "INSERT INTO test_table (id, name, value) VALUES (?, ?, ?)"
        assert query == expected_query
        assert params == ["test-id", "Test Name", 123]
    
    def test_build_select_query_basic(self, query_builder):
        """Test building basic SELECT queries"""
        query, params = query_builder.build_select("test_table")
        
        assert query == "SELECT * FROM test_table"
        assert params == []
    
    def test_build_select_query_with_filters(self, query_builder):
        """Test building SELECT queries with WHERE filters"""
        filters = {"category": "A", "status": "active"}
        
        query, params = query_builder.build_select("test_table", filters=filters)
        
        expected_query = "SELECT * FROM test_table WHERE category = ? AND status = ?"
        assert query == expected_query
        assert set(params) == {"A", "active"}  # Order might vary due to dict iteration
    
    def test_build_select_query_with_order_by(self, query_builder):
        """Test building SELECT queries with ORDER BY"""
        query, params = query_builder.build_select(
            "test_table", 
            order_by="created_at", 
            desc=True
        )
        
        assert query == "SELECT * FROM test_table ORDER BY created_at DESC"
        assert params == []
    
    def test_build_select_query_with_limit(self, query_builder):
        """Test building SELECT queries with LIMIT"""
        query, params = query_builder.build_select("test_table", limit=10)
        
        assert query == "SELECT * FROM test_table LIMIT 10"
        assert params == []
    
    def test_build_select_query_complex(self, query_builder):
        """Test building complex SELECT queries with all options"""
        filters = {"genre": "Fantasy", "status": "published"}
        
        query, params = query_builder.build_select(
            "books",
            filters=filters,
            order_by="publication_date",
            desc=True,
            limit=5
        )
        
        expected_query = "SELECT * FROM books WHERE genre = ? AND status = ? ORDER BY publication_date DESC LIMIT 5"
        assert query == expected_query
        assert set(params) == {"Fantasy", "published"}
    
    def test_build_update_query(self, query_builder):
        """Test building UPDATE queries"""
        data = {"name": "Updated Name", "status": "inactive"}
        
        query, params = query_builder.build_update("test_table", "test-id", data)
        
        expected_query = "UPDATE test_table SET name = ?, status = ? WHERE id = ?"
        assert query == expected_query
        # Parameters should end with the ID
        assert params[-1] == "test-id"
        assert set(params[:-1]) == {"Updated Name", "inactive"}
    
    def test_build_delete_query(self, query_builder):
        """Test building DELETE queries"""
        query, params = query_builder.build_delete("test_table", "test-id")
        
        assert query == "DELETE FROM test_table WHERE id = ?"
        assert params == ["test-id"]
    
    def test_build_count_query_basic(self, query_builder):
        """Test building basic COUNT queries"""
        query, params = query_builder.build_count("test_table")
        
        assert query == "SELECT COUNT(*) FROM test_table"
        assert params == []
    
    def test_build_count_query_with_filters(self, query_builder):
        """Test building COUNT queries with filters"""
        filters = {"category": "A", "active": True}
        
        query, params = query_builder.build_count("test_table", filters)
        
        expected_query = "SELECT COUNT(*) FROM test_table WHERE category = ? AND active = ?"
        assert query == expected_query
        assert set(params) == {"A", True}
    
    def test_build_search_query(self, query_builder):
        """Test building search queries with LIKE conditions"""
        search_criteria = {"title": "%fantasy%", "description": "%magic%"}
        
        query, params = query_builder.build_search("books", search_criteria, limit=10)
        
        expected_query = "SELECT * FROM books WHERE title LIKE ? AND description LIKE ? LIMIT 10"
        assert query == expected_query
        assert set(params) == {"%fantasy%", "%magic%"}
    
    def test_build_batch_insert_query(self, query_builder):
        """Test building batch INSERT queries"""
        records = [
            {"id": "1", "name": "Name1", "value": 100},
            {"id": "2", "name": "Name2", "value": 200},
            {"id": "3", "name": "Name3", "value": 300}
        ]
        
        query, params = query_builder.build_batch_insert("test_table", records)
        
        expected_query = "INSERT INTO test_table (id, name, value) VALUES (?, ?, ?), (?, ?, ?), (?, ?, ?)"
        assert query == expected_query
        assert len(params) == 9  # 3 records × 3 fields each
        assert params[0:3] == ["1", "Name1", 100]
        assert params[3:6] == ["2", "Name2", 200]
        assert params[6:9] == ["3", "Name3", 300]
    
    def test_build_select_by_ids_query(self, query_builder):
        """Test building SELECT queries for multiple IDs"""
        ids = ["id1", "id2", "id3"]
        
        query, params = query_builder.build_select_by_ids("test_table", ids)
        
        expected_query = "SELECT * FROM test_table WHERE id IN (?, ?, ?)"
        assert query == expected_query
        assert params == ids
    
    def test_sanitize_column_names(self, query_builder):
        """Test column name sanitization for security"""
        # Test valid column names
        assert query_builder.sanitize_column_name("valid_column") == "valid_column"
        assert query_builder.sanitize_column_name("Column123") == "Column123"
        assert query_builder.sanitize_column_name("snake_case_column") == "snake_case_column"
        
        # Test invalid column names should raise error
        with pytest.raises(ValueError):
            query_builder.sanitize_column_name("invalid; DROP TABLE")
        
        with pytest.raises(ValueError):
            query_builder.sanitize_column_name("invalid--comment")
        
        with pytest.raises(ValueError):
            query_builder.sanitize_column_name("invalid/*comment*/")
    
    def test_sanitize_table_names(self, query_builder):
        """Test table name sanitization for security"""
        # Test valid table names
        assert query_builder.sanitize_table_name("valid_table") == "valid_table"
        assert query_builder.sanitize_table_name("Table123") == "Table123"
        
        # Test invalid table names should raise error
        with pytest.raises(ValueError):
            query_builder.sanitize_table_name("invalid; DROP TABLE")
        
        with pytest.raises(ValueError):
            query_builder.sanitize_table_name("invalid table")  # spaces not allowed
    
    def test_empty_data_handling(self, query_builder):
        """Test handling of empty data structures"""
        # Empty insert should raise error
        with pytest.raises(ValueError):
            query_builder.build_insert("test_table", {})
        
        # Empty update should raise error
        with pytest.raises(ValueError):
            query_builder.build_update("test_table", "test-id", {})
        
        # Empty batch insert should raise error
        with pytest.raises(ValueError):
            query_builder.build_batch_insert("test_table", [])
        
        # Empty IDs list should raise error
        with pytest.raises(ValueError):
            query_builder.build_select_by_ids("test_table", [])
    
    def test_special_characters_in_values(self, query_builder):
        """Test handling of special characters in data values"""
        data = {
            "title": "Book with 'quotes' and \"double quotes\"",
            "description": "Text with ; semicolon and -- comment",
            "content": "Multi\nline\ntext"
        }
        
        query, params = query_builder.build_insert("books", data)
        
        # Query structure should be safe
        expected_query = "INSERT INTO books (title, description, content) VALUES (?, ?, ?)"
        assert query == expected_query
        
        # Parameters should contain the original values
        assert "Book with 'quotes' and \"double quotes\"" in params
        assert "Text with ; semicolon and -- comment" in params
        assert "Multi\nline\ntext" in params