"""
Database Connection Validator Module.

This module provides connection validation and health checking for database
connections, including caching, retry logic, and different validation strategies.
"""

import time
import sqlite3
import threading
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict
from ..core.logging import get_logger


@dataclass(frozen=True)
class ValidationResult:
    """Result of a connection validation attempt"""
    is_valid: bool
    error_message: Optional[str] = None
    validation_time: float = field(default_factory=time.time)
    
    @classmethod
    def success(cls, validation_time: Optional[float] = None) -> 'ValidationResult':
        """
        Create a successful validation result.
        
        Args:
            validation_time: Optional custom validation time
            
        Returns:
            ValidationResult indicating success
        """
        return cls(
            is_valid=True,
            validation_time=validation_time or time.time()
        )
    
    @classmethod
    def failure(cls, error_message: str, validation_time: Optional[float] = None) -> 'ValidationResult':
        """
        Create a failed validation result.
        
        Args:
            error_message: Description of the validation failure
            validation_time: Optional custom validation time
            
        Returns:
            ValidationResult indicating failure
        """
        return cls(
            is_valid=False,
            error_message=error_message,
            validation_time=validation_time or time.time()
        )
    
    def __str__(self) -> str:
        """String representation of validation result"""
        if self.is_valid:
            return f"ValidationResult(valid, time={self.validation_time:.4f})"
        else:
            return f"ValidationResult(invalid: {self.error_message}, time={self.validation_time:.4f})"


class ValidationStrategy(Enum):
    """Validation strategies for different levels of health checking"""
    BASIC_HEALTH_CHECK = "basic"
    PING_TEST = "ping"
    QUERY_TEST = "query"
    COMPREHENSIVE = "comprehensive"


class ConnectionValidator(ABC):
    """Abstract base class for connection validators"""
    
    def __init__(self, timeout: float = 30.0, max_retries: int = 0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    @abstractmethod
    def validate_connection(self, connection: Any) -> ValidationResult:
        """
        Validate a database connection.
        
        Args:
            connection: Database connection to validate
            
        Returns:
            ValidationResult indicating success or failure
        """
        pass
    
    @abstractmethod
    def is_connection_healthy(self, connection: Any) -> bool:
        """
        Quick health check for a database connection.
        
        Args:
            connection: Database connection to check
            
        Returns:
            True if connection appears healthy, False otherwise
        """
        pass


class SQLiteConnectionValidator(ConnectionValidator):
    """Validator for SQLite database connections"""
    
    def __init__(
        self, 
        timeout: float = 30.0, 
        max_retries: int = 0,
        validation_query: str = "SELECT 1",
        strategy: ValidationStrategy = ValidationStrategy.BASIC_HEALTH_CHECK
    ):
        super().__init__(timeout, max_retries)
        self.validation_query = validation_query
        self.strategy = strategy
    
    def validate_connection(self, connection: sqlite3.Connection) -> ValidationResult:
        """
        Validate a SQLite connection.
        
        Args:
            connection: SQLite connection to validate
            
        Returns:
            ValidationResult indicating success or failure
        """
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self._perform_validation(connection)
                # Create new result with updated timing
                return ValidationResult(
                    is_valid=result.is_valid,
                    error_message=result.error_message,
                    validation_time=time.time() - start_time
                )
                
            except Exception as e:
                if attempt == self.max_retries:
                    return ValidationResult.failure(
                        f"SQLite validation failed after {self.max_retries} retries: {str(e)}",
                        time.time() - start_time
                    )
                
                # Brief pause before retry
                time.sleep(0.1 * (attempt + 1))
        
        return ValidationResult.failure(
            "Unexpected validation failure",
            time.time() - start_time
        )
    
    def _perform_validation(self, connection: sqlite3.Connection) -> ValidationResult:
        """
        Perform the actual validation logic.
        
        Args:
            connection: SQLite connection to validate
            
        Returns:
            ValidationResult
        """
        try:
            cursor = connection.cursor()
            
            if self.strategy == ValidationStrategy.BASIC_HEALTH_CHECK:
                # Simple SELECT 1 query
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            elif self.strategy == ValidationStrategy.PING_TEST:
                # Test connection responsiveness
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise sqlite3.Error("Unexpected query result")
            
            elif self.strategy == ValidationStrategy.QUERY_TEST:
                # Use custom validation query
                cursor.execute(self.validation_query)
                cursor.fetchall()
            
            elif self.strategy == ValidationStrategy.COMPREHENSIVE:
                # Multiple validation checks
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.execute("PRAGMA integrity_check(1)")
                integrity_result = cursor.fetchone()
                if integrity_result[0] != "ok":
                    raise sqlite3.Error("Database integrity check failed")
            
            cursor.close()
            return ValidationResult.success()
            
        except (sqlite3.Error, sqlite3.OperationalError) as e:
            return ValidationResult.failure(f"SQLite error: {str(e)}")
        except Exception as e:
            return ValidationResult.failure(f"Validation error: {str(e)}")
    
    def is_connection_healthy(self, connection: sqlite3.Connection) -> bool:
        """
        Quick health check for SQLite connection.
        
        Args:
            connection: SQLite connection to check
            
        Returns:
            True if connection appears healthy
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except (sqlite3.Error, sqlite3.OperationalError):
            return False


class SupabaseConnectionValidator(ConnectionValidator):
    """Validator for Supabase client connections"""
    
    def __init__(
        self, 
        timeout: float = 30.0, 
        max_retries: int = 0,
        strategy: ValidationStrategy = ValidationStrategy.BASIC_HEALTH_CHECK
    ):
        super().__init__(timeout, max_retries)
        self.strategy = strategy
    
    def validate_connection(self, client: Any) -> ValidationResult:
        """
        Validate a Supabase client connection.
        
        Args:
            client: Supabase client to validate
            
        Returns:
            ValidationResult indicating success or failure
        """
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self._perform_validation(client)
                # Create new result with updated timing
                return ValidationResult(
                    is_valid=result.is_valid,
                    error_message=result.error_message,
                    validation_time=time.time() - start_time
                )
                
            except Exception as e:
                if attempt == self.max_retries:
                    return ValidationResult.failure(
                        f"Supabase validation failed after {self.max_retries} retries: {str(e)}",
                        time.time() - start_time
                    )
                
                # Brief pause before retry
                time.sleep(0.1 * (attempt + 1))
        
        return ValidationResult.failure(
            "Unexpected validation failure",
            time.time() - start_time
        )
    
    def _perform_validation(self, client: Any) -> ValidationResult:
        """
        Perform the actual validation logic for Supabase.
        
        Args:
            client: Supabase client to validate
            
        Returns:
            ValidationResult
        """
        try:
            if self.strategy == ValidationStrategy.BASIC_HEALTH_CHECK:
                # Simple auth check
                client.auth.get_user()
            
            elif self.strategy == ValidationStrategy.PING_TEST:
                # Test with a simple table query
                client.table("__ping_test__").select("*").limit(1).execute()
            
            elif self.strategy == ValidationStrategy.QUERY_TEST:
                # Test actual table access
                client.table("public").select("*").limit(1).execute()
            
            elif self.strategy == ValidationStrategy.COMPREHENSIVE:
                # Multiple validation checks
                client.auth.get_user()
                # Additional checks could be added here
            
            return ValidationResult.success()
            
        except Exception as e:
            return ValidationResult.failure(f"Supabase auth error: {str(e)}")
    
    def is_connection_healthy(self, client: Any) -> bool:
        """
        Quick health check for Supabase client.
        
        Args:
            client: Supabase client to check
            
        Returns:
            True if client appears healthy
        """
        try:
            client.auth.get_user()
            return True
        except Exception:
            return False
    
    async def validate_connection_async(self, client: Any) -> ValidationResult:
        """
        Async validation for Supabase client.
        
        Args:
            client: Supabase client to validate
            
        Returns:
            ValidationResult indicating success or failure
        """
        start_time = time.time()
        
        try:
            # For now, run sync validation in executor
            # In a real implementation, this would use async Supabase methods
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.validate_connection, client)
            return result
            
        except Exception as e:
            return ValidationResult.failure(
                f"Async validation error: {str(e)}",
                time.time() - start_time
            )


class HealthCheckCache:
    """Cache for connection health check results"""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self.logger = get_logger("health_check_cache")
    
    def get(self, connection_id: str) -> Optional[ValidationResult]:
        """
        Get cached validation result.
        
        Args:
            connection_id: Unique identifier for the connection
            
        Returns:
            Cached ValidationResult or None if not found/expired
        """
        with self._lock:
            if connection_id not in self._cache:
                return None
            
            cached_time, result = self._cache[connection_id]
            
            # Check if cached result has expired
            if time.time() - cached_time > self.ttl_seconds:
                del self._cache[connection_id]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(connection_id)
            return result
    
    def set(self, connection_id: str, result: ValidationResult):
        """
        Cache validation result.
        
        Args:
            connection_id: Unique identifier for the connection
            result: ValidationResult to cache
        """
        with self._lock:
            # Remove oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[connection_id] = (time.time(), result)
    
    def clear(self):
        """Clear all cached results"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)


class ConnectionHealthMonitor:
    """Monitor for managing connection health checks"""
    
    def __init__(
        self, 
        validator: ConnectionValidator, 
        enable_cache: bool = True,
        cache_ttl: int = 300,
        track_stats: bool = False
    ):
        self.validator = validator
        self.enable_cache = enable_cache
        self.cache = HealthCheckCache(ttl_seconds=cache_ttl) if enable_cache else None
        self.track_stats = track_stats
        self.logger = get_logger("connection_health_monitor")
        
        # Statistics tracking
        if track_stats:
            self._stats = {
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'total_validation_time': 0.0
            }
            self._stats_lock = threading.Lock()
    
    def check_health(self, connection: Any) -> ValidationResult:
        """
        Check connection health using the configured validator.
        
        Args:
            connection: Database connection to check
            
        Returns:
            ValidationResult
        """
        try:
            start_time = time.time()
            result = self.validator.validate_connection(connection)
            
            if self.track_stats:
                self._update_stats(result, time.time() - start_time, cache_hit=False)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            return ValidationResult.failure(f"Health check error: {str(e)}")
    
    def check_health_cached(self, connection: Any, connection_id: str) -> ValidationResult:
        """
        Check connection health with caching.
        
        Args:
            connection: Database connection to check
            connection_id: Unique identifier for caching
            
        Returns:
            ValidationResult (may be cached)
        """
        # Try cache first
        if self.enable_cache and self.cache:
            cached_result = self.cache.get(connection_id)
            if cached_result:
                if self.track_stats:
                    self._update_stats(cached_result, 0.0, cache_hit=True)
                return cached_result
        
        # Perform actual health check
        result = self.check_health(connection)
        
        # Cache the result
        if self.enable_cache and self.cache:
            self.cache.set(connection_id, result)
            if self.track_stats:
                with self._stats_lock:
                    self._stats['cache_misses'] += 1
        
        return result
    
    def check_health_batch(self, connections: List[Any]) -> List[ValidationResult]:
        """
        Check health of multiple connections.
        
        Args:
            connections: List of database connections to check
            
        Returns:
            List of ValidationResults in same order as input
        """
        results = []
        for connection in connections:
            result = self.check_health(connection)
            results.append(result)
        return results
    
    async def check_health_async(self, connection: Any) -> ValidationResult:
        """
        Async health check.
        
        Args:
            connection: Database connection to check
            
        Returns:
            ValidationResult
        """
        try:
            # Check if validator supports async
            if hasattr(self.validator, 'validate_connection_async'):
                return await self.validator.validate_connection_async(connection)
            else:
                # Run sync validation in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.check_health, connection)
                
        except Exception as e:
            self.logger.error(f"Error during async health check: {e}")
            return ValidationResult.failure(f"Async health check error: {str(e)}")
    
    def _update_stats(self, result: ValidationResult, validation_time: float, cache_hit: bool):
        """Update statistics tracking"""
        if not self.track_stats:
            return
        
        with self._stats_lock:
            self._stats['total_checks'] += 1
            self._stats['total_validation_time'] += validation_time
            
            if result.is_valid:
                self._stats['successful_checks'] += 1
            else:
                self._stats['failed_checks'] += 1
            
            if cache_hit:
                self._stats['cache_hits'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get health check statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self.track_stats:
            return {}
        
        with self._stats_lock:
            stats = self._stats.copy()
            
            # Calculate derived statistics
            if stats['total_checks'] > 0:
                stats['success_rate'] = stats['successful_checks'] / stats['total_checks']
                stats['failure_rate'] = stats['failed_checks'] / stats['total_checks']
                stats['average_validation_time'] = (
                    stats['total_validation_time'] / stats['total_checks']
                )
            else:
                stats['success_rate'] = 0.0
                stats['failure_rate'] = 0.0
                stats['average_validation_time'] = 0.0
            
            if self.enable_cache and stats['total_checks'] > 0:
                total_cache_requests = stats['cache_hits'] + stats['cache_misses']
                if total_cache_requests > 0:
                    stats['cache_hit_rate'] = stats['cache_hits'] / total_cache_requests
                else:
                    stats['cache_hit_rate'] = 0.0
            
            return stats
    
    def reset_statistics(self):
        """Reset all statistics"""
        if not self.track_stats:
            return
        
        with self._stats_lock:
            self._stats = {
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'total_validation_time': 0.0
            }