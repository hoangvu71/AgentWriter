# Complete Installation Guide

This guide provides detailed installation and configuration instructions for BooksWriter.

## 🏗️ System Architecture

BooksWriter is a sophisticated AI-powered book writing system using:

### Core Agents
- **Orchestrator Agent**: Routes requests to appropriate specialized agents
- **Plot Generator Agent**: Creates detailed plot summaries with genre metadata
- **Author Generator Agent**: Creates author profiles and writing styles  
- **World Building Agent**: Constructs detailed fictional worlds
- **Characters Agent**: Creates character profiles and relationships
- **Enhancement/Critique/Scoring Agents**: Improve and evaluate content

### Technology Stack
- **Backend**: FastAPI (Python) with WebSocket support
- **Database**: Supabase (PostgreSQL) with SQLite for development
- **AI**: Google Vertex AI (Gemini models)
- **Frontend**: Vanilla JavaScript with real-time chat
- **Integration**: MCP for direct database access

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Node.js 16+** for MCP integration
3. **Google Cloud Project** with Vertex AI enabled
4. **Supabase Account** with a project created
5. **Git** for version control

## 🔧 Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd AgentWriter
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root with these configurations:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=true

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-database-password

# Model Configuration
MODEL_NAME=gemini-2.0-flash-exp  # or gemini-1.5-flash-002

# Database Mode Selection
DATABASE_MODE=supabase  # Options: supabase, sqlite

# MCP Supabase Integration (Optional)
SUPABASE_ACCESS_TOKEN=your-personal-access-token

# ADK Service Mode
ADK_SERVICE_MODE=development  # Options: development, database, vertex_ai

# Connection Pool Configuration (Optional)
DB_POOL_MIN_CONNECTIONS=3
DB_POOL_MAX_CONNECTIONS=15
DB_POOL_MAX_IDLE_TIME=300
DB_POOL_CONNECTION_TIMEOUT=30
DB_POOL_HEALTH_CHECK_INTERVAL=60
DB_POOL_ENABLE_METRICS=true
```

### 4. Google Cloud Setup

1. **Create Service Account**:
   - Go to Google Cloud Console
   - Navigate to IAM & Admin > Service Accounts
   - Create new service account with Vertex AI permissions

2. **Download Credentials**:
   - Generate and download JSON key
   - Save as `config/service-account-key.json`

3. **Enable APIs**:
   - Vertex AI API
   - Generative AI API

### 5. Database Setup

#### Option A: Automated Setup (Recommended)
```bash
python scripts/setup/one_click_setup.py
```

#### Option B: Supabase CLI Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Initialize and link project
cd supabase
supabase init
supabase link --project-ref your-project-ref

# Run migrations
supabase db push
```

#### Option C: Manual Setup
1. Connect to Supabase SQL Editor
2. Run migration files in order from `migrations/` directory:
   - `001_initial_schema.sql`
   - `002_add_character_development_agent.sql`
   - `003_normalize_target_audience_and_genre_tables.sql`
   - (continue in numerical order)
3. Verify tables are created correctly

### 6. MCP Integration Setup (Optional)

For direct database access via Claude agents:

```bash
# Install MCP Supabase server
npm install -g @supabase/mcp-server-supabase

# Configure Claude MCP (create .claude/mcp.json)
mkdir -p .claude
```

See [MCP Supabase Integration](../integrations/mcp-supabase.md) for detailed setup.

## 🎯 Verification

### 1. Start the Application
```bash
python main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Test Web Interface
- Open browser to `http://localhost:8000`
- Test the chat interface with a simple prompt
- Verify models load in the dropdown

### 3. Test Database Connection
```bash
python scripts/database/check_tables.py
```

### 4. Run Tests
```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## 📁 Project Structure

```
AgentWriter/
├── src/                    # Source code
│   ├── agents/            # Agent implementations
│   ├── core/              # Core system components
│   ├── database/          # Database adapters and services
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic services
│   ├── websocket/         # WebSocket handlers
│   └── tools/             # Agent tools
├── tests/                 # Test files
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docs/                 # Documentation
├── migrations/           # Database migrations
├── scripts/              # Setup and maintenance scripts
├── templates/            # HTML templates
├── static/               # Static assets (CSS, JS)
├── config/               # Configuration files
├── requirements.txt      # Python dependencies
└── main.py              # Application entry point
```

## 🔍 Deployment Modes

### Development Mode (Default)
```bash
ADK_SERVICE_MODE=development
DATABASE_MODE=sqlite
```
- Fast startup, in-memory services
- SQLite database (auto-created)
- No external dependencies

### Database Mode
```bash
ADK_SERVICE_MODE=database
DATABASE_MODE=supabase
```
- Full conversation continuity
- Persistent Supabase database
- Connection pooling enabled

### Vertex AI Mode
```bash
ADK_SERVICE_MODE=vertex_ai
DATABASE_MODE=supabase
VERTEX_AI_AGENT_ENGINE_ID=your-engine-id
```
- Cloud-managed sessions
- Advanced semantic memory
- Full production capabilities

## 🚨 Common Issues & Solutions

### Database Connection Issues
**Symptoms**: Connection refused, authentication errors
**Solutions**:
- Verify Supabase URL and keys in `.env`
- Check database password in Supabase Dashboard → Settings → Database
- Ensure IP is whitelisted in Supabase network settings
- Test connection: `python scripts/database/check_tables.py`

### Google Cloud Authentication
**Symptoms**: "Could not automatically determine credentials"
**Solutions**:
- Verify service account key path is correct
- Check if Vertex AI API is enabled
- Ensure service account has Vertex AI User role
- Test: `gcloud auth application-default print-access-token`

### Migration Failures
**Symptoms**: Tables not found, foreign key errors
**Solutions**:
- Run migrations in numerical order
- Check `migrations/applied_migrations.json` for status
- Use Supabase SQL Editor to run migrations manually
- Verify all foreign key references exist

### Port 8000 Already in Use
**Symptoms**: "Address already in use"
**Solutions**:
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn src.app:app --port 8001
```

### MCP Tools Not Available
**Symptoms**: MCP tools don't appear in Claude agents
**Solutions**:
- Set environment variables as system variables (not just `.env`)
- Restart Claude Code completely
- Verify MCP server installation: `npx @supabase/mcp-server-supabase@latest`
- Check `.claude/mcp.json` configuration

## 🔒 Security Configuration

### Development Security
- Environment variables in `.env` file
- Service account key in `config/` directory
- Default security headers enabled

### Production Security
- Use environment variables (not `.env` files)
- Enable Row Level Security (RLS) in Supabase
- Configure CORS properly
- Use HTTPS termination
- Regular security audits

See [Security Guidelines](../guides/security.md) for detailed security configuration.

## 📊 Performance Optimization

### Connection Pooling
Default pool settings are optimized for most use cases:
- **SQLite**: 3-15 connections
- **Supabase**: 2-8 connections
- **Health checks**: 60-second intervals

### Model Selection
Choose the right model for your use case:
- **Gemini 2.0 Flash Exp**: Best performance and latest features
- **Gemini 1.5 Pro**: Stable production model
- **Gemini 1.5 Flash**: Cost-effective for basic tasks

## 🆘 Getting Help

### Documentation
- **[Architecture Overview](../architecture/overview.md)** - System design
- **[Development Workflow](../guides/development.md)** - TDD methodology
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Common issues

### Support Channels
- Check existing documentation in `docs/`
- Review test files for usage examples
- Examine migration files for database schema details

### Contributing
1. Follow TDD methodology outlined in [Development Workflow](../guides/development.md)
2. Write tests for all new functionality
3. Keep code simple and focused
4. Update documentation for any changes

---

**Installation complete!** 🎉 Your BooksWriter system is now ready for multi-agent book creation with full database persistence and real-time capabilities.