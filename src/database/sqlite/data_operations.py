"""
SQLite Data Operations - High-level database operations and business logic.
Extracted from SQLiteAdapter for better modularity.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...core.logging import get_logger
from .connection_manager import SQLiteConnectionManager
from .query_builder import SQLiteQueryBuilder
from .table_manager import SQLiteTableManager


class SQLiteDataOperations:
    """High-level data operations for SQLite database"""
    
    def __init__(self, connection_manager: SQLiteConnectionManager, 
                 query_builder: SQLiteQueryBuilder, table_manager: SQLiteTableManager):
        """Initialize data operations with dependencies"""
        self.connection_manager = connection_manager
        self.query_builder = query_builder
        self.table_manager = table_manager
        self.logger = get_logger("sqlite_data_operations")
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string for storage"""
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return str(data)
    
    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string from storage"""
        if not data:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    async def insert(self, table: str, data: Dict[str, Any]) -> str:
        """Insert a record into the specified table"""
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
                'performance_metrics': False, 'trace_events': True,  # performance_metrics uses timestamp
                'content_ratings': True, 'lore_documents': True, 'lore_clusters': True
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
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes', 'metadata', 'embedding'
            ]
            serialized_data = {}
            for key, value in data.items():
                if key in json_fields and isinstance(value, (dict, list)):
                    serialized_data[key] = self._serialize_json(value)
                else:
                    serialized_data[key] = value
            
            # Build query
            query, params = self.query_builder.build_insert(table, serialized_data)
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                self.connection_manager.execute_query, 
                query, 
                params
            )
            
            # Return the ID
            return data['id']
            
        except Exception as e:
            self.logger.error(f"Error inserting into {table}: {e}")
            raise
    
    async def select(self, table: str, filters: Optional[Dict[str, Any]] = None,
                    order_by: Optional[str] = None, desc: bool = False,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Select records from the specified table"""
        try:
            # Build query
            query, params = self.query_builder.build_select(
                table, filters, order_by, desc, limit
            )
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.connection_manager.execute_select,
                query,
                params
            )
            
            # Deserialize JSON fields
            for result in results:
                for key, value in result.items():
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                        try:
                            result[key] = self._deserialize_json(value)
                        except:
                            # If deserialization fails, keep as string
                            pass
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error selecting from {table}: {e}")
            raise
    
    async def get_by_id(self, table_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        results = await self.select(table_name, {"id": entity_id}, limit=1)
        return results[0] if results else None
    
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
                'parsed_json', 'tags', 'attributes', 'events', 'resource_attributes', 'metadata', 'embedding'
            ]
            serialized_data = {}
            for key, value in data.items():
                if key in json_fields and isinstance(value, (dict, list)):
                    serialized_data[key] = self._serialize_json(value)
                else:
                    serialized_data[key] = value
            
            # Build query
            query, params = self.query_builder.build_update(table, record_id, serialized_data)
            
            # Execute in thread pool to avoid blocking and get row count
            loop = asyncio.get_event_loop()
            rows_affected = await loop.run_in_executor(
                None,
                self.connection_manager.execute_query_with_rowcount,
                query,
                params
            )
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error updating {table} record {record_id}: {e}")
            return False
    
    async def delete(self, table: str, record_id: str) -> bool:
        """Delete a record from the specified table"""
        try:
            # Build query
            query, params = self.query_builder.build_delete(table, record_id)
            
            # Execute in thread pool to avoid blocking and get row count
            loop = asyncio.get_event_loop()
            rows_affected = await loop.run_in_executor(
                None,
                self.connection_manager.execute_query_with_rowcount,
                query,
                params
            )
            
            return rows_affected > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting from {table}: {e}")
            return False
    
    async def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records in the specified table"""
        try:
            # Build query
            query, params = self.query_builder.build_count(table, filters)
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(
                None,
                self.connection_manager.execute_count,
                query,
                params
            )
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting {table}: {e}")
            raise
    
    async def get_all(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all records with pagination"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.connection_manager.execute_select,
                query
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting all from {table_name}: {e}")
            raise
    
    async def search(self, table_name: str, criteria: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Search records with LIKE conditions"""
        try:
            # Build search query
            query, params = self.query_builder.build_search(table_name, criteria, limit)
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.connection_manager.execute_select,
                query,
                params
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching {table_name}: {e}")
            raise
    
    async def batch_insert(self, table: str, records: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple records in a batch"""
        try:
            # Generate IDs and serialize JSON fields
            processed_records = []
            record_ids = []
            
            for record in records:
                # Generate ID if not provided
                if 'id' not in record:
                    record['id'] = str(uuid.uuid4())
                record_ids.append(record['id'])
                
                # Serialize JSON fields
                serialized_record = {}
                for key, value in record.items():
                    if isinstance(value, (dict, list)):
                        serialized_record[key] = self._serialize_json(value)
                    else:
                        serialized_record[key] = value
                processed_records.append(serialized_record)
            
            # Build batch query
            query, params = self.query_builder.build_batch_insert(table, processed_records)
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.connection_manager.execute_query,
                query,
                params
            )
            
            return record_ids
            
        except Exception as e:
            self.logger.error(f"Error batch inserting into {table}: {e}")
            raise
    
    async def batch_select_by_ids(self, table: str, ids: List[str]) -> List[Dict[str, Any]]:
        """Select multiple records by their IDs"""
        try:
            # Build query
            query, params = self.query_builder.build_select_by_ids(table, ids)
            
            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.connection_manager.execute_select,
                query,
                params
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error batch selecting from {table}: {e}")
            raise
    
    async def batch_update(self, table: str, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records in a batch"""
        try:
            updated_count = 0
            
            # Process each update individually for now
            # TODO: Could be optimized with a single query
            for update_data in updates:
                record_id = update_data.pop('id')  # Remove ID from update data
                success = await self.update(table, record_id, update_data)
                if success:
                    updated_count += 1
            
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error batch updating {table}: {e}")
            raise
    
    # Specialized operations for plots and authors
    
    async def save_plot(self, plot_data: Dict[str, Any]) -> str:
        """Save a plot record"""
        return await self.insert("plots", plot_data)
    
    async def save_author(self, author_data: Dict[str, Any]) -> str:
        """Save an author record"""
        return await self.insert("authors", author_data)
    
    async def get_plot(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Get a plot by ID"""
        return await self.get_by_id("plots", plot_id)
    
    async def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Get an author by ID"""
        return await self.get_by_id("authors", author_id)
    
    async def get_plots_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all plots for a specific user"""
        return await self.select("plots", {"user_id": user_id}, limit=limit)
    
    async def get_authors_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all authors for a specific user"""
        return await self.select("authors", {"user_id": user_id}, limit=limit)
    
    async def get_plot_with_author(self, plot_id: str) -> Dict[str, Any]:
        """Get plot with its associated author"""
        try:
            # Get the plot
            plot = await self.get_plot(plot_id)
            if not plot:
                return {"plot": None, "author": None}
            
            # Get associated author if exists
            author = None
            if plot.get("author_id"):
                author = await self.get_author(plot["author_id"])
            
            return {
                "plot": plot,
                "author": author
            }
            
        except Exception as e:
            self.logger.error(f"Error getting plot with author for {plot_id}: {e}")
            raise
    
    async def search_content(self, query: str, content_type: str, user_id: str) -> List[Dict[str, Any]]:
        """Search content across different content types"""
        try:
            # Map content types to tables and searchable fields
            content_mappings = {
                "plots": ["title", "plot_summary"],
                "authors": ["author_name", "biography"],
                "world_building": ["world_name", "overview"],
                "characters": ["characters"]
            }
            
            if content_type not in content_mappings:
                return []
            
            # Build search criteria
            search_criteria = {}
            for field in content_mappings[content_type]:
                search_criteria[field] = f"%{query}%"
            
            # Add user filter
            results = await self.select(content_type, {"user_id": user_id})
            
            # Filter results based on search criteria
            filtered_results = []
            for result in results:
                for field in content_mappings[content_type]:
                    if field in result and result[field]:
                        if query.lower() in str(result[field]).lower():
                            filtered_results.append(result)
                            break
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error searching content: {e}")
            raise
    
    async def close(self):
        """Close data operations (cleanup)"""
        # Delegate to connection manager
        self.connection_manager.close()