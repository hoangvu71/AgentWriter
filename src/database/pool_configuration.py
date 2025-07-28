"""
Database Connection Pool Configuration Module.

This module provides configuration management for database connection pools,
including validation, factory methods, and environment variable integration.
"""

import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict, replace
from ..core.logging import get_logger


@dataclass(frozen=True)
class ConnectionPoolConfig:
    """Configuration for database connection pools"""
    min_connections: int = 2
    max_connections: int = 10
    max_idle_time: int = 300  # 5 minutes
    connection_timeout: int = 30  # seconds
    health_check_interval: int = 60  # seconds
    max_retries: int = 3
    enable_metrics: bool = True


class PoolConfigurationValidator:
    """Validator for connection pool configurations"""
    
    def __init__(self):
        self.logger = get_logger("pool_config_validator")
        
        # Define validation ranges
        self.min_connection_range = (1, 1000)
        self.max_connection_range = (1, 1000)
        self.timeout_range = (1, 3600)  # 1 second to 1 hour
        self.idle_time_range = (1, 86400)  # 1 second to 24 hours
        self.health_check_range = (1, 3600)  # 1 second to 1 hour
        self.retry_range = (0, 10)
    
    def validate(self, config: ConnectionPoolConfig) -> bool:
        """
        Validate a connection pool configuration.
        
        Args:
            config: The configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        self._validate_individual_parameters(config)
        self.validate_logical_constraints(config)
        return True
    
    def _validate_individual_parameters(self, config: ConnectionPoolConfig):
        """Validate individual configuration parameters"""
        self.validate_range(
            config.min_connections, 
            *self.min_connection_range, 
            "min_connections"
        )
        
        self.validate_range(
            config.max_connections, 
            *self.max_connection_range, 
            "max_connections"
        )
        
        self.validate_range(
            config.connection_timeout, 
            *self.timeout_range, 
            "connection_timeout"
        )
        
        self.validate_range(
            config.max_idle_time, 
            *self.idle_time_range, 
            "max_idle_time"
        )
        
        self.validate_range(
            config.health_check_interval, 
            *self.health_check_range, 
            "health_check_interval"
        )
        
        self.validate_range(
            config.max_retries, 
            *self.retry_range, 
            "max_retries"
        )
    
    def validate_range(self, value: int, min_val: int, max_val: int, param_name: str) -> bool:
        """
        Validate that a value is within the specified range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            param_name: Parameter name for error messages
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If value is out of range
        """
        if value < min_val:
            if min_val == 1:
                raise ValueError(f"{param_name} must be positive, got {value}")
            else:
                raise ValueError(f"{param_name} must be at least {min_val}, got {value}")
        
        if value > max_val:
            raise ValueError(f"{param_name} exceeds maximum allowed value {max_val}, got {value}")
        
        return True
    
    def validate_logical_constraints(self, config: ConnectionPoolConfig) -> bool:
        """
        Validate logical relationships between configuration parameters.
        
        Args:
            config: The configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If logical constraints are violated
        """
        if config.min_connections > config.max_connections:
            raise ValueError(
                f"min_connections ({config.min_connections}) cannot be greater than "
                f"max_connections ({config.max_connections})"
            )
        
        return True


class PoolConfigurationFactory:
    """Factory for creating connection pool configurations"""
    
    def __init__(self):
        self.logger = get_logger("pool_config_factory")
        self.validator = PoolConfigurationValidator()
    
    def create_default(self) -> ConnectionPoolConfig:
        """
        Create a default connection pool configuration.
        
        Returns:
            Default ConnectionPoolConfig instance
        """
        config = ConnectionPoolConfig()
        self.validator.validate(config)
        return config
    
    def create_sqlite_optimized(self) -> ConnectionPoolConfig:
        """
        Create a configuration optimized for SQLite databases.
        
        Returns:
            SQLite-optimized ConnectionPoolConfig instance
        """
        config = ConnectionPoolConfig(
            min_connections=1,  # SQLite can handle fewer connections
            max_connections=20,  # Conservative limit for SQLite
            max_idle_time=180,  # Shorter idle time for local DB
            connection_timeout=30,  # Quick timeout for local access
            health_check_interval=30,  # More frequent checks for local DB
            max_retries=3,
            enable_metrics=True
        )
        
        self.validator.validate(config)
        return config
    
    def create_supabase_optimized(self) -> ConnectionPoolConfig:
        """
        Create a configuration optimized for Supabase databases.
        
        Returns:
            Supabase-optimized ConnectionPoolConfig instance
        """
        config = ConnectionPoolConfig(
            min_connections=2,  # Maintain minimum for network DB
            max_connections=15,  # Reasonable limit for cloud DB
            max_idle_time=600,  # Longer idle time for network DB
            connection_timeout=60,  # Longer timeout for network calls
            health_check_interval=120,  # Less frequent checks for remote DB
            max_retries=5,  # More retries for network issues
            enable_metrics=True
        )
        
        self.validator.validate(config)
        return config
    
    def create_from_dict(self, config_dict: Dict[str, Any]) -> ConnectionPoolConfig:
        """
        Create a configuration from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values
            
        Returns:
            ConnectionPoolConfig instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Start with defaults and override with provided values
            defaults = asdict(ConnectionPoolConfig())
            defaults.update(config_dict)
            
            config = ConnectionPoolConfig(**defaults)
            self.validator.validate(config)
            return config
            
        except TypeError as e:
            raise ValueError(f"Invalid configuration parameters: {e}")
    
    def create_from_environment(self, prefix: str = "POOL_") -> ConnectionPoolConfig:
        """
        Create a configuration from environment variables.
        
        Args:
            prefix: Prefix for environment variable names
            
        Returns:
            ConnectionPoolConfig instance
            
        Raises:
            ValueError: If environment variables contain invalid values
        """
        try:
            env_config = {}
            
            # Mapping of config fields to environment variable names
            env_mappings = {
                'min_connections': f'{prefix}MIN_CONNECTIONS',
                'max_connections': f'{prefix}MAX_CONNECTIONS',
                'max_idle_time': f'{prefix}MAX_IDLE_TIME',
                'connection_timeout': f'{prefix}CONNECTION_TIMEOUT',
                'health_check_interval': f'{prefix}HEALTH_CHECK_INTERVAL',
                'max_retries': f'{prefix}MAX_RETRIES',
                'enable_metrics': f'{prefix}ENABLE_METRICS'
            }
            
            for field, env_var in env_mappings.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    if field == 'enable_metrics':
                        # Handle boolean environment variable
                        env_config[field] = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        # Handle integer environment variables
                        try:
                            env_config[field] = int(env_value)
                        except ValueError:
                            raise ValueError(
                                f"Invalid value for environment variable {env_var}: '{env_value}'. "
                                f"Expected integer."
                            )
            
            return self.create_from_dict(env_config)
            
        except ValueError as e:
            raise ValueError(f"Invalid configuration from environment variables: {e}")
    
    def create_with_overrides(
        self, 
        base_config: ConnectionPoolConfig, 
        overrides: Dict[str, Any]
    ) -> ConnectionPoolConfig:
        """
        Create a configuration by overriding values in a base configuration.
        
        Args:
            base_config: Base configuration to start with
            overrides: Dictionary of values to override
            
        Returns:
            New ConnectionPoolConfig instance with overrides applied
            
        Raises:
            ValueError: If resulting configuration is invalid
        """
        try:
            # Use dataclass replace to create new instance with overrides
            config = replace(base_config, **overrides)
            self.validator.validate(config)
            return config
            
        except TypeError as e:
            raise ValueError(f"Invalid override parameters: {e}")