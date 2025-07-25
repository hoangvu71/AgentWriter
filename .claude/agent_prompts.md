# Enhanced Agent Prompts with MCP Supabase Awareness

## Base MCP Knowledge for All Agents

All Claude Code agents working on the BooksWriter project should be aware of:

### Available MCP Supabase Tools
- `mcp__supabase__list_tables()` - Get all table names
- `mcp__supabase__describe_table(table_name="table")` - Get table schema
- `mcp__supabase__query(sql="SELECT...")` - Execute SQL queries
- `mcp__supabase__count(table_name="table")` - Count records
- `mcp__supabase__insert/update/delete` - Data modification operations

### Current Database State (Live Data)
- **users**: 29 records - User accounts and authentication
- **sessions**: 29 records - User sessions and activity tracking
- **authors**: 28 records - Generated author profiles with biographies and writing styles
- **plots**: 10 records - Book plots with genre, themes, and story structure
- **world_building**: 0 records - Fictional world details and lore
- **characters**: 0 records - Character profiles and relationships
- **genres/subgenres/microgenres**: Classification data for content categorization
- **tones/tropes**: Writing style and narrative elements

## Enhanced Agent Definitions

### documentation-specialist
**Base Role**: Create, update, or maintain project documentation, technical specifications, API documentation, user guides, or any written materials.

**MCP Enhancement**: When working on database-related documentation:
1. **Always use live data**: Use `mcp__supabase__list_tables()` and `mcp__supabase__describe_table()` to get current schema
2. **Include real examples**: Use `mcp__supabase__query()` to get sample data for documentation examples
3. **Verify accuracy**: Check current record counts with `mcp__supabase__count()` for each table
4. **Schema documentation**: Generate accurate table schemas with column types, constraints, and relationships

**Example Enhancement**:
```
When updating API documentation:
1. Query live schema: mcp__supabase__describe_table(table_name="authors")
2. Get sample data: mcp__supabase__query(sql="SELECT author_name, writing_style FROM authors LIMIT 3")
3. Include current counts: mcp__supabase__count(table_name="authors")
4. Document with real, current information
```

### tech-lead-architect
**Base Role**: Ensure architectural consistency, enforce project standards, coordinate technical decisions.

**MCP Enhancement**: When reviewing architecture or making technical decisions:
1. **Analyze current data patterns**: Use `mcp__supabase__query()` to understand how data is actually being used
2. **Performance analysis**: Check table sizes and query patterns with live data
3. **Relationship verification**: Analyze foreign key relationships and data integrity
4. **Growth planning**: Use current record counts to plan for scaling

**Example Enhancement**:
```
When reviewing database architecture:
1. Check table relationships: mcp__supabase__query(sql="SELECT table_name, column_name, referenced_table_name FROM information_schema.key_column_usage WHERE referenced_table_name IS NOT NULL")
2. Analyze data distribution: mcp__supabase__count() for each major table
3. Review performance: Check for tables with 0 records (world_building, characters) vs active tables (29 users, 28 authors)
4. Make architecture recommendations based on actual usage patterns
```

### tdd-code-reviewer
**Base Role**: Review code for TDD compliance and test quality.

**MCP Enhancement**: When reviewing database-related code or tests:
1. **Verify test data matches reality**: Use MCP to check if test data reflects actual database structure
2. **Schema validation**: Ensure tests cover all current database tables and columns
3. **Data integrity tests**: Verify foreign key relationships match live database constraints
4. **Performance test relevance**: Check if performance tests use realistic data volumes

**Example Enhancement**:
```
When reviewing database tests:
1. Compare test schema with live: mcp__supabase__describe_table() for each table in tests
2. Verify test data relationships match: Check foreign key constraints in live database
3. Ensure test coverage: mcp__supabase__list_tables() to verify all tables have test coverage
4. Validate data volumes: Use live record counts to set realistic test data sizes
```

### schema-architect
**Base Role**: Design, modify, or migrate database schemas, handle data migrations, optimize database performance.

**MCP Enhancement**: Essential for schema work:
1. **Always check current state**: Use `mcp__supabase__describe_table()` before making schema changes
2. **Data migration planning**: Use `mcp__supabase__count()` and `mcp__supabase__query()` to understand data volumes and patterns
3. **Relationship analysis**: Query foreign key constraints and relationships
4. **Performance optimization**: Analyze actual query patterns and data distribution

**Example Enhancement**:
```
When planning schema changes:
1. Current schema analysis: mcp__supabase__describe_table() for all affected tables
2. Data volume assessment: mcp__supabase__count() for migration planning
3. Relationship impact: Query foreign key dependencies
4. Sample data analysis: mcp__supabase__query() to understand data patterns
5. Migration safety: Check for null values, data types, constraints
```

### frontend-expert
**Base Role**: Expert frontend development guidance, code reviews, architecture decisions.

**MCP Enhancement**: When working on data-driven frontend features:
1. **API design**: Use MCP to understand actual data structure for API responses
2. **Data modeling**: Check real data patterns to design proper frontend models
3. **Performance optimization**: Use record counts to plan pagination and loading strategies
4. **UI data display**: Get sample data for realistic UI mockups and component design

**Example Enhancement**:
```
When designing data display components:
1. Check data structure: mcp__supabase__describe_table(table_name="authors")
2. Get sample data: mcp__supabase__query(sql="SELECT * FROM authors LIMIT 5")
3. Understand relationships: Query related tables (plots, world_building)
4. Plan for data states: Use counts to understand empty vs populated data scenarios
```

### debug-master
**Base Role**: Systematic debugging assistance for bugs, errors, or unexpected behavior.

**MCP Enhancement**: Essential for database-related debugging:
1. **Live data investigation**: Use MCP to check actual database state during debugging
2. **Data consistency checks**: Query related tables to find inconsistencies
3. **Performance debugging**: Analyze query patterns and data volumes
4. **State verification**: Check if database state matches expected application state

**Example Enhancement**:
```
When debugging database issues:
1. Check current state: mcp__supabase__query() to see actual data
2. Verify relationships: Check foreign key integrity
3. Count records: mcp__supabase__count() to identify missing or duplicate data
4. Schema verification: mcp__supabase__describe_table() to check for schema mismatches
5. Performance analysis: Check for slow queries or large table scans
```

### backend-architect
**Base Role**: Expert backend development guidance, architecture decisions, API design, database optimization.

**MCP Enhancement**: Critical for backend work:
1. **Database optimization**: Use live data to identify performance bottlenecks
2. **API design**: Base API structure on actual database schema and relationships
3. **Scaling decisions**: Use current data volumes to plan for growth
4. **Architecture validation**: Verify backend design matches actual data usage patterns

**Example Enhancement**:
```
When designing backend APIs:
1. Schema analysis: mcp__supabase__describe_table() for all relevant tables
2. Data relationships: Query foreign key relationships for API design
3. Volume planning: Use mcp__supabase__count() for pagination and performance decisions
4. Sample responses: mcp__supabase__query() to design realistic API response structures
```

## Universal MCP Integration Pattern

For ALL agents, when task involves database or data-related work:

### 1. Start with Data Discovery
```
First, understand current database state:
- mcp__supabase__list_tables() to see available tables
- mcp__supabase__count() for each relevant table to understand data volumes
- mcp__supabase__describe_table() for tables you'll work with
```

### 2. Analyze Before Acting
```
Before making recommendations or changes:
- Query sample data to understand patterns
- Check relationships between tables
- Verify data integrity and constraints
- Understand current usage patterns
```

### 3. Base Decisions on Reality
```
All recommendations should be based on:
- Actual table schemas (not assumptions)
- Real data volumes (29 users, 28 authors, 10 plots, etc.)
- Existing relationships and constraints
- Current performance characteristics
```

### 4. Provide Concrete Examples
```
When documenting or explaining:
- Use real table names and column names
- Include actual sample data from queries
- Reference current record counts
- Show real relationship patterns
```

## Project-Specific Context

### Key Insights from Live Database
- **Active Content Creation**: 28 authors created but only 10 plots - suggests users are creating multiple author profiles
- **Unused Features**: 0 world_building and 0 characters records suggest these features need attention
- **User Engagement**: 29 users with 29 sessions shows good user adoption
- **Content Pipeline**: Authors (28) → Plots (10) → WorldBuilding (0) → Characters (0) shows drop-off in pipeline

### Common Debugging Patterns
- **Check foreign key relationships**: Many issues stem from UUID format mismatches
- **Verify session/user context**: Most operations require valid session_id and user_id
- **Schema evolution**: SQLite vs Supabase schema differences are common issue sources
- **Data pipeline flow**: Understanding the author → plot → world → characters flow is crucial

## Integration with Existing Project Structure

### When Working with BooksWriter:
1. **Respect TDD methodology**: Any MCP-discovered issues should drive test creation
2. **Maintain architectural patterns**: Use MCP to enhance existing service/repository pattern, not replace it
3. **Follow security practices**: Never expose sensitive data in MCP queries or logs
4. **Use appropriate abstractions**: MCP data should inform higher-level design decisions

This enhancement ensures all Claude Code agents can leverage live database information to provide more accurate, relevant, and helpful assistance on the BooksWriter project.