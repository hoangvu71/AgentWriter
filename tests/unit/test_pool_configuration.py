"""
TDD Test Suite for Pool Configuration module.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- ConnectionPoolConfig configuration validation
- Configuration validation logic
- Configuration factory methods
- Environment variable integration
- Configuration merging and defaults
- Configuration serialization/deserialization
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from src.database.pool_configuration import (
    ConnectionPoolConfig,
    PoolConfigurationValidator,
    PoolConfigurationFactory
)


class TestConnectionPoolConfig:
    """Test ConnectionPoolConfig dataclass functionality"""
    
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
    
    def test_connection_pool_config_immutability(self):
        """
        RED: Test ConnectionPoolConfig immutability
        Should be immutable after creation (frozen dataclass)
        """
        # Arrange
        config = ConnectionPoolConfig()
        
        # Act & Assert
        with pytest.raises(AttributeError):
            config.min_connections = 5
    
    def test_connection_pool_config_to_dict(self):
        """
        RED: Test ConnectionPoolConfig conversion to dictionary
        Should convert to dictionary for serialization
        """
        # Arrange
        config = ConnectionPoolConfig(min_connections=3, max_connections=15)
        
        # Act
        config_dict = asdict(config)
        
        # Assert
        assert isinstance(config_dict, dict)
        assert config_dict['min_connections'] == 3
        assert config_dict['max_connections'] == 15
        assert 'max_idle_time' in config_dict
        assert 'connection_timeout' in config_dict
    
    def test_connection_pool_config_equality(self):
        """
        RED: Test ConnectionPoolConfig equality comparison
        Should support equality comparison between instances
        """
        # Arrange
        config1 = ConnectionPoolConfig(min_connections=5)
        config2 = ConnectionPoolConfig(min_connections=5)
        config3 = ConnectionPoolConfig(min_connections=3)
        
        # Act & Assert
        assert config1 == config2
        assert config1 != config3
        assert config2 != config3


class TestPoolConfigurationValidator:
    """Test PoolConfigurationValidator functionality"""
    
    def test_pool_configuration_validator_initialization(self):
        """
        RED: Test PoolConfigurationValidator initialization
        Should create validator instance with default settings
        """
        # Act
        validator = PoolConfigurationValidator()
        
        # Assert
        assert validator is not None
        assert hasattr(validator, 'validate')
        assert hasattr(validator, 'validate_range')
        assert hasattr(validator, 'validate_logical_constraints')
    
    def test_pool_configuration_validator_validate_success(self):
        """
        RED: Test PoolConfigurationValidator validation success
        Should validate correct configuration without errors
        """
        # Arrange
        validator = PoolConfigurationValidator()
        config = ConnectionPoolConfig(
            min_connections=2,
            max_connections=10,
            max_idle_time=300,
            connection_timeout=30
        )
        
        # Act
        result = validator.validate(config)
        
        # Assert
        assert result is True
    
    def test_pool_configuration_validator_validate_min_greater_than_max(self):
        """
        RED: Test PoolConfigurationValidator validation failure
        Should reject configuration where min_connections > max_connections
        """
        # Arrange
        validator = PoolConfigurationValidator()
        config = ConnectionPoolConfig(
            min_connections=15,
            max_connections=10
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="min_connections.*max_connections"):
            validator.validate(config)
    
    def test_pool_configuration_validator_validate_negative_values(self):
        """
        RED: Test PoolConfigurationValidator validation of negative values
        Should reject configuration with negative values
        """
        # Arrange
        validator = PoolConfigurationValidator()
        
        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            config = ConnectionPoolConfig(min_connections=-1)
            validator.validate(config)
        
        with pytest.raises(ValueError, match="must be positive"):
            config = ConnectionPoolConfig(max_connections=-5)
            validator.validate(config)
        
        with pytest.raises(ValueError, match="must be positive"):
            config = ConnectionPoolConfig(connection_timeout=-10)
            validator.validate(config)
    
    def test_pool_configuration_validator_validate_zero_values(self):
        """
        RED: Test PoolConfigurationValidator validation of zero values
        Should reject configuration with zero values for critical parameters
        """
        # Arrange
        validator = PoolConfigurationValidator()
        
        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            config = ConnectionPoolConfig(min_connections=0)
            validator.validate(config)
        
        with pytest.raises(ValueError, match="must be positive"):
            config = ConnectionPoolConfig(max_connections=0)
            validator.validate(config)
    
    def test_pool_configuration_validator_validate_range_constraints(self):
        """
        RED: Test PoolConfigurationValidator range constraints
        Should validate reasonable ranges for configuration values
        """
        # Arrange
        validator = PoolConfigurationValidator()
        
        # Act & Assert
        # Test extremely high values
        with pytest.raises(ValueError, match="exceeds maximum"):
            config = ConnectionPoolConfig(max_connections=10000)
            validator.validate(config)
        
        # Test extremely long timeouts
        with pytest.raises(ValueError, match="exceeds maximum"):
            config = ConnectionPoolConfig(connection_timeout=86400)  # 24 hours
            validator.validate(config)
    
    def test_pool_configuration_validator_validate_range_method(self):
        """
        RED: Test PoolConfigurationValidator validate_range method
        Should validate individual value ranges
        """
        # Arrange
        validator = PoolConfigurationValidator()
        
        # Act & Assert
        assert validator.validate_range(5, 1, 100, "test_param") is True
        
        with pytest.raises(ValueError):
            validator.validate_range(0, 1, 100, "test_param")
        
        with pytest.raises(ValueError):
            validator.validate_range(101, 1, 100, "test_param")
    
    def test_pool_configuration_validator_logical_constraints(self):
        """
        RED: Test PoolConfigurationValidator logical constraints
        Should validate logical relationships between parameters
        """
        # Arrange
        validator = PoolConfigurationValidator()
        
        # Act & Assert
        # Valid constraints
        config = ConnectionPoolConfig(min_connections=2, max_connections=10)
        assert validator.validate_logical_constraints(config) is True
        
        # Invalid constraints
        config = ConnectionPoolConfig(min_connections=10, max_connections=5)
        with pytest.raises(ValueError):
            validator.validate_logical_constraints(config)
        
        # Edge case: equal values should be allowed
        config = ConnectionPoolConfig(min_connections=5, max_connections=5)
        assert validator.validate_logical_constraints(config) is True


class TestPoolConfigurationFactory:
    """Test PoolConfigurationFactory functionality"""
    
    def test_pool_configuration_factory_initialization(self):
        """
        RED: Test PoolConfigurationFactory initialization
        Should create factory instance
        """
        # Act
        factory = PoolConfigurationFactory()
        
        # Assert
        assert factory is not None
        assert hasattr(factory, 'create_default')
        assert hasattr(factory, 'create_from_dict')
        assert hasattr(factory, 'create_from_environment')
    
    def test_pool_configuration_factory_create_default(self):
        """
        RED: Test PoolConfigurationFactory default configuration creation
        Should create valid default configuration
        """
        # Arrange
        factory = PoolConfigurationFactory()
        
        # Act
        config = factory.create_default()
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.enable_metrics is True
    
    def test_pool_configuration_factory_create_sqlite_optimized(self):
        """
        RED: Test PoolConfigurationFactory SQLite optimized configuration
        Should create configuration optimized for SQLite usage
        """
        # Arrange
        factory = PoolConfigurationFactory()
        
        # Act
        config = factory.create_sqlite_optimized()
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        # SQLite specific optimizations
        assert config.min_connections >= 1
        assert config.max_connections <= 50  # SQLite has connection limits
        assert config.connection_timeout <= 60  # Faster timeouts for local DB
    
    def test_pool_configuration_factory_create_supabase_optimized(self):
        """
        RED: Test PoolConfigurationFactory Supabase optimized configuration
        Should create configuration optimized for Supabase usage
        """
        # Arrange
        factory = PoolConfigurationFactory()
        
        # Act
        config = factory.create_supabase_optimized()
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        # Supabase specific optimizations
        assert config.min_connections >= 2
        assert config.connection_timeout >= 30  # Network calls need more time
        assert config.health_check_interval >= 60  # Less frequent for remote DB
    
    def test_pool_configuration_factory_create_from_dict(self):
        """
        RED: Test PoolConfigurationFactory creation from dictionary
        Should create configuration from dictionary input
        """
        # Arrange
        factory = PoolConfigurationFactory()
        config_dict = {
            'min_connections': 3,
            'max_connections': 15,
            'connection_timeout': 45,
            'enable_metrics': False
        }
        
        # Act
        config = factory.create_from_dict(config_dict)
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        assert config.min_connections == 3
        assert config.max_connections == 15
        assert config.connection_timeout == 45
        assert config.enable_metrics is False
        # Should use defaults for unspecified values
        assert config.max_idle_time == 300
    
    def test_pool_configuration_factory_create_from_dict_validation(self):
        """
        RED: Test PoolConfigurationFactory dictionary validation
        Should validate input dictionary before creating configuration
        """
        # Arrange
        factory = PoolConfigurationFactory()
        invalid_dict = {
            'min_connections': 15,
            'max_connections': 10  # Invalid: min > max
        }
        
        # Act & Assert
        with pytest.raises(ValueError):
            factory.create_from_dict(invalid_dict)
    
    @patch.dict(os.environ, {
        'POOL_MIN_CONNECTIONS': '4',
        'POOL_MAX_CONNECTIONS': '20',
        'POOL_CONNECTION_TIMEOUT': '60',
        'POOL_ENABLE_METRICS': 'false'
    })
    def test_pool_configuration_factory_create_from_environment(self):
        """
        RED: Test PoolConfigurationFactory creation from environment variables
        Should create configuration from environment variables
        """
        # Arrange
        factory = PoolConfigurationFactory()
        
        # Act
        config = factory.create_from_environment()
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        assert config.min_connections == 4
        assert config.max_connections == 20
        assert config.connection_timeout == 60
        assert config.enable_metrics is False
    
    @patch.dict(os.environ, {
        'POOL_MIN_CONNECTIONS': 'invalid',
        'POOL_MAX_CONNECTIONS': '20'
    })
    def test_pool_configuration_factory_create_from_environment_invalid(self):
        """
        RED: Test PoolConfigurationFactory environment variable validation
        Should handle invalid environment variable values gracefully
        """
        # Arrange
        factory = PoolConfigurationFactory()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid.*environment"):
            factory.create_from_environment()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_pool_configuration_factory_create_from_environment_defaults(self):
        """
        RED: Test PoolConfigurationFactory environment with defaults
        Should use default values when environment variables are not set
        """
        # Arrange
        factory = PoolConfigurationFactory()
        
        # Act
        config = factory.create_from_environment()
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        # Should use default values
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.enable_metrics is True
    
    def test_pool_configuration_factory_create_with_overrides(self):
        """
        RED: Test PoolConfigurationFactory with parameter overrides
        Should allow selective parameter overrides
        """
        # Arrange
        factory = PoolConfigurationFactory()
        base_config = ConnectionPoolConfig(min_connections=2, max_connections=10)
        overrides = {'max_connections': 20, 'connection_timeout': 60}
        
        # Act
        config = factory.create_with_overrides(base_config, overrides)
        
        # Assert
        assert isinstance(config, ConnectionPoolConfig)
        assert config.min_connections == 2  # Unchanged
        assert config.max_connections == 20  # Overridden
        assert config.connection_timeout == 60  # Overridden
        # Other values should remain from base
        assert config.max_idle_time == base_config.max_idle_time
    
    def test_pool_configuration_factory_create_with_overrides_validation(self):
        """
        RED: Test PoolConfigurationFactory override validation
        Should validate overridden configuration
        """
        # Arrange
        factory = PoolConfigurationFactory()
        base_config = ConnectionPoolConfig(min_connections=2, max_connections=10)
        invalid_overrides = {'max_connections': 1}  # Would make max < min
        
        # Act & Assert
        with pytest.raises(ValueError):
            factory.create_with_overrides(base_config, invalid_overrides)


class TestConfigurationIntegration:
    """Test integration between configuration components"""
    
    def test_configuration_validator_factory_integration(self):
        """
        RED: Test integration between validator and factory
        Should ensure factory creates valid configurations
        """
        # Arrange
        factory = PoolConfigurationFactory()
        validator = PoolConfigurationValidator()
        
        # Act
        default_config = factory.create_default()
        sqlite_config = factory.create_sqlite_optimized()
        supabase_config = factory.create_supabase_optimized()
        
        # Assert
        assert validator.validate(default_config) is True
        assert validator.validate(sqlite_config) is True
        assert validator.validate(supabase_config) is True
    
    def test_configuration_serialization_roundtrip(self):
        """
        RED: Test configuration serialization and deserialization
        Should maintain configuration integrity through serialization
        """
        # Arrange
        factory = PoolConfigurationFactory()
        original_config = ConnectionPoolConfig(
            min_connections=3,
            max_connections=15,
            connection_timeout=45
        )
        
        # Act
        config_dict = asdict(original_config)
        restored_config = factory.create_from_dict(config_dict)
        
        # Assert
        assert restored_config == original_config
        assert asdict(restored_config) == config_dict