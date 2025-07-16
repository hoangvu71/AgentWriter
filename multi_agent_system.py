#!/usr/bin/env python3
"""
Multi-Agent System for Book Writing
- Orchestrator Agent: Routes requests and coordinates workflows
- Plot Generator Agent: Creates plots based on genre/audience parameters
- Author Generator Agent: Creates author profiles matching microgenre/audience
"""

from typing import Dict, Any, List, Optional
import asyncio
import json
import re
from dataclasses import dataclass
from enum import Enum
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
import os
from dotenv import load_dotenv

# Import Supabase service
try:
    from supabase_service import supabase_service
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
    print("Supabase not available - running without data persistence")

load_dotenv()

@dataclass
class PlotRequest:
    """Request parameters for plot generation"""
    genre: str
    subgenre: str
    microgenre: str
    trope: str
    tone: str
    target_audience: Dict[str, str]  # age_range, sexual_orientation, gender

@dataclass
class AuthorRequest:
    """Request parameters for author generation"""
    microgenre: str
    target_audience: Dict[str, str]
    plot_context: Optional[str] = None

@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    agent_name: str
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error: Optional[str] = None

class AgentType(Enum):
    ORCHESTRATOR = "orchestrator"
    PLOT_GENERATOR = "plot_generator"
    AUTHOR_GENERATOR = "author_generator"

class MultiAgentSystem:
    """Multi-agent system for book writing with orchestrator coordination"""
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self.agents: Dict[str, Agent] = {}
        self.runners: Dict[str, InMemoryRunner] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize all agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents in the system"""
        
        # Orchestrator Agent
        self.agents[AgentType.ORCHESTRATOR.value] = Agent(
            name="orchestrator",
            model=self.model,
            instruction="""You are the Orchestrator Agent in a multi-agent book writing system.

Your responsibilities:
1. ROUTE user requests to appropriate agents (plot_generator, author_generator)
2. COORDINATE sequential workflows
3. ANALYZE user intent and determine which agents to invoke
4. MANAGE communication between agents
5. COMPILE final responses from multiple agents

Routing Logic:
- If user mentions plot, story, genre, trope → route to plot_generator
- If user mentions author, biography, voice, style → route to author_generator  
- If user requests both → coordinate sequential workflow (plot → author)

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "routing_decision": "plot_only|author_only|plot_then_author",
    "agents_to_invoke": ["agent_name1", "agent_name2"],
    "extracted_parameters": {
        "genre": "string",
        "subgenre": "string", 
        "microgenre": "string",
        "trope": "string",
        "tone": "string",
        "target_audience": {
            "age_range": "string",
            "sexual_orientation": "string",
            "gender": "string"
        }
    },
    "workflow_plan": "description of execution plan",
    "message_to_plot_agent": "specific message for plot generator",
    "message_to_author_agent": "specific message for author generator"
}

Be decisive and clear in your routing decisions. Always return valid JSON only.""",
            description="Routes requests and coordinates workflows between plot and author generators"
        )
        
        # Plot Generator Agent
        self.agents[AgentType.PLOT_GENERATOR.value] = Agent(
            name="plot_generator",
            model=self.model,
            instruction="""You are the Plot Generator Agent specialized in creating compelling book plots.

Your task: Generate detailed plots based on user specifications:
- Genre, subgenre, microgenre
- Tropes and tone
- Target audience (age range, sexual orientation, gender)

Guidelines:
1. Create engaging, original plots that match all specified parameters
2. Consider target audience preferences and sensitivities
3. Incorporate requested tropes naturally into the story
4. Balance tone elements (dark, humorous, realistic, etc.)
5. Write a comprehensive plot that includes setup, conflicts, and potential resolutions within the plot summary
6. Include character archetypes suitable for the audience

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format - ONLY these two fields:
{
    "title": "compelling book title",
    "plot_summary": "detailed 2-3 paragraph plot summary that includes the full story arc, main conflicts, and resolution"
}

DO NOT add any other fields like plot_points, potential_conflicts, or potential_resolutions. Everything should be included in the plot_summary narrative.

Be creative while staying true to genre conventions and audience expectations. Always return valid JSON only.""",
            description="Generates plots based on genre, tropes, tone, and target audience"
        )
        
        # Author Generator Agent
        self.agents[AgentType.AUTHOR_GENERATOR.value] = Agent(
            name="author_generator",
            model=self.model,
            instruction="""You are the Author Generator Agent specialized in creating author profiles.

Your task: Generate author profiles that match microgenre and target audience:
- Author name (pen name if appropriate)
- Biography (background, experience, credentials)
- Writing voice and style description
- Match to microgenre expertise
- Appeal to target audience

Guidelines:
1. Create believable, diverse author profiles
2. Match author background to microgenre credibility
3. Consider target audience connection and relatability
4. Include relevant experience or expertise
5. Develop authentic voice/style descriptions
6. Ensure author persona fits the genre expectations

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "author_name": "full author name",
    "pen_name": "pen name if different from real name",
    "biography": "author background and life experience in paragraph form, like an 'about the author' section",
    "writing_style": "simple description of writing voice and style"
}

Create authors that readers would trust and connect with for the specified genre and audience. Always return valid JSON only.""",
            description="Creates author profiles matching microgenre and target audience"
        )
        
        # Initialize runners for each agent
        for agent_type, agent in self.agents.items():
            self.runners[agent_type] = InMemoryRunner(agent, app_name="multi_agent_book_system")
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from agent response"""
        try:
            # Try to parse the entire response as JSON first
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            # If that fails, try to find JSON within the response
            try:
                # Look for JSON between braces
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # If still no JSON found, return None
            return None
    
    def _validate_orchestrator_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate orchestrator JSON response structure"""
        required_fields = ["routing_decision", "agents_to_invoke", "extracted_parameters", "workflow_plan"]
        return all(field in json_data for field in required_fields)
    
    def _validate_plot_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate plot generator JSON response structure"""
        required_fields = ["title", "plot_summary"]
        return all(field in json_data for field in required_fields)
    
    def _validate_author_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate author generator JSON response structure"""
        required_fields = ["author_name", "biography", "writing_style"]
        return all(field in json_data for field in required_fields)
    
    async def _create_session(self, agent_type: str, session_id: str, user_id: str = "default"):
        """Create session for specific agent"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        
        if agent_type not in self.sessions[session_id]:
            session = await self.runners[agent_type].session_service.create_session(
                app_name="multi_agent_book_system",
                user_id=user_id,
                session_id=f"{session_id}_{agent_type}"
            )
            self.sessions[session_id][agent_type] = session
    
    async def _send_to_agent(self, agent_type: str, message: str, session_id: str, user_id: str = "default") -> AgentResponse:
        """Send message to specific agent and get response"""
        try:
            # Ensure session exists
            await self._create_session(agent_type, session_id, user_id)
            
            # Create message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=message)]
            )
            
            # Get response from agent
            response_text = ""
            async for event in self.runners[agent_type].run_async(
                user_id=user_id,
                session_id=f"{session_id}_{agent_type}",
                new_message=content
            ):
                if hasattr(event, 'content') and event.content:
                    response_text += str(event.content)
                elif hasattr(event, 'text') and event.text:
                    response_text += event.text
            
            # Parse JSON from response
            parsed_json = self._extract_json_from_response(response_text)
            
            # Validate JSON structure based on agent type
            json_valid = False
            if parsed_json:
                if agent_type == AgentType.ORCHESTRATOR.value:
                    json_valid = self._validate_orchestrator_response(parsed_json)
                elif agent_type == AgentType.PLOT_GENERATOR.value:
                    json_valid = self._validate_plot_response(parsed_json)
                elif agent_type == AgentType.AUTHOR_GENERATOR.value:
                    json_valid = self._validate_author_response(parsed_json)
            
            # Return response with parsed JSON
            return AgentResponse(
                agent_name=agent_type,
                content=response_text,
                parsed_json=parsed_json if json_valid else None,
                metadata={"session_id": session_id, "user_id": user_id, "json_valid": json_valid},
                success=True
            )
            
        except Exception as e:
            return AgentResponse(
                agent_name=agent_type,
                content="",
                parsed_json=None,
                metadata={"session_id": session_id, "user_id": user_id},
                success=False,
                error=str(e)
            )
    
    async def process_request(self, user_message: str, session_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Process user request through multi-agent system"""
        
        # Step 1: Send to orchestrator for routing decision
        orchestrator_response = await self._send_to_agent(
            AgentType.ORCHESTRATOR.value,
            user_message,
            session_id,
            user_id
        )
        
        if not orchestrator_response.success:
            return {
                "success": False,
                "error": f"Orchestrator failed: {orchestrator_response.error}",
                "responses": []
            }
        
        # Step 2: Parse orchestrator JSON decision
        if not orchestrator_response.parsed_json:
            return {
                "success": False,
                "error": "Orchestrator did not return valid JSON",
                "responses": [orchestrator_response]
            }
        
        routing_data = orchestrator_response.parsed_json
        routing_decision = routing_data.get("routing_decision", "")
        agents_to_invoke = routing_data.get("agents_to_invoke", [])
        
        responses = [orchestrator_response]
        saved_plot_id = None
        saved_author_id = None
        
        # Save orchestrator decision to Supabase
        if SUPABASE_ENABLED:
            try:
                await supabase_service.save_orchestrator_decision(session_id, user_id, routing_data)
            except Exception as e:
                print(f"Failed to save orchestrator decision: {e}")
        
        # Step 3: Route to appropriate agents based on JSON decision
        # NEW LOGIC: Author first, then plots for that author
        if "author" in routing_decision and "author_generator" in agents_to_invoke:
            # Use orchestrator's specific message for author generator
            author_message = routing_data.get("message_to_author_agent", user_message)
            author_response = await self._send_to_agent(
                AgentType.AUTHOR_GENERATOR.value,
                author_message,
                session_id,
                user_id
            )
            responses.append(author_response)
            
            # Save author to Supabase first
            if SUPABASE_ENABLED and author_response.parsed_json:
                try:
                    saved_author = await supabase_service.save_author(
                        session_id, 
                        user_id, 
                        author_response.parsed_json
                    )
                    saved_author_id = saved_author["id"]
                except Exception as e:
                    print(f"Failed to save author: {e}")
            
            # If workflow includes plot generation for this author
            if "plot" in routing_decision and "plot_generator" in agents_to_invoke:
                # Use orchestrator's specific message for plot generator
                plot_message = routing_data.get("message_to_plot_agent", user_message)
                if author_response.parsed_json:
                    # Include author context in plot message
                    plot_message += f"\n\nAuthor context: {json.dumps(author_response.parsed_json, indent=2)}"
                
                plot_response = await self._send_to_agent(
                    AgentType.PLOT_GENERATOR.value,
                    plot_message,
                    session_id,
                    user_id
                )
                responses.append(plot_response)
                
                # Save plot with author assignment
                if SUPABASE_ENABLED and plot_response.parsed_json:
                    try:
                        saved_plot = await supabase_service.save_plot(
                            session_id, 
                            user_id, 
                            plot_response.parsed_json, 
                            routing_data,
                            saved_author_id  # Assign plot to author
                        )
                        saved_plot_id = saved_plot["id"]
                    except Exception as e:
                        print(f"Failed to save plot: {e}")
        
        elif "plot" in routing_decision and "plot_generator" in agents_to_invoke:
            # Plot only (no author specified)
            plot_message = routing_data.get("message_to_plot_agent", user_message)
            plot_response = await self._send_to_agent(
                AgentType.PLOT_GENERATOR.value,
                plot_message,
                session_id,
                user_id
            )
            responses.append(plot_response)
            
            # Save plot without author assignment
            if SUPABASE_ENABLED and plot_response.parsed_json:
                try:
                    saved_plot = await supabase_service.save_plot(
                        session_id, 
                        user_id, 
                        plot_response.parsed_json, 
                        routing_data
                    )
                    saved_plot_id = saved_plot["id"]
                except Exception as e:
                    print(f"Failed to save plot: {e}")
        
        return {
            "success": True,
            "responses": responses,
            "workflow_completed": True,
            "orchestrator_routing": routing_data,
            "saved_data": {
                "plot_id": saved_plot_id,
                "author_id": saved_author_id
            }
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about all agents in the system"""
        return {
            "agents": list(self.agents.keys()),
            "model": self.model,
            "capabilities": {
                "orchestrator": "Routes requests and coordinates workflows",
                "plot_generator": "Creates plots based on genre/audience parameters",
                "author_generator": "Creates author profiles matching microgenre/audience"
            }
        }

# Global multi-agent system instance
multi_agent_system = MultiAgentSystem()