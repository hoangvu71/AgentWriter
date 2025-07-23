"""
Repository for orchestrator decision tracking and routing logs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..database.supabase_adapter import SupabaseAdapter
from ..core.logging import get_logger


class OrchestratorRepository:
    """Repository for orchestrator decision tracking and analysis"""
    
    def __init__(self, database: SupabaseAdapter):
        self._database = database
        self._logger = get_logger("orchestrator_repository")
    
    async def save_decision(self, session_id: str, user_id: str, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save orchestrator routing decision for analysis and debugging.
        
        Args:
            session_id: Session identifier
            user_id: User identifier  
            decision_data: Orchestrator decision details
            
        Returns:
            Dictionary containing the saved decision record
        """
        try:
            # Prepare decision record
            decision_record = {
                "session_id": session_id,
                "user_id": user_id,
                "request_content": decision_data.get("request_content", ""),
                "routing_decision": decision_data.get("routing_decision", ""),
                "agents_selected": decision_data.get("agents_selected", []),
                "reasoning": decision_data.get("reasoning", ""),
                "confidence_score": decision_data.get("confidence_score", 0.0),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save to orchestrator_decisions table
            response = await self._database.insert("orchestrator_decisions", decision_record)
            
            self._logger.info(f"Saved orchestrator decision for session {session_id}")
            return response
            
        except Exception as e:
            self._logger.error(f"Error saving orchestrator decision: {e}", error=e)
            raise
    
    async def get_decisions_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all orchestrator decisions for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of orchestrator decisions for the session
        """
        try:
            decisions = await self._database.select(
                "orchestrator_decisions",
                filters={"session_id": session_id},
                order_by="created_at"
            )
            
            return decisions
            
        except Exception as e:
            self._logger.error(f"Error getting decisions for session {session_id}: {e}", error=e)
            raise
    
    async def get_routing_analytics(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get analytics on orchestrator routing patterns.
        
        Args:
            limit: Maximum number of recent decisions to analyze
            
        Returns:
            Dictionary containing routing analytics
        """
        try:
            # Get recent decisions
            recent_decisions = await self._database.select(
                "orchestrator_decisions",
                order_by="created_at",
                desc=True,
                limit=limit
            )
            
            # Analyze patterns
            agent_usage = {}
            total_decisions = len(recent_decisions)
            confidence_scores = []
            
            for decision in recent_decisions:
                agents = decision.get("agents_selected", [])
                confidence = decision.get("confidence_score", 0.0)
                
                # Count agent usage
                for agent in agents:
                    agent_usage[agent] = agent_usage.get(agent, 0) + 1
                
                # Collect confidence scores
                if confidence > 0:
                    confidence_scores.append(confidence)
            
            # Calculate statistics
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return {
                "total_decisions": total_decisions,
                "agent_usage_patterns": agent_usage,
                "average_confidence": round(avg_confidence, 2),
                "confidence_distribution": {
                    "high_confidence": len([s for s in confidence_scores if s >= 0.8]),
                    "medium_confidence": len([s for s in confidence_scores if 0.5 <= s < 0.8]),
                    "low_confidence": len([s for s in confidence_scores if s < 0.5])
                }
            }
            
        except Exception as e:
            self._logger.error(f"Error getting routing analytics: {e}", error=e)
            raise