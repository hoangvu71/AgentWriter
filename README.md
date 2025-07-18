# Multi-Agent Book Writer System

A sophisticated multi-agent system for book writing powered by Google's Agent Development Kit (ADK) and Gemini AI. **All data is automatically persisted to Supabase database for permanent storage and retrieval.**

## 🎯 Quick Start

1. **Start the system:**
   ```bash
   python main.py
   ```

2. **Open web interface:** http://localhost:8000

3. **Try example prompt:**
   ```
   Create a fantasy novel, LitRPG, Zombie Apocalypse, survive and family, dark/humour/realistic, Male/Heterosexual/Young Adults. Create author too.
   ```

**✅ All plots and authors are automatically saved to your Supabase database!**

## Multi-Agent Architecture

### **🎯 Orchestrator Agent**
- Routes user requests to appropriate agents
- Coordinates sequential workflows between agents
- Manages inter-agent communication
- Makes intelligent routing decisions based on user intent
- **Logs all decisions to database for analytics**

### **📖 Plot Generator Agent**
- Creates detailed plots based on comprehensive parameters:
  - **Genre**: Fantasy, Romance, Sci-Fi, Mystery, etc.
  - **Subgenre**: LitRPG, Space Opera, Cozy Mystery, etc.
  - **Microgenre**: Zombie Apocalypse, Time Travel, etc.
  - **Tropes**: Survive and family, Chosen one, etc.
  - **Tone**: Dark, humorous, realistic, etc.
  - **Target Audience**: Age range, sexual orientation, gender
- **Automatically saves all generated plots with metadata**

### **✍️ Author Generator Agent**
- Creates author profiles matching microgenre and target audience:
  - Author name and pen name suggestions
  - Comprehensive biography and background
  - Writing voice and style descriptions
  - Genre expertise and credentials
  - Target audience appeal analysis
- **Links authors to plots and saves to database**

### **🌍 World Building Agent**
- Creates intricate fictional worlds based on plot requirements:
  - Geography, climate, and physical environments
  - Political systems, governments, and power structures
  - Cultural traditions, religions, and social hierarchies
  - Economic systems, trade, and resources
  - Magic systems and supernatural elements (for fantasy)
- **All world building data stored as structured JSONB in database**

### **👥 Characters Agent**
- Develops detailed character populations for stories:
  - Primary protagonists with complete character arcs
  - Supporting characters with defined roles and relationships
  - Antagonists with clear motivations and backgrounds
  - Character relationship networks and dynamics
  - Character development trajectories throughout the story
- **Links characters to both plots and world building contexts**

## 🗄️ Database Persistence (✅ Fully Operational)

### Current Database Schema:
1. **users** - User management and tracking
2. **sessions** - Chat session persistence  
3. **plots** - Generated plot data with normalized foreign keys
4. **authors** - Author profiles (can have multiple plots)
5. **world_building** - Fictional world details with JSONB data structures
6. **characters** - Character populations and relationship networks
7. **orchestrator_decisions** - AI routing analytics
8. **genres** - Genre definitions with descriptions
9. **subgenres** - Subgenre categories linked to genres
10. **microgenres** - Microgenre types linked to subgenres
11. **tropes** - Story tropes linked to microgenres
12. **tones** - Tone variations linked to tropes
13. **target_audiences** - Audience demographics and interests
14. **improvement_sessions** - Iterative content enhancement tracking
15. **improvement_iterations** - Individual critique/enhancement cycles

### What Gets Saved Automatically:
- ✅ **Every plot** with complete genre metadata
- ✅ **Every author** linked to their plots
- ✅ **World building details** with structured geography, politics, culture
- ✅ **Character populations** with relationships and development arcs
- ✅ **User sessions** for conversation tracking
- ✅ **AI decisions** for system improvement
- ✅ **Improvement iterations** with critique and enhancement cycles
- ✅ **Searchable history** of all creations

**📖 See `docs/database_documentation.md` for complete schema details.**

## Features

- **🤖 Multi-Agent Coordination**: Orchestrator routes requests to specialized agents
- **📊 Sequential Workflows**: Plot → World Building → Characters → Author coordination
- **🎭 Genre Specialization**: Comprehensive genre, subgenre, and microgenre support
- **👥 Target Audience Matching**: Age, orientation, and gender considerations
- **💾 Database Persistence**: All data automatically saved to Supabase
- **🔍 Search & Retrieval**: Find past plots, authors, worlds, and characters easily
- **📚 Library Interface**: Card-based browsing with search, filter, and detailed modal views
- **⚙️ Admin Interface**: Manage genres and target audiences with real-time validation
- **🔄 Iterative Improvement**: Built-in critique, enhancement, and scoring system for content quality
- **🧠 Memory**: Maintains conversation history and user preferences across agents
- **🤖 Model Selection**: Choose from 5 different Google AI models:
  - **Gemini 2.0 Flash**: Fast, efficient for general writing tasks
  - **Gemini 2.5 Flash**: Latest with thinking capabilities
  - **Gemini 2.5 Pro Preview**: Advanced reasoning for complex projects
  - **Gemini 1.5 Pro**: Stable production model
  - **Gemini 1.5 Flash**: Cost-effective for basic tasks
- **⚡ Real-time Chat**: WebSocket-based streaming responses from all agents
- **🔄 Session Management**: Persistent conversations across sessions and agents
- **🎨 Clean Formatting**: Automatically formats responses for readability

## System Architecture

- **Backend**: FastAPI with WebSocket support
- **Database**: Supabase (PostgreSQL) with automatic persistence
- **Multi-Agent System**: Google Agent Development Kit (ADK) with specialized agents
- **Frontend**: Simple HTML/CSS/JavaScript interface with multi-agent support
- **Communication**: Inter-agent communication via orchestrator coordination

## Prerequisites (✅ Already Configured)

1. **✅ Google Cloud Setup**:
   - Google Cloud Project with billing enabled
   - Vertex AI API enabled
   - Service account with appropriate permissions

2. **✅ Supabase Database**:
   - Complete schema deployed
   - All tables and indexes created
   - Connection configured and tested

3. **✅ Python Dependencies**:
   - All required packages installed

## Environment Configuration (✅ Ready)

```env
# Google Cloud AI
GOOGLE_CLOUD_PROJECT=writing-book-457206
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=true

# Supabase Database  
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=BTTmSilqcNn9Ynj5
```

## 🔄 Adding New Features/Agents

### 1. Database Schema Changes
```bash
# Create migration for new tables
python create_migration.py "add character development agent"

# Edit the generated SQL file in migrations/
# Apply via Supabase CLI
npx supabase db push
```

### 2. Code Changes
1. Create new agent file following existing patterns
2. Add database methods to `supabase_service.py`
3. Update orchestrator routing logic
4. Test with `python test_database.py`

## Usage

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Access the interface**:
   - Open your browser to `http://localhost:8000`
   - Start chatting with the multi-agent book writing system

3. **Example interactions**:
   - "Create a fantasy novel, LitRPG, Zombie Apocalypse, survive and family, dark/humour/realistic, Male/Heterosexual/Young Adults. Create author too."
   - "Generate a complete story foundation: plot, world, and characters for a space opera"
   - "Create a romance plot with detailed world building and character relationships"
   - "I need a mystery plot, then build a world and characters to support it"
   - "Create author, plot, world building and characters for a cyberpunk thriller"

## API Endpoints

- `GET /` - Web interface
- `GET /library` - Content library interface
- `GET /admin` - Administration interface for genres and audiences
- `GET /health` - Health check with multi-agent system info
- `GET /sessions` - List active sessions
- `GET /sessions/{session_id}` - Get session info
- `WebSocket /ws/{session_id}` - Multi-agent chat interface

### Content Management
- `GET /api/plots` - List all plots with metadata and author information
- `GET /api/authors` - List all authors with plot counts and relationships
- `GET /api/genres` - List all genres with subgenres and microgenres
- `GET /api/target-audiences` - List all target audiences
- `POST /api/genres` - Create new genre with name and description
- `POST /api/target-audiences` - Create new audience with structured data

### Multi-Agent System
- `GET /agents` - List all available agents and their capabilities

### Model Management
- `GET /models` - List available AI models and current selection
- `GET /models/{model_id}` - Get detailed information about a specific model
- `POST /models/{model_id}/switch` - Switch to a different AI model

## 🧪 Testing

### Database Testing
```bash
# Test complete database functionality
python -m pytest tests/unit/test_database.py -v
```

### Application Testing
```bash
# Run all tests
python -m pytest tests/unit/ -v

# Specific test files
python -m pytest tests/unit/test_app.py -v
python -m pytest tests/unit/test_agent_integration.py -v
python -m pytest tests/unit/test_multi_agent_integration.py -v
```

## 📁 File Structure

```
BooksWriter/
├── main.py                     # FastAPI web server with multi-agent support
├── src/                        # Application source code
│   ├── agents/
│   │   ├── multi_agent_system.py    # Main multi-agent orchestrator
│   │   └── agent_service.py         # Agent service utilities
│   ├── database/
│   │   └── supabase_service.py      # Database service layer
│   ├── services/
│   │   └── library_service.py       # Library management and content retrieval
│   ├── api/                    # Future API endpoints
│   └── utils/                  # Utility functions
│       └── validation.py       # Input validation and sanitization
├── tests/                      # Comprehensive test suite
│   ├── unit/                   # Unit tests for components
│   ├── integration/            # Integration and system tests
│   ├── conftest.py             # Pytest configuration and fixtures
│   └── test_*.py               # Individual test files
├── scripts/                    # Organized utility scripts
│   ├── setup/                  # Installation and setup automation
│   ├── migration/              # Database migration utilities
│   ├── database/               # Database verification and management
│   ├── dev/                    # Development tools (port management, etc.)
│   └── maintenance/            # System maintenance and TDD compliance
├── templates/                  # HTML templates with full functionality
│   ├── index.html              # Main application landing page
│   ├── chat.html               # Interactive chat interface
│   ├── library.html            # Content library with search/filter
│   └── admin.html              # Administration interface
├── static/                     # Frontend assets (CSS, JavaScript)
│   ├── css/main.css            # Unified CSS with theme support
│   └── js/                     # JavaScript utilities and interactions
├── migrations/                 # Database migration system
│   ├── 001_initial_schema.sql  # Base schema (✅ Applied)
│   ├── 008_world_building_and_characters_system.sql  # Latest migration (✅ Applied)
│   └── applied_migrations.json # Migration tracking
├── docs/                       # All documentation
│   ├── CLAUDE.md               # AI development guidelines and TDD approach
│   ├── DATABASE_MIGRATIONS_GUIDE.md  # Migration process documentation
│   └── database_documentation.md     # Complete schema reference
├── config/                     # Configuration files
│   ├── .env                    # Environment variables  
│   └── service-account-key.json # Google Cloud credentials
├── backups/                    # Backup files and version history
├── supabase/                   # Supabase CLI configuration and migrations
├── requirements.txt            # Python dependencies
├── package.json               # Node.js dependencies
├── pytest.ini                 # Test configuration with coverage
└── README.md                   # This file
```

## 📊 Database Access

### Supabase Dashboard
- **URL**: https://app.supabase.com/project/YOUR_PROJECT_ID
- **Tables**: users, sessions, plots, authors, world_building, characters, orchestrator_decisions, improvement_sessions
- **Status**: ✅ All tables operational with data

### Connection Details
- **Host**: db.YOUR_PROJECT_ID.supabase.co
- **Database**: postgres
- **Connection**: `postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres`

## WebSocket Message Format

### Client to Server:
```json
{
  "type": "message",
  "content": "Your message here",
  "user_id": "user123"
}
```

### Server to Client:
```json
{
  "type": "stream_chunk",
  "content": "Response chunk..."
}
```

## Agent Response Formats

### Plot Generator Agent Response:
```json
{
  "title": "The Echoes of Tomorrow",
  "plot_summary": "A comprehensive 2-3 paragraph plot summary that includes the full story arc, main conflicts, character development, and resolution. All plot elements are woven into the narrative."
}
```

### Author Generator Agent Response:
```json
{
  "author_name": "Sarah Jane Mitchell",
  "pen_name": "S.J. Mitchell",
  "biography": "Born in Portland, Oregon, Sarah Jane Mitchell grew up surrounded by the misty forests of the Pacific Northwest, which deeply influenced her love for fantasy literature. With a PhD in Medieval History from Stanford University...",
  "writing_style": "Mitchell's prose is lyrical yet accessible, blending rich world-building with emotionally resonant character development. Her writing features vivid sensory details and a talent for weaving complex magic systems into relatable human stories."
}
```

## Development

The project follows Test-Driven Development (TDD) principles:

1. **Write tests first** - All functionality starts with failing tests
2. **Keep it simple** - No overengineering or unnecessary complexity  
3. **Ask for clarification** - Never assume requirements
4. **Focus on root causes** - Fix core issues, not symptoms
5. **Multi-agent design** - Each agent has a single, well-defined responsibility
6. **Database-first** - All data automatically persisted

## 🔒 Security & Performance

### Database Security
- ✅ Secure Supabase connection with SSL
- ✅ Environment variable protection
- ✅ Row Level Security ready for production

### Performance Features
- **🔄 Streaming**: Real-time response streaming
- **⚡ Async Processing**: Concurrent agent execution  
- **🎯 Smart Routing**: Intelligent model selection
- **💾 Auto-Save**: Immediate database persistence
- **🔍 Fast Retrieval**: Indexed database queries

## Troubleshooting

1. **Authentication errors**: Ensure Google Cloud credentials are properly configured
2. **Database connection issues**: Run `python test_database.py` to verify connectivity
3. **Port 8000 in use**: Kill existing process or use different port
4. **Migration failed**: Check Supabase CLI login with `npx supabase projects list`
5. **WebSocket disconnections**: Check network connectivity and firewall settings

## 📚 Documentation

- **📖 `docs/database_documentation.md`** - Complete database schema and API reference
- **⚙️ `docs/setup_documentation.md`** - Detailed setup and configuration guide
- **🔄 `migrations/README.md`** - Database migration system guide

## Contributing

1. Follow the TDD approach outlined in `CLAUDE.md`
2. Write tests for all new functionality
3. Keep code simple and focused
4. Update database schema through migrations
5. Test database operations thoroughly
6. Ask for clarification when requirements are unclear

## License

This project is for educational and demonstration purposes.

---

**🎉 Status: Fully Operational** - Multi-agent system with complete database persistence ready for production use!