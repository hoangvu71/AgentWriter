# Multi-Agent System Architecture

BooksWriter's multi-agent system consists of 9 specialized agents that work in coordination to generate comprehensive book content with full database persistence.

## 🎯 Agent Coordination Model

### Orchestrator Pattern
The system uses a **centralized orchestrator** that:
- Routes user requests to appropriate specialized agents
- Manages sequential workflows between agents
- Coordinates inter-agent communication
- Makes intelligent routing decisions based on user intent
- Logs all decisions for system analytics

### Tool-Based Communication
Agents communicate through **structured tools** rather than direct messaging:
- **save_plot** - Persists plot data with validation
- **save_author** - Stores author profiles
- **save_world_building** - Saves world details with plot linkage
- **save_characters** - Stores character data with world/plot relationships
- **search_content** - Unified content search across all types

## 🤖 Agent Specifications

### 1. OrchestratorAgent
**Purpose**: Central coordinator for multi-agent workflows

**Capabilities**:
- Analyzes user requests to determine required agents
- Extracts parameters for each agent invocation
- Plans sequential execution workflows
- Coordinates between agents for complex tasks
- Tracks decision analytics for system improvement

**Tools Used**:
- All agent tools for coordination
- Database logging for analytics
- Parameter extraction and validation

**Example Workflow**:
```
User: "Create a fantasy novel with author and world"
→ OrchestratorAgent analyzes request
→ Routes to PlotGeneratorAgent → AuthorGeneratorAgent → WorldBuildingAgent
→ Coordinates sequential execution with proper data linking
```

### 2. PlotGeneratorAgent
**Purpose**: Creates detailed book plots with comprehensive genre metadata

**Capabilities**:
- Generates plot summaries with full story arcs
- Includes main conflicts, character development, and resolution
- Applies genre-specific elements and tropes
- Considers target audience preferences
- Links to genre classification system

**Parameters Handled**:
- **Genre**: Fantasy, Romance, Sci-Fi, Mystery, etc.
- **Subgenre**: LitRPG, Space Opera, Cozy Mystery, etc.
- **Microgenre**: Zombie Apocalypse, Time Travel, etc.
- **Tropes**: Survive and family, Chosen one, etc.
- **Tone**: Dark, humorous, realistic, etc.
- **Target Audience**: Age range, sexual orientation, gender

**Database Integration**:
- Saves to `plots` table with full metadata
- Links to genre classification tables
- Maintains user and session relationships

**Example Output**:
```json
{
  "title": "The Echoes of Tomorrow",
  "plot_summary": "A comprehensive 2-3 paragraph plot summary that includes the full story arc, main conflicts, character development, and resolution. All plot elements are woven into the narrative.",
  "genre": "fantasy",
  "subgenre": "epic_fantasy",
  "microgenre": "portal_fantasy",
  "trope": "chosen_one",
  "tone": "dark_humor"
}
```

### 3. AuthorGeneratorAgent
**Purpose**: Creates author profiles matching microgenre and target audience

**Capabilities**:
- Generates realistic author names and pen names
- Creates comprehensive biographies and backgrounds
- Develops writing voice and style descriptions
- Establishes genre expertise and credentials
- Analyzes target audience appeal

**Content Generated**:
- Author name and pen name suggestions
- Comprehensive biography (education, background, influences)
- Writing style analysis and examples
- Genre specialization and experience
- Market positioning and audience appeal

**Database Integration**:
- Saves to `authors` table
- Links to associated plots
- Maintains plot-author relationships

**Example Output**:
```json
{
  "author_name": "Sarah Jane Mitchell",
  "pen_name": "S.J. Mitchell",
  "biography": "Born in Portland, Oregon, Sarah Jane Mitchell grew up surrounded by the misty forests of the Pacific Northwest, which deeply influenced her love for fantasy literature. With a PhD in Medieval History from Stanford University...",
  "writing_style": "Mitchell's prose is lyrical yet accessible, blending rich world-building with emotionally resonant character development. Her writing features vivid sensory details and a talent for weaving complex magic systems into relatable human stories."
}
```

### 4. WorldBuildingAgent
**Purpose**: Constructs detailed fictional worlds based on plot requirements

**Capabilities**:
- Creates intricate world geography and climate systems
- Develops political systems, governments, and power structures
- Establishes cultural traditions, religions, and social hierarchies
- Designs economic systems, trade networks, and resources
- Implements magic systems and supernatural elements (genre-appropriate)

**World Building Elements**:
- **Geography**: Physical environments, climate, natural features
- **Political Landscape**: Governments, power structures, conflicts
- **Cultural Systems**: Traditions, religions, social hierarchies
- **Economic Framework**: Trade, currency, resource distribution
- **Historical Timeline**: Past events shaping current world
- **Power Systems**: Magic, technology, supernatural elements
- **Languages**: Communication systems and linguistic diversity
- **Belief Systems**: Religions, philosophies, worldviews

**Database Integration**:
- Saves to `world_building` table with JSONB structured data
- Links to plots for context-appropriate world creation
- Supports complex nested data structures

### 5. CharactersAgent
**Purpose**: Develops detailed character populations for stories

**Capabilities**:
- Creates primary protagonists with complete character arcs
- Develops supporting characters with defined roles and relationships
- Designs antagonists with clear motivations and backgrounds
- Maps character relationship networks and dynamics
- Plans character development trajectories throughout the story

**Character Development**:
- **Primary Characters**: Protagonists with full development arcs
- **Supporting Cast**: Well-defined roles and relationships
- **Antagonists**: Complex motivations and believable conflicts
- **Relationship Networks**: How characters interact and influence each other
- **Development Arcs**: Character growth throughout the story

**Database Integration**:
- Saves to `characters` table
- Links to both plots and world building contexts
- Maintains character relationship data

### 6. EnhancementAgent
**Purpose**: Improves existing content through targeted enhancements

**Capabilities**:
- Analyzes existing content for improvement opportunities
- Enhances plot complexity and character development
- Improves world building depth and consistency
- Strengthens narrative flow and pacing
- Adds missing elements or details

**Enhancement Types**:
- Content depth and detail improvements
- Consistency fixes across related content
- Narrative flow optimization
- Character development strengthening
- World building expansion

### 7. CritiqueAgent
**Purpose**: Provides constructive feedback on generated content

**Capabilities**:
- Analyzes content against genre conventions
- Identifies plot holes and inconsistencies
- Evaluates character development quality
- Assesses world building coherence
- Provides specific improvement recommendations

**Critique Areas**:
- Plot structure and pacing
- Character development and consistency
- World building logic and detail
- Genre convention adherence
- Target audience appropriateness

### 8. ScoringAgent
**Purpose**: Evaluates content quality using objective metrics

**Capabilities**:
- Scores content across multiple quality dimensions
- Provides quantitative assessments for improvement tracking
- Compares content against successful examples
- Identifies strengths and weaknesses
- Tracks improvement over iterations

**Scoring Dimensions**:
- Plot complexity and engagement
- Character development quality
- World building depth and consistency
- Writing quality and style
- Genre convention adherence

### 9. LoreGenAgent
**Purpose**: Expands world lore using RAG and clustering techniques

**Capabilities**:
- Uses Retrieval-Augmented Generation for lore expansion
- Employs clustering to organize and categorize lore elements
- Generates consistent additional world details
- Maintains coherence with existing world building
- Creates rich background lore for immersive worlds

**Advanced Features**:
- **RAG Integration**: Uses existing lore to generate consistent additions
- **Clustering Service**: Organizes lore elements by themes and categories
- **Consistency Checking**: Ensures new lore aligns with existing world
- **Deep World Building**: Creates extensive background details

## 🔄 Agent Workflows

### Sequential Workflow Example
```
User Request: "Create complete story foundation"
↓
OrchestratorAgent
├── Analyzes request: plot + world + characters needed
├── Plans execution order: plot → world → characters
└── Coordinates execution:
    ├── PlotGeneratorAgent creates base plot
    ├── WorldBuildingAgent uses plot context
    └── CharactersAgent uses both plot and world context
```

### Iterative Improvement Workflow
```
Initial Content Creation
↓
CritiqueAgent analyzes content
↓
ScoringAgent provides quantitative assessment
↓
EnhancementAgent improves based on feedback
↓
Repeat until quality threshold met
```

### Cross-Agent Content Sharing
```python
# CharactersAgent accessing WorldBuildingAgent content
def get_world_context(self, plot_id):
    """Get world building context for character creation"""
    query = """
    SELECT world_name, overview, cultural_systems, power_systems
    FROM world_building 
    WHERE plot_id = %s
    """
    return world_context

# WorldBuildingAgent accessing PlotGeneratorAgent content
def get_plot_requirements(self, plot_id):
    """Get plot details to inform world building"""
    query = """
    SELECT genre, subgenre, tone, target_audience, plot_summary
    FROM plots 
    WHERE id = %s
    """
    return plot_details
```

## 🛠️ Agent Architecture

### BaseAgent Class
All agents inherit from `BaseAgent` which provides:

- **Conversation Continuity**: Automatic conversation history integration
- **Tool Integration**: Standardized tool calling interface
- **Error Handling**: Comprehensive error management
- **Performance Tracking**: Automatic performance metrics
- **Memory Management**: User preference and context management

### Agent Lifecycle
```python
class BaseAgent:
    async def _prepare_message(self, request: AgentRequest) -> str:
        # Load conversation context
        # Inject user preferences
        # Prepare agent-specific message
        
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        # Execute agent logic
        # Call appropriate tools
        # Save results to database
        # Update conversation memory
```

### Critical Implementation Details

#### 1. Async Bug Fix
All agents' `_prepare_message` methods are **async** to support:
- Database operations
- External API calls
- Tool executions
- Memory management

#### 2. Tool Interface Alignment
Agent instructions match actual tool parameters:
- Consistent parameter naming
- Proper data validation
- Clear tool documentation

#### 3. Database Schema Consistency
SQLite and Supabase schemas are synchronized:
- Identical table structures
- Consistent foreign key relationships
- Unified data types

## 📊 Agent Performance Tracking

### Agent Invocation Monitoring
Every agent call is tracked in the `agent_invocations` table:

```sql
INSERT INTO agent_invocations (
    invocation_id, agent_name, user_id, session_id,
    request_content, start_time, llm_model,
    tool_calls, success, duration_ms
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

### Performance Analytics
- **Success rates** by agent and time period
- **Average response times** for performance optimization
- **Tool usage patterns** for system improvement
- **Error rates** for reliability monitoring

## 🔧 Adding New Agents

### Step-by-Step Process

1. **Create Agent Class**:
   ```python
   class NewAgent(BaseAgent):
       async def _prepare_message(self, request: AgentRequest) -> str:
           # Agent-specific message preparation
           pass
   ```

2. **Implement Required Methods**:
   - `_prepare_message()` method (must be async)
   - Agent-specific processing logic
   - Tool integration

3. **Add to Agent Factory**:
   ```python
   # In AgentFactory.create_agent()
   elif agent_type == "new_agent":
       return NewAgent(config)
   ```

4. **Create TDD Tests**:
   - Unit tests for agent logic
   - Integration tests with tools
   - Performance tests

5. **Update Orchestrator**:
   - Add routing logic for new agent
   - Update tool coordination if needed

## 📚 Related Documentation

- **[Architecture Overview](overview.md)** - Complete system architecture
- **[Database Architecture](database.md)** - Database design and integration
- **[Agent Tools Reference](../reference/agents.md)** - Detailed tool documentation
- **[Development Workflow](../guides/development.md)** - TDD practices for agents

---

This multi-agent architecture provides a sophisticated, scalable foundation for AI-powered book writing, with each agent specializing in specific aspects of the creative process while maintaining coordination and data consistency across the entire system.