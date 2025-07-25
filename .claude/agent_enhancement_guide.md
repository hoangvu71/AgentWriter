# How to Enhance Claude Agents with MCP Awareness

Since Claude Code's built-in agents can't be directly modified, use these enhanced prompt patterns to ensure agents use MCP tools effectively.

## Enhanced Agent Call Patterns

### Documentation Specialist
**Instead of:**
```
/agents documentation-specialist
"Update the database schema documentation"
```

**Use this enhanced prompt:**
```
/agents documentation-specialist
"Update the database schema documentation for BooksWriter. You have access to MCP Supabase tools - use mcp__supabase__list_tables() to get all table names, mcp__supabase__describe_table() for each table's schema, and mcp__supabase__query() to get sample data. Current live data: 29 users, 29 sessions, 28 authors, 10 plots, 0 world_building, 0 characters. Base documentation on live database schema, not assumptions."
```

### Tech Lead Architect  
**Instead of:**
```
/agents tech-lead-architect
"Review our database design"
```

**Use this enhanced prompt:**
```
/agents tech-lead-architect  
"Review BooksWriter's database design and architecture. Use MCP Supabase tools to analyze the live database: mcp__supabase__list_tables() for table overview, mcp__supabase__count() for each table to understand data volumes, mcp__supabase__describe_table() for schema analysis. Key insight: we have 28 authors but only 10 plots, and 0 world_building/characters - analyze this pipeline and suggest improvements based on actual data patterns."
```

### Schema Architect
**Instead of:**
```
/agents schema-architect
"Help optimize our database"
```

**Use this enhanced prompt:**
```
/agents schema-architect
"Optimize BooksWriter's database schema using live data analysis. Use mcp__supabase__describe_table() for all tables, mcp__supabase__query() to analyze data patterns and relationships, mcp__supabase__count() for volume analysis. Focus on: 1) Why world_building (0 records) and characters (0 records) aren't being used when we have 28 authors and 10 plots, 2) Foreign key relationships and constraints, 3) Performance optimization opportunities."
```

### Debug Master
**Instead of:**
```
/agents debug-master
"Debug why world building isn't working"
```

**Use this enhanced prompt:**
```
/agents debug-master
"Debug why world_building table has 0 records despite having 28 authors and 10 plots. Use MCP tools: mcp__supabase__describe_table('world_building') for schema, mcp__supabase__query() to check foreign key relationships and constraints, mcp__supabase__describe_table('plots') to verify plot_id relationships. Analyze the data flow from authors → plots → world_building and identify the breakpoint."
```

### Frontend Expert
**Instead of:**
```
/agents frontend-expert
"Design a dashboard for the book data"
```

**Use this enhanced prompt:**
```
/agents frontend-expert
"Design a dashboard for BooksWriter book data. Use MCP tools to understand the data structure: mcp__supabase__describe_table() for authors, plots, world_building, characters tables. Get sample data with mcp__supabase__query(). Current state: 29 users, 28 authors, 10 plots, 0 world_building, 0 characters. Design UI that handles both populated tables (authors/plots) and empty ones (world/characters), showing the content creation pipeline flow."
```

### Backend Architect
**Instead of:**
```
/agents backend-architect
"Design an API for content retrieval"
```

**Use this enhanced prompt:**
```
/agents backend-architect
"Design APIs for BooksWriter content retrieval. Use MCP tools to analyze current data structure: mcp__supabase__list_tables(), mcp__supabase__describe_table() for core tables, mcp__supabase__query() for relationship patterns. Design endpoints that handle the content pipeline: users(29) → authors(28) → plots(10) → world_building(0) → characters(0). Include proper foreign key handling and pagination for authors/plots tables."
```

## Universal Enhancement Template

For any agent task involving database work, use this template:

```
/agents [AGENT_TYPE]
"[YOUR_TASK_DESCRIPTION]

MCP Context: You have access to MCP Supabase tools for live database analysis:
- mcp__supabase__list_tables() - Get all table names
- mcp__supabase__describe_table(table_name) - Get table schema  
- mcp__supabase__query(sql) - Execute SELECT queries
- mcp__supabase__count(table_name) - Count records

Current BooksWriter database state:
- users: 29 records
- sessions: 29 records  
- authors: 28 records
- plots: 10 records
- world_building: 0 records
- characters: 0 records
- Genre/classification tables: 1-2 records each

Use these tools to base your analysis on actual database schema and data rather than assumptions. Pay attention to the content creation pipeline drop-off: authors(28) → plots(10) → world_building(0)."
```

## Quick Reference Prompts

### Get Database Overview
```
/agents debug-master
"Provide a complete overview of the BooksWriter database. Use mcp__supabase__list_tables() to get all tables, then mcp__supabase__count() for each table to show record counts, and mcp__supabase__describe_table() for the main content tables (users, sessions, authors, plots, world_building, characters). Identify any issues or patterns in the data."
```

### Schema Analysis
```
/agents schema-architect  
"Analyze BooksWriter's complete database schema using MCP tools. Use mcp__supabase__describe_table() for all tables, focusing on foreign key relationships, constraints, and data types. Use mcp__supabase__query() to verify relationship integrity. Provide recommendations for schema improvements."
```

### Performance Analysis
```
/agents backend-architect
"Analyze BooksWriter database performance using MCP tools. Check table sizes with mcp__supabase__count(), analyze slow queries, and examine index usage. Use mcp__supabase__query() with EXPLAIN to understand query performance. Focus on the authors(28) and plots(10) tables as they have the most data."
```

### Documentation Update
```
/agents documentation-specialist
"Update all BooksWriter database documentation using live schema data. Use mcp__supabase__list_tables() for complete table list, mcp__supabase__describe_table() for each table's current schema, and mcp__supabase__query() for sample data examples. Ensure documentation reflects the actual current database structure, not outdated information."
```

## Pro Tips

### 1. Always Include Current Data Context
When calling agents, always mention the current record counts so they understand the system's usage patterns.

### 2. Be Specific About Tables
Instead of "check the database", specify which tables are relevant to your task.

### 3. Combine Multiple Tools
Encourage agents to use multiple MCP tools together for comprehensive analysis.

### 4. Reference Real Issues
Point agents to actual problems like "0 world_building records despite 28 authors" to focus their analysis.

### 5. Request Concrete Examples
Ask agents to include actual table names, column names, and sample queries in their responses.

This approach ensures Claude Code agents leverage your MCP Supabase tools effectively while working within the existing agent system constraints.