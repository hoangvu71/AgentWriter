"""
Supabase database adapter implementing the IDatabase interface.
Direct Supabase client wrapper without supabase_service dependency.
"""

import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from ..core.interfaces import IDatabase, ContentType
from ..core.logging import get_logger
from .connection_pool import SupabaseConnectionPool, ConnectionPoolConfig


class SupabaseAdapter(IDatabase):
    """Supabase client adapter with connection pooling implementing IDatabase interface"""
    
    def __init__(self, url: str = None, key: str = None, pool_config: Optional[ConnectionPoolConfig] = None):
        self.logger = get_logger("database.supabase")
        
        # Use provided credentials or get from environment
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be provided")
        
        # Initialize connection pool
        self.pool_config = pool_config or ConnectionPoolConfig(
            min_connections=2,
            max_connections=8,
            max_idle_time=300,
            connection_timeout=30,
            health_check_interval=60,
            enable_metrics=True
        )
        
        try:
            # Create primary client for immediate use
            self.client: Client = create_client(self.url, self.key)
            
            # Initialize connection pool
            self.connection_pool = SupabaseConnectionPool(self.url, self.key, self.pool_config)
            
            self.logger.info("Supabase client and connection pool initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> str:
        """Insert data into table and return ID using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).insert(data).execute()
                if response.data:
                    return response.data[0]["id"]
                raise Exception("No data returned from insert")
        except Exception as e:
            self.logger.error(f"Error inserting into {table_name}: {e}", error=e)
            raise
    
    async def get_by_id(self, table_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).select("*").eq("id", entity_id).execute()
                return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error(f"Error getting {table_name} by ID {entity_id}: {e}", error=e)
            raise
    
    async def update(self, table_name: str, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update entity by ID using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).update(data).eq("id", entity_id).execute()
                return len(response.data) > 0
        except Exception as e:
            self.logger.error(f"Error updating {table_name} {entity_id}: {e}", error=e)
            raise
    
    async def delete(self, table_name: str, entity_id: str) -> bool:
        """Delete entity by ID using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).delete().eq("id", entity_id).execute()
                return len(response.data) > 0
        except Exception as e:
            self.logger.error(f"Error deleting {table_name} {entity_id}: {e}", error=e)
            raise
    
    async def get_all(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all entities with pagination using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
                return response.data
        except Exception as e:
            self.logger.error(f"Error getting all {table_name}: {e}", error=e)
            raise
    
    async def search(self, table_name: str, criteria: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Search entities by criteria using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                query = conn.client.table(table_name).select("*")
                
                # Apply criteria as filters
                for key, value in criteria.items():
                    query = query.eq(key, value)
                
                response = query.order("created_at", desc=True).limit(limit).execute()
                return response.data
        except Exception as e:
            self.logger.error(f"Error searching {table_name}: {e}", error=e)
            raise
    
    async def count(self, table_name: str, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching criteria using connection pool"""
        try:
            async with self.connection_pool.get_connection() as conn:
                query = conn.client.table(table_name).select("*", count="exact")
                
                if criteria:
                    for key, value in criteria.items():
                        query = query.eq(key, value)
                
                response = query.execute()
                return response.count or 0
        except Exception as e:
            self.logger.error(f"Error counting {table_name}: {e}", error=e)
            raise
    
    # Implementation of content-specific methods required by interface
    async def save_plot(self, plot_data: Dict[str, Any]) -> str:
        """Save plot data and return ID"""
        try:
            # Extract metadata for proper Supabase format
            external_session_id = plot_data.get("session_id")
            external_user_id = plot_data.get("user_id")
            
            # Convert external IDs to internal UUIDs if needed
            if external_session_id and external_user_id:
                user_data = await self._create_or_get_user(external_user_id)
                
                # Get the session by external session_id to get internal UUID
                session_response = self.client.table("sessions").select("*").eq("session_id", external_session_id).execute()
                if not session_response.data:
                    # Create session if it doesn't exist
                    session_data = await self._create_session(external_session_id, external_user_id)
                    session_uuid = session_data["id"]
                else:
                    session_uuid = session_response.data[0]["id"]
                
                # Update plot data with proper UUID references
                plot_data["user_id"] = user_data["id"]  # internal user UUID
                plot_data["session_id"] = session_uuid  # internal session UUID
            
            return await self.insert("plots", plot_data)
        except Exception as e:
            self.logger.error(f"Error saving plot: {e}", error=e)
            raise
    
    async def save_author(self, author_data: Dict[str, Any]) -> str:
        """Save author data and return ID"""
        try:
            # Extract metadata for proper Supabase format
            external_session_id = author_data.get("session_id")
            external_user_id = author_data.get("user_id")
            
            # Convert external IDs to internal UUIDs if needed
            if external_session_id and external_user_id:
                user_data = await self._create_or_get_user(external_user_id)
                
                # Get the session by external session_id to get internal UUID
                session_response = self.client.table("sessions").select("*").eq("session_id", external_session_id).execute()
                if not session_response.data:
                    # Create session if it doesn't exist
                    session_data = await self._create_session(external_session_id, external_user_id)
                    session_uuid = session_data["id"]
                else:
                    session_uuid = session_response.data[0]["id"]
                
                # Update author data with proper UUID references
                author_data["user_id"] = user_data["id"]  # internal user UUID
                author_data["session_id"] = session_uuid  # internal session UUID
            
            return await self.insert("authors", author_data)
        except Exception as e:
            self.logger.error(f"Error saving author: {e}", error=e)
            raise
    
    async def get_plot(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve plot by ID"""
        return await self.get_by_id("plots", plot_id)
    
    async def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve author by ID"""
        return await self.get_by_id("authors", author_id)
    
    async def search_content(self, query: str, content_type: ContentType, user_id: str) -> List[Dict[str, Any]]:
        """Search for content"""
        try:
            # Get user UUID
            user_data = await self._create_or_get_user(user_id)
            user_uuid = user_data["id"]
            
            if content_type == ContentType.PLOT:
                return await self._search_plots(user_id, query, 20)
            elif content_type == ContentType.AUTHOR:
                # Search authors by name
                response = self.client.table("authors").select("*").eq("user_id", user_uuid).or_(f"author_name.ilike.%{query}%,pen_name.ilike.%{query}%").order("created_at", desc=True).limit(20).execute()
                return response.data
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error searching content: {e}", error=e)
            raise
    
    # Additional methods for repository compatibility
    async def get_plots_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get plots for a user using external user_id"""
        return await self._get_user_plots(user_id, limit)
    
    async def get_authors_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get authors for a user using external user_id"""
        return await self._get_user_authors(user_id, limit)
    
    async def get_plot_with_author(self, plot_id: str) -> Dict[str, Any]:
        """Get plot with associated author"""
        try:
            # Get plot data
            plot_response = self.client.table("plots").select("*").eq("id", plot_id).execute()
            if not plot_response.data:
                return {}
            
            plot = plot_response.data[0]
            
            # Get associated author if exists
            if plot.get("author_id"):
                author_response = self.client.table("authors").select("*").eq("id", plot["author_id"]).execute()
                if author_response.data:
                    plot["author"] = author_response.data[0]
            
            return plot
        except Exception as e:
            self.logger.error(f"Error getting plot with author: {e}")
            return {}
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a table"""
        try:
            query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
            """
            
            response = self.client.rpc('exec_sql', {'sql': query}).execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error getting table schema: {e}")
            return []
    
    async def _create_or_get_user(self, user_id: str) -> Dict[str, Any]:
        """Create or get user by external user_id"""
        try:
            # Try to get existing user (using correct field name)
            response = self.client.table("users").select("*").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0]
            
            # Create new user (matching actual database schema)
            user_data = {"user_id": user_id}
            response = self.client.table("users").insert(user_data).execute()
            return response.data[0] if response.data else user_data
        except Exception as e:
            self.logger.error(f"Error creating/getting user: {e}")
            return {"user_id": user_id}
    
    async def _create_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Create a new session"""
        try:
            # First ensure user exists and get their internal UUID
            user_data = await self._create_or_get_user(user_id)
            user_uuid = user_data["id"]  # Get the actual UUID from the database
            
            session_data = {
                "session_id": session_id,  # external session identifier
                "user_id": user_uuid,      # internal user UUID for foreign key
                "created_at": "now()",
                "updated_at": "now()"
            }
            response = self.client.table("sessions").insert(session_data).execute()
            return response.data[0] if response.data else session_data
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return {"session_id": session_id, "user_id": user_id}
    
    async def _search_plots(self, user_id: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search plots for a user"""
        try:
            response = (self.client.table("plots")
                       .select("*")
                       .eq("user_id", user_id)
                       .ilike("title", f"%{query}%")
                       .limit(limit)
                       .execute())
            return response.data
        except Exception as e:
            self.logger.error(f"Error searching plots: {e}")
            return []
    
    async def _get_user_plots(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get plots for a user"""
        try:
            response = (self.client.table("plots")
                       .select("*")
                       .eq("user_id", user_id)
                       .order("created_at", desc=True)
                       .limit(limit)
                       .execute())
            return response.data
        except Exception as e:
            self.logger.error(f"Error getting user plots: {e}")
            return []
    
    async def _get_user_authors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get authors for a user"""
        try:
            # Get authors through plots since authors don't directly reference users
            response = (self.client.table("plots")
                       .select("author_id")
                       .eq("user_id", user_id)
                       .execute())
            
            if not response.data:
                return []
            
            author_ids = [plot["author_id"] for plot in response.data if plot.get("author_id")]
            if not author_ids:
                return []
            
            # Get unique authors
            authors_response = (self.client.table("authors")
                               .select("*")
                               .in_("id", list(set(author_ids)))
                               .limit(limit)
                               .execute())
            return authors_response.data
        except Exception as e:
            self.logger.error(f"Error getting user authors: {e}")
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
    
    async def batch_insert(self, table_name: str, records: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple records using connection pool"""
        if not records:
            return []
        
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).insert(records).execute()
                return [record["id"] for record in response.data] if response.data else []
        except Exception as e:
            self.logger.error(f"Error in batch insert to {table_name}: {e}")
            raise
    
    async def batch_select_by_ids(self, table_name: str, ids: List[str]) -> List[Dict[str, Any]]:
        """Select multiple records by IDs using connection pool"""
        if not ids:
            return []
        
        try:
            async with self.connection_pool.get_connection() as conn:
                response = conn.client.table(table_name).select("*").in_("id", ids).execute()
                return response.data if response.data else []
        except Exception as e:
            self.logger.error(f"Error in batch select from {table_name}: {e}")
            raise
    
    async def batch_update(self, table_name: str, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records using connection pool"""
        if not updates:
            return 0
        
        updated_count = 0
        
        try:
            async with self.connection_pool.get_connection() as conn:
                for update in updates:
                    record_id = update['id']
                    data = update['data']
                    
                    response = conn.client.table(table_name).update(data).eq("id", record_id).execute()
                    if response.data and len(response.data) > 0:
                        updated_count += 1
                
                return updated_count
        except Exception as e:
            self.logger.error(f"Error in batch update to {table_name}: {e}")
            raise
    
    async def start_background_tasks(self):
        """Start background health monitoring tasks"""
        if hasattr(self, 'connection_pool'):
            await self.connection_pool.start_background_tasks()
    
    async def close(self):
        """Close the database adapter and connection pool"""
        if hasattr(self, 'connection_pool'):
            await self.connection_pool.close()
            self.logger.info("Supabase adapter closed")