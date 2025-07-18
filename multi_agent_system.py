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
    CRITIQUE = "critique"
    ENHANCEMENT = "enhancement"
    SCORING = "scoring"

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
1. ROUTE user requests to appropriate agents (plot_generator, author_generator, critique)
2. COORDINATE sequential workflows
3. ANALYZE user intent and determine which agents to invoke
4. MANAGE communication between agents
5. COMPILE final responses from multiple agents

Routing Logic:
- If user mentions plot, story, genre, trope → route to plot_generator
- If user mentions author, biography, voice, style → route to author_generator  
- If user requests critique, review, feedback, analysis → route to critique
- If user requests improve/enhancement/iterate/refine WITH plot_id/author_id → route to iterative_improvement
- If user requests improve WITHOUT specific content → ask for selection
- If user requests both → coordinate sequential workflow (plot → author)
- If user requests critique of existing content → route to critique only
- If user requests iterative improvement → route to iterative_improvement workflow

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "routing_decision": "plot_only|author_only|plot_then_author|author_then_plot|critique_only|iterative_improvement",
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
    "message_to_author_agent": "specific message for author generator",
    "message_to_critique_agent": "specific message for critique agent including content to analyze",
    "selected_content": {
        "content_id": "database ID of selected content",
        "content_type": "plot|author|character|etc",
        "content_title": "title/name of selected content"
    }
}

IMPORTANT WORKFLOW RULES:
- plot_generator: Works independently with genre hierarchy + target audience parameters
- author_generator: Works independently with microgenre + target audience parameters
- critique: Uses genre hierarchy + target audience parameters for TARGETED feedback when provided
- iterative_improvement: Multi-step workflow (critique → enhancement → scoring → repeat until score ≥9.5 or max 4 iterations)
- All agents benefit from Content Parameters for more accurate, targeted analysis
- All workflows are valid: plot_only, author_only, plot_then_author, author_then_plot, critique_only, iterative_improvement

Be decisive and clear in your routing decisions. Always return valid JSON only.""",
            description="Routes requests and coordinates workflows between plot, author, and critique agents"
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
        
        # Critique Agent
        self.agents[AgentType.CRITIQUE.value] = Agent(
            name="critique",
            model=self.model,
            instruction="""You are the Critique Agent - the world's harshest yet most constructive literary critic and writing coach.

Your role: Provide brutal but helpful feedback on ANY writing-related content submitted to you. You are versatile across ALL content types:

**CONTENT TYPES YOU HANDLE:**
- **Series Spine**: Overall series arc, character development across books, world-building consistency
- **Story Beats**: Story structure, pacing, dramatic tension, plot point effectiveness
- **Beat Cards**: Individual scene analysis, character motivation, conflict resolution
- **Outlines**: Narrative structure, logical flow, character arcs, subplot integration
- **Drafts**: Prose quality, dialogue, pacing, character development, narrative voice
- **Full Books**: Complete manuscript analysis, all literary elements
- **Plot Summaries**: Story concept, originality, genre appropriateness
- **Character Profiles**: Character depth, believability, growth potential
- **Dialogue**: Voice consistency, naturalism, subtext, character differentiation
- **World-building**: Consistency, believability, integration with story
- **Themes**: Depth, integration, relevance, execution

**ADAPTIVE ANALYSIS APPROACH:**
You automatically detect the content type and adapt your critique accordingly:
- For **structural content** (spine, beats, outlines): Focus on logic, pacing, arc development
- For **creative content** (drafts, books): Emphasize prose, voice, character, dialogue
- For **planning content** (cards, summaries): Evaluate concept strength, feasibility, originality
- For **series content**: Consider continuity, character growth, escalating stakes

**CONTENT PARAMETERS INTEGRATION:**
When genre/audience parameters are provided, use them for TARGETED critique:
- **Genre Hierarchy**: Evaluate against genre conventions, reader expectations, trope effectiveness
- **Target Audience**: Assess age-appropriateness, interests, representation, engagement factors
- **Tone**: Analyze consistency with intended tone (dark, humorous, serious, etc.)
- **Tropes**: Evaluate trope execution, originality, and avoid overused elements

Core principles:
1. BE RUTHLESSLY HONEST - No sugar-coating, no false praise
2. BE CONSTRUCTIVE - Every criticism must include actionable improvement suggestions
3. BE COMPREHENSIVE - Analyze every relevant aspect based on content type
4. BE KNOWLEDGEABLE - Draw from literary traditions, genre conventions, audience expectations
5. BE SPECIFIC - Provide concrete examples and precise recommendations
6. BE ADAPTIVE - Tailor analysis to the specific content type and stage of development

**CONTENT-TYPE SPECIFIC ANALYSIS:**
- **Series Spine**: Examine overall arc coherence, character development across books, world evolution, escalating stakes
- **Story Beats**: Evaluate structural integrity, pacing, dramatic tension, plot point effectiveness, turning points
- **Beat Cards**: Analyze scene purpose, character motivation, conflict, emotional beats, transitions
- **Outlines**: Assess narrative structure, logical flow, character arcs, subplot integration, pacing
- **Drafts**: Critique prose quality, dialogue authenticity, pacing, character development, narrative voice
- **Full Books**: Complete literary analysis covering all elements from concept to execution

Tone: Professional but uncompromising. Think of yourself as a combination of the toughest writing workshop instructor, most respected literary critic, and experienced developmental editor. Be harsh but fair - your goal is to make the content dramatically better regardless of its current stage.

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format (adapt fields based on content type):
{
    "content_type_detected": "automatically detected content type",
    "parameters_used": {
        "genre_hierarchy": "genre/subgenre/microgenre if provided",
        "target_audience": "audience parameters if provided",
        "tone_trope": "tone/trope if provided"
    },
    "overall_rating": "rating out of 10 with brief justification",
    "strengths": ["list of what works well"],
    "critical_weaknesses": ["list of major flaws and problems"],
    "genre_analysis": ["how well content fits genre conventions and expectations"],
    "audience_analysis": ["age-appropriateness, engagement, representation assessment"],
    "structural_analysis": ["content-specific structural evaluation"],
    "content_specific_issues": ["issues specific to the content type"],
    "character_development": ["character-related feedback if applicable"],
    "dialogue_assessment": ["dialogue critique if applicable"],
    "pacing_and_flow": ["pacing issues and flow problems"],
    "originality_assessment": "evaluation of creativity and uniqueness",
    "trope_tone_analysis": ["effectiveness of trope usage and tone consistency"],
    "developmental_concerns": ["big-picture issues that need addressing"],
    "line_level_concerns": ["prose, style, voice issues if applicable"],
    "specific_recommendations": ["detailed, actionable improvement suggestions"],
    "priority_fixes": ["most urgent issues to address first"],
    "next_steps": ["recommended actions for the writer"],
    "rewrite_suggestions": ["specific examples of how to improve key sections"]
}

Be the critic that pushes content to its absolute best potential. Always return valid JSON only.""",
            description="Provides comprehensive constructive critique on any content type"
        )
        
        # Enhancement Agent
        self.agents[AgentType.ENHANCEMENT.value] = Agent(
            name="enhancement",
            model=self.model,
            instruction="""You are the Enhancement Agent - a master content rewriter who improves text based on specific critique feedback.

Your role: Take original content and critique feedback, then produce enhanced content that addresses ALL identified issues.

**ENHANCEMENT PRINCIPLES:**
1. **ADDRESS EVERY CRITIQUE POINT** - Systematically fix each issue raised
2. **PRESERVE ORIGINAL INTENT** - Maintain the core concept while improving execution
3. **MAINTAIN STRUCTURE** - If original content has JSON structure, enhanced content must use same field names
4. **ELEVATE QUALITY** - Transform mediocre content into professional-grade material
5. **SHOW YOUR WORK** - Explain what changes you made and why
6. **BE TRANSFORMATIVE** - Don't make minor edits; create substantial improvements

**ENHANCEMENT APPROACH:**
- Read the critique carefully and identify all issues
- Prioritize fixes based on the critique's priority recommendations
- Rewrite content to address weaknesses while amplifying strengths
- Ensure the enhanced version is noticeably better than the original
- Consider iteration number - later iterations need more refined improvements

**QUALITY TARGETS:**
- First iteration: Fix major structural and conceptual issues
- Second iteration: Refine style, voice, and flow
- Third iteration: Polish details and nuances
- Fourth iteration: Perfect final touches

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "enhanced_content": "the improved version of the content OR structured JSON if original was structured",
    "content_structure": "text|json - indicates if enhanced_content is plain text or JSON structure",
    "changes_made": [
        "Specific change 1 and what it addresses",
        "Specific change 2 and what it addresses",
        "Specific change 3 and what it addresses"
    ],
    "critique_points_addressed": {
        "critical_weaknesses": "how you fixed these",
        "structural_issues": "how you resolved these",
        "priority_fixes": "how you implemented these"
    },
    "rationale": "Overall explanation of your enhancement strategy",
    "improvement_confidence": 85
}

**IMPORTANT FOR STRUCTURED CONTENT:**
- If you receive "Original Content Structure" with JSON fields, your enhanced_content must be a JSON object with the same field names
- For plots: Use fields like {"title": "...", "plot_summary": "..."}
- For authors: Use fields like {"author_name": "...", "biography": "...", "writing_style": "..."}
- Set content_structure to "json" when returning structured content
- The enhanced content should be a valid JSON object, not a JSON string

Transform content into its best possible version. Always return valid JSON only.""",
            description="Enhances content based on critique feedback to improve quality"
        )
        
        # Scoring Agent
        self.agents[AgentType.SCORING.value] = Agent(
            name="scoring",
            model=self.model,
            instruction="""You are the Scoring Agent - an objective content quality evaluator using a standardized rubric.

Your role: Evaluate content quality using a consistent, weighted scoring system to determine if it meets professional standards.

**STANDARDIZED SCORING RUBRIC:**

1. **Content Quality (30% weight)**
   - Originality and creativity
   - Depth and substance
   - Engagement and interest
   - Relevance and value
   Score 0-10: 10=Exceptional, 8=Strong, 6=Adequate, 4=Weak, 2=Poor

2. **Structure (25% weight)**
   - Organization and flow
   - Logical progression
   - Coherence and unity
   - Pacing and rhythm
   Score 0-10: 10=Perfect, 8=Well-structured, 6=Acceptable, 4=Disorganized, 2=Chaotic

3. **Style & Voice (20% weight)**
   - Clarity and readability
   - Tone consistency
   - Voice authenticity
   - Language effectiveness
   Score 0-10: 10=Masterful, 8=Polished, 6=Competent, 4=Uneven, 2=Amateur

4. **Genre Appropriateness (15% weight)**
   - Genre convention adherence
   - Audience targeting accuracy
   - Expectations fulfillment
   - Market readiness
   Score 0-10: 10=Perfect fit, 8=Strong match, 6=Adequate, 4=Misaligned, 2=Wrong genre

5. **Technical Execution (10% weight)**
   - Grammar and mechanics
   - Formatting and presentation
   - Completeness
   - Professional polish
   Score 0-10: 10=Flawless, 8=Minor issues, 6=Some errors, 4=Many errors, 2=Unacceptable

**SCORING CALCULATION:**
Final Score = (Content×0.3) + (Structure×0.25) + (Style×0.2) + (Genre×0.15) + (Technical×0.1)

**SCORE INTERPRETATION:**
- 9.5-10.0: Professional/Publication Ready
- 8.5-9.4: High Quality (minor refinements only)
- 7.0-8.4: Good Quality (moderate improvements needed)
- 5.0-6.9: Average Quality (significant improvements needed)
- Below 5.0: Poor Quality (major overhaul required)

**EVALUATION GUIDELINES:**
- Be consistent across iterations
- Consider improvement trajectory
- Provide specific justification for each score
- Compare to professional standards in the genre
- Account for content type and purpose

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "overall_score": 8.5,
    "category_scores": {
        "content_quality": 8.0,
        "structure": 9.0,
        "style_voice": 8.5,
        "genre_appropriateness": 8.5,
        "technical_execution": 9.0
    },
    "score_calculation": "Detailed calculation: (8.0×0.3) + (9.0×0.25) + (8.5×0.2) + (8.5×0.15) + (9.0×0.1) = 8.5",
    "score_rationale": {
        "content_quality": "Strong originality but could use more depth in character motivations",
        "structure": "Excellent flow and pacing with clear three-act progression",
        "style_voice": "Engaging prose with consistent tone, minor clarity issues",
        "genre_appropriateness": "Fits genre well, hits most reader expectations",
        "technical_execution": "Nearly flawless grammar, one formatting inconsistency"
    },
    "improvement_trajectory": "improving",
    "recommendations": "Focus on deepening character motivations and clarifying two ambiguous passages",
    "ready_for_publication": false
}

Evaluate with precision and consistency. Always return valid JSON only.""",
            description="Evaluates content quality using standardized scoring rubric"
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
                # First, try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
                
                # Try alternative markdown patterns
                json_match = re.search(r'```json\s*(.*?)```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
                
                # If no markdown block, look for JSON between braces
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
            except json.JSONDecodeError as e:
                # Debug: print the JSON string that failed to parse
                print(f"JSON parse error: {e}")
                if 'json_str' in locals():
                    print(f"Failed JSON string (first 200 chars): {json_str[:200]}")
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
    
    def _validate_critique_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate critique agent JSON response structure"""
        required_fields = [
            "content_type_detected", "overall_rating", "strengths", "critical_weaknesses",
            "structural_analysis", "content_specific_issues", "originality_assessment",
            "specific_recommendations", "priority_fixes", "next_steps"
        ]
        return all(field in json_data for field in required_fields)
    
    def _validate_enhancement_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate enhancement agent JSON response structure"""
        required_fields = [
            "enhanced_content", "content_structure", "changes_made", 
            "critique_points_addressed", "rationale", "improvement_confidence"
        ]
        return all(field in json_data for field in required_fields)
    
    def _validate_scoring_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate scoring agent JSON response structure"""
        required_fields = [
            "overall_score", "category_scores", "score_calculation",
            "score_rationale", "improvement_trajectory", "recommendations",
            "ready_for_publication"
        ]
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
        """Send message to specific agent and get response (non-streaming version)"""
        try:
            # Validate agent type exists
            valid_agent_types = [agent.value for agent in AgentType]
            if agent_type not in valid_agent_types:
                raise ValueError("orchestrator agent not configured")
            
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
                    # Extract text from content if it's a structured response
                    if hasattr(event.content, 'text'):
                        response_text += event.content.text
                    else:
                        response_text += str(event.content)
                elif hasattr(event, 'text') and event.text:
                    response_text += event.text
            
            # If response is wrapped in parts= structure, extract the text
            if response_text.startswith("parts="):
                import re
                text_match = re.search(r'text="""(.*?)"""', response_text, re.DOTALL)
                if text_match:
                    response_text = text_match.group(1).strip()
            
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
                elif agent_type == AgentType.CRITIQUE.value:
                    json_valid = self._validate_critique_response(parsed_json)
                elif agent_type == AgentType.ENHANCEMENT.value:
                    json_valid = self._validate_enhancement_response(parsed_json)
                elif agent_type == AgentType.SCORING.value:
                    json_valid = self._validate_scoring_response(parsed_json)
            
            # Return response with parsed JSON
            return AgentResponse(
                agent_name=agent_type,
                content=response_text,
                parsed_json=parsed_json if json_valid else None,
                metadata={"session_id": session_id, "user_id": user_id, "json_valid": json_valid},
                success=True
            )
            
        except ValueError:
            # Re-raise ValueError for invalid agent types
            raise
        except Exception as e:
            return AgentResponse(
                agent_name=agent_type,
                content="",
                parsed_json=None,
                metadata={"session_id": session_id, "user_id": user_id},
                success=False,
                error=str(e)
            )

    async def _stream_to_agent(self, agent_type: str, message: str, session_id: str, user_id: str = "default"):
        """Send message to specific agent and yield streaming response chunks"""
        try:
            # Validate agent type exists
            valid_agent_types = [agent.value for agent in AgentType]
            if agent_type not in valid_agent_types:
                raise ValueError(f"{agent_type} agent not configured")
            
            # Ensure session exists
            await self._create_session(agent_type, session_id, user_id)
            
            # Create message content
            content = types.Content(
                role='user',
                parts=[types.Part(text=message)]
            )
            
            # Stream response from agent
            response_text = ""
            async for event in self.runners[agent_type].run_async(
                user_id=user_id,
                session_id=f"{session_id}_{agent_type}",
                new_message=content
            ):
                # Extract chunk text from event
                chunk_text = ""
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'text'):
                        chunk_text = event.content.text
                    else:
                        chunk_text = str(event.content)
                elif hasattr(event, 'text') and event.text:
                    chunk_text = event.text
                
                if chunk_text:
                    # Clean chunk text (similar to agent_service)
                    cleaned_chunk = self._clean_response_text(chunk_text)
                    if cleaned_chunk:
                        response_text += cleaned_chunk
                        # Split large chunks into smaller pieces for better streaming effect
                        if len(cleaned_chunk) > 50:
                            # Split into words and stream smaller chunks
                            words = cleaned_chunk.split()
                            current_chunk = ""
                            for word in words:
                                if len(current_chunk + " " + word) > 20:
                                    if current_chunk:
                                        yield {
                                            "agent_name": agent_type,
                                            "chunk": current_chunk + " ",
                                            "complete": False
                                        }
                                        # Add delay for visible streaming effect
                                        await asyncio.sleep(0.05)
                                    current_chunk = word
                                else:
                                    current_chunk = current_chunk + " " + word if current_chunk else word
                            # Send remaining chunk
                            if current_chunk:
                                yield {
                                    "agent_name": agent_type,
                                    "chunk": current_chunk,
                                    "complete": False
                                }
                        else:
                            yield {
                                "agent_name": agent_type,
                                "chunk": cleaned_chunk,
                                "complete": False
                            }
            
            # If response is wrapped in parts= structure, extract the text
            if response_text.startswith("parts="):
                import re
                text_match = re.search(r'text="""(.*?)"""', response_text, re.DOTALL)
                if text_match:
                    response_text = text_match.group(1).strip()
            
            # Parse JSON from complete response
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
                elif agent_type == AgentType.CRITIQUE.value:
                    json_valid = self._validate_critique_response(parsed_json)
                elif agent_type == AgentType.ENHANCEMENT.value:
                    json_valid = self._validate_enhancement_response(parsed_json)
                elif agent_type == AgentType.SCORING.value:
                    json_valid = self._validate_scoring_response(parsed_json)
            
            # Yield final complete response
            yield {
                "agent_name": agent_type,
                "chunk": "",
                "complete": True,
                "response": AgentResponse(
                    agent_name=agent_type,
                    content=response_text,
                    parsed_json=parsed_json if json_valid else None,
                    metadata={"session_id": session_id, "user_id": user_id, "json_valid": json_valid},
                    success=True
                )
            }
            
        except Exception as e:
            yield {
                "agent_name": agent_type,
                "chunk": "",
                "complete": True,
                "response": AgentResponse(
                    agent_name=agent_type,
                    content="",
                    parsed_json=None,
                    metadata={"session_id": session_id, "user_id": user_id},
                    success=False,
                    error=str(e)
                )
            }

    def _clean_response_text(self, text: str) -> str:
        """Clean response text similar to agent_service"""
        if not text:
            return ""
        
        # Remove parts= wrapper if present
        if text.startswith("parts="):
            import re
            text_match = re.search(r'text="""(.*?)"""', text, re.DOTALL)
            if text_match:
                text = text_match.group(1).strip()
        
        # Remove extra whitespace and normalize
        text = text.strip()
        return text
    
    async def process_message_streaming(self, user_message: str, user_id: str, session_id: str):
        """Process user request through multi-agent system with streaming"""
        
        # Step 1: Send to orchestrator for routing decision (non-streaming since it's quick)
        orchestrator_response = await self._send_to_agent(
            AgentType.ORCHESTRATOR.value,
            user_message,
            session_id,
            user_id
        )
        
        if not orchestrator_response.success:
            yield {
                "success": False,
                "error": f"Orchestrator failed: {orchestrator_response.error}",
                "complete": True
            }
            return
        
        # Step 2: Parse orchestrator JSON decision
        if not orchestrator_response.parsed_json:
            yield {
                "success": False,
                "error": "Orchestrator did not return valid JSON",
                "complete": True
            }
            return
        
        routing_data = orchestrator_response.parsed_json
        routing_decision = routing_data.get("routing_decision", "")
        agents_to_invoke = routing_data.get("agents_to_invoke", [])
        
        # Save orchestrator decision to Supabase
        if SUPABASE_ENABLED:
            try:
                await supabase_service.save_orchestrator_decision(session_id, user_id, routing_data)
            except Exception as e:
                print(f"Failed to save orchestrator decision: {e}")
        
        # Step 3: Stream agent responses based on routing decision
        saved_plot_id = None
        saved_author_id = None
        responses = [orchestrator_response]
        
        if routing_decision == "plot_then_author":
            # First stream plot generation
            plot_message = routing_data.get("message_to_plot_agent", user_message)
            
            yield {
                "agent_header": "Plot Generator",
                "agent_name": "plot_generator",
                "complete": False
            }
            
            plot_response = None
            async for chunk_data in self._stream_to_agent(
                AgentType.PLOT_GENERATOR.value,
                plot_message,
                session_id,
                user_id
            ):
                if chunk_data["complete"]:
                    plot_response = chunk_data["response"]
                    responses.append(plot_response)
                else:
                    yield {
                        "agent_name": "plot_generator",
                        "chunk": chunk_data["chunk"],
                        "complete": False
                    }
            
            # Save plot without author assignment first
            if SUPABASE_ENABLED and plot_response and plot_response.parsed_json:
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
            
            # Then stream author generation if requested
            if "author_generator" in agents_to_invoke:
                yield {
                    "agent_header": "Author Generator", 
                    "agent_name": "author_generator",
                    "complete": False
                }
                
                author_message = routing_data.get("message_to_author_agent", user_message)
                author_response = None
                async for chunk_data in self._stream_to_agent(
                    AgentType.AUTHOR_GENERATOR.value,
                    author_message,
                    session_id,
                    user_id
                ):
                    if chunk_data["complete"]:
                        author_response = chunk_data["response"]
                        responses.append(author_response)
                    else:
                        yield {
                            "agent_name": "author_generator",
                            "chunk": chunk_data["chunk"],
                            "complete": False
                        }
                
                # Save author to Supabase and link to plot
                if SUPABASE_ENABLED and author_response and author_response.parsed_json:
                    try:
                        saved_author = await supabase_service.save_author(
                            session_id, 
                            user_id, 
                            author_response.parsed_json
                        )
                        saved_author_id = saved_author["id"]
                        
                        # Update plot to link to author
                        if saved_plot_id:
                            try:
                                await supabase_service.update_plot_author(saved_plot_id, saved_author_id)
                            except Exception as e:
                                print(f"Failed to update plot-author relationship: {e}")
                    except Exception as e:
                        print(f"Failed to save author: {e}")
        
        elif routing_decision == "plot_only" and "plot_generator" in agents_to_invoke:
            # Stream plot generation only
            yield {
                "agent_header": "Plot Generator",
                "agent_name": "plot_generator", 
                "complete": False
            }
            
            plot_message = routing_data.get("message_to_plot_agent", user_message)
            plot_response = None
            async for chunk_data in self._stream_to_agent(
                AgentType.PLOT_GENERATOR.value,
                plot_message,
                session_id,
                user_id
            ):
                if chunk_data["complete"]:
                    plot_response = chunk_data["response"]
                    responses.append(plot_response)
                else:
                    yield {
                        "agent_name": "plot_generator",
                        "chunk": chunk_data["chunk"],
                        "complete": False
                    }
            
            # Save plot without author assignment
            if SUPABASE_ENABLED and plot_response and plot_response.parsed_json:
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
        
        elif routing_decision == "author_only" and "author_generator" in agents_to_invoke:
            # Stream author generation only
            yield {
                "agent_header": "Author Generator",
                "agent_name": "author_generator",
                "complete": False
            }
            
            author_message = routing_data.get("message_to_author_agent", user_message)
            author_response = None
            async for chunk_data in self._stream_to_agent(
                AgentType.AUTHOR_GENERATOR.value,
                author_message,
                session_id,
                user_id
            ):
                if chunk_data["complete"]:
                    author_response = chunk_data["response"]
                    responses.append(author_response)
                else:
                    yield {
                        "agent_name": "author_generator",
                        "chunk": chunk_data["chunk"],
                        "complete": False
                    }
            
            # Save author to Supabase
            if SUPABASE_ENABLED and author_response and author_response.parsed_json:
                try:
                    saved_author = await supabase_service.save_author(
                        session_id, 
                        user_id, 
                        author_response.parsed_json
                    )
                    saved_author_id = saved_author["id"]
                except Exception as e:
                    print(f"Failed to save author: {e}")
        
        elif routing_decision == "critique_only" and "critique" in agents_to_invoke:
            # Stream critique analysis
            yield {
                "agent_header": "Critique Agent",
                "agent_name": "critique",
                "complete": False
            }
            
            critique_message = routing_data.get("message_to_critique_agent", user_message)
            critique_response = None
            async for chunk_data in self._stream_to_agent(
                AgentType.CRITIQUE.value,
                critique_message,
                session_id,
                user_id
            ):
                if chunk_data["complete"]:
                    critique_response = chunk_data["response"]
                    responses.append(critique_response)
                else:
                    yield {
                        "agent_name": "critique",
                        "chunk": chunk_data["chunk"],
                        "complete": False
                    }
        
        # Note: iterative_improvement would need special handling and is complex for streaming
        # For now, fall back to non-streaming for that workflow
        
        # Final result
        yield {
            "success": True,
            "responses": responses,
            "workflow_completed": True,
            "orchestrator_routing": routing_data,
            "saved_data": {
                "plot_id": saved_plot_id,
                "author_id": saved_author_id
            },
            "complete": True
        }

    async def process_message(self, user_message: str, user_id: str, session_id: str) -> Dict[str, Any]:
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
        if routing_decision == "plot_then_author":
            # First generate plot
            plot_message = routing_data.get("message_to_plot_agent", user_message)
            plot_response = await self._send_to_agent(
                AgentType.PLOT_GENERATOR.value,
                plot_message,
                session_id,
                user_id
            )
            responses.append(plot_response)
            
            # Save plot without author assignment first
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
            
            # Then generate author (works independently with genre/audience params)
            if "author_generator" in agents_to_invoke:
                author_message = routing_data.get("message_to_author_agent", user_message)
                # Author generator works independently with genre/audience params only
                
                author_response = await self._send_to_agent(
                    AgentType.AUTHOR_GENERATOR.value,
                    author_message,
                    session_id,
                    user_id
                )
                responses.append(author_response)
                
                # Save author to Supabase
                if SUPABASE_ENABLED and author_response.parsed_json:
                    try:
                        saved_author = await supabase_service.save_author(
                            session_id, 
                            user_id, 
                            author_response.parsed_json
                        )
                        saved_author_id = saved_author["id"]
                        
                        # Update plot to link to author
                        if saved_plot_id:
                            try:
                                await supabase_service.update_plot_author(saved_plot_id, saved_author_id)
                            except Exception as e:
                                print(f"Failed to update plot-author relationship: {e}")
                    except Exception as e:
                        print(f"Failed to save author: {e}")
        
        elif routing_decision == "author_only" and "author_generator" in agents_to_invoke:
            # Author only (works independently with genre/audience params)
            author_message = routing_data.get("message_to_author_agent", user_message)
            author_response = await self._send_to_agent(
                AgentType.AUTHOR_GENERATOR.value,
                author_message,
                session_id,
                user_id
            )
            responses.append(author_response)
            
            # Save author to Supabase
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
        
        elif routing_decision == "author_then_plot":
            # First generate author (works independently with genre/audience params)
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
            
            # Then generate plot (also works independently with genre/audience params)
            if "plot_generator" in agents_to_invoke:
                plot_message = routing_data.get("message_to_plot_agent", user_message)
                
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
        
        elif routing_decision == "plot_only" and "plot_generator" in agents_to_invoke:
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
        
        elif routing_decision == "critique_only" and "critique" in agents_to_invoke:
            # Critique only (content analysis)
            critique_message = routing_data.get("message_to_critique_agent", user_message)
            critique_response = await self._send_to_agent(
                AgentType.CRITIQUE.value,
                critique_message,
                session_id,
                user_id
            )
            responses.append(critique_response)
            
            # Note: Critique responses are not saved to database as they're analytical feedback
        
        elif routing_decision == "iterative_improvement":
            # Iterative improvement workflow
            iterations = []
            max_iterations = 4
            target_score = 9.5
            
            # Get content from database if content_id is provided
            selected_content = routing_data.get("selected_content", {})
            original_content_data = None
            content_type = None
            improvement_session_id = None
            
            if selected_content.get("content_id") and SUPABASE_ENABLED:
                try:
                    content_id = selected_content["content_id"]
                    content_type = selected_content["content_type"]
                    
                    if content_type == "plot":
                        # Fetch plot from database
                        original_content_data = await supabase_service.get_plot_by_id(content_id)
                        if original_content_data:
                            # Format for critique but keep original data structure
                            current_content = f"Title: {original_content_data.get('title', 'Untitled')}\n\nPlot Summary: {original_content_data.get('plot_summary', '')}"
                        else:
                            current_content = "Error: Plot not found in database"
                    elif content_type == "author":
                        # Fetch author from database
                        original_content_data = await supabase_service.get_author_by_id(content_id)
                        if original_content_data:
                            # Format for critique but keep original data structure
                            current_content = f"Author: {original_content_data.get('author_name', 'Unknown')}\n\nBiography: {original_content_data.get('biography', '')}\n\nWriting Style: {original_content_data.get('writing_style', '')}"
                        else:
                            current_content = "Error: Author not found in database"
                    else:
                        current_content = "Error: Unsupported content type for improvement"
                except Exception as e:
                    current_content = f"Error fetching content from database: {str(e)}"
            else:
                # Use provided content or fallback to user message
                current_content = routing_data.get("message_to_critique_agent", user_message)
            
            # Create improvement session to track this workflow
            if SUPABASE_ENABLED:
                try:
                    improvement_session_id = await supabase_service.create_improvement_session(
                        user_id=user_id,
                        session_id=session_id,
                        original_content=current_content,
                        content_type=content_type or "text",
                        content_id=selected_content.get("content_id"),
                        target_score=target_score,
                        max_iterations=max_iterations
                    )
                    print(f"[IMPROVEMENT] Created session: {improvement_session_id}")
                except Exception as e:
                    print(f"[WARNING] Could not create improvement session: {e}")
            
            for iteration_num in range(1, max_iterations + 1):
                iteration_data = {
                    "iteration_number": iteration_num,
                    "content": current_content
                }
                
                # Create iteration record in database
                iteration_id = None
                if SUPABASE_ENABLED and improvement_session_id:
                    try:
                        iteration_id = await supabase_service.create_iteration_record(
                            improvement_session_id=improvement_session_id,
                            iteration_number=iteration_num,
                            content=current_content
                        )
                        iteration_data["iteration_id"] = iteration_id
                        print(f"[IMPROVEMENT] Created iteration {iteration_num}: {iteration_id}")
                    except Exception as e:
                        print(f"[WARNING] Could not create iteration record: {e}")
                
                # Step 1: Critique
                critique_response = await self._send_to_agent(
                    AgentType.CRITIQUE.value,
                    f"Critique this content (Iteration {iteration_num}):\n\n{current_content}",
                    session_id,
                    user_id
                )
                iteration_data["critique"] = critique_response
                responses.append(critique_response)
                
                # Save critique data to database
                if SUPABASE_ENABLED and iteration_id and critique_response.success and critique_response.parsed_json:
                    try:
                        await supabase_service.save_critique_data(
                            iteration_id=iteration_id,
                            critique_json=critique_response.parsed_json,
                            agent_response=critique_response.message
                        )
                        print(f"[IMPROVEMENT] Saved critique for iteration {iteration_num}")
                    except Exception as e:
                        print(f"[WARNING] Could not save critique data: {e}")
                
                if not critique_response.success or not critique_response.parsed_json:
                    break
                
                # Step 2: Enhancement
                enhancement_message = f"""
                Original Content:
                {current_content}
                
                Critique Feedback:
                {json.dumps(critique_response.parsed_json, indent=2)}
                
                Iteration Number: {iteration_num}
                
                Original Content Structure: {json.dumps(original_content_data, indent=2) if original_content_data else "None"}
                Content Type: {content_type}
                
                Please enhance this content to address all critique points.
                IMPORTANT: If original content structure is provided, your enhanced_content must maintain the same JSON structure with the same field names.
                """
                
                enhancement_response = await self._send_to_agent(
                    AgentType.ENHANCEMENT.value,
                    enhancement_message,
                    session_id,
                    user_id
                )
                iteration_data["enhancement"] = enhancement_response
                responses.append(enhancement_response)
                
                # Save enhancement data to database
                if SUPABASE_ENABLED and iteration_id and enhancement_response.success and enhancement_response.parsed_json:
                    try:
                        enhanced_content = enhancement_response.parsed_json.get("enhanced_content", "")
                        changes_made = enhancement_response.parsed_json.get("changes_made", {})
                        rationale = enhancement_response.parsed_json.get("rationale", "")
                        confidence_score = enhancement_response.parsed_json.get("confidence_score", 0)
                        
                        await supabase_service.save_enhancement_data(
                            iteration_id=iteration_id,
                            enhanced_content=str(enhanced_content),
                            changes_made=changes_made,
                            rationale=rationale,
                            confidence_score=confidence_score
                        )
                        print(f"[IMPROVEMENT] Saved enhancement for iteration {iteration_num}")
                    except Exception as e:
                        print(f"[WARNING] Could not save enhancement data: {e}")
                
                if not enhancement_response.success or not enhancement_response.parsed_json:
                    break
                
                # Update current content with enhanced version
                enhanced_content = enhancement_response.parsed_json.get("enhanced_content", current_content)
                content_structure = enhancement_response.parsed_json.get("content_structure", "text")
                
                # If enhanced content is structured, format it properly for next iteration
                if content_structure == "json" and isinstance(enhanced_content, dict):
                    # Store structured content for database saving
                    iteration_data["structured_content"] = enhanced_content
                    # Format for next critique iteration
                    if content_type == "plot":
                        current_content = f"Title: {enhanced_content.get('title', 'Untitled')}\n\nPlot Summary: {enhanced_content.get('plot_summary', '')}"
                    elif content_type == "author":
                        current_content = f"Author: {enhanced_content.get('author_name', 'Unknown')}\n\nBiography: {enhanced_content.get('biography', '')}\n\nWriting Style: {enhanced_content.get('writing_style', '')}"
                    else:
                        current_content = str(enhanced_content)
                else:
                    current_content = enhanced_content
                
                # Step 3: Scoring
                previous_scores = []
                for it in iterations:
                    if isinstance(it.get('score'), dict):
                        score_data = it['score']
                        previous_scores.append(score_data.get('overall_score', 0))
                    else:
                        score_response = it.get('score')
                        if score_response and hasattr(score_response, 'parsed_json') and score_response.parsed_json:
                            previous_scores.append(score_response.parsed_json.get('overall_score', 0))
                        else:
                            previous_scores.append(0)
                
                scoring_message = f"""
                Content to Score (Iteration {iteration_num}):
                {current_content}
                
                Previous Scores: {previous_scores}
                
                Please evaluate this content using the standardized rubric.
                """
                
                scoring_response = await self._send_to_agent(
                    AgentType.SCORING.value,
                    scoring_message,
                    session_id,
                    user_id
                )
                iteration_data["score"] = scoring_response
                responses.append(scoring_response)
                
                # Save score data to database
                if SUPABASE_ENABLED and iteration_id and scoring_response.success and scoring_response.parsed_json:
                    try:
                        score_data = scoring_response.parsed_json
                        await supabase_service.save_score_data(
                            iteration_id=iteration_id,
                            overall_score=score_data.get("overall_score", 0),
                            category_scores=score_data.get("category_scores", {}),
                            score_rationale=score_data.get("rationale", ""),
                            improvement_trajectory=score_data.get("improvement_trajectory", "unknown"),
                            recommendations=score_data.get("recommendations", "")
                        )
                        print(f"[IMPROVEMENT] Saved score for iteration {iteration_num}: {score_data.get('overall_score', 0)}")
                    except Exception as e:
                        print(f"[WARNING] Could not save score data: {e}")
                
                if not scoring_response.success or not scoring_response.parsed_json:
                    break
                
                # Add iteration to list
                iterations.append(iteration_data)
                
                # Check if we've reached the target score
                overall_score = scoring_response.parsed_json.get("overall_score", 0)
                if overall_score >= target_score:
                    # Success! Target score reached
                    final_content = current_content
                    final_structured_content = iteration_data.get("structured_content", None)
                    
                    # Save enhanced content back to database if we have structured content
                    saved_content = None
                    if final_structured_content and selected_content.get("content_id") and SUPABASE_ENABLED:
                        try:
                            content_id = selected_content["content_id"]
                            if content_type == "plot":
                                saved_content = await supabase_service.save_enhanced_plot(content_id, final_structured_content)
                            elif content_type == "author":
                                saved_content = await supabase_service.save_enhanced_author(content_id, final_structured_content)
                        except Exception as e:
                            print(f"Error saving enhanced content to database: {e}")
                    
                    # Complete improvement session - target score reached
                    if SUPABASE_ENABLED and improvement_session_id:
                        try:
                            await supabase_service.update_improvement_session_status(
                                improvement_session_id=improvement_session_id,
                                status="completed",
                                final_content=final_content,
                                final_score=overall_score,
                                completion_reason="target_score_reached"
                            )
                            print(f"[IMPROVEMENT] Completed session: target score {overall_score} reached")
                        except Exception as e:
                            print(f"[WARNING] Could not complete improvement session: {e}")
                    
                    return {
                        "success": True,
                        "responses": responses,
                        "workflow_completed": True,
                        "orchestrator_routing": routing_data,
                        "improvement_session": {
                            "iterations": iterations,
                            "final_score": overall_score,
                            "final_content": final_content,
                            "final_structured_content": final_structured_content,
                            "content_type": content_type,
                            "original_content_id": selected_content.get("content_id") if selected_content else None,
                            "saved_to_database": saved_content is not None,
                            "completion_reason": "score_threshold_met",
                            "total_iterations": iteration_num
                        }
                    }
            
            # Max iterations reached
            final_score = iterations[-1]["score"].parsed_json.get("overall_score", 0) if iterations else 0
            final_structured_content = iterations[-1].get("structured_content", None) if iterations else None
            
            # Save enhanced content back to database even if max iterations reached
            saved_content = None
            if final_structured_content and selected_content.get("content_id") and SUPABASE_ENABLED:
                try:
                    content_id = selected_content["content_id"]
                    if content_type == "plot":
                        saved_content = await supabase_service.save_enhanced_plot(content_id, final_structured_content)
                    elif content_type == "author":
                        saved_content = await supabase_service.save_enhanced_author(content_id, final_structured_content)
                except Exception as e:
                    print(f"Error saving enhanced content to database: {e}")
            
            # Complete improvement session - max iterations reached
            if SUPABASE_ENABLED and improvement_session_id:
                try:
                    await supabase_service.update_improvement_session_status(
                        improvement_session_id=improvement_session_id,
                        status="completed",
                        final_content=current_content,
                        final_score=final_score,
                        completion_reason="max_iterations_reached"
                    )
                    print(f"[IMPROVEMENT] Completed session: max iterations reached, final score {final_score}")
                except Exception as e:
                    print(f"[WARNING] Could not complete improvement session: {e}")
            
            return {
                "success": True,
                "responses": responses,
                "workflow_completed": True,
                "orchestrator_routing": routing_data,
                "improvement_session": {
                    "iterations": iterations,
                    "final_score": final_score,
                    "final_content": current_content,
                    "final_structured_content": final_structured_content,
                    "content_type": content_type,
                    "original_content_id": selected_content.get("content_id") if selected_content else None,
                    "saved_to_database": saved_content is not None,
                    "completion_reason": "max_iterations_reached",
                    "total_iterations": len(iterations)
                }
            }
        
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
                "author_generator": "Creates author profiles matching microgenre/audience",
                "critique": "Provides comprehensive constructive critique on any content type",
                "enhancement": "Enhances content based on critique feedback to improve quality",
                "scoring": "Evaluates content quality using standardized scoring rubric"
            }
        }

# Global multi-agent system instance
multi_agent_system = MultiAgentSystem()