# MCP Tools Quick Reference for Claude Agents

> **This file has been moved and reorganized.**
> 
> Please see the new location: **[docs/reference/mcp-tools.md](docs/reference/mcp-tools.md)**
> 
> The content has been updated and integrated into the new documentation structure.

---

# MCP Tools Quick Reference for Claude Agents

## Available MCP Supabase Tools

When using `/agents` or `Task` tool, Claude agents have access to these MCP tools:

### Database Query Tools
```python
# List all tables
mcp__supabase__list_tables()

# Get table schema
mcp__supabase__describe_table(table_name="authors")

# Execute SQL queries
mcp__supabase__query(sql="SELECT * FROM authors LIMIT 5")

# Count records
mcp__supabase__count(table_name="plots", filters={"genre": "fantasy"})
```

### Data Modification Tools
```python
# Insert new record
mcp__supabase__insert(table_name="authors", data={"author_name": "New Author"})

# Update existing record  
mcp__supabase__update(table_name="authors", id="uuid", data={"author_name": "Updated"})

# Delete record
mcp__supabase__delete(table_name="authors", id="uuid")
```

## Current Database State (Live)

**Core Tables:**
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

## Usage Examples for Agents

### Documentation Agent
```
/agents documentation-specialist
"Update database schema docs using live data"

Agent will use:
- mcp__supabase__list_tables()
- mcp__supabase__describe_table() for each table
- mcp__supabase__query() for sample data
```

### Tech Lead Agent  
```
/agents tech-lead-architect
"Analyze database performance and suggest optimizations"

Agent will use:
- mcp__supabase__count() for table sizes
- mcp__supabase__query() with EXPLAIN for performance analysis
- mcp__supabase__describe_table() for relationship analysis
```

### Debug Agent
```
/agents debug-master
"Debug why plot creation is failing"

Agent will use:
- mcp__supabase__query() to check recent plots
- mcp__supabase__describe_table() to verify schema
- mcp__supabase__count() to check related records
```

## Quick Test

To verify MCP is working for agents:
```
/agents debug-master
"Test MCP connection and show me the first 3 authors from the database"
```

Expected: Agent uses `mcp__supabase__query(sql="SELECT author_name FROM authors LIMIT 3")` and shows results.