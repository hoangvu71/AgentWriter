"""
Centralized service for saving agent-generated content to database.
Provides repository-only database access for all agent-generated content.
"""

from typing import Dict, Any, Optional
from ..core.logging import get_logger


class ContentSavingService:
    """
    Centralized service for saving all types of agent-generated content.
    Uses repository-first approach with supabase_service fallback.
    """
    
    def __init__(self, plot_repository, author_repository, world_building_repository, 
                 characters_repository, session_repository=None, iterative_repository=None):
        """Initialize ContentSavingService with required repositories - no fallbacks to supabase_service."""
        self.plot_repository = plot_repository
        self.author_repository = author_repository
        self.world_building_repository = world_building_repository
        self.characters_repository = characters_repository
        self.session_repository = session_repository
        self.iterative_repository = iterative_repository
        self.logger = get_logger("content_saving")
        
        # Validate required repositories are provided
        if not all([plot_repository, author_repository, world_building_repository, characters_repository]):
            raise ValueError("All core repositories (plot, author, world_building, characters) are required")
        
        if not iterative_repository:
            raise ValueError("IterativeRepository is required for critique/enhancement/scoring operations")
    
    async def save_plot_data(self, session_id: str, user_id: str, plot_data: Dict[str, Any], 
                           orchestrator_params: Dict[str, Any] = None, author_id: str = None) -> Dict[str, Any]:
        """
        Save plot data using repository if available, fallback to supabase_service.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            plot_data: Plot data dictionary
            orchestrator_params: Optional orchestrator parameters
            author_id: Optional author identifier
            
        Returns:
            Saved plot data including generated ID
        """
        try:
            from ..models.entities import Plot
            plot_entity = Plot(
                session_id=session_id,
                user_id=user_id,
                title=plot_data.get("title", ""),
                plot_summary=plot_data.get("plot_summary", ""),
                author_id=author_id
            )
            
            plot_id = await self.plot_repository.create(plot_entity)
            
            return {
                "id": plot_id,
                "session_id": session_id,
                "user_id": user_id,
                "author_id": author_id,
                **plot_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save plot data via repository: {e}")
            raise
    
    async def save_author_data(self, session_id: str, user_id: str, author_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save author data using repository if available, fallback to supabase_service.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            author_data: Author data dictionary
            
        Returns:
            Saved author data including generated ID
        """
        try:
            from ..models.entities import Author
            author_entity = Author(
                session_id=session_id,
                user_id=user_id,
                author_name=author_data.get("author_name", ""),
                pen_name=author_data.get("pen_name"),
                biography=author_data.get("biography", ""),
                writing_style=author_data.get("writing_style", "")
            )
            
            author_id = await self.author_repository.create(author_entity)
            
            return {
                "id": author_id,
                "session_id": session_id,
                "user_id": user_id,
                **author_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save author data via repository: {e}")
            raise
    
    async def save_world_building_data(self, session_id: str, user_id: str, world_data: Dict[str, Any], 
                                     orchestrator_params: Dict[str, Any] = None, plot_id: str = None) -> Dict[str, Any]:
        """
        Save world building data using repository if available, fallback to supabase_service.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            world_data: World building data dictionary
            orchestrator_params: Optional orchestrator parameters
            plot_id: Optional plot identifier
            
        Returns:
            Saved world building data including generated ID
        """
        try:
            from ..models.entities import WorldBuilding
            world_entity = WorldBuilding(
                session_id=session_id,
                user_id=user_id,
                world_name=world_data.get("world_name", ""),
                world_content=world_data.get("world_content", ""),
                plot_id=plot_id
            )
            
            world_id = await self.world_building_repository.create(world_entity)
            
            return {
                "id": world_id,
                "session_id": session_id,
                "user_id": user_id,
                "plot_id": plot_id,
                **world_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save world building data via repository: {e}")
            raise
    
    async def save_characters_data(self, session_id: str, user_id: str, characters_data: Dict[str, Any], 
                                 orchestrator_params: Dict[str, Any] = None, world_id: str = None, 
                                 plot_id: str = None) -> Dict[str, Any]:
        """
        Save characters data using repository if available, fallback to supabase_service.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            characters_data: Characters data dictionary
            orchestrator_params: Optional orchestrator parameters
            world_id: Optional world building identifier
            plot_id: Optional plot identifier
            
        Returns:
            Saved characters data including generated ID
        """
        try:
            from ..models.entities import Characters
            characters_entity = Characters(
                session_id=session_id,
                user_id=user_id,
                characters=characters_data.get("characters", []),
                world_context_integration=characters_data.get("world_context_integration", ""),
                character_count=len(characters_data.get("characters", [])),
                plot_id=plot_id,
                world_id=world_id
            )
            
            characters_id = await self.characters_repository.create(characters_entity)
            
            return {
                "id": characters_id,
                "session_id": session_id,
                "user_id": user_id,
                "plot_id": plot_id,
                "world_id": world_id,
                **characters_data
            }
        except Exception as e:
            self.logger.error(f"Failed to save characters data via repository: {e}")
            raise
    
    async def save_critique_data(self, iteration_id: str, critique_json: Dict[str, Any], agent_response: str) -> Dict[str, Any]:
        """
        Save critique data using repository pattern.
        
        Args:
            iteration_id: Iteration identifier
            critique_json: Critique data in JSON format
            agent_response: Agent response text
            
        Returns:
            Dictionary containing the saved critique record
        """
        try:
            return await self.iterative_repository.save_critique(iteration_id, critique_json, agent_response)
        except Exception as e:
            self.logger.error(f"Failed to save critique data for iteration {iteration_id}: {e}")
            raise
    
    async def save_enhancement_data(self, iteration_id: str, enhanced_content: str, changes_made: Dict[str, Any], 
                                  rationale: str, confidence_score: float) -> None:
        """
        Save enhancement data using repository if available, fallback to supabase_service.
        
        Args:
            iteration_id: Iteration identifier
            enhanced_content: Enhanced content text
            changes_made: Dictionary of changes made
            rationale: Enhancement rationale
            confidence_score: Confidence score for enhancement
        """
        # TODO: Implement enhancement repository when needed
        # Using supabase_service directly for specialized tables not yet in repository pattern
        try:
            return await self.iterative_repository.save_enhancement(
                iteration_id, enhanced_content, changes_made, rationale, confidence_score
            )
        except Exception as e:
            self.logger.error(f"Failed to save enhancement data for iteration {iteration_id}: {e}")
            raise
    
    async def save_score_data(self, iteration_id: str, overall_score: float, category_scores: Dict[str, Any], 
                            score_rationale: str, improvement_trajectory: str, recommendations: str) -> None:
        """
        Save score data using repository if available, fallback to supabase_service.
        
        Args:
            iteration_id: Iteration identifier
            overall_score: Overall score value
            category_scores: Dictionary of category scores
            score_rationale: Score rationale
            improvement_trajectory: Improvement trajectory description
            recommendations: Recommendations text
        """
        # TODO: Implement scoring repository when needed
        # Using supabase_service directly for specialized tables not yet in repository pattern
        try:
            return await self.iterative_repository.save_score(
                iteration_id, overall_score, category_scores, score_rationale, improvement_trajectory, recommendations
            )
        except Exception as e:
            self.logger.error(f"Failed to save score data for iteration {iteration_id}: {e}")
            raise
    
    async def save_agent_response(self, agent, response_data: Dict[str, Any], session_id: str, 
                                user_id: str, orchestrator_params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Save agent response data using the agent's persistence strategy.
        
        Args:
            agent: Agent instance with persistence strategy
            response_data: Agent response data
            session_id: Session identifier
            user_id: User identifier
            orchestrator_params: Optional orchestrator parameters containing context
            
        Returns:
            Saved data dictionary or None if no saving needed
            
        Raises:
            ValueError: If required context is missing for the agent type
        """
        try:
            # Get agent's persistence strategy
            persistence_strategy = agent.get_persistence_strategy()
            
            # Prepare repositories dictionary
            repositories = {
                "plot_repository": self.plot_repository,
                "author_repository": self.author_repository,
                "world_building_repository": self.world_building_repository,
                "characters_repository": self.characters_repository,
                "session_repository": self.session_repository,
                "iterative_repository": self.iterative_repository
            }
            
            # Use strategy to save data
            result = await persistence_strategy.save(
                response_data=response_data,
                session_id=session_id,
                user_id=user_id,
                repositories=repositories,
                orchestrator_params=orchestrator_params
            )
            
            if result:
                self.logger.info(f"Successfully saved {agent.name} response using {persistence_strategy.__class__.__name__}")
            else:
                self.logger.info(f"No persistence required for {agent.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to save response for agent {agent.name}: {e}")
            raise