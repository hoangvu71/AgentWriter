"""
Orchestrator agent for routing and coordinating multi-agent workflows.
"""

import re
from typing import List, Dict, Any, AsyncGenerator
from ..core.interfaces import IOrchestrator, AgentRequest, AgentResponse, ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class OrchestratorAgent(BaseAgent, IOrchestrator):
    """Orchestrator agent that routes requests and coordinates workflows"""
    
    def __init__(self, config: Configuration):
        instruction = """You are the Orchestrator Agent in a multi-agent book writing system.

Your responsibilities:
1. ROUTE user requests to appropriate agents (plot_generator, author_generator, world_building, characters, critique)
2. COORDINATE sequential workflows
3. ANALYZE user intent and determine which agents to invoke
4. MANAGE communication between agents
5. COMPILE final responses from multiple agents
6. EXTRACT selected content from message context (look for CONTENT_ID, CONTENT_TYPE, CONTENT_TITLE)

Routing Logic:
- If user mentions plot, story, genre, trope → route to plot_generator
- If user mentions author, biography, voice, style → route to author_generator
- If user mentions world, setting, geography, culture, politics, history → route to plot_then_world_building
- If user mentions characters, personalities, relationships → route to plot_then_world_then_characters
- If user mentions "improve", "enhance", "critique" with content ID → route to improvement_workflow
- If user wants multiple things → route to appropriate sequential workflow

Sequential Workflows:
1. plot_generator → Basic plot creation
2. author_generator → Author profile creation
3. plot_then_world_building → Plot creation followed by world building
4. plot_then_world_then_characters → Full story foundation (plot → world → characters)
5. improvement_workflow → Critique → Enhancement → Scoring cycle

Response Format:
Always respond with JSON containing:
{
    "routing_decision": "agent_name or workflow_name",
    "reasoning": "Why this routing decision was made",
    "workflow_type": "single_agent" or "sequential_workflow",
    "agents_to_invoke": ["list", "of", "agent", "names"],
    "context_extracted": {
        "content_id": "if found in message",
        "content_type": "plot/author/etc if found",
        "genre_context": "if genre parameters mentioned",
        "audience_context": "if target audience mentioned"
    }
}

Be decisive and clear in your routing decisions."""
        
        super().__init__(
            name="orchestrator",
            description="Routes requests and coordinates multi-agent workflows",
            instruction=instruction,
            config=config
        )
    
    async def route_request(self, request: AgentRequest) -> List[str]:
        """Determine which agents should handle the request"""
        try:
            # Process the request to get routing decision
            response = await self.process_request(request)
            
            if response.success and response.parsed_json:
                return response.parsed_json.get("agents_to_invoke", [])
            
            # Fallback to simple keyword matching
            return self._fallback_routing(request.content)
            
        except Exception as e:
            self._logger.error(f"Error in routing request: {e}", error=e)
            return self._fallback_routing(request.content)
    
    async def coordinate_workflow(self, request: AgentRequest, agent_names: List[str]) -> AgentResponse:
        """Coordinate execution across multiple agents"""
        # This will be implemented with the actual agent execution logic
        # For now, return the routing decision
        response = await self.process_request(request)
        return response
    
    def _fallback_routing(self, content: str) -> List[str]:
        """Simple keyword-based routing fallback"""
        content_lower = content.lower()
        
        # Check for improvement workflow keywords
        if any(word in content_lower for word in ["improve", "enhance", "critique", "better"]):
            return ["critique", "enhancement", "scoring"]
        
        # Check for character-related keywords
        if any(word in content_lower for word in ["character", "personality", "relationship", "protagonist"]):
            return ["plot_generator", "world_building", "characters"]
        
        # Check for world building keywords
        if any(word in content_lower for word in ["world", "setting", "geography", "culture", "magic"]):
            return ["plot_generator", "world_building"]
        
        # Check for author-related keywords
        if any(word in content_lower for word in ["author", "biography", "writing style", "pen name"]):
            return ["author_generator"]
        
        # Default to plot generation
        return ["plot_generator"]
    
    def _get_content_type(self) -> ContentType:
        """Orchestrator doesn't produce content directly"""
        return ContentType.PLOT  # This won't be used
    
    def _extract_context(self, content: str) -> Dict[str, Any]:
        """Extract context information from the content"""
        context = {}
        
        # Look for content IDs (UUIDs)
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_matches = re.findall(uuid_pattern, content, re.IGNORECASE)
        if uuid_matches:
            context["content_id"] = uuid_matches[0]
        
        # Look for content type mentions
        content_types = ["plot", "author", "world", "character", "characters"]
        for content_type in content_types:
            if content_type in content.lower():
                context["content_type"] = content_type
                break
        
        # Look for genre context
        if "genre" in content.lower() or "fantasy" in content.lower() or "sci-fi" in content.lower():
            context["has_genre_context"] = True
        
        # Look for audience context
        if "audience" in content.lower() or "young adult" in content.lower() or "adult" in content.lower():
            context["has_audience_context"] = True
        
        return context