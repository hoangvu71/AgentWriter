"""
TDD Test Suite for DatabaseFactory class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- DatabaseFactory initialization and configuration
- Adapter selection logic based on environment variables
- Supabase connectivity checking and fallback
- SQLite mode enforcement and configuration
- Connection caching and reuse
- Offline data synchronization capabilities
- Error handling and graceful degradation
- Configuration validation and edge cases
"""

import pytest
import asyncio
import os
import uuid
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

# Mock external dependencies before importing
mock_supabase = MagicMock()
mock_supabase.create_client = MagicMock()
mock_supabase.Client = MagicMock()
sys.modules['supabase'] = mock_supabase

mock_httpx = MagicMock()
sys.modules['httpx'] = mock_httpx

from src.database.database_factory import DatabaseFactory, db_factory
from src.database.sqlite.adapter import SQLiteAdapter
from src.database.supabase_adapter import SupabaseAdapter


class TestDatabaseFactoryInitialization:
    """Test DatabaseFactory initialization and basic properties"""
    
    def test_database_factory_initialization(self):
        """
        RED: Test DatabaseFactory initialization
        Should initialize with proper default values
        """
        # Act
        factory = DatabaseFactory()
        
        # Assert
        assert factory._supabase_available is None
        assert factory._adapter is None
        assert factory.logger is not None
    
    def test_global_database_factory_instance(self):
        """
        RED: Test global database factory instance
        Should provide singleton-like access to factory
        """
        # Act & Assert
        assert db_factory is not None
        assert isinstance(db_factory, DatabaseFactory)
        
        # Verify it's the same instance when imported multiple times
        from src.database.database_factory import db_factory as db_factory2
        assert db_factory is db_factory2


class TestDatabaseFactoryAdapterSelection:
    """Test DatabaseFactory adapter selection logic"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        with patch('src.database.database_factory.config') as mock_config:
            mock_config.is_supabase_enabled.return_value = True
            mock_config.supabase_config = {
                "url": "https://test.supabase.co",
                "anon_key": "test-anon-key"
            }
            yield mock_config
    
    @pytest.mark.asyncio
    async def test_get_adapter_sqlite_mode_explicit(self, mock_config):
        """
        RED: Test get_adapter with explicit SQLite mode
        Should return SQLiteAdapter when DATABASE_MODE=sqlite
        """
        # Arrange
        with patch.dict(os.environ, {"DATABASE_MODE": "sqlite", "SQLITE_DB_PATH": "test.db"}), \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_adapter:
            
            mock_adapter = MagicMock()
            mock_sqlite_adapter.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert
            assert adapter == mock_adapter
            assert factory.is_offline_mode() is True
            assert factory.is_using_supabase() is False
            mock_sqlite_adapter.assert_called_once_with("test.db")
    
    @pytest.mark.asyncio
    async def test_get_adapter_supabase_mode_available(self, mock_config):
        """
        RED: Test get_adapter with Supabase mode when available
        Should return SupabaseAdapter when Supabase is reachable
        """
        # Arrange
        with patch.dict(os.environ, {"DATABASE_MODE": "supabase"}), \
             patch('src.database.database_factory.SupabaseAdapter') as mock_supabase_adapter, \
             patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check:
            
            mock_adapter = MagicMock()
            mock_supabase_adapter.return_value = mock_adapter
            mock_check.return_value = True
            
            factory = DatabaseFactory()
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert
            assert adapter == mock_adapter
            assert factory.is_using_supabase() is True
            assert factory.is_offline_mode() is False
            mock_supabase_adapter.assert_called_once_with(
                url="https://test.supabase.co",
                key="test-anon-key"
            )
            mock_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_adapter_supabase_mode_unavailable_fallback(self, mock_config):
        """
        RED: Test get_adapter with Supabase mode when unavailable
        Should fallback to SQLiteAdapter when Supabase is unreachable
        """
        # Arrange
        with patch.dict(os.environ, {"DATABASE_MODE": "supabase"}), \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_adapter, \
             patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check:
            
            mock_adapter = MagicMock()
            mock_sqlite_adapter.return_value = mock_adapter
            mock_check.return_value = False
            
            factory = DatabaseFactory()
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert
            assert adapter == mock_adapter
            assert factory.is_offline_mode() is True
            assert factory.is_using_supabase() is False
            mock_sqlite_adapter.assert_called_once_with("development.db")
            mock_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_adapter_default_mode_supabase_disabled(self, mock_config):
        """
        RED: Test get_adapter with default mode when Supabase is disabled
        Should default to SQLiteAdapter when Supabase is not configured
        """
        # Arrange
        mock_config.is_supabase_enabled.return_value = False
        
        with patch.dict(os.environ, {}, clear=True), \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_adapter:
            
            mock_adapter = MagicMock()
            mock_sqlite_adapter.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert
            assert adapter == mock_adapter
            assert factory.is_offline_mode() is True
            assert factory.is_using_supabase() is False
            mock_sqlite_adapter.assert_called_once_with("development.db")
    
    @pytest.mark.asyncio
    async def test_get_adapter_cached_adapter_reuse(self, mock_config):
        """
        RED: Test get_adapter adapter caching
        Should reuse existing adapter on subsequent calls
        """
        # Arrange
        with patch.dict(os.environ, {"DATABASE_MODE": "sqlite"}), \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_adapter:
            
            mock_adapter = MagicMock()
            mock_sqlite_adapter.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Act
            adapter1 = await factory.get_adapter()
            adapter2 = await factory.get_adapter()
            
            # Assert
            assert adapter1 == adapter2
            assert adapter1 == mock_adapter
            # SQLiteAdapter should only be called once due to caching
            mock_sqlite_adapter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_adapter_custom_sqlite_path(self, mock_config):
        """
        RED: Test get_adapter with custom SQLite database path
        Should use custom path when SQLITE_DB_PATH is set
        """
        # Arrange
        custom_path = "/custom/path/database.db"
        
        with patch.dict(os.environ, {"DATABASE_MODE": "sqlite", "SQLITE_DB_PATH": custom_path}), \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_adapter:
            
            mock_adapter = MagicMock()
            mock_sqlite_adapter.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert
            assert adapter == mock_adapter
            mock_sqlite_adapter.assert_called_once_with(custom_path)


class TestDatabaseFactoryConnectivityChecking:
    """Test DatabaseFactory Supabase connectivity checking"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        with patch('src.database.database_factory.config') as mock_config:
            mock_config.supabase_config = {
                "url": "https://test.supabase.co",
                "anon_key": "test-anon-key"
            }
            yield mock_config
    
    @pytest.mark.asyncio
    async def test_check_supabase_connectivity_success(self, mock_config):
        """
        RED: Test successful Supabase connectivity check
        Should return True when Supabase responds with success status
        """
        # Arrange
        with patch('src.database.database_factory.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            factory = DatabaseFactory()
            
            # Act
            result = await factory._check_supabase_connectivity()
            
            # Assert
            assert result is True
            mock_client.get.assert_called_once_with(
                "https://test.supabase.co/rest/v1/",
                timeout=5.0,
                headers={"apikey": "test-anon-key"}
            )
    
    @pytest.mark.asyncio
    async def test_check_supabase_connectivity_server_error(self, mock_config):
        """
        RED: Test Supabase connectivity check with server error
        Should return False when Supabase responds with server error (5xx)
        """
        # Arrange
        with patch('src.database.database_factory.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            factory = DatabaseFactory()
            
            # Act
            result = await factory._check_supabase_connectivity()
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_supabase_connectivity_client_error_acceptable(self, mock_config):
        """
        RED: Test Supabase connectivity check with client error
        Should return True for client errors (4xx) as they indicate server is responding
        """
        # Arrange
        with patch('src.database.database_factory.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401  # Unauthorized, but server is responding
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            factory = DatabaseFactory()
            
            # Act
            result = await factory._check_supabase_connectivity()
            
            # Assert
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_supabase_connectivity_timeout(self, mock_config):
        """
        RED: Test Supabase connectivity check with timeout
        Should return False when request times out
        """
        # Arrange
        with patch('src.database.database_factory.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = asyncio.TimeoutError("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            factory = DatabaseFactory()
            
            # Act
            result = await factory._check_supabase_connectivity()
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_supabase_connectivity_network_error(self, mock_config):
        """
        RED: Test Supabase connectivity check with network error
        Should return False when network error occurs
        """
        # Arrange
        with patch('src.database.database_factory.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network unreachable")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            factory = DatabaseFactory()
            
            # Act
            result = await factory._check_supabase_connectivity()
            
            # Assert
            assert result is False


class TestDatabaseFactoryStatusMethods:
    """Test DatabaseFactory status checking methods"""
    
    def test_is_using_supabase_true(self):
        """
        RED: Test is_using_supabase when using Supabase
        Should return True when _supabase_available is True
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = True
        
        # Act & Assert
        assert factory.is_using_supabase() is True
    
    def test_is_using_supabase_false(self):
        """
        RED: Test is_using_supabase when not using Supabase
        Should return False when _supabase_available is False
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = False
        
        # Act & Assert
        assert factory.is_using_supabase() is False
    
    def test_is_using_supabase_none(self):
        """
        RED: Test is_using_supabase when status is unknown
        Should return False when _supabase_available is None
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = None
        
        # Act & Assert
        assert factory.is_using_supabase() is False
    
    def test_is_offline_mode_true(self):
        """
        RED: Test is_offline_mode when in offline mode
        Should return True when _supabase_available is False
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = False
        
        # Act & Assert
        assert factory.is_offline_mode() is True
    
    def test_is_offline_mode_false(self):
        """
        RED: Test is_offline_mode when not in offline mode
        Should return False when _supabase_available is True
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = True
        
        # Act & Assert
        assert factory.is_offline_mode() is False
    
    def test_is_offline_mode_none(self):
        """
        RED: Test is_offline_mode when status is unknown
        Should return False when _supabase_available is None
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = None
        
        # Act & Assert
        assert factory.is_offline_mode() is False


class TestDatabaseFactoryOfflineSync:
    """Test DatabaseFactory offline data synchronization"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        with patch('src.database.database_factory.config') as mock_config:
            mock_config.is_supabase_enabled.return_value = True
            mock_config.supabase_config = {
                "url": "https://test.supabase.co",
                "anon_key": "test-anon-key"
            }
            yield mock_config
    
    @pytest.mark.asyncio
    async def test_sync_offline_data_not_in_offline_mode(self, mock_config):
        """
        RED: Test sync_offline_data when not in offline mode
        Should return early without attempting sync
        """
        # Arrange
        factory = DatabaseFactory()
        factory._supabase_available = True  # Not in offline mode
        
        # Act
        await factory.sync_offline_data()
        
        # Assert - No additional operations should occur
        # This is verified by the fact that no exceptions are raised
        # and no external calls are made
    
    @pytest.mark.asyncio
    async def test_sync_offline_data_supabase_still_unavailable(self, mock_config):
        """
        RED: Test sync_offline_data when Supabase is still unavailable
        Should log warning and continue in offline mode
        """
        # Arrange
        with patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check:
            mock_check.return_value = False
            
            factory = DatabaseFactory()
            factory._supabase_available = False  # In offline mode
            
            # Act
            await factory.sync_offline_data()
            
            # Assert
            mock_check.assert_called_once()
            assert factory._supabase_available is False
    
    @pytest.mark.asyncio
    async def test_sync_offline_data_successful_sync(self, mock_config):
        """
        RED: Test successful offline data synchronization
        Should sync data from SQLite to Supabase and switch adapters
        """
        # Arrange
        with patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check, \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class, \
             patch('src.database.database_factory.SupabaseAdapter') as mock_supabase_class:
            
            mock_check.return_value = True
            
            # Mock SQLite adapter with sample data
            mock_sqlite = AsyncMock()
            mock_sqlite.select.return_value = [
                {"id": "1", "name": "Test User", "created_at": "2025-01-01T00:00:00"},
                {"id": "2", "name": "Another User", "created_at": "2025-01-02T00:00:00"}
            ]
            mock_sqlite_class.return_value = mock_sqlite
            
            # Mock Supabase adapter
            mock_supabase = AsyncMock()
            mock_supabase.select.return_value = []  # No existing records
            mock_supabase.insert = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            factory = DatabaseFactory()
            factory._supabase_available = False  # Start in offline mode
            
            # Act
            await factory.sync_offline_data()
            
            # Assert
            mock_check.assert_called_once()
            
            # Verify adapters were created
            mock_sqlite_class.assert_called_once()
            mock_supabase_class.assert_called_once_with(
                url="https://test.supabase.co",
                key="test-anon-key"
            )
            
            # Verify data sync for each table
            expected_tables = [
                'users', 'sessions', 'authors', 'plots', 
                'world_building', 'characters', 'orchestrator_decisions',
                'genres', 'target_audiences'
            ]
            
            # Check that select was called for each table
            assert mock_sqlite.select.call_count == len(expected_tables)
            
            # Check that insert was called for each record
            assert mock_supabase.insert.call_count == 2 * len(expected_tables)  # 2 records per table
            
            # Verify adapter switch
            assert factory._adapter == mock_supabase
            assert factory._supabase_available is True
    
    @pytest.mark.asyncio
    async def test_sync_offline_data_with_existing_records(self, mock_config):
        """
        RED: Test offline sync with existing records in Supabase
        Should update existing records if offline version is newer
        """
        # Arrange
        with patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check, \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class, \
             patch('src.database.database_factory.SupabaseAdapter') as mock_supabase_class:
            
            mock_check.return_value = True
            
            # Mock SQLite adapter with newer data
            mock_sqlite = AsyncMock()
            sqlite_record = {"id": "1", "name": "Updated User", "created_at": "2025-01-02T00:00:00"}
            mock_sqlite.select.return_value = [sqlite_record]
            mock_sqlite_class.return_value = mock_sqlite
            
            # Mock Supabase adapter with older existing record
            mock_supabase = AsyncMock()
            existing_record = {"id": "1", "name": "Old User", "created_at": "2025-01-01T00:00:00"}
            mock_supabase.select.return_value = [existing_record]
            mock_supabase.update = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            factory = DatabaseFactory()
            factory._supabase_available = False
            
            # Act
            await factory.sync_offline_data()
            
            # Assert
            # Should call update instead of insert for existing record
            mock_supabase.update.assert_called()
            mock_supabase.insert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_offline_data_partial_failure(self, mock_config):
        """
        RED: Test offline sync with partial record failures
        Should continue sync despite individual record failures
        """
        # Arrange
        with patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check, \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class, \
             patch('src.database.database_factory.SupabaseAdapter') as mock_supabase_class:
            
            mock_check.return_value = True
            
            # Mock SQLite adapter
            mock_sqlite = AsyncMock()
            mock_sqlite.select.return_value = [
                {"id": "1", "name": "Good Record"},
                {"id": "2", "name": "Bad Record"}
            ]
            mock_sqlite_class.return_value = mock_sqlite
            
            # Mock Supabase adapter with one failing insert
            mock_supabase = AsyncMock()
            mock_supabase.select.return_value = []  # No existing records
            mock_supabase.insert.side_effect = [
                None,  # First insert succeeds
                Exception("Insert failed")  # Second insert fails
            ]
            mock_supabase_class.return_value = mock_supabase
            
            factory = DatabaseFactory()
            factory._supabase_available = False
            
            # Act
            await factory.sync_offline_data()
            
            # Assert
            # Sync should complete despite partial failures
            assert factory._adapter == mock_supabase
            assert factory._supabase_available is True
    
    @pytest.mark.asyncio
    async def test_sync_offline_data_sync_error(self, mock_config):
        """
        RED: Test offline sync with critical sync error
        Should handle exceptions gracefully and remain in offline mode
        """
        # Arrange
        with patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check, \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class:
            
            mock_check.return_value = True
            mock_sqlite_class.side_effect = Exception("SQLite adapter creation failed")
            
            factory = DatabaseFactory()
            factory._supabase_available = False
            original_adapter = factory._adapter
            
            # Act
            await factory.sync_offline_data()
            
            # Assert
            # Should remain in offline mode due to error
            assert factory._supabase_available is False
            assert factory._adapter == original_adapter


class TestDatabaseFactoryIntegration:
    """Test DatabaseFactory integration scenarios and edge cases"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        with patch('src.database.database_factory.config') as mock_config:
            mock_config.is_supabase_enabled.return_value = True
            mock_config.supabase_config = {
                "url": "https://test.supabase.co",
                "anon_key": "test-anon-key"
            }
            yield mock_config
    
    @pytest.mark.asyncio
    async def test_complete_workflow_online_to_offline(self, mock_config):
        """
        RED: Test complete workflow from online to offline mode
        Should handle Supabase failure and fallback gracefully
        """
        # Arrange
        with patch('src.database.database_factory.SupabaseAdapter') as mock_supabase_class, \
             patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class, \
             patch.object(DatabaseFactory, '_check_supabase_connectivity') as mock_check:
            
            # First call: Supabase available
            # Second call: Supabase unavailable (simulating network loss)
            mock_check.side_effect = [True, False]
            
            mock_supabase = MagicMock()
            mock_sqlite = MagicMock()
            mock_supabase_class.return_value = mock_supabase
            mock_sqlite_class.return_value = mock_sqlite
            
            factory = DatabaseFactory()
            
            with patch.dict(os.environ, {"DATABASE_MODE": "supabase"}):
                # Act - First adapter creation (online)
                adapter1 = await factory.get_adapter()
                
                # Clear cache to force re-evaluation
                factory._adapter = None
                factory._supabase_available = None
                
                # Act - Second adapter creation (offline)
                adapter2 = await factory.get_adapter()
            
            # Assert
            assert adapter1 == mock_supabase  # First call used Supabase
            assert adapter2 == mock_sqlite    # Second call fell back to SQLite
            assert mock_check.call_count == 2
    
    @pytest.mark.asyncio
    async def test_environment_variable_precedence(self, mock_config):
        """
        RED: Test environment variable precedence
        Should respect DATABASE_MODE over configuration
        """
        # Arrange
        with patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class:
            mock_adapter = MagicMock()
            mock_sqlite_class.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Test with different environment variable values
            test_cases = [
                ("sqlite", True),
                ("SQLITE", True),  # Case insensitive
                ("SQLite", True),
                ("supabase", False),  # Would need connectivity check
                ("invalid", False)   # Should default to SQLite
            ]
            
            for env_value, should_be_sqlite in test_cases:
                # Clear cache
                factory._adapter = None
                factory._supabase_available = None
                
                with patch.dict(os.environ, {"DATABASE_MODE": env_value}):
                    # Act
                    adapter = await factory.get_adapter()
                    
                    # Assert
                    if should_be_sqlite or env_value == "invalid":
                        assert adapter == mock_adapter
                        assert factory.is_offline_mode() is True
    
    @pytest.mark.asyncio
    async def test_concurrent_adapter_requests(self, mock_config):
        """
        RED: Test concurrent adapter requests
        Should handle multiple simultaneous requests correctly
        """
        # Arrange
        with patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class, \
             patch.dict(os.environ, {"DATABASE_MODE": "sqlite"}):
            
            mock_adapter = MagicMock()
            mock_sqlite_class.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Act - Simulate concurrent requests
            tasks = [factory.get_adapter() for _ in range(5)]
            adapters = await asyncio.gather(*tasks)
            
            # Assert
            # All should return the same adapter instance (cached)
            assert all(adapter == mock_adapter for adapter in adapters)
            # SQLiteAdapter should only be created once
            mock_sqlite_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_configuration_validation_edge_cases(self, mock_config):
        """
        RED: Test configuration validation edge cases
        Should handle missing or invalid configuration gracefully
        """
        # Test case 1: Missing Supabase URL
        mock_config.supabase_config = {"anon_key": "test-key"}  # Missing URL
        
        with patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class, \
             patch.dict(os.environ, {"DATABASE_MODE": "supabase"}):
            
            mock_adapter = MagicMock()
            mock_sqlite_class.return_value = mock_adapter
            
            factory = DatabaseFactory()
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert - Should fallback to SQLite due to invalid config
            assert adapter == mock_adapter
            assert factory.is_offline_mode() is True
        
        # Test case 2: None configuration
        mock_config.supabase_config = None
        factory._adapter = None
        factory._supabase_available = None
        
        with patch('src.database.database_factory.SQLiteAdapter') as mock_sqlite_class:
            mock_adapter = MagicMock()
            mock_sqlite_class.return_value = mock_adapter
            
            # Act
            adapter = await factory.get_adapter()
            
            # Assert - Should default to SQLite
            assert adapter == mock_adapter
            assert factory.is_offline_mode() is True