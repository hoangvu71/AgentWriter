"""
Refactored SQLite Adapter - Uses modular components for better maintainability.
This replaces the monolithic SQLiteAdapter with a composition-based approach.
"""

from typing import Dict, Any, List, Optional
from ...core.logging import get_logger
from .connection_manager import SQLiteConnectionManager
from .query_builder import SQLiteQueryBuilder  
from .table_manager import SQLiteTableManager
from .data_operations import SQLiteDataOperations


class SQLiteAdapter:
    """
    Refactored SQLite database adapter using modular components.
    
    This adapter maintains the same interface as the original SQLiteAdapter
    but uses focused modules for better separation of concerns.
    """
    
    def __init__(self, db_path: str = "local_database.db"):
        """Initialize adapter with modular components"""
        self.db_path = db_path
        self.logger = get_logger("sqlite_adapter")
        
        # Initialize modular components
        self.connection_manager = SQLiteConnectionManager(db_path)
        self.query_builder = SQLiteQueryBuilder()
        self.table_manager = SQLiteTableManager(self.connection_manager)
        self.data_operations = SQLiteDataOperations(
            self.connection_manager, 
            self.query_builder, 
            self.table_manager
        )
        
        # Initialize database schema
        self.table_manager.create_all_tables()
        
        self.logger.info(f"Refactored SQLite adapter initialized at {db_path}")
    
    # Delegate all operations to the data_operations module
    # This maintains the original interface while using the new modular structure
    
    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert a record into the specified table"""
        return await self.data_operations.insert(table, data)
    
    async def select(self, table: str, filters: Optional[Dict[str, Any]] = None,
                    order_by: Optional[str] = None, desc: bool = False,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Select records from the specified table"""
        return await self.data_operations.select(table, filters, order_by, desc, limit)
    
    async def get_by_id(self, table_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        return await self.data_operations.get_by_id(table_name, entity_id)
    
    async def update(self, table: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update a record in the specified table"""
        return await self.data_operations.update(table, record_id, data)
    
    async def delete(self, table: str, record_id: str) -> bool:
        """Delete a record from the specified table"""
        return await self.data_operations.delete(table, record_id)
    
    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records in the specified table"""
        return await self.data_operations.count(table, filters)
    
    async def get_all(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all records with pagination"""
        return await self.data_operations.get_all(table_name, limit, offset)
    
    async def search(self, table_name: str, criteria: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Search records with LIKE conditions"""
        return await self.data_operations.search(table_name, criteria, limit)
    
    async def batch_insert(self, table: str, records: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple records in a batch"""
        return await self.data_operations.batch_insert(table, records)
    
    async def batch_select_by_ids(self, table: str, ids: List[str]) -> List[Dict[str, Any]]:
        """Select multiple records by their IDs"""
        return await self.data_operations.batch_select_by_ids(table, ids)
    
    async def batch_update(self, table: str, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records in a batch"""
        return await self.data_operations.batch_update(table, updates)
    
    # Specialized operations
    
    async def save_plot(self, plot_data: Dict[str, Any]) -> str:
        """Save a plot record"""
        return await self.data_operations.save_plot(plot_data)
    
    async def save_author(self, author_data: Dict[str, Any]) -> str:
        """Save an author record"""
        return await self.data_operations.save_author(author_data)
    
    async def get_plot(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Get a plot by ID"""
        return await self.data_operations.get_plot(plot_id)
    
    async def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Get an author by ID"""
        return await self.data_operations.get_author(author_id)
    
    async def get_plots_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all plots for a specific user"""
        return await self.data_operations.get_plots_by_user(user_id, limit)
    
    async def get_authors_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all authors for a specific user"""
        return await self.data_operations.get_authors_by_user(user_id, limit)
    
    async def get_plot_with_author(self, plot_id: str) -> Dict[str, Any]:
        """Get plot with its associated author"""
        return await self.data_operations.get_plot_with_author(plot_id)
    
    async def search_content(self, query: str, content_type: str, user_id: str) -> List[Dict[str, Any]]:
        """Search content across different content types"""
        return await self.data_operations.search_content(query, content_type, user_id)
    
    # Pool metrics compatibility (simplified for modular design)
    
    async def get_pool_metrics(self) -> Dict[str, Any]:
        """Get simplified pool metrics"""
        return {
            "total_operations": 0,  # Could be tracked if needed
            "active_connections": 1,  # Simplified for current design
            "adapter_type": "modular_sqlite"
        }
    
    async def reset_pool_metrics(self):
        """Reset pool metrics (placeholder)"""
        pass
    
    async def close(self):
        """Close the adapter and all components"""
        await self.data_operations.close()
        self.logger.info("Refactored SQLite adapter closed")