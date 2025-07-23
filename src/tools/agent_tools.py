"""
Agent coordination tools for orchestrator and workflow management
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
from functools import wraps

# Google ADK uses simple functions as tools

from ..core.container import get_container

logger = logging.getLogger(__name__)


# Global workflow context storage (in production, use Redis or similar)
WORKFLOW_CONTEXTS = {}


def async_tool(func):
    """Decorator to handle async functions in tool context"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Try to get the current running loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, schedule coroutine
            return asyncio.ensure_future(func(*args, **kwargs))
        except RuntimeError:
            # No running loop, create one
            return asyncio.run(func(*args, **kwargs))
    return wrapper


@async_tool
async def invoke_agent(
    agent_name: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invoke another agent in the workflow
    
    Args:
        agent_name: Name of the agent to invoke
        message: Message to send to the agent
        context: Optional context to pass to the agent
        workflow_id: Optional workflow ID for context tracking
        
    Returns:
        Dict containing the agent's response
    """
    try:
        container = get_container()
        agent_factory = container.agent_factory()
        
        # Get or create the agent
        agent = agent_factory.get_agent(agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "message": f"Failed to invoke agent '{agent_name}'"
            }
        
        # Prepare the full message with context
        full_message = message
        if context:
            context_str = "\n\nCONTEXT:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            full_message = message + context_str
        
        # If workflow_id provided, update global context
        if workflow_id and context:
            if workflow_id not in WORKFLOW_CONTEXTS:
                WORKFLOW_CONTEXTS[workflow_id] = {}
            WORKFLOW_CONTEXTS[workflow_id].update(context)
        
        # Process the request
        logger.info(f"Invoking agent '{agent_name}' with message: {message[:100]}...")
        response = await agent.process_request(full_message)
        
        # Extract structured data if available
        result = {
            "success": True,
            "agent_name": agent_name,
            "response": response.content,
            "metadata": {}
        }
        
        # If agent returned structured data, include it
        if hasattr(response, 'parsed_json') and response.parsed_json:
            result["structured_data"] = response.parsed_json
            
            # Update workflow context with any returned IDs
            if workflow_id:
                for key in ['plot_id', 'author_id', 'world_building_id', 'characters_id']:
                    if key in response.parsed_json:
                        WORKFLOW_CONTEXTS[workflow_id][key] = response.parsed_json[key]
        
        # If agent performed tool calls, include that info
        if hasattr(response, 'tool_calls') and response.tool_calls:
            result["tool_calls"] = [
                {
                    "tool": tc.name,
                    "args": tc.args,
                    "result": tc.result
                }
                for tc in response.tool_calls
            ]
        
        logger.info(f"Agent '{agent_name}' invocation successful")
        return result
        
    except Exception as e:
        logger.error(f"Error invoking agent '{agent_name}': {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to invoke agent '{agent_name}'"
        }


@async_tool
async def get_agent_context(
    workflow_id: str,
    keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get workflow context for agents to share data
    
    Args:
        workflow_id: The workflow ID
        keys: Optional list of specific keys to retrieve
        
    Returns:
        Dict containing the requested context
    """
    try:
        if workflow_id not in WORKFLOW_CONTEXTS:
            return {
                "success": True,
                "context": {},
                "message": "No context found for this workflow"
            }
        
        context = WORKFLOW_CONTEXTS[workflow_id]
        
        # Filter to specific keys if requested
        if keys:
            filtered_context = {k: v for k, v in context.items() if k in keys}
        else:
            filtered_context = context.copy()
        
        return {
            "success": True,
            "context": filtered_context,
            "workflow_id": workflow_id
        }
        
    except Exception as e:
        logger.error(f"Error getting agent context: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get agent context"
        }


@async_tool
async def update_workflow_context(
    workflow_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update workflow context with new data
    
    Args:
        workflow_id: The workflow ID
        updates: Dictionary of updates to apply
        
    Returns:
        Dict confirming the update
    """
    try:
        if workflow_id not in WORKFLOW_CONTEXTS:
            WORKFLOW_CONTEXTS[workflow_id] = {}
        
        WORKFLOW_CONTEXTS[workflow_id].update(updates)
        
        logger.info(f"Updated workflow context for '{workflow_id}' with keys: {list(updates.keys())}")
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "updated_keys": list(updates.keys()),
            "message": "Workflow context updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating workflow context: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update workflow context"
        }


@async_tool
async def list_available_agents() -> Dict[str, Any]:
    """
    List all available agents in the system
    
    Returns:
        Dict containing list of available agents
    """
    try:
        container = get_container()
        agent_factory = container.agent_factory()
        
        # Get registered agents
        agents = agent_factory.list_agents()
        
        agent_info = []
        for agent_name in agents:
            agent = agent_factory.get_agent(agent_name)
            if agent:
                agent_info.append({
                    "name": agent_name,
                    "description": getattr(agent, '_description', 'No description available'),
                    "available": True
                })
        
        return {
            "success": True,
            "agents": agent_info,
            "count": len(agent_info)
        }
        
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list available agents"
        }


# Google ADK uses simple functions as tools
# The functions above are the actual tools that agents can use
