"""
SQLite Schema Manager - Handles database table schema creation and management.
Extracted from SQLiteTableManager for better modularity and single responsibility.
"""

from typing import List, Dict, Any

from ...core.logging import get_logger
from .connection_manager import SQLiteConnectionManager


class SQLiteSchemaManager:
    """Manages SQLite database table schemas"""
    
    def __init__(self, connection_manager: SQLiteConnectionManager):
        """Initialize schema manager with connection manager"""
        self.connection_manager = connection_manager
        self.logger = get_logger("sqlite_schema_manager")
    
    def create_users_table(self):
        """Create users table"""
        query = """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_sessions_table(self):
        """Create sessions table"""
        query = """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                messages TEXT DEFAULT '[]',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_authors_table(self):
        """Create authors table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_plots_table(self):
        """Create plots table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_world_building_table(self):
        """Create world_building table with JSON fields"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_characters_table(self):
        """Create characters table"""
        query = """
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                user_id TEXT,
                plot_id TEXT,
                world_id TEXT,
                character_count INTEGER DEFAULT 0,
                world_context_integration TEXT,
                characters TEXT DEFAULT '[]',
                additional_context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plot_id) REFERENCES plots (id),
                FOREIGN KEY (world_id) REFERENCES world_building (id)
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_orchestrator_decisions_table(self):
        """Create orchestrator decisions table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_genres_table(self):
        """Create genres table"""
        query = """
            CREATE TABLE IF NOT EXISTS genres (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_target_audiences_table(self):
        """Create target audiences table"""
        query = """
            CREATE TABLE IF NOT EXISTS target_audiences (
                id TEXT PRIMARY KEY,
                age_group TEXT NOT NULL,
                gender TEXT,
                sexual_orientation TEXT,
                interests TEXT DEFAULT '[]',
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_subgenres_table(self):
        """Create subgenres table"""
        query = """
            CREATE TABLE IF NOT EXISTS subgenres (
                id TEXT PRIMARY KEY,
                genre_id TEXT REFERENCES genres(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(genre_id, name)
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_microgenres_table(self):
        """Create microgenres table"""
        query = """
            CREATE TABLE IF NOT EXISTS microgenres (
                id TEXT PRIMARY KEY,
                subgenre_id TEXT REFERENCES subgenres(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subgenre_id, name)
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_tropes_table(self):
        """Create tropes table"""
        query = """
            CREATE TABLE IF NOT EXISTS tropes (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_tones_table(self):
        """Create tones table"""
        query = """
            CREATE TABLE IF NOT EXISTS tones (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_improvement_sessions_table(self):
        """Create improvement sessions table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_iterations_table(self):
        """Create iterations table"""
        query = """
            CREATE TABLE IF NOT EXISTS iterations (
                id TEXT PRIMARY KEY,
                improvement_session_id TEXT REFERENCES improvement_sessions(id) ON DELETE CASCADE,
                iteration_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_critiques_table(self):
        """Create critiques table"""
        query = """
            CREATE TABLE IF NOT EXISTS critiques (
                id TEXT PRIMARY KEY,
                iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
                critique_json TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_enhancements_table(self):
        """Create enhancements table"""
        query = """
            CREATE TABLE IF NOT EXISTS enhancements (
                id TEXT PRIMARY KEY,
                iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
                enhanced_content TEXT NOT NULL,
                changes_made TEXT NOT NULL,
                rationale TEXT NOT NULL,
                confidence_score INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_scores_table(self):
        """Create scores table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_agent_invocations_table(self):
        """Create agent invocations table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_performance_metrics_table(self):
        """Create performance metrics table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_trace_events_table(self):
        """Create trace events table"""
        query = """
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
        """
        self.connection_manager.execute_query(query)
    
    def create_content_ratings_table(self):
        """Create content ratings table"""
        query = """
            CREATE TABLE IF NOT EXISTS content_ratings (
                id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                rating INTEGER CHECK(rating >= 1 AND rating <= 10),
                feedback TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_lore_documents_table(self):
        """Create lore documents table"""
        query = """
            CREATE TABLE IF NOT EXISTS lore_documents (
                id TEXT PRIMARY KEY,
                cluster_id TEXT,
                content TEXT NOT NULL,
                embedding TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def create_lore_clusters_table(self):
        """Create lore clusters table"""
        query = """
            CREATE TABLE IF NOT EXISTS lore_clusters (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                centroid TEXT,
                document_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.connection_manager.execute_query(query)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        results = self.connection_manager.execute_select(query, [table_name])
        return len(results) > 0
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return self.connection_manager.execute_select(query)
    
    def drop_table(self, table_name: str):
        """Drop a table if it exists"""
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.connection_manager.execute_query(query)
        self.logger.info(f"Dropped table: {table_name}")
    
    def get_all_table_names(self) -> List[str]:
        """Get all table names excluding system tables"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        results = self.connection_manager.execute_select(query)
        return [row['name'] for row in results]