"""
Orchestrator agent for routing and coordinating multi-agent workflows.
"""

import re
import time
import uuid
from typing import List, Dict, Any, AsyncGenerator, Optional
from ..core.interfaces import IOrchestrator, AgentRequest, AgentResponse, ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration
from ..tools.agent_tools import invoke_agent, update_workflow_context


class OrchestratorAgent(BaseAgent, IOrchestrator):
    """Orchestrator agent that routes requests and coordinates workflows"""
    
    def __init__(self, config: Configuration):
        instruction = """You are the Orchestrator Agent in a multi-agent book writing system.

Your role is to fulfill user requests by coordinating with specialized agents using tools.

Available agents:
- plot_generator: Creates story plots and narratives
- author_generator: Creates author profiles and biographies
- world_building: Creates detailed fictional worlds
- characters: Creates character populations and relationships
- critique: Analyzes and provides feedback on content
- enhancement: Improves content based on critiques
- scoring: Evaluates content quality

CRITICAL WORKFLOW COORDINATION RULES:
1. For multi-agent requests, create a unique workflow identifier as a string
2. Pass the workflow_id parameter to each invoke_agent tool call
3. Pass context between agents - extract IDs from responses and pass to next agent
4. For plot+author requests: create author FIRST, then plot with author_id
5. For world building: always pass plot_id from previous plot creation
6. For characters: always pass both plot_id and world_building_id

Sequential workflow patterns:
- Author + Plot: author_generator → plot_generator (with author_id)
- Plot + World: plot_generator → world_building (with plot_id)  
- Plot + World + Characters: plot_generator → world_building → characters (with plot_id, world_building_id)

Workflow coordination approach:
1. Create a workflow identifier (use a descriptive string like "plot_author_workflow")
2. Use invoke_agent tool with parameters: agent_name, message, context, workflow_id
3. Extract returned IDs from structured_data in the response
4. Pass extracted IDs as context to subsequent agents

IMPORTANT: Always use the invoke_agent tool for coordination. Never generate code or write function definitions."""
        
        # Initialize with agent coordination tools
        tools = [invoke_agent, update_workflow_context]
        
        super().__init__(
            name="orchestrator",
            description="Routes requests and coordinates multi-agent workflows",
            instruction=instruction,
            config=config,
            tools=tools
        )
    
    async def route_request(self, request: AgentRequest) -> List[str]:
        """Determine which agents should handle the request"""
        try:
            # Check for LoreGen request first
            if await self._is_loregen_request(request.content):
                # Extract context and add to request for LoreGen processing
                extracted_context = self.analyze_request_context(request)
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
        """Enhanced routing with structured context analysis"""
        content_lower = content.lower()
        
        # Use structured context analysis instead of text parsing
        from ..core.interfaces import AgentRequest
        temp_request = AgentRequest(content=content, user_id="routing", session_id="routing", context=context)
        analyzed_context = self.analyze_request_context(temp_request)
        
        # === STRUCTURED CONTEXT ROUTING ===
        
        # Priority 1: Content improvement workflow
        if analyzed_context.get("has_selected_content"):
            improvement_keywords = ["critique", "enhance", "improve", "better", "fix", "review"]
            if any(word in content_lower for word in improvement_keywords):
                return ["critique", "enhancement", "scoring"]
            
            # Selected content + specific requests
            content_type = analyzed_context.get("selected_content_type", "")
            if content_type == "plot":
                if any(word in content_lower for word in ["world", "setting", "geography", "culture"]):
                    return ["world_building"]
                elif any(word in content_lower for word in ["character", "personality", "protagonist"]):
                    return ["world_building", "characters"]
        
        # Priority 2: Structured parameter-based routing
        if analyzed_context.get("has_parameters"):
            agents = self.determine_agents_from_context(analyzed_context)
            
            # Combine with content intent analysis
            has_plot = any(word in content_lower for word in ["plot", "story"])
            has_author = any(word in content_lower for word in ["author", "biography", "writing style"])
            has_world = any(word in content_lower for word in ["world", "setting", "geography"])
            has_characters = any(word in content_lower for word in ["character", "personality"])
            
            # Refine agents based on explicit content requests
            if has_author and "author_generator" not in agents:
                agents.append("author_generator")
            
            if has_world and "world_building" not in agents:
                agents.append("world_building")
            
            if has_characters and "characters" not in agents:
                agents.append("characters")
            
            if agents:
                return agents
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
    
    def analyze_request_context(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Analyze request context from structured parameters instead of text parsing.
        Replaces the inefficient _extract_context method with structured data analysis.
        """
        context = {}
        content = request.content
        request_context = request.context or {}
        
        # Look for content IDs (UUIDs) in content text - keep this as fallback
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_matches = re.findall(uuid_pattern, content, re.IGNORECASE)
        if uuid_matches:
            context["content_id"] = uuid_matches[0]
        
        # NEW: Analyze structured context parameters
        if request_context:
            context["has_parameters"] = True
            context["parameter_types"] = request.get_context_types()
            
            # Content improvement workflow
            if "content_selection" in request_context:
                context["has_selected_content"] = True
                content_selection = request_context["content_selection"]
                context["selected_content_type"] = content_selection.get("type", "unknown")
                context["content_info"] = content_selection
                
            # Genre hierarchy analysis
            if "genre_hierarchy" in request_context:
                context["has_genre_context"] = True
                context["genre_info"] = request_context["genre_hierarchy"]
                
                # Determine world-building needs based on genre
                genre_name = request_context["genre_hierarchy"].get("genre", {}).get("name", "").lower()
                if genre_name in ["fantasy", "sci-fi", "science fiction", "historical"]:
                    context["needs_world_building"] = True
            
            # Story elements analysis  
            if "story_elements" in request_context:
                context["has_story_elements"] = True
                context["story_elements"] = request_context["story_elements"]
                
            # Target audience analysis
            if "target_audience" in request_context:
                context["has_audience_context"] = True
                context["audience_info"] = request_context["target_audience"]
        
        # Look for cycle/iteration requests in content text
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
            
        # Fallback content type analysis from text (when no structured context)
        if not request_context:
            content_types = ["plot", "author", "world", "character", "characters"]
            for content_type in content_types:
                if content_type in content.lower():
                    context["content_type"] = content_type
                    break
            
            # Fallback genre/audience detection from text
            if "genre" in content.lower() or "fantasy" in content.lower() or "sci-fi" in content.lower():
                context["has_genre_context"] = True
            
            if "audience" in content.lower() or "young adult" in content.lower() or "adult" in content.lower():
                context["has_audience_context"] = True
        
        return context
    
    def determine_agents_from_context(self, context: Dict[str, Any]) -> List[str]:
        """
        Determine agent sequence based on structured context parameters.
        This replaces the old text-parsing approach with intelligent context analysis.
        """
        agents = []
        
        # Base agent selection based on parameter types
        parameter_types = context.get("parameter_types", [])
        
        if "genre" in parameter_types or "audience" in parameter_types:
            agents.append("plot_generator")
            
        if "genre" in parameter_types:
            genre_info = context.get("genre_info", {})
            genre_name = genre_info.get("genre", {}).get("name", "").lower()
            
            # Fantasy, Sci-Fi, Historical genres need rich world-building
            if genre_name in ["fantasy", "sci-fi", "science fiction", "historical", "steampunk", "cyberpunk"]:
                agents.append("world_building")
        
        if "story_elements" in parameter_types or "audience" in parameter_types:
            agents.append("characters")
            
        # Content improvement workflow
        if "content_improvement" in parameter_types:
            agents.extend(["critique", "enhancement", "scoring"])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(agents))
    
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