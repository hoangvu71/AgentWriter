"""
Agent invocation tracking and performance monitoring.
Provides detailed logging of individual agent calls, LLM interactions, and tool usage.
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from .observability import get_observability_manager
from .logging import get_logger

logger = get_logger("agent_tracker")


@dataclass
class AgentInvocation:
    """Detailed record of an agent invocation"""
    invocation_id: str
    agent_name: str
    user_id: str
    session_id: str
    
    # Request details
    request_content: str
    request_context: Optional[Dict[str, Any]]
    
    # Execution details
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # LLM interaction details
    llm_model: Optional[str] = None
    final_prompt: Optional[str] = None
    raw_response: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Tool usage details
    tool_calls: List[Dict[str, Any]] = None
    tool_results: List[Dict[str, Any]] = None
    
    # Performance metrics
    latency_ms: Optional[float] = None
    cost_estimate: Optional[float] = None
    
    # Result details
    success: bool = False
    error_message: Optional[str] = None
    response_content: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
        if self.tool_results is None:
            self.tool_results = []


class AgentTracker:
    """Tracks detailed agent invocations and performance metrics"""
    
    def __init__(self):
        self.observability = get_observability_manager()
        self.active_invocations: Dict[str, AgentInvocation] = {}
        self.invocation_history: List[AgentInvocation] = []
        self.max_history_size = 1000
        
        logger.info("Agent tracker initialized")
    
    def start_invocation(self, invocation_id: str, agent_name: str, user_id: str, 
                        session_id: str, request_content: str, 
                        request_context: Optional[Dict[str, Any]] = None) -> AgentInvocation:
        """Start tracking an agent invocation"""
        
        invocation = AgentInvocation(
            invocation_id=invocation_id,
            agent_name=agent_name,
            user_id=user_id,
            session_id=session_id,
            request_content=request_content,
            request_context=request_context,
            start_time=datetime.utcnow()
        )
        
        self.active_invocations[invocation_id] = invocation
        
        # Start tracing span
        span = self.observability.trace_agent_execution(
            agent_name, user_id, session_id, request_content
        )
        
        logger.info(f"Started tracking invocation {invocation_id} for agent {agent_name}")
        return invocation
    
    def record_llm_interaction(self, invocation_id: str, model: str, prompt: str, 
                             response: str, prompt_tokens: int = None, 
                             completion_tokens: int = None, latency_ms: float = None):
        """Record LLM interaction details"""
        
        if invocation_id not in self.active_invocations:
            logger.warning(f"No active invocation found for {invocation_id}")
            return
        
        invocation = self.active_invocations[invocation_id]
        invocation.llm_model = model
        invocation.final_prompt = prompt
        invocation.raw_response = response
        invocation.prompt_tokens = prompt_tokens
        invocation.completion_tokens = completion_tokens
        invocation.total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)
        invocation.latency_ms = latency_ms
        
        # Record performance metrics
        if latency_ms:
            self.observability.record_performance_metric(
                "llm_latency_ms", latency_ms, 
                {"agent": invocation.agent_name, "model": model}
            )
        
        if invocation.total_tokens:
            self.observability.record_performance_metric(
                "llm_tokens_total", invocation.total_tokens,
                {"agent": invocation.agent_name, "model": model}
            )
        
        # Estimate cost (rough estimates for common models)
        if invocation.total_tokens:
            cost = self._estimate_llm_cost(model, prompt_tokens or 0, completion_tokens or 0)
            invocation.cost_estimate = cost
            
            if cost:
                self.observability.record_performance_metric(
                    "llm_cost_usd", cost,
                    {"agent": invocation.agent_name, "model": model}
                )
        
        logger.debug(f"Recorded LLM interaction for {invocation_id}: {invocation.total_tokens} tokens, {latency_ms}ms")
    
    def record_tool_usage(self, invocation_id: str, tool_calls: List[Dict[str, Any]], 
                         tool_results: List[Dict[str, Any]]):
        """Record tool usage details"""
        
        if invocation_id not in self.active_invocations:
            logger.warning(f"No active invocation found for {invocation_id}")
            return
        
        invocation = self.active_invocations[invocation_id]
        invocation.tool_calls = tool_calls
        invocation.tool_results = tool_results
        
        # Record tool usage metrics
        for tool_call in tool_calls:
            tool_name = tool_call.get('tool', 'unknown')
            self.observability.record_performance_metric(
                "tool_usage_count", 1,
                {"agent": invocation.agent_name, "tool": tool_name}
            )
        
        logger.debug(f"Recorded {len(tool_calls)} tool calls for {invocation_id}")
    
    def complete_invocation(self, invocation_id: str, success: bool = True, 
                           error_message: str = None, response_content: str = None,
                           parsed_json: Dict[str, Any] = None):
        """Complete an agent invocation"""
        
        if invocation_id not in self.active_invocations:
            logger.warning(f"No active invocation found for {invocation_id}")
            return
        
        invocation = self.active_invocations[invocation_id]
        invocation.end_time = datetime.utcnow()
        invocation.duration_ms = (invocation.end_time - invocation.start_time).total_seconds() * 1000
        invocation.success = success
        invocation.error_message = error_message
        invocation.response_content = response_content
        invocation.parsed_json = parsed_json
        
        # Record overall performance metrics
        self.observability.record_performance_metric(
            "agent_duration_ms", invocation.duration_ms,
            {"agent": invocation.agent_name, "success": str(success)}
        )
        
        # Move to history
        self.invocation_history.append(invocation)
        del self.active_invocations[invocation_id]
        
        # Maintain history size
        if len(self.invocation_history) > self.max_history_size:
            self.invocation_history = self.invocation_history[-self.max_history_size:]
        
        status = "completed" if success else "failed"
        logger.info(f"Invocation {invocation_id} {status} in {invocation.duration_ms:.1f}ms")
        
        return invocation
    
    def get_invocation_details(self, invocation_id: str) -> Optional[AgentInvocation]:
        """Get details of a specific invocation"""
        
        # Check active invocations
        if invocation_id in self.active_invocations:
            return self.active_invocations[invocation_id]
        
        # Check history
        for invocation in self.invocation_history:
            if invocation.invocation_id == invocation_id:
                return invocation
        
        return None
    
    def get_agent_performance(self, agent_name: str, limit: int = 100) -> Dict[str, Any]:
        """Get performance analytics for a specific agent"""
        
        # Get recent invocations for this agent
        agent_invocations = [
            inv for inv in self.invocation_history[-limit:] 
            if inv.agent_name == agent_name and inv.end_time is not None
        ]
        
        if not agent_invocations:
            return {"agent": agent_name, "invocations": 0}
        
        # Calculate performance metrics
        durations = [inv.duration_ms for inv in agent_invocations if inv.duration_ms]
        tokens = [inv.total_tokens for inv in agent_invocations if inv.total_tokens]
        costs = [inv.cost_estimate for inv in agent_invocations if inv.cost_estimate]
        
        success_count = len([inv for inv in agent_invocations if inv.success])
        tool_usage_count = sum(len(inv.tool_calls) for inv in agent_invocations)
        
        return {
            "agent": agent_name,
            "invocations": len(agent_invocations),
            "success_rate": success_count / len(agent_invocations) if agent_invocations else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "avg_tokens": sum(tokens) / len(tokens) if tokens else 0,
            "total_cost_usd": sum(costs) if costs else 0,
            "total_tool_calls": tool_usage_count,
            "recent_errors": [
                {"id": inv.invocation_id, "error": inv.error_message}
                for inv in agent_invocations[-10:] if not inv.success
            ]
        }
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a specific session"""
        
        session_invocations = [
            inv for inv in self.invocation_history 
            if inv.session_id == session_id and inv.end_time is not None
        ]
        
        if not session_invocations:
            return {"session_id": session_id, "invocations": 0}
        
        # Agent usage patterns
        agent_usage = {}
        for inv in session_invocations:
            agent_usage[inv.agent_name] = agent_usage.get(inv.agent_name, 0) + 1
        
        # Calculate session metrics
        total_duration = sum(inv.duration_ms for inv in session_invocations if inv.duration_ms)
        total_tokens = sum(inv.total_tokens for inv in session_invocations if inv.total_tokens)
        total_cost = sum(inv.cost_estimate for inv in session_invocations if inv.cost_estimate)
        
        return {
            "session_id": session_id,
            "invocations": len(session_invocations),
            "agents_used": agent_usage,
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "conversation_turns": len(set(inv.request_content for inv in session_invocations))
        }
    
    def _estimate_llm_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        """Estimate LLM API cost based on model and token usage"""
        
        # Rough cost estimates per 1K tokens (as of 2024)
        model_costs = {
            "gemini-1.5-flash": {"input": 0.075/1000, "output": 0.30/1000},
            "gemini-1.5-pro": {"input": 3.50/1000, "output": 10.50/1000},
            "gpt-4": {"input": 30.0/1000, "output": 60.0/1000},
            "gpt-3.5-turbo": {"input": 1.0/1000, "output": 2.0/1000},
        }
        
        # Find matching model (case insensitive, partial match)
        model_lower = model.lower()
        for cost_model, rates in model_costs.items():
            if cost_model.lower() in model_lower:
                input_cost = (prompt_tokens / 1000) * rates["input"]
                output_cost = (completion_tokens / 1000) * rates["output"]
                return input_cost + output_cost
        
        return None
    
    def export_invocation_data(self, invocation_id: str) -> Optional[Dict[str, Any]]:
        """Export detailed invocation data for debugging"""
        
        invocation = self.get_invocation_details(invocation_id)
        if not invocation:
            return None
        
        return asdict(invocation)


# Global agent tracker instance
_agent_tracker = None


def get_agent_tracker() -> AgentTracker:
    """Get the global agent tracker instance"""
    global _agent_tracker
    
    if _agent_tracker is None:
        _agent_tracker = AgentTracker()
    
    return _agent_tracker