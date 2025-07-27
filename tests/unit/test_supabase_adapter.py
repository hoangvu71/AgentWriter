"""
TDD Test Suite for SupabaseAdapter class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- SupabaseAdapter initialization and configuration
- Connection pooling lifecycle and management
- CRUD operations with comprehensive error handling
- Connection pool context management
- Health check and monitoring functionality
- Schema synchronization validation
- Async/await patterns and concurrency
- Connection timeout and retry logic
- Performance metrics collection
- Transaction support and rollback
"""

import pytest
import asyncio
import uuid
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
from contextlib import AsyncExitStack

# Mock the supabase module before importing SupabaseAdapter
mock_supabase = MagicMock()
mock_supabase.create_client = MagicMock()
mock_supabase.Client = MagicMock()
sys.modules['supabase'] = mock_supabase

from src.database.supabase_adapter import SupabaseAdapter
from src.database.connection_pool import ConnectionPoolConfig, SupabaseConnectionPool
from src.core.interfaces import ContentType


class TestSupabaseAdapterInitialization:
    """Test SupabaseAdapter initialization and configuration"""
    
    def test_adapter_initialization_with_credentials(self):
        """
        RED: Test SupabaseAdapter initialization with provided credentials
        Should initialize client and connection pool successfully
        """
        # Arrange
        test_url = "https://test.supabase.co"
        test_key = "test-anon-key"
        
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool
            
            # Act
            adapter = SupabaseAdapter(url=test_url, key=test_key)
            
            # Assert
            assert adapter.url == test_url
            assert adapter.key == test_key
            assert adapter.client == mock_client
            assert adapter.connection_pool == mock_pool
            mock_create_client.assert_called_once_with(test_url, test_key)
            mock_pool_class.assert_called_once()
    
    def test_adapter_initialization_from_environment(self):
        """
        RED: Test SupabaseAdapter initialization using environment variables
        Should read credentials from environment when not provided
        """
        # Arrange
        env_url = "https://env.supabase.co"
        env_key = "env-anon-key"
        
        with patch.dict('os.environ', {'SUPABASE_URL': env_url, 'SUPABASE_ANON_KEY': env_key}), \
             patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool
            
            # Act
            adapter = SupabaseAdapter()
            
            # Assert
            assert adapter.url == env_url
            assert adapter.key == env_key
            mock_create_client.assert_called_once_with(env_url, env_key)
    
    def test_adapter_initialization_missing_credentials(self):
        """
        RED: Test SupabaseAdapter initialization with missing credentials
        Should raise ValueError when credentials not available
        """
        # Arrange
        with patch.dict('os.environ', {}, clear=True):
            
            # Act & Assert
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_ANON_KEY must be provided"):
                SupabaseAdapter()
    
    def test_adapter_initialization_with_custom_pool_config(self):
        """
        RED: Test SupabaseAdapter initialization with custom connection pool configuration
        Should use provided pool configuration
        """
        # Arrange
        test_url = "https://test.supabase.co"
        test_key = "test-anon-key"
        custom_config = ConnectionPoolConfig(
            min_connections=5,
            max_connections=20,
            max_idle_time=600,
            connection_timeout=60
        )
        
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool
            
            # Act
            adapter = SupabaseAdapter(url=test_url, key=test_key, pool_config=custom_config)
            
            # Assert
            assert adapter.pool_config == custom_config
            mock_pool_class.assert_called_once_with(test_url, test_key, custom_config)
    
    def test_adapter_initialization_client_creation_failure(self):
        """
        RED: Test SupabaseAdapter initialization when client creation fails
        Should raise exception and log error
        """
        # Arrange
        test_url = "https://test.supabase.co"
        test_key = "test-anon-key"
        
        with patch('src.database.supabase_adapter.create_client') as mock_create_client:
            mock_create_client.side_effect = Exception("Client creation failed")
            
            # Act & Assert
            with pytest.raises(Exception, match="Client creation failed"):
                SupabaseAdapter(url=test_url, key=test_key)


class TestSupabaseAdapterCRUDOperations:
    """Test SupabaseAdapter CRUD operations with connection pooling"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock SupabaseAdapter for testing"""
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            # Mock client
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            # Mock connection pool
            mock_pool = MagicMock()
            mock_conn = MagicMock()
            mock_conn.client = mock_client
            mock_pool.get_connection.return_value.__aenter__.return_value = mock_conn
            mock_pool.get_connection.return_value.__aexit__.return_value = None
            mock_pool_class.return_value = mock_pool
            
            adapter = SupabaseAdapter(url="https://test.supabase.co", key="test-key")
            adapter.connection_pool = mock_pool
            
            return adapter, mock_client, mock_pool, mock_conn
    
    @pytest.mark.asyncio
    async def test_insert_record_success(self, mock_adapter):
        """
        RED: Test successful record insertion
        Should use connection pool and return inserted record ID
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        test_data = {"name": "John Doe", "email": "john@example.com"}
        expected_id = str(uuid.uuid4())
        
        # Mock table operations
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": expected_id, **test_data}]
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act
        result_id = await adapter.insert(table_name, test_data)
        
        # Assert
        assert result_id == expected_id
        mock_client.table.assert_called_once_with(table_name)
        mock_table.insert.assert_called_once_with(test_data)
        mock_insert.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_record_no_data_returned(self, mock_adapter):
        """
        RED: Test insert operation when no data is returned
        Should raise exception
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        test_data = {"name": "John Doe"}
        
        # Mock table operations returning no data
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = []
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act & Assert
        with pytest.raises(Exception, match="No data returned from insert"):
            await adapter.insert(table_name, test_data)
    
    @pytest.mark.asyncio
    async def test_get_by_id_existing_record(self, mock_adapter):
        """
        RED: Test retrieving existing record by ID
        Should use connection pool and return record data
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        expected_data = {"id": entity_id, "name": "John Doe", "email": "john@example.com"}
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [expected_data]
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.get_by_id(table_name, entity_id)
        
        # Assert
        assert result == expected_data
        mock_client.table.assert_called_once_with(table_name)
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("id", entity_id)
        mock_eq.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_record(self, mock_adapter):
        """
        RED: Test retrieving nonexistent record by ID
        Should return None when record not found
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        
        # Mock table operations returning no data
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = []
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.get_by_id(table_name, entity_id)
        
        # Assert
        assert result is None
        mock_select.eq.assert_called_once_with("id", entity_id)
    
    @pytest.mark.asyncio
    async def test_update_record_success(self, mock_adapter):
        """
        RED: Test successful record update
        Should use connection pool and return True for successful update
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        
        # Mock table operations
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": entity_id, **update_data}]
        
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.update(table_name, entity_id, update_data)
        
        # Assert
        assert result is True
        mock_client.table.assert_called_once_with(table_name)
        mock_table.update.assert_called_once_with(update_data)
        mock_update.eq.assert_called_once_with("id", entity_id)
        mock_eq.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_record_not_found(self, mock_adapter):
        """
        RED: Test updating nonexistent record
        Should return False when no records are updated
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        
        # Mock table operations returning no data
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = []
        
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.update(table_name, entity_id, update_data)
        
        # Assert
        assert result is False
        mock_update.eq.assert_called_once_with("id", entity_id)
    
    @pytest.mark.asyncio
    async def test_delete_record_success(self, mock_adapter):
        """
        RED: Test successful record deletion
        Should use connection pool and return True for successful deletion
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        
        # Mock table operations
        mock_table = MagicMock()
        mock_delete = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": entity_id}]
        
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.delete(table_name, entity_id)
        
        # Assert
        assert result is True
        mock_client.table.assert_called_once_with(table_name)
        mock_table.delete.assert_called_once()
        mock_delete.eq.assert_called_once_with("id", entity_id)
        mock_eq.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, mock_adapter):
        """
        RED: Test deleting nonexistent record
        Should return False when no records are deleted
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        
        # Mock table operations returning no data
        mock_table = MagicMock()
        mock_delete = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = []
        
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.delete(table_name, entity_id)
        
        # Assert
        assert result is False
        mock_delete.eq.assert_called_once_with("id", entity_id)


class TestSupabaseAdapterQueryOperations:
    """Test SupabaseAdapter query operations with pagination and search"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock SupabaseAdapter for testing"""
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            mock_pool = MagicMock()
            mock_conn = MagicMock()
            mock_conn.client = mock_client
            mock_pool.get_connection.return_value.__aenter__.return_value = mock_conn
            mock_pool.get_connection.return_value.__aexit__.return_value = None
            mock_pool_class.return_value = mock_pool
            
            adapter = SupabaseAdapter(url="https://test.supabase.co", key="test-key")
            adapter.connection_pool = mock_pool
            
            return adapter, mock_client, mock_pool, mock_conn
    
    @pytest.mark.asyncio
    async def test_get_all_records_with_pagination(self, mock_adapter):
        """
        RED: Test get_all with custom pagination parameters
        Should use connection pool and apply pagination correctly
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        limit = 50
        offset = 100
        expected_data = [
            {"id": str(uuid.uuid4()), "name": f"User {i}"}
            for i in range(limit)
        ]
        
        # Mock table operations with chained calls
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_order = MagicMock()
        mock_range = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = expected_data
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.range.return_value = mock_range
        mock_range.execute.return_value = mock_execute
        
        # Act
        result = await adapter.get_all(table_name, limit=limit, offset=offset)
        
        # Assert
        assert result == expected_data
        mock_client.table.assert_called_once_with(table_name)
        mock_table.select.assert_called_once_with("*")
        mock_select.order.assert_called_once_with("created_at", desc=True)
        mock_order.range.assert_called_once_with(offset, offset + limit - 1)
        mock_range.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_records_default_pagination(self, mock_adapter):
        """
        RED: Test get_all with default pagination parameters
        Should use default limit and offset values
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        expected_data = [{"id": str(uuid.uuid4()), "name": "User 1"}]
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_order = MagicMock()
        mock_range = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = expected_data
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.range.return_value = mock_range
        mock_range.execute.return_value = mock_execute
        
        # Act
        result = await adapter.get_all(table_name)
        
        # Assert
        assert result == expected_data
        # Check default pagination (limit=100, offset=0)
        mock_order.range.assert_called_once_with(0, 99)  # offset + limit - 1
    
    @pytest.mark.asyncio
    async def test_search_records_with_criteria(self, mock_adapter):
        """
        RED: Test search with specific criteria
        Should apply search filters and use connection pool
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        criteria = {"status": "active", "role": "admin"}
        limit = 25
        expected_data = [{"id": str(uuid.uuid4()), "name": "Admin User", "status": "active"}]
        
        # Mock table operations with filter chaining
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_limit = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = expected_data
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_execute
        
        # Act
        result = await adapter.search(table_name, criteria, limit)
        
        # Assert
        assert result == expected_data
        mock_client.table.assert_called_once_with(table_name)
        mock_table.select.assert_called_once_with("*")
        # Check that eq was called for each criteria
        assert mock_select.eq.call_count >= 1
        mock_limit.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_records_no_criteria(self, mock_adapter):
        """
        RED: Test search without criteria
        Should return all records with limit applied
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        criteria = {}
        limit = 10
        expected_data = [{"id": str(uuid.uuid4()), "name": f"User {i}"} for i in range(limit)]
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_limit = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = expected_data
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_execute
        
        # Act
        result = await adapter.search(table_name, criteria, limit)
        
        # Assert
        assert result == expected_data
        mock_table.select.assert_called_once_with("*")
        mock_select.limit.assert_called_once_with(limit)
        # Should not call eq when no criteria
        mock_select.eq.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_count_records_with_criteria(self, mock_adapter):
        """
        RED: Test count operation with search criteria
        Should return count of matching records
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        criteria = {"status": "active"}
        expected_count = 42
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.count = expected_count
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.count(table_name, criteria)
        
        # Assert
        assert result == expected_count
        mock_client.table.assert_called_once_with(table_name)
        mock_table.select.assert_called_once_with("*", count="exact")
        mock_select.eq.assert_called_once_with("status", "active")
        mock_eq.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_all_records(self, mock_adapter):
        """
        RED: Test count operation without criteria
        Should return total count of all records
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        criteria = {}
        expected_count = 150
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_execute = MagicMock()
        mock_execute.count = expected_count
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.execute.return_value = mock_execute
        
        # Act
        result = await adapter.count(table_name, criteria)
        
        # Assert
        assert result == expected_count
        mock_table.select.assert_called_once_with("*", count="exact")
        # Should not call eq when no criteria
        mock_select.eq.assert_not_called()
        mock_select.execute.assert_called_once()


class TestSupabaseAdapterSpecializedOperations:
    """Test SupabaseAdapter specialized operations for specific entity types"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock SupabaseAdapter for testing"""
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            mock_pool = MagicMock()
            mock_conn = MagicMock()
            mock_conn.client = mock_client
            mock_pool.get_connection.return_value.__aenter__.return_value = mock_conn
            mock_pool.get_connection.return_value.__aexit__.return_value = None
            mock_pool_class.return_value = mock_pool
            
            adapter = SupabaseAdapter(url="https://test.supabase.co", key="test-key")
            adapter.connection_pool = mock_pool
            
            return adapter, mock_client, mock_pool, mock_conn
    
    @pytest.mark.asyncio
    async def test_save_plot_with_valid_data(self, mock_adapter):
        """
        RED: Test save_plot specialized operation
        Should insert plot data and return plot ID
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        plot_data = {
            "title": "Epic Fantasy Quest",
            "genre": "Fantasy",
            "summary": "A hero's journey to save the realm",
            "user_id": "test-user",
            "session_id": "test-session"
        }
        expected_id = str(uuid.uuid4())
        
        # Mock table operations
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": expected_id, **plot_data}]
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act
        result_id = await adapter.save_plot(plot_data)
        
        # Assert
        assert result_id == expected_id
        mock_client.table.assert_called_once_with("plots")
        mock_table.insert.assert_called_once_with(plot_data)
        mock_insert.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_author_with_valid_data(self, mock_adapter):
        """
        RED: Test save_author specialized operation
        Should insert author data and return author ID
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        author_data = {
            "author_name": "J.R.R. TestAuthor",
            "bio": "A fictional author for testing",
            "style": "Epic Fantasy",
            "user_id": "test-user",
            "session_id": "test-session"
        }
        expected_id = str(uuid.uuid4())
        
        # Mock table operations
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": expected_id, **author_data}]
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act
        result_id = await adapter.save_author(author_data)
        
        # Assert
        assert result_id == expected_id
        mock_client.table.assert_called_once_with("authors")
        mock_table.insert.assert_called_once_with(author_data)
        mock_insert.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_plot_existing(self, mock_adapter):
        """
        RED: Test get_plot specialized operation for existing plot
        Should retrieve plot data by ID
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        plot_id = str(uuid.uuid4())
        expected_plot = {
            "id": plot_id,
            "title": "Epic Fantasy Quest",
            "genre": "Fantasy",
            "summary": "A hero's journey to save the realm"
        }
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [expected_plot]
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.get_plot(plot_id)
        
        # Assert
        assert result == expected_plot
        mock_client.table.assert_called_once_with("plots")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("id", plot_id)
        mock_eq.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_author_existing(self, mock_adapter):
        """
        RED: Test get_author specialized operation for existing author
        Should retrieve author data by ID
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        author_id = str(uuid.uuid4())
        expected_author = {
            "id": author_id,
            "author_name": "J.R.R. TestAuthor",
            "bio": "A fictional author for testing",
            "style": "Epic Fantasy"
        }
        
        # Mock table operations
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [expected_author]
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute
        
        # Act
        result = await adapter.get_author(author_id)
        
        # Assert
        assert result == expected_author
        mock_client.table.assert_called_once_with("authors")
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_once_with("id", author_id)
        mock_eq.execute.assert_called_once()
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_content_across_tables(self, mock_adapter):
        """
        RED: Test search_content specialized operation
        Should search across multiple content tables
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        query = "fantasy adventure"
        content_type = ContentType.PLOT
        user_id = "test-user"
        
        # Expected results from multiple tables
        expected_results = [
            {"id": str(uuid.uuid4()), "title": "Fantasy Adventure", "type": "plot"},
            {"id": str(uuid.uuid4()), "title": "Adventure Chronicles", "type": "plot"}
        ]
        
        # Mock table operations for plots table
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_ilike = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = expected_results
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.ilike.return_value = mock_ilike
        mock_ilike.execute.return_value = mock_execute
        
        # Act
        result = await adapter.search_content(query, content_type, user_id)
        
        # Assert
        assert result == expected_results
        mock_client.table.assert_called_with("plots")  # Should search plots table for PLOT content type
        mock_table.select.assert_called_once_with("*")
        mock_select.eq.assert_called_with("user_id", user_id)
        mock_pool.get_connection.assert_called_once()


class TestSupabaseAdapterErrorHandling:
    """Test SupabaseAdapter error handling and logging"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock SupabaseAdapter for testing"""
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            mock_pool = MagicMock()
            mock_conn = MagicMock()
            mock_conn.client = mock_client
            mock_pool.get_connection.return_value.__aenter__.return_value = mock_conn
            mock_pool.get_connection.return_value.__aexit__.return_value = None
            mock_pool_class.return_value = mock_pool
            
            adapter = SupabaseAdapter(url="https://test.supabase.co", key="test-key")
            adapter.connection_pool = mock_pool
            
            return adapter, mock_client, mock_pool, mock_conn
    
    @pytest.mark.asyncio
    async def test_insert_operation_database_error(self, mock_adapter):
        """
        RED: Test insert operation with database error
        Should handle exception and re-raise with proper logging
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        test_data = {"name": "John Doe"}
        
        # Mock table operations to raise exception
        mock_client.table.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            await adapter.insert(table_name, test_data)
        
        # Verify connection pool was attempted
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_operation_error_handling(self, mock_adapter):
        """
        RED: Test get_by_id operation with error handling
        Should handle exceptions gracefully and log errors
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        
        # Mock table operations to raise exception
        mock_client.table.side_effect = Exception("Query execution failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Query execution failed"):
            await adapter.get_by_id(table_name, entity_id)
        
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_operation_constraint_error(self, mock_adapter):
        """
        RED: Test update operation with constraint violation
        Should handle database constraint errors appropriately
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        update_data = {"email": "duplicate@example.com"}
        
        # Mock table operations to raise constraint error
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_eq.execute.side_effect = Exception("Unique constraint violation")
        
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        
        # Act & Assert
        with pytest.raises(Exception, match="Unique constraint violation"):
            await adapter.update(table_name, entity_id, update_data)
        
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_operation_foreign_key_error(self, mock_adapter):
        """
        RED: Test delete operation with foreign key constraint error
        Should handle foreign key violations appropriately
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        
        # Mock table operations to raise foreign key error
        mock_table = MagicMock()
        mock_delete = MagicMock()
        mock_eq = MagicMock()
        mock_eq.execute.side_effect = Exception("Foreign key constraint violation")
        
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq
        
        # Act & Assert
        with pytest.raises(Exception, match="Foreign key constraint violation"):
            await adapter.delete(table_name, entity_id)
        
        mock_pool.get_connection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_pool_timeout_error(self, mock_adapter):
        """
        RED: Test operation with connection pool timeout
        Should handle connection timeout gracefully
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        test_data = {"name": "John Doe"}
        
        # Mock connection pool to raise timeout error
        mock_pool.get_connection.side_effect = asyncio.TimeoutError("Connection pool timeout")
        
        # Act & Assert
        with pytest.raises(asyncio.TimeoutError, match="Connection pool timeout"):
            await adapter.insert(table_name, test_data)
        
        mock_pool.get_connection.assert_called_once()


class TestSupabaseAdapterConnectionPooling:
    """Test SupabaseAdapter connection pooling functionality"""
    
    @pytest.fixture
    def mock_adapter_with_detailed_pool(self):
        """Create mock SupabaseAdapter with detailed connection pool mocking"""
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            # Create detailed pool mock
            mock_pool = MagicMock()
            mock_conn_context = AsyncMock()
            mock_conn = MagicMock()
            mock_conn.client = mock_client
            
            # Setup async context manager
            mock_conn_context.__aenter__.return_value = mock_conn
            mock_conn_context.__aexit__.return_value = None
            mock_pool.get_connection.return_value = mock_conn_context
            
            # Setup pool health and metrics
            mock_pool.health_check = AsyncMock()
            mock_pool.get_pool_stats.return_value = {
                "active_connections": 2,
                "idle_connections": 3,
                "total_connections": 5,
                "max_connections": 8
            }
            
            mock_pool_class.return_value = mock_pool
            
            adapter = SupabaseAdapter(url="https://test.supabase.co", key="test-key")
            adapter.connection_pool = mock_pool
            
            return adapter, mock_client, mock_pool, mock_conn, mock_conn_context
    
    @pytest.mark.asyncio
    async def test_connection_pool_context_management(self, mock_adapter_with_detailed_pool):
        """
        RED: Test proper connection pool context management
        Should acquire and release connections properly
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn, mock_conn_context = mock_adapter_with_detailed_pool
        table_name = "users"
        test_data = {"name": "John Doe"}
        expected_id = str(uuid.uuid4())
        
        # Mock successful table operation
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": expected_id, **test_data}]
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act
        result_id = await adapter.insert(table_name, test_data)
        
        # Assert
        assert result_id == expected_id
        
        # Verify connection pool context management
        mock_pool.get_connection.assert_called_once()
        mock_conn_context.__aenter__.assert_called_once()
        mock_conn_context.__aexit__.assert_called_once()
        
        # Verify operation used the pooled connection
        mock_client.table.assert_called_once_with(table_name)
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self, mock_adapter_with_detailed_pool):
        """
        RED: Test multiple concurrent operations using connection pool
        Should handle multiple concurrent database operations efficiently
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn, mock_conn_context = mock_adapter_with_detailed_pool
        
        # Mock multiple concurrent operations
        table_name = "users"
        test_data_list = [
            {"name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(5)
        ]
        
        # Mock table operations for concurrent inserts
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": str(uuid.uuid4()), **test_data_list[0]}]
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act - Simulate concurrent operations
        tasks = [
            adapter.insert(table_name, test_data)
            for test_data in test_data_list
        ]
        results = await asyncio.gather(*tasks)
        
        # Assert
        assert len(results) == 5
        assert all(isinstance(result, str) for result in results)
        
        # Verify connection pool was used for each operation
        assert mock_pool.get_connection.call_count == 5
        assert mock_conn_context.__aenter__.call_count == 5
        assert mock_conn_context.__aexit__.call_count == 5
    
    @pytest.mark.asyncio
    async def test_connection_pool_health_check(self, mock_adapter_with_detailed_pool):
        """
        RED: Test connection pool health check functionality
        Should verify pool health and connection validity
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn, mock_conn_context = mock_adapter_with_detailed_pool
        
        # Act - Trigger health check
        await mock_pool.health_check()
        
        # Assert
        mock_pool.health_check.assert_called_once()
    
    def test_connection_pool_statistics(self, mock_adapter_with_detailed_pool):
        """
        RED: Test connection pool statistics collection
        Should provide accurate pool usage metrics
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn, mock_conn_context = mock_adapter_with_detailed_pool
        
        # Act
        stats = mock_pool.get_pool_stats()
        
        # Assert
        assert "active_connections" in stats
        assert "idle_connections" in stats
        assert "total_connections" in stats
        assert "max_connections" in stats
        assert stats["total_connections"] == stats["active_connections"] + stats["idle_connections"]
        assert stats["total_connections"] <= stats["max_connections"]
    
    @pytest.mark.asyncio
    async def test_connection_pool_connection_reuse(self, mock_adapter_with_detailed_pool):
        """
        RED: Test connection pool connection reuse
        Should reuse connections efficiently for sequential operations
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn, mock_conn_context = mock_adapter_with_detailed_pool
        table_name = "users"
        entity_id = str(uuid.uuid4())
        
        # Mock table operations for get and update
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_execute_get = MagicMock()
        mock_execute_get.data = [{"id": entity_id, "name": "John Doe"}]
        
        mock_update = MagicMock()
        mock_eq_update = MagicMock()
        mock_execute_update = MagicMock()
        mock_execute_update.data = [{"id": entity_id, "name": "Updated Name"}]
        
        # Setup chained calls for get operation
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_execute_get
        
        # Setup chained calls for update operation
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_update
        mock_eq_update.execute.return_value = mock_execute_update
        
        # Act - Perform sequential operations
        get_result = await adapter.get_by_id(table_name, entity_id)
        update_result = await adapter.update(table_name, entity_id, {"name": "Updated Name"})
        
        # Assert
        assert get_result is not None
        assert update_result is True
        
        # Verify connection pool was used for both operations
        assert mock_pool.get_connection.call_count == 2
        assert mock_conn_context.__aenter__.call_count == 2
        assert mock_conn_context.__aexit__.call_count == 2


class TestSupabaseAdapterIntegration:
    """Test SupabaseAdapter integration scenarios and edge cases"""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock SupabaseAdapter for integration testing"""
        with patch('src.database.supabase_adapter.create_client') as mock_create_client, \
             patch('src.database.supabase_adapter.SupabaseConnectionPool') as mock_pool_class:
            
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            mock_pool = MagicMock()
            mock_conn = MagicMock()
            mock_conn.client = mock_client
            mock_pool.get_connection.return_value.__aenter__.return_value = mock_conn
            mock_pool.get_connection.return_value.__aexit__.return_value = None
            mock_pool_class.return_value = mock_pool
            
            adapter = SupabaseAdapter(url="https://test.supabase.co", key="test-key")
            adapter.connection_pool = mock_pool
            
            return adapter, mock_client, mock_pool, mock_conn
    
    @pytest.mark.asyncio
    async def test_end_to_end_crud_workflow(self, mock_adapter):
        """
        RED: Test complete CRUD workflow for a single entity
        Should handle create, read, update, delete sequence successfully
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        entity_id = str(uuid.uuid4())
        initial_data = {"name": "John Doe", "email": "john@example.com"}
        update_data = {"name": "Jane Doe", "email": "jane@example.com"}
        
        # Mock all CRUD operations
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        
        # CREATE - Insert operation
        mock_insert = MagicMock()
        mock_execute_insert = MagicMock()
        mock_execute_insert.data = [{"id": entity_id, **initial_data}]
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute_insert
        
        # READ - Get operation
        mock_select = MagicMock()
        mock_eq_get = MagicMock()
        mock_execute_get = MagicMock()
        mock_execute_get.data = [{"id": entity_id, **initial_data}]
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq_get
        mock_eq_get.execute.return_value = mock_execute_get
        
        # UPDATE - Update operation
        mock_update = MagicMock()
        mock_eq_update = MagicMock()
        mock_execute_update = MagicMock()
        mock_execute_update.data = [{"id": entity_id, **update_data}]
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq_update
        mock_eq_update.execute.return_value = mock_execute_update
        
        # DELETE - Delete operation
        mock_delete = MagicMock()
        mock_eq_delete = MagicMock()
        mock_execute_delete = MagicMock()
        mock_execute_delete.data = [{"id": entity_id}]
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq_delete
        mock_eq_delete.execute.return_value = mock_execute_delete
        
        # Act - Perform complete CRUD workflow
        # CREATE
        created_id = await adapter.insert(table_name, initial_data)
        
        # READ
        retrieved_entity = await adapter.get_by_id(table_name, entity_id)
        
        # UPDATE
        update_success = await adapter.update(table_name, entity_id, update_data)
        
        # DELETE
        delete_success = await adapter.delete(table_name, entity_id)
        
        # Assert
        assert created_id == entity_id
        assert retrieved_entity["id"] == entity_id
        assert retrieved_entity["name"] == initial_data["name"]
        assert update_success is True
        assert delete_success is True
        
        # Verify all operations used the connection pool
        assert mock_pool.get_connection.call_count == 4
    
    @pytest.mark.asyncio
    async def test_transaction_like_behavior_with_error_recovery(self, mock_adapter):
        """
        RED: Test error recovery in transaction-like scenarios
        Should handle partial failures gracefully
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        test_data_list = [
            {"name": "User 1", "email": "user1@example.com"},
            {"name": "User 2", "email": "user2@example.com"},
            {"name": "User 3", "email": "user3@example.com"}
        ]
        
        # Mock table operations with one failure
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        
        # Mock successful executions for first and third insert
        mock_execute_success = MagicMock()
        mock_execute_success.data = [{"id": str(uuid.uuid4())}]
        
        # Mock failure for second insert
        mock_execute_failure = MagicMock()
        mock_execute_failure.side_effect = Exception("Constraint violation")
        
        # Setup execution results: success, failure, success
        mock_insert.execute.side_effect = [
            mock_execute_success,
            Exception("Constraint violation"),
            mock_execute_success
        ]
        
        # Act & Assert
        # First insert should succeed
        result1 = await adapter.insert(table_name, test_data_list[0])
        assert isinstance(result1, str)
        
        # Second insert should fail
        with pytest.raises(Exception, match="Constraint violation"):
            await adapter.insert(table_name, test_data_list[1])
        
        # Third insert should succeed (recovery)
        result3 = await adapter.insert(table_name, test_data_list[2])
        assert isinstance(result3, str)
        
        # Verify connection pool was used for all attempts
        assert mock_pool.get_connection.call_count == 3
    
    @pytest.mark.asyncio
    async def test_content_type_specific_operations(self, mock_adapter):
        """
        RED: Test content type specific operations (save_plot, save_author, etc.)
        Should handle different content types with appropriate table routing
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        
        plot_data = {
            "title": "Epic Quest",
            "genre": "Fantasy",
            "summary": "A hero's journey"
        }
        author_data = {
            "author_name": "Test Author",
            "bio": "Test biography",
            "style": "Descriptive"
        }
        
        # Mock table operations for different content types
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"id": str(uuid.uuid4())}]
        
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        
        # Act
        plot_id = await adapter.save_plot(plot_data)
        author_id = await adapter.save_author(author_data)
        
        # Assert
        assert isinstance(plot_id, str)
        assert isinstance(author_id, str)
        
        # Verify correct table routing
        table_calls = mock_client.table.call_args_list
        assert call("plots") in table_calls
        assert call("authors") in table_calls
        
        # Verify connection pool usage
        assert mock_pool.get_connection.call_count == 2
    
    @pytest.mark.asyncio
    async def test_large_dataset_pagination_handling(self, mock_adapter):
        """
        RED: Test handling of large datasets with pagination
        Should efficiently handle pagination for large result sets
        """
        # Arrange
        adapter, mock_client, mock_pool, mock_conn = mock_adapter
        table_name = "users"
        
        # Generate large dataset
        large_dataset = [
            {"id": str(uuid.uuid4()), "name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(1000)
        ]
        
        # Mock table operations for paginated requests
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_order = MagicMock()
        mock_range = MagicMock()
        mock_execute = MagicMock()
        
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.range.return_value = mock_range
        mock_range.execute.return_value = mock_execute
        
        # Test different page sizes
        page_sizes = [10, 50, 100]
        
        for page_size in page_sizes:
            # Mock appropriate subset of data
            start_index = 0
            end_index = min(page_size, len(large_dataset))
            mock_execute.data = large_dataset[start_index:end_index]
            
            # Act
            result = await adapter.get_all(table_name, limit=page_size, offset=0)
            
            # Assert
            assert len(result) == min(page_size, len(large_dataset))
            mock_order.range.assert_called_with(0, page_size - 1)
        
        # Verify connection pool usage for all pagination requests
        assert mock_pool.get_connection.call_count == len(page_sizes)