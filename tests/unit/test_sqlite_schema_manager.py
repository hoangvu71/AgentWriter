"""
TDD Tests for SQLite Schema Manager Module.
This will handle database table schema creation and management.
"""

import pytest
import tempfile
import os
import sqlite3

from src.database.sqlite.schema_manager import SQLiteSchemaManager
from src.database.sqlite.connection_manager import SQLiteConnectionManager


class TestSQLiteSchemaManager:
    """TDD tests for SQLite schema management functionality"""
    
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
    def schema_manager(self, connection_manager):
        """Create schema manager"""
        return SQLiteSchemaManager(connection_manager)
    
    def test_initialization(self, connection_manager):
        """Test schema manager initialization"""
        manager = SQLiteSchemaManager(connection_manager)
        assert manager.connection_manager == connection_manager
        assert hasattr(manager, 'logger')
    
    def test_create_users_table(self, schema_manager, connection_manager):
        """Test users table creation"""
        schema_manager.create_users_table()
        
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
    
    def test_create_sessions_table(self, schema_manager, connection_manager):
        """Test sessions table creation with foreign key"""
        schema_manager.create_users_table()  # Create dependency first
        schema_manager.create_sessions_table()
        
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
    
    def test_create_authors_table(self, schema_manager, connection_manager):
        """Test authors table creation"""
        schema_manager.create_users_table()
        schema_manager.create_sessions_table()
        schema_manager.create_authors_table()
        
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
    
    def test_create_plots_table(self, schema_manager, connection_manager):
        """Test plots table creation with multiple foreign keys"""
        # Create dependencies
        schema_manager.create_users_table()
        schema_manager.create_sessions_table()
        schema_manager.create_authors_table()
        schema_manager.create_plots_table()
        
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
    
    def test_create_world_building_table(self, schema_manager, connection_manager):
        """Test world_building table creation with JSON fields"""
        # Create dependencies
        schema_manager.create_users_table()
        schema_manager.create_sessions_table()
        schema_manager.create_authors_table()
        schema_manager.create_plots_table()
        schema_manager.create_world_building_table()
        
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
    
    def test_create_characters_table(self, schema_manager, connection_manager):
        """Test characters table creation"""
        # Create dependencies
        schema_manager.create_users_table()
        schema_manager.create_sessions_table()
        schema_manager.create_authors_table()
        schema_manager.create_plots_table()
        schema_manager.create_world_building_table()
        schema_manager.create_characters_table()
        
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
    
    def test_create_supporting_tables(self, schema_manager, connection_manager):
        """Test creation of supporting tables"""
        schema_manager.create_orchestrator_decisions_table()
        schema_manager.create_genres_table()
        schema_manager.create_target_audiences_table()
        schema_manager.create_subgenres_table()
        schema_manager.create_microgenres_table()
        schema_manager.create_tropes_table()
        schema_manager.create_tones_table()
        
        # Verify tables exist
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = connection_manager.execute_select(query)
        table_names = [row['name'] for row in results]
        
        expected_tables = [
            'orchestrator_decisions', 'genres', 'target_audiences',
            'subgenres', 'microgenres', 'tropes', 'tones'
        ]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_create_iterative_improvement_tables(self, schema_manager, connection_manager):
        """Test creation of iterative improvement tables"""
        schema_manager.create_improvement_sessions_table()
        schema_manager.create_iterations_table()
        schema_manager.create_critiques_table()
        schema_manager.create_enhancements_table()
        schema_manager.create_scores_table()
        
        # Verify tables exist
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = connection_manager.execute_select(query)
        table_names = [row['name'] for row in results]
        
        expected_tables = [
            'improvement_sessions', 'iterations', 'critiques', 
            'enhancements', 'scores'
        ]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_create_observability_tables(self, schema_manager, connection_manager):
        """Test creation of observability tables"""
        schema_manager.create_agent_invocations_table()
        schema_manager.create_performance_metrics_table()
        schema_manager.create_trace_events_table()
        
        # Verify tables exist
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = connection_manager.execute_select(query)
        table_names = [row['name'] for row in results]
        
        expected_tables = [
            'agent_invocations', 'performance_metrics', 'trace_events'
        ]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_create_additional_tables(self, schema_manager, connection_manager):
        """Test creation of additional tables"""
        schema_manager.create_content_ratings_table()
        schema_manager.create_lore_documents_table()
        schema_manager.create_lore_clusters_table()
        
        # Verify tables exist
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = connection_manager.execute_select(query)
        table_names = [row['name'] for row in results]
        
        expected_tables = [
            'content_ratings', 'lore_documents', 'lore_clusters'
        ]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_table_exists_check(self, schema_manager, connection_manager):
        """Test checking if tables exist"""
        # Initially no tables should exist (except sqlite_master)
        assert not schema_manager.table_exists('users')
        assert not schema_manager.table_exists('plots')
        
        # Create a table
        schema_manager.create_users_table()
        
        # Now it should exist
        assert schema_manager.table_exists('users')
        assert not schema_manager.table_exists('plots')  # Still doesn't exist
    
    def test_get_table_schema(self, schema_manager, connection_manager):
        """Test getting table schema information"""
        schema_manager.create_users_table()
        
        schema = schema_manager.get_table_schema('users')
        
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
    
    def test_drop_table(self, schema_manager, connection_manager):
        """Test dropping tables"""
        # Create table
        schema_manager.create_users_table()
        assert schema_manager.table_exists('users')
        
        # Drop table
        schema_manager.drop_table('users')
        assert not schema_manager.table_exists('users')
    
    def test_get_all_table_names(self, schema_manager, connection_manager):
        """Test getting all table names"""
        # Create some tables
        schema_manager.create_users_table()
        schema_manager.create_sessions_table()
        
        table_names = schema_manager.get_all_table_names()
        assert 'users' in table_names
        assert 'sessions' in table_names
        assert 'sqlite_master' not in table_names  # Should exclude system tables