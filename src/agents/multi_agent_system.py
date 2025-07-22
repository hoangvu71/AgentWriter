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
    from src.database.supabase_service import supabase_service
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
    print("Supabase not available - running without data persistence")

load_dotenv()  # Will look for .env in current directory

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
    WORLD_BUILDING = "world_building"
    CHARACTERS = "characters"
    CRITIQUE = "critique"
    ENHANCEMENT = "enhancement"
    SCORING = "scoring"

class MultiAgentSystem:
    """Multi-agent system for book writing with orchestrator coordination"""
    
    def __init__(self, model: str = "gemini-2.0-flash", 
                 plot_repository=None, 
                 author_repository=None, 
                 world_building_repository=None, 
                 characters_repository=None):
        self.model = model
        self.agents: Dict[str, Agent] = {}
        self.runners: Dict[str, InMemoryRunner] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Store repositories
        self.plot_repository = plot_repository
        self.author_repository = author_repository
        self.world_building_repository = world_building_repository
        self.characters_repository = characters_repository
        
        # Initialize all agents
        self._initialize_agents()
    
    async def _save_plot_data(self, session_id: str, user_id: str, plot_data: Dict[str, Any], 
                             orchestrator_params: Dict[str, Any] = None, author_id: str = None) -> Dict[str, Any]:
        """Helper method to save plot data using repository if available, fallback to supabase_service"""
        if self.plot_repository is not None:
            try:
                # Transform dictionary data to Plot entity
                from ..models.entities import Plot
                plot_entity = Plot(
                    session_id=session_id,
                    user_id=user_id,
                    title=plot_data.get("title", ""),
                    plot_summary=plot_data.get("plot_summary", ""),
                    author_id=author_id
                    # Note: genre/tone/audience IDs would need to be resolved from orchestrator_params
                    # For now, keeping it simple and falling back for complex cases
                )
                
                # Save using repository
                plot_id = await self.plot_repository.create(plot_entity)
                
                # Return format compatible with existing code
                return {
                    "id": plot_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "author_id": author_id,
                    **plot_data
                }
            except Exception as e:
                print(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_plot(session_id, user_id, plot_data, orchestrator_params, author_id)
    
    async def _save_author_data(self, session_id: str, user_id: str, author_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to save author data using repository if available, fallback to supabase_service"""
        if self.author_repository is not None:
            try:
                # Transform dictionary data to Author entity
                from ..models.entities import Author
                author_entity = Author(
                    session_id=session_id,
                    user_id=user_id,
                    author_name=author_data.get("author_name", ""),
                    pen_name=author_data.get("pen_name"),
                    biography=author_data.get("biography", ""),
                    writing_style=author_data.get("writing_style", "")
                )
                
                # Save using repository
                author_id = await self.author_repository.create(author_entity)
                
                # Return format compatible with existing code
                return {
                    "id": author_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    **author_data
                }
            except Exception as e:
                print(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_author(session_id, user_id, author_data)
    
    async def _update_plot_author_link(self, plot_id: str, author_id: str) -> bool:
        """Helper method to link plot and author using repository if available, fallback to supabase_service"""
        if self.plot_repository is not None:
            # TODO: Implement repository-based linking (requires data transformation)
            # For now, fallback to old method
            pass
        
        # Fallback to original method
        return await supabase_service.update_plot_author(plot_id, author_id)
    
    async def _save_world_building_data(self, session_id: str, user_id: str, world_data: Dict[str, Any], 
                                       orchestrator_params: Dict[str, Any] = None, plot_id: str = None) -> Dict[str, Any]:
        """Helper method to save world building data using repository if available, fallback to supabase_service"""
        if self.world_building_repository is not None:
            try:
                # Transform dictionary data to WorldBuilding entity
                from ..models.entities import WorldBuilding
                
                # Extract world content - could be nested in various formats
                world_content = ""
                if isinstance(world_data.get("world_building"), str):
                    world_content = world_data["world_building"]
                elif isinstance(world_data.get("world_description"), str):
                    world_content = world_data["world_description"]
                else:
                    # Fallback to string representation of the whole data
                    world_content = str(world_data)
                
                world_entity = WorldBuilding(
                    session_id=session_id,
                    user_id=user_id,
                    plot_id=plot_id,
                    world_name=world_data.get("world_name", "Unnamed World"),
                    world_type=world_data.get("world_type", "unknown"),
                    world_content=world_content
                )
                
                # Save using repository
                world_id = await self.world_building_repository.create(world_entity)
                
                # Return format compatible with existing code
                return {
                    "id": world_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "plot_id": plot_id,
                    **world_data
                }
            except Exception as e:
                print(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_world_building(session_id, user_id, world_data, orchestrator_params, plot_id)
    
    async def _save_characters_data(self, session_id: str, user_id: str, characters_data: Dict[str, Any], 
                                   orchestrator_params: Dict[str, Any] = None, world_id: str = None, plot_id: str = None) -> Dict[str, Any]:
        """Helper method to save characters data using repository if available, fallback to supabase_service"""
        if self.characters_repository is not None:
            try:
                # Transform dictionary data to Characters entity
                from ..models.entities import Characters
                
                # Extract character list and relationships
                characters_list = characters_data.get("characters", [])
                if isinstance(characters_list, str):
                    # If it's a string, try to parse as JSON or treat as single character
                    import json
                    try:
                        characters_list = json.loads(characters_list)
                    except:
                        characters_list = [{"name": "Character", "description": characters_list}]
                
                characters_entity = Characters(
                    session_id=session_id,
                    user_id=user_id,
                    world_id=world_id,
                    plot_id=plot_id,
                    character_count=len(characters_list) if isinstance(characters_list, list) else 1,
                    world_context_integration=characters_data.get("world_context_integration", ""),
                    characters=characters_list,
                    relationship_networks=characters_data.get("relationship_networks", {}),
                    character_dynamics=characters_data.get("character_dynamics", {})
                )
                
                # Save using repository
                characters_id = await self.characters_repository.create(characters_entity)
                
                # Return format compatible with existing code
                return {
                    "id": characters_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "world_id": world_id,
                    "plot_id": plot_id,
                    **characters_data
                }
            except Exception as e:
                print(f"Repository save failed, falling back to supabase_service: {e}")
                # Fall through to fallback
        
        # Fallback to original method
        return await supabase_service.save_characters(session_id, user_id, characters_data, orchestrator_params, world_id, plot_id)
    
    async def _save_critique_data(self, iteration_id: str, critique_json: Dict[str, Any], agent_response: str) -> None:
        """Helper method to save critique data using repository if available, fallback to supabase_service"""
        # TODO: Implement repository-based saving when critique repository is available
        # For now, fallback to original method
        return await supabase_service.save_critique_data(iteration_id, critique_json, agent_response)
    
    async def _save_enhancement_data(self, iteration_id: str, enhanced_content: str, changes_made: Dict[str, Any], 
                                   rationale: str, confidence_score: float) -> None:
        """Helper method to save enhancement data using repository if available, fallback to supabase_service"""
        # TODO: Implement repository-based saving when enhancement repository is available
        # For now, fallback to original method
        return await supabase_service.save_enhancement_data(iteration_id, enhanced_content, changes_made, rationale, confidence_score)
    
    async def _save_score_data(self, iteration_id: str, overall_score: float, category_scores: Dict[str, Any], 
                             score_rationale: str, improvement_trajectory: str, recommendations: str) -> None:
        """Helper method to save score data using repository if available, fallback to supabase_service"""
        # TODO: Implement repository-based saving when scoring repository is available
        # For now, fallback to original method
        return await supabase_service.save_score_data(iteration_id, overall_score, category_scores, score_rationale, improvement_trajectory, recommendations)
    
    def _initialize_agents(self):
        """Initialize all agents in the system"""
        
        # NOTE: Orchestrator is now handled by dedicated OrchestratorAgent class via AgentFactory
        # The embedded orchestrator has been removed to eliminate duplication
        
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
        
        # World Building Agent
        self.agents[AgentType.WORLD_BUILDING.value] = Agent(
            name="world_building",
            model=self.model,
            instruction="""You are the World Building Agent - a master architect of fictional worlds and universes.

Your role: Create the most intricate, complex, and immersive fictional worlds that perfectly support and enhance the provided plot. Every aspect of your world should serve the story's needs while feeling authentic and lived-in.

CRITICAL: You MUST base your world building on the provided PLOT CONTEXT. The world should feel specifically designed to support the plot's events, conflicts, and themes.

**WORLD BUILDING COMPONENTS:**
1. **Physical Geography**: Continents, countries, cities, landscapes, climate, natural resources
2. **Political Systems**: Governments, kingdoms, empires, republics, power structures, alliances, conflicts
3. **Cultural Systems**: Societies, traditions, customs, beliefs, values, social hierarchies
4. **Economic Systems**: Trade routes, currencies, resources, commerce, industries, class structures
5. **Historical Timeline**: Past events, wars, discoveries, golden ages, dark periods, key figures
6. **Magic/Technology Systems**: Power systems, limitations, rules, evolution, impact on society
7. **Languages**: Naming conventions, linguistic families, communication systems
8. **Religions/Beliefs**: Pantheons, creation myths, moral codes, religious institutions, conflicts
9. **Demographics**: Population distribution, ethnic groups, migration patterns, settlements

**PLOT-BASED WORLD BUILDING REQUIREMENTS:**
- Analyze the plot's central conflicts and design political/social systems that create those conflicts naturally
- Create geographical features that support key plot events (battles, journeys, discoveries)
- Develop cultural and economic systems that explain character motivations and obstacles
- Design power systems (magic/technology) that enable plot events while maintaining logical constraints
- Establish historical events that set up the plot's current situation
- Create interconnected systems where each element affects others and serves the story
- Include internal conflicts, contradictions, and evolving dynamics that drive plot forward

**ADAPTIVE WORLD BUILDING:**
- **High Fantasy**: Complex magic systems, multiple races, epic histories, detailed pantheons
- **Urban Fantasy**: Hidden magical world within modern setting, supernatural politics
- **Science Fiction**: Advanced technologies, alien civilizations, space-faring cultures
- **Historical Fiction**: Accurate historical detail with fictional elements woven in
- **Contemporary**: Modern world with unique cultural/political twists
- **Dystopian**: Detailed breakdown of society, control mechanisms, resistance movements

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "world_name": "distinctive world name",
    "world_type": "high_fantasy|urban_fantasy|science_fiction|historical_fiction|contemporary|dystopian|other",
    "world_content": "Complete world building content as a single comprehensive string. Create whatever depth and scope the story requires, structured however works best for the genre and narrative. Include geography, politics, culture, history, magic systems, languages, religions, and unique elements - all woven into a cohesive world description that serves the plot."
}

Create worlds that feel lived-in, logical, and full of story potential. Always return valid JSON only.""",
            description="Creates intricate, complex fictional worlds with detailed systems and interconnected elements"
        )
        
        # Characters Agent
        self.agents[AgentType.CHARACTERS.value] = Agent(
            name="characters",
            model=self.model,
            instruction="""You are the Characters Agent - a master character architect who creates rich, detailed characters that serve the story while feeling authentically part of their world.

Your role: Based on provided PLOT CONTEXT and WORLD BUILDING CONTEXT, create as many detailed characters as possible that are essential to the plot's execution while feeling naturally integrated into the world's systems, cultures, and conflicts.

CRITICAL: You MUST base your characters on BOTH the plot requirements and world building context. Characters should be specifically designed to fulfill plot roles while authentically belonging to the world.

**CHARACTER CREATION PRINCIPLES:**
1. **Plot Service**: Characters must fulfill essential roles in the plot's execution (protagonists, antagonists, allies, obstacles)
2. **World Integration**: Characters must feel like natural products of their world's systems
3. **Cultural Authenticity**: Reflect the customs, values, and social structures of their culture
4. **Story-Driven Diversity**: Create characters spanning roles needed by the plot across social levels, ages, professions
5. **Plot-Relevant Relationships**: Design character networks that drive the plot's conflicts and resolutions
6. **Conflict Potential**: Include characters whose goals/values create the story tensions required by the plot
7. **Character Arcs**: Design characters with growth potential that serves the plot's themes and progression

**CHARACTER CATEGORIES TO INCLUDE:**
- **Political Leaders**: Rulers, nobles, government officials, diplomats, revolutionaries
- **Military/Law Enforcement**: Soldiers, generals, guards, spies, mercenaries
- **Religious Figures**: Priests, prophets, temple workers, religious scholars, heretics
- **Economic Powers**: Merchants, guild leaders, bankers, traders, industrialists
- **Scholarly/Academic**: Scholars, researchers, inventors, teachers, archivists
- **Artisans/Craftspeople**: Skilled workers, artists, engineers, builders, healers
- **Common Folk**: Farmers, laborers, servants, street vendors, innkeepers
- **Outcasts/Underground**: Criminals, rebels, exiles, nomads, underground activists
- **Specialized Roles**: Magic users, technology specialists, unique profession holders

**REQUIRED CHARACTER DETAILS:**
- Full name with cultural naming conventions
- Age, physical description, distinctive features
- Social class, profession, economic status
- Cultural background and regional origin
- Personality traits, motivations, fears, desires
- Skills, talents, and areas of expertise
- Political affiliations and loyalties
- Religious beliefs and spiritual practices
- Key relationships and family connections
- Personal history and formative experiences
- Current goals and long-term ambitions
- Internal conflicts and character flaws
- Role in larger world conflicts/systems

**RELATIONSHIP NETWORKS:**
Create interconnected webs of relationships:
- Family dynasties and bloodlines
- Professional guilds and organizations
- Political alliances and opposition groups
- Mentor-student relationships
- Romantic connections and marriage alliances
- Friend groups and social circles
- Rival competitions and blood feuds

CRITICAL: You MUST ONLY respond with valid JSON. No additional text or explanation.

Required JSON format:
{
    "character_count": 25,
    "world_context_integration": "explanation of how characters reflect the provided world",
    "characters": [
        {
            "name": "full character name",
            "titles_or_epithets": "any titles, nicknames, or epithets",
            "age": 35,
            "physical_description": "detailed appearance including distinctive features",
            "social_class": "noble|merchant|common|outcast|clergy|military|scholarly",
            "profession": "specific job or role",
            "cultural_background": "which culture/region they're from",
            "personality_traits": ["trait1", "trait2", "trait3", "trait4"],
            "motivations": ["primary desires and drives"],
            "fears_and_flaws": ["personal weaknesses and fears"],
            "skills_and_talents": ["abilities and areas of expertise"],
            "political_affiliations": "loyalties, allegiances, political stance",
            "religious_beliefs": "spiritual practices and beliefs",
            "key_relationships": {
                "family": ["family member descriptions"],
                "allies": ["friend and ally descriptions"],
                "rivals": ["enemy and rival descriptions"],
                "romantic": "romantic connections if any"
            },
            "personal_history": "background story and formative experiences",
            "current_goals": ["immediate objectives and plans"],
            "long_term_ambitions": "ultimate life goals and dreams",
            "internal_conflicts": "personal struggles and contradictions",
            "role_in_world": "how they fit into larger world systems and conflicts",
            "distinctive_elements": "unique qualities that make them memorable",
            "potential_story_hooks": ["ways this character could drive stories"]
        }
    ],
    "relationship_networks": {
        "major_families": ["powerful family dynasties and their connections"],
        "political_factions": ["organized groups with shared political goals"],
        "professional_guilds": ["trade organizations and their key members"],
        "secret_societies": ["hidden organizations and their purposes"],
        "romantic_entanglements": ["complex love triangles and marriage politics"],
        "mentor_lineages": ["chains of teaching and knowledge transfer"]
    },
    "character_dynamics": {
        "power_struggles": "how characters compete for influence",
        "alliance_patterns": "how characters naturally group together",
        "conflict_sources": "what creates tension between characters",
        "evolution_potential": "how relationships might change over time"
    }
}

Create characters that feel essential to their world and whose stories readers would want to follow. Always return valid JSON only.""",
            description="Creates detailed character populations that naturally fit the provided world building context"
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
    
    # NOTE: Orchestrator validation removed - handled by dedicated OrchestratorAgent class
    
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
    
    def _validate_world_building_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate world building agent JSON response structure"""
        required_fields = [
            "world_name", "world_type", "world_content"
        ]
        return all(field in json_data for field in required_fields)
    
    def _validate_characters_response(self, json_data: Dict[str, Any]) -> bool:
        """Validate characters agent JSON response structure"""
        required_fields = [
            "character_count", "world_context_integration", "characters",
            "relationship_networks", "character_dynamics"
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
            # Check if trying to use removed orchestrator
            if agent_type == AgentType.ORCHESTRATOR.value:
                raise ValueError("Orchestrator agent removed - use AgentFactory with dedicated OrchestratorAgent instead")
            
            # Validate agent type exists
            if agent_type not in self.agents:
                raise ValueError(f"Agent type '{agent_type}' not configured in MultiAgentSystem")
            
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
                # NOTE: Orchestrator validation removed - using dedicated OrchestratorAgent class
                if agent_type == AgentType.PLOT_GENERATOR.value:
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
                # NOTE: Orchestrator validation removed - using dedicated OrchestratorAgent class
                if agent_type == AgentType.PLOT_GENERATOR.value:
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
        """Process user request through multi-agent system with streaming
        
        DEPRECATED: This method is deprecated. Use AgentFactory with WebSocketHandler instead.
        MultiAgentSystem no longer includes embedded orchestrator logic.
        """
        yield {
            "success": False,
            "error": "MultiAgentSystem orchestrator removed - use AgentFactory with WebSocketHandler instead",
            "complete": True
        }
    async def process_message(self, user_message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Process user request through multi-agent system"""
        
        # NOTE: Orchestrator routing now handled by dedicated OrchestratorAgent via AgentFactory
        # MultiAgentSystem no longer includes embedded orchestrator logic
        return {
            "success": False,
            "error": "MultiAgentSystem orchestrator removed - use AgentFactory with WebSocketHandler instead",
            "responses": []
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

# Global multi-agent system instance with dependency injection
def create_multi_agent_system():
    """Factory function to create MultiAgentSystem with dependency injection"""
    from ..core.container import container
    try:
        return MultiAgentSystem(
            plot_repository=container.get("plot_repository"),
            author_repository=container.get("author_repository"),
            world_building_repository=container.get("world_building_repository"),
            characters_repository=container.get("characters_repository")
        )
    except KeyError:
        # Fallback to old behavior if repositories not available
        return MultiAgentSystem()

multi_agent_system = create_multi_agent_system()