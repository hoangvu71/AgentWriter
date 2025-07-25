"""
Agent coordination tools for orchestrator and workflow management
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import time
import threading
from threading import Lock

# Google ADK uses simple functions as tools

from ..core.container import get_container
from ..core.safe_async_runner import run_async_safe

logger = logging.getLogger(__name__)


class TTLCache:
    """Thread-safe cache with time-to-live cleanup to prevent memory leaks"""
    
    def __init__(self, ttl_seconds: int = 1800):  # 30 minutes default
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl_seconds
        self._lock = Lock()
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._periodic_cleanup, 
                daemon=True
            )
            self._cleanup_thread.start()
    
    def _periodic_cleanup(self):
        """Periodically clean up expired entries"""
        while not self._stop_cleanup.wait(300):  # Check every 5 minutes
            try:
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Error in TTL cache cleanup: {e}")
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        now = time.time()
        with self._lock:
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if now - timestamp > self._ttl
            ]
            for key in expired_keys:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired workflow contexts")
    
    def set(self, key: str, value: Any):
        """Set a value in the cache with current timestamp"""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def get(self, key: str, default=None):
        """Get a value from cache, None if expired or not found"""
        now = time.time()
        with self._lock:
            if key not in self._cache:
                return default
            if now - self._timestamps.get(key, 0) > self._ttl:
                # Expired, remove it
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
                return default
            return self._cache[key]
    
    def update(self, key: str, updates: Dict[str, Any]):
        """Update existing cache entry with new values"""
        with self._lock:
            if key not in self._cache:
                self._cache[key] = {}
            self._cache[key].update(updates)
            self._timestamps[key] = time.time()
    
    def contains(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None
    
    def __contains__(self, key: str) -> bool:
        return self.contains(key)
    
    def cleanup(self):
        """Manual cleanup and shutdown"""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1)
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


# Workflow context storage with automatic cleanup (prevents memory leaks)
WORKFLOW_CONTEXTS = TTLCache(ttl_seconds=1800)  # 30 minutes TTL


def invoke_agent(
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
        
        # Merge workflow context with provided context
        merged_context = {}
        if workflow_id:
            stored_context = WORKFLOW_CONTEXTS.get(workflow_id, {})
            merged_context.update(stored_context)
        if context:
            merged_context.update(context)
        
        # Prepare the full message with merged context
        full_message = message
        if merged_context:
            context_str = "\n\nCONTEXT:\n"
            for key, value in merged_context.items():
                context_str += f"- {key}: {value}\n"
            full_message = message + context_str
        
        # Update global workflow context
        if workflow_id and context:
            WORKFLOW_CONTEXTS.update(workflow_id, context)
        
        # Create proper AgentRequest object
        from ..core.interfaces import AgentRequest
        import uuid
        
        # Generate user_id and session_id if not provided in merged context
        # Use proper UUID format for Supabase compatibility
        user_id = merged_context.get('user_id', str(uuid.uuid4()))
        session_id = merged_context.get('session_id', str(uuid.uuid4()))
        
        agent_request = AgentRequest(
            content=full_message,
            user_id=user_id,
            session_id=session_id,
            context=merged_context
        )
        
        # Process the request synchronously using safe async runner
        logger.info(f"Invoking agent '{agent_name}' with message: {message[:100]}...")
        
        # Use safe async runner to prevent race conditions and event loop conflicts
        try:
            response = run_async_safe(agent.process_request(agent_request), timeout=30.0)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Agent '{agent_name}' execution failed"
            }
        
        # Extract structured data if available
        result = {
            "success": True,
            "agent_name": agent_name,
            "response": response.content,
            "metadata": response.metadata if hasattr(response, 'metadata') else {}
        }
        
        # If agent returned structured data, include it
        if hasattr(response, 'parsed_json') and response.parsed_json:
            result["structured_data"] = response.parsed_json
            
            # Update workflow context with any returned IDs
            if workflow_id:
                context_updates = {}
                for key in ['plot_id', 'author_id', 'world_building_id', 'characters_id']:
                    if key in response.parsed_json:
                        context_updates[key] = response.parsed_json[key]
                if context_updates:
                    WORKFLOW_CONTEXTS.update(workflow_id, context_updates)
        
        # Also check metadata for IDs (where they're usually stored)
        if hasattr(response, 'metadata') and response.metadata and workflow_id:
            context_updates = {}
            for key in ['plot_id', 'author_id', 'world_building_id', 'characters_id']:
                if key in response.metadata:
                    context_updates[key] = response.metadata[key]
            if context_updates:
                WORKFLOW_CONTEXTS.update(workflow_id, context_updates)
        
        # If agent performed tool calls, include that info and extract IDs
        if hasattr(response, 'tool_calls') and response.tool_calls:
            result["tool_calls"] = [
                {
                    "tool": tc.name,
                    "args": tc.args,
                    "result": tc.result
                }
                for tc in response.tool_calls
            ]
            
            # Extract IDs from tool call results for workflow context
            if workflow_id:
                context_updates = {}
                for tc in response.tool_calls:
                    if hasattr(tc, 'result') and isinstance(tc.result, dict):
                        # Extract IDs from tool results
                        if tc.name == "save_plot" and "plot_id" in tc.result:
                            context_updates["plot_id"] = tc.result["plot_id"]
                        elif tc.name == "save_author" and "author_id" in tc.result:
                            context_updates["author_id"] = tc.result["author_id"]
                        elif tc.name == "save_world_building" and "world_building_id" in tc.result:
                            context_updates["world_building_id"] = tc.result["world_building_id"]
                        elif tc.name == "save_characters" and "characters_id" in tc.result:
                            context_updates["characters_id"] = tc.result["characters_id"]
                if context_updates:
                    WORKFLOW_CONTEXTS.update(workflow_id, context_updates)
        
        logger.info(f"Agent '{agent_name}' invocation successful")
        return result
        
    except Exception as e:
        logger.error(f"Error invoking agent '{agent_name}': {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to invoke agent '{agent_name}'"
        }


def get_agent_context(
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
        context = WORKFLOW_CONTEXTS.get(workflow_id, {})
        if not context:
            return {
                "success": True,
                "context": {},
                "message": "No context found for this workflow"
            }
        
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


def update_workflow_context(
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
        WORKFLOW_CONTEXTS.update(workflow_id, updates)
        
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


def list_available_agents() -> Dict[str, Any]:
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
