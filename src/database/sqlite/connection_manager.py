"""
SQLite Connection Manager - Handles database connections and basic operations.
Extracted from SQLiteAdapter for better modularity.
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from pathlib import Path

from ...core.logging import get_logger


class SQLiteConnectionManager:
    """Manages SQLite database connections and basic operations"""
    
    def __init__(self, db_path: str):
        """Initialize connection manager with database path"""
        self.db_path = db_path
        self.logger = get_logger("sqlite_connection_manager")
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database file and enable foreign keys"""
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create database file if it doesn't exist
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()
            
            self.logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite database: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Enable foreign keys for this connection
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        
        return conn
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> None:
        """Execute a query that doesn't return results (INSERT, UPDATE, DELETE)"""
        if params is None:
            params = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
    
    def execute_select(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        if params is None:
            params = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert Row objects to dictionaries
            return [dict(row) for row in rows]
    
    def execute_count(self, query: str, params: Optional[List[Any]] = None) -> int:
        """Execute a COUNT query and return the count value"""
        if params is None:
            params = []
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def close(self):
        """Close connection manager (placeholder for future cleanup)"""
        # Currently no persistent connections to close
        # This method exists for interface compatibility
        pass