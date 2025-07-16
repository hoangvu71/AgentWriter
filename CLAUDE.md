# Claude AI Code Generation Instructions

## CRITICAL REQUIREMENTS

### 1. Test-Driven Development (TDD)
- ALWAYS write tests FIRST before any implementation
- Red-Green-Refactor cycle is mandatory
- No code without a failing test first
- Tests drive the design, not the other way around

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

### 10. Database Schema Evolution and Migration Workflow
When making changes to database schema (adding tables, normalizing data, etc.), follow this proven workflow:

#### Phase 1: Planning & Migration Creation
1. **Create Migration File**
   ```bash
   python create_migration.py "description of changes"
   ```
2. **Design New Schema** 
   - Use proper normalization (foreign keys instead of VARCHAR/JSONB)
   - Add appropriate indexes for performance
   - Include sample data for immediate testing
   - Use `IF NOT EXISTS` for idempotent operations

#### Phase 2: Schema Application
3. **Apply New Schema**
   ```bash
   # Use direct database connection with password
   python apply_migration_direct.py
   ```
4. **Verify Schema Creation**
   - Check all tables created successfully
   - Verify foreign key relationships
   - Confirm indexes are in place
   - Test with sample data

#### Phase 3: Data Migration (Critical!)
5. **Migrate Existing Data**
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
- Update `DATABASE_DOCUMENTATION.md` with new schema
- Document migration in `migrations/README.md`
- Add new tables to entity relationship documentation
- Update API documentation if schema affects endpoints

#### Critical Rules
- **NEVER skip data migration** - new foreign keys must be populated
- **ALWAYS verify before cleanup** - ensure no data loss
- **Test thoroughly** - run full system tests after migration
- **Document everything** - migrations should be self-explanatory
- **Use transactions** - ensure atomicity of migration operations

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
  - Interests: Comma-separated list (Adventure, Romance, Action, etc.)
  - Custom descriptions for each audience
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