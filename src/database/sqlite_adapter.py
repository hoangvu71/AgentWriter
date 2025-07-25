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
from .schema_synchronizer import SchemaSynchronizer


class SQLiteAdapter:
    """SQLite database adapter for offline storage"""
    
    def __init__(self, db_path: str = "local_database.db"):
        self.db_path = db_path
        self.logger = get_logger("sqlite_adapter")
        self.synchronizer = SchemaSynchronizer(db_path)
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
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
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
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                author_name TEXT NOT NULL,
                pen_name TEXT,
                biography TEXT,
                writing_style TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Plots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plots (
                id TEXT PRIMARY KEY,
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
        
        # World building table (updated to match Supabase schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS world_building (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                plot_id TEXT,
                world_name TEXT NOT NULL,
                world_type TEXT NOT NULL DEFAULT 'fantasy',
                overview TEXT NOT NULL DEFAULT '',
                geography TEXT NOT NULL DEFAULT '{}',
                political_landscape TEXT NOT NULL DEFAULT '{}',
                cultural_systems TEXT NOT NULL DEFAULT '{}',
                economic_framework TEXT NOT NULL DEFAULT '{}',
                historical_timeline TEXT NOT NULL DEFAULT '{}',
                power_systems TEXT NOT NULL DEFAULT '{}',
                languages_and_communication TEXT NOT NULL DEFAULT '{}',
                religious_and_belief_systems TEXT NOT NULL DEFAULT '{}',
                unique_elements TEXT NOT NULL DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plot_id) REFERENCES plots (id)
            )
        """)
        
        # Characters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                plot_id TEXT,
                world_id TEXT,
                character_count INTEGER DEFAULT 0,
                world_context_integration TEXT,
                characters TEXT DEFAULT '[]',
                relationship_networks TEXT DEFAULT '{}',
                character_dynamics TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plot_id) REFERENCES plots (id),
                FOREIGN KEY (world_id) REFERENCES world_building (id)
            )
        """)
        
        # Orchestrator decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orchestrator_decisions (
                id TEXT PRIMARY KEY,
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
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Target audiences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS target_audiences (
                id TEXT PRIMARY KEY,
                age_group TEXT NOT NULL,
                gender TEXT,
                sexual_orientation TEXT,
                interests TEXT DEFAULT '[]',
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Genre hierarchy tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subgenres (
                id TEXT PRIMARY KEY,
                genre_id TEXT REFERENCES genres(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(genre_id, name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS microgenres (
                id TEXT PRIMARY KEY,
                subgenre_id TEXT REFERENCES subgenres(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subgenre_id, name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tropes (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tones (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Iterative improvement system tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvement_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                original_content TEXT NOT NULL,
                content_type TEXT NOT NULL,
                target_score REAL DEFAULT 9.5,
                max_iterations INTEGER DEFAULT 4,
                status TEXT DEFAULT 'in_progress',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                completion_reason TEXT,
                final_content TEXT,
                final_score REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iterations (
                id TEXT PRIMARY KEY,
                improvement_session_id TEXT REFERENCES improvement_sessions(id) ON DELETE CASCADE,
                iteration_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS critiques (
                id TEXT PRIMARY KEY,
                iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
                critique_json TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhancements (
                id TEXT PRIMARY KEY,
                iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
                enhanced_content TEXT NOT NULL,
                changes_made TEXT NOT NULL,
                rationale TEXT NOT NULL,
                confidence_score INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id TEXT PRIMARY KEY,
                iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
                overall_score REAL NOT NULL,
                category_scores TEXT NOT NULL,
                score_rationale TEXT NOT NULL,
                improvement_trajectory TEXT NOT NULL,
                recommendations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Observability and performance tracking tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_invocations (
                id TEXT PRIMARY KEY,
                invocation_id TEXT UNIQUE NOT NULL,
                agent_name TEXT NOT NULL,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                request_content TEXT NOT NULL,
                request_context TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_ms REAL,
                llm_model TEXT,
                final_prompt TEXT,
                raw_response TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                tool_calls TEXT DEFAULT '[]',
                tool_results TEXT DEFAULT '[]',
                latency_ms REAL,
                cost_estimate REAL,
                success BOOLEAN DEFAULT 0,
                error_message TEXT,
                response_content TEXT,
                parsed_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                tags TEXT DEFAULT '{}',
                agent_name TEXT,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trace_events (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                span_id TEXT NOT NULL,
                parent_span_id TEXT,
                span_name TEXT NOT NULL,
                span_kind TEXT DEFAULT 'INTERNAL',
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_ns INTEGER,
                attributes TEXT DEFAULT '{}',
                events TEXT DEFAULT '[]',
                status_code TEXT DEFAULT 'OK',
                status_message TEXT,
                resource_attributes TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        self._create_indexes(cursor)
    
    def _create_indexes(self, cursor):
        """Create performance indexes for all tables"""
        # Core table indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_authors_session_id ON authors(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_authors_user_id ON authors(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plots_session_id ON plots(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plots_user_id ON plots(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plots_author_id ON plots(author_id)")
        
        # World building indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_world_building_user_id ON world_building(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_world_building_session_id ON world_building(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_world_building_plot_id ON world_building(plot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_world_building_world_type ON world_building(world_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_world_building_created_at ON world_building(created_at)")
        
        # Characters indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_session_id ON characters(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_world_id ON characters(world_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_plot_id ON characters(plot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_created_at ON characters(created_at)")
        
        # Genre hierarchy indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_genres_name ON genres(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subgenres_genre_id ON subgenres(genre_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subgenres_name ON subgenres(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_microgenres_subgenre_id ON microgenres(subgenre_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_microgenres_name ON microgenres(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tropes_name ON tropes(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tropes_category ON tropes(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tones_name ON tones(name)")
        
        # Target audience indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_audiences_age_group ON target_audiences(age_group)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_audiences_gender ON target_audiences(gender)")
        
        # Iterative improvement system indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_improvement_sessions_user_id ON improvement_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_improvement_sessions_session_id ON improvement_sessions(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_improvement_sessions_status ON improvement_sessions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iterations_improvement_session_id ON iterations(improvement_session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_critiques_iteration_id ON critiques(iteration_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhancements_iteration_id ON enhancements(iteration_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_iteration_id ON scores(iteration_id)")
        
        # Observability indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_invocations_agent_name ON agent_invocations(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_invocations_user_id ON agent_invocations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_invocations_session_id ON agent_invocations(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_invocations_start_time ON agent_invocations(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_invocations_success ON agent_invocations(success)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent ON performance_metrics(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_events_trace_id ON trace_events(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_events_span_id ON trace_events(span_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_events_parent_span_id ON trace_events(parent_span_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_events_span_name ON trace_events(span_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trace_events_start_time ON trace_events(start_time)")
    
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
        if isinstance(data, (dict, list)):
            return data  # Already deserialized
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.warning(f"Failed to deserialize JSON data: {e}")
            return data  # Return original data if deserialization fails
    
    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert a record into the specified table and return ID"""
        try:
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            # Add timestamp if not provided and table has created_at column
            table_schemas = {
                'users': True, 'authors': True, 'plots': True, 'world_building': True, 
                'characters': True, 'orchestrator_decisions': True, 'genres': True, 
                'target_audiences': True, 'sessions': False,  # sessions uses start_time not created_at
                'subgenres': True, 'microgenres': True, 'tropes': True, 'tones': True,
                'improvement_sessions': True, 'iterations': True, 'critiques': True,
                'enhancements': True, 'scores': True, 'agent_invocations': True,
                'performance_metrics': False, 'trace_events': True  # performance_metrics uses timestamp
            }
            
            if table in table_schemas and table_schemas[table] and 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            elif table == 'sessions' and 'start_time' not in data:
                data['start_time'] = datetime.utcnow().isoformat()
            elif table == 'performance_metrics' and 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow().isoformat()
            
            # Serialize JSON fields
            json_fields = [
                'messages', 'agents_selected', 'characters', 'relationship_networks', 'character_dynamics',
                'geography', 'political_landscape', 'cultural_systems', 'economic_framework', 
                'historical_timeline', 'power_systems', 'languages_and_communication',
                'religious_and_belief_systems', 'unique_elements', 'interests', 'critique_json',
                'changes_made', 'category_scores', 'request_context', 'tool_calls', 'tool_results',
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes'
            ]
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
            
            # Return just the ID to match Supabase interface
            return data['id']
            
        except Exception as e:
            self.logger.error(f"Error inserting into {table}: {e}")
            raise
    
    def _execute_insert(self, query: str, values: List[Any], table: str, record_id: str) -> Dict[str, Any]:
        """Execute INSERT query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Enable foreign keys for this connection
            cursor.execute("PRAGMA foreign_keys = ON")
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
            
            # Execute using connection pool
            results = await self._execute_select(query, params)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error selecting from {table}: {e}")
            raise
    
    def _execute_select(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        """Execute SELECT query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Enable foreign keys for this connection
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                record = self._dict_from_row(row)
                # Deserialize JSON fields
                json_fields = [
                'messages', 'agents_selected', 'characters', 'relationship_networks', 'character_dynamics',
                'geography', 'political_landscape', 'cultural_systems', 'economic_framework', 
                'historical_timeline', 'power_systems', 'languages_and_communication',
                'religious_and_belief_systems', 'unique_elements', 'interests', 'critique_json',
                'changes_made', 'category_scores', 'request_context', 'tool_calls', 'tool_results',
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes'
            ]
                for field in json_fields:
                    if field in record and record[field]:
                        record[field] = self._deserialize_json(record[field])
                results.append(record)
            
            return results
    
    async def get_by_id(self, table_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        try:
            filters = {"id": entity_id}
            results = await self.select(table_name, filters, limit=1)
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Error getting {table_name} by ID {entity_id}: {e}")
            raise
    
    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record in the specified table"""
        try:
            # Serialize JSON fields
            json_fields = [
                'messages', 'agents_selected', 'characters', 'relationship_networks', 'character_dynamics',
                'geography', 'political_landscape', 'cultural_systems', 'economic_framework', 
                'historical_timeline', 'power_systems', 'languages_and_communication',
                'religious_and_belief_systems', 'unique_elements', 'interests', 'critique_json',
                'changes_made', 'category_scores', 'request_context', 'tool_calls', 'tool_results',
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes'
            ]
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
            
            # Return boolean to match Supabase interface
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Error updating {table}: {e}")
            raise
    
    def _execute_update(self, query: str, values: List[Any], table: str, record_id: str) -> Dict[str, Any]:
        """Execute UPDATE query synchronously"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Enable foreign keys for this connection
            cursor.execute("PRAGMA foreign_keys = ON")
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
            # Enable foreign keys for this connection
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    async def get_all(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all entities with pagination"""
        try:
            query = f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params = [limit, offset]
            
            # Execute using connection pool
            results = await self._execute_select(query, params)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting all {table_name}: {e}")
            raise
    
    async def search(self, table_name: str, criteria: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Search entities by criteria"""
        try:
            return await self.select(table_name, filters=criteria, limit=limit)
        except Exception as e:
            self.logger.error(f"Error searching {table_name}: {e}")
            raise
    
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
            # Enable foreign keys for this connection
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
    
    # Additional methods for interface compatibility with Supabase adapter
    async def save_plot(self, plot_data: Dict[str, Any]) -> str:
        """Save plot data and return ID (interface compatibility)"""
        return await self.insert("plots", plot_data)
    
    async def save_author(self, author_data: Dict[str, Any]) -> str:
        """Save author data and return ID (interface compatibility)"""
        return await self.insert("authors", author_data)
    
    async def get_plot(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve plot by ID (interface compatibility)"""
        return await self.get_by_id("plots", plot_id)
    
    async def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve author by ID (interface compatibility)"""
        return await self.get_by_id("authors", author_id)
    
    async def get_plots_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get plots for a user"""
        return await self.select("plots", filters={"user_id": user_id}, limit=limit, order_by="created_at", desc=True)
    
    async def get_authors_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get authors for a user"""
        return await self.select("authors", filters={"user_id": user_id}, limit=limit, order_by="created_at", desc=True)
    
    async def get_plot_with_author(self, plot_id: str) -> Dict[str, Any]:
        """Get plot with associated author"""
        try:
            plot = await self.get_by_id("plots", plot_id)
            if not plot:
                return {}
            
            # Get associated author if exists
            if plot.get("author_id"):
                author = await self.get_by_id("authors", plot["author_id"])
                if author:
                    plot["author"] = author
            
            return plot
        except Exception as e:
            self.logger.error(f"Error getting plot with author: {e}")
            return {}
    
    async def search_content(self, query: str, content_type: str, user_id: str) -> List[Dict[str, Any]]:
        """Search for content (basic text search implementation)"""
        try:
            if content_type.lower() == "plot":
                # Search plots by title or summary
                plots = await self.select("plots", filters={"user_id": user_id}, limit=50)
                return [
                    plot for plot in plots 
                    if query.lower() in (plot.get("title", "") + " " + plot.get("plot_summary", "")).lower()
                ]
            elif content_type.lower() == "author":
                # Search authors by name
                authors = await self.select("authors", filters={"user_id": user_id}, limit=50)
                return [
                    author for author in authors
                    if query.lower() in (author.get("author_name", "") + " " + author.get("pen_name", "")).lower()
                ]
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error searching content: {e}")
            return []
    
    async def get_pool_metrics(self) -> Dict[str, Any]:
        """Get connection pool performance metrics"""
        if hasattr(self, 'connection_pool'):
            metrics = self.connection_pool.get_metrics()
            return {
                "total_connections": metrics.total_connections,
                "active_connections": metrics.active_connections,
                "idle_connections": metrics.idle_connections,
                "pool_hits": metrics.pool_hits,
                "pool_misses": metrics.pool_misses,
                "hit_rate": metrics.pool_hits / (metrics.pool_hits + metrics.pool_misses) if (metrics.pool_hits + metrics.pool_misses) > 0 else 0,
                "health_check_failures": metrics.health_check_failures,
                "avg_connection_time": metrics.avg_connection_time,
                "query_count": metrics.query_count
            }
        return {}
    
    async def reset_pool_metrics(self):
        """Reset connection pool metrics"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.reset_metrics()
    
    async def batch_insert(self, table: str, records: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple records in a single transaction for better performance"""
        if not records:
            return []
        
        try:
            # Generate IDs for records that don't have them
            for record in records:
                if 'id' not in record:
                    record['id'] = str(uuid.uuid4())
            
            # Add timestamps for records that need them
            table_schemas = {
                'users': True, 'authors': True, 'plots': True, 'world_building': True, 
                'characters': True, 'orchestrator_decisions': True, 'genres': True, 
                'target_audiences': True, 'sessions': False,
                'subgenres': True, 'microgenres': True, 'tropes': True, 'tones': True,
                'improvement_sessions': True, 'iterations': True, 'critiques': True,
                'enhancements': True, 'scores': True, 'agent_invocations': True,
                'performance_metrics': False, 'trace_events': True
            }
            
            for record in records:
                if table in table_schemas and table_schemas[table] and 'created_at' not in record:
                    record['created_at'] = datetime.utcnow().isoformat()
                elif table == 'sessions' and 'start_time' not in record:
                    record['start_time'] = datetime.utcnow().isoformat()
                elif table == 'performance_metrics' and 'timestamp' not in record:
                    record['timestamp'] = datetime.utcnow().isoformat()
            
            # Serialize JSON fields for all records
            json_fields = [
                'messages', 'agents_selected', 'characters', 'relationship_networks', 'character_dynamics',
                'geography', 'political_landscape', 'cultural_systems', 'economic_framework', 
                'historical_timeline', 'power_systems', 'languages_and_communication',
                'religious_and_belief_systems', 'unique_elements', 'interests', 'critique_json',
                'changes_made', 'category_scores', 'request_context', 'tool_calls', 'tool_results',
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes'
            ]
            
            for record in records:
                for field in json_fields:
                    if field in record:
                        record[field] = self._serialize_json(record[field])
            
            # Use connection pool for batch insert
            async with self.connection_pool.get_connection() as conn:
                try:
                    conn.connection.execute("BEGIN TRANSACTION")
                    
                    # Prepare the INSERT statement
                    columns = list(records[0].keys())
                    placeholders = ['?' for _ in columns]
                    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    
                    # Execute batch insert
                    for record in records:
                        values = [record[col] for col in columns]
                        conn.execute(query, values)
                    
                    conn.connection.commit()
                    
                    # Return list of IDs
                    return [record['id'] for record in records]
                    
                except Exception as e:
                    conn.connection.rollback()
                    raise e
                    
        except Exception as e:
            self.logger.error(f"Error in batch insert to {table}: {e}")
            raise
    
    async def batch_select_by_ids(self, table: str, ids: List[str]) -> List[Dict[str, Any]]:
        """Select multiple records by IDs in a single query"""
        if not ids:
            return []
        
        try:
            # Build query with IN clause
            placeholders = ','.join(['?' for _ in ids])
            query = f"SELECT * FROM {table} WHERE id IN ({placeholders})"
            
            return await self._execute_select(query, ids)
            
        except Exception as e:
            self.logger.error(f"Error in batch select from {table}: {e}")
            raise
    
    async def batch_update(self, table: str, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records in a single transaction"""
        if not updates:
            return 0
        
        try:
            # Serialize JSON fields for all records
            json_fields = [
                'messages', 'agents_selected', 'characters', 'relationship_networks', 'character_dynamics',
                'geography', 'political_landscape', 'cultural_systems', 'economic_framework', 
                'historical_timeline', 'power_systems', 'languages_and_communication',
                'religious_and_belief_systems', 'unique_elements', 'interests', 'critique_json',
                'changes_made', 'category_scores', 'request_context', 'tool_calls', 'tool_results',
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes'
            ]
            
            for update in updates:
                data = update.get('data', {})
                for field in json_fields:
                    if field in data:
                        data[field] = self._serialize_json(data[field])
            
            updated_count = 0
            
            async with self.connection_pool.get_connection() as conn:
                try:
                    conn.connection.execute("BEGIN TRANSACTION")
                    
                    for update in updates:
                        record_id = update['id']
                        data = update['data']
                        
                        # Build UPDATE query
                        set_clauses = [f"{key} = ?" for key in data.keys()]
                        query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
                        values = list(data.values()) + [record_id]
                        
                        cursor = conn.execute(query, values)
                        if cursor.rowcount > 0:
                            updated_count += 1
                    
                    conn.connection.commit()
                    return updated_count
                    
                except Exception as e:
                    conn.connection.rollback()
                    raise e
                    
        except Exception as e:
            self.logger.error(f"Error in batch update to {table}: {e}")
            raise
    
    async def close(self):
        """Close the database adapter and connection pool"""
        if hasattr(self, 'connection_pool'):
            await self.connection_pool.close()
            self.logger.info("SQLite adapter closed")