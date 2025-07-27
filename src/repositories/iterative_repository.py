"""
Repository for iterative improvement operations (critique, enhancement, scoring).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..database.supabase_adapter import SupabaseAdapter
from ..core.logging import get_logger


class IterativeRepository:
    """Repository for critique, enhancement, and scoring operations"""
    
    def __init__(self, database: SupabaseAdapter):
        self._database = database
        self._logger = get_logger("iterative_repository")
    
    async def save_critique(self, iteration_id: str, critique_json: Dict[str, Any], agent_response: str) -> Dict[str, Any]:
        """
        Save critique analysis data.
        
        Args:
            iteration_id: Iteration identifier
            critique_json: Structured critique data
            agent_response: Raw agent response
            
        Returns:
            Dictionary containing the saved critique record
        """
        try:
            critique_record = {
                "iteration_id": iteration_id,
                "critique_data": critique_json,
                "agent_response": agent_response,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = await self._database.insert("critiques", critique_record)
            
            self._logger.info(f"Saved critique for iteration {iteration_id}")
            return response
            
        except Exception as e:
            self._logger.error(f"Error saving critique for iteration {iteration_id}: {e}", error=e)
            raise
    
    async def save_enhancement(self, iteration_id: str, enhanced_content: str, 
                             changes_made: Dict[str, Any], rationale: str, 
                             confidence_score: float) -> Dict[str, Any]:
        """
        Save enhancement data.
        
        Args:
            iteration_id: Iteration identifier
            enhanced_content: Improved content
            changes_made: Structured changes data
            rationale: Enhancement reasoning
            confidence_score: Enhancement confidence
            
        Returns:
            Dictionary containing the saved enhancement record
        """
        try:
            enhancement_record = {
                "iteration_id": iteration_id,
                "enhanced_content": enhanced_content,
                "changes_made": changes_made,
                "rationale": rationale,
                "confidence_score": confidence_score,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = await self._database.insert("enhancements", enhancement_record)
            
            self._logger.info(f"Saved enhancement for iteration {iteration_id}")
            return response
            
        except Exception as e:
            self._logger.error(f"Error saving enhancement for iteration {iteration_id}: {e}", error=e)
            raise
    
    async def save_score(self, iteration_id: str, overall_score: float, 
                        category_scores: Dict[str, Any], score_rationale: str, 
                        improvement_trajectory: str, recommendations: str) -> Dict[str, Any]:
        """
        Save scoring data.
        
        Args:
            iteration_id: Iteration identifier
            overall_score: Overall quality score
            category_scores: Detailed category scores
            score_rationale: Scoring reasoning
            improvement_trajectory: Improvement suggestions
            recommendations: Specific recommendations
            
        Returns:
            Dictionary containing the saved score record
        """
        try:
            score_record = {
                "iteration_id": iteration_id,
                "overall_score": overall_score,
                "category_scores": category_scores,
                "score_rationale": score_rationale,
                "improvement_trajectory": improvement_trajectory,
                "recommendations": recommendations,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = await self._database.insert("scores", score_record)
            
            self._logger.info(f"Saved score for iteration {iteration_id}")
            return response
            
        except Exception as e:
            self._logger.error(f"Error saving score for iteration {iteration_id}: {e}", error=e)
            raise
    
    async def get_iteration_history(self, iteration_id: str) -> Dict[str, Any]:
        """
        Get complete history for an iteration (critique, enhancement, scoring).
        
        Args:
            iteration_id: Iteration identifier
            
        Returns:
            Dictionary containing all iteration data
        """
        try:
            # Get all related records
            critiques = await self._database.select(
                "critiques",
                filters={"iteration_id": iteration_id},
                order_by="created_at"
            )
            
            enhancements = await self._database.select(
                "enhancements", 
                filters={"iteration_id": iteration_id},
                order_by="created_at"
            )
            
            scores = await self._database.select(
                "scores",
                filters={"iteration_id": iteration_id}, 
                order_by="created_at"
            )
            
            return {
                "iteration_id": iteration_id,
                "critiques": critiques,
                "enhancements": enhancements,
                "scores": scores,
                "total_operations": len(critiques) + len(enhancements) + len(scores)
            }
            
        except Exception as e:
            self._logger.error(f"Error getting iteration history for {iteration_id}: {e}", error=e)
            raise
    
    async def get_quality_trends(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get quality improvement trends across iterations.
        
        Args:
            limit: Maximum number of recent scores to analyze
            
        Returns:
            Dictionary containing quality trend analysis
        """
        try:
            # Get recent scores
            recent_scores = await self._database.select(
                "scores",
                order_by="created_at",
                desc=True,
                limit=limit
            )
            
            if not recent_scores:
                return {"message": "No scoring data available"}
            
            # Calculate trends
            scores = [score.get("overall_score", 0.0) for score in recent_scores]
            avg_score = sum(scores) / len(scores)
            
            # Quality distribution
            high_quality = len([s for s in scores if s >= 8.0])
            medium_quality = len([s for s in scores if 6.0 <= s < 8.0])
            low_quality = len([s for s in scores if s < 6.0])
            
            return {
                "total_iterations": len(recent_scores),
                "average_score": round(avg_score, 2),
                "quality_distribution": {
                    "high_quality": high_quality,
                    "medium_quality": medium_quality, 
                    "low_quality": low_quality
                },
                "score_range": {
                    "min": min(scores),
                    "max": max(scores)
                }
            }
            
        except Exception as e:
            self._logger.error(f"Error getting quality trends: {e}", error=e)
            raise