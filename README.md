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

## 🗄️ Database Persistence (✅ Fully Operational)

### Current Database Schema:
1. **users** - User management and tracking
2. **sessions** - Chat session persistence  
3. **plots** - Generated plot data with normalized foreign keys
4. **authors** - Author profiles (can have multiple plots)
5. **orchestrator_decisions** - AI routing analytics
6. **genres** - Genre definitions with descriptions
7. **subgenres** - Subgenre categories linked to genres
8. **microgenres** - Microgenre types linked to subgenres
9. **tropes** - Story tropes linked to microgenres
10. **tones** - Tone variations linked to tropes
11. **target_audiences** - Audience demographics and interests

### What Gets Saved Automatically:
- ✅ **Every plot** with complete genre metadata
- ✅ **Every author** linked to their plots
- ✅ **User sessions** for conversation tracking
- ✅ **AI decisions** for system improvement
- ✅ **Searchable history** of all creations

**📖 See `DATABASE_DOCUMENTATION.md` for complete schema details.**

## Features

- **🤖 Multi-Agent Coordination**: Orchestrator routes requests to specialized agents
- **📊 Sequential Workflows**: Plot → Author → Final Response coordination
- **🎭 Genre Specialization**: Comprehensive genre, subgenre, and microgenre support
- **👥 Target Audience Matching**: Age, orientation, and gender considerations
- **💾 Database Persistence**: All data automatically saved to Supabase
- **🔍 Search & Retrieval**: Find past plots and authors easily
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
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=true

# Supabase Database  
SUPABASE_URL=https://cfqgzbudjnvtyxrrvvmo.supabase.co
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
   - "Generate a plot for a romance novel with enemies-to-lovers trope"
   - "Create an author profile for a mystery writer targeting middle-aged women"
   - "I need both a plot and author for a sci-fi thriller"

## API Endpoints

- `GET /` - Web interface
- `GET /health` - Health check with multi-agent system info
- `GET /sessions` - List active sessions
- `GET /sessions/{session_id}` - Get session info
- `WebSocket /ws/{session_id}` - Multi-agent chat interface

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
python test_database.py
```

### Application Testing
```bash
# Run the test suite
python test_app.py

# Integration tests
python -m pytest test_agent_integration.py -v

# Multi-agent system tests
python -m pytest test_multi_agent_integration.py -v
```

## 📁 File Structure

```
BooksWriter/
├── main.py                     # FastAPI application with multi-agent support
├── orchestrator_agent.py       # Main routing agent
├── plot_generator_agent.py     # Plot creation agent
├── author_generator_agent.py   # Author creation agent
├── supabase_service.py         # Database service layer
├── .env                        # Environment configuration
│
├── migrations/                 # Database migration system
│   ├── 001_initial_schema.sql  # Base schema (✅ Applied)
│   ├── 002_*.sql              # Future migrations
│   └── README.md               # Migration instructions
│
├── DATABASE_DOCUMENTATION.md   # Complete schema reference
├── SETUP_DOCUMENTATION.md      # Detailed setup guide
├── create_migration.py         # Migration helper tool
│
├── test_app.py                 # Application tests
├── test_agent_integration.py   # Integration tests
├── test_database.py            # Database functionality tests
├── requirements.txt            # Python dependencies
├── service-account-key.json    # Google Cloud credentials
└── README.md                   # This file
```

## 📊 Database Access

### Supabase Dashboard
- **URL**: https://app.supabase.com/project/cfqgzbudjnvtyxrrvvmo
- **Tables**: users, sessions, plots, authors, orchestrator_decisions
- **Status**: ✅ All tables operational with data

### Connection Details
- **Host**: db.cfqgzbudjnvtyxrrvvmo.supabase.co
- **Database**: postgres
- **Connection**: `postgresql://postgres:BTTmSilqcNn9Ynj5@db.cfqgzbudjnvtyxrrvvmo.supabase.co:5432/postgres`

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

- **📖 `DATABASE_DOCUMENTATION.md`** - Complete database schema and API reference
- **⚙️ `SETUP_DOCUMENTATION.md`** - Detailed setup and configuration guide
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