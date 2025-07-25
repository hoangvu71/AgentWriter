"""
MCP Tool Manager for direct agent access to MCP tools.
Provides discovery, validation, and execution of MCP tools.
"""

import logging
import inspect
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass
from functools import wraps

from .interfaces import IConfiguration
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class MCPToolDescriptor:
    """Describes an available MCP tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    security_level: str = "standard"  # standard, restricted, admin
    category: str = "database"  # database, search, analytics, etc.


class MCPToolManager:
    """
    Manages discovery and execution of MCP tools for agents.
    Provides validation, security, and observability for direct MCP access.
    """
    
    def __init__(self, config: IConfiguration):
        self._config = config
        self._logger = get_logger("mcp_tool_manager")
        self._available_tools: Dict[str, MCPToolDescriptor] = {}
        self._tool_registry: Dict[str, Callable] = {}
        self._restricted_tools: Set[str] = set()
        
        # Initialize MCP tool discovery
        self._discover_mcp_tools()
    
    def _discover_mcp_tools(self) -> None:
        """Discover available MCP tools from the environment"""
        try:
            # Check if we're running in an MCP-enabled environment
            if self._has_mcp_capabilities():
                self._register_supabase_tools()
                self._register_analytics_tools()
                self._register_search_tools()
                self._logger.info(f"Discovered {len(self._available_tools)} MCP tools")
            else:
                self._logger.warning("MCP capabilities not detected - tools will be unavailable")
                
        except Exception as e:
            self._logger.error(f"Error discovering MCP tools: {e}")
    
    def _has_mcp_capabilities(self) -> bool:
        """Check if MCP tools are available in the current environment"""
        # In a real implementation, this would check for MCP server connectivity
        # For now, we'll assume MCP is available if certain environment conditions are met
        try:
            # Check if we have required MCP configuration
            import os
            return bool(
                os.getenv("SUPABASE_ACCESS_TOKEN") and 
                os.getenv("SUPABASE_URL")
            )
        except Exception:
            return False
    
    def _register_supabase_tools(self) -> None:
        """Register Supabase MCP tools"""
        supabase_tools = [
            MCPToolDescriptor(
                name="mcp__supabase__query",
                description="Execute SQL queries on Supabase database",
                parameters={
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "parameters": {"type": "array", "description": "Query parameters", "optional": True}
                },
                security_level="standard",
                category="database"
            ),
            MCPToolDescriptor(
                name="mcp__supabase__insert",
                description="Insert data into Supabase tables",
                parameters={
                    "table": {"type": "string", "description": "Table name"},
                    "data": {"type": "object", "description": "Data to insert"}
                },
                security_level="standard",
                category="database"
            ),
            MCPToolDescriptor(
                name="mcp__supabase__update",
                description="Update data in Supabase tables",
                parameters={
                    "table": {"type": "string", "description": "Table name"},
                    "data": {"type": "object", "description": "Data to update"},
                    "where": {"type": "object", "description": "Where conditions"}
                },
                security_level="standard",
                category="database"
            ),
            MCPToolDescriptor(
                name="mcp__supabase__delete",
                description="Delete data from Supabase tables",
                parameters={
                    "table": {"type": "string", "description": "Table name"},
                    "where": {"type": "object", "description": "Where conditions"}
                },
                security_level="restricted",
                category="database"
            ),
            MCPToolDescriptor(
                name="mcp__supabase__list_tables",
                description="List all available tables",
                parameters={},
                security_level="standard",
                category="database"
            ),
            MCPToolDescriptor(
                name="mcp__supabase__describe_table",
                description="Get table schema information",
                parameters={
                    "table": {"type": "string", "description": "Table name"}
                },
                security_level="standard",
                category="database"
            )
        ]
        
        for tool in supabase_tools:
            self._available_tools[tool.name] = tool
            if tool.security_level == "restricted":
                self._restricted_tools.add(tool.name)
    
    def _register_analytics_tools(self) -> None:
        """Register analytics and monitoring MCP tools"""
        # These would be additional MCP tools for system analytics
        pass
    
    def _register_search_tools(self) -> None:
        """Register search and content discovery MCP tools"""
        # These would be additional MCP tools for content search
        pass
    
    def get_available_tools(self, agent_name: str = None) -> List[MCPToolDescriptor]:
        """Get list of available MCP tools for an agent"""
        available = list(self._available_tools.values())
        
        # Filter based on agent permissions if needed
        if agent_name:
            # In the future, we could implement per-agent permissions
            pass
        
        return available
    
    def get_tool_by_name(self, tool_name: str) -> Optional[MCPToolDescriptor]:
        """Get tool descriptor by name"""
        return self._available_tools.get(tool_name)
    
    def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any], agent_name: str) -> bool:
        """Validate an MCP tool call before execution"""
        try:
            # Check if tool exists
            tool = self._available_tools.get(tool_name)
            if not tool:
                self._logger.warning(f"Unknown MCP tool requested: {tool_name}")
                return False
            
            # Check if agent is allowed to use restricted tools
            if tool.security_level == "restricted":
                if not self._is_agent_authorized_for_restricted_tools(agent_name):
                    self._logger.warning(f"Agent {agent_name} not authorized for restricted tool {tool_name}")
                    return False
            
            # Validate required parameters
            if not self._validate_parameters(tool, parameters):
                return False
            
            # Additional security checks for database operations
            if tool.category == "database":
                if not self._validate_database_operation(tool_name, parameters):
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error validating tool call {tool_name}: {e}")
            return False
    
    def _is_agent_authorized_for_restricted_tools(self, agent_name: str) -> bool:
        """Check if agent is authorized for restricted tools"""
        # For now, only orchestrator and specific agents can use restricted tools
        authorized_agents = {"orchestrator", "enhancement", "critique"}
        return agent_name.lower() in authorized_agents
    
    def _validate_parameters(self, tool: MCPToolDescriptor, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters against schema"""
        try:
            for param_name, param_schema in tool.parameters.items():
                # Check required parameters
                if not param_schema.get("optional", False) and param_name not in parameters:
                    self._logger.warning(f"Required parameter {param_name} missing for tool {tool.name}")
                    return False
                
                # Basic type validation
                if param_name in parameters:
                    expected_type = param_schema.get("type")
                    if expected_type and not self._validate_parameter_type(parameters[param_name], expected_type):
                        self._logger.warning(f"Parameter {param_name} has invalid type for tool {tool.name}")
                        return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error validating parameters: {e}")
            return False
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, allow it
    
    def _validate_database_operation(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Additional validation for database operations"""
        try:
            # Validate SQL queries for dangerous operations
            if tool_name == "mcp__supabase__query":
                query = parameters.get("query", "").lower().strip()
                
                # Block dangerous operations
                dangerous_keywords = ["drop", "truncate", "alter", "create", "grant", "revoke"]
                if any(keyword in query for keyword in dangerous_keywords):
                    self._logger.warning(f"Dangerous SQL operation blocked: {query[:100]}...")
                    return False
                
                # Require WHERE clause for UPDATE/DELETE operations
                if "delete" in query and "where" not in query:
                    self._logger.warning("DELETE without WHERE clause blocked")
                    return False
                
                if "update" in query and "where" not in query:
                    self._logger.warning("UPDATE without WHERE clause blocked")
                    return False
            
            # Validate table names for direct table operations
            if tool_name in ["mcp__supabase__insert", "mcp__supabase__update", "mcp__supabase__delete"]:
                table = parameters.get("table", "")
                if not self._is_valid_table_name(table):
                    self._logger.warning(f"Invalid table name: {table}")
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error validating database operation: {e}")
            return False
    
    def _is_valid_table_name(self, table_name: str) -> bool:
        """Validate table name against allowed tables"""
        # Define allowed tables based on our schema
        allowed_tables = {
            "users", "sessions", "plots", "authors", "world_building", 
            "characters", "orchestrator_decisions", "agent_invocations",
            "performance_metrics", "trace_events"
        }
        return table_name in allowed_tables
    
    async def execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Execute an MCP tool call with validation and logging"""
        execution_id = f"{agent_name}_{tool_name}_{id(parameters)}"
        
        try:
            # Validate the tool call
            if not self.validate_tool_call(tool_name, parameters, agent_name):
                return {
                    "success": False,
                    "error": "Tool call validation failed",
                    "execution_id": execution_id
                }
            
            # Log the execution attempt
            self._logger.info(f"Executing MCP tool {tool_name} for agent {agent_name}")
            
            # Execute the actual MCP tool
            # NOTE: In a real implementation, this would call the actual MCP server
            result = await self._execute_actual_mcp_tool(tool_name, parameters)
            
            # Log successful execution
            self._logger.info(f"MCP tool {tool_name} executed successfully")
            
            return {
                "success": True,
                "result": result,
                "execution_id": execution_id,
                "tool_name": tool_name
            }
            
        except Exception as e:
            self._logger.error(f"Error executing MCP tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id,
                "tool_name": tool_name
            }
    
    async def _execute_actual_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute the actual MCP tool - this would interface with MCP server"""
        # This is a placeholder implementation
        # In reality, this would interface with the MCP server through the appropriate protocol
        
        if tool_name == "mcp__supabase__list_tables":
            return {
                "tables": [
                    "users", "sessions", "plots", "authors", "world_building", 
                    "characters", "orchestrator_decisions", "agent_invocations"
                ]
            }
        elif tool_name == "mcp__supabase__describe_table":
            table = parameters.get("table")
            return {
                "table": table,
                "columns": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "created_at", "type": "timestamp"},
                    {"name": "updated_at", "type": "timestamp"}
                ]
            }
        elif tool_name == "mcp__supabase__query":
            query = parameters.get("query")
            # This would execute the actual query through MCP
            return {
                "rows": [],
                "count": 0,
                "query": query
            }
        else:
            # Placeholder for other tools
            return {"status": "executed", "tool": tool_name, "parameters": parameters}


# Factory function
def create_mcp_tool_manager(config: IConfiguration) -> MCPToolManager:
    """Create MCP tool manager instance"""
    return MCPToolManager(config)