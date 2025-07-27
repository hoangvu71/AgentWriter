"""
TDD Tests for SQLite Connection Manager Module.
This will be extracted from SQLiteAdapter for better modularity.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
import sqlite3

from src.database.sqlite.connection_manager import SQLiteConnectionManager


class TestSQLiteConnectionManager:
    """TDD tests for SQLite connection management functionality"""
    
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
        """Create connection manager with temporary database"""
        return SQLiteConnectionManager(temp_db_path)
    
    def test_initialization(self, temp_db_path):
        """Test connection manager initialization"""
        manager = SQLiteConnectionManager(temp_db_path)
        assert manager.db_path == temp_db_path
        assert os.path.exists(temp_db_path)
    
    def test_get_connection(self, connection_manager):
        """Test getting database connection"""
        conn = connection_manager.get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        
        # Test connection works
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        conn.close()
    
    def test_context_manager(self, connection_manager):
        """Test connection manager as context manager"""
        with connection_manager.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_factory_settings(self, connection_manager):
        """Test connection has proper factory settings"""
        conn = connection_manager.get_connection()
        assert conn.row_factory == sqlite3.Row
        
        # Test foreign keys are enabled
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1  # Foreign keys enabled
        conn.close()
    
    def test_execute_query(self, connection_manager):
        """Test query execution through connection manager"""
        # Create a test table
        with connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_table (
                    id TEXT PRIMARY KEY,
                    name TEXT
                )
            """)
            conn.commit()
        
        # Test insert
        query = "INSERT INTO test_table (id, name) VALUES (?, ?)"
        connection_manager.execute_query(query, ["test-id", "test-name"])
        
        # Test select
        results = connection_manager.execute_select("SELECT * FROM test_table")
        assert len(results) == 1
        assert results[0]["id"] == "test-id"
        assert results[0]["name"] == "test-name"
    
    def test_execute_select_with_parameters(self, connection_manager):
        """Test parameterized select queries"""
        # Setup test data
        with connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_table (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    value INTEGER
                )
            """)
            cursor.execute("INSERT INTO test_table VALUES (?, ?, ?)", ["1", "A", 100])
            cursor.execute("INSERT INTO test_table VALUES (?, ?, ?)", ["2", "B", 200])
            cursor.execute("INSERT INTO test_table VALUES (?, ?, ?)", ["3", "A", 300])
            conn.commit()
        
        # Test filtered select
        results = connection_manager.execute_select(
            "SELECT * FROM test_table WHERE category = ?", 
            ["A"]
        )
        assert len(results) == 2
        assert all(r["category"] == "A" for r in results)
    
    def test_execute_count(self, connection_manager):
        """Test count queries"""
        # Setup test data
        with connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_table (
                    id TEXT PRIMARY KEY,
                    category TEXT
                )
            """)
            cursor.execute("INSERT INTO test_table VALUES (?, ?)", ["1", "A"])
            cursor.execute("INSERT INTO test_table VALUES (?, ?)", ["2", "B"])
            cursor.execute("INSERT INTO test_table VALUES (?, ?)", ["3", "A"])
            conn.commit()
        
        # Test count
        count = connection_manager.execute_count("SELECT COUNT(*) FROM test_table")
        assert count == 3
        
        # Test filtered count
        count = connection_manager.execute_count(
            "SELECT COUNT(*) FROM test_table WHERE category = ?", 
            ["A"]
        )
        assert count == 2
    
    def test_transaction_handling(self, connection_manager):
        """Test transaction management"""
        # Setup test table
        with connection_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE test_table (
                    id TEXT PRIMARY KEY,
                    name TEXT
                )
            """)
            conn.commit()
        
        # Test successful transaction
        with connection_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO test_table VALUES (?, ?)", ["1", "test1"])
            cursor.execute("INSERT INTO test_table VALUES (?, ?)", ["2", "test2"])
        
        # Verify data was committed
        results = connection_manager.execute_select("SELECT COUNT(*) as count FROM test_table")
        assert results[0]["count"] == 2
        
        # Test failed transaction (should rollback)
        try:
            with connection_manager.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO test_table VALUES (?, ?)", ["3", "test3"])
                # Simulate error
                raise Exception("Test error")
        except Exception:
            pass
        
        # Verify rollback occurred
        results = connection_manager.execute_select("SELECT COUNT(*) as count FROM test_table")
        assert results[0]["count"] == 2  # Should still be 2
    
    def test_close_functionality(self, connection_manager):
        """Test connection manager cleanup"""
        # Use connection
        conn = connection_manager.get_connection()
        conn.close()
        
        # Close manager
        connection_manager.close()
        
        # Should not raise errors on multiple closes
        connection_manager.close()