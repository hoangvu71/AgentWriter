"""
Centralized service for saving agent-generated content to database.
Delegates to tool functions to eliminate code duplication.
"""

from typing import Dict, Any, Optional
from ..core.logging import get_logger


class ContentSavingService:
    """
    Centralized service for saving all types of agent-generated content.
    Delegates to tool functions to maintain single source of truth.
    """
    
    def __init__(self, plot_repository, author_repository, world_building_repository, 
                 characters_repository, session_repository=None, iterative_repository=None):
        """Initialize ContentSavingService with required repositories."""
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
    
    async def save_agent_response(self, agent_name: str, response_data: Dict[str, Any], 
                                session_id: str, user_id: str, 
                                orchestrator_params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Save agent response data by delegating to appropriate tool functions.
        
        Args:
            agent_name: Name of the agent (string, not object)
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
            # Route to appropriate tool function based on agent name
            if agent_name == "plot_generator":
                return await self._save_plot_via_tool(response_data, session_id, user_id, orchestrator_params)
            elif agent_name == "author_generator":
                return await self._save_author_via_tool(response_data, session_id, user_id)
            elif agent_name == "world_building":
                return await self._save_world_building_via_tool(response_data, session_id, user_id, orchestrator_params)
            elif agent_name == "characters":
                return await self._save_characters_via_tool(response_data, session_id, user_id, orchestrator_params)
            elif agent_name in ["critique", "enhancement", "scoring"]:
                return await self._save_iterative_content(agent_name, response_data, orchestrator_params)
            else:
                self.logger.info(f"No persistence required for agent: {agent_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to save {agent_name} response: {e}")
            raise
    
    async def _save_plot_via_tool(self, response_data: Dict[str, Any], session_id: str, 
                                user_id: str, orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save plot data using the save_plot tool function"""
        from ..tools.writing_tools import save_plot
        
        # Set up session context (tool functions expect this)
        from ..core.container import get_container
        container = get_container()
        container.set_session_context(session_id, user_id)
        
        # Extract author_id from orchestrator params if available
        author_id = orchestrator_params.get("author_id") if orchestrator_params else None
        
        # Call the tool function
        result = save_plot(
            title=response_data.get("title", ""),
            plot_summary=response_data.get("plot_summary", ""),
            genre=response_data.get("genre"),
            themes=response_data.get("themes"),
            session_id=session_id,
            user_id=user_id,
            author_id=author_id
        )
        
        return result
    
    async def _save_author_via_tool(self, response_data: Dict[str, Any], session_id: str, user_id: str) -> Dict[str, Any]:
        """Save author data using the save_author tool function"""
        from ..tools.writing_tools import save_author
        
        # Set up session context
        from ..core.container import get_container
        container = get_container()
        container.set_session_context(session_id, user_id)
        
        # Call the tool function
        result = save_author(
            author_name=response_data.get("author_name", ""),
            author_bio=response_data.get("biography", ""),
            writing_style=response_data.get("writing_style", ""),
            session_id=session_id,
            user_id=user_id,
            pen_name=response_data.get("pen_name"),
            genres=response_data.get("genres")
        )
        
        return result
    
    async def _save_world_building_via_tool(self, response_data: Dict[str, Any], session_id: str, 
                                          user_id: str, orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save world building data using the save_world_building tool function"""
        from ..tools.writing_tools import save_world_building
        
        # Validate required context
        plot_id = orchestrator_params.get("plot_id") if orchestrator_params else None
        if not plot_id:
            raise ValueError("Cannot save world_building data: missing plot_id in context")
        
        # Set up session context
        from ..core.container import get_container
        container = get_container()
        container.set_session_context(session_id, user_id)
        
        # Call the tool function with correct parameters matching save_world_building interface
        result = save_world_building(
            world_name=response_data.get("world_name", ""),
            description=response_data.get("world_content", ""),  # Tool expects 'description', not 'world_content'
            plot_id=plot_id,
            session_id=session_id,
            user_id=user_id,
            geography=response_data.get("geography"),
            culture=response_data.get("culture"),
            history=response_data.get("history"),
            magic_system=response_data.get("magic_system"),
            technology=response_data.get("technology")
        )
        
        return result
    
    async def _save_characters_via_tool(self, response_data: Dict[str, Any], session_id: str, 
                                      user_id: str, orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save characters data using the save_characters tool function"""
        from ..tools.writing_tools import save_characters
        
        # Validate required context
        plot_id = orchestrator_params.get("plot_id") if orchestrator_params else None
        world_id = orchestrator_params.get("world_id") if orchestrator_params else None
        
        if not plot_id:
            raise ValueError("Cannot save characters data: missing plot_id in context")
        if not world_id:
            raise ValueError("Cannot save characters data: missing world_id in context")
        
        # Set up session context
        from ..core.container import get_container
        container = get_container()
        container.set_session_context(session_id, user_id)
        
        # Call the tool function with correct parameters matching save_characters interface
        result = save_characters(
            plot_id=plot_id,
            world_building_id=world_id,
            characters=response_data.get("characters", []),
            session_id=session_id,
            user_id=user_id
        )
        
        return result
    
    async def _save_iterative_content(self, agent_name: str, response_data: Dict[str, Any], 
                                    orchestrator_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save iterative content (critique, enhancement, scoring) using repository"""
        iteration_id = orchestrator_params.get("iteration_id") if orchestrator_params else None
        if not iteration_id:
            raise ValueError(f"Cannot save {agent_name} data: missing iteration_id in context")
        
        if agent_name == "critique":
            critique_json = response_data.get("critique", {})
            agent_response = response_data.get("full_response", "")
            return await self.iterative_repository.save_critique(iteration_id, critique_json, agent_response)
        
        elif agent_name == "enhancement":
            enhanced_content = response_data.get("enhanced_content", "")
            changes_made = response_data.get("changes_made", {})
            rationale = response_data.get("rationale", "")
            confidence_score = response_data.get("confidence_score", 0.0)
            return await self.iterative_repository.save_enhancement(
                iteration_id, enhanced_content, changes_made, rationale, confidence_score
            )
        
        elif agent_name == "scoring":
            overall_score = response_data.get("overall_score", 0.0)
            category_scores = response_data.get("category_scores", {})
            score_rationale = response_data.get("rationale", "")
            improvement_trajectory = response_data.get("improvement_trajectory", "")
            recommendations = response_data.get("recommendations", "")
            return await self.iterative_repository.save_score(
                iteration_id, overall_score, category_scores, score_rationale, 
                improvement_trajectory, recommendations
            )
        
        return None
    
    # DEPRECATED: Legacy methods for backwards compatibility - delegate to tool functions
    # These methods are maintained for WebSocket handler compatibility but should not be used in new code
    async def save_plot_data(self, session_id: str, user_id: str, plot_data: Dict[str, Any], 
                           orchestrator_params: Dict[str, Any] = None, author_id: str = None) -> Dict[str, Any]:
        """DEPRECATED: Legacy method - delegates to tool function. Use tools directly."""
        self.logger.warning("save_plot_data is deprecated - use plot tools directly")
        if orchestrator_params is None:
            orchestrator_params = {}
        if author_id:
            orchestrator_params["author_id"] = author_id
        return await self._save_plot_via_tool(plot_data, session_id, user_id, orchestrator_params)
    
    async def save_author_data(self, session_id: str, user_id: str, author_data: Dict[str, Any]) -> Dict[str, Any]:
        """DEPRECATED: Legacy method - delegates to tool function. Use tools directly."""
        self.logger.warning("save_author_data is deprecated - use author tools directly")
        return await self._save_author_via_tool(author_data, session_id, user_id)
    
    async def save_world_building_data(self, session_id: str, user_id: str, world_data: Dict[str, Any], 
                                     orchestrator_params: Dict[str, Any] = None, plot_id: str = None) -> Dict[str, Any]:
        """DEPRECATED: Legacy method - delegates to tool function. Use tools directly."""
        self.logger.warning("save_world_building_data is deprecated - use world building tools directly")
        if orchestrator_params is None:
            orchestrator_params = {}
        if plot_id:
            orchestrator_params["plot_id"] = plot_id
        return await self._save_world_building_via_tool(world_data, session_id, user_id, orchestrator_params)
    
    async def save_characters_data(self, session_id: str, user_id: str, characters_data: Dict[str, Any], 
                                 orchestrator_params: Dict[str, Any] = None, plot_id: str = None, world_id: str = None) -> Dict[str, Any]:
        """DEPRECATED: Legacy method - delegates to tool function. Use tools directly."""
        self.logger.warning("save_characters_data is deprecated - use character tools directly")
        if orchestrator_params is None:
            orchestrator_params = {}
        if plot_id:
            orchestrator_params["plot_id"] = plot_id
        if world_id:
            orchestrator_params["world_id"] = world_id
        return await self._save_characters_via_tool(characters_data, session_id, user_id, orchestrator_params)
    
    async def save_critique_data(self, iteration_id: str, critique_json: Dict[str, Any], agent_response: str) -> None:
        """DEPRECATED: Legacy method - delegates to repository. Use iterative repositories directly."""
        self.logger.warning("save_critique_data is deprecated - use iterative repositories directly")
        orchestrator_params = {"iteration_id": iteration_id}
        response_data = {"critique": critique_json, "full_response": agent_response}
        return await self._save_iterative_content("critique", response_data, orchestrator_params)
    
    async def save_enhancement_data(self, iteration_id: str, enhanced_content: str, changes_made: Dict[str, Any], 
                                  rationale: str, confidence_score: float) -> None:
        """DEPRECATED: Legacy method - delegates to repository. Use iterative repositories directly."""
        self.logger.warning("save_enhancement_data is deprecated - use iterative repositories directly")
        orchestrator_params = {"iteration_id": iteration_id}
        response_data = {
            "enhanced_content": enhanced_content,
            "changes_made": changes_made,
            "rationale": rationale,
            "confidence_score": confidence_score
        }
        return await self._save_iterative_content("enhancement", response_data, orchestrator_params)
    
    async def save_score_data(self, iteration_id: str, overall_score: float, category_scores: Dict[str, Any], 
                            score_rationale: str, improvement_trajectory: str, recommendations: str) -> None:
        """DEPRECATED: Legacy method - delegates to repository. Use iterative repositories directly."""
        self.logger.warning("save_score_data is deprecated - use iterative repositories directly")
        orchestrator_params = {"iteration_id": iteration_id}
        response_data = {
            "overall_score": overall_score,
            "category_scores": category_scores,
            "rationale": score_rationale,
            "improvement_trajectory": improvement_trajectory,
            "recommendations": recommendations
        }
        return await self._save_iterative_content("scoring", response_data, orchestrator_params)