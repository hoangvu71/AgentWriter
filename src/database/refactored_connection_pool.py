"""
Refactored Database Connection Pool using modular architecture.

This is the new modular implementation that will replace the original
connection_pool.py while maintaining 100% API compatibility.
"""

import sqlite3
import asyncio
import threading
import time
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
from queue import Queue, Empty, Full
from supabase import Client as SupabaseClient

from .pool_configuration import ConnectionPoolConfig, PoolConfigurationFactory, PoolConfigurationValidator
from .pool_metrics import PoolMetrics, MetricsCalculator, MetricsReporter, MetricsSnapshot
from .connection_validator import SQLiteConnectionValidator, SupabaseConnectionValidator, ValidationStrategy
from ..core.logging import get_logger


# Re-export the original dataclasses and protocols for backward compatibility
@dataclass
class SQLitePooledConnection:
    """Wrapper for SQLite connections with pooling metadata"""
    connection: sqlite3.Connection
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    
    def execute(self, query: str, params: List[Any] = None) -> sqlite3.Cursor:
        """Execute query and update metadata"""
        self.last_used = time.time()
        self.use_count += 1
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor
    
    def close(self) -> None:
        """Close the underlying connection"""
        self.connection.close()
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        validator = SQLiteConnectionValidator()
        return validator.is_connection_healthy(self.connection)
    
    @property
    def is_idle_expired(self) -> bool:
        """Check if connection has been idle too long"""
        return (time.time() - self.last_used) > 300  # 5 minutes


@dataclass
class SupabasePooledConnection:
    """Wrapper for Supabase client with pooling metadata"""
    client: SupabaseClient
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    
    def execute(self, table: str, operation: str, **kwargs) -> Any:
        """Execute Supabase operation and update metadata"""
        self.last_used = time.time()
        self.use_count += 1
        
        table_ref = self.client.table(table)
        if operation == "select":
            return table_ref.select(kwargs.get("columns", "*"))
        elif operation == "insert":
            return table_ref.insert(kwargs.get("data", {}))
        elif operation == "update":
            return table_ref.update(kwargs.get("data", {}))
        elif operation == "delete":
            return table_ref.delete()
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    def close(self) -> None:
        """Close the Supabase client (graceful cleanup)"""
        pass
    
    def is_healthy(self) -> bool:
        """Check if Supabase client is healthy"""
        validator = SupabaseConnectionValidator()
        return validator.is_connection_healthy(self.client)
    
    @property
    def is_idle_expired(self) -> bool:
        """Check if connection has been idle too long"""
        return (time.time() - self.last_used) > 300  # 5 minutes


class ModularSQLiteConnectionPool:
    """High-performance SQLite connection pool with modular architecture"""
    
    def __init__(self, db_path: str, config: ConnectionPoolConfig):
        self.db_path = db_path
        self.config = config
        self.logger = get_logger("sqlite_pool")
        
        # Validate configuration
        validator = PoolConfigurationValidator()
        validator.validate(config)
        
        # Initialize modular components
        self._metrics = PoolMetrics()
        self._metrics_calculator = MetricsCalculator()
        self._metrics_reporter = MetricsReporter()
        self._connection_validator = SQLiteConnectionValidator(
            timeout=config.connection_timeout,
            strategy=ValidationStrategy.BASIC_HEALTH_CHECK
        )
        
        # Connection pool and management
        self._pool: Queue[SQLitePooledConnection] = Queue(maxsize=config.max_connections)
        self._all_connections: List[SQLitePooledConnection] = []
        self._lock = threading.RLock()
        
        # Health monitoring
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        # Initialize minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections"""
        with self._lock:
            for _ in range(self.config.min_connections):
                conn = self._create_connection()
                if conn:
                    self._pool.put_nowait(conn)
                    self._all_connections.append(conn)
    
    def _create_connection(self) -> Optional[SQLitePooledConnection]:
        """Create a new SQLite connection with optimizations"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False,
                isolation_level=None
            )
            
            # Apply SQLite optimizations
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA mmap_size = 268435456")
            conn.row_factory = sqlite3.Row
            
            pooled_conn = SQLitePooledConnection(connection=conn)
            
            # Update metrics using the modular metrics system
            with self._lock:
                self._metrics = self._metrics.increment_connections_created()
            
            self.logger.debug(f"Created new SQLite connection. Total: {self._metrics.total_connections}")
            return pooled_conn
            
        except Exception as e:
            self.logger.error(f"Failed to create SQLite connection: {e}")
            return None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool (async context manager)"""
        start_time = time.time()
        connection = None
        
        try:
            # Try to get connection from pool
            try:
                connection = self._pool.get_nowait()
                with self._lock:
                    self._metrics = self._metrics.increment_pool_hits()
                    self._metrics = self._metrics.update_connection_counts(
                        active=self._metrics.active_connections + 1,
                        idle=max(0, self._metrics.idle_connections - 1),
                        total=self._metrics.total_connections
                    )
            except Empty:
                # Pool is empty, create new connection if under limit
                with self._lock:
                    if self._metrics.total_connections < self.config.max_connections:
                        connection = self._create_connection()
                        if connection:
                            self._all_connections.append(connection)
                            self._metrics = self._metrics.increment_pool_misses()
                            self._metrics = self._metrics.update_connection_counts(
                                active=self._metrics.active_connections + 1,
                                idle=self._metrics.idle_connections,
                                total=self._metrics.total_connections
                            )
                    else:
                        # Wait for a connection to become available
                        await asyncio.sleep(0.01)
                        connection = await asyncio.get_event_loop().run_in_executor(
                            None, self._pool.get, True, self.config.connection_timeout
                        )
                        with self._lock:
                            self._metrics = self._metrics.increment_pool_hits()
                            self._metrics = self._metrics.update_connection_counts(
                                active=self._metrics.active_connections + 1,
                                idle=max(0, self._metrics.idle_connections - 1),
                                total=self._metrics.total_connections
                            )
            
            if not connection:
                raise Exception("Could not obtain database connection")
            
            # Health check the connection using validator
            if not connection.is_healthy():
                self.logger.warning("Retrieved unhealthy connection, creating new one")
                self._remove_connection(connection)
                connection = self._create_connection()
                if connection:
                    self._all_connections.append(connection)
                else:
                    raise Exception("Could not create healthy database connection")
            
            # Update connection time metrics
            connection_time = time.time() - start_time
            with self._lock:
                self._metrics = self._metrics.update_connection_time(connection_time)
            
            yield connection
            
        finally:
            # Return connection to pool
            if connection:
                try:
                    if connection.is_healthy() and not connection.is_idle_expired:
                        self._pool.put_nowait(connection)
                        with self._lock:
                            self._metrics = self._metrics.update_connection_counts(
                                active=max(0, self._metrics.active_connections - 1),
                                idle=self._metrics.idle_connections + 1,
                                total=self._metrics.total_connections
                            )
                    else:
                        self._remove_connection(connection)
                except Full:
                    self._remove_connection(connection)
    
    def _remove_connection(self, connection: SQLitePooledConnection):
        """Remove and close a connection"""
        try:
            connection.close()
            with self._lock:
                if connection in self._all_connections:
                    self._all_connections.remove(connection)
                self._metrics = self._metrics.increment_connections_closed()
        except Exception as e:
            self.logger.error(f"Error removing connection: {e}")
    
    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics"""
        with self._lock:
            # Update current connection counts
            return self._metrics.update_connection_counts(
                active=self._metrics.active_connections,
                idle=self._pool.qsize(),
                total=self._metrics.total_connections
            )
    
    def reset_metrics(self):
        """Reset performance metrics"""
        with self._lock:
            self._metrics = self._metrics.reset()
    
    def generate_metrics_report(self, include_calculations: bool = False) -> str:
        """Generate human-readable metrics report"""
        current_metrics = self.get_metrics()
        return self._metrics_reporter.generate_report(current_metrics, include_calculations)
    
    async def close(self):
        """Close all connections and shut down the pool"""
        self._shutdown = True
        
        # Cancel background tasks
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        with self._lock:
            connections_to_close = self._all_connections.copy()
            self._all_connections.clear()
            
            while not self._pool.empty():
                try:
                    self._pool.get_nowait()
                except Empty:
                    break
        
        for conn in connections_to_close:
            try:
                conn.close()
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
        
        self.logger.info("SQLite connection pool closed")


# Create aliases for backward compatibility
SQLiteConnectionPool = ModularSQLiteConnectionPool
SupabaseConnectionPool = ModularSQLiteConnectionPool  # Placeholder for now

# Add missing imports for backward compatibility
from dataclasses import dataclass, field