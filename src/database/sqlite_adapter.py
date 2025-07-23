"""
SQLite adapter for offline database storage.
Provides same interface as SupabaseAdapter for seamless switching.
"""

import sqlite3
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import uuid
from ..core.logging import get_logger


class SQLiteAdapter:
    """SQLite database adapter for offline storage"""
    
    def __init__(self, db_path: str = "local_database.db"):
        self.db_path = db_path
        self.logger = get_logger("sqlite_adapter")
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Create tables matching Supabase schema
                self._create_tables(cursor)
                conn.commit()
                
            self.logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite database: {e}")
            raise
    
    def _create_tables(self, cursor):
        """Create all required tables"""
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                messages TEXT DEFAULT '[]',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Authors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                author_name TEXT NOT NULL,
                pen_name TEXT,
                biography TEXT,
                writing_style TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Plots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plots (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                session_id TEXT,
                user_id TEXT,
                author_id TEXT,
                title TEXT NOT NULL,
                plot_summary TEXT NOT NULL,
                genre TEXT,
                subgenre TEXT,
                microgenre TEXT,
                trope TEXT,
                tone TEXT,
                target_audience TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (author_id) REFERENCES authors (id)
            )
        """)
        
        # World building table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS world_building (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                plot_id TEXT,
                world_name TEXT NOT NULL,
                geography TEXT DEFAULT '{}',
                politics TEXT DEFAULT '{}',
                culture TEXT DEFAULT '{}',
                magic_system TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plot_id) REFERENCES plots (id)
            )
        """)
        
        # Characters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                plot_id TEXT,
                world_building_id TEXT,
                character_populations TEXT DEFAULT '{}',
                relationships TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plot_id) REFERENCES plots (id),
                FOREIGN KEY (world_building_id) REFERENCES world_building (id)
            )
        """)
        
        # Orchestrator decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orchestrator_decisions (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                session_id TEXT,
                user_id TEXT,
                request_content TEXT,
                routing_decision TEXT,
                agents_selected TEXT DEFAULT '[]',
                reasoning TEXT,
                confidence_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Genres table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Target audiences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS target_audiences (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                age_group TEXT NOT NULL,
                gender TEXT NOT NULL,
                sexual_orientation TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _dict_from_row(self, row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary"""
        if row is None:
            return None
        return dict(zip(row.keys(), row))
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string"""
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return str(data)
    
    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string to data"""
        if not data:
            return None
        try:
            return json.loads(data)
        except:
            return data
    
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into the specified table"""
        try:
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            # Add timestamp if not provided
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            
            # Serialize JSON fields
            json_fields = ['messages', 'agents_selected', 'geography', 'politics', 
                          'culture', 'magic_system', 'character_populations', 'relationships']
            for field in json_fields:
                if field in data:
                    data[field] = self._serialize_json(data[field])
            
            # Build INSERT query
            columns = list(data.keys())
            placeholders = ['?' for _ in columns]
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._execute_insert, query, list(data.values()), table, data['id'])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error inserting into {table}: {e}")
            raise
    
    def _execute_insert(self, query: str, values: List[Any], table: str, record_id: str) -> Dict[str, Any]:
        """Execute INSERT query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            
            # Fetch the inserted record
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return self._dict_from_row(row)
    
    async def select(self, table: str, filters: Optional[Dict[str, Any]] = None, 
                    order_by: Optional[str] = None, desc: bool = False, 
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Select records from the specified table"""
        try:
            query = f"SELECT * FROM {table}"
            params = []
            
            # Add WHERE clause
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                query += f" WHERE {' AND '.join(conditions)}"
            
            # Add ORDER BY clause
            if order_by:
                direction = "DESC" if desc else "ASC"
                query += f" ORDER BY {order_by} {direction}"
            
            # Add LIMIT clause
            if limit:
                query += f" LIMIT {limit}"
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self._execute_select, query, params)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error selecting from {table}: {e}")
            raise
    
    def _execute_select(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        """Execute SELECT query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                record = self._dict_from_row(row)
                # Deserialize JSON fields
                json_fields = ['messages', 'agents_selected', 'geography', 'politics', 
                              'culture', 'magic_system', 'character_populations', 'relationships']
                for field in json_fields:
                    if field in record and record[field]:
                        record[field] = self._deserialize_json(record[field])
                results.append(record)
            
            return results
    
    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record in the specified table"""
        try:
            # Serialize JSON fields
            json_fields = ['messages', 'agents_selected', 'geography', 'politics', 
                          'culture', 'magic_system', 'character_populations', 'relationships']
            for field in json_fields:
                if field in data:
                    data[field] = self._serialize_json(data[field])
            
            # Build UPDATE query
            set_clauses = [f"{key} = ?" for key in data.keys()]
            query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
            values = list(data.values()) + [record_id]
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._execute_update, query, values, table, record_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating {table}: {e}")
            raise
    
    def _execute_update(self, query: str, values: List[Any], table: str, record_id: str) -> Dict[str, Any]:
        """Execute UPDATE query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            
            # Fetch the updated record
            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return self._dict_from_row(row)
    
    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records in the specified table"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table}"
            params = []
            
            # Add WHERE clause
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                query += f" WHERE {' AND '.join(conditions)}"
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(None, self._execute_count, query, params)
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting {table}: {e}")
            raise
    
    def _execute_count(self, query: str, params: List[Any]) -> int:
        """Execute COUNT query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    async def delete(self, table: str, record_id: str) -> bool:
        """Delete a record from the specified table"""
        try:
            query = f"DELETE FROM {table} WHERE id = ?"
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._execute_delete, query, [record_id])
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting from {table}: {e}")
            raise
    
    def _execute_delete(self, query: str, params: List[Any]) -> bool:
        """Execute DELETE query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0