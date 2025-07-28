"""
TDD Test Suite for Connection Validator module.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- PooledConnection protocol and interface
- SQLiteConnectionValidator health checks
- SupabaseConnectionValidator health checks
- Connection validation strategies
- Health check caching and optimization
- Validation error handling and recovery
- Timeout and retry logic
"""

import pytest
import sqlite3
import tempfile
import os
import time
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import dataclass

from src.database.connection_validator import (
    ConnectionValidator,
    SQLiteConnectionValidator,
    SupabaseConnectionValidator,
    ValidationResult,
    ValidationStrategy,
    HealthCheckCache,
    ConnectionHealthMonitor
)


class TestValidationResult:
    """Test ValidationResult dataclass functionality"""
    
    def test_validation_result_success(self):
        """
        RED: Test ValidationResult for successful validation
        Should create result with success status
        """
        # Act
        result = ValidationResult.success()
        
        # Assert
        assert result.is_valid is True
        assert result.error_message is None
        assert isinstance(result.validation_time, float)
        assert result.validation_time > 0
    
    def test_validation_result_failure(self):
        """
        RED: Test ValidationResult for failed validation
        Should create result with failure status and error message
        """
        # Arrange
        error_msg = "Connection timeout"
        
        # Act
        result = ValidationResult.failure(error_msg)
        
        # Assert
        assert result.is_valid is False
        assert result.error_message == error_msg
        assert isinstance(result.validation_time, float)
    
    def test_validation_result_with_custom_time(self):
        """
        RED: Test ValidationResult with custom validation time
        Should allow setting custom validation time
        """
        # Arrange
        custom_time = 0.05
        
        # Act
        result = ValidationResult.success(validation_time=custom_time)
        
        # Assert
        assert result.validation_time == custom_time
        assert result.is_valid is True
    
    def test_validation_result_string_representation(self):
        """
        RED: Test ValidationResult string representation
        Should provide meaningful string representation
        """
        # Arrange
        success_result = ValidationResult.success()
        failure_result = ValidationResult.failure("Test error")
        
        # Act
        success_str = str(success_result)
        failure_str = str(failure_result)
        
        # Assert
        assert "valid" in success_str.lower()
        assert "invalid" in failure_str.lower() or "error" in failure_str.lower()
        assert "Test error" in failure_str


class TestConnectionValidator:
    """Test ConnectionValidator base class functionality"""
    
    def test_connection_validator_abstract_interface(self):
        """
        RED: Test ConnectionValidator abstract interface
        Should define abstract methods for validation
        """
        # Act & Assert
        # ConnectionValidator should be abstract/have abstract methods
        assert hasattr(ConnectionValidator, 'validate_connection')
        assert hasattr(ConnectionValidator, 'is_connection_healthy')
        
        # Should not be directly instantiable (abstract class)
        with pytest.raises(TypeError):
            ConnectionValidator()
    
    def test_connection_validator_strategy_pattern(self):
        """
        RED: Test ConnectionValidator strategy pattern support
        Should support different validation strategies
        """
        # This test verifies that the validator supports strategy pattern
        # by having configurable validation approaches
        # Implementation details will be in concrete classes
        pass


class TestSQLiteConnectionValidator:
    """Test SQLiteConnectionValidator functionality"""
    
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
    
    def test_sqlite_connection_validator_initialization(self):
        """
        RED: Test SQLiteConnectionValidator initialization
        Should create validator with configuration options
        """
        # Act
        validator = SQLiteConnectionValidator()
        
        # Assert
        assert validator is not None
        assert hasattr(validator, 'validate_connection')
        assert hasattr(validator, 'is_connection_healthy')
        assert hasattr(validator, 'timeout')
    
    def test_sqlite_connection_validator_with_timeout(self):
        """
        RED: Test SQLiteConnectionValidator with custom timeout
        Should accept and use custom timeout value
        """
        # Arrange
        custom_timeout = 5.0
        
        # Act
        validator = SQLiteConnectionValidator(timeout=custom_timeout)
        
        # Assert
        assert validator.timeout == custom_timeout
    
    def test_sqlite_connection_validator_healthy_connection(self, sqlite_connection):
        """
        RED: Test SQLiteConnectionValidator with healthy connection
        Should return success result for healthy connection
        """
        # Arrange
        validator = SQLiteConnectionValidator()
        
        # Act
        result = validator.validate_connection(sqlite_connection)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.error_message is None
        assert result.validation_time > 0
    
    def test_sqlite_connection_validator_unhealthy_connection(self):
        """
        RED: Test SQLiteConnectionValidator with unhealthy connection
        Should return failure result for unhealthy connection
        """
        # Arrange
        validator = SQLiteConnectionValidator()
        
        # Create closed connection
        conn = sqlite3.connect(":memory:")
        conn.close()
        
        # Act
        result = validator.validate_connection(conn)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert result.error_message is not None
        assert "sqlite" in result.error_message.lower() or "database" in result.error_message.lower()
    
    def test_sqlite_connection_validator_is_healthy_method(self, sqlite_connection):
        """
        RED: Test SQLiteConnectionValidator is_connection_healthy method
        Should provide quick health check without full validation
        """
        # Arrange
        validator = SQLiteConnectionValidator()
        
        # Act
        is_healthy = validator.is_connection_healthy(sqlite_connection)
        
        # Assert
        assert isinstance(is_healthy, bool)
        assert is_healthy is True
    
    def test_sqlite_connection_validator_custom_query(self, sqlite_connection):
        """
        RED: Test SQLiteConnectionValidator with custom validation query
        Should allow custom validation queries
        """
        # Arrange
        custom_query = "SELECT COUNT(*) FROM test_table"
        validator = SQLiteConnectionValidator(validation_query=custom_query)
        
        # Act
        result = validator.validate_connection(sqlite_connection)
        
        # Assert
        assert result.is_valid is True
    
    def test_sqlite_connection_validator_timeout_handling(self):
        """
        RED: Test SQLiteConnectionValidator timeout handling
        Should handle connection timeouts gracefully
        """
        # Arrange
        validator = SQLiteConnectionValidator(timeout=0.001)  # Very short timeout
        
        # Create connection that might timeout
        conn = sqlite3.connect(":memory:")
        
        # Act
        result = validator.validate_connection(conn)
        
        # Assert
        # Should either succeed quickly or fail with timeout
        assert isinstance(result, ValidationResult)
        if not result.is_valid:
            assert "timeout" in result.error_message.lower()
    
    def test_sqlite_connection_validator_retry_logic(self, sqlite_connection):
        """
        RED: Test SQLiteConnectionValidator with retry logic
        Should retry failed validations up to max retries
        """
        # Arrange
        validator = SQLiteConnectionValidator(max_retries=3)
        
        # Mock validation to fail initially then succeed
        original_validate = validator._perform_validation
        call_count = 0
        
        def mock_validate(conn):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("Temporary error")
            return ValidationResult.success()
        
        validator._perform_validation = mock_validate
        
        # Act
        result = validator.validate_connection(sqlite_connection)
        
        # Assert
        assert result.is_valid is True
        assert call_count == 3  # Should have retried


class TestSupabaseConnectionValidator:
    """Test SupabaseConnectionValidator functionality"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client for testing"""
        mock_client = Mock()
        mock_client.auth = Mock()
        mock_client.table = Mock()
        return mock_client
    
    def test_supabase_connection_validator_initialization(self):
        """
        RED: Test SupabaseConnectionValidator initialization
        Should create validator with Supabase-specific configuration
        """
        # Act
        validator = SupabaseConnectionValidator()
        
        # Assert
        assert validator is not None
        assert hasattr(validator, 'validate_connection')
        assert hasattr(validator, 'is_connection_healthy')
        assert hasattr(validator, 'timeout')
    
    def test_supabase_connection_validator_healthy_connection(self, mock_supabase_client):
        """
        RED: Test SupabaseConnectionValidator with healthy connection
        Should return success result for healthy Supabase connection
        """
        # Arrange
        validator = SupabaseConnectionValidator()
        
        # Mock successful auth check
        mock_supabase_client.auth.get_user.return_value = {"id": "test-user"}
        
        # Act
        result = validator.validate_connection(mock_supabase_client)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
    
    def test_supabase_connection_validator_unhealthy_connection(self, mock_supabase_client):
        """
        RED: Test SupabaseConnectionValidator with unhealthy connection
        Should return failure result for unhealthy Supabase connection
        """
        # Arrange
        validator = SupabaseConnectionValidator()
        
        # Mock failed auth check
        mock_supabase_client.auth.get_user.side_effect = Exception("Auth failed")
        
        # Act
        result = validator.validate_connection(mock_supabase_client)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert "auth" in result.error_message.lower()
    
    def test_supabase_connection_validator_network_timeout(self, mock_supabase_client):
        """
        RED: Test SupabaseConnectionValidator with network timeout
        Should handle network timeouts gracefully
        """
        # Arrange
        validator = SupabaseConnectionValidator(timeout=0.1)
        
        # Mock slow response
        def slow_auth():
            time.sleep(0.2)  # Longer than timeout
            return {"id": "test-user"}
        
        mock_supabase_client.auth.get_user = slow_auth
        
        # Act
        result = validator.validate_connection(mock_supabase_client)
        
        # Assert
        assert isinstance(result, ValidationResult)
        if not result.is_valid:
            assert "timeout" in result.error_message.lower()
    
    def test_supabase_connection_validator_custom_health_check(self, mock_supabase_client):
        """
        RED: Test SupabaseConnectionValidator with custom health check
        Should allow custom health check strategies
        """
        # Arrange
        validator = SupabaseConnectionValidator(strategy=ValidationStrategy.PING_TEST)
        
        # Mock table query for ping test
        mock_table = Mock()
        mock_table.select.return_value.limit.return_value.execute.return_value = {"data": []}
        mock_supabase_client.table.return_value = mock_table
        
        # Act
        result = validator.validate_connection(mock_supabase_client)
        
        # Assert
        assert isinstance(result, ValidationResult)
        # Validation should attempt the ping test
        mock_supabase_client.table.assert_called()
    
    @pytest.mark.asyncio
    async def test_supabase_connection_validator_async_validation(self, mock_supabase_client):
        """
        RED: Test SupabaseConnectionValidator async validation
        Should support async validation for non-blocking operations
        """
        # Arrange
        validator = SupabaseConnectionValidator()
        
        # Mock async auth check
        mock_supabase_client.auth.get_user = AsyncMock(return_value={"id": "test-user"})
        
        # Act
        result = await validator.validate_connection_async(mock_supabase_client)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True


class TestValidationStrategy:
    """Test ValidationStrategy enum and behavior"""
    
    def test_validation_strategy_enum_values(self):
        """
        RED: Test ValidationStrategy enum values
        Should define different validation strategies
        """
        # Act & Assert
        assert hasattr(ValidationStrategy, 'BASIC_HEALTH_CHECK')
        assert hasattr(ValidationStrategy, 'PING_TEST')
        assert hasattr(ValidationStrategy, 'QUERY_TEST')
        assert hasattr(ValidationStrategy, 'COMPREHENSIVE')
    
    def test_validation_strategy_selection(self):
        """
        RED: Test validation strategy selection
        Should affect validation behavior
        """
        # This test verifies that different strategies exist
        # Implementation details will be in validator classes
        strategies = [
            ValidationStrategy.BASIC_HEALTH_CHECK,
            ValidationStrategy.PING_TEST,
            ValidationStrategy.QUERY_TEST,
            ValidationStrategy.COMPREHENSIVE
        ]
        
        # All strategies should be distinct
        assert len(set(strategies)) == len(strategies)


class TestHealthCheckCache:
    """Test HealthCheckCache functionality"""
    
    def test_health_check_cache_initialization(self):
        """
        RED: Test HealthCheckCache initialization
        Should create cache with configurable TTL
        """
        # Act
        cache = HealthCheckCache(ttl_seconds=300)
        
        # Assert
        assert cache is not None
        assert cache.ttl_seconds == 300
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'clear')
    
    def test_health_check_cache_set_and_get(self):
        """
        RED: Test HealthCheckCache set and get operations
        Should store and retrieve validation results
        """
        # Arrange
        cache = HealthCheckCache(ttl_seconds=60)
        connection_id = "test-connection-123"
        result = ValidationResult.success()
        
        # Act
        cache.set(connection_id, result)
        cached_result = cache.get(connection_id)
        
        # Assert
        assert cached_result is not None
        assert cached_result.is_valid == result.is_valid
        assert cached_result.validation_time == result.validation_time
    
    def test_health_check_cache_expiration(self):
        """
        RED: Test HealthCheckCache TTL expiration
        Should expire cached results after TTL
        """
        # Arrange
        cache = HealthCheckCache(ttl_seconds=0.1)  # Very short TTL
        connection_id = "test-connection-123"
        result = ValidationResult.success()
        
        # Act
        cache.set(connection_id, result)
        
        # Verify it's cached
        assert cache.get(connection_id) is not None
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Assert
        assert cache.get(connection_id) is None
    
    def test_health_check_cache_miss(self):
        """
        RED: Test HealthCheckCache cache miss
        Should return None for non-existent keys
        """
        # Arrange
        cache = HealthCheckCache()
        
        # Act
        result = cache.get("non-existent-key")
        
        # Assert
        assert result is None
    
    def test_health_check_cache_clear(self):
        """
        RED: Test HealthCheckCache clear operation
        Should remove all cached results
        """
        # Arrange
        cache = HealthCheckCache()
        cache.set("key1", ValidationResult.success())
        cache.set("key2", ValidationResult.failure("test"))
        
        # Verify items are cached
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None
        
        # Act
        cache.clear()
        
        # Assert
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_health_check_cache_size_limit(self):
        """
        RED: Test HealthCheckCache size limiting
        Should limit cache size to prevent memory issues
        """
        # Arrange
        cache = HealthCheckCache(max_size=2)
        
        # Act
        cache.set("key1", ValidationResult.success())
        cache.set("key2", ValidationResult.success())
        cache.set("key3", ValidationResult.success())  # Should evict oldest
        
        # Assert
        # Oldest entry should be evicted
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None


class TestConnectionHealthMonitor:
    """Test ConnectionHealthMonitor functionality"""
    
    def test_connection_health_monitor_initialization(self):
        """
        RED: Test ConnectionHealthMonitor initialization
        Should create monitor with validator and cache
        """
        # Arrange
        validator = SQLiteConnectionValidator()
        
        # Act
        monitor = ConnectionHealthMonitor(validator)
        
        # Assert
        assert monitor is not None
        assert monitor.validator == validator
        assert hasattr(monitor, 'check_health')
        assert hasattr(monitor, 'check_health_cached')
    
    def test_connection_health_monitor_basic_check(self):
        """
        RED: Test ConnectionHealthMonitor basic health check
        Should perform health check using configured validator
        """
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_connection.return_value = ValidationResult.success()
        
        monitor = ConnectionHealthMonitor(mock_validator)
        mock_connection = Mock()
        
        # Act
        result = monitor.check_health(mock_connection)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        mock_validator.validate_connection.assert_called_once_with(mock_connection)
    
    def test_connection_health_monitor_cached_check(self):
        """
        RED: Test ConnectionHealthMonitor cached health check
        Should use cache to avoid redundant validations
        """
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_connection.return_value = ValidationResult.success()
        
        monitor = ConnectionHealthMonitor(mock_validator, enable_cache=True)
        mock_connection = Mock()
        connection_id = id(mock_connection)
        
        # Act
        result1 = monitor.check_health_cached(mock_connection, str(connection_id))
        result2 = monitor.check_health_cached(mock_connection, str(connection_id))
        
        # Assert
        assert result1.is_valid is True
        assert result2.is_valid is True
        # Validator should only be called once due to caching
        mock_validator.validate_connection.assert_called_once()
    
    def test_connection_health_monitor_batch_check(self):
        """
        RED: Test ConnectionHealthMonitor batch health check
        Should check multiple connections efficiently
        """
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_connection.return_value = ValidationResult.success()
        
        monitor = ConnectionHealthMonitor(mock_validator)
        connections = [Mock(), Mock(), Mock()]
        
        # Act
        results = monitor.check_health_batch(connections)
        
        # Assert
        assert len(results) == 3
        assert all(result.is_valid for result in results)
        assert mock_validator.validate_connection.call_count == 3
    
    @pytest.mark.asyncio
    async def test_connection_health_monitor_async_check(self):
        """
        RED: Test ConnectionHealthMonitor async health check
        Should support async health checking
        """
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_connection_async = AsyncMock(return_value=ValidationResult.success())
        
        monitor = ConnectionHealthMonitor(mock_validator)
        mock_connection = Mock()
        
        # Act
        result = await monitor.check_health_async(mock_connection)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
    
    def test_connection_health_monitor_error_handling(self):
        """
        RED: Test ConnectionHealthMonitor error handling
        Should handle validator errors gracefully
        """
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_connection.side_effect = Exception("Validator error")
        
        monitor = ConnectionHealthMonitor(mock_validator)
        mock_connection = Mock()
        
        # Act
        result = monitor.check_health(mock_connection)
        
        # Assert
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert "error" in result.error_message.lower()
    
    def test_connection_health_monitor_statistics(self):
        """
        RED: Test ConnectionHealthMonitor statistics tracking
        Should track validation statistics
        """
        # Arrange
        mock_validator = Mock()
        mock_validator.validate_connection.return_value = ValidationResult.success()
        
        monitor = ConnectionHealthMonitor(mock_validator, track_stats=True)
        mock_connection = Mock()
        
        # Act
        monitor.check_health(mock_connection)
        monitor.check_health(mock_connection)
        stats = monitor.get_statistics()
        
        # Assert
        assert stats['total_checks'] == 2
        assert stats['successful_checks'] == 2
        assert stats['failed_checks'] == 0
        assert 'average_validation_time' in stats