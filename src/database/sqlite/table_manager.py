"""
SQLite Table Manager - Handles database schema creation and management.
Extracted from SQLiteAdapter for better modularity.
Refactored to use specialized managers while maintaining API compatibility.
"""

from typing import List, Dict, Any

from ...core.logging import get_logger
from .connection_manager import SQLiteConnectionManager
from .schema_manager import SQLiteSchemaManager
from .index_manager import SQLiteIndexManager
from .constraint_manager import SQLiteConstraintManager


class SQLiteTableManager:
    """Manages SQLite database tables and schema using specialized managers"""
    
    def __init__(self, connection_manager: SQLiteConnectionManager):
        """Initialize table manager with connection manager and specialized managers"""
        self.connection_manager = connection_manager
        self.logger = get_logger("sqlite_table_manager")
        
        # Initialize specialized managers
        self.schema_manager = SQLiteSchemaManager(connection_manager)
        self.index_manager = SQLiteIndexManager(connection_manager)
        self.constraint_manager = SQLiteConstraintManager(connection_manager)
    
    def create_all_tables(self):
        """Create all required tables in the correct order"""
        self.logger.info("Creating all database tables")
        
        # Create tables in dependency order
        self.create_users_table()
        self.create_sessions_table()
        self.create_authors_table()
        self.create_plots_table()
        self.create_world_building_table()
        self.create_characters_table()
        
        # Create supporting tables
        self.create_orchestrator_decisions_table()
        self.create_genres_table()
        self.create_target_audiences_table()
        self.create_subgenres_table()
        self.create_microgenres_table()
        self.create_tropes_table()
        self.create_tones_table()
        
        # Create iterative improvement tables
        self.create_improvement_sessions_table()
        self.create_iterations_table()
        self.create_critiques_table()
        self.create_enhancements_table()
        self.create_scores_table()
        
        # Create observability tables
        self.create_agent_invocations_table()
        self.create_performance_metrics_table()
        self.create_trace_events_table()
        
        # Create additional tables for ratings and lore
        self.create_content_ratings_table()
        self.create_lore_documents_table()
        self.create_lore_clusters_table()
        
        # Create indexes for performance
        self.create_indexes()
        
        self.logger.info("All database tables created successfully")
    
    # Table creation methods - delegate to schema manager
    def create_users_table(self):
        """Create users table"""
        return self.schema_manager.create_users_table()
    
    def create_sessions_table(self):
        """Create sessions table"""
        return self.schema_manager.create_sessions_table()
    
    def create_authors_table(self):
        """Create authors table"""
        return self.schema_manager.create_authors_table()
    
    def create_plots_table(self):
        """Create plots table"""
        return self.schema_manager.create_plots_table()
    
    def create_world_building_table(self):
        """Create world_building table with JSON fields"""
        return self.schema_manager.create_world_building_table()
    
    def create_characters_table(self):
        """Create characters table"""
        return self.schema_manager.create_characters_table()
    
    def create_orchestrator_decisions_table(self):
        """Create orchestrator decisions table"""
        return self.schema_manager.create_orchestrator_decisions_table()
    
    def create_genres_table(self):
        """Create genres table"""
        return self.schema_manager.create_genres_table()
    
    def create_target_audiences_table(self):
        """Create target audiences table"""
        return self.schema_manager.create_target_audiences_table()
    
    def create_subgenres_table(self):
        """Create subgenres table"""
        return self.schema_manager.create_subgenres_table()
    
    def create_microgenres_table(self):
        """Create microgenres table"""
        return self.schema_manager.create_microgenres_table()
    
    def create_tropes_table(self):
        """Create tropes table"""
        return self.schema_manager.create_tropes_table()
    
    def create_tones_table(self):
        """Create tones table"""
        return self.schema_manager.create_tones_table()
    
    def create_improvement_sessions_table(self):
        """Create improvement sessions table"""
        return self.schema_manager.create_improvement_sessions_table()
    
    def create_iterations_table(self):
        """Create iterations table"""
        return self.schema_manager.create_iterations_table()
    
    def create_critiques_table(self):
        """Create critiques table"""
        return self.schema_manager.create_critiques_table()
    
    def create_enhancements_table(self):
        """Create enhancements table"""
        return self.schema_manager.create_enhancements_table()
    
    def create_scores_table(self):
        """Create scores table"""
        return self.schema_manager.create_scores_table()
    
    def create_agent_invocations_table(self):
        """Create agent invocations table"""
        return self.schema_manager.create_agent_invocations_table()
    
    def create_performance_metrics_table(self):
        """Create performance metrics table"""
        return self.schema_manager.create_performance_metrics_table()
    
    def create_trace_events_table(self):
        """Create trace events table"""
        return self.schema_manager.create_trace_events_table()
    
    def create_content_ratings_table(self):
        """Create content ratings table"""
        return self.schema_manager.create_content_ratings_table()
    
    def create_lore_documents_table(self):
        """Create lore documents table"""
        return self.schema_manager.create_lore_documents_table()
    
    def create_lore_clusters_table(self):
        """Create lore clusters table"""
        return self.schema_manager.create_lore_clusters_table()
    
    # Index management methods - delegate to index manager
    def create_indexes(self):
        """Create performance indexes for all tables"""
        return self.index_manager.create_all_indexes()
    
    # Schema introspection methods - delegate to schema manager
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        return self.schema_manager.table_exists(table_name)
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        return self.schema_manager.get_table_schema(table_name)
    
    def drop_table(self, table_name: str):
        """Drop a table if it exists"""
        return self.schema_manager.drop_table(table_name)
    
    def recreate_all_tables(self):
        """Drop and recreate all tables (DANGEROUS - loses all data)"""
        self.logger.warning("Recreating all tables - this will delete all data!")
        
        # Use a different approach: drop all tables with a single SQL command
        try:
            # First, disable foreign key constraints
            self.constraint_manager.disable_foreign_key_constraints()
            
            # Get all table names
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            tables = self.connection_manager.execute_select(query)
            
            # Drop each table individually but more carefully
            for table in tables:
                table_name = table['name']
                try:
                    # Use explicit DROP TABLE IF EXISTS
                    drop_query = f"DROP TABLE IF EXISTS `{table_name}`"
                    self.connection_manager.execute_query(drop_query)
                    self.logger.info(f"Dropped table: {table_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to drop table {table_name}: {e}")
            
            # Recreate all tables
            self.create_all_tables()
            
        finally:
            # Re-enable foreign key constraints
            self.constraint_manager.enable_foreign_key_constraints()