#!/usr/bin/env python3
"""
Multi-Agent System for Book Writing
- Orchestrator Agent: Routes requests and coordinates workflows
- Plot Generator Agent: Creates plots based on genre/audience parameters
- Author Generator Agent: Creates author profiles matching microgenre/audience
"""

from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
import os
from dotenv import load_dotenv

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
    metadata: Dict[str, Any]
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

Always respond in JSON format with:
{
    "routing_decision": "plot_only|author_only|plot_then_author",
    "agents_to_invoke": ["agent_name1", "agent_name2"],
    "extracted_parameters": {...},
    "workflow_plan": "description of execution plan"
}

Be decisive and clear in your routing decisions.""",
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
5. Provide plot structure: setup, conflict, resolution
6. Include character archetypes suitable for the audience

Output Format:
- Title suggestion
- Plot summary (2-3 paragraphs)
- Main characters and their roles
- Key plot points and conflicts
- Tone and style notes
- Target audience fit explanation

Be creative while staying true to genre conventions and audience expectations.""",
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

Output Format:
- Author name
- Biography (2-3 sentences)
- Writing style and voice description
- Genre expertise and credentials
- Target audience appeal explanation
- Published works suggestions (fictional)

Create authors that readers would trust and connect with for the specified genre and audience.""",
            description="Creates author profiles matching microgenre and target audience"
        )
        
        # Initialize runners for each agent
        for agent_type, agent in self.agents.items():
            self.runners[agent_type] = InMemoryRunner(agent, app_name="multi_agent_book_system")
    
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
            
            return AgentResponse(
                agent_name=agent_type,
                content=response_text,
                metadata={"session_id": session_id, "user_id": user_id},
                success=True
            )
            
        except Exception as e:
            return AgentResponse(
                agent_name=agent_type,
                content="",
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
        
        # Step 2: Parse orchestrator decision (simplified - in production would use JSON parsing)
        routing_decision = orchestrator_response.content.lower()
        
        responses = [orchestrator_response]
        
        # Step 3: Route to appropriate agents based on decision
        if "plot" in routing_decision:
            plot_response = await self._send_to_agent(
                AgentType.PLOT_GENERATOR.value,
                user_message,
                session_id,
                user_id
            )
            responses.append(plot_response)
            
            # If workflow includes author generation after plot
            if "author" in routing_decision:
                author_message = f"Generate author profile for: {user_message}\n\nPlot context:\n{plot_response.content}"
                author_response = await self._send_to_agent(
                    AgentType.AUTHOR_GENERATOR.value,
                    author_message,
                    session_id,
                    user_id
                )
                responses.append(author_response)
        
        elif "author" in routing_decision:
            author_response = await self._send_to_agent(
                AgentType.AUTHOR_GENERATOR.value,
                user_message,
                session_id,
                user_id
            )
            responses.append(author_response)
        
        return {
            "success": True,
            "responses": responses,
            "workflow_completed": True
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