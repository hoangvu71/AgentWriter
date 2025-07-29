# Environment Configuration

This guide covers all environment variables and configuration options for BooksWriter.

## 📝 Environment Variables

### Core Configuration

Create a `.env` file in your project root with these variables:

```env
# Google Cloud / Vertex AI (Required)
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true

# Supabase Database (Optional - for cloud persistence)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-db-password

# MCP Supabase Integration (Optional - for direct database access)
SUPABASE_ACCESS_TOKEN=your-personal-access-token

# Model Configuration
MODEL_NAME=gemini-2.0-flash-exp  # or gemini-1.5-flash-002

# Database Mode Selection
DATABASE_MODE=supabase  # Options: supabase, sqlite

# ADK Service Mode
ADK_SERVICE_MODE=development  # Options: development, database, vertex_ai

# For vertex_ai mode only
VERTEX_AI_AGENT_ENGINE_ID=your-agent-engine-id
```

### Optional Performance Configuration

```env
# Connection Pool Configuration
DB_POOL_MIN_CONNECTIONS=3          # Minimum pool connections
DB_POOL_MAX_CONNECTIONS=15         # Maximum pool connections  
DB_POOL_MAX_IDLE_TIME=300          # Idle timeout (seconds)
DB_POOL_CONNECTION_TIMEOUT=30      # Connection timeout (seconds)
DB_POOL_HEALTH_CHECK_INTERVAL=60   # Health check interval (seconds)
DB_POOL_ENABLE_METRICS=true        # Enable metrics collection

# Logging Configuration
LOG_LEVEL=INFO                     # Options: DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=detailed                # Options: simple, detailed, json

# Server Configuration
HOST=127.0.0.1                     # Server host
PORT=8000                          # Server port
WORKERS=1                          # Number of worker processes
```

## 🔑 Getting Credentials

### Google Cloud Credentials

1. **Create Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Add these roles:
     - Vertex AI User
     - AI Platform Developer

2. **Download Service Account Key**:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key" → JSON
   - Save as `config/service-account-key.json`

3. **Get Project Information**:
   - **Project ID**: Found in Google Cloud Console header
   - **Location**: Use `us-central1` (recommended)

### Supabase Credentials

1. **Project URL**:
   - Go to [Supabase Dashboard](https://app.supabase.com/)
   - Select your project
   - Settings → API → Project URL

2. **Anonymous Key**:
   - Same location: Settings → API → Project API keys → `anon public`

3. **Database Password**:
   - Settings → Database → Connection string
   - Password is embedded in the connection string

4. **Access Token** (for MCP):
   - Go to [Supabase Dashboard](https://app.supabase.com/)
   - Account Settings → Access Tokens
   - Generate new token with appropriate permissions

## 🏗️ Configuration Modes

### Development Mode (Fastest Setup)
```env
ADK_SERVICE_MODE=development
DATABASE_MODE=sqlite
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=DEBUG
```

**Features**:
- In-memory services (fast startup)
- SQLite database (auto-created)
- No external dependencies required
- Full debug logging

### Production Mode (Full Features)
```env
ADK_SERVICE_MODE=database
DATABASE_MODE=supabase
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=INFO
DB_POOL_ENABLE_METRICS=true
```

**Features**:
- Persistent conversation memory
- Supabase cloud database
- Connection pooling
- Performance metrics
- Production logging

### Cloud Mode (Advanced)
```env
ADK_SERVICE_MODE=vertex_ai
DATABASE_MODE=supabase
VERTEX_AI_AGENT_ENGINE_ID=your-engine-id
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=WARNING
```

**Features**:
- Google Cloud managed sessions
- Advanced semantic memory
- Enterprise-grade scaling
- Minimal local resources

## 🔧 Configuration Templates

### Template: Local Development
```env
# .env.development
GOOGLE_CLOUD_PROJECT=your-dev-project
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/dev-service-account.json

DATABASE_MODE=sqlite
ADK_SERVICE_MODE=development
MODEL_NAME=gemini-1.5-flash
LOG_LEVEL=DEBUG
```

### Template: Staging Environment
```env
# .env.staging
GOOGLE_CLOUD_PROJECT=your-staging-project
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/staging-service-account.json

SUPABASE_URL=https://your-staging.supabase.co
SUPABASE_ANON_KEY=your-staging-anon-key
SUPABASE_DB_PASSWORD=your-staging-password

DATABASE_MODE=supabase
ADK_SERVICE_MODE=database
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=INFO
```

### Template: Production Environment
```env
# .env.production
GOOGLE_CLOUD_PROJECT=your-prod-project
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/prod-service-account.json

SUPABASE_URL=https://your-prod.supabase.co
SUPABASE_ANON_KEY=your-prod-anon-key
SUPABASE_DB_PASSWORD=your-prod-password
SUPABASE_ACCESS_TOKEN=your-prod-access-token

DATABASE_MODE=supabase
ADK_SERVICE_MODE=vertex_ai
VERTEX_AI_AGENT_ENGINE_ID=your-prod-engine-id
MODEL_NAME=gemini-2.0-flash-exp
LOG_LEVEL=WARNING

# Production optimization
DB_POOL_MAX_CONNECTIONS=25
DB_POOL_ENABLE_METRICS=true
WORKERS=4
```

## 🔐 Security Best Practices

### Environment Variable Security

1. **Never commit `.env` files**:
   ```bash
   # Add to .gitignore
   .env
   .env.*
   config/*.json
   ```

2. **Use environment-specific files**:
   - `.env.development`
   - `.env.staging`
   - `.env.production`

3. **Production deployment**:
   - Use system environment variables
   - Avoid `.env` files in production
   - Use secret management services

### Credential Rotation

```bash
# Template for credential rotation script
#!/bin/bash
# rotate_credentials.sh

# Backup current config
cp .env .env.backup.$(date +%Y%m%d)

# Update Supabase access token
export NEW_SUPABASE_TOKEN="$(get_new_supabase_token)"
sed -i "s/SUPABASE_ACCESS_TOKEN=.*/SUPABASE_ACCESS_TOKEN=$NEW_SUPABASE_TOKEN/" .env

# Restart services
systemctl restart bookswriter
```

## 🧪 Configuration Validation

### Validate Environment Setup
```bash
# Test script: scripts/validate_environment.py
python -c "
import os
from src.core.configuration import Configuration

config = Configuration()
print('✅ Configuration loaded successfully')
print(f'Database mode: {config.database_mode}')
print(f'ADK service mode: {config.adk_service_mode}')
print(f'Model: {config.model_name}')
"
```

### Test Database Connection
```bash
python scripts/database/check_tables.py
```

Expected output:
```
✅ Database connection successful
✅ Found 18 tables
✅ All required tables present
```

### Test Google Cloud Authentication
```bash
python -c "
from google.cloud import aiplatform
aiplatform.init()
print('✅ Google Cloud authentication successful')
"
```

## 🔄 Environment Switching

### Using Different Environments
```bash
# Development
cp .env.development .env
python main.py

# Staging
cp .env.staging .env
python main.py

# Production
cp .env.production .env
python main.py
```

### Docker Environment Variables
```dockerfile
# Dockerfile
ENV GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
ENV SUPABASE_URL=${SUPABASE_URL}
ENV DATABASE_MODE=${DATABASE_MODE}
ENV ADK_SERVICE_MODE=${ADK_SERVICE_MODE}
```

```yaml
# docker-compose.yml
services:
  bookswriter:
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - SUPABASE_URL=${SUPABASE_URL}
      - DATABASE_MODE=${DATABASE_MODE}
      - ADK_SERVICE_MODE=${ADK_SERVICE_MODE}
```

## 🚨 Troubleshooting

### Common Environment Issues

#### 1. Google Cloud Authentication Fails
```bash
# Error: Could not automatically determine credentials
# Solutions:
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
gcloud auth application-default login
```

#### 2. Supabase Connection Errors
```bash
# Error: Connection refused
# Check these variables:
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
# Verify in Supabase Dashboard → Settings → API
```

#### 3. Model Not Available
```bash
# Error: Model not found
# Available models:
# - gemini-2.0-flash-exp
# - gemini-1.5-pro
# - gemini-1.5-flash
```

#### 4. Environment Variables Not Loading
```bash
# Check if .env file exists and is readable
ls -la .env
cat .env | grep -v "^#" | grep -v "^$"

# Load environment manually for testing
set -a; source .env; set +a
python main.py
```

### Debugging Configuration

```python
# Debug configuration loading
from src.core.configuration import Configuration
import os

print("Environment variables:")
for key, value in os.environ.items():
    if any(x in key.upper() for x in ['GOOGLE', 'SUPABASE', 'MODEL', 'DATABASE', 'ADK']):
        print(f"{key}={value[:20]}..." if len(value) > 20 else f"{key}={value}")

config = Configuration()
print(f"\nLoaded configuration:")
print(f"Database mode: {config.database_mode}")
print(f"ADK service mode: {config.adk_service_mode}")
print(f"Model name: {config.model_name}")
```

## 📚 Related Documentation

- **[Installation Guide](installation.md)** - Complete setup instructions
- **[Architecture Overview](../architecture/overview.md)** - System design
- **[Database Architecture](../architecture/database.md)** - Database configuration
- **[Security Guidelines](../guides/security.md)** - Security best practices

---

💡 **Pro tip**: Start with development mode for quickest setup, then upgrade to production mode as needed. Each mode provides the right balance of features and complexity for different use cases.