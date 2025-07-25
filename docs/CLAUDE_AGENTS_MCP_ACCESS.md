# Claude Code Agents MCP Access Guide

## Overview

This guide documents how Claude Code's built-in agents (accessed via `/agents` command or `Task` tool) can directly access and use MCP Supabase tools when working on the BooksWriter project.

## MCP Configuration for Claude Agents

### Current Setup
Your `.claude/mcp.json` configuration makes Supabase MCP tools available to all Claude agents:

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

### Environment Variables Required
Ensure these are set in your `.env`:
```bash
SUPABASE_URL=https://cfqgzbudjnvtyxrrvvmo.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ACCESS_TOKEN=sbp_52daeb2d737663036052abc28d90aa4cefdb3e4d
```

## Available MCP Tools for Claude Agents

When MCP Supabase is properly configured, Claude agents have access to these tools:

### Core Database Operations
- `mcp__supabase__list_tables` - Get all table names
- `mcp__supabase__describe_table` - Get table schema details
- `mcp__supabase__query` - Execute SQL queries
- `mcp__supabase__insert` - Insert new records
- `mcp__supabase__update` - Update existing records
- `mcp__supabase__delete` - Delete records

### Project-Specific Operations
- `mcp__supabase__count` - Count records with filters
- `mcp__supabase__search` - Search across tables
- `mcp__supabase__get_schema` - Get complete database schema

## Agent Usage Patterns

### 1. Documentation Specialist Agent

**When working on API documentation:**
```
Task: "Update API documentation with current database schema"

The documentation-specialist can:
1. Use mcp__supabase__list_tables to get all table names
2. Use mcp__supabase__describe_table for each table to get schema
3. Use mcp__supabase__query to get sample data for examples
4. Generate comprehensive API docs with real data structure
```

**Example Agent Usage:**
```python
# Agent can call MCP tools directly:
tables = await mcp__supabase__list_tables()
for table in tables:
    schema = await mcp__supabase__describe_table(table_name=table)
    # Document the schema
```

### 2. Tech Lead Architect Agent

**When reviewing database design:**
```
Task: "Review database design and suggest optimizations"

The tech-lead-architect can:
1. Query mcp__supabase__get_schema for full database structure
2. Use mcp__supabase__query to analyze data patterns
3. Use mcp__supabase__count to check table sizes
4. Provide architectural recommendations based on real data
```

### 3. Backend Architect Agent

**When designing new features:**
```
Task: "Design a new reporting feature for book analytics"

The backend-architect can:
1. Query existing data structure with MCP tools
2. Analyze current data relationships
3. Suggest new tables or schema changes
4. Provide implementation recommendations
```

### 4. Debug Master Agent

**When troubleshooting database issues:**
```
Task: "Debug why plot generation is failing"

The debug-master can:
1. Query recent plots data to identify patterns
2. Check for foreign key constraint issues
3. Analyze error logs in relation to database state
4. Provide specific debugging recommendations
```

## Agent MCP Tool Discovery

### How Agents Know MCP Tools Are Available

Claude agents automatically discover MCP tools when:
1. MCP server is properly configured in `.claude/mcp.json`
2. Environment variables are set correctly
3. MCP server is running and accessible

### Agent Tool Introspection

Agents can check available tools:
```python
# Agents can discover available MCP tools
available_tools = get_available_tools()
mcp_tools = [tool for tool in available_tools if tool.startswith('mcp__supabase__')]
```

## Practical Examples

### Example 1: Documentation Agent Using MCP

```
User: "/agents documentation-specialist - Update the database schema documentation"

Agent Response:
"I'll use MCP tools to get the current database schema and update the documentation.

1. Getting table list...
   [Calls mcp__supabase__list_tables]
   
2. For each table, getting schema details...
   [Calls mcp__supabase__describe_table for each table]
   
3. Getting sample data for examples...
   [Calls mcp__supabase__query with SELECT statements]
   
4. Updating documentation with real schema and examples..."
```

### Example 2: Tech Lead Using MCP for Architecture Review

```
User: "/agents tech-lead-architect - Review our database performance"

Agent Response:
"I'll analyze the database structure and performance using MCP tools.

1. Analyzing table sizes and relationships...
   [Calls mcp__supabase__count for each table]
   
2. Checking index usage and query patterns...
   [Calls mcp__supabase__query with EXPLAIN statements]
   
3. Reviewing foreign key constraints...
   [Calls mcp__supabase__describe_table for relationship analysis]
   
Architecture recommendations based on analysis..."
```

## Database Context for Agents

### Current BooksWriter Database Structure (Live Data)

Agents have access to these tables with current record counts:

**Core Content Tables:**
- `users`: 29 records
- `sessions`: 29 records  
- `authors`: 28 records
- `plots`: 10 records
- `world_building`: 0 records
- `characters`: 0 records

**Classification Tables:**
- `genres`: 1 record
- `target_audiences`: 2 records
- `subgenres`: 1 record
- `microgenres`: 1 record
- `tropes`: 1 record
- `tones`: 1 record

**Workflow Tables:**
- `orchestrator_decisions`: 0 records
- `improvement_sessions`: 0 records
- `iterations`: 0 records
- `critiques`: 0 records
- `enhancements`: 0 records
- `scores`: 0 records

## Agent Capabilities Enhancement

### What MCP Access Enables for Agents

1. **Real-Time Data Analysis**: Agents can query current database state
2. **Schema-Aware Recommendations**: Agents understand actual data structure
3. **Data-Driven Documentation**: Documentation reflects real schema and data
4. **Accurate Troubleshooting**: Debug issues with actual database state
5. **Performance Analysis**: Analyze real query performance and data patterns

### Agent Workflows Enhanced by MCP

**Before MCP:**
- Agents work with static information
- Documentation may be outdated
- Recommendations based on assumptions

**With MCP:**
- Agents query live database for current state
- Documentation always reflects real schema
- Recommendations based on actual data patterns

## Troubleshooting MCP Access for Agents

### Common Issues

1. **MCP Tools Not Available to Agents**
   ```bash
   # Check MCP server status
   curl -X POST http://localhost:3000/mcp/status
   
   # Verify environment variables
   echo $SUPABASE_ACCESS_TOKEN
   ```

2. **Authentication Errors**
   ```bash
   # Test Supabase connection
   curl -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
        -H "apikey: $SUPABASE_ANON_KEY" \
        "$SUPABASE_URL/rest/v1/"
   ```

3. **Agent Can't Find MCP Tools**
   - Restart Claude Code session
   - Check `.claude/mcp.json` syntax
   - Verify MCP server is running

### Debugging Agent MCP Usage

```python
# Agents can self-diagnose MCP availability
def check_mcp_availability():
    try:
        tables = mcp__supabase__list_tables()
        return f"MCP working - found {len(tables)} tables"
    except Exception as e:
        return f"MCP error: {e}"
```

### Testing Agent MCP Access

**Manual Test:**
```
User: "/agents debug-master - Test MCP connection and list available tools"

Expected Agent Response:
"Testing MCP Supabase connection...
✓ MCP server accessible
✓ Authentication working
✓ Available tables: users, sessions, authors, plots, ...
✓ MCP tools ready for use"
```

## Best Practices for Agents Using MCP

### 1. Efficient Query Patterns
```python
# Good: Specific queries
SELECT author_name, created_at FROM authors LIMIT 10

# Avoid: Expensive operations without limits
SELECT * FROM authors  # No limit on large tables
```

### 2. Error Handling
```python
try:
    result = mcp__supabase__query(sql="SELECT COUNT(*) FROM authors")
    return f"Found {result[0]['count']} authors"
except Exception as e:
    return f"Query failed: {e} - falling back to documentation"
```

### 3. Security Considerations
- Agents should avoid exposing sensitive data in logs
- Use parameterized queries when possible
- Respect table access permissions

## Integration with BooksWriter Development

### Agent-Enhanced Development Workflow

1. **Feature Planning**: Architects query current data to plan features
2. **Documentation**: Docs always reflect current schema
3. **Debugging**: Debug-master uses real data for troubleshooting
4. **Testing**: Test planning based on actual data patterns
5. **Performance**: Backend architects analyze real performance metrics

### Agent Collaboration Patterns

**Multi-Agent Database Analysis:**
```
1. tech-lead-architect: Analyzes database structure
2. backend-architect: Reviews performance implications  
3. documentation-specialist: Updates docs with findings
4. debug-master: Identifies potential issues
```

## Conclusion

With MCP Supabase access, Claude Code agents become significantly more effective at working with the BooksWriter project by:

- **Operating on live data** instead of assumptions
- **Providing accurate, up-to-date information**
- **Making data-driven recommendations**
- **Troubleshooting with actual database state**

This creates a powerful development environment where AI agents can work intelligently with your real project data and database structure.