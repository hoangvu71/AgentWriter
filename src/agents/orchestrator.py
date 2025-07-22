"""
Orchestrator agent for routing and coordinating multi-agent workflows.
"""

import re
import time
from typing import List, Dict, Any, AsyncGenerator, Optional
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

Content Parameters Workflows:
- If CONTENT_TO_IMPROVE is selected (plot/author) + "critique"/"enhance" → improvement_workflow
- If CONTENT_TO_IMPROVE is plot + "world building" → world_building_from_plot
- If CONTENT_TO_IMPROVE is plot + "characters" → characters_from_plot_and_world
- If CONTENT_TO_IMPROVE is plot + "world" + "characters" → world_then_characters_from_plot
- If genre/audience params selected + "create plot" → plot_generator_with_params

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
            # Check for LoreGen request first
            if await self._is_loregen_request(request.content):
                # Extract context and add to request for LoreGen processing
                extracted_context = self._extract_context(request.content)
                if request.context:
                    request.context.update(extracted_context)
                else:
                    request.context = extracted_context
                return ['loregen']
            
            # Process the request to get routing decision
            response = await self.process_request(request)
            
            if response.success and response.parsed_json:
                return response.parsed_json.get("agents_to_invoke", [])
            
            # Fallback to simple keyword matching
            return await self._fallback_routing(request.content, request.context or {})
            
        except Exception as e:
            self._logger.error(f"Error in routing request: {e}", error=e)
            return await self._fallback_routing(request.content, request.context or {})
    
    async def coordinate_workflow(self, request: AgentRequest, agent_names: List[str]) -> AgentResponse:
        """Coordinate execution across multiple agents"""
        # This will be implemented with the actual agent execution logic
        # For now, return the routing decision
        response = await self.process_request(request)
        return response
    
    async def _fallback_routing(self, content: str, context: Dict[str, Any]) -> List[str]:
        """Enhanced routing with Content Parameters and LoreGen support"""
        content_lower = content.lower()
        extracted_context = self._extract_context(content)
        combined_context = {**extracted_context, **context}
        
        # === CONTENT PARAMETERS WORKFLOWS ===
        
        # If user selected content to improve + wants critique/enhance
        if context.get("has_selected_content") and any(word in content_lower for word in ["critique", "enhance", "improve", "better"]):
            return ["critique", "enhancement", "scoring"]
        
        # If user selected plot + wants world building
        if context.get("selected_content_type") == "plot" and any(word in content_lower for word in ["world", "setting", "geography", "culture"]):
            return ["world_building"]
        
        # If user selected plot + wants characters
        if context.get("selected_content_type") == "plot" and any(word in content_lower for word in ["character", "personality", "protagonist"]):
            # Characters need world context, so build world first
            return ["world_building", "characters"]
        
        # If user selected plot + wants both world and characters
        if context.get("selected_content_type") == "plot" and any(word in content_lower for word in ["world", "setting"]) and any(word in content_lower for word in ["character", "personality"]):
            return ["world_building", "characters"]
        
        # === PARAMETER-BASED CREATION ===
        
        # If user has genre/audience params and wants to create content
        if context.get("has_parameters") or context.get("uses_parameters"):
            has_plot = any(word in content_lower for word in ["plot", "story"])
            has_author = any(word in content_lower for word in ["author", "biography", "writing style"])
            has_world = any(word in content_lower for word in ["world", "setting", "geography"])
            has_characters = any(word in content_lower for word in ["character", "personality"])
            
            if has_plot and has_author:
                return ["plot_generator", "author_generator"]
            elif has_plot and has_world and has_characters:
                return ["plot_generator", "world_building", "characters"]
            elif has_plot and has_world:
                return ["plot_generator", "world_building"]
            elif has_plot and has_characters:
                return ["plot_generator", "world_building", "characters"]
            elif has_plot:
                return ["plot_generator"]
            elif has_author:
                return ["author_generator"]
        
        # === REGULAR WORKFLOWS (no Content Parameters) ===
        
        # Check for improvement workflow keywords
        if any(word in content_lower for word in ["improve", "enhance", "critique", "better"]):
            return ["critique", "enhancement", "scoring"]
        
        # Check for combined requests (plot AND author, plot AND world, etc.)
        has_plot = any(word in content_lower for word in ["plot", "story"])
        has_author = any(word in content_lower for word in ["author", "biography", "writing style", "pen name"])
        has_world = any(word in content_lower for word in ["world", "setting", "geography", "culture", "magic"])
        has_characters = any(word in content_lower for word in ["character", "personality", "relationship", "protagonist"])
        
        # Multi-agent workflows
        if has_plot and has_author and has_world and has_characters:
            return ["plot_generator", "author_generator", "world_building", "characters"]
        elif has_plot and has_author and has_world:
            return ["plot_generator", "author_generator", "world_building"]
        elif has_plot and has_author:
            return ["plot_generator", "author_generator"]
        elif has_plot and has_characters:
            return ["plot_generator", "world_building", "characters"]
        elif has_plot and has_world:
            return ["plot_generator", "world_building"]
        
        # Single agent workflows
        elif has_characters:
            # If user already selected content, don't generate new plot
            if context.get("has_selected_content"):
                return ["world_building", "characters"]
            else:
                return ["plot_generator", "world_building", "characters"]
        elif has_world:
            # If user already selected content, don't generate new plot
            if context.get("has_selected_content"):
                return ["world_building"]
            else:
                return ["plot_generator", "world_building"]
        elif has_author:
            return ["author_generator"]
        elif has_plot:
            return ["plot_generator"]
        
        # Default to plot generation
        return ["plot_generator"]
    
    def _get_content_type(self) -> ContentType:
        """Orchestrator doesn't produce content directly"""
        return ContentType.PLOT  # This won't be used
    
    def _extract_context(self, content: str) -> Dict[str, Any]:
        """Extract context information from the content including Content Parameters"""
        context = {}
        
        # Look for content IDs (UUIDs)
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_matches = re.findall(uuid_pattern, content, re.IGNORECASE)
        if uuid_matches:
            context["content_id"] = uuid_matches[0]
        
        # Look for Content Parameters context markers
        if "CONTENT_TO_IMPROVE:" in content:
            context["has_selected_content"] = True
            # Extract content type from the parameters
            if "CONTENT_TYPE: plot" in content:
                context["selected_content_type"] = "plot"
            elif "CONTENT_TYPE: author" in content:
                context["selected_content_type"] = "author"
        
        # Look for Genre/Audience Parameters
        if "MAIN GENRE:" in content or "SUBGENRE:" in content or "TARGET AUDIENCE:" in content or "DETAILED CONTENT SPECIFICATIONS" in content:
            context["has_parameters"] = True
            
        # Look for parameter-based requests
        if "based on" in content.lower() and "param" in content.lower():
            context["uses_parameters"] = True
        
        # Look for cycle/iteration requests
        cycle_patterns = [
            r'(\d+)\s*(?:cycles?|times?|iterations?)',
            r'(?:run|expand|iterate)\s*(\d+)\s*(?:cycles?|times?)',
            r'(?:cycles?|iterations?).*?(\d+)',
            r'(\d+)x\s*expansion'
        ]
        
        cycles_requested = 1  # Default to 1 cycle
        for pattern in cycle_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    cycles_requested = int(match.group(1))
                    # Limit to reasonable range
                    cycles_requested = max(1, min(cycles_requested, 10))
                    break
                except (ValueError, IndexError):
                    continue
        
        if cycles_requested > 1:
            context["expansion_cycles"] = cycles_requested
            
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
    
    # === LOREGEN INTEGRATION METHODS ===
    
    async def _is_loregen_request(self, message: str) -> bool:
        """
        Detect if this is a LoreGen request for world building expansion.
        """
        message_lower = message.lower()
        
        # Primary LoreGen patterns - order matters, check specific first
        loregen_patterns = [
            "use this plot's worldbuilding and expand",
            "use this plot and expand", 
            "take this plot's worldbuilding and expand",
            "use the world building of this plot and expand"
        ]
        
        # Flexible LoreGen patterns (with cycles support)
        flexible_patterns = [
            r"expand.*plot.*worldbuilding",
            r"expand.*plot.*world building", 
            r"expand.*worldbuilding.*plot",
            r"expand.*world building.*plot",
            r"worldbuilding.*expand",
            r"world building.*expand",
            r"lore.*expand",
            r"expand.*lore",
            r"cycles.*lore.*expansion",
            r"cycles.*worldbuilding",
            r"cycles.*world building",
            r"iterate.*worldbuilding",
            r"iterate.*world building",
            r"iterate.*lore",
            r"expansion.*plot",
            r"expand.*worldbuilding.*cycles",
            r"expand.*world building.*cycles"
        ]
        
        # Check for exact pattern matches first
        for pattern in loregen_patterns:
            if pattern in message_lower:
                self._logger.info(f"LoreGen exact pattern matched: '{pattern}'")
                return True
        
        # Check flexible patterns (with regex)
        import re
        for pattern in flexible_patterns:
            if re.search(pattern, message_lower):
                self._logger.info(f"LoreGen flexible pattern matched: '{pattern}'")
                return True
        
        # Check for keyword combinations (fallback)
        has_plot = "plot" in message_lower
        has_expand = any(word in message_lower for word in ["expand", "expansion", "generate more"])
        has_worldbuilding = any(word in message_lower for word in ["worldbuilding", "world building", "world", "lore"])
        has_use = "use" in message_lower
        
        # LoreGen requires all key components (legacy detection)
        if has_plot and has_expand and has_worldbuilding and has_use:
            self._logger.info("LoreGen keyword combination matched")
            return True
        
        return False
    
    def _extract_plot_id(self, request: AgentRequest) -> Optional[str]:
        """Extract plot_id from request context"""
        if not request.context:
            return None
        # Try plot_id first, then fall back to content_id for plot-type content
        return request.context.get('plot_id') or request.context.get('content_id')
    
    async def _enrich_loregen_request(self, request: AgentRequest) -> AgentRequest:
        """
        Enrich LoreGen request with additional context for processing.
        """
        enriched_context = dict(request.context) if request.context else {}
        
        # Add LoreGen-specific context
        enriched_context.update({
            'loregen_request': True,
            'processing_timestamp': time.time(),
            'expansion_type': 'full_world_expansion'
        })
        
        return AgentRequest(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            context=enriched_context
        )
    
    async def _validate_loregen_request(self, plot_id: str) -> bool:
        """
        Validate that LoreGen request can be processed.
        Checks if plot exists and has world building content.
        """
        if not plot_id:
            return False
        
        try:
            # Check if database service is available
            if hasattr(self, '_database_service') and self._database_service:
                plot_exists = await self._database_service.plot_exists(plot_id)
                has_world_building = await self._database_service.has_world_building(plot_id)
                return plot_exists and has_world_building
            
            # If no database service, assume valid (will be caught by LoreGen agent)
            return True
            
        except Exception as e:
            self._logger.warning(f"Could not validate LoreGen request: {e}")
            return True  # Allow processing, let LoreGen handle validation
    
    async def _determine_routing(self, message: str, context: Dict[str, Any]) -> List[str]:
        """
        Determine routing with LoreGen support integration.
        """
        # Check for LoreGen first
        if await self._is_loregen_request(message):
            # Map content_id to plot_id if it's a plot type content
            plot_id = context.get('plot_id') or context.get('content_id')
            if await self._validate_loregen_request(plot_id):
                return ['loregen']
            else:
                # Invalid LoreGen request, fall through to normal routing
                pass
        
        # Use existing fallback routing
        return await self._fallback_routing(message, context)