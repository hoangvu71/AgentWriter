# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**BooksWriter** is a sophisticated multi-agent system for AI-powered book writing, built with:
- **Google Agent Development Kit (ADK)** for agent orchestration
- **Vertex AI/Gemini** models for content generation
- **FastAPI** backend with WebSocket support
- **Supabase** (PostgreSQL) for cloud persistence
- **SQLite** for local development
- **Open-WebUI** integration for enhanced frontend
- **MCP Supabase** integration for direct database interaction

## Current State (January 2025)

### ✅ Completed
1. **Full TDD Implementation** - All 54+ components follow Test-Driven Development
2. **Multi-Agent System** - 9 specialized agents working in coordination
3. **Tool-Based Orchestration** - Orchestrator uses tools instead of manual loops
4. **Database Layer** - Dual support for Supabase (production) and SQLite (development)
5. **WebSocket Real-Time Communication** - Streaming responses and status updates
6. **Open-WebUI Integration** - Alternative frontend with OpenAI-compatible API
7. **MCP Supabase Integration** - Direct database access via Model Context Protocol

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                        │
├─────────────────────┬───────────────────────────────────────┤
│   Vanilla JS UI     │        Open-WebUI (Optional)          │
├─────────────────────┴───────────────────────────────────────┤
│                      API/WebSocket Layer                      │
├─────────────────────────────────────────────────────────────┤
│                    Multi-Agent System                         │
├──────────┬───────────┬──────────┬──────────┬────────────────┤
│Orchestrator│   Plot   │  Author  │  World   │  Characters   │
├──────────┴───────────┼──────────┼──────────┼────────────────┤
│    Enhancement       │ Critique │ Scoring  │   LoreGen      │
├──────────────────────┴──────────┴──────────┴────────────────┤
│                     Service Layer                             │
├─────────────────────────────┬───────────────────────────────┤
│     Database Layer          │        MCP Integration        │
│   (Supabase/SQLite)         │   (Direct DB Operations)      │
└─────────────────────────────┴───────────────────────────────┘
```

## Key Components

### Agents (src/agents/)
1. **OrchestratorAgent** - Coordinates multi-agent workflows using tools
2. **PlotGeneratorAgent** - Creates book plots with genre-specific elements
3. **AuthorGeneratorAgent** - Develops author profiles and writing styles
4. **WorldBuildingAgent** - Constructs detailed fictional worlds
5. **CharactersAgent** - Creates character profiles and relationships
6. **EnhancementAgent** - Improves existing content
7. **CritiqueAgent** - Provides constructive feedback
8. **ScoringAgent** - Evaluates content quality
9. **LoreGenAgent** - Expands world lore using RAG and clustering

### Tools (src/tools/)
- **save_plot** - Persists plot data with validation
- **save_author** - Stores author profiles
- **save_world_building** - Saves world details with plot linkage
- **save_characters** - Stores character data with world/plot relationships
- **search_content** - Unified content search across all types

### Critical Fixes Applied
1. **Async Bug Fix** - All agents' `_prepare_message` methods are now async
2. **Tool Interface Alignment** - Agent instructions match actual tool parameters
3. **Database Schema Consistency** - SQLite and Supabase schemas are synchronized
4. **Foreign Key Handling** - Proper UUID format and relationship management
5. **Service Parameter Validation** - ContentSavingService validates all inputs
6. **Legacy Code Cleanup (Issue #5)** - Removed deprecated code and TODO markers:
   - Removed deprecated `run_async_in_sync` function, replaced with `run_async_safe`
   - Removed unused `_handle_legacy_agent_processing` method from WebSocket handler
   - Removed deprecated `_extract_context` method from orchestrator agent
   - Added deprecation warnings to legacy context service methods
   - Added deprecation warnings to legacy content saving service methods
   - Marked legacy Gemini models (1.5-pro, 1.5-flash) as deprecated with replacement recommendations
   - Resolved all TODO/FIXME comments with proper solutions or documentation

## Environment Setup

### Required Environment Variables
```bash
# Google Cloud / Vertex AI (Required)
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Supabase (Optional - for cloud persistence)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Model Configuration
MODEL_NAME=gemini-2.0-flash-exp  # or gemini-1.5-flash-002

# MCP Supabase Integration (Optional - for direct database access)
SUPABASE_ACCESS_TOKEN=your-personal-access-token
```

### Quick Start Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (all should pass)
pytest

# Start backend
python -m uvicorn src.app:app --reload

# Start with Open-WebUI (optional)
docker-compose -f docker-compose.openwebui.yml up -d
```

## Common Tasks

### Running Specific Tests
```bash
# Run TDD tests for specific components
pytest tests/test_tdd_base_repository.py -v
pytest tests/test_tdd_author_generator_agent.py -v
pytest tests/test_tdd_plot_generator_agent.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Adding a New Agent
1. Create agent class inheriting from `BaseAgent`
2. Implement `_prepare_message()` method (must be async)
3. Add to `AgentFactory.create_agent()`
4. Create TDD tests following existing patterns
5. Update orchestrator tools if needed

### Working with MCP Supabase
```bash
# Test MCP connection
curl -X POST http://localhost:8000/mcp/tools/get_tables

# Query database via MCP
curl -X POST http://localhost:8000/mcp/tools/query_data \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM plots LIMIT 5"}'

# Check MCP server status
ps aux | grep supabase-mcp
```

### Debugging WebSocket Issues
- Check `src/websocket/websocket_handler.py` for message handling
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Monitor WebSocket frames in browser DevTools

## Known Issues & Workarounds

### 1. Model Loading in UI
**Issue**: AI models dropdown sometimes doesn't populate
**Fix**: Implemented proper initialization order and error handling

### 2. UUID Format Errors
**Issue**: Mixing UUID strings and objects
**Fix**: Standardized on string UUIDs throughout the system

### 3. Vertex AI Timeouts
**Issue**: Long operations (30+ seconds) for lore generation
**Workaround**: Increased timeouts, added progress indicators

## Testing Philosophy

This project follows strict TDD methodology:
1. **RED** - Write failing tests that define requirements
2. **GREEN** - Implement minimal code to pass tests
3. **REFACTOR** - Improve code while keeping tests green

All 54+ components have comprehensive test coverage.

## MCP Supabase Integration

The project includes **Model Context Protocol (MCP)** integration for direct Supabase database access, enabling AI assistants to interact with the database through specialized tools.

### Capabilities
- **Direct Database Operations** - Query, insert, update, and delete operations
- **Schema Management** - View and modify table structures
- **Configuration Access** - Retrieve project settings and metadata
- **Development Tools** - Support for database development workflows

### Setup
1. **Install MCP Server**: `npm install -g @supabase/mcp-server-supabase`
2. **Configure Access Token**: Set `SUPABASE_ACCESS_TOKEN` in environment
3. **MCP Configuration**: Located in `.claude/mcp.json`

### Security Configuration
```json
{
  "servers": {
    "supabase": {
      "command": "npx",
      "args": ["@supabase/mcp-server-supabase@latest"],
      "env": {
        "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}"
      }
    }
  }
}
```

### Best Practices
- **Development Only** - Use with development/staging projects
- **Read-Only Mode** - Enable for safer database interactions
- **Project Scoping** - Limit access to specific Supabase projects
- **Review Tool Calls** - Always verify AI-generated database operations

### Available Tools
- `get_tables` - List database tables and schemas
- `query_data` - Execute SELECT queries
- `get_project_config` - Retrieve project configuration
- `manage_functions` - Handle edge functions
- Additional tools for comprehensive database management

**Note**: MCP integration is pre-1.0 and may have breaking changes. See detailed documentation in `docs/integrations/mcp-supabase.md`.

## Open-WebUI Integration

### Setup
1. Start BooksWriter backend on port 8000
2. Run `docker-compose -f docker-compose.openwebui.yml up -d`
3. Access Open-WebUI at http://localhost:3000

### Available Endpoints
- `/openai/v1/models` - List available models
- `/openai/v1/chat/completions` - Chat completion (OpenAI-compatible)
- `/ws/{session_id}` - WebSocket for real-time communication

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all function parameters and returns
- Async functions for I/O operations
- Comprehensive error handling with logging

### Git Workflow
- Commit messages should be descriptive
- Test before committing
- Use feature branches for major changes

### Adding Features
1. Write TDD tests first
2. Implement feature
3. Update documentation
4. Ensure all tests pass
5. Update CLAUDE.md if architecture changes

## Useful Commands for Debugging

```bash
# Check service health
curl http://localhost:8000/health

# List available models
curl http://localhost:8000/models

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/test-session

# View container logs
docker-compose -f docker-compose.openwebui.yml logs -f

# Database migrations (if needed)
python scripts/migrate_db.py
```

## Contact & Resources

- **Project Type**: Multi-agent book writing system
- **Primary Models**: Gemini 2.0 Flash Exp, Gemini 1.5 Flash
- **Documentation**: See **[docs/index.md](docs/index.md)** for organized documentation hub
- **Tests**: Comprehensive TDD test suite in `tests`

## For Future Claude Instances

When working on this project:
1. Always check this file first for context
2. Run tests before making changes
3. Follow TDD methodology for new features
4. Update this file with significant changes
5. Preserve the architectural integrity
6. **MCP Capabilities** - Leverage MCP Supabase tools for direct database operations
7. **Database Security** - Always use read-only mode for MCP in production contexts
8. **IMPORTANT: Always use Claude Custom Sub Agents** - Leverage specialized agents for complex tasks

Remember: This is a production-ready system with real users. Code quality and reliability are paramount.