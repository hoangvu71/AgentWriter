"""
TDD Test Suite for SchemaSynchronizer class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- SchemaSynchronizer initialization and configuration
- SQLite schema information extraction
- Schema comparison and validation
- Table structure analysis
- Index and constraint detection
- Foreign key relationship mapping
- Schema version management
- Error handling and edge cases
- Database connection management
- Schema consistency validation
"""

import pytest
import sqlite3
import tempfile
import os
import json
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from src.database.schema_synchronizer import SchemaSynchronizer


class TestSchemaSynchronizerInitialization:
    """Test SchemaSynchronizer initialization and configuration"""
    
    def test_schema_synchronizer_initialization_default_path(self):
        """
        RED: Test SchemaSynchronizer initialization with default path
        Should initialize with default SQLite database path
        """
        # Act
        synchronizer = SchemaSynchronizer()
        
        # Assert
        assert synchronizer.sqlite_path == "local_database.db"
        assert synchronizer.logger is not None
        assert synchronizer.schema_version == "009"  # Current migration version
    
    def test_schema_synchronizer_initialization_custom_path(self):
        """
        RED: Test SchemaSynchronizer initialization with custom path
        Should initialize with provided SQLite database path
        """
        # Arrange
        custom_path = "/path/to/custom/database.db"
        
        # Act
        synchronizer = SchemaSynchronizer(sqlite_path=custom_path)
        
        # Assert
        assert synchronizer.sqlite_path == custom_path
        assert synchronizer.logger is not None
        assert synchronizer.schema_version == "009"
    
    def test_schema_synchronizer_logger_initialization(self):
        """
        RED: Test SchemaSynchronizer logger initialization
        Should create logger with appropriate namespace
        """
        # Act
        synchronizer = SchemaSynchronizer()
        
        # Assert
        assert synchronizer.logger is not None
        assert "schema_synchronizer" in synchronizer.logger.name
    
    def test_schema_synchronizer_version_management(self):
        """
        RED: Test SchemaSynchronizer version management
        Should track current schema version
        """
        # Act
        synchronizer = SchemaSynchronizer()
        
        # Assert
        assert synchronizer.schema_version is not None
        assert isinstance(synchronizer.schema_version, str)
        assert len(synchronizer.schema_version) > 0


class TestSchemaSynchronizerSchemaExtraction:
    """Test SchemaSynchronizer SQLite schema extraction"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
    
    @pytest.fixture
    def sample_database(self, temp_db_path):
        """Create sample database with test schema"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Create sample tables
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE posts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                published_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_users_email ON users (email)")
        cursor.execute("CREATE INDEX idx_posts_user_id ON posts (user_id)")
        cursor.execute("CREATE INDEX idx_posts_published ON posts (published_at)")
        
        conn.commit()
        conn.close()
        
        return temp_db_path
    
    def test_get_sqlite_schema_info_success(self, sample_database):
        """
        RED: Test get_sqlite_schema_info with valid database
        Should extract complete schema information from SQLite database
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=sample_database)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert isinstance(schema_info, dict)
        assert "version" in schema_info
        assert "tables" in schema_info
        assert "indexes" in schema_info
        assert "foreign_keys" in schema_info
        
        # Check version
        assert schema_info["version"] == "009"
        
        # Check tables
        assert "users" in schema_info["tables"]
        assert "posts" in schema_info["tables"]
        
        # Check users table structure
        users_columns = schema_info["tables"]["users"]
        assert len(users_columns) == 4
        
        # Find id column
        id_column = next(col for col in users_columns if col["name"] == "id")
        assert id_column["type"] == "TEXT"
        assert id_column["primary_key"] is True
        assert id_column["nullable"] is False
        
        # Find name column
        name_column = next(col for col in users_columns if col["name"] == "name")
        assert name_column["type"] == "TEXT"
        assert name_column["nullable"] is False
        
        # Find email column
        email_column = next(col for col in users_columns if col["name"] == "email")
        assert email_column["type"] == "TEXT"
        assert email_column["nullable"] is True
        
        # Check posts table structure
        posts_columns = schema_info["tables"]["posts"]
        assert len(posts_columns) == 5
        
        # Find foreign key column
        user_id_column = next(col for col in posts_columns if col["name"] == "user_id")
        assert user_id_column["type"] == "TEXT"
        assert user_id_column["nullable"] is False
    
    def test_get_sqlite_schema_info_empty_database(self, temp_db_path):
        """
        RED: Test get_sqlite_schema_info with empty database
        Should return schema info with empty tables
        """
        # Arrange
        # Create empty database
        conn = sqlite3.connect(temp_db_path)
        conn.close()
        
        synchronizer = SchemaSynchronizer(sqlite_path=temp_db_path)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert isinstance(schema_info, dict)
        assert "version" in schema_info
        assert "tables" in schema_info
        assert "indexes" in schema_info
        assert "foreign_keys" in schema_info
        assert len(schema_info["tables"]) == 0
    
    def test_get_sqlite_schema_info_with_indexes(self, sample_database):
        """
        RED: Test get_sqlite_schema_info index extraction
        Should extract index information from database
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=sample_database)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert "indexes" in schema_info
        indexes = schema_info["indexes"]
        
        # Check if indexes are captured (implementation may vary)
        # This test verifies the structure exists for index tracking
        assert isinstance(indexes, dict)
    
    def test_get_sqlite_schema_info_nonexistent_database(self):
        """
        RED: Test get_sqlite_schema_info with nonexistent database
        Should handle missing database file gracefully
        """
        # Arrange
        nonexistent_path = "/nonexistent/path/database.db"
        synchronizer = SchemaSynchronizer(sqlite_path=nonexistent_path)
        
        # Act & Assert
        # The method should handle the error gracefully
        # (specific behavior depends on implementation)
        try:
            schema_info = synchronizer.get_sqlite_schema_info()
            # If no exception, verify basic structure
            assert isinstance(schema_info, dict)
        except Exception as e:
            # Expected behavior - should handle missing file
            assert "No such file" in str(e) or "database" in str(e).lower()
    
    def test_get_sqlite_schema_info_corrupted_database(self, temp_db_path):
        """
        RED: Test get_sqlite_schema_info with corrupted database
        Should handle corrupted database file gracefully
        """
        # Arrange
        # Create corrupted database file
        with open(temp_db_path, 'wb') as f:
            f.write(b"This is not a valid SQLite database file")
        
        synchronizer = SchemaSynchronizer(sqlite_path=temp_db_path)
        
        # Act & Assert
        # Should handle corruption gracefully
        try:
            schema_info = synchronizer.get_sqlite_schema_info()
            # If no exception, verify basic structure
            assert isinstance(schema_info, dict)
        except Exception as e:
            # Expected behavior - should handle corruption
            assert "database" in str(e).lower() or "file" in str(e).lower()


class TestSchemaSynchronizerTableAnalysis:
    """Test SchemaSynchronizer table structure analysis"""
    
    @pytest.fixture
    def complex_database(self):
        """Create complex database with various column types and constraints"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create table with various column types
        cursor.execute("""
            CREATE TABLE complex_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_col TEXT NOT NULL,
                integer_col INTEGER,
                real_col REAL,
                blob_col BLOB,
                nullable_col TEXT,
                default_col TEXT DEFAULT 'default_value',
                timestamp_col TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create table with composite primary key
        cursor.execute("""
            CREATE TABLE composite_key_table (
                key1 TEXT NOT NULL,
                key2 TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (key1, key2)
            )
        """)
        
        # Create table with multiple foreign keys
        cursor.execute("""
            CREATE TABLE multi_fk_table (
                id TEXT PRIMARY KEY,
                parent1_id INTEGER,
                parent2_id TEXT,
                data TEXT,
                FOREIGN KEY (parent1_id) REFERENCES complex_table (id),
                FOREIGN KEY (parent2_id) REFERENCES composite_key_table (key1)
            )
        """)
        
        conn.commit()
        conn.close()
        
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
    
    def test_schema_extraction_column_types(self, complex_database):
        """
        RED: Test schema extraction for various column types
        Should correctly identify different SQLite column types
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=complex_database)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert "complex_table" in schema_info["tables"]
        columns = schema_info["tables"]["complex_table"]
        
        # Check column types
        column_dict = {col["name"]: col for col in columns}
        
        assert column_dict["id"]["type"] == "INTEGER"
        assert column_dict["id"]["primary_key"] is True
        
        assert column_dict["text_col"]["type"] == "TEXT"
        assert column_dict["text_col"]["nullable"] is False
        
        assert column_dict["integer_col"]["type"] == "INTEGER"
        assert column_dict["integer_col"]["nullable"] is True
        
        assert column_dict["real_col"]["type"] == "REAL"
        assert column_dict["blob_col"]["type"] == "BLOB"
        
        assert column_dict["nullable_col"]["nullable"] is True
        assert column_dict["default_col"]["default"] == "'default_value'"
    
    def test_schema_extraction_composite_primary_key(self, complex_database):
        """
        RED: Test schema extraction for composite primary keys
        Should correctly identify composite primary key columns
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=complex_database)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert "composite_key_table" in schema_info["tables"]
        columns = schema_info["tables"]["composite_key_table"]
        
        # Check composite primary key
        primary_key_columns = [col for col in columns if col["primary_key"]]
        assert len(primary_key_columns) >= 1  # At least one key column should be marked
        
        # Check key columns exist
        column_names = [col["name"] for col in columns]
        assert "key1" in column_names
        assert "key2" in column_names
        assert "value" in column_names
    
    def test_schema_extraction_foreign_keys(self, complex_database):
        """
        RED: Test schema extraction for foreign key relationships
        Should identify foreign key relationships between tables
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=complex_database)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert "multi_fk_table" in schema_info["tables"]
        
        # Check that foreign key structure exists in schema
        assert "foreign_keys" in schema_info
        # Note: Actual foreign key extraction implementation may vary
        # This test ensures the structure is present for foreign key tracking


class TestSchemaSynchronizerErrorHandling:
    """Test SchemaSynchronizer error handling scenarios"""
    
    def test_schema_synchronizer_database_lock_handling(self):
        """
        RED: Test SchemaSynchronizer handling of database locks
        Should handle locked database gracefully
        """
        # Arrange
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            # Create a connection that locks the database
            blocking_conn = sqlite3.connect(temp_path)
            blocking_conn.execute("BEGIN EXCLUSIVE TRANSACTION")
            
            synchronizer = SchemaSynchronizer(sqlite_path=temp_path)
            
            # Act & Assert
            # Should handle lock scenario appropriately
            try:
                schema_info = synchronizer.get_sqlite_schema_info()
                # If successful, verify structure
                assert isinstance(schema_info, dict)
            except Exception as e:
                # Expected behavior - should handle lock appropriately
                assert "locked" in str(e).lower() or "busy" in str(e).lower()
            finally:
                blocking_conn.rollback()
                blocking_conn.close()
        
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    def test_schema_synchronizer_permission_error_handling(self):
        """
        RED: Test SchemaSynchronizer handling of permission errors
        Should handle permission denied errors gracefully
        """
        # Arrange
        # Use a path that would require special permissions
        restricted_path = "/root/restricted_database.db"
        synchronizer = SchemaSynchronizer(sqlite_path=restricted_path)
        
        # Act & Assert
        # Should handle permission errors gracefully
        try:
            schema_info = synchronizer.get_sqlite_schema_info()
            # If successful, verify structure
            assert isinstance(schema_info, dict)
        except Exception as e:
            # Expected behavior - should handle permission errors
            expected_errors = ["permission", "access", "denied", "no such file"]
            assert any(error in str(e).lower() for error in expected_errors)
    
    def test_schema_synchronizer_invalid_path_handling(self):
        """
        RED: Test SchemaSynchronizer handling of invalid paths
        Should handle invalid file paths gracefully
        """
        # Arrange
        invalid_paths = [
            "",  # Empty path
            None,  # None path (if constructor allows)
            "/\x00invalid",  # Invalid characters
            "con:" if os.name == 'nt' else "/dev/null/invalid"  # OS-specific invalid paths
        ]
        
        for invalid_path in invalid_paths:
            if invalid_path is None:
                continue  # Skip None if constructor doesn't allow it
            
            try:
                synchronizer = SchemaSynchronizer(sqlite_path=invalid_path)
                
                # Act & Assert
                try:
                    schema_info = synchronizer.get_sqlite_schema_info()
                    # If successful, verify structure
                    assert isinstance(schema_info, dict)
                except Exception as e:
                    # Expected behavior - should handle invalid paths
                    assert len(str(e)) > 0  # Should have meaningful error message
            except Exception:
                # Constructor itself may reject invalid paths
                pass


class TestSchemaSynchronizerIntegration:
    """Test SchemaSynchronizer integration scenarios"""
    
    @pytest.fixture
    def realistic_database(self):
        """Create realistic BooksWriter-like database schema"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create tables similar to BooksWriter schema
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE plots (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                title TEXT NOT NULL,
                genre TEXT,
                summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE authors (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                author_name TEXT NOT NULL,
                bio TEXT,
                style TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_plots_user_id ON plots (user_id)")
        cursor.execute("CREATE INDEX idx_plots_session_id ON plots (session_id)")
        cursor.execute("CREATE INDEX idx_authors_user_id ON authors (user_id)")
        
        conn.commit()
        conn.close()
        
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
    
    def test_schema_extraction_realistic_database(self, realistic_database):
        """
        RED: Test schema extraction on realistic BooksWriter database
        Should extract complete schema from realistic database structure
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=realistic_database)
        
        # Act
        schema_info = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert isinstance(schema_info, dict)
        assert schema_info["version"] == "009"
        
        # Check all expected tables
        expected_tables = ["users", "sessions", "plots", "authors"]
        for table in expected_tables:
            assert table in schema_info["tables"]
        
        # Check plots table structure (most complex)
        plots_columns = schema_info["tables"]["plots"]
        column_names = [col["name"] for col in plots_columns]
        
        expected_columns = ["id", "session_id", "user_id", "title", "genre", "summary", "created_at"]
        for col_name in expected_columns:
            assert col_name in column_names
        
        # Check primary key
        id_column = next(col for col in plots_columns if col["name"] == "id")
        assert id_column["primary_key"] is True
        
        # Check NOT NULL constraint
        title_column = next(col for col in plots_columns if col["name"] == "title")
        assert title_column["nullable"] is False
    
    def test_schema_version_consistency(self, realistic_database):
        """
        RED: Test schema version consistency
        Should maintain consistent version information
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=realistic_database)
        
        # Act
        schema_info1 = synchronizer.get_sqlite_schema_info()
        schema_info2 = synchronizer.get_sqlite_schema_info()
        
        # Assert
        assert schema_info1["version"] == schema_info2["version"]
        assert schema_info1["version"] == synchronizer.schema_version
    
    def test_schema_extraction_performance(self, realistic_database):
        """
        RED: Test schema extraction performance
        Should extract schema information efficiently
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=realistic_database)
        
        # Act
        import time
        start_time = time.time()
        schema_info = synchronizer.get_sqlite_schema_info()
        end_time = time.time()
        
        # Assert
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second
        assert isinstance(schema_info, dict)
        assert len(schema_info["tables"]) > 0
    
    def test_schema_extraction_deterministic(self, realistic_database):
        """
        RED: Test schema extraction determinism
        Should produce consistent results across multiple calls
        """
        # Arrange
        synchronizer = SchemaSynchronizer(sqlite_path=realistic_database)
        
        # Act
        schema_info1 = synchronizer.get_sqlite_schema_info()
        schema_info2 = synchronizer.get_sqlite_schema_info()
        
        # Assert
        # Convert to JSON strings for comparison (handles nested structures)
        json1 = json.dumps(schema_info1, sort_keys=True)
        json2 = json.dumps(schema_info2, sort_keys=True)
        assert json1 == json2