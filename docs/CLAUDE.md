# Claude AI Code Generation Instructions

## CRITICAL REQUIREMENTS

### 1. Test-Driven Development (TDD) 
- Write tests alongside implementation when adding new features
- Ensure all new code has appropriate test coverage
- Use existing test patterns in the tests/ directory
- Run tests before committing changes

### 2. Always Ask for Clarification
- NEVER assume requirements
- Ask specific questions when specs are unclear
- Confirm understanding before implementing
- Request examples when behavior is ambiguous

### 3. Keep It Simple
- NO overengineering or overcomplication
- Simplest solution that works is the best solution
- Avoid premature optimization
- Don't add features that weren't requested
- YAGNI (You Aren't Gonna Need It)

### 4. Focus on Root Causes
- Always identify the CORE issue, not symptoms
- Don't implement workarounds
- Fix the actual problem, not the surface issue
- Ask "why" multiple times to get to the root

### 5. Always Research When Unsure
- Use search function when uncertain about APIs, libraries, or implementations
- Don't guess or assume - verify with search
- Look up current best practices and documentation
- Confirm version compatibility and requirements

### 6. Multi-Agent System Design
- Each agent has a single, well-defined responsibility
- Agents communicate through the orchestrator (no direct agent-to-agent communication)
- Sequential workflows are preferred over parallel processing for complexity management
- Agent responses should be clean, formatted, and user-friendly
- All agents should maintain session state and memory

#### Current Multi-Agent Architecture
The system implements a comprehensive multi-agent ecosystem with specialized agents:

**Core Content Generation Agents:**
- **Orchestrator Agent**: Routes requests and coordinates workflows between all agents
- **Plot Generator Agent**: Creates detailed plots based on genre hierarchy and target audience
- **Author Generator Agent**: Creates author profiles matching microgenre and target audience
- **World Building Agent**: Creates intricate fictional worlds based on plot requirements
- **Characters Agent**: Creates detailed character populations based on both plot and world building contexts
- **Library Service**: Manages viewing and organizing all generated content with search/filter capabilities

**Quality Assurance Agents:**
- **Critique Agent**: Provides detailed, constructive feedback on any writing content (plots, authors, drafts, outlines, etc.)
- **Enhancement Agent**: Improves content based on critique feedback using systematic rewriting
- **Scoring Agent**: Evaluates content quality using standardized rubric (Content Quality 30%, Structure 25%, Style 20%, Genre Appropriateness 15%, Technical Execution 10%)

**Iterative Improvement Workflow:**
1. User requests improvement of existing content (plot_id or author_id)
2. Critique Agent analyzes content and provides detailed feedback
3. Enhancement Agent rewrites content addressing all critique points
4. Scoring Agent evaluates enhanced content using weighted rubric
5. Process repeats until score ≥ 9.5 or maximum 4 iterations reached
6. Final enhanced content replaces original in database

**Agent Communication Protocol:**
- All agent requests route through orchestrator with standardized JSON responses
- Agents never communicate directly - all coordination via orchestrator
- Session state maintained across multi-step workflows
- Error handling and fallback mechanisms for agent failures

**Critical Workflow Dependencies:**
- **World Building** requires **Plot Context** - worlds are designed to support specific stories
- **Characters** require **both Plot and World Building contexts** - characters serve story needs within authentic world systems
- **Proper Sequence**: Plot → World Building → Characters for complete story foundation

## Core Principles

### 1. Code Quality Standards
- Write production-ready code with proper error handling, validation, and edge cases
- Follow SOLID principles and design patterns where appropriate
- Implement defensive programming practices
- Ensure code is type-safe, performant, and maintainable
- Use meaningful variable/function names that self-document the code

### 2. Architecture & Design
- Think holistically about system architecture before implementation
- Design for scalability, maintainability, and extensibility
- Separate concerns properly (presentation, business logic, data access)
- Use appropriate design patterns (Factory, Observer, Strategy, etc.)
- Consider performance implications from the start

### 3. Best Practices by Language

#### JavaScript/TypeScript
- Always use TypeScript for type safety
- Prefer functional programming patterns where appropriate
- Use modern ES6+ syntax (arrow functions, destructuring, async/await)
- Implement proper error boundaries in React
- Use proper state management (Context API, Redux, Zustand)
- Optimize React components with memo, useMemo, useCallback

#### Python
- Follow PEP 8 style guide
- Use type hints for all functions
- Implement proper exception handling
- Use dataclasses or Pydantic for data models
- Leverage comprehensions and generators for performance
- Write Pythonic code (use enumerate, zip, itertools)

#### General
- Write comprehensive error messages
- Implement logging at appropriate levels
- Add input validation and sanitization
- Consider security implications (SQL injection, XSS, etc.)
- Write code that's testable (dependency injection, pure functions)

### 4. Development Workflow
- Always understand the existing codebase before making changes
- Check for existing patterns and follow them
- Run linters and type checkers before considering task complete
- Test edge cases and error scenarios
- Consider backward compatibility

### 5. Code Documentation
- Write clear, concise inline documentation only when necessary
- Document complex algorithms or business logic
- Include examples in function docstrings
- Keep documentation up-to-date with code changes

### 6. Performance Optimization
- Profile before optimizing
- Use appropriate data structures (Set vs Array, Map vs Object)
- Implement caching where beneficial
- Optimize database queries (indexes, query optimization)
- Consider lazy loading and code splitting

### 7. Security First
- Never hardcode secrets or credentials
- Validate and sanitize all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Follow OWASP guidelines

### 8. Testing Approach
- Write testable code from the start
- Implement unit tests for critical functions
- Use integration tests for API endpoints
- Consider edge cases in test scenarios
- Aim for meaningful test coverage, not just high percentages

### 9. Project-Specific Guidelines

#### For Book Writing Applications
- Implement auto-save functionality
- Support rich text editing with proper sanitization
- Design flexible chapter/section organization
- Implement robust import/export functionality
- Consider offline-first architecture
- Support collaborative features where applicable

#### For Multi-Agent Book Writing Systems
- Design agents with clear boundaries and responsibilities
- Implement proper orchestration logic for routing user requests
- Ensure agents can handle genre-specific requirements (Fantasy, Romance, Sci-Fi, etc.)
- Support comprehensive target audience parameters (age, orientation, gender)
- Maintain conversation memory across agent interactions
- Format agent responses for optimal user experience
- Test agent coordination and sequential workflows thoroughly

#### Current System Implementation
**Technology Stack:**
- Google AI SDK (google.adk.agents) for agent creation and management
- InMemoryRunner for session management and agent execution
- Gemini 2.0 Flash model for fast, efficient content generation
- Supabase for data persistence and normalized database schema
- FastAPI for REST API endpoints and WebSocket communication

**Agent Response Standards:**
- All agents return standardized JSON responses with consistent structure
- Content generation agents return domain-specific fields (title, plot_summary, author_name, etc.)
- Quality agents return structured analysis with scores, feedback, and improvement suggestions
- Error handling with fallback responses and graceful degradation

**Quality Assurance Integration:**
- Built-in iterative improvement system with automatic content enhancement
- Standardized scoring rubric ensuring consistent quality evaluation
- Multi-iteration workflow capable of transforming content from initial draft to professional quality
- Integration with library system for content management and version tracking

### 10. Database Schema Evolution and Migration Workflow

**QUICK REFERENCE - How Claude Applies Migrations:**
```bash
# 1. Create migration
npx supabase migration new "world_building_and_characters"

# 2. Edit supabase/migrations/YYYYMMDDHHMMSS_description.sql

# 3. Apply to database (user provides password)
npx supabase db push --password "USER_PROVIDED_PASSWORD"

# 4. Verify tables created
python scripts/database/check_tables.py
```

When making changes to database schema (adding tables, normalizing data, etc.), follow this proven workflow:

#### Phase 1: Planning & Migration Creation
1. **Create Migration File Using Supabase CLI**
   ```bash
   npx supabase migration new "description of changes"
   ```
   This creates: `supabase/migrations/YYYYMMDDHHMMSS_description.sql`

2. **Design New Schema** 
   - Use proper normalization (foreign keys instead of VARCHAR/JSONB)
   - Add appropriate indexes for performance
   - Include sample data for immediate testing
   - Use `IF NOT EXISTS` for idempotent operations
   - Edit the generated migration file with your SQL

#### Phase 2: Schema Application
3. **Apply New Schema Using Supabase CLI**
   ```bash
   # IMPORTANT: You must have the database password
   npx supabase db push --password "YOUR_DB_PASSWORD"
   ```
   
   **Getting the Database Password:**
   - Go to Supabase Dashboard → Project Settings → Database
   - Copy the database password
   - Or ask the user to provide it when needed
   
   **Alternative: Set password in environment**
   ```bash
   # Add to .env file
   SUPABASE_DB_PASSWORD=your_password_here
   
   # Then use with environment variable
   npx supabase db push --password "$SUPABASE_DB_PASSWORD"
   ```
4. **Verify Schema Creation**
   ```bash
   python scripts/database/check_tables.py
   ```
   - Check all tables created successfully
   - Verify foreign key relationships
   - Confirm indexes are in place
   - Automatically updates migration tracking

#### Phase 3: Data Migration (Critical!)
5. **Migrate Existing Data** (if needed)
   ```bash
   python migrate_existing_data.py
   ```
   - Extract data from old VARCHAR/JSONB columns
   - Create missing lookup table entries (genres, etc.)
   - Populate new foreign key columns
   - Preserve original data during migration
   
6. **Verify Data Migration**
   ```bash
   python verify_migration.py
   ```
   - Confirm all data transferred correctly
   - Check foreign key relationships work
   - Verify no data loss occurred

#### Phase 4: Cleanup
7. **Remove Old Columns** (After verification)
   ```bash
   python cleanup_old_columns.py
   ```
   - Remove redundant VARCHAR/JSONB columns
   - Keep only normalized foreign key structure
   - Verify final table structure

#### Phase 5: Code Updates
8. **Update Service Layer**
   - Modify `supabase_service.py` to use new schema
   - Update all CRUD operations
   - Test database operations
   - Update agent code if needed

#### Documentation Requirements
- Update `database_documentation.md` with new schema
- Document migration in `migrations/README.md`
- Add new tables to entity relationship documentation
- Update API documentation if schema affects endpoints

#### Critical Rules
- **NEVER skip data migration** - new foreign keys must be populated
- **ALWAYS verify before cleanup** - ensure no data loss
- **Test thoroughly** - run full system tests after migration
- **Document everything** - migrations should be self-explanatory
- **Use transactions** - ensure atomicity of migration operations

#### Database Connection Requirements

**IMPORTANT: Claude can apply migrations directly using Supabase CLI**

**Prerequisites:**
1. **Supabase CLI available via npx** (already installed)
2. **Project must be linked** to Supabase:
   ```bash
   npx supabase link --project-ref <your-project-ref>
   ```
   Get your project reference from: Supabase Dashboard → Settings → General → Reference ID
3. **Database password required** for remote operations

**Standard Migration Application Process:**
1. Create migration: `npx supabase migration new "description"`
2. Edit the SQL file in `supabase/migrations/`
3. Apply with password: `npx supabase db push --password "PASSWORD"`
4. Verify with: `python scripts/database/check_tables.py`

**Project Configuration:**
- Project Reference ID: `<your-project-ref>` (get from Supabase Dashboard → Settings → General)
- Database Host: `<your-database-host>` (get from Supabase Dashboard → Settings → Database)
- Migration Path: `supabase/migrations/`
- Tracking: `migrations/applied_migrations.json`

**Troubleshooting:**
- If "failed SASL auth": Wrong password provided
- If "No connection": Database or network issue
- If "target machine refused": Local Supabase not running (use remote)
- Always use `--password` flag for remote database operations

### 11. Library Interface and User Experience
The system includes a comprehensive library interface for viewing and managing generated content:

#### Library Features
- **Card-based Layout**: All plots and authors displayed in responsive card grid
- **Detailed Modal Views**: Click any card to see full details in a professional modal
- **Search & Filter**: Real-time search with genre and audience filtering
- **Responsive Design**: Works on desktop and mobile devices
- **Normalized Metadata Display**: Shows readable names instead of UUID foreign keys

#### Modal Functionality
**Plot Modals Include:**
- Complete plot summary (no character truncation)
- Organized metadata sections: Genre, Subgenre, Microgenre, Trope, Tone, Target Audience
- Creation timestamps and system IDs
- Professional layout with organized grid display

**Author Modals Include:**
- Full biography and writing style descriptions
- Author information: full name, pen name
- Associated plot relationships
- Creation details and system metadata

#### Technical Implementation
- **API Endpoints**: `/api/plots` and `/api/authors` with normalized metadata
- **Modal System**: CSS3 animations, click-outside-to-close, responsive design
- **Normalized Schema**: Foreign key lookups populate readable metadata names
- **Real-time Updates**: Interface updates automatically when new content is generated
- **Author-Plot Relationships**: Plots reference authors (multiple plots per author)

#### Accessing the Library
- Main interface: `http://localhost:8000/library`
- Or click "View Library" from main page: `http://localhost:8000`

### 12. Author-Plot Relationship System
The system implements a **one-to-many relationship** where one author can have multiple plots:

#### Database Schema
- **Authors Table**: Independent entities (no foreign keys to plots)
- **Plots Table**: Contains `author_id` foreign key referencing authors
- **Relationship**: `plots.author_id → authors.id` (multiple plots per author)

#### Workflow Logic
**Author-First Approach** (Recommended):
1. User requests: *"Create a fantasy author and plot"*
2. System creates author first
3. System creates plot assigned to that author
4. Result: Author can have additional plots created later

**Standalone Creation**:
- **Authors**: Can be created without plots (author profiles)
- **Plots**: Can be created without authors (unassigned plots)
- **Assignment**: Plots can be manually assigned to authors later

#### Multi-Agent Coordination
**Sequential Workflow**:
```
User Request → Orchestrator → Author Agent → Plot Agent
                                ↓              ↓
                           Save Author → Save Plot (with author_id)
```

**Context Passing**:
- Author context included in plot generation message
- Ensures plot matches author's style and background
- Maintains consistency across author's works

#### API Endpoints
- **`GET /api/authors`**: List all authors with plot counts
- **`GET /api/plots`**: List all plots with author information  
- **`GET /data/plot/{plot_id}`**: Get specific plot with author details
- **`POST /save_plot`**: Create plot with optional author assignment

#### Library Interface Features
**Author Modals**:
- Show all plots by that author
- Display plot count and relationships
- Author biography and writing style
- Scrollable plot list with metadata

**Plot Modals**:
- Show assigned author information
- Author biography snippet
- Link to author's other works
- Complete plot and author metadata

#### Database Migration Applied
**Migration 004**: `reverse_author_plot_relationship.sql`
- Added `plots.author_id` column
- Migrated existing `authors.plot_id` relationships
- Removed old `authors.plot_id` column
- Updated indexes for optimal performance

**Migration 005**: `hierarchical_genre_system.sql`
- Normalized genre system with proper foreign key hierarchy
- Genre → Subgenre → Microgenre → Trope → Tone
- Updated `plots` table to use foreign key references
- Added `target_audiences` table for structured audience data

**Migration 006**: `remove_target_audience_columns.sql`
- Simplified target_audiences table by removing interests and description columns
- Streamlined to core demographic fields: age_group, gender, sexual_orientation

**Migration 007**: `iterative_improvement_system.sql`
- Added improvement_sessions and improvement_iterations tables
- Enabled multi-step content enhancement workflow
- Added tracking for critique → enhancement → scoring cycles

**Migration 008**: `world_building_and_characters_system.sql` ✅ Applied
- Added world_building table with complex JSONB fields for geography, politics, culture
- Added characters table with character populations and relationship networks
- Both tables link to plots via foreign keys for context-aware generation

### 13. Genre and Target Audience Management System
The system provides comprehensive management of content parameters with admin interface and automatic context injection:

#### Admin Interface (`/admin`)
**Genres Management**:
- Create new genres with names and descriptions
- View all existing genres in organized cards
- Real-time form validation and success/error feedback
- RESTful API backend for genre CRUD operations

**Target Audiences Management**:
- Create audiences with structured data:
  - Age Group: Children, Middle Grade, Young Adult, New Adult, Adult, Senior
  - Gender: All, Male, Female, Non-binary
  - Sexual Orientation: All, Heterosexual, LGBTQ+, Gay, Lesbian, Bisexual
- View all audiences with complete metadata display
- Organized interface with dropdown selections

#### Parameter Selection in Web Chat
**Collapsible Parameters Section**:
- Toggle-able interface in main chat (📋 Content Parameters)
- Real-time dropdown population from database
- Visual parameter preview with tags and descriptions
- Smart context injection when referenced in messages

**Context Injection Keywords**:
User can trigger parameter injection by using phrases like:
- "specified genres and audience params"
- "specified genre and audience"
- "selected parameters"
- "chosen parameters"
- "based on the specified"
- "using the specified"

#### Automatic Context Enhancement
**Message Processing**:
```javascript
// User types: "Create a plot based on the specified genre and audience"
// System automatically appends:
// "CONTEXT - Use these specifications:
// GENRE: Cyberpunk - High tech, low life - stories set in dystopian futures
// TARGET AUDIENCE: Age Group: Young Adult, Gender: All, Sexual Orientation: All
// Audience Interests: Gaming, Technology, Dystopian fiction"
```

**Agent Integration**:
- No agent code changes required
- Context automatically included in orchestrator routing
- Genre/audience parameters flow through to plot and author agents
- Maintains consistency across all generated content

#### API Endpoints
**Genre Management**:
- `GET /api/genres` - List all genres with subgenres and microgenres
- `POST /api/genres` - Create new genre with name and description

**Target Audience Management**:
- `GET /api/target-audiences` - List all target audiences
- `POST /api/target-audiences` - Create new audience with structured data

#### User Workflow
1. **Setup Parameters** (via `/admin`):
   - Create custom genres for your project
   - Define target audiences with specific characteristics
   - Build reusable parameter library

2. **Select Parameters** (main chat):
   - Click "📋 Content Parameters" to expand
   - Choose genre from dropdown
   - Choose target audience from dropdown
   - See real-time preview of selections

3. **Generate Content** (natural language):
   - Type: "Create a cyberpunk plot for the specified audience"
   - System automatically injects full context
   - Agents receive detailed genre and audience specifications
   - Consistent output matching exact parameters

#### Benefits
**For Content Creators**:
- Consistent genre adherence across projects
- Precise target audience matching
- Reusable parameter definitions
- No need to retype detailed specifications

**For System Quality**:
- Standardized genre definitions prevent confusion
- Structured audience data improves targeting
- Context injection ensures parameter usage
- Maintains consistency across all agents

### 14. Communication & Clarity
- Explain complex implementations clearly
- Provide multiple solutions when trade-offs exist
- Highlight potential issues or limitations
- Suggest improvements to existing code
- Be proactive about best practices

### 15. Project Structure and Organization
The project follows a clean, modular structure with full separation of concerns:

```
BooksWriter/
├── src/                    # Source code modules
│   ├── agents/            # Multi-agent system components
│   │   ├── agent_factory.py      # Agent factory and registry
│   │   ├── orchestrator.py       # Orchestrator agent
│   │   └── [modular agents]      # Individual agent implementations
│   ├── database/          # Database services
│   │   └── supabase_service.py   # Supabase integration
│   ├── services/          # Business logic services
│   │   └── library_service.py    # Library management and content retrieval
│   ├── api/               # API endpoints (future expansion)
│   └── utils/             # Utility functions
│       └── validation.py  # Input validation and sanitization
├── tests/                 # Comprehensive test suite
│   ├── unit/             # Unit tests for components
│   ├── integration/      # Integration and system tests
│   ├── conftest.py       # Pytest configuration and fixtures
│   ├── test_library_functionality.py  # Library unit tests
│   └── test_library_integration.py    # Library integration tests
├── templates/             # HTML templates with full functionality
│   ├── index.html        # Main application landing page
│   ├── chat.html         # Interactive chat interface
│   ├── library.html      # Content library with search/filter
│   └── admin.html        # Administration interface
├── static/                # Static assets (JS, CSS)
│   ├── css/main.css      # Unified CSS with theme support
│   └── js/               # Modular JavaScript architecture
│       ├── modules/      # Core JavaScript modules
│       │   ├── api.js           # API communication service
│       │   ├── websocket.js     # WebSocket connection management
│       │   ├── state.js         # Centralized state management
│       │   ├── ui.js           # DOM manipulation & UI components
│       │   ├── agents.js       # Agent system & workflow visualization
│       │   └── theme.js        # Theme management
│       └── chat-enhanced.js     # Enhanced chat application
├── docs/                  # Documentation
│   ├── CLAUDE.md         # This file - AI instructions
│   ├── SETUP_GUIDE.md    # Consolidated setup instructions
│   └── archive/          # Historical/obsolete docs
├── scripts/               # Automation scripts
│   ├── setup/            # Installation and setup
│   └── maintenance/      # System maintenance tools
├── migrations/            # Database migrations with full history
└── config/                # Configuration files
    └── service-account-key.json  # Google Cloud credentials

```

**Key Files**:
- `main.py` - FastAPI application entry point with modular route organization
- `requirements.txt` - Python dependencies
- `.env` - Environment variables for Google Cloud and database configuration
- `pytest.ini` - Test configuration with coverage reporting
- `kill_port_8000.sh/.bat` - Development utility scripts

**Architecture Highlights**:
- **Modular Design**: Complete separation of agents, database, services, and utilities
- **Template Organization**: Full HTML templates extracted from main.py (removed 2,590+ lines of inline code)
- **Comprehensive Testing**: Unit and integration tests with fixtures and mocking
- **Library System**: Complete content management with search, filtering, and detailed modal views
- **Admin Interface**: Genre and target audience management with real-time validation
- **Responsive Design**: Mobile-friendly interface with dark/light theme support

### 16. Agent Development Guidelines

#### Adding New Agents to the System
When extending the multi-agent system with new specialized agents:

**1. Create Agent Class**
```python
# Create new agent class inheriting from BaseAgent
class NewAgent(BaseAgent):
    def __init__(self, config: Configuration):
        super().__init__(
            name="new_agent",
            description="Brief description of agent capabilities",
            instruction="Clear, concise instructions for the agent's role",
            config=config
        )
```

**2. Register in AgentFactory**
```python
# Add to agent_factory.py registry
self._agent_registry["new_agent"] = NewAgent
```

**2. Agent Design Principles**
- **Single Responsibility**: Each agent handles one specific content type or task
- **JSON Response Format**: All agents must return structured JSON for parsing
- **Error Handling**: Include fallback responses and graceful error management
- **Context Awareness**: Consider genre, audience, and existing content in responses
- **Scalable Instructions**: Write instructions that work across different content types

**3. Integration with Orchestrator**
- Update orchestrator routing logic to recognize new agent triggers
- Add appropriate workflow coordination (sequential vs parallel execution)
- Ensure session state management across multi-agent workflows
- Test agent communication protocols thoroughly

**4. Current Agent Capabilities Summary**
- **Plot Generator**: Creates complete story concepts with genre-appropriate elements
- **Author Generator**: Develops believable author personas matching target demographics
- **Critique Agent**: Provides comprehensive feedback on any writing content type
- **Enhancement Agent**: Systematically improves content based on critique analysis
- **Scoring Agent**: Evaluates content using weighted quality rubric
- **Library Service**: Manages content organization, search, and metadata display

**5. Potential Agent Extensions**
Consider these specialized agents for future development:
- **Character Development Agent**: Detailed character profiles with arcs and relationships
- **World Building Agent**: Settings, cultures, magic systems, and fictional environments
- **Dialogue Agent**: Natural character conversations with voice consistency
- **Research Agent**: Real-world information gathering for story authenticity
- **Chapter Structure Agent**: Plot breakdown into detailed scene outlines
- **Marketing Agent**: Blurbs, descriptions, and promotional content generation

## Commands to Run

### Before Marking Task Complete
```bash
# For TypeScript/JavaScript projects
npm run lint
npm run typecheck
npm test

# For Python projects
ruff check .
mypy .
pytest

# For multi-agent systems
python test_multi_agent_integration.py
python -m pytest test_multi_agent_integration.py -v

# Always run
git status
```

## Remember
- Quality over speed
- Think before coding
- Consider the bigger picture
- Write code you'd be proud to maintain
- Always validate assumptions
- Test edge cases
- Document wisely
- Refactor when needed
- Learn from the existing codebase
- Be security conscious