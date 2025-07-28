"""
SQLite Index Manager - Handles database index creation, management, and optimization.
Extracted from SQLiteTableManager for better modularity and single responsibility.
"""

from typing import List, Dict, Any, Optional

from ...core.logging import get_logger
from .connection_manager import SQLiteConnectionManager


class SQLiteIndexManager:
    """Manages SQLite database indexes"""
    
    def __init__(self, connection_manager: SQLiteConnectionManager):
        """Initialize index manager with connection manager"""
        self.connection_manager = connection_manager
        self.logger = get_logger("sqlite_index_manager")
    
    def create_index(self, index_name: str, table_name: str, columns: List[str], 
                    unique: bool = False, where_clause: Optional[str] = None):
        """Create an index on specified columns"""
        unique_clause = "UNIQUE " if unique else ""
        columns_str = ", ".join(columns)
        where_clause_str = f" WHERE {where_clause}" if where_clause else ""
        
        query = f"""
            CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} 
            ON {table_name}({columns_str}){where_clause_str}
        """
        
        self.connection_manager.execute_query(query)
        self.logger.info(f"Created index: {index_name} on {table_name}({columns_str})")
    
    def create_all_core_indexes(self):
        """Create core performance indexes for main tables"""
        self.logger.info("Creating core performance indexes")
        
        # Core table indexes
        core_indexes = [
            ("idx_sessions_user_id", "sessions", ["user_id"]),
            ("idx_plots_user_id", "plots", ["user_id"]),
            ("idx_plots_session_id", "plots", ["session_id"]),
        ]
        
        for index_name, table_name, columns in core_indexes:
            try:
                self.create_index(index_name, table_name, columns)
            except Exception as e:
                self.logger.warning(f"Failed to create index {index_name}: {e}")
        
        self.logger.info("Core indexes created successfully")
    
    def create_all_indexes(self):
        """Create all performance indexes for all tables"""
        self.logger.info("Creating all performance indexes")
        
        # All table indexes
        all_indexes = [
            ("idx_sessions_user_id", "sessions", ["user_id"]),
            ("idx_authors_session_id", "authors", ["session_id"]),
            ("idx_authors_user_id", "authors", ["user_id"]),
            ("idx_plots_session_id", "plots", ["session_id"]),
            ("idx_plots_user_id", "plots", ["user_id"]),
            ("idx_plots_author_id", "plots", ["author_id"]),
            
            # World building indexes
            ("idx_world_building_user_id", "world_building", ["user_id"]),
            ("idx_world_building_session_id", "world_building", ["session_id"]),
            ("idx_world_building_plot_id", "world_building", ["plot_id"]),
            
            # Characters indexes
            ("idx_characters_user_id", "characters", ["user_id"]),
            ("idx_characters_session_id", "characters", ["session_id"]),
            ("idx_characters_plot_id", "characters", ["plot_id"]),
            
            # Content ratings indexes
            ("idx_content_ratings_content_id", "content_ratings", ["content_id"]),
            ("idx_content_ratings_content_type", "content_ratings", ["content_type"]),
            
            # Lore indexes
            ("idx_lore_documents_cluster_id", "lore_documents", ["cluster_id"]),
            
            # Agent invocations indexes
            ("idx_agent_invocations_agent_name", "agent_invocations", ["agent_name"]),
            ("idx_agent_invocations_user_id", "agent_invocations", ["user_id"]),
        ]
        
        for index_name, table_name, columns in all_indexes:
            try:
                self.create_index(index_name, table_name, columns)
            except Exception as e:
                self.logger.warning(f"Failed to create index {index_name}: {e}")
        
        self.logger.info("All indexes created successfully")
    
    def drop_index(self, index_name: str):
        """Drop an index if it exists"""
        query = f"DROP INDEX IF EXISTS {index_name}"
        self.connection_manager.execute_query(query)
        self.logger.info(f"Dropped index: {index_name}")
    
    def index_exists(self, index_name: str) -> bool:
        """Check if an index exists"""
        query = "SELECT name FROM sqlite_master WHERE type='index' AND name=?"
        results = self.connection_manager.execute_select(query, [index_name])
        return len(results) > 0
    
    def get_all_indexes(self) -> List[Dict[str, Any]]:
        """Get all indexes excluding system indexes"""
        query = "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        return self.connection_manager.execute_select(query)
    
    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all indexes for a specific table"""
        query = "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND name NOT LIKE 'sqlite_%'"
        return self.connection_manager.execute_select(query, [table_name])
    
    def analyze_table_performance(self, table_name: str) -> Dict[str, Any]:
        """Analyze table performance statistics"""
        # Get basic table statistics
        stats = {'table_name': table_name}
        
        try:
            # Count rows
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            count_result = self.connection_manager.execute_select(count_query)
            stats['row_count'] = count_result[0]['row_count'] if count_result else 0
            
            # Get table info
            info_query = f"PRAGMA table_info({table_name})"
            columns = self.connection_manager.execute_select(info_query)
            stats['column_count'] = len(columns)
            
            # Get indexes for this table
            indexes = self.get_table_indexes(table_name)
            stats['index_count'] = len(indexes)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing table {table_name}: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def reindex_table(self, table_name: str):
        """Reindex all indexes for a specific table"""
        self.logger.info(f"Reindexing table: {table_name}")
        
        try:
            # Get all indexes for the table
            indexes = self.get_table_indexes(table_name)
            
            # Reindex each one
            for index in indexes:
                index_name = index['name']
                reindex_query = f"REINDEX {index_name}"
                self.connection_manager.execute_query(reindex_query)
                self.logger.debug(f"Reindexed: {index_name}")
            
            self.logger.info(f"Reindexed {len(indexes)} indexes for table {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error reindexing table {table_name}: {e}")
            raise
    
    def rebuild_all_indexes(self):
        """Rebuild all indexes in the database"""
        self.logger.info("Rebuilding all indexes")
        
        try:
            # Get all non-system indexes
            indexes = self.get_all_indexes()
            
            # Reindex each one
            for index in indexes:
                index_name = index['name']
                reindex_query = f"REINDEX {index_name}"
                self.connection_manager.execute_query(reindex_query)
                self.logger.debug(f"Reindexed: {index_name}")
            
            self.logger.info(f"Rebuilt {len(indexes)} indexes")
            
        except Exception as e:
            self.logger.error(f"Error rebuilding indexes: {e}")
            raise
    
    def get_index_usage_stats(self, index_name: str) -> Dict[str, Any]:
        """Get usage statistics for a specific index"""
        stats = {'index_name': index_name}
        
        try:
            # Check if index exists
            if not self.index_exists(index_name):
                stats['exists'] = False
                return stats
            
            stats['exists'] = True
            
            # Get index information
            query = "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name=?"
            result = self.connection_manager.execute_select(query, [index_name])
            if result:
                stats.update(result[0])
            
        except Exception as e:
            self.logger.warning(f"Error getting index stats for {index_name}: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def optimize_indexes(self) -> List[Dict[str, Any]]:
        """Optimize indexes and return optimization results"""
        self.logger.info("Optimizing database indexes")
        
        optimization_results = []
        
        try:
            # Run ANALYZE to update statistics
            self.connection_manager.execute_query("ANALYZE")
            optimization_results.append({
                'action': 'analyze',
                'table': 'all',
                'status': 'completed',
                'description': 'Updated database statistics'
            })
            
            # Get all tables
            tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            tables = self.connection_manager.execute_select(tables_query)
            
            for table in tables:
                table_name = table['name']
                
                try:
                    # Reindex table
                    self.reindex_table(table_name)
                    optimization_results.append({
                        'action': 'reindex',
                        'table': table_name,
                        'status': 'completed',
                        'description': f'Reindexed all indexes for {table_name}'
                    })
                    
                except Exception as e:
                    optimization_results.append({
                        'action': 'reindex',
                        'table': table_name,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            self.logger.info(f"Index optimization completed with {len(optimization_results)} actions")
            
        except Exception as e:
            self.logger.error(f"Error during index optimization: {e}")
            optimization_results.append({
                'action': 'optimize',
                'table': 'all',
                'status': 'failed',
                'error': str(e)
            })
        
        return optimization_results