# Configuration Reference

Complete reference for all BooksWriter configuration options.

## Environment Variables

### Core Configuration
```bash
# Application Settings
PORT=8000                    # Server port (default: 8000)
HOST=0.0.0.0                # Server host (default: localhost)
DEBUG=false                 # Debug mode (default: false)
LOG_LEVEL=INFO              # Logging level (DEBUG, INFO, WARN, ERROR)

# Model Configuration
MODEL_NAME=gemini-2.0-flash-exp  # Default AI model
```

### Google Cloud Configuration
```bash
# Required for Vertex AI integration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=true
```

### Database Configuration

#### Supabase (Production)
```bash
# Supabase configuration for production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-database-password
```

#### SQLite (Development)
```bash
# SQLite configuration for local development
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=data/bookswriter.db
```

### MCP Integration
```bash
# Optional: Model Context Protocol integration
SUPABASE_ACCESS_TOKEN=your-personal-access-token
MCP_SERVER_PORT=3001
```

### Security Configuration
```bash
# CORS settings
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
CORS_ALLOW_CREDENTIALS=true

# API Security
API_KEY_REQUIRED=false      # Enable API key authentication
RATE_LIMIT_ENABLED=true     # Enable rate limiting
RATE_LIMIT_REQUESTS=100     # Requests per minute
```

## Configuration Files

### .env File Template
```bash
# Copy this template to .env and fill in your values

# Google Cloud Configuration (Required)
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=true

# Database Configuration (Choose one)
# Option 1: Supabase (Production)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_DB_PASSWORD=

# Option 2: SQLite (Development)
# DATABASE_TYPE=sqlite
# SQLITE_DB_PATH=data/bookswriter.db

# Optional: MCP Integration
# SUPABASE_ACCESS_TOKEN=

# Application Settings
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### MCP Configuration (.claude/mcp.json)
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

## Model Configuration

### Available Models
- `gemini-2.0-flash-exp` - Latest experimental model with enhanced capabilities
- `gemini-1.5-flash-002` - Fast, efficient for general writing tasks
- `gemini-1.5-pro` - Stable production model with advanced reasoning
- `gemini-1.5-flash` - Cost-effective for basic tasks

### Model Switching
```bash
# Runtime model switching via API
curl -X POST http://localhost:8000/models/gemini-1.5-pro/switch
```

## Database Configuration

### Connection Pooling
```python
# SQLite pool settings
SQLITE_POOL_SIZE = 20
SQLITE_POOL_TIMEOUT = 30
SQLITE_POOL_RECYCLE = 3600

# Supabase pool settings
SUPABASE_POOL_SIZE = 10
SUPABASE_POOL_TIMEOUT = 30
SUPABASE_MAX_OVERFLOW = 20
```

### Migration Settings
```bash
# Migration configuration
MIGRATION_AUTO_APPLY=false
MIGRATION_BACKUP_ENABLED=true
MIGRATION_VALIDATION_ENABLED=true
```

## Agent Configuration

### Agent Settings
```python
# Agent response limits
MAX_PLOT_LENGTH = 2000
MAX_AUTHOR_BIO_LENGTH = 1500
MAX_WORLD_DESCRIPTION_LENGTH = 3000

# Agent timeout settings
AGENT_TIMEOUT_SECONDS = 120
AGENT_RETRY_ATTEMPTS = 3
```

### Tool Configuration
```python
# Tool validation settings
VALIDATE_TOOL_INPUTS = true
TOOL_RESPONSE_CACHE_TTL = 300
TOOL_MAX_RETRIES = 2
```

## Deployment Configuration

### Development
```bash
# Development environment
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_TYPE=sqlite
CORS_ORIGINS=["http://localhost:3000"]
```

### Staging
```bash
# Staging environment
DEBUG=false
LOG_LEVEL=INFO
DATABASE_TYPE=supabase
RATE_LIMIT_ENABLED=true
```

### Production
```bash
# Production environment
DEBUG=false
LOG_LEVEL=WARN
DATABASE_TYPE=supabase
API_KEY_REQUIRED=true
RATE_LIMIT_ENABLED=true
HTTPS_ONLY=true
```

## Configuration Validation

### Environment Validation
The application validates required environment variables on startup:
- Google Cloud credentials and project settings
- Database connection parameters
- Required API keys and tokens

### Configuration Tests
```bash
# Validate configuration
python scripts/validate_config.py

# Test database connection
python scripts/test_database_connection.py

# Verify MCP integration
python scripts/test_mcp_connection.py
```

## Related Documentation

- **[Installation Guide](../setup/installation.md)** - Setup instructions
- **[Environment Configuration](../setup/environment.md)** - Environment setup
- **[Database Architecture](../architecture/database.md)** - Database configuration
- **[Security Guidelines](../guides/security.md)** - Security configuration

---

*This reference provides complete configuration information for all BooksWriter deployment scenarios.*