"""
TDD Tests for SQLite Index Manager Module.
This will handle database index creation, management, and optimization.
"""

import pytest
import tempfile
import os

from src.database.sqlite.index_manager import SQLiteIndexManager
from src.database.sqlite.connection_manager import SQLiteConnectionManager


class TestSQLiteIndexManager:
    """TDD tests for SQLite index management functionality"""
    
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
    def index_manager(self, connection_manager):
        """Create index manager"""
        return SQLiteIndexManager(connection_manager)
    
    @pytest.fixture
    def setup_basic_tables(self, connection_manager):
        """Setup basic tables for index testing"""
        # Create users table
        connection_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create sessions table
        connection_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                messages TEXT DEFAULT '[]',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create plots table
        connection_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS plots (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                author_id TEXT,
                title TEXT NOT NULL,
                plot_summary TEXT NOT NULL,
                genre TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
    
    def test_initialization(self, connection_manager):
        """Test index manager initialization"""
        manager = SQLiteIndexManager(connection_manager)
        assert manager.connection_manager == connection_manager
        assert hasattr(manager, 'logger')
    
    def test_create_single_index(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating a single index"""
        index_manager.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
        
        # Verify index exists
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_sessions_user_id'"
        results = connection_manager.execute_select(query)
        assert len(results) == 1
        assert results[0]['name'] == 'idx_sessions_user_id'
    
    def test_create_composite_index(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating a composite index"""
        index_manager.create_index('idx_plots_user_genre', 'plots', ['user_id', 'genre'])
        
        # Verify index exists
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_plots_user_genre'"
        results = connection_manager.execute_select(query)
        assert len(results) == 1
        assert results[0]['name'] == 'idx_plots_user_genre'
    
    def test_create_unique_index(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating a unique index"""
        index_manager.create_index(
            'idx_users_name_unique', 
            'users', 
            ['name'], 
            unique=True
        )
        
        # Verify index exists
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_users_name_unique'"
        results = connection_manager.execute_select(query)
        assert len(results) == 1
        assert results[0]['name'] == 'idx_users_name_unique'
    
    def test_create_partial_index(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating a partial index with WHERE clause"""
        index_manager.create_index(
            'idx_plots_active_title', 
            'plots', 
            ['title'], 
            where_clause="genre IS NOT NULL"
        )
        
        # Verify index exists
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_plots_active_title'"
        results = connection_manager.execute_select(query)
        assert len(results) == 1
    
    def test_create_if_not_exists(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating index with IF NOT EXISTS"""
        # Create index first time
        index_manager.create_index('idx_test', 'users', ['id'])
        
        # Create same index again - should not raise error
        index_manager.create_index('idx_test', 'users', ['id'])
        
        # Verify only one index exists
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_test'"
        results = connection_manager.execute_select(query)
        assert len(results) == 1
    
    def test_create_all_core_indexes(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating all core performance indexes"""
        index_manager.create_all_core_indexes()
        
        # Verify expected indexes exist
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        results = connection_manager.execute_select(query)
        index_names = [row['name'] for row in results]
        
        expected_indexes = [
            'idx_sessions_user_id',
            'idx_plots_user_id',
            'idx_plots_session_id'
        ]
        
        for expected_index in expected_indexes:
            assert expected_index in index_names
    
    def test_create_all_indexes(self, index_manager, connection_manager, setup_basic_tables):
        """Test creating all performance indexes"""
        # Add more tables for comprehensive testing
        connection_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS authors (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                author_name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        connection_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS world_building (
                id TEXT PRIMARY KEY,
                plot_id TEXT,
                user_id TEXT,
                world_name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        index_manager.create_all_indexes()
        
        # Verify comprehensive indexes exist
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        results = connection_manager.execute_select(query)
        index_names = [row['name'] for row in results]
        
        expected_indexes = [
            'idx_sessions_user_id',
            'idx_authors_session_id',
            'idx_authors_user_id',
            'idx_plots_session_id',
            'idx_plots_user_id',
            'idx_world_building_plot_id'
        ]
        
        for expected_index in expected_indexes:
            assert expected_index in index_names
    
    def test_drop_index(self, index_manager, connection_manager, setup_basic_tables):
        """Test dropping an index"""
        # Create index first
        index_manager.create_index('idx_to_drop', 'users', ['name'])
        
        # Verify it exists
        assert index_manager.index_exists('idx_to_drop')
        
        # Drop the index
        index_manager.drop_index('idx_to_drop')
        
        # Verify it's gone
        assert not index_manager.index_exists('idx_to_drop')
    
    def test_index_exists_check(self, index_manager, connection_manager, setup_basic_tables):
        """Test checking if an index exists"""
        # Initially should not exist
        assert not index_manager.index_exists('idx_test_existence')
        
        # Create index
        index_manager.create_index('idx_test_existence', 'users', ['id'])
        
        # Now should exist
        assert index_manager.index_exists('idx_test_existence')
    
    def test_get_all_indexes(self, index_manager, connection_manager, setup_basic_tables):
        """Test getting all indexes"""
        # Create some indexes
        index_manager.create_index('idx_test1', 'users', ['name'])
        index_manager.create_index('idx_test2', 'sessions', ['user_id'])
        
        indexes = index_manager.get_all_indexes()
        index_names = [idx['name'] for idx in indexes]
        
        assert 'idx_test1' in index_names
        assert 'idx_test2' in index_names
        # Should not include system indexes
        assert not any('sqlite_' in name for name in index_names)
    
    def test_get_table_indexes(self, index_manager, connection_manager, setup_basic_tables):
        """Test getting indexes for a specific table"""
        # Create indexes on different tables
        index_manager.create_index('idx_users_name', 'users', ['name'])
        index_manager.create_index('idx_users_created', 'users', ['created_at'])
        index_manager.create_index('idx_sessions_user', 'sessions', ['user_id'])
        
        # Get indexes for users table only
        user_indexes = index_manager.get_table_indexes('users')
        index_names = [idx['name'] for idx in user_indexes]
        
        assert 'idx_users_name' in index_names
        assert 'idx_users_created' in index_names
        assert 'idx_sessions_user' not in index_names  # Should not include other tables
    
    def test_analyze_table_performance(self, index_manager, connection_manager, setup_basic_tables):
        """Test analyzing table performance statistics"""
        # Insert some test data
        connection_manager.execute_query(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ["user1", "Test User 1"]
        )
        connection_manager.execute_query(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ["user2", "Test User 2"]
        )
        
        # Analyze table
        stats = index_manager.analyze_table_performance('users')
        
        assert 'table_name' in stats
        assert stats['table_name'] == 'users'
        assert 'row_count' in stats
        assert stats['row_count'] >= 2  # At least our test data
    
    def test_reindex_table(self, index_manager, connection_manager, setup_basic_tables):
        """Test reindexing a table"""
        # Create some indexes
        index_manager.create_index('idx_users_name', 'users', ['name'])
        index_manager.create_index('idx_users_created', 'users', ['created_at'])
        
        # Reindex should not raise errors
        index_manager.reindex_table('users')
        
        # Indexes should still exist
        assert index_manager.index_exists('idx_users_name')
        assert index_manager.index_exists('idx_users_created')
    
    def test_rebuild_all_indexes(self, index_manager, connection_manager, setup_basic_tables):
        """Test rebuilding all indexes"""
        # Create some indexes
        index_manager.create_index('idx_users_name', 'users', ['name'])
        index_manager.create_index('idx_sessions_user', 'sessions', ['user_id'])
        
        # Rebuild all should not raise errors
        index_manager.rebuild_all_indexes()
        
        # Indexes should still exist
        assert index_manager.index_exists('idx_users_name')
        assert index_manager.index_exists('idx_sessions_user')
    
    def test_get_index_usage_stats(self, index_manager, connection_manager, setup_basic_tables):
        """Test getting index usage statistics"""
        # Create index
        index_manager.create_index('idx_users_name', 'users', ['name'])
        
        # Insert some data
        connection_manager.execute_query(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            ["user1", "Test User"]
        )
        
        # Query using the index
        connection_manager.execute_select("SELECT * FROM users WHERE name = ?", ["Test User"])
        
        # Get usage stats
        stats = index_manager.get_index_usage_stats('idx_users_name')
        
        assert 'index_name' in stats
        assert stats['index_name'] == 'idx_users_name'
    
    def test_optimize_indexes(self, index_manager, connection_manager, setup_basic_tables):
        """Test optimizing indexes"""
        # Create some indexes
        index_manager.create_index('idx_users_name', 'users', ['name'])
        index_manager.create_index('idx_sessions_user', 'sessions', ['user_id'])
        
        # Optimize should not raise errors and return results
        optimization_results = index_manager.optimize_indexes()
        
        assert isinstance(optimization_results, list)
        # Should have information about optimization actions
        for result in optimization_results:
            assert 'action' in result
            assert 'table' in result