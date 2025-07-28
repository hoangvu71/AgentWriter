"""
Agent Tool Manager for BaseAgent refactoring.

This module handles tool validation, execution, and serialization
cleaning with clear single responsibility.
"""

from typing import Dict, Any, List, Optional
import asyncio
from concurrent.futures import Future

from ..interfaces import AgentRequest
from ..logging import get_logger


class AgentToolManager:
    """
    Manages agent tool validation, execution, and serialization.
    
    Responsibilities:
    - Tool call validation and filtering
    - Tool execution and result handling
    - Serialization cleaning for tool calls and results
    - Error handling for tool execution failures
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize agent tool manager.
        
        Args:
            agent_name: Name of the agent for logging
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name}.tool_manager")
        
        # Valid tool names that agents can call
        self.valid_tools = {
            'save_plot', 'save_author', 'save_world_building', 'save_characters',
            'get_plot', 'get_author', 'list_plots', 'list_authors',
            'invoke_agent', 'get_agent_context', 'update_workflow_context',
            'search_content'
        }
        
        # Malformed patterns to reject
        self.malformed_patterns = [
            'print', 'console.log', 'str', 'uuid.uuid4', 'eval', 'exec',
            'import', 'from', 'def', 'class', 'return', 'print(str(uuid.uuid4()))',
            'workflow_id', 'generated workflow id'
        ]
    
    def is_valid_tool_call(self, function_name: str) -> bool:
        """
        Validate that a function call is a legitimate tool call and not malformed instruction text.
        
        Args:
            function_name: Name of the function to validate
            
        Returns:
            True if valid tool call, False otherwise
        """
        # Check if it's a known valid tool
        if function_name in self.valid_tools:
            return True
        
        # Check for multi-line code blocks (ADK sometimes treats instruction examples as function calls)
        if '\n' in function_name:
            function_lower = function_name.lower()
            # Multi-line patterns that are definitely not valid function calls
            if any(pattern in function_lower for pattern in ['import uuid', 'workflow_id =', 'print(f"']):
                self.logger.warning(f"Detected multi-line code block as function call: {function_name[:150]}...")
                return False
        
        # Check for malformed patterns
        for pattern in self.malformed_patterns:
            if pattern in function_name.lower():
                self.logger.warning(f"Detected malformed function call pattern '{pattern}' in '{function_name}'")
                return False
        
        # If it's not in our valid list and doesn't match malformed patterns,
        # log it for investigation but allow it (could be a new tool)
        self.logger.info(f"Unknown tool call detected: '{function_name}' - allowing but monitoring")
        return True
    
    async def execute_tool(self, tool_call, request: AgentRequest) -> Optional[Dict[str, Any]]:
        """
        Execute a tool call dynamically.
        
        Args:
            tool_call: Tool call object with name and arguments
            request: Original agent request for context
            
        Returns:
            Tool execution result or None if execution failed
        """
        try:
            # Add session context to tool args if not present
            tool_args = dict(tool_call.args)
            if 'session_id' not in tool_args:
                tool_args['session_id'] = request.session_id
            if 'user_id' not in tool_args:
                tool_args['user_id'] = request.user_id
            
            # Map of tool names to functions
            tool_map = {
                'save_plot': 'save_plot',
                'save_author': 'save_author',
                'save_world_building': 'save_world_building',
                'save_characters': 'save_characters',
                'get_plot': 'get_plot',
                'get_author': 'get_author',
                'list_plots': 'list_plots',
                'list_authors': 'list_authors',
                'invoke_agent': 'invoke_agent',
                'get_agent_context': 'get_agent_context',
                'update_workflow_context': 'update_workflow_context'
            }
            
            # Get the tool function
            tool_func_name = tool_map.get(tool_call.name)
            if not tool_func_name:
                self.logger.warning(f"Unknown tool: {tool_call.name}")
                return None
            
            # Import and execute the tool
            if tool_call.name.startswith('save_') or tool_call.name in ['get_plot', 'get_author', 'list_plots', 'list_authors']:
                from ...tools import writing_tools
                tool_func = getattr(writing_tools, tool_func_name)
            else:
                from ...tools import agent_tools
                tool_func = getattr(agent_tools, tool_func_name)
            
            # Execute the tool
            result = await tool_func(**tool_args)
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_call.name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to execute tool {tool_call.name}"
            }
    
    def is_serializable(self, obj) -> bool:
        """
        Check if an object can be serialized.
        
        Args:
            obj: Object to check for serializability
            
        Returns:
            True if object is serializable, False otherwise
        """
        # Check for common non-serializable types
        if isinstance(obj, (asyncio.Task, asyncio.Future, Future)):
            return False
        if hasattr(obj, '__call__') and not isinstance(obj, type):
            return False  # Functions/methods
        if isinstance(obj, type):
            return False  # Classes
            
        # Try basic serialization test for complex objects
        try:
            import json
            json.dumps(obj, default=str)
            return True
        except (TypeError, ValueError):
            return False
    
    def clean_tool_calls_for_serialization(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Clean tool calls to ensure they are serializable and prevent data loss.
        
        Args:
            tool_calls: List of tool call dictionaries
            
        Returns:
            Cleaned list of serializable tool calls
        """
        serializable_tool_calls = []
        
        for i, tc in enumerate(tool_calls):
            try:
                clean_tc = {}
                
                # Process each field in the tool call
                for key, value in tc.items():
                    if key in ['tool', 'name']:
                        # Tool name should always be a string
                        clean_tc[key] = str(value) if value is not None else 'unknown'
                    
                    elif key in ['args', 'arguments']:
                        # Arguments should be a dict, clean recursively
                        if isinstance(value, dict):
                            clean_tc[key] = self._clean_dict_for_serialization(value)
                        else:
                            clean_tc[key] = str(value) if value is not None else {}
                    
                    elif key == 'result':
                        # Results are critical - preserve as much as possible
                        if isinstance(value, dict):
                            clean_tc[key] = self._clean_dict_for_serialization(value)
                        elif self.is_serializable(value):
                            clean_tc[key] = value
                        else:
                            # Convert non-serializable results to structured info
                            clean_tc[key] = {
                                'success': True,  # Assume success if we got a result
                                'type': type(value).__name__,
                                'value': str(value)[:500],  # Truncate long values
                                'serialization_note': 'Value converted to string due to serialization issues'
                            }
                    
                    else:
                        # Handle other fields
                        if self.is_serializable(value):
                            clean_tc[key] = value
                        else:
                            clean_tc[key] = str(value) if value is not None else None
                
                # Ensure required fields exist
                if 'tool' not in clean_tc and 'name' not in clean_tc:
                    clean_tc['tool'] = f'unknown_tool_{i}'
                
                if 'result' not in clean_tc:
                    clean_tc['result'] = {'success': True, 'message': 'Tool executed (result not captured)'}
                
                serializable_tool_calls.append(clean_tc)
                
            except Exception as clean_error:
                self.logger.error(f"Failed to clean tool call {i}: {clean_error}")
                # Create minimal fallback tool call
                fallback_tc = {
                    'tool': f'tool_{i}',
                    'result': {
                        'success': False,
                        'error': f'Serialization failed: {str(clean_error)[:200]}',
                        'original_data_available': False
                    },
                    'serialization_error': str(clean_error)
                }
                serializable_tool_calls.append(fallback_tc)
        
        return serializable_tool_calls
    
    def _clean_dict_for_serialization(self, data: Dict) -> Dict:
        """
        Recursively clean a dictionary for serialization.
        
        Args:
            data: Dictionary to clean
            
        Returns:
            Cleaned dictionary
        """
        clean_dict = {}
        
        for key, value in data.items():
            try:
                # Convert key to string if needed
                str_key = str(key)
                
                if isinstance(value, dict):
                    clean_dict[str_key] = self._clean_dict_for_serialization(value)
                elif isinstance(value, (list, tuple)):
                    clean_dict[str_key] = self._clean_list_for_serialization(value)
                elif self.is_serializable(value):
                    clean_dict[str_key] = value
                else:
                    # Convert non-serializable values to safe representation
                    clean_dict[str_key] = {
                        'type': type(value).__name__,
                        'value': str(value)[:200],  # Truncate to prevent huge strings
                        'serializable': False
                    }
                    
            except Exception as e:
                # If we can't process this key-value pair, create a safe fallback
                safe_key = str(key) if key is not None else 'unknown_key'
                clean_dict[safe_key] = f'<serialization_error: {str(e)[:100]}>'
        
        return clean_dict
    
    def _clean_list_for_serialization(self, data: List) -> List:
        """
        Clean a list for serialization.
        
        Args:
            data: List to clean
            
        Returns:
            Cleaned list
        """
        clean_list = []
        
        for item in data:
            try:
                if isinstance(item, dict):
                    clean_list.append(self._clean_dict_for_serialization(item))
                elif isinstance(item, (list, tuple)):
                    clean_list.append(self._clean_list_for_serialization(item))
                elif self.is_serializable(item):
                    clean_list.append(item)
                else:
                    clean_list.append(str(item)[:100])  # Truncate long items
            except Exception:
                clean_list.append('<item_serialization_error>')
        
        return clean_list