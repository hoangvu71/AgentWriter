# MCP Supabase Integration

The BooksWriter project integrates with Supabase through the Model Context Protocol (MCP), providing Claude instances with direct database access capabilities. This enables real-time database operations, content queries, and system analysis without requiring API endpoints.

## 📋 Table of Contents
1. [MCP Setup and Configuration](#mcp-setup-and-configuration)
2. [Database Structure](#database-structure)
3. [Available MCP Operations](#available-mcp-operations)
4. [Agent Integration Patterns](#agent-integration-patterns)
5. [Multi-Agent System Integration](#multi-agent-system-integration)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

## 🔧 MCP Setup and Configuration

### 1. MCP Configuration File

The MCP server is configured via `.claude/mcp.json`:

```json
{
  "servers": {
    "supabase": {
      "command": "npx",
      "args": [
        "@supabase/mcp-server-supabase@latest"
      ],
      "env": {
        "SUPABASE_ACCESS_TOKEN": "${SUPABASE_ACCESS_TOKEN}"
      }
    }
  }
}
```

### 2. Environment Variables

Required environment variables in `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://cfqgzbudjnvtyxrrvvmo.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_ACCESS_TOKEN=sbp_your-personal-access-token

# Database Mode Selection
DATABASE_MODE=supabase  # Options: supabase, sqlite
```

### 3. Prerequisites

- Node.js and npm installed
- Supabase project with proper access tokens
- Claude Desktop or compatible MCP client
- Network access to Supabase instance

## 📊 Database Structure

### Current Database Status (Live Data)

Based on recent analysis, the database contains **18 tables** with the following content:

| Table Name | Record Count | Purpose |
|------------|--------------|---------|
| **users** | 29 | User authentication and tracking |
| **sessions** | 29 | Conversation session management |
| **authors** | 28 | AI-generated author profiles |
| **plots** | 10 | Book plot data with genre metadata |
| **world_building** | 2 | Fictional world construction data |
| **characters** | 2 | Character populations and relationships |
| **orchestrator_decisions** | 146 | AI routing decision analytics |
| **agent_invocations** | 336 | Detailed agent execution tracking |
| **performance_metrics** | 0 | System performance monitoring |
| **trace_events** | 0 | OpenTelemetry distributed tracing |

### Core Content Tables Schema

See [Database Architecture](../architecture/database.md) for complete schema details.

## 🛠️ Available MCP Operations

### 1. Database Discovery

**mcp__supabase__list_tables**
- Lists all available tables in the database
- Returns table names and basic metadata
- Essential for database exploration

**mcp__supabase__describe_table**
- Provides detailed schema information for specific tables
- Includes column types, constraints, and relationships
- Critical for understanding data structure

### 2. Data Retrieval

**mcp__supabase__query**
- Execute SELECT queries with full PostgreSQL syntax
- Supports JOINs, aggregations, and complex filtering
- JSONB operators for structured data queries
- Pagination and ordering capabilities

Example usage:
```sql
-- Get recent plots with author information
SELECT p.title, p.genre, a.author_name, p.created_at 
FROM plots p 
LEFT JOIN authors a ON p.id = a.plot_id 
ORDER BY p.created_at DESC 
LIMIT 10;

-- Search world building data
SELECT world_name, overview, geography->>'climate' as climate
FROM world_building 
WHERE world_type = 'high_fantasy'
ORDER BY created_at DESC;

-- Analyze agent performance
SELECT agent_name, COUNT(*) as invocations, AVG(duration_ms) as avg_duration
FROM agent_invocations 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY agent_name
ORDER BY avg_duration DESC;
```

### 3. Data Modification

**mcp__supabase__insert**
- Insert new records into any table
- Full validation and constraint checking
- Returns inserted record with generated UUIDs

**mcp__supabase__update**
- Update existing records with WHERE clauses
- Supports partial updates and JSONB field updates
- Automatic timestamp management

**mcp__supabase__delete**
- Delete records with proper foreign key handling
- CASCADE deletion where configured
- Safe deletion with confirmation

### 4. Advanced Operations

**JSONB Queries**
- PostgreSQL JSONB operators (@>, ->, ->>, etc.)
- Full-text search within JSON fields
- Efficient filtering and indexing

**Aggregation and Analytics**
- COUNT, SUM, AVG operations
- GROUP BY with complex expressions
- Window functions for advanced analytics

## 🤖 Agent Integration Patterns

### 1. Content Retrieval Pattern

Agents can directly query for existing content to inform new generation:

```python
# PlotGeneratorAgent example
def get_user_plot_history(self, user_id):
    """Retrieve user's previous plots for context"""
    query = """
    SELECT title, genre, subgenre, plot_summary 
    FROM plots 
    WHERE user_id = %s 
    ORDER BY created_at DESC 
    LIMIT 5
    """
    # MCP query execution would happen here
    return previous_plots

def avoid_repetition(self, new_plot, previous_plots):
    """Ensure new content doesn't repeat themes"""
    # Logic to check against previous_plots
    pass
```

### 2. Content Validation Pattern

Validate generated content against existing database constraints:

```python
# AuthorGeneratorAgent example
def validate_author_uniqueness(self, author_name, user_id):
    """Ensure author names are unique per user"""
    query = """
    SELECT COUNT(*) 
    FROM authors 
    WHERE author_name = %s AND user_id = %s
    """
    # MCP validation query
    return count == 0
```

### 3. Analytics-Informed Generation

Use system analytics to improve content quality:

```python
# EnhancementAgent example
def get_successful_patterns(self, content_type):
    """Find patterns in highly-rated content"""
    query = """
    SELECT ai.parsed_json, ai.success
    FROM agent_invocations ai
    WHERE ai.agent_name = %s 
    AND ai.success = true
    ORDER BY ai.created_at DESC
    LIMIT 20
    """
    # Analyze successful patterns for improvement
    return patterns
```

## 🔄 Multi-Agent System Integration

### 1. Orchestrator Decision Tracking

The OrchestratorAgent logs all routing decisions for system analysis:

```sql
INSERT INTO orchestrator_decisions (
    session_id, user_id, routing_decision, 
    agents_invoked, extracted_parameters, workflow_plan
) VALUES (%s, %s, %s, %s, %s, %s);
```

### 2. Agent Performance Monitoring

Each agent invocation is tracked for performance optimization:

```sql
INSERT INTO agent_invocations (
    invocation_id, agent_name, user_id, session_id,
    request_content, start_time, llm_model,
    tool_calls, success, duration_ms
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

### 3. Cross-Agent Content Sharing

Agents can access content created by other agents:

```python
# CharactersAgent accessing WorldBuildingAgent content
def get_world_context(self, plot_id):
    """Get world building context for character creation"""
    query = """
    SELECT world_name, overview, cultural_systems, power_systems
    FROM world_building 
    WHERE plot_id = %s
    """
    return world_context

# WorldBuildingAgent accessing PlotGeneratorAgent content
def get_plot_requirements(self, plot_id):
    """Get plot details to inform world building"""
    query = """
    SELECT genre, subgenre, tone, target_audience, plot_summary
    FROM plots 
    WHERE id = %s
    """
    return plot_details
```

## 💻 Usage Examples

### 1. System Health Check

```sql
-- Check database connectivity and recent activity
SELECT 
    'users' as table_name, COUNT(*) as record_count
FROM users
UNION ALL
SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL
SELECT 'plots', COUNT(*) FROM plots
UNION ALL
SELECT 'authors', COUNT(*) FROM authors
ORDER BY table_name;
```

### 2. Content Analysis

```sql
-- Analyze content generation patterns
SELECT 
    p.genre,
    COUNT(*) as plot_count,
    COUNT(DISTINCT a.id) as author_count,
    COUNT(DISTINCT w.id) as world_count
FROM plots p
LEFT JOIN authors a ON p.id = a.plot_id
LEFT JOIN world_building w ON p.id = w.plot_id
GROUP BY p.genre
ORDER BY plot_count DESC;
```

### 3. Performance Analytics

```sql
-- Agent performance over time
SELECT 
    DATE(created_at) as date,
    agent_name,
    COUNT(*) as invocations,
    AVG(duration_ms) as avg_duration,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_runs
FROM agent_invocations
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), agent_name
ORDER BY date DESC, avg_duration DESC;
```

### 4. User Journey Analysis

```sql
-- Trace user content creation journey
SELECT 
    s.session_id,
    p.title as plot_title,
    a.author_name,
    w.world_name,
    c.character_count,
    p.created_at as plot_created,
    a.created_at as author_created,
    w.created_at as world_created
FROM sessions s
LEFT JOIN plots p ON s.id = p.session_id
LEFT JOIN authors a ON p.id = a.plot_id
LEFT JOIN world_building w ON p.id = w.plot_id
LEFT JOIN characters c ON p.id = c.plot_id
WHERE s.user_id = 'specific-user-uuid'
ORDER BY s.created_at DESC;
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Problems

**Symptom**: MCP operations fail with timeout errors
**Solutions**:
- Verify `SUPABASE_ACCESS_TOKEN` is valid and has proper permissions
- Check network connectivity to Supabase instance
- Confirm MCP server is properly installed: `npx @supabase/mcp-server-supabase@latest`

#### 2. Permission Errors

**Symptom**: "Insufficient permissions" or "Access denied" errors
**Solutions**:
- Verify Supabase access token has required database permissions
- Check Row Level Security (RLS) policies if enabled
- Ensure service role key is used for administrative operations

#### 3. Query Syntax Errors

**Symptom**: SQL queries fail with syntax errors
**Solutions**:
- Use PostgreSQL syntax (not SQLite)
- Proper escaping for string literals
- JSONB operators: `->`, `->>`, `@>`, `?`
- UUID values must be properly formatted strings

#### 4. Data Type Mismatches

**Symptom**: Insert/update operations fail with type errors
**Solutions**:
- UUIDs as strings, not objects
- JSONB fields require proper JSON formatting
- Timestamp values in ISO format
- Arrays use PostgreSQL array syntax: `{'item1','item2'}`

### Debugging Techniques

#### 1. Query Testing

Test queries directly in Supabase SQL editor before using in MCP:

```sql
-- Test basic connectivity
SELECT NOW() as current_time;

-- Test table access
SELECT COUNT(*) FROM users;

-- Test JSONB operations
SELECT geography->>'climate' FROM world_building LIMIT 1;
```

#### 2. MCP Operation Validation

Validate MCP operations step by step:

1. **list_tables** - Confirm database connectivity
2. **describe_table** - Verify table structure
3. **query** - Test with simple SELECT
4. **insert** - Test with minimal required fields
5. **update/delete** - Test with WHERE clauses

#### 3. Error Log Analysis

Common error patterns and solutions:

```
Error: "relation does not exist"
Solution: Check table name spelling and case sensitivity

Error: "column does not exist" 
Solution: Use describe_table to verify column names

Error: "invalid input syntax for type uuid"
Solution: Ensure UUID strings are properly formatted

Error: "invalid input syntax for type json"
Solution: Validate JSON structure before insertion
```

## 🔒 Security Considerations

### 1. Access Control

- **Service Role Tokens**: Use service role tokens for administrative operations
- **Anon Key Limitations**: Anonymous keys have restricted permissions
- **Row Level Security**: Enable RLS for production multi-tenant scenarios

### 2. Data Protection

- **UUID Primary Keys**: Prevent enumeration attacks
- **Parameterized Queries**: Avoid SQL injection (MCP handles this)
- **Field Validation**: Validate all inputs before database operations

### 3. Audit Trail

The system automatically tracks:
- All agent invocations with timestamps
- User actions and content generation
- Performance metrics and error rates
- Orchestrator routing decisions

### 4. Production Readiness

For production deployment:

```sql
-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE plots ENABLE ROW LEVEL SECURITY;
-- ... (enable for all user-content tables)

-- Create RLS policies
CREATE POLICY "Users can only access their own data" 
ON users FOR ALL 
USING (auth.uid() = id);

CREATE POLICY "Users can only access their own sessions" 
ON sessions FOR ALL 
USING (auth.uid() = user_id);
-- ... (create policies for all tables)
```

## 🔄 Integration with Existing Architecture

### 1. Service Layer Compatibility

MCP operations complement existing service layer:

```python
# Existing ContentSavingService
class ContentSavingService:
    def save_plot(self, plot_data):
        # Traditional API-based save
        pass

# MCP-enhanced operations
def analyze_plot_trends():
    # Direct database analysis via MCP
    query = "SELECT genre, COUNT(*) FROM plots GROUP BY genre"
    # Execute via MCP
    return results
```

### 2. WebSocket Integration

MCP operations can be triggered via WebSocket:

```javascript
// Frontend sends analysis request
websocket.send({
    type: 'analyze_content',
    data: { content_type: 'plots', timeframe: '30_days' }
});

// Backend executes MCP queries and streams results
```

### 3. Agent Tool Enhancement

Existing agent tools can be enhanced with MCP capabilities:

```python
@tool
def search_content(query: str, content_type: str):
    """Enhanced search using direct database queries"""
    if content_type == "plots":
        sql = """
        SELECT title, plot_summary, genre 
        FROM plots 
        WHERE plot_summary ILIKE %s
        ORDER BY created_at DESC
        """
        # Execute via MCP for faster, more flexible search
    
    return search_results
```

## 🔮 Future Enhancements

### 1. Real-Time Notifications

Potential integration with Supabase Realtime:
- Live updates on content generation progress
- Multi-user collaboration notifications
- System health monitoring alerts

### 2. Advanced Analytics

Enhanced analytics capabilities:
- Content quality scoring based on user feedback
- Agent performance optimization recommendations
- Predictive content generation patterns

### 3. Content Versioning

Database schema extensions for:
- Content revision tracking
- A/B testing of generated content
- Rollback capabilities for content modifications

## 📚 Related Documentation

- **[Claude Agents MCP Access](claude-agents-mcp.md)** - How Claude agents use MCP tools
- **[Database Architecture](../architecture/database.md)** - Complete database design
- **[MCP Tools Reference](../reference/mcp-tools.md)** - Quick reference guide
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Additional troubleshooting

---

This MCP Supabase integration provides Claude instances with powerful, direct database access while maintaining the existing multi-agent architecture. The integration enables real-time analytics, cross-agent content sharing, and system optimization through comprehensive data access.