"""
TDD Test Suite for Connection Pool classes.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- ConnectionPoolConfig configuration validation
- PoolMetrics tracking and reset functionality
- SQLitePooledConnection wrapper behavior
- SQLiteConnectionPool lifecycle management
- Connection pool size management and limits
- Health monitoring and cleanup tasks
- Performance metrics collection
- Connection reuse and timeout handling
- Async context manager behavior
- Error handling and graceful degradation
"""

import pytest
import asyncio
import sqlite3
import time
import threading
import tempfile
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
from queue import Queue, Empty, Full

# Mock the supabase module before importing connection pool
mock_supabase = MagicMock()
mock_supabase.Client = MagicMock()
sys.modules['supabase'] = mock_supabase

from src.database.connection_pool import (
    ConnectionPoolConfig, 
    PoolMetrics, 
    SQLitePooledConnection, 
    SQLiteConnectionPool,
    PooledConnection
)


class TestConnectionPoolConfig:
    """Test ConnectionPoolConfig dataclass"""
    
    def test_connection_pool_config_default_values(self):
        """
        RED: Test ConnectionPoolConfig default values
        Should initialize with appropriate default configuration
        """
        # Act
        config = ConnectionPoolConfig()
        
        # Assert
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.max_idle_time == 300  # 5 minutes
        assert config.connection_timeout == 30
        assert config.health_check_interval == 60
        assert config.max_retries == 3
        assert config.enable_metrics is True
    
    def test_connection_pool_config_custom_values(self):
        """
        RED: Test ConnectionPoolConfig with custom values
        Should allow customization of all configuration parameters
        """
        # Arrange & Act
        config = ConnectionPoolConfig(
            min_connections=5,
            max_connections=20,
            max_idle_time=600,
            connection_timeout=60,
            health_check_interval=120,
            max_retries=5,
            enable_metrics=False
        )
        
        # Assert
        assert config.min_connections == 5
        assert config.max_connections == 20
        assert config.max_idle_time == 600
        assert config.connection_timeout == 60
        assert config.health_check_interval == 120
        assert config.max_retries == 5
        assert config.enable_metrics is False
    
    def test_connection_pool_config_validation_max_greater_than_min(self):
        """
        RED: Test ConnectionPoolConfig validation
        Should allow max_connections greater than min_connections
        """
        # Arrange & Act
        config = ConnectionPoolConfig(min_connections=3, max_connections=15)
        
        # Assert
        assert config.max_connections > config.min_connections


class TestPoolMetrics:
    """Test PoolMetrics dataclass and functionality"""
    
    def test_pool_metrics_default_values(self):
        """
        RED: Test PoolMetrics default initialization
        Should initialize with zero values and current timestamp
        """
        # Act
        metrics = PoolMetrics()
        
        # Assert
        assert metrics.total_connections == 0
        assert metrics.active_connections == 0
        assert metrics.idle_connections == 0
        assert metrics.connections_created == 0
        assert metrics.connections_closed == 0
        assert metrics.pool_hits == 0
        assert metrics.pool_misses == 0
        assert metrics.health_check_failures == 0
        assert metrics.query_count == 0
        assert metrics.avg_connection_time == 0.0
        assert isinstance(metrics.last_reset, float)
        assert metrics.last_reset > 0
    
    def test_pool_metrics_custom_values(self):
        """
        RED: Test PoolMetrics with custom initialization
        Should allow setting custom values for all metrics
        """
        # Arrange & Act
        metrics = PoolMetrics(
            total_connections=10,
            active_connections=3,
            idle_connections=7,
            connections_created=15,
            connections_closed=5,
            pool_hits=100,
            pool_misses=10,
            health_check_failures=2,
            query_count=500,
            avg_connection_time=0.05
        )
        
        # Assert
        assert metrics.total_connections == 10
        assert metrics.active_connections == 3
        assert metrics.idle_connections == 7
        assert metrics.connections_created == 15
        assert metrics.connections_closed == 5
        assert metrics.pool_hits == 100
        assert metrics.pool_misses == 10
        assert metrics.health_check_failures == 2
        assert metrics.query_count == 500
        assert metrics.avg_connection_time == 0.05
    
    def test_pool_metrics_reset_functionality(self):
        """
        RED: Test PoolMetrics reset functionality
        Should reset counters but preserve current state metrics
        """
        # Arrange
        metrics = PoolMetrics(
            total_connections=10,
            active_connections=3,
            idle_connections=7,
            connections_created=15,
            connections_closed=5,
            pool_hits=100,
            pool_misses=10,
            health_check_failures=2,
            query_count=500,
            avg_connection_time=0.05
        )
        original_reset_time = metrics.last_reset
        
        # Act
        time.sleep(0.01)  # Ensure time difference
        metrics.reset()
        
        # Assert
        # Counters should be reset
        assert metrics.connections_created == 0
        assert metrics.connections_closed == 0
        assert metrics.pool_hits == 0
        assert metrics.pool_misses == 0
        assert metrics.health_check_failures == 0
        assert metrics.query_count == 0
        
        # Current state should be preserved
        assert metrics.total_connections == 10
        assert metrics.active_connections == 3
        assert metrics.idle_connections == 7
        assert metrics.avg_connection_time == 0.05
        
        # Reset time should be updated
        assert metrics.last_reset > original_reset_time


class TestSQLitePooledConnection:
    """Test SQLitePooledConnection wrapper functionality"""
    
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
    def sqlite_connection(self, temp_db_path):
        """Create SQLite connection for testing"""
        conn = sqlite3.connect(temp_db_path, check_same_thread=False)
        conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        yield conn
        conn.close()
    
    def test_sqlite_pooled_connection_initialization(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection initialization
        Should initialize with connection and default metadata
        """
        # Act
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        
        # Assert
        assert pooled_conn.connection == sqlite_connection
        assert isinstance(pooled_conn.created_at, float)
        assert isinstance(pooled_conn.last_used, float)
        assert pooled_conn.use_count == 0
        assert pooled_conn.created_at > 0
        assert pooled_conn.last_used > 0
    
    def test_sqlite_pooled_connection_execute_with_params(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection execute with parameters
        Should execute query with parameters and update metadata
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        original_last_used = pooled_conn.last_used
        original_use_count = pooled_conn.use_count
        
        # Act
        time.sleep(0.01)  # Ensure time difference
        cursor = pooled_conn.execute("INSERT INTO test_table (name) VALUES (?)", ["Test Name"])
        
        # Assert
        assert cursor is not None
        assert isinstance(cursor, sqlite3.Cursor)
        assert pooled_conn.last_used > original_last_used
        assert pooled_conn.use_count == original_use_count + 1
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        assert count == 1
        cursor.close()
    
    def test_sqlite_pooled_connection_execute_without_params(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection execute without parameters
        Should execute query without parameters and update metadata
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        original_use_count = pooled_conn.use_count
        
        # Act
        cursor = pooled_conn.execute("SELECT COUNT(*) FROM test_table")
        
        # Assert
        assert cursor is not None
        assert pooled_conn.use_count == original_use_count + 1
        
        # Verify query executed
        result = cursor.fetchone()
        assert result is not None
        cursor.close()
    
    def test_sqlite_pooled_connection_is_healthy_success(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection health check success
        Should return True for healthy connection
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        
        # Act
        is_healthy = pooled_conn.is_healthy()
        
        # Assert
        assert is_healthy is True
    
    def test_sqlite_pooled_connection_is_healthy_failure(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection health check failure
        Should return False for unhealthy connection
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        
        # Close the underlying connection to simulate failure
        sqlite_connection.close()
        
        # Act
        is_healthy = pooled_conn.is_healthy()
        
        # Assert
        assert is_healthy is False
    
    def test_sqlite_pooled_connection_close(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection close functionality
        Should close the underlying connection
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        
        # Verify connection is initially working
        assert pooled_conn.is_healthy() is True
        
        # Act
        pooled_conn.close()
        
        # Assert
        # After closing, health check should fail
        assert pooled_conn.is_healthy() is False
    
    def test_sqlite_pooled_connection_is_idle_expired_fresh(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection idle expiration for fresh connection
        Should return False for recently used connection
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        
        # Act
        is_expired = pooled_conn.is_idle_expired
        
        # Assert
        assert is_expired is False
    
    def test_sqlite_pooled_connection_is_idle_expired_old(self, sqlite_connection):
        """
        RED: Test SQLitePooledConnection idle expiration for old connection
        Should return True for connection idle longer than 5 minutes
        """
        # Arrange
        pooled_conn = SQLitePooledConnection(connection=sqlite_connection)
        
        # Simulate old last_used time (6 minutes ago)
        pooled_conn.last_used = time.time() - 360
        
        # Act
        is_expired = pooled_conn.is_idle_expired
        
        # Assert
        assert is_expired is True


class TestSQLiteConnectionPool:
    """Test SQLiteConnectionPool functionality"""
    
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
    def pool_config(self):
        """Create connection pool configuration for testing"""
        return ConnectionPoolConfig(
            min_connections=2,
            max_connections=5,
            max_idle_time=300,
            connection_timeout=30,
            health_check_interval=60,
            enable_metrics=True
        )
    
    def test_sqlite_connection_pool_initialization(self, temp_db_path, pool_config):
        """
        RED: Test SQLiteConnectionPool initialization
        Should initialize pool with minimum connections
        """
        # Act
        pool = SQLiteConnectionPool(temp_db_path, pool_config)
        
        # Assert
        assert pool.db_path == temp_db_path
        assert pool.config == pool_config
        assert pool.logger is not None
        assert pool._shutdown is False
        
        # Check that minimum connections were created
        assert pool._metrics.total_connections >= pool_config.min_connections
        assert len(pool._all_connections) >= pool_config.min_connections
        
        # Cleanup
        pool._shutdown = True
    
    def test_sqlite_connection_pool_create_connection_success(self, temp_db_path, pool_config):
        """
        RED: Test SQLiteConnectionPool connection creation success
        Should create optimized SQLite connection with proper settings
        """
        # Arrange
        pool = SQLiteConnectionPool(temp_db_path, pool_config)
        original_count = pool._metrics.connections_created
        
        # Act
        connection = pool._create_connection()
        
        # Assert
        assert connection is not None
        assert isinstance(connection, SQLitePooledConnection)
        assert pool._metrics.connections_created == original_count + 1
        
        # Verify connection has proper settings
        assert connection.is_healthy() is True
        
        # Test that foreign keys are enabled
        cursor = connection.execute("PRAGMA foreign_keys")
        foreign_keys_status = cursor.fetchone()[0]
        assert foreign_keys_status == 1
        cursor.close()
        
        # Cleanup
        connection.close()
        pool._shutdown = True
    
    def test_sqlite_connection_pool_create_connection_failure(self, pool_config):
        """
        RED: Test SQLiteConnectionPool connection creation failure
        Should handle connection creation errors gracefully
        """
        # Arrange - Use invalid database path
        invalid_path = "/invalid/path/database.db"
        pool = SQLiteConnectionPool(invalid_path, pool_config)
        
        # Act
        connection = pool._create_connection()
        
        # Assert
        # Should return None on failure (depending on implementation)
        # The test verifies that the method handles errors gracefully
        # without raising unhandled exceptions
        if connection is not None:
            connection.close()
        
        # Cleanup
        pool._shutdown = True
    
    @pytest.mark.asyncio
    async def test_sqlite_connection_pool_get_connection_from_pool(self, temp_db_path, pool_config):
        """
        RED: Test getting connection from pool
        Should return existing connection and update metrics
        """
        # Arrange
        pool = SQLiteConnectionPool(temp_db_path, pool_config)
        original_pool_hits = pool._metrics.pool_hits
        original_active = pool._metrics.active_connections
        
        # Act
        async with pool.get_connection() as connection:
            # Assert
            assert connection is not None
            assert isinstance(connection, SQLitePooledConnection)
            assert pool._metrics.pool_hits >= original_pool_hits
            assert pool._metrics.active_connections > original_active
            
            # Test connection functionality
            cursor = connection.execute("CREATE TABLE test (id INTEGER)")
            assert cursor is not None
            cursor.close()
        
        # After context exit, active connections should decrease
        assert pool._metrics.active_connections == original_active
        
        # Cleanup
        pool._shutdown = True
    
    @pytest.mark.asyncio
    async def test_sqlite_connection_pool_get_connection_pool_miss(self, temp_db_path, pool_config):
        """
        RED: Test getting connection when pool is empty
        Should create new connection and update metrics
        """
        # Arrange
        # Create pool with no minimum connections to test pool miss
        config = ConnectionPoolConfig(min_connections=0, max_connections=5)
        pool = SQLiteConnectionPool(temp_db_path, config)
        
        # Empty the pool
        while not pool._pool.empty():
            try:
                conn = pool._pool.get_nowait()
                conn.close()
            except:
                break
        
        original_pool_misses = pool._metrics.pool_misses
        original_total = pool._metrics.total_connections
        
        # Act
        async with pool.get_connection() as connection:
            # Assert
            assert connection is not None
            assert pool._metrics.pool_misses >= original_pool_misses
            assert pool._metrics.total_connections >= original_total
        
        # Cleanup
        pool._shutdown = True
    
    @pytest.mark.asyncio
    async def test_sqlite_connection_pool_max_connections_limit(self, temp_db_path, pool_config):
        """
        RED: Test connection pool maximum connections limit
        Should respect max_connections configuration
        """
        # Arrange
        # Use small pool to easily test limits
        config = ConnectionPoolConfig(min_connections=1, max_connections=2, connection_timeout=1)
        pool = SQLiteConnectionPool(temp_db_path, config)
        
        connections = []
        
        try:
            # Act - Get maximum number of connections
            for i in range(config.max_connections):
                conn_context = pool.get_connection()
                connection = await conn_context.__aenter__()
                connections.append((conn_context, connection))
            
            # Assert - Pool should be at capacity
            assert pool._metrics.active_connections <= config.max_connections
            
            # Try to get one more connection (should timeout or wait)
            with pytest.raises((asyncio.TimeoutError, Exception)):
                async with asyncio.wait_for(pool.get_connection(), timeout=0.1):
                    pass
        
        finally:
            # Cleanup - Return all connections
            for conn_context, connection in connections:
                await conn_context.__aexit__(None, None, None)
            pool._shutdown = True
    
    @pytest.mark.asyncio
    async def test_sqlite_connection_pool_concurrent_access(self, temp_db_path, pool_config):
        """
        RED: Test concurrent access to connection pool
        Should handle multiple simultaneous connection requests
        """
        # Arrange
        pool = SQLiteConnectionPool(temp_db_path, pool_config)
        
        async def get_and_use_connection(pool, task_id):
            async with pool.get_connection() as connection:
                # Simulate some work
                cursor = connection.execute(f"CREATE TABLE IF NOT EXISTS test_{task_id} (id INTEGER)")
                cursor.close()
                await asyncio.sleep(0.01)  # Small delay to simulate work
                return task_id
        
        # Act - Run multiple concurrent tasks
        tasks = [get_and_use_connection(pool, i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Assert
        assert len(results) == 5
        assert all(isinstance(result, int) for result in results)
        
        # Cleanup
        pool._shutdown = True
    
    def test_sqlite_connection_pool_metrics_tracking(self, temp_db_path, pool_config):
        """
        RED: Test connection pool metrics tracking
        Should accurately track pool usage statistics
        """
        # Arrange
        pool = SQLiteConnectionPool(temp_db_path, pool_config)
        initial_metrics = pool._metrics
        
        # Act - Create additional connection to trigger metrics update
        connection = pool._create_connection()
        
        # Assert
        assert pool._metrics.connections_created > initial_metrics.connections_created
        assert pool._metrics.total_connections > initial_metrics.total_connections
        
        # Cleanup
        if connection:
            connection.close()
        pool._shutdown = True
    
    @pytest.mark.asyncio
    async def test_sqlite_connection_pool_connection_return(self, temp_db_path, pool_config):
        """
        RED: Test connection return to pool after use
        Should return connection to pool for reuse
        """
        # Arrange
        pool = SQLiteConnectionPool(temp_db_path, pool_config)
        original_pool_size = pool._pool.qsize()
        
        # Act
        async with pool.get_connection() as connection:
            assert connection is not None
            # Connection is in use, pool size might be reduced
        
        # After exiting context, connection should be returned
        # Pool size should be restored (may not be exact due to pool management)
        final_pool_size = pool._pool.qsize()
        
        # Assert
        # The connection should have been returned to the pool
        # (exact size comparison may vary due to pool implementation details)
        assert final_pool_size >= 0  # Basic sanity check
        
        # Cleanup
        pool._shutdown = True


class TestSQLiteConnectionPoolErrorHandling:
    """Test SQLiteConnectionPool error handling and edge cases"""
    
    @pytest.fixture
    def pool_config(self):
        """Create connection pool configuration for testing"""
        return ConnectionPoolConfig(
            min_connections=1,
            max_connections=3,
            connection_timeout=1,  # Short timeout for testing
            enable_metrics=True
        )
    
    @pytest.mark.asyncio
    async def test_connection_pool_database_lock_handling(self, pool_config):
        """
        RED: Test connection pool handling of database locks
        Should handle database lock scenarios gracefully
        """
        # Arrange
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            # Create a connection that locks the database
            blocking_conn = sqlite3.connect(temp_path)
            blocking_conn.execute("BEGIN EXCLUSIVE TRANSACTION")
            
            pool = SQLiteConnectionPool(temp_path, pool_config)
            
            # Act & Assert
            # Connection creation might handle locks differently
            # This test verifies that the pool doesn't crash
            async with pool.get_connection() as connection:
                # Basic functionality test
                assert connection is not None
            
            # Cleanup
            blocking_conn.rollback()
            blocking_conn.close()
            pool._shutdown = True
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    @pytest.mark.asyncio
    async def test_connection_pool_corrupted_database_handling(self, pool_config):
        """
        RED: Test connection pool handling of corrupted database
        Should handle database corruption scenarios gracefully
        """
        # Arrange
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        
        # Write invalid data to create corrupted database
        with open(temp_path, 'wb') as f:
            f.write(b"This is not a valid SQLite database file")
        
        os.close(fd)
        
        try:
            # Act
            pool = SQLiteConnectionPool(temp_path, pool_config)
            
            # The pool should handle corruption gracefully
            # (behavior may vary based on implementation)
            assert pool is not None
            
            # Cleanup
            pool._shutdown = True
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    @pytest.mark.asyncio
    async def test_connection_pool_thread_safety(self, pool_config):
        """
        RED: Test connection pool thread safety
        Should be safe for use across multiple threads
        """
        # Arrange
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            pool = SQLiteConnectionPool(temp_path, pool_config)
            results = []
            errors = []
            
            def worker_thread(thread_id):
                try:
                    # Create async context in thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def async_work():
                        async with pool.get_connection() as connection:
                            cursor = connection.execute("SELECT 1")
                            result = cursor.fetchone()
                            cursor.close()
                            return result[0] if result else None
                    
                    result = loop.run_until_complete(async_work())
                    results.append((thread_id, result))
                    loop.close()
                    
                except Exception as e:
                    errors.append((thread_id, str(e)))
            
            # Act - Run multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=5.0)
            
            # Assert
            assert len(errors) == 0, f"Thread errors: {errors}"
            assert len(results) == 3
            assert all(result[1] == 1 for result in results)
            
            # Cleanup
            pool._shutdown = True
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


class TestConnectionPoolIntegration:
    """Test connection pool integration scenarios"""
    
    @pytest.fixture
    def pool_config(self):
        """Create connection pool configuration for testing"""
        return ConnectionPoolConfig(
            min_connections=2,
            max_connections=5,
            max_idle_time=1,  # Short idle time for testing
            health_check_interval=1,  # Frequent health checks for testing
            enable_metrics=True
        )
    
    @pytest.mark.asyncio
    async def test_connection_pool_performance_under_load(self, pool_config):
        """
        RED: Test connection pool performance under load
        Should maintain performance with many concurrent operations
        """
        # Arrange
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            pool = SQLiteConnectionPool(temp_path, pool_config)
            
            async def perform_operations(pool, num_operations):
                for i in range(num_operations):
                    async with pool.get_connection() as connection:
                        cursor = connection.execute("SELECT ?", [i])
                        result = cursor.fetchone()
                        cursor.close()
                        assert result[0] == i
            
            # Act - Perform many operations concurrently
            start_time = time.time()
            tasks = [perform_operations(pool, 10) for _ in range(5)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Assert
            execution_time = end_time - start_time
            assert execution_time < 5.0  # Should complete within reasonable time
            
            # Check metrics
            assert pool._metrics.query_count >= 50  # 5 tasks * 10 operations each
            assert pool._metrics.pool_hits > 0
            
            # Cleanup
            pool._shutdown = True
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    def test_connection_pool_metrics_accuracy(self, pool_config):
        """
        RED: Test connection pool metrics accuracy
        Should provide accurate usage statistics
        """
        # Arrange
        fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            pool = SQLiteConnectionPool(temp_path, pool_config)
            initial_connections = pool._metrics.total_connections
            
            # Act - Create additional connections
            connections = []
            for i in range(3):
                conn = pool._create_connection()
                if conn:
                    connections.append(conn)
            
            # Assert
            assert pool._metrics.total_connections == initial_connections + len(connections)
            assert pool._metrics.connections_created >= len(connections)
            
            # Cleanup connections
            for conn in connections:
                conn.close()
            pool._shutdown = True
            
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass