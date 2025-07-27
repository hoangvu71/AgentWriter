"""
MCP Agent Mixin - Adds direct MCP tool access to BaseAgent.
Provides agents with secure, validated access to MCP tools.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC

from .mcp_tool_manager import MCPToolManager, MCPToolDescriptor, create_mcp_tool_manager
from .logging import get_logger


class MCPAgentMixin(ABC):
    """
    Mixin class that adds MCP tool capabilities to BaseAgent.
    Provides direct access to MCP tools with validation and security.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mcp_manager: Optional[MCPToolManager] = None
        self._mcp_logger = get_logger(f"mcp.{getattr(self, '_name', 'unknown')}")
        
        # Initialize MCP manager if available
        self._init_mcp_manager()
    
    def _init_mcp_manager(self) -> None:
        """Initialize MCP tool manager"""
        try:
            if hasattr(self, '_config'):
                self._mcp_manager = create_mcp_tool_manager(self._config)
                self._mcp_logger.info("MCP tool manager initialized successfully")
            else:
                self._mcp_logger.warning("No configuration available for MCP manager")
        except Exception as e:
            self._mcp_logger.error(f"Failed to initialize MCP manager: {e}")
            self._mcp_manager = None
    
    @property
    def has_mcp_access(self) -> bool:
        """Check if agent has MCP access"""
        return self._mcp_manager is not None
    
    def list_mcp_tools(self) -> List[MCPToolDescriptor]:
        """
        List available MCP tools for this agent.
        
        Returns:
            List of available MCP tool descriptors
        """
        if not self._mcp_manager:
            self._mcp_logger.warning("MCP manager not available")
            return []
        
        try:
            agent_name = getattr(self, '_name', 'unknown')
            tools = self._mcp_manager.get_available_tools(agent_name)
            self._mcp_logger.info(f"Found {len(tools)} MCP tools available for {agent_name}")
            return tools
        except Exception as e:
            self._mcp_logger.error(f"Error listing MCP tools: {e}")
            return []
    
    def get_mcp_tool_info(self, tool_name: str) -> Optional[MCPToolDescriptor]:
        """
        Get information about a specific MCP tool.
        
        Args:
            tool_name: Name of the MCP tool
            
        Returns:
            Tool descriptor or None if not found
        """
        if not self._mcp_manager:
            return None
        
        return self._mcp_manager.get_tool_by_name(tool_name)
    
    async def call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call an MCP tool with parameters.
        
        Args:
            tool_name: Name of the MCP tool to call
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        if not self._mcp_manager:
            return {
                "success": False,
                "error": "MCP manager not available",
                "tool_name": tool_name
            }
        
        try:
            agent_name = getattr(self, '_name', 'unknown')
            self._mcp_logger.info(f"Agent {agent_name} calling MCP tool: {tool_name}")
            
            result = await self._mcp_manager.execute_mcp_tool(tool_name, kwargs, agent_name)
            
            if result.get("success"):
                self._mcp_logger.info(f"MCP tool {tool_name} executed successfully")
            else:
                self._mcp_logger.warning(f"MCP tool {tool_name} failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self._mcp_logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    # Convenience methods for common MCP operations
    
    async def mcp_query_database(self, query: str, parameters: Optional[List] = None) -> Dict[str, Any]:
        """
        Execute a database query using MCP.
        
        Args:
            query: SQL query to execute
            parameters: Optional query parameters
            
        Returns:
            Query result
        """
        params = {"query": query}
        if parameters:
            params["parameters"] = parameters
        
        return await self.call_mcp_tool("mcp__supabase__query", **params)
    
    async def mcp_insert_data(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert data into a table using MCP.
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Insert result
        """
        return await self.call_mcp_tool("mcp__supabase__insert", table=table, data=data)
    
    async def mcp_update_data(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update data in a table using MCP.
        
        Args:
            table: Table name
            data: Data to update
            where: WHERE conditions
            
        Returns:
            Update result
        """
        return await self.call_mcp_tool("mcp__supabase__update", table=table, data=data, where=where)
    
    async def mcp_list_tables(self) -> Dict[str, Any]:
        """
        List available database tables using MCP.
        
        Returns:
            List of tables
        """
        return await self.call_mcp_tool("mcp__supabase__list_tables")
    
    async def mcp_describe_table(self, table: str) -> Dict[str, Any]:
        """
        Get table schema information using MCP.
        
        Args:
            table: Table name
            
        Returns:
            Table schema information
        """
        return await self.call_mcp_tool("mcp__supabase__describe_table", table=table)
    
    # Helper methods for data analysis and content discovery
    
    async def mcp_get_user_content_history(self, user_id: str, content_type: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get user's content history for context-aware generation.
        
        Args:
            user_id: User ID
            content_type: Type of content (plots, authors, worlds, etc.)
            limit: Maximum number of items to return
            
        Returns:
            User's content history
        """
        table_map = {
            "plots": "plots",
            "authors": "authors", 
            "worlds": "world_building",
            "characters": "characters"
        }
        
        table = table_map.get(content_type)
        if not table:
            return {"success": False, "error": f"Unknown content type: {content_type}"}
        
        query = f"""
        SELECT * FROM {table} 
        WHERE user_id = $1 
        ORDER BY created_at DESC 
        LIMIT $2
        """
        
        return await self.mcp_query_database(query, [user_id, limit])
    
    async def mcp_analyze_content_patterns(self, content_type: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze content generation patterns for system optimization.
        
        Args:
            content_type: Type of content to analyze
            days: Number of days to analyze
            
        Returns:
            Content pattern analysis
        """
        table_map = {
            "plots": "plots",
            "authors": "authors",
            "worlds": "world_building", 
            "characters": "characters"
        }
        
        table = table_map.get(content_type)
        if not table:
            return {"success": False, "error": f"Unknown content type: {content_type}"}
        
        query = f"""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count,
            AVG(CASE WHEN genre IS NOT NULL THEN 1 ELSE 0 END) as genre_completion_rate
        FROM {table}
        WHERE created_at >= NOW() - INTERVAL '{days} days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        
        return await self.mcp_query_database(query)
    
    async def mcp_check_content_uniqueness(self, content_type: str, field: str, value: str, user_id: str) -> Dict[str, Any]:
        """
        Check if content is unique for a user to avoid duplicates.
        
        Args:
            content_type: Type of content
            field: Field to check uniqueness for
            value: Value to check
            user_id: User ID
            
        Returns:
            Uniqueness check result
        """
        table_map = {
            "plots": "plots",
            "authors": "authors",
            "worlds": "world_building",
            "characters": "characters"
        }
        
        table = table_map.get(content_type)
        if not table:
            return {"success": False, "error": f"Unknown content type: {content_type}"}
        
        query = f"""
        SELECT COUNT(*) as count 
        FROM {table} 
        WHERE {field} = $1 AND user_id = $2
        """
        
        result = await self.mcp_query_database(query, [value, user_id])
        
        if result.get("success"):
            rows = result.get("result", {}).get("rows", [])
            is_unique = len(rows) == 0 or (len(rows) > 0 and rows[0].get("count", 0) == 0)
            return {
                "success": True,
                "is_unique": is_unique,
                "existing_count": rows[0].get("count", 0) if rows else 0
            }
        
        return result
    
    def _log_mcp_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log MCP operation for observability"""
        agent_name = getattr(self, '_name', 'unknown')
        self._mcp_logger.info(f"Agent {agent_name} MCP operation: {operation}", extra=details)