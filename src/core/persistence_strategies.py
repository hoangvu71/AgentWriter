"""
Persistence strategy interfaces and implementations for agent-generated content.
Implements Strategy pattern to decouple agents from specific persistence logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..core.logging import get_logger


class PersistenceStrategy(ABC):
    """Abstract base class for persistence strategies"""
    
    def __init__(self):
        self.logger = get_logger(f"persistence.{self.__class__.__name__}")
    
    @abstractmethod
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Save agent response data using appropriate persistence logic.
        
        Args:
            response_data: Agent response data to save
            session_id: Session identifier
            user_id: User identifier  
            repositories: Dictionary of available repositories
            orchestrator_params: Optional orchestrator context parameters
            
        Returns:
            Saved data dictionary with generated ID, or None if no saving needed
        """
        pass


class PlotPersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for plot generator agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save plot data using plot repository"""
        try:
            from ..models.entities import Plot
            
            plot_repository = repositories.get("plot_repository")
            if not plot_repository:
                raise ValueError("Plot repository not available")
            
            author_id = orchestrator_params.get("author_id") if orchestrator_params else None
            
            plot_entity = Plot(
                session_id=session_id,
                user_id=user_id,
                title=response_data.get("title", ""),
                plot_summary=response_data.get("plot_summary", ""),
                author_id=author_id
            )
            
            plot_id = await plot_repository.create(plot_entity)
            
            return {
                "id": plot_id,
                "session_id": session_id,
                "user_id": user_id,
                "author_id": author_id,
                **response_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save plot data: {e}")
            raise


class AuthorPersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for author generator agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save author data using author repository"""
        try:
            from ..models.entities import Author
            
            author_repository = repositories.get("author_repository")
            if not author_repository:
                raise ValueError("Author repository not available")
            
            author_entity = Author(
                session_id=session_id,
                user_id=user_id,
                author_name=response_data.get("author_name", ""),
                pen_name=response_data.get("pen_name"),
                biography=response_data.get("biography", ""),
                writing_style=response_data.get("writing_style", "")
            )
            
            author_id = await author_repository.create(author_entity)
            
            return {
                "id": author_id,
                "session_id": session_id,
                "user_id": user_id,
                **response_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save author data: {e}")
            raise


class WorldBuildingPersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for world building agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save world building data using world building repository"""
        try:
            from ..models.entities import WorldBuilding
            
            world_building_repository = repositories.get("world_building_repository")
            if not world_building_repository:
                raise ValueError("World building repository not available")
            
            # Validate required context
            plot_id = orchestrator_params.get("plot_id") if orchestrator_params else None
            if not plot_id:
                raise ValueError("Cannot save world_building data: missing plot_id in context")
            
            world_entity = WorldBuilding(
                session_id=session_id,
                user_id=user_id,
                world_name=response_data.get("world_name", ""),
                world_content=response_data.get("world_content", ""),
                plot_id=plot_id
            )
            
            world_id = await world_building_repository.create(world_entity)
            
            return {
                "id": world_id,
                "session_id": session_id,
                "user_id": user_id,
                "plot_id": plot_id,
                **response_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save world building data: {e}")
            raise


class CharactersPersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for characters agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save characters data using characters repository"""
        try:
            from ..models.entities import Characters
            
            characters_repository = repositories.get("characters_repository")
            if not characters_repository:
                raise ValueError("Characters repository not available")
            
            # Validate required context
            world_id = orchestrator_params.get("world_id") if orchestrator_params else None
            plot_id = orchestrator_params.get("plot_id") if orchestrator_params else None
            
            if not plot_id:
                raise ValueError("Cannot save characters data: missing plot_id in context")
            if not world_id:
                raise ValueError("Cannot save characters data: missing world_id in context")
            
            characters_entity = Characters(
                session_id=session_id,
                user_id=user_id,
                characters=response_data.get("characters", []),
                world_context_integration=response_data.get("world_context_integration", ""),
                character_count=len(response_data.get("characters", [])),
                plot_id=plot_id,
                world_id=world_id
            )
            
            characters_id = await characters_repository.create(characters_entity)
            
            return {
                "id": characters_id,
                "session_id": session_id,
                "user_id": user_id,
                "plot_id": plot_id,
                "world_id": world_id,
                **response_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save characters data: {e}")
            raise


class CritiquePersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for critique agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save critique data using iterative repository"""
        try:
            iterative_repository = repositories.get("iterative_repository")
            if not iterative_repository:
                raise ValueError("Iterative repository not available")
            
            iteration_id = orchestrator_params.get("iteration_id") if orchestrator_params else None
            if not iteration_id:
                raise ValueError("Cannot save critique data: missing iteration_id in context")
            
            critique_json = response_data.get("critique", {})
            agent_response = response_data.get("full_response", "")
            
            return await iterative_repository.save_critique(iteration_id, critique_json, agent_response)
        except Exception as e:
            self.logger.error(f"Failed to save critique data: {e}")
            raise


class EnhancementPersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for enhancement agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save enhancement data using iterative repository"""
        try:
            iterative_repository = repositories.get("iterative_repository")
            if not iterative_repository:
                raise ValueError("Iterative repository not available")
            
            iteration_id = orchestrator_params.get("iteration_id") if orchestrator_params else None
            if not iteration_id:
                raise ValueError("Cannot save enhancement data: missing iteration_id in context")
            
            enhanced_content = response_data.get("enhanced_content", "")
            changes_made = response_data.get("changes_made", {})
            rationale = response_data.get("rationale", "")
            confidence_score = response_data.get("confidence_score", 0.0)
            
            return await iterative_repository.save_enhancement(
                iteration_id, enhanced_content, changes_made, rationale, confidence_score
            )
        except Exception as e:
            self.logger.error(f"Failed to save enhancement data: {e}")
            raise


class ScoringPersistenceStrategy(PersistenceStrategy):
    """Persistence strategy for scoring agent"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save score data using iterative repository"""
        try:
            iterative_repository = repositories.get("iterative_repository")
            if not iterative_repository:
                raise ValueError("Iterative repository not available")
            
            iteration_id = orchestrator_params.get("iteration_id") if orchestrator_params else None
            if not iteration_id:
                raise ValueError("Cannot save score data: missing iteration_id in context")
            
            overall_score = response_data.get("overall_score", 0.0)
            category_scores = response_data.get("category_scores", {})
            score_rationale = response_data.get("rationale", "")
            improvement_trajectory = response_data.get("improvement_trajectory", "")
            recommendations = response_data.get("recommendations", "")
            
            return await iterative_repository.save_score(
                iteration_id, overall_score, category_scores, score_rationale, 
                improvement_trajectory, recommendations
            )
        except Exception as e:
            self.logger.error(f"Failed to save score data: {e}")
            raise


class NoOpPersistenceStrategy(PersistenceStrategy):
    """No-operation persistence strategy for agents that don't need persistence"""
    
    async def save(self, response_data: Dict[str, Any], session_id: str, user_id: str,
                   repositories: Dict[str, Any], orchestrator_params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """No-op save operation"""
        self.logger.info("No persistence required for this agent type")
        return None