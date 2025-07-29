# MCP Tools Quick Reference

Quick reference guide for MCP Supabase tools available to Claude agents and developers.

## 🛠️ Available MCP Supabase Tools

### Database Query Tools

#### `mcp__supabase__list_tables()`
**Purpose**: Get all table names from the database
**Parameters**: None
**Returns**: List of table names
**Example**:
```python
tables = await mcp__supabase__list_tables()
# Returns: ['users', 'sessions', 'plots', 'authors', ...]
```

#### `mcp__supabase__describe_table(table_name)`
**Purpose**: Get detailed schema information for a specific table
**Parameters**:
- `table_name` (string): Name of the table to describe
**Returns**: Table schema with columns, types, and constraints
**Example**:
```python
schema = await mcp__supabase__describe_table(table_name="authors")
# Returns detailed column information, constraints, indexes
```

#### `mcp__supabase__query(sql)`
**Purpose**: Execute SELECT queries with full PostgreSQL syntax
**Parameters**:
- `sql` (string): PostgreSQL SELECT query
**Returns**: Query results as list of dictionaries
**Example**:
```python
results = await mcp__supabase__query(sql="SELECT * FROM authors LIMIT 5")
# Returns: [{'id': '...', 'author_name': '...', ...}, ...]
```

#### `mcp__supabase__count(table_name, filters=None)`
**Purpose**: Count records in a table with optional filtering
**Parameters**:
- `table_name` (string): Name of the table
- `filters` (dict, optional): Filter conditions
**Returns**: Record count
**Example**:
```python
count = await mcp__supabase__count(table_name="plots", filters={"genre": "fantasy"})
# Returns: 5
```

### Data Modification Tools

#### `mcp__supabase__insert(table_name, data)`
**Purpose**: Insert new record into a table
**Parameters**:
- `table_name` (string): Target table name
- `data` (dict): Record data to insert
**Returns**: Inserted record with generated ID
**Example**:
```python
new_author = await mcp__supabase__insert(
    table_name="authors",
    data={"author_name": "New Author", "biography": "Bio text..."}
)
```

#### `mcp__supabase__update(table_name, id, data)`
**Purpose**: Update existing record by ID
**Parameters**:
- `table_name` (string): Target table name
- `id` (string): Record UUID to update
- `data` (dict): Fields to update
**Returns**: Updated record
**Example**:
```python
updated = await mcp__supabase__update(
    table_name="authors",
    id="uuid-string",
    data={"author_name": "Updated Name"}
)
```

#### `mcp__supabase__delete(table_name, id)`
**Purpose**: Delete record by ID
**Parameters**:
- `table_name` (string): Target table name
- `id` (string): Record UUID to delete
**Returns**: Deletion confirmation
**Example**:
```python
result = await mcp__supabase__delete(table_name="authors", id="uuid-string")
```

## 📊 Current Database State

**Core Tables** (Live Data):
- `users`: 29 records
- `sessions`: 29 records  
- `authors`: 28 records
- `plots`: 10 records
- `world_building`: 2 records
- `characters`: 2 records

**Classification Tables**:
- `genres`: 1 record
- `target_audiences`: 2 records
- `subgenres`: 1 record
- `microgenres`: 1 record
- `tropes`: 1 record
- `tones`: 1 record

**Analytics Tables**:
- `orchestrator_decisions`: 146 records
- `agent_invocations`: 336 records
- `performance_metrics`: 0 records
- `trace_events`: 0 records

## 💻 Common Usage Patterns

### Database Exploration
```python
# Get overview of all tables
tables = await mcp__supabase__list_tables()
for table in tables:
    count = await mcp__supabase__count(table_name=table)
    print(f"{table}: {count} records")
```

### Content Analysis
```python
# Analyze plot distribution by genre
results = await mcp__supabase__query(sql="""
    SELECT genre, COUNT(*) as count
    FROM plots 
    GROUP BY genre 
    ORDER BY count DESC
""")
```

### Performance Monitoring
```python
# Check agent performance
performance = await mcp__supabase__query(sql="""
    SELECT 
        agent_name,
        COUNT(*) as invocations,
        AVG(duration_ms) as avg_duration,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
    FROM agent_invocations
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY agent_name
    ORDER BY avg_duration DESC
""")
```

### Data Relationships
```python
# Get plots with their authors
plots_with_authors = await mcp__supabase__query(sql="""
    SELECT 
        p.title,
        p.genre,
        p.created_at,
        a.author_name,
        a.pen_name
    FROM plots p
    LEFT JOIN authors a ON p.id = a.plot_id
    ORDER BY p.created_at DESC
    LIMIT 10
""")
```

## 🤖 Agent Integration Examples

### Documentation Specialist Agent
```python
# Use in agent workflows
/agents documentation-specialist
"Update database schema docs using live data"

# Agent will use:
tables = await mcp__supabase__list_tables()
for table in tables:
    schema = await mcp__supabase__describe_table(table_name=table)
    sample_data = await mcp__supabase__query(
        sql=f"SELECT * FROM {table} LIMIT 3"
    )
    # Generate documentation from live data
```

### Tech Lead Architect Agent
```python
/agents tech-lead-architect
"Analyze database performance and suggest optimizations"

# Agent will use:
table_sizes = {}
for table in await mcp__supabase__list_tables():
    table_sizes[table] = await mcp__supabase__count(table_name=table)

# Analyze query performance
slow_queries = await mcp__supabase__query(sql="""
    EXPLAIN (ANALYZE, BUFFERS) 
    SELECT * FROM plots p JOIN authors a ON p.id = a.plot_id
""")
```

### Debug Master Agent
```python
/agents debug-master
"Debug why plot creation is failing"

# Agent will use:
recent_plots = await mcp__supabase__query(sql="""
    SELECT * FROM plots 
    ORDER BY created_at DESC 
    LIMIT 5
""")

recent_errors = await mcp__supabase__query(sql="""
    SELECT * FROM agent_invocations 
    WHERE success = false 
    AND agent_name = 'PlotGeneratorAgent'
    ORDER BY created_at DESC 
    LIMIT 10
""")
```

## 🚨 Safety Guidelines

### Query Safety
```python
# Good: Use LIMIT for large tables
SELECT * FROM plots LIMIT 10

# Avoid: Unlimited queries on large tables
SELECT * FROM plots  # Could return thousands of records
```

### Read-Only Best Practices
```python
# Prefer SELECT queries for analysis
SELECT COUNT(*) FROM table_name

# Use INSERT/UPDATE/DELETE sparingly and carefully
# Always verify the impact before modifying data
```

### Error Handling
```python
try:
    result = await mcp__supabase__query(sql="SELECT COUNT(*) FROM authors")
    return f"Found {result[0]['count']} authors"
except Exception as e:
    return f"Query failed: {e} - falling back to cached data"
```

## ⚡ Quick Tests

### Test MCP Connection
```python
/agents debug-master
"Test MCP connection and show me the first 3 authors from the database"

# Expected: Agent uses mcp__supabase__query() and shows results
```

### Verify Database Health
```python
# Quick health check
tables = await mcp__supabase__list_tables()
user_count = await mcp__supabase__count(table_name="users")
plot_count = await mcp__supabase__count(table_name="plots")

print(f"✅ Found {len(tables)} tables")
print(f"✅ {user_count} users, {plot_count} plots")
```

## 🔗 JSONB Operations

### Query JSONB Fields
```python
# World building JSONB queries
worlds = await mcp__supabase__query(sql="""
    SELECT 
        world_name,
        geography->>'climate' as climate,
        political_landscape->>'government_type' as government
    FROM world_building
    WHERE geography @> '{"climate": "temperate"}'
""")
```

### JSONB Operators Reference
- `->` : Get JSON object field by key
- `->>` : Get JSON object field as text
- `@>` : Does left JSON contain right JSON
- `?` : Does string exist as top-level key
- `?&` : Do all strings exist as top-level keys
- `?|` : Do any strings exist as top-level keys

## 📚 Related Documentation

- **[MCP Supabase Integration](../integrations/mcp-supabase.md)** - Complete integration guide
- **[Claude Agents MCP Access](../integrations/claude-agents-mcp.md)** - Agent usage patterns
- **[Database Architecture](../architecture/database.md)** - Database schema details
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - MCP troubleshooting

---

This reference provides quick access to all MCP tools and common usage patterns for efficient database operations and analysis in BooksWriter.