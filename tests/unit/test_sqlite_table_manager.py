"""
TDD Tests for SQLite Table Manager Module.
This will handle database schema creation and management.
"""

import pytest
import tempfile
import os
import sqlite3

from src.database.sqlite.table_manager import SQLiteTableManager
from src.database.sqlite.connection_manager import SQLiteConnectionManager


class TestSQLiteTableManager:
    """TDD tests for SQLite table management functionality"""
    
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
    def table_manager(self, connection_manager):
        """Create table manager"""
        return SQLiteTableManager(connection_manager)
    
    def test_initialization(self, connection_manager):
        """Test table manager initialization"""
        manager = SQLiteTableManager(connection_manager)
        assert manager.connection_manager == connection_manager
    
    def test_create_all_tables(self, table_manager, connection_manager):
        """Test creating all required tables"""
        table_manager.create_all_tables()
        
        # Verify all expected tables exist
        expected_tables = [
            'users', 'sessions', 'authors', 'plots', 
            'world_building', 'characters', 'content_ratings', 
            'lore_documents', 'lore_clusters'
        ]
        
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = connection_manager.execute_select(query)
        table_names = [row['name'] for row in results]
        
        for expected_table in expected_tables:
            assert expected_table in table_names
    
    def test_create_users_table(self, table_manager, connection_manager):
        """Test users table creation"""
        table_manager.create_users_table()
        
        # Verify table structure
        query = "PRAGMA table_info(users)"
        results = connection_manager.execute_select(query)
        
        column_names = [row['name'] for row in results]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'created_at' in column_names
        
        # Verify primary key
        pk_columns = [row['name'] for row in results if row['pk']]
        assert 'id' in pk_columns
    
    def test_create_sessions_table(self, table_manager, connection_manager):
        """Test sessions table creation with foreign key"""
        table_manager.create_users_table()  # Create dependency first
        table_manager.create_sessions_table()
        
        # Verify table structure
        query = "PRAGMA table_info(sessions)"
        results = connection_manager.execute_select(query)
        
        column_names = [row['name'] for row in results]
        assert 'id' in column_names
        assert 'user_id' in column_names
        assert 'start_time' in column_names
        assert 'end_time' in column_names
        assert 'messages' in column_names
        
        # Verify foreign key constraint
        query = "PRAGMA foreign_key_list(sessions)"
        fk_results = connection_manager.execute_select(query)
        assert len(fk_results) >= 1
        assert any(fk['table'] == 'users' for fk in fk_results)
    
    def test_create_authors_table(self, table_manager, connection_manager):
        """Test authors table creation"""
        table_manager.create_users_table()
        table_manager.create_sessions_table()
        table_manager.create_authors_table()
        
        # Verify table structure
        query = "PRAGMA table_info(authors)"
        results = connection_manager.execute_select(query)
        
        column_names = [row['name'] for row in results]
        expected_columns = [
            'id', 'session_id', 'user_id', 'author_name', 
            'pen_name', 'biography', 'writing_style', 'created_at'
        ]
        
        for col in expected_columns:
            assert col in column_names
        
        # Verify NOT NULL constraints
        not_null_columns = [row['name'] for row in results if row['notnull']]
        assert 'author_name' in not_null_columns
    
    def test_create_plots_table(self, table_manager, connection_manager):
        """Test plots table creation with multiple foreign keys"""
        # Create dependencies
        table_manager.create_users_table()
        table_manager.create_sessions_table()
        table_manager.create_authors_table()
        table_manager.create_plots_table()
        
        # Verify table structure
        query = "PRAGMA table_info(plots)"
        results = connection_manager.execute_select(query)
        
        column_names = [row['name'] for row in results]
        expected_columns = [
            'id', 'session_id', 'user_id', 'author_id', 'title', 
            'plot_summary', 'genre', 'subgenre', 'microgenre', 
            'trope', 'tone', 'target_audience', 'created_at'
        ]
        
        for col in expected_columns:
            assert col in column_names
        
        # Verify NOT NULL constraints
        not_null_columns = [row['name'] for row in results if row['notnull']]
        assert 'title' in not_null_columns
        assert 'plot_summary' in not_null_columns
        
        # Verify foreign keys
        query = "PRAGMA foreign_key_list(plots)"
        fk_results = connection_manager.execute_select(query)
        fk_tables = [fk['table'] for fk in fk_results]
        assert 'users' in fk_tables
        assert 'sessions' in fk_tables
        assert 'authors' in fk_tables
    
    def test_create_world_building_table(self, table_manager, connection_manager):
        """Test world_building table creation with JSON fields"""
        # Create dependencies
        table_manager.create_users_table()
        table_manager.create_sessions_table()
        table_manager.create_authors_table()
        table_manager.create_plots_table()
        table_manager.create_world_building_table()
        
        # Verify table structure
        query = "PRAGMA table_info(world_building)"
        results = connection_manager.execute_select(query)
        
        column_names = [row['name'] for row in results]
        expected_columns = [
            'id', 'session_id', 'user_id', 'plot_id', 'world_name',
            'world_type', 'overview', 'geography', 'political_landscape',
            'cultural_systems', 'economic_framework', 'historical_timeline',
            'power_systems', 'languages_and_communication', 
            'religious_and_belief_systems', 'unique_elements', 
            'created_at', 'updated_at'
        ]
        
        for col in expected_columns:
            assert col in column_names
        
        # Verify NOT NULL constraints with defaults
        not_null_columns = [row['name'] for row in results if row['notnull']]
        assert 'world_name' in not_null_columns
        assert 'world_type' in not_null_columns
        assert 'overview' in not_null_columns
    
    def test_create_characters_table(self, table_manager, connection_manager):
        """Test characters table creation"""
        # Create dependencies
        table_manager.create_users_table()
        table_manager.create_sessions_table()
        table_manager.create_authors_table()
        table_manager.create_plots_table()
        table_manager.create_world_building_table()
        table_manager.create_characters_table()
        
        # Verify table structure
        query = "PRAGMA table_info(characters)"
        results = connection_manager.execute_select(query)
        
        column_names = [row['name'] for row in results]
        expected_columns = [
            'id', 'session_id', 'user_id', 'plot_id', 'world_id',
            'character_count', 'world_context_integration', 'characters',
            'additional_context', 'created_at', 'updated_at'
        ]
        
        for col in expected_columns:
            assert col in column_names
    
    def test_create_indexes(self, table_manager, connection_manager):
        """Test index creation for performance"""
        # Create all tables first
        table_manager.create_all_tables()
        table_manager.create_indexes()
        
        # Verify indexes exist
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        results = connection_manager.execute_select(query)
        index_names = [row['name'] for row in results]
        
        expected_indexes = [
            'idx_sessions_user_id',
            'idx_authors_user_id',
            'idx_plots_user_id',
            'idx_plots_author_id',
            'idx_world_building_plot_id',
            'idx_characters_plot_id',
            'idx_content_ratings_content_id',
            'idx_lore_documents_cluster_id'
        ]
        
        for expected_index in expected_indexes:
            assert expected_index in index_names
    
    def test_table_exists_check(self, table_manager, connection_manager):
        """Test checking if tables exist"""
        # Initially no tables should exist (except sqlite_master)
        assert not table_manager.table_exists('users')
        assert not table_manager.table_exists('plots')
        
        # Create a table
        table_manager.create_users_table()
        
        # Now it should exist
        assert table_manager.table_exists('users')
        assert not table_manager.table_exists('plots')  # Still doesn't exist
    
    def test_get_table_schema(self, table_manager, connection_manager):
        """Test getting table schema information"""
        table_manager.create_users_table()
        
        schema = table_manager.get_table_schema('users')
        
        assert len(schema) >= 3  # id, name, created_at
        
        # Check schema structure
        column_names = [col['name'] for col in schema]
        assert 'id' in column_names
        assert 'name' in column_names
        assert 'created_at' in column_names
        
        # Check column details
        id_column = next(col for col in schema if col['name'] == 'id')
        assert id_column['type'] == 'TEXT'
        assert id_column['pk'] == 1  # Primary key
    
    def test_drop_table(self, table_manager, connection_manager):
        """Test dropping tables"""
        # Create table
        table_manager.create_users_table()
        assert table_manager.table_exists('users')
        
        # Drop table
        table_manager.drop_table('users')
        assert not table_manager.table_exists('users')
    
    def test_recreate_tables(self, table_manager, connection_manager):
        """Test recreating all tables (drop and create)"""
        # Create initial tables
        table_manager.create_all_tables()
        
        # Add some test data
        connection_manager.execute_query(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ["test-id", "Test User"]
        )
        
        # Verify data exists
        results = connection_manager.execute_select("SELECT * FROM users")
        assert len(results) == 1
        
        # Recreate tables (should drop and recreate)
        table_manager.recreate_all_tables()
        
        # Data should be gone, but tables should exist
        assert table_manager.table_exists('users')
        results = connection_manager.execute_select("SELECT * FROM users")
        assert len(results) == 0
    
    def test_foreign_key_enforcement(self, table_manager, connection_manager):
        """Test that foreign key constraints are properly enforced"""
        table_manager.create_all_tables()
        
        # Try to insert plot without user (should fail)
        with pytest.raises(sqlite3.IntegrityError):
            connection_manager.execute_query(
                "INSERT INTO plots (id, title, plot_summary, user_id) VALUES (?, ?, ?, ?)",
                ["plot-id", "Test Plot", "Test Summary", "non-existent-user"]
            )
        
        # Insert user first
        connection_manager.execute_query(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ["user-id", "Test User"]
        )
        
        # Now plot insert should work
        connection_manager.execute_query(
            "INSERT INTO plots (id, title, plot_summary, user_id) VALUES (?, ?, ?, ?)",
            ["plot-id", "Test Plot", "Test Summary", "user-id"]
        )
        
        # Verify insert succeeded
        results = connection_manager.execute_select("SELECT * FROM plots WHERE id = ?", ["plot-id"])
        assert len(results) == 1