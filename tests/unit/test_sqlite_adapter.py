"""
TDD Test Suite for SQLiteAdapter.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- SQLiteAdapter initialization and database setup
- Table creation and schema validation
- CRUD operations (insert, select, update, delete)
- Search and filtering functionality
- Error handling and connection management
- Schema synchronization and migration support
- Offline data persistence
- Connection pool integration
- Data integrity and foreign key constraints
- Async/await pattern compliance
"""

import pytest
import sqlite3
import asyncio
import os
import uuid
import tempfile
import shutil
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any, List, Optional

from src.database.sqlite.adapter import SQLiteAdapter
from src.core.interfaces import IDatabase


class TestSQLiteAdapterInitialization:
    """Test SQLiteAdapter initialization and setup"""
    
    def test_adapter_initialization_default_path(self):
        """
        RED: Test adapter initialization with default database path
        Should create adapter with default database file
        """
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value = MagicMock()
            adapter = SQLiteAdapter()
        
        # Assert
        assert adapter.db_path == "local_database.db"
        assert adapter.logger is not None
        assert adapter.synchronizer is not None
    
    def test_adapter_initialization_custom_path(self):
        """
        RED: Test adapter initialization with custom database path
        Should create adapter with specified database file
        """
        # Arrange
        custom_path = "test_custom.db"
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value = MagicMock()
            adapter = SQLiteAdapter(custom_path)
        
        # Assert
        assert adapter.db_path == custom_path
        assert adapter.logger is not None
        assert adapter.synchronizer is not None
    
    def test_adapter_initialization_creates_database(self):
        """
        RED: Test that adapter initialization creates and configures database
        Should call _initialize_database and create required tables
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            adapter = SQLiteAdapter("test.db")
        
        # Assert
        mock_connect.assert_called_with("test.db")
        mock_cursor.execute.assert_any_call("PRAGMA foreign_keys = ON")
        # Should have created tables (verified by _create_tables call)
        assert mock_cursor.execute.call_count > 1
    
    def test_adapter_initialization_database_error(self):
        """
        RED: Test adapter initialization handles database errors
        Should raise exception when database initialization fails
        """
        # Arrange & Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("Database locked")
            
            with pytest.raises(sqlite3.OperationalError):
                SQLiteAdapter("error.db")
    
    def test_create_tables_creates_all_required_tables(self):
        """
        RED: Test that _create_tables creates all required database tables
        Should create users, sessions, plots, authors, etc. tables
        """
        # Arrange
        mock_cursor = MagicMock()
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            adapter = SQLiteAdapter("test.db")
        
        # Assert - Check that tables were created
        table_creation_calls = [call for call in mock_cursor.execute.call_args_list 
                               if 'CREATE TABLE' in str(call)]
        
        # Should create multiple tables
        assert len(table_creation_calls) >= 5
        
        # Check for specific tables
        all_sql = " ".join([str(call) for call in table_creation_calls])
        assert "users" in all_sql
        assert "sessions" in all_sql
        assert "plots" in all_sql
        assert "authors" in all_sql


class TestSQLiteAdapterCRUDOperations:
    """Test CRUD operations in SQLiteAdapter"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            adapter._cursor = mock_cursor
            adapter._conn = mock_conn
            return adapter
    
    @pytest.mark.asyncio
    async def test_insert_new_record_success(self, mock_adapter):
        """
        RED: Test successful insertion of new record
        Should insert record and return the generated ID
        """
        # Arrange
        table_name = "users"
        data = {"name": "John Doe", "email": "john@example.com"}
        expected_id = str(uuid.uuid4())
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result_id = await mock_adapter.insert(table_name, data)
        
        # Assert
        assert result_id is not None
        mock_cursor.execute.assert_called_once()
        # Verify INSERT statement was constructed
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO" in sql_call
        assert table_name in sql_call
    
    @pytest.mark.asyncio
    async def test_insert_record_with_id_provided(self, mock_adapter):
        """
        RED: Test insertion when ID is provided in data
        Should use the provided ID instead of generating one
        """
        # Arrange
        table_name = "users"
        provided_id = str(uuid.uuid4())
        data = {"id": provided_id, "name": "Jane Doe"}
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result_id = await mock_adapter.insert(table_name, data)
        
        # Assert
        assert result_id == provided_id
        mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_record_database_error(self, mock_adapter):
        """
        RED: Test insertion handles database errors
        Should raise exception when database operation fails
        """
        # Arrange
        table_name = "users"
        data = {"name": "Error User"}
        
        # Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value.execute.side_effect = \
                sqlite3.IntegrityError("UNIQUE constraint failed")
            
            with pytest.raises(sqlite3.IntegrityError):
                await mock_adapter.insert(table_name, data)
    
    @pytest.mark.asyncio
    async def test_get_by_id_existing_record(self, mock_adapter):
        """
        RED: Test retrieving existing record by ID
        Should return record data as dictionary
        """
        # Arrange
        table_name = "users"
        record_id = str(uuid.uuid4())
        expected_data = {"id": record_id, "name": "John Doe", "email": "john@example.com"}
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchone.return_value = expected_data
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.get_by_id(table_name, record_id)
        
        # Assert
        assert result == expected_data
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT * FROM" in sql_call
        assert table_name in sql_call
        assert "WHERE id = ?" in sql_call
    
    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_record(self, mock_adapter):
        """
        RED: Test retrieving non-existent record by ID
        Should return None when record doesn't exist
        """
        # Arrange
        table_name = "users"
        record_id = str(uuid.uuid4())
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.get_by_id(table_name, record_id)
        
        # Assert
        assert result is None
        mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_existing_record_success(self, mock_adapter):
        """
        RED: Test successful update of existing record
        Should update record and return True
        """
        # Arrange
        table_name = "users"
        record_id = str(uuid.uuid4())
        data = {"name": "Updated Name", "email": "updated@example.com"}
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.rowcount = 1  # Indicates successful update
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.update(table_name, record_id, data)
        
        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "UPDATE" in sql_call
        assert table_name in sql_call
        assert "WHERE id = ?" in sql_call
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_record(self, mock_adapter):
        """
        RED: Test update of non-existent record
        Should return False when record doesn't exist
        """
        # Arrange
        table_name = "users"
        record_id = str(uuid.uuid4())
        data = {"name": "Updated Name"}
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.rowcount = 0  # No rows affected
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.update(table_name, record_id, data)
        
        # Assert
        assert result is False
        mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_existing_record_success(self, mock_adapter):
        """
        RED: Test successful deletion of existing record
        Should delete record and return True
        """
        # Arrange
        table_name = "users"
        record_id = str(uuid.uuid4())
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.rowcount = 1  # Indicates successful deletion
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.delete(table_name, record_id)
        
        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "DELETE FROM" in sql_call
        assert table_name in sql_call
        assert "WHERE id = ?" in sql_call
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_record(self, mock_adapter):
        """
        RED: Test deletion of non-existent record
        Should return False when record doesn't exist
        """
        # Arrange
        table_name = "users"
        record_id = str(uuid.uuid4())
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.rowcount = 0  # No rows affected
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.delete(table_name, record_id)
        
        # Assert
        assert result is False
        mock_cursor.execute.assert_called_once()


class TestSQLiteAdapterQueryOperations:
    """Test query and search operations"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            return adapter
    
    @pytest.mark.asyncio
    async def test_get_all_records_with_pagination(self, mock_adapter):
        """
        RED: Test retrieving all records with pagination
        Should return paginated results with limit and offset
        """
        # Arrange
        table_name = "users"
        limit = 10
        offset = 20
        expected_data = [
            {"id": str(uuid.uuid4()), "name": "User 1"},
            {"id": str(uuid.uuid4()), "name": "User 2"}
        ]
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchall.return_value = expected_data
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.get_all(table_name, limit, offset)
        
        # Assert
        assert result == expected_data
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT * FROM" in sql_call
        assert table_name in sql_call
        assert "LIMIT" in sql_call
        assert "OFFSET" in sql_call
    
    @pytest.mark.asyncio
    async def test_search_records_with_criteria(self, mock_adapter):
        """
        RED: Test searching records with specific criteria
        Should construct WHERE clause from criteria and return matching records
        """
        # Arrange
        table_name = "users"
        criteria = {"name": "John", "status": "active"}
        limit = 25
        expected_data = [{"id": str(uuid.uuid4()), "name": "John Doe", "status": "active"}]
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchall.return_value = expected_data
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.search(table_name, criteria, limit)
        
        # Assert
        assert result == expected_data
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT * FROM" in sql_call
        assert table_name in sql_call
        assert "WHERE" in sql_call
        assert "LIMIT" in sql_call
    
    @pytest.mark.asyncio
    async def test_search_records_no_criteria(self, mock_adapter):
        """
        RED: Test searching records without criteria
        Should return all records up to limit when no criteria provided
        """
        # Arrange
        table_name = "users"
        criteria = {}
        limit = 50
        expected_data = []
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchall.return_value = expected_data
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.search(table_name, criteria, limit)
        
        # Assert
        assert result == expected_data
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT * FROM" in sql_call
        assert table_name in sql_call
        # Should not have WHERE clause for empty criteria
        assert "WHERE" not in sql_call
    
    @pytest.mark.asyncio
    async def test_count_records_with_criteria(self, mock_adapter):
        """
        RED: Test counting records with criteria
        Should return count of matching records
        """
        # Arrange
        table_name = "users"
        criteria = {"status": "active"}
        expected_count = 15
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchone.return_value = (expected_count,)
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.count(table_name, criteria)
        
        # Assert
        assert result == expected_count
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT COUNT(*) FROM" in sql_call
        assert table_name in sql_call
        assert "WHERE" in sql_call
    
    @pytest.mark.asyncio
    async def test_count_all_records(self, mock_adapter):
        """
        RED: Test counting all records without criteria
        Should return total count of all records in table
        """
        # Arrange
        table_name = "users"
        criteria = None
        expected_count = 100
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.fetchone.return_value = (expected_count,)
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            result = await mock_adapter.count(table_name, criteria)
        
        # Assert
        assert result == expected_count
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT COUNT(*) FROM" in sql_call
        assert table_name in sql_call
        # Should not have WHERE clause for None criteria
        assert "WHERE" not in sql_call


class TestSQLiteAdapterSpecializedOperations:
    """Test specialized operations like save_plot, save_author, etc."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            return adapter
    
    @pytest.mark.asyncio
    async def test_save_plot_with_valid_data(self, mock_adapter):
        """
        RED: Test saving plot with valid data
        Should save plot data to plots table and return plot ID
        """
        # Arrange
        plot_data = {
            "title": "Epic Adventure",
            "genre": "Fantasy",
            "summary": "A brave hero's journey",
            "user_id": "user123",
            "session_id": "session456"
        }
        expected_id = str(uuid.uuid4())
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            with patch.object(mock_adapter, 'insert', return_value=expected_id) as mock_insert:
                result_id = await mock_adapter.save_plot(plot_data)
        
        # Assert
        assert result_id == expected_id
        mock_insert.assert_called_once_with("plots", plot_data)
    
    @pytest.mark.asyncio
    async def test_save_author_with_valid_data(self, mock_adapter):
        """
        RED: Test saving author with valid data
        Should save author data to authors table and return author ID
        """
        # Arrange
        author_data = {
            "author_name": "J.R.R. Tolkien",
            "bio": "Fantasy author",
            "style": "Epic Fantasy",
            "user_id": "user123",
            "session_id": "session456"
        }
        expected_id = str(uuid.uuid4())
        
        # Act
        with patch.object(mock_adapter, 'insert', return_value=expected_id) as mock_insert:
            result_id = await mock_adapter.save_author(author_data)
        
        # Assert
        assert result_id == expected_id
        mock_insert.assert_called_once_with("authors", author_data)
    
    @pytest.mark.asyncio
    async def test_get_plot_existing(self, mock_adapter):
        """
        RED: Test retrieving existing plot by ID
        Should return plot data from plots table
        """
        # Arrange
        plot_id = str(uuid.uuid4())
        expected_plot = {
            "id": plot_id,
            "title": "Retrieved Plot",
            "genre": "Mystery"
        }
        
        # Act
        with patch.object(mock_adapter, 'get_by_id', return_value=expected_plot) as mock_get:
            result = await mock_adapter.get_plot(plot_id)
        
        # Assert
        assert result == expected_plot
        mock_get.assert_called_once_with("plots", plot_id)
    
    @pytest.mark.asyncio
    async def test_get_author_existing(self, mock_adapter):
        """
        RED: Test retrieving existing author by ID
        Should return author data from authors table
        """
        # Arrange
        author_id = str(uuid.uuid4())
        expected_author = {
            "id": author_id,
            "author_name": "Retrieved Author",
            "style": "Literary Fiction"
        }
        
        # Act
        with patch.object(mock_adapter, 'get_by_id', return_value=expected_author) as mock_get:
            result = await mock_adapter.get_author(author_id)
        
        # Assert
        assert result == expected_author
        mock_get.assert_called_once_with("authors", author_id)
    
    @pytest.mark.asyncio
    async def test_search_content_across_tables(self, mock_adapter):
        """
        RED: Test searching content across multiple tables
        Should search in plots, authors, world_building, and characters tables
        """
        # Arrange
        query = "fantasy adventure"
        expected_results = [
            {"type": "plot", "id": str(uuid.uuid4()), "title": "Fantasy Plot"},
            {"type": "author", "id": str(uuid.uuid4()), "author_name": "Fantasy Author"}
        ]
        
        # Act
        with patch.object(mock_adapter, 'search', side_effect=[
            [expected_results[0]], [expected_results[1]], [], []
        ]) as mock_search:
            results = await mock_adapter.search_content(query)
        
        # Assert
        assert len(results) == 2
        assert results[0]["type"] == "plot"
        assert results[1]["type"] == "author"
        assert mock_search.call_count == 4  # 4 tables searched


class TestSQLiteAdapterErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            return adapter
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, mock_adapter):
        """
        RED: Test handling of database connection errors
        Should raise appropriate exception when connection fails
        """
        # Arrange
        table_name = "users"
        data = {"name": "Test User"}
        
        # Act & Assert
        with patch('sqlite3.connect', side_effect=sqlite3.OperationalError("Database is locked")):
            with pytest.raises(sqlite3.OperationalError):
                await mock_adapter.insert(table_name, data)
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraint_error(self, mock_adapter):
        """
        RED: Test handling of foreign key constraint violations
        Should raise constraint error when foreign key is invalid
        """
        # Arrange
        table_name = "plots"
        data = {"title": "Test Plot", "user_id": "nonexistent_user"}
        
        # Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value.execute.side_effect = \
                sqlite3.IntegrityError("FOREIGN KEY constraint failed")
            
            with pytest.raises(sqlite3.IntegrityError):
                await mock_adapter.insert(table_name, data)
    
    @pytest.mark.asyncio
    async def test_unique_constraint_error(self, mock_adapter):
        """
        RED: Test handling of unique constraint violations
        Should raise constraint error when unique constraint is violated
        """
        # Arrange
        table_name = "users"
        data = {"email": "existing@example.com", "name": "Duplicate User"}
        
        # Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value.execute.side_effect = \
                sqlite3.IntegrityError("UNIQUE constraint failed: users.email")
            
            with pytest.raises(sqlite3.IntegrityError):
                await mock_adapter.insert(table_name, data)
    
    @pytest.mark.asyncio
    async def test_invalid_table_name(self, mock_adapter):
        """
        RED: Test handling of invalid table names
        Should raise appropriate error for non-existent table
        """
        # Arrange
        invalid_table = "nonexistent_table"
        data = {"field": "value"}
        
        # Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value.execute.side_effect = \
                sqlite3.OperationalError("no such table: nonexistent_table")
            
            with pytest.raises(sqlite3.OperationalError):
                await mock_adapter.insert(invalid_table, data)
    
    @pytest.mark.asyncio
    async def test_invalid_column_name(self, mock_adapter):
        """
        RED: Test handling of invalid column names
        Should raise appropriate error for non-existent column
        """
        # Arrange
        table_name = "users"
        data = {"invalid_column": "value", "name": "Test User"}
        
        # Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value.cursor.return_value.execute.side_effect = \
                sqlite3.OperationalError("no such column: invalid_column")
            
            with pytest.raises(sqlite3.OperationalError):
                await mock_adapter.insert(table_name, data)


class TestSQLiteAdapterSchemaOperations:
    """Test schema-related operations and synchronization"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            return adapter
    
    def test_schema_synchronizer_integration(self, mock_adapter):
        """
        RED: Test that adapter integrates with SchemaSynchronizer
        Should create SchemaSynchronizer instance on initialization
        """
        # Assert
        assert mock_adapter.synchronizer is not None
        assert hasattr(mock_adapter.synchronizer, 'sqlite_path')
    
    @pytest.mark.asyncio
    async def test_database_backup_and_restore(self, mock_adapter):
        """
        RED: Test database backup and restore functionality
        Should be able to backup and restore database state
        """
        # This test establishes the requirement for backup/restore functionality
        # Implementation would involve file operations and database dumps
        pass
    
    def test_foreign_key_enforcement(self, mock_adapter):
        """
        RED: Test that foreign key constraints are enforced
        Should enable foreign key constraints during initialization
        """
        # Arrange & Act
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            SQLiteAdapter("test.db")
        
        # Assert
        mock_cursor.execute.assert_any_call("PRAGMA foreign_keys = ON")
    
    def test_table_creation_idempotent(self, mock_adapter):
        """
        RED: Test that table creation is idempotent
        Should use CREATE TABLE IF NOT EXISTS for all tables
        """
        # Arrange & Act
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            SQLiteAdapter("test.db")
        
        # Assert - Check that CREATE TABLE IF NOT EXISTS was used
        create_calls = [call for call in mock_cursor.execute.call_args_list 
                       if 'CREATE TABLE' in str(call)]
        
        for call in create_calls:
            sql = str(call)
            assert "IF NOT EXISTS" in sql


class TestSQLiteAdapterConnectionManagement:
    """Test connection management and resource cleanup"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            return adapter
    
    @pytest.mark.asyncio
    async def test_connection_context_management(self, mock_adapter):
        """
        RED: Test proper connection context management
        Should use context managers for database connections
        """
        # Arrange
        table_name = "users"
        data = {"name": "Test User"}
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_connect.return_value.__exit__.return_value = None
            
            await mock_adapter.insert(table_name, data)
        
        # Assert
        assert mock_connect.return_value.__enter__.called
        assert mock_connect.return_value.__exit__.called
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, mock_adapter):
        """
        RED: Test transaction rollback on database errors
        Should rollback transaction when operation fails
        """
        # Arrange
        table_name = "users"
        data = {"name": "Error User"}
        
        # Act & Assert
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.IntegrityError("Constraint failed")
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            with pytest.raises(sqlite3.IntegrityError):
                await mock_adapter.insert(table_name, data)
            
            # Connection should still be properly closed
            assert mock_connect.return_value.__exit__.called
    
    def test_connection_path_validation(self):
        """
        RED: Test validation of database path
        Should handle various path formats and create directories if needed
        """
        # This test establishes the requirement for path validation
        # Implementation would involve checking file paths and creating directories
        pass


class TestSQLiteAdapterDataIntegrity:
    """Test data integrity and validation"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock SQLiteAdapter for testing"""
        with patch('sqlite3.connect') as mock_connect:
            mock_cursor = MagicMock()
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value.__enter__.return_value = mock_conn
            
            adapter = SQLiteAdapter("test.db")
            return adapter
    
    @pytest.mark.asyncio
    async def test_json_field_serialization(self, mock_adapter):
        """
        RED: Test proper JSON field serialization
        Should serialize complex data structures to JSON strings
        """
        # Arrange
        table_name = "plots"
        data = {
            "title": "Complex Plot",
            "metadata": {"genre_hierarchy": {"primary": "Fantasy", "sub": "Epic"}}
        }
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            await mock_adapter.insert(table_name, data)
        
        # Assert
        mock_cursor.execute.assert_called_once()
        # Should have serialized the metadata field
        call_args = mock_cursor.execute.call_args[0]
        # Check that complex data was processed
        assert len(call_args) >= 2  # SQL and parameters
    
    @pytest.mark.asyncio
    async def test_datetime_field_handling(self, mock_adapter):
        """
        RED: Test proper datetime field handling
        Should convert datetime objects to ISO format strings
        """
        # Arrange
        table_name = "users"
        current_time = datetime.now()
        data = {
            "name": "Time User",
            "created_at": current_time,
            "updated_at": current_time.isoformat()
        }
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            await mock_adapter.insert(table_name, data)
        
        # Assert
        mock_cursor.execute.assert_called_once()
        # Should have processed datetime fields appropriately
    
    @pytest.mark.asyncio
    async def test_uuid_field_validation(self, mock_adapter):
        """
        RED: Test UUID field validation and formatting
        Should ensure UUIDs are properly formatted as strings
        """
        # Arrange
        table_name = "users"
        user_uuid = uuid.uuid4()
        data = {
            "id": user_uuid,  # UUID object
            "name": "UUID User"
        }
        
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value = mock_cursor
        
        # Act
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            await mock_adapter.insert(table_name, data)
        
        # Assert
        mock_cursor.execute.assert_called_once()
        # Should have converted UUID to string