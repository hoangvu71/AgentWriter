# Agent Reference

Detailed reference for all BooksWriter agents and their capabilities.

## Multi-Agent System Overview

BooksWriter uses 9 specialized agents working in coordination to create comprehensive book content.

## Agent Specifications

### OrchestratorAgent
- **Purpose**: Coordinates multi-agent workflows and routes requests
- **Capabilities**: Request routing, workflow coordination, tool orchestration
- **Tools**: All agent tools (delegated)
- **Implementation**: `src/agents/orchestrator.py`

### PlotGeneratorAgent
- **Purpose**: Creates detailed book plots with genre-specific elements  
- **Capabilities**: Plot generation, genre analysis, story structure
- **Tools**: `save_plot`
- **Implementation**: `src/agents/plot_generator_agent.py`

### AuthorGeneratorAgent
- **Purpose**: Develops author profiles and writing styles
- **Capabilities**: Author profile creation, writing style analysis
- **Tools**: `save_author`
- **Implementation**: `src/agents/author_generator_agent.py`

### WorldBuildingAgent
- **Purpose**: Constructs detailed fictional worlds
- **Capabilities**: World creation, geography, politics, culture
- **Tools**: `save_world_building`
- **Implementation**: `src/agents/world_building_agent.py`

### CharactersAgent
- **Purpose**: Creates character profiles and relationships
- **Capabilities**: Character development, relationship mapping
- **Tools**: `save_characters`
- **Implementation**: `src/agents/characters_agent.py`

### EnhancementAgent
- **Purpose**: Improves existing content
- **Capabilities**: Content enhancement, quality improvement
- **Tools**: Content improvement tools
- **Implementation**: `src/agents/enhancement_agent.py`

### CritiqueAgent
- **Purpose**: Provides constructive feedback
- **Capabilities**: Content analysis, feedback generation
- **Tools**: Critique and analysis tools
- **Implementation**: `src/agents/critique_agent.py`

### ScoringAgent
- **Purpose**: Evaluates content quality
- **Capabilities**: Quality scoring, metrics analysis
- **Tools**: Scoring and evaluation tools
- **Implementation**: `src/agents/scoring_agent.py`

### LoreGenAgent
- **Purpose**: Expands world lore using RAG and clustering
- **Capabilities**: Lore generation, content clustering, RAG integration
- **Tools**: Lore expansion tools
- **Implementation**: `src/agents/loregen_agent.py`

## Agent Communication

All agents communicate through:
- **Tool-based coordination**: Agents use tools to save and retrieve data
- **Orchestrator routing**: Central coordination through OrchestratorAgent
- **Database persistence**: All agent outputs stored in Supabase

## Tool Integration

### Core Tools
- `save_plot` - Persists plot data with validation
- `save_author` - Stores author profiles  
- `save_world_building` - Saves world details with plot linkage
- `save_characters` - Stores character data with relationships
- `search_content` - Unified content search across all types

### Tool Usage Patterns
Each agent follows consistent patterns:
1. Receive user request through orchestrator
2. Process request using AI model
3. Format response according to tool requirements
4. Save results using appropriate tool
5. Return formatted response to user

## Related Documentation

- **[Multi-Agent System](../architecture/agents.md)** - System architecture
- **[Architecture Overview](../architecture/overview.md)** - Complete system design
- **[Development Workflow](../guides/development.md)** - Agent development practices

---

*This reference provides comprehensive information about all BooksWriter agents and their integration patterns.*