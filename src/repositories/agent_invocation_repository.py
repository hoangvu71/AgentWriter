"""
Repository for agent invocation tracking and observability data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from ..core.interfaces import IDatabase
from ..core.logging import get_logger
from ..core.agent_tracker import AgentInvocation

logger = get_logger("agent_invocation_repository")


class AgentInvocationRepository(BaseRepository):
    """Repository for agent invocation tracking and performance analytics"""
    
    def __init__(self, database: IDatabase):
        super().__init__(database, "agent_invocations")
    
    def _serialize(self, invocation: AgentInvocation) -> Dict[str, Any]:
        """Convert AgentInvocation to database format"""
        return {
            "invocation_id": invocation.invocation_id,
            "agent_name": invocation.agent_name,
            "user_id": invocation.user_id,
            "session_id": invocation.session_id,
            "request_content": invocation.request_content,
            "request_context": invocation.request_context,
            "start_time": invocation.start_time.isoformat() if invocation.start_time else None,
            "end_time": invocation.end_time.isoformat() if invocation.end_time else None,
            "duration_ms": invocation.duration_ms,
            "llm_model": invocation.llm_model,
            "final_prompt": invocation.final_prompt,
            "raw_response": invocation.raw_response,
            "prompt_tokens": invocation.prompt_tokens,
            "completion_tokens": invocation.completion_tokens,
            "total_tokens": invocation.total_tokens,
            "tool_calls": invocation.tool_calls or [],
            "tool_results": invocation.tool_results or [],
            "latency_ms": invocation.latency_ms,
            "cost_estimate": invocation.cost_estimate,
            "success": invocation.success,
            "error_message": invocation.error_message,
            "response_content": invocation.response_content,
            "parsed_json": invocation.parsed_json
        }
    
    def _deserialize(self, data: Dict[str, Any]) -> AgentInvocation:
        """Convert database data to AgentInvocation"""
        return AgentInvocation(
            invocation_id=data["invocation_id"],
            agent_name=data["agent_name"],
            user_id=data["user_id"],
            session_id=data["session_id"],
            request_content=data["request_content"],
            request_context=data.get("request_context"),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration_ms=data.get("duration_ms"),
            llm_model=data.get("llm_model"),
            final_prompt=data.get("final_prompt"),
            raw_response=data.get("raw_response"),
            prompt_tokens=data.get("prompt_tokens"),
            completion_tokens=data.get("completion_tokens"),
            total_tokens=data.get("total_tokens"),
            tool_calls=data.get("tool_calls", []),
            tool_results=data.get("tool_results", []),
            latency_ms=data.get("latency_ms"),
            cost_estimate=data.get("cost_estimate"),
            success=data.get("success", False),
            error_message=data.get("error_message"),
            response_content=data.get("response_content"),
            parsed_json=data.get("parsed_json")
        )
    
    async def save_invocation(self, invocation: AgentInvocation) -> str:
        """Save an agent invocation record"""
        try:
            data = self._serialize(invocation)
            result = await self._database.insert(self._table_name, data)
            
            self._logger.info(f"Saved invocation {invocation.invocation_id} for agent {invocation.agent_name}")
            return result.get("id") if isinstance(result, dict) else str(result)
            
        except Exception as e:
            self._logger.error(f"Error saving invocation {invocation.invocation_id}: {e}")
            raise
    
    async def get_invocation_by_id(self, invocation_id: str) -> Optional[AgentInvocation]:
        """Get a specific invocation by its ID"""
        try:
            results = await self._database.select(
                self._table_name,
                filters={"invocation_id": invocation_id},
                limit=1
            )
            
            if results:
                return self._deserialize(results[0])
            return None
            
        except Exception as e:
            self._logger.error(f"Error getting invocation {invocation_id}: {e}")
            raise
    
    async def get_agent_invocations(self, agent_name: str, limit: int = 100) -> List[AgentInvocation]:
        """Get recent invocations for a specific agent"""
        try:
            results = await self._database.select(
                self._table_name,
                filters={"agent_name": agent_name},
                order_by="start_time",
                desc=True,
                limit=limit
            )
            
            return [self._deserialize(row) for row in results]
            
        except Exception as e:
            self._logger.error(f"Error getting invocations for agent {agent_name}: {e}")
            raise
    
    async def get_session_invocations(self, session_id: str) -> List[AgentInvocation]:
        """Get all invocations for a specific session"""
        try:
            results = await self._database.select(
                self._table_name,
                filters={"session_id": session_id},
                order_by="start_time"
            )
            
            return [self._deserialize(row) for row in results]
            
        except Exception as e:
            self._logger.error(f"Error getting invocations for session {session_id}: {e}")
            raise
    
    async def get_performance_analytics(self, agent_name: str = None, 
                                      hours: int = 24) -> Dict[str, Any]:
        """Get performance analytics for agents"""
        try:
            # Build query filters
            filters = {}
            if agent_name:
                filters["agent_name"] = agent_name
            
            # Time range filter
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # For SQLite, we'll use a simple approach
            # For production, consider using raw SQL for complex analytics
            results = await self._database.select(
                self._table_name,
                filters=filters,
                order_by="start_time",
                desc=True,
                limit=1000
            )
            
            # Filter by time (basic approach)
            recent_results = [
                row for row in results 
                if row.get("start_time") and 
                datetime.fromisoformat(row["start_time"]) >= since_time
            ]
            
            if not recent_results:
                return {"total_invocations": 0, "timeframe_hours": hours}
            
            # Calculate analytics
            total_invocations = len(recent_results)
            successful_invocations = len([r for r in recent_results if r.get("success")])
            success_rate = successful_invocations / total_invocations if total_invocations > 0 else 0
            
            # Duration statistics
            durations = [r["duration_ms"] for r in recent_results if r.get("duration_ms")]
            avg_duration = sum(durations) / len(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            
            # Token statistics
            tokens = [r["total_tokens"] for r in recent_results if r.get("total_tokens")]
            total_tokens = sum(tokens) if tokens else 0
            avg_tokens = total_tokens / len(tokens) if tokens else 0
            
            # Cost statistics
            costs = [r["cost_estimate"] for r in recent_results if r.get("cost_estimate")]
            total_cost = sum(costs) if costs else 0
            
            # Agent usage patterns
            agent_usage = {}
            for result in recent_results:
                agent = result["agent_name"]
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
            
            # Tool usage patterns
            tool_usage = {}
            for result in recent_results:
                tool_calls = result.get("tool_calls", [])
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "unknown")
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
            # Recent errors
            recent_errors = [
                {
                    "invocation_id": r["invocation_id"],
                    "agent": r["agent_name"],
                    "error": r["error_message"],
                    "timestamp": r["start_time"]
                }
                for r in recent_results[-20:] 
                if not r.get("success") and r.get("error_message")
            ]
            
            return {
                "timeframe_hours": hours,
                "total_invocations": total_invocations,
                "success_rate": round(success_rate, 3),
                "performance": {
                    "avg_duration_ms": round(avg_duration, 2),
                    "max_duration_ms": max_duration,
                    "min_duration_ms": min_duration
                },
                "token_usage": {
                    "total_tokens": total_tokens,
                    "avg_tokens_per_invocation": round(avg_tokens, 2)
                },
                "cost_analysis": {
                    "total_cost_usd": round(total_cost, 4),
                    "avg_cost_per_invocation": round(total_cost / total_invocations, 6) if total_invocations > 0 else 0
                },
                "agent_usage_patterns": agent_usage,
                "tool_usage_patterns": tool_usage,
                "recent_errors": recent_errors
            }
            
        except Exception as e:
            self._logger.error(f"Error getting performance analytics: {e}")
            raise
    
    async def save_performance_metric(self, metric_name: str, value: float, 
                                    tags: Dict[str, str] = None, 
                                    agent_name: str = None, user_id: str = None, 
                                    session_id: str = None) -> str:
        """Save a performance metric"""
        try:
            data = {
                "metric_name": metric_name,
                "metric_value": value,
                "tags": tags or {},
                "agent_name": agent_name,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self._database.insert("performance_metrics", data)
            return result.get("id") if isinstance(result, dict) else str(result)
            
        except Exception as e:
            self._logger.error(f"Error saving performance metric {metric_name}: {e}")
            raise
    
    async def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed error analysis"""
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            results = await self._database.select(
                self._table_name,
                filters={"success": False},
                order_by="start_time",
                desc=True,
                limit=500
            )
            
            # Filter by time
            recent_errors = [
                row for row in results 
                if row.get("start_time") and 
                datetime.fromisoformat(row["start_time"]) >= since_time
            ]
            
            if not recent_errors:
                return {"total_errors": 0, "timeframe_hours": hours}
            
            # Error pattern analysis
            error_patterns = {}
            agent_errors = {}
            
            for error in recent_errors:
                error_msg = error.get("error_message", "Unknown error")
                agent_name = error["agent_name"]
                
                # Count error patterns
                error_patterns[error_msg] = error_patterns.get(error_msg, 0) + 1
                
                # Count errors by agent
                agent_errors[agent_name] = agent_errors.get(agent_name, 0) + 1
            
            return {
                "timeframe_hours": hours,
                "total_errors": len(recent_errors),
                "error_patterns": dict(sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
                "errors_by_agent": agent_errors,
                "recent_errors": [
                    {
                        "invocation_id": e["invocation_id"],
                        "agent": e["agent_name"],
                        "error": e["error_message"],
                        "timestamp": e["start_time"],
                        "request_preview": e["request_content"][:100] + "..." if len(e["request_content"]) > 100 else e["request_content"]
                    }
                    for e in recent_errors[:20]
                ]
            }
            
        except Exception as e:
            self._logger.error(f"Error getting error analysis: {e}")
            raise