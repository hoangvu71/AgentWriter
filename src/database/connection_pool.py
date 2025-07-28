"""
Database connection pooling implementation for high-performance database operations.
Provides connection pooling for both SQLite and Supabase adapters with health monitoring.

IMPORTANT: This module has been refactored into modular components for better maintainability.
The original API is preserved for backward compatibility.
"""

import sqlite3
import asyncio
import threading
import time
from typing import Dict, Any, List, Optional, Protocol, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty, Full
from supabase import Client as SupabaseClient
from ..core.logging import get_logger

# Import modular components
from .pool_configuration import ConnectionPoolConfig as ModularConnectionPoolConfig
from .pool_metrics import PoolMetrics as ModularPoolMetrics
from .connection_validator import SQLiteConnectionValidator, SupabaseConnectionValidator

# Maintain backward compatibility with original API


# Re-export modular components with original names for backward compatibility
ConnectionPoolConfig = ModularConnectionPoolConfig

@dataclass
class PoolMetrics:
    """Connection pool performance metrics - backward compatibility wrapper"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connections_created: int = 0
    connections_closed: int = 0
    pool_hits: int = 0
    pool_misses: int = 0
    health_check_failures: int = 0
    query_count: int = 0
    avg_connection_time: float = 0.0
    last_reset: float = field(default_factory=time.time)
    
    def reset(self):
        """Reset metrics counters"""
        self.connections_created = 0
        self.connections_closed = 0
        self.pool_hits = 0
        self.pool_misses = 0
        self.health_check_failures = 0
        self.query_count = 0
        self.last_reset = time.time()


class PooledConnection(Protocol):
    """Protocol for pooled database connections"""
    def execute(self, query: str, params: List[Any] = None) -> Any: ...
    def close(self) -> None: ...
    def is_healthy(self) -> bool: ...


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
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except (sqlite3.Error, sqlite3.OperationalError):
            return False
    
    @property
    def is_idle_expired(self) -> bool:
        """Check if connection has been idle too long"""
        return (time.time() - self.last_used) > 300  # 5 minutes


class SQLiteConnectionPool:
    """High-performance SQLite connection pool with health monitoring"""
    
    def __init__(self, db_path: str, config: ConnectionPoolConfig):
        self.db_path = db_path
        self.config = config
        self.logger = get_logger("sqlite_pool")
        
        # Connection pool and management
        self._pool: Queue[SQLitePooledConnection] = Queue(maxsize=config.max_connections)
        self._all_connections: List[SQLitePooledConnection] = []
        self._lock = threading.RLock()
        self._metrics = PoolMetrics()
        
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
            # Create connection with optimizations
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.config.connection_timeout,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode for better performance
            )
            
            # Apply SQLite optimizations
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety and performance
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
            conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
            
            conn.row_factory = sqlite3.Row
            
            pooled_conn = SQLitePooledConnection(connection=conn)
            
            with self._lock:
                self._metrics.connections_created += 1
                self._metrics.total_connections += 1
            
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
                    self._metrics.pool_hits += 1
                    self._metrics.active_connections += 1
                    self._metrics.idle_connections = max(0, self._metrics.idle_connections - 1)
            except Empty:
                # Pool is empty, create new connection if under limit
                with self._lock:
                    if self._metrics.total_connections < self.config.max_connections:
                        connection = self._create_connection()
                        if connection:
                            self._all_connections.append(connection)
                            self._metrics.pool_misses += 1
                            self._metrics.active_connections += 1
                    else:
                        # Wait for a connection to become available
                        await asyncio.sleep(0.01)  # Brief yield
                        connection = await asyncio.get_event_loop().run_in_executor(
                            None, self._pool.get, True, self.config.connection_timeout
                        )
                        with self._lock:
                            self._metrics.pool_hits += 1
                            self._metrics.active_connections += 1
                            self._metrics.idle_connections = max(0, self._metrics.idle_connections - 1)
            
            if not connection:
                raise Exception("Could not obtain database connection")
            
            # Health check the connection
            if not connection.is_healthy():
                self.logger.warning("Retrieved unhealthy connection, creating new one")
                self._remove_connection(connection)
                connection = self._create_connection()
                if connection:
                    self._all_connections.append(connection)
                else:
                    raise Exception("Could not create healthy database connection")
            
            connection_time = time.time() - start_time
            with self._lock:
                self._metrics.avg_connection_time = (
                    (self._metrics.avg_connection_time * self._metrics.query_count + connection_time) /
                    (self._metrics.query_count + 1)
                )
                self._metrics.query_count += 1
            
            yield connection
            
        finally:
            # Return connection to pool
            if connection:
                try:
                    # Only return healthy connections to pool
                    if connection.is_healthy() and not connection.is_idle_expired:
                        self._pool.put_nowait(connection)
                        with self._lock:
                            self._metrics.active_connections = max(0, self._metrics.active_connections - 1)
                            self._metrics.idle_connections += 1
                    else:
                        # Remove expired or unhealthy connections
                        self._remove_connection(connection)
                except Full:
                    # Pool is full, close connection
                    self._remove_connection(connection)
    
    def _remove_connection(self, connection: SQLitePooledConnection):
        """Remove and close a connection"""
        try:
            connection.close()
            with self._lock:
                if connection in self._all_connections:
                    self._all_connections.remove(connection)
                self._metrics.connections_closed += 1
                self._metrics.total_connections = max(0, self._metrics.total_connections - 1)
                self._metrics.active_connections = max(0, self._metrics.active_connections - 1)
        except Exception as e:
            self.logger.error(f"Error removing connection: {e}")
    
    async def start_background_tasks(self):
        """Start background health monitoring and cleanup tasks"""
        if not self._health_monitor_task:
            self._health_monitor_task = asyncio.create_task(self._health_monitor())
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_connections())
    
    async def _health_monitor(self):
        """Background task to monitor connection health"""
        while not self._shutdown:
            try:
                with self._lock:
                    unhealthy_connections = []
                    for conn in self._all_connections:
                        if not conn.is_healthy():
                            unhealthy_connections.append(conn)
                            self._metrics.health_check_failures += 1
                
                # Remove unhealthy connections
                for conn in unhealthy_connections:
                    self._remove_connection(conn)
                
                # Ensure minimum connections
                with self._lock:
                    needed = self.config.min_connections - self._metrics.total_connections
                    
                for _ in range(needed):
                    conn = self._create_connection()
                    if conn:
                        self._all_connections.append(conn)
                        try:
                            self._pool.put_nowait(conn)
                            with self._lock:
                                self._metrics.idle_connections += 1
                        except Full:
                            pass  # Pool is full
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_expired_connections(self):
        """Background task to clean up expired idle connections"""
        while not self._shutdown:
            try:
                with self._lock:
                    expired_connections = []
                    for conn in self._all_connections:
                        if conn.is_idle_expired and self._metrics.total_connections > self.config.min_connections:
                            expired_connections.append(conn)
                
                # Remove expired connections
                for conn in expired_connections:
                    # Try to remove from pool queue (best effort)
                    temp_connections = []
                    while True:
                        try:
                            pool_conn = self._pool.get_nowait()
                            if pool_conn != conn:
                                temp_connections.append(pool_conn)
                            else:
                                with self._lock:
                                    self._metrics.idle_connections = max(0, self._metrics.idle_connections - 1)
                                break
                        except Empty:
                            break
                    
                    # Put back other connections
                    for pool_conn in temp_connections:
                        try:
                            self._pool.put_nowait(pool_conn)
                        except Full:
                            pass
                    
                    self._remove_connection(conn)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(5)
    
    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics"""
        with self._lock:
            # Update current connection counts
            self._metrics.idle_connections = self._pool.qsize()
            return PoolMetrics(
                total_connections=self._metrics.total_connections,
                active_connections=self._metrics.active_connections,
                idle_connections=self._metrics.idle_connections,
                connections_created=self._metrics.connections_created,
                connections_closed=self._metrics.connections_closed,
                pool_hits=self._metrics.pool_hits,
                pool_misses=self._metrics.pool_misses,
                health_check_failures=self._metrics.health_check_failures,
                query_count=self._metrics.query_count,
                avg_connection_time=self._metrics.avg_connection_time,
                last_reset=self._metrics.last_reset
            )
    
    def reset_metrics(self):
        """Reset performance metrics"""
        with self._lock:
            self._metrics.reset()
    
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
            
            # Empty the pool queue
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
        # Supabase clients don't need explicit closing like DB connections
        pass
    
    def is_healthy(self) -> bool:
        """Check if Supabase client is healthy"""
        try:
            # Simple health check - attempt to get auth user
            self.client.auth.get_user()
            return True
        except Exception:
            return False
    
    @property
    def is_idle_expired(self) -> bool:
        """Check if connection has been idle too long"""
        return (time.time() - self.last_used) > 300  # 5 minutes


class SupabaseConnectionPool:
    """Connection pool for Supabase clients with health monitoring"""
    
    def __init__(self, url: str, key: str, config: ConnectionPoolConfig):
        self.url = url
        self.key = key
        self.config = config
        self.logger = get_logger("supabase_pool")
        
        # Connection pool and management
        self._pool: Queue[SupabasePooledConnection] = Queue(maxsize=config.max_connections)
        self._all_connections: List[SupabasePooledConnection] = []
        self._lock = threading.RLock()
        self._metrics = PoolMetrics()
        
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
    
    def _create_connection(self) -> Optional[SupabasePooledConnection]:
        """Create a new Supabase client connection"""
        try:
            from supabase import create_client
            client = create_client(self.url, self.key)
            
            pooled_conn = SupabasePooledConnection(client=client)
            
            with self._lock:
                self._metrics.connections_created += 1
                self._metrics.total_connections += 1
            
            self.logger.debug(f"Created new Supabase connection. Total: {self._metrics.total_connections}")
            return pooled_conn
            
        except Exception as e:
            self.logger.error(f"Failed to create Supabase connection: {e}")
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
                    self._metrics.pool_hits += 1
                    self._metrics.active_connections += 1
                    self._metrics.idle_connections = max(0, self._metrics.idle_connections - 1)
            except Empty:
                # Pool is empty, create new connection if under limit
                with self._lock:
                    if self._metrics.total_connections < self.config.max_connections:
                        connection = self._create_connection()
                        if connection:
                            self._all_connections.append(connection)
                            self._metrics.pool_misses += 1
                            self._metrics.active_connections += 1
                    else:
                        # Wait for a connection to become available
                        await asyncio.sleep(0.01)
                        connection = await asyncio.get_event_loop().run_in_executor(
                            None, self._pool.get, True, self.config.connection_timeout
                        )
                        with self._lock:
                            self._metrics.pool_hits += 1
                            self._metrics.active_connections += 1
                            self._metrics.idle_connections = max(0, self._metrics.idle_connections - 1)
            
            if not connection:
                raise Exception("Could not obtain Supabase connection")
            
            connection_time = time.time() - start_time
            with self._lock:
                self._metrics.avg_connection_time = (
                    (self._metrics.avg_connection_time * self._metrics.query_count + connection_time) /
                    (self._metrics.query_count + 1)
                )
                self._metrics.query_count += 1
            
            yield connection
            
        finally:
            # Return connection to pool
            if connection:
                try:
                    if not connection.is_idle_expired:
                        self._pool.put_nowait(connection)
                        with self._lock:
                            self._metrics.active_connections = max(0, self._metrics.active_connections - 1)
                            self._metrics.idle_connections += 1
                    else:
                        self._remove_connection(connection)
                except Full:
                    self._remove_connection(connection)
    
    def _remove_connection(self, connection: SupabasePooledConnection):
        """Remove and close a connection"""
        try:
            connection.close()
            with self._lock:
                if connection in self._all_connections:
                    self._all_connections.remove(connection)
                self._metrics.connections_closed += 1
                self._metrics.total_connections = max(0, self._metrics.total_connections - 1)
                self._metrics.active_connections = max(0, self._metrics.active_connections - 1)
        except Exception as e:
            self.logger.error(f"Error removing Supabase connection: {e}")
    
    async def start_background_tasks(self):
        """Start background health monitoring and cleanup tasks"""
        if not self._health_monitor_task:
            self._health_monitor_task = asyncio.create_task(self._health_monitor())
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_connections())
    
    async def _health_monitor(self):
        """Background task to monitor connection health"""
        while not self._shutdown:
            try:
                with self._lock:
                    unhealthy_connections = []
                    for conn in self._all_connections:
                        if not conn.is_healthy():
                            unhealthy_connections.append(conn)
                            self._metrics.health_check_failures += 1
                
                # Remove unhealthy connections
                for conn in unhealthy_connections:
                    self._remove_connection(conn)
                
                # Ensure minimum connections
                with self._lock:
                    needed = self.config.min_connections - self._metrics.total_connections
                    
                for _ in range(needed):
                    conn = self._create_connection()
                    if conn:
                        self._all_connections.append(conn)
                        try:
                            self._pool.put_nowait(conn)
                            with self._lock:
                                self._metrics.idle_connections += 1
                        except Full:
                            pass
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in Supabase health monitor: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_expired_connections(self):
        """Background task to clean up expired idle connections"""
        while not self._shutdown:
            try:
                with self._lock:
                    expired_connections = []
                    for conn in self._all_connections:
                        if conn.is_idle_expired and self._metrics.total_connections > self.config.min_connections:
                            expired_connections.append(conn)
                
                for conn in expired_connections:
                    self._remove_connection(conn)
                
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in Supabase cleanup task: {e}")
                await asyncio.sleep(5)
    
    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics"""
        with self._lock:
            self._metrics.idle_connections = self._pool.qsize()
            return PoolMetrics(
                total_connections=self._metrics.total_connections,
                active_connections=self._metrics.active_connections,
                idle_connections=self._metrics.idle_connections,
                connections_created=self._metrics.connections_created,
                connections_closed=self._metrics.connections_closed,
                pool_hits=self._metrics.pool_hits,
                pool_misses=self._metrics.pool_misses,
                health_check_failures=self._metrics.health_check_failures,
                query_count=self._metrics.query_count,
                avg_connection_time=self._metrics.avg_connection_time,
                last_reset=self._metrics.last_reset
            )
    
    def reset_metrics(self):
        """Reset performance metrics"""
        with self._lock:
            self._metrics.reset()
    
    async def close(self):
        """Close all connections and shut down the pool"""
        self._shutdown = True
        
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
                self.logger.error(f"Error closing Supabase connection: {e}")
        
        self.logger.info("Supabase connection pool closed")