# Troubleshooting Guide

This comprehensive guide covers common issues and solutions for BooksWriter development and deployment.

## 🎯 Quick Diagnosis

### System Health Check
```bash
# Check if the application is running
curl http://localhost:8000/health

# Check database connectivity
python scripts/database/check_tables.py

# Check available models
curl http://localhost:8000/models

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/test-session
```

## 💾 Database Issues

### Connection Problems

#### Supabase Connection Refused
**Symptoms**: 
- "Connection refused" errors
- "Authentication failed" messages
- Database operations timeout

**Solutions**:
1. **Verify credentials in `.env`**:
   ```bash
   # Check environment variables
   echo $SUPABASE_URL
   echo $SUPABASE_ANON_KEY
   echo $SUPABASE_DB_PASSWORD
   ```

2. **Get correct credentials from Supabase Dashboard**:
   - URL: Dashboard → Settings → API → Project URL
   - Anon Key: Dashboard → Settings → API → Project API keys → `anon public`
   - DB Password: Dashboard → Settings → Database → Connection string

3. **Check IP whitelisting**:
   - Supabase Dashboard → Settings → Database → Network restrictions
   - Ensure your IP is allowed

4. **Test connection manually**:
   ```bash
   curl -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
        -H "apikey: $SUPABASE_ANON_KEY" \
        "$SUPABASE_URL/rest/v1/"
   ```

#### SQLite Database Issues
**Symptoms**:
- "Database is locked" errors
- File permission errors
- Corruption warnings

**Solutions**:
1. **Check file permissions**:
   ```bash
   ls -la *.db
   chmod 664 development.db
   ```

2. **Handle database locks**:
   ```bash
   # Kill processes using the database
   lsof development.db
   # Kill specific processes if needed
   ```

3. **Reset database if corrupted**:
   ```bash
   # Backup first
   cp development.db development.db.backup
   # Remove and recreate
   rm development.db
   python main.py  # Will recreate database
   ```

### Migration Failures

#### Migration Not Applied
**Symptoms**:
- Tables don't exist after migration
- Foreign key constraint errors
- "Relation does not exist" errors

**Solutions**:
1. **Check migration status**:
   ```bash
   npx supabase migration list --linked
   cat migrations/applied_migrations.json
   ```

2. **Apply migrations manually**:
   ```bash
   # For specific migration
   npx supabase db push --password "$SUPABASE_DB_PASSWORD"
   
   # Force apply specific file
   psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
   ```

3. **Verify table creation**:
   ```bash
   python scripts/database/check_tables.py
   ```

#### Schema Consistency Issues
**Symptoms**:
- SQLite works but Supabase fails
- Different column types between databases
- Constraint violations

**Solutions**:
1. **Check schema synchronization**:
   ```python
   # Compare schemas
   python scripts/database/compare_schemas.py
   ```

2. **Re-sync schemas**:
   ```bash
   # Apply all migrations to both databases
   python scripts/database/sync_schemas.py
   ```

## 🔐 Authentication Issues

### Google Cloud Authentication

#### Service Account Key Issues
**Symptoms**:
- "Could not automatically determine credentials"
- "Service account key file not found"
- "Invalid service account"

**Solutions**:
1. **Verify key file path**:
   ```bash
   ls -la config/service-account-key.json
   export GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
   ```

2. **Test authentication**:
   ```bash
   python -c "
   from google.cloud import aiplatform
   aiplatform.init()
   print('Authentication successful')
   "
   ```

3. **Re-download service account key**:
   - Google Cloud Console → IAM & Admin → Service Accounts
   - Select service account → Keys → Add Key → Create new key → JSON

#### API Access Issues
**Symptoms**:
- "Vertex AI API is not enabled"
- "Permission denied" for AI operations
- Model not available errors

**Solutions**:
1. **Enable required APIs**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable generativelanguage.googleapis.com
   ```

2. **Check service account permissions**:
   - Add "Vertex AI User" role
   - Add "AI Platform Developer" role

3. **Verify project configuration**:
   ```bash
   gcloud config list
   gcloud auth application-default print-access-token
   ```

## 🌐 Network and Server Issues

### Port Already in Use
**Symptoms**:
- "Address already in use" error
- Cannot start server on port 8000

**Solutions**:
1. **Find and kill process**:
   ```bash
   # Find process using port 8000
   lsof -ti:8000
   
   # Kill the process
   lsof -ti:8000 | xargs kill -9
   
   # Or use different port
   uvicorn src.app:app --port 8001
   ```

2. **Check for other services**:
   ```bash
   netstat -tlnp | grep 8000
   ps aux | grep python | grep 8000
   ```

### WebSocket Connection Issues
**Symptoms**:
- WebSocket connections fail to establish
- Messages not received
- Connection drops frequently

**Solutions**:
1. **Check WebSocket endpoint**:
   ```bash
   # Test WebSocket connection
   wscat -c ws://localhost:8000/ws/test-session
   ```

2. **Verify network configuration**:
   ```bash
   # Check firewall settings
   sudo ufw status
   
   # Check if port is accessible
   telnet localhost 8000
   ```

3. **Debug WebSocket handler**:
   ```python
   # Enable debug logging
   LOG_LEVEL=DEBUG python main.py
   
   # Check websocket handler logs
   tail -f logs/websocket.log
   ```

## 🤖 Agent and Model Issues

### Model Loading Problems
**Symptoms**:
- AI models dropdown doesn't populate
- "Model not found" errors
- Timeout waiting for model response

**Solutions**:
1. **Check model availability**:
   ```bash
   curl http://localhost:8000/models
   ```

2. **Verify Google Cloud configuration**:
   ```python
   # Test model access
   from google.cloud import aiplatform
   from vertexai.generative_models import GenerativeModel
   
   model = GenerativeModel("gemini-2.0-flash-exp")
   response = model.generate_content("Hello")
   print(response.text)
   ```

3. **Check model configuration**:
   ```bash
   # Verify environment variables
   echo $MODEL_NAME
   echo $GOOGLE_CLOUD_PROJECT
   echo $GOOGLE_CLOUD_LOCATION
   ```

### Agent Execution Failures
**Symptoms**:
- Agents return empty responses
- Tool calls fail
- Agent coordination errors

**Solutions**:
1. **Check agent logs**:
   ```bash
   # Enable debug logging
   LOG_LEVEL=DEBUG python main.py
   
   # Check specific agent logs
   grep "PlotGeneratorAgent" logs/agents.log
   ```

2. **Test agent individually**:
   ```python
   # Test agent in isolation
   from src.agents.plot_generator import PlotGeneratorAgent
   from src.core.configuration import Configuration
   
   agent = PlotGeneratorAgent(Configuration())
   # Test agent functionality
   ```

3. **Validate tool interface**:
   ```python
   # Check tool parameters match agent expectations
   from src.tools.writing_tools import save_plot
   
   # Verify tool signature
   import inspect
   print(inspect.signature(save_plot))
   ```

## 🔧 MCP Integration Issues

### MCP Tools Not Available
**Symptoms**:
- MCP tools don't appear in Claude agents
- "MCP server not found" errors
- Tool calls to MCP fail

**Solutions**:
1. **Check MCP server installation**:
   ```bash
   # Test MCP server
   npx @supabase/mcp-server-supabase@latest
   ```

2. **Verify environment variables**:
   ```bash
   # Check system environment variables (not just .env)
   echo $SUPABASE_ACCESS_TOKEN
   echo $SUPABASE_URL
   echo $SUPABASE_ANON_KEY
   ```

3. **Set system environment variables** (Windows):
   ```cmd
   setx SUPABASE_URL "https://your-project.supabase.co"
   setx SUPABASE_ANON_KEY "your-anon-key"
   setx SUPABASE_ACCESS_TOKEN "your-access-token"
   ```

4. **Restart Claude Code completely** after setting environment variables

5. **Check MCP configuration**:
   ```json
   // .claude/mcp.json
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

### MCP Authentication Errors
**Symptoms**:
- "Insufficient permissions" from MCP operations
- "Access denied" for database operations
- Authentication timeouts

**Solutions**:
1. **Verify access token permissions**:
   - Supabase Dashboard → Account Settings → Access Tokens
   - Ensure token has required database permissions

2. **Check Row Level Security (RLS)**:
   ```sql
   -- Disable RLS temporarily for testing
   ALTER TABLE plots DISABLE ROW LEVEL SECURITY;
   ```

3. **Use service role key for admin operations**:
   ```bash
   # Use service_role key instead of anon key for admin tasks
   export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
   ```

## 🎨 Frontend Issues

### UI Not Loading
**Symptoms**:
- Blank page on localhost:8000
- JavaScript errors in console
- Static files not loading

**Solutions**:
1. **Check static file serving**:
   ```bash
   # Verify static files exist
   ls -la static/css/
   ls -la static/js/
   
   # Check file permissions
   chmod -R 644 static/
   ```

2. **Check browser console for errors**:
   - Open Developer Tools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed requests

3. **Verify template paths**:
   ```python
   # Check template configuration in main.py
   from fastapi.templating import Jinja2Templates
   templates = Jinja2Templates(directory="templates")
   ```

### Security Policy Violations
**Symptoms**:
- Content Security Policy (CSP) errors
- Inline styles blocked
- DOMPurify integrity errors

**Solutions**:
1. **Check CSP headers**:
   ```javascript
   // Remove strict CSP temporarily for debugging
   // In templates/index.html, comment out:
   // <meta http-equiv="Content-Security-Policy" content="...">
   ```

2. **Fix DOMPurify integrity**:
   ```html
   <!-- Remove integrity attribute temporarily -->
   <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>
   
   <!-- Or get correct hash from https://www.srihash.org/ -->
   ```

3. **Move inline styles to CSS**:
   ```css
   /* Move inline styles to static/css/main.css */
   .hidden { display: none; }
   .typing-indicator { display: block; }
   ```

## 🧪 Testing Issues

### Tests Failing
**Symptoms**:
- pytest failures
- Mock objects not working
- Database tests failing

**Solutions**:
1. **Run tests with verbose output**:
   ```bash
   pytest -v --tb=long
   pytest tests/unit/test_specific.py -v -s
   ```

2. **Check test database setup**:
   ```python
   # Ensure test database is isolated
   @pytest.fixture
   def test_db():
       # Setup test database
       yield
       # Cleanup test database
   ```

3. **Fix mock configuration**:
   ```python
   # Example mock setup
   from unittest.mock import AsyncMock, MagicMock
   
   @pytest.fixture
   def mock_database_adapter():
       mock = AsyncMock()
       mock.save_plot.return_value = {"id": "test-id"}
       return mock
   ```

### Performance Issues
**Symptoms**:
- Slow response times
- High memory usage
- Database connection timeouts

**Solutions**:
1. **Check connection pool metrics**:
   ```bash
   curl http://localhost:8000/metrics/database/pool
   curl http://localhost:8000/metrics/database/health
   ```

2. **Monitor resource usage**:
   ```bash
   # Check memory usage
   ps aux | grep python
   
   # Check database connections
   python -c "
   import asyncio
   from src.core.container import Container
   container = Container()
   metrics = asyncio.run(container.get_database_metrics())
   print(metrics)
   "
   ```

3. **Optimize queries**:
   ```python
   # Use batch operations instead of individual queries
   plots = await repository.get_plots_with_authors_batch(user_id)
   # Instead of N+1 queries
   ```

## 🛠️ Development Tools

### Debugging Commands
```bash
# Check system health
curl http://localhost:8000/health

# View container logs (if using Docker)
docker-compose -f docker-compose.openwebui.yml logs -f

# Database migrations check
python scripts/maintenance/verify_migration.py

# TDD compliance report
python scripts/maintenance/tdd_compliance_report.py

# Connection pool validation
python scripts/database/test_connection_pool.py
```

### Log Analysis
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Filter specific logs
grep "ERROR" logs/application.log
grep "PlotGeneratorAgent" logs/agents.log
grep "database" logs/system.log

# Real-time log monitoring
tail -f logs/application.log | grep "ERROR\|WARNING"
```

### Environment Validation
```bash
# Validate all environment variables
python scripts/validate_environment.py

# Check configuration loading
python -c "
from src.core.configuration import Configuration
config = Configuration()
print('✅ Configuration loaded successfully')
print(f'Database mode: {config.database_mode}')
print(f'ADK service mode: {config.adk_service_mode}')
"
```

## 🚨 Emergency Procedures

### System Recovery
```bash
# 1. Stop all processes
pkill -f "python main.py"
pkill -f uvicorn

# 2. Reset database connections
python scripts/database/reset_connections.py

# 3. Clear application cache
rm -rf __pycache__ src/__pycache__ tests/__pycache__

# 4. Restart with clean state
python main.py
```

### Database Recovery
```bash
# 1. Backup current database
cp development.db development.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. Run database repair
python scripts/database/repair_database.py

# 3. Re-apply migrations if needed
npx supabase db push --password "$SUPABASE_DB_PASSWORD"

# 4. Verify data integrity
python scripts/database/verify_data_integrity.py
```

## 📞 Getting Help

### Information to Gather
Before seeking help, collect this information:

1. **System Information**:
   ```bash
   python --version
   pip list | grep -E "(fastapi|supabase|google)"
   cat .env | grep -v PASSWORD | grep -v TOKEN
   ```

2. **Error Details**:
   - Complete error message
   - Stack trace if available
   - Steps to reproduce

3. **Environment**:
   - Operating system
   - Python version
   - Database mode (SQLite/Supabase)
   - ADK service mode

### Documentation Resources
- **[Architecture Overview](../architecture/overview.md)** - System design
- **[Database Architecture](../architecture/database.md)** - Database issues
- **[MCP Integration](../integrations/mcp-supabase.md)** - MCP troubleshooting
- **[Development Workflow](development.md)** - Development issues

---

This troubleshooting guide covers the most common issues encountered in BooksWriter development and deployment. For additional help, check the related documentation or create detailed issue reports with the information gathering steps above.