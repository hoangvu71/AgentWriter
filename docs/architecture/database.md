# Database Architecture

This document details BooksWriter's database architecture, including the dual-database design, connection pooling implementation, and performance optimizations.

## 🏗️ Database Design Overview

BooksWriter uses a **dual-database architecture** that supports both cloud and local development:

- **Supabase (PostgreSQL)**: Production/staging environments with real-time features
- **SQLite**: Local development with fast setup and no external dependencies
- **Unified Schema**: Both databases share the same schema for consistency
- **Connection Pooling**: High-performance connection management for both adapters

## 📊 Database Schema

### Core Content Tables

#### 1. users
```sql
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. sessions
```sql
CREATE TABLE sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. plots
```sql
CREATE TABLE plots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    plot_summary TEXT NOT NULL,
    genre VARCHAR(100),
    subgenre VARCHAR(100),
    microgenre VARCHAR(100),
    trope VARCHAR(255),
    tone VARCHAR(255),
    target_audience JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. authors
```sql
CREATE TABLE authors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plot_id UUID REFERENCES plots(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    pen_name VARCHAR(255),
    biography TEXT NOT NULL,
    writing_style TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. world_building
```sql
CREATE TABLE world_building (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plot_id UUID REFERENCES plots(id) ON DELETE SET NULL,
    world_name TEXT NOT NULL,
    world_type TEXT NOT NULL,
    overview TEXT NOT NULL,
    geography JSONB NOT NULL DEFAULT '{}',
    political_landscape JSONB NOT NULL DEFAULT '{}',
    cultural_systems JSONB NOT NULL DEFAULT '{}',
    economic_framework JSONB NOT NULL DEFAULT '{}',
    historical_timeline JSONB NOT NULL DEFAULT '{}',
    power_systems JSONB NOT NULL DEFAULT '{}',
    languages_and_communication JSONB NOT NULL DEFAULT '{}',
    religious_and_belief_systems JSONB NOT NULL DEFAULT '{}',
    unique_elements JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Analytics and Monitoring Tables

#### 6. orchestrator_decisions
Tracks AI routing decisions for system optimization.

#### 7. agent_invocations
Comprehensive agent execution tracking with performance metrics.

#### 8. performance_metrics
Time-series data for system monitoring.

#### 9. trace_events
OpenTelemetry integration for distributed tracing.

### Current Database Status

**Live Data (as of January 2025)**:

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

## 🚄 Connection Pooling Implementation

### Key Features

The database layer includes comprehensive connection pooling for both SQLite and Supabase adapters, addressing performance issues and eliminating the N+1 query problem.

#### 1. Connection Pool Infrastructure (`src/database/connection_pool.py`)

- **SQLiteConnectionPool**: High-performance connection pool for SQLite with WAL mode
- **SupabaseConnectionPool**: Connection pool for Supabase clients with health monitoring
- **ConnectionPoolConfig**: Configurable pool settings (min/max connections, timeouts)
- **PoolMetrics**: Comprehensive performance tracking

#### 2. Enhanced Database Adapters

**SQLite Adapter** (`src/database/sqlite_adapter.py`):
- Connection pooling with WAL mode optimization
- Memory-mapped I/O and increased cache size
- Batch operations: `batch_insert()`, `batch_select_by_ids()`, `batch_update()`
- Performance metrics and health monitoring

**Supabase Adapter** (`src/database/supabase_adapter.py`):
- Pooled Supabase client connections
- Efficient bulk operations for cloud database
- Health monitoring and connection management
- Performance tracking for optimization

### Configuration

#### Environment Variables

```bash
# Connection Pool Configuration
DB_POOL_MIN_CONNECTIONS=3          # Minimum pool connections
DB_POOL_MAX_CONNECTIONS=15         # Maximum pool connections  
DB_POOL_MAX_IDLE_TIME=300          # Idle timeout (seconds)
DB_POOL_CONNECTION_TIMEOUT=30      # Connection timeout (seconds)
DB_POOL_HEALTH_CHECK_INTERVAL=60   # Health check interval (seconds)
DB_POOL_ENABLE_METRICS=true        # Enable metrics collection

# Database Selection
DATABASE_MODE=supabase              # 'supabase' or 'sqlite'
SQLITE_DB_PATH=development.db       # SQLite database path
```

#### Default Pool Settings

- **SQLite**: 3-15 connections, optimized for local development
- **Supabase**: 2-8 connections, optimized for cloud operations
- **Health Checks**: 60-second intervals with automatic cleanup
- **Metrics**: Enabled by default for monitoring

## 📈 Performance Improvements

### Before Implementation
- **Individual Connections**: New connection for each database operation
- **Thread Pool Overhead**: Every operation executed in thread pool
- **N+1 Query Problem**: Multiple individual queries for related data
- **No Connection Reuse**: Connections created and destroyed constantly

### After Implementation
- **Connection Reuse**: Pooled connections with 80%+ hit rates
- **Batch Operations**: Single queries for multiple records
- **Optimized SQLite**: WAL mode, memory-mapped I/O, larger cache
- **Health Monitoring**: Automatic connection health management
- **Performance Metrics**: Real-time monitoring and optimization insights

## 🔧 Batch Operations and N+1 Prevention

### BatchOperationsMixin (`src/repositories/batch_operations.py`)

Provides reusable batch operations for repositories:

```python
# Get plots with authors (avoids N+1 queries)
plots_with_authors = await plot_repository.get_plots_with_authors_batch(user_id)

# Create multiple plots efficiently
plot_ids = await plot_repository.create_multiple_plots(plots_list)

# Search with related data and pagination
result = await plot_repository.search_plots_with_related_data(
    criteria={"genre": "fantasy"},
    include_authors=True,
    limit=50,
    offset=0
)
```

### Optimized Repositories

Enhanced repositories with batch operations:
- **PlotRepository**: Batch plot operations with related data
- **AuthorRepository**: Efficient author creation and retrieval
- **CharactersRepository**: Optimized character population queries
- **WorldBuildingRepository**: Bulk world data operations

## 📊 Performance Monitoring

### Metrics API (`src/routers/metrics.py`)

Real-time performance monitoring endpoints:

- **`/metrics/database/pool`** - Real-time pool statistics
- **`/metrics/database/health`** - Connection health status
- **`/metrics/performance/summary`** - Overall system performance
- **`/metrics/database/config`** - Current pool configuration

### Key Metrics Tracked

- **Pool Utilization**: Active vs. idle connections
- **Hit Rate**: Pool hits vs. misses (target: >80%)
- **Connection Lifecycle**: Created, closed, failed health checks
- **Query Performance**: Average connection time, query count
- **Health Status**: Connection health and pool status

### Performance Indicators

- **High Hit Rate (>80%)**: Indicates efficient connection reuse
- **Low Average Connection Time (<100ms)**: Shows good pool performance
- **Zero Health Failures**: Indicates stable connections
- **Balanced Active/Idle Ratio**: Shows proper pool sizing

## 💻 Usage Examples

### Connection Pool Monitoring

```python
# Get pool metrics
metrics = await container.get_database_metrics()
print(f"Hit rate: {metrics['hit_rate']:.2%}")
print(f"Active connections: {metrics['active_connections']}")

# Reset metrics
await container.reset_database_metrics()
```

### API Monitoring

```bash
# Get pool metrics
curl http://localhost:8000/metrics/database/pool

# Check database health
curl http://localhost:8000/metrics/database/health

# Get performance summary
curl http://localhost:8000/metrics/performance/summary
```

## 🔄 Migration System

### Database Migrations

The project uses a version-controlled migration system:

- **Migration Files**: Stored in `migrations/` directory
- **Applied Tracking**: `migrations/applied_migrations.json`
- **Automated Validation**: Safety checks before applying
- **Rollback Support**: Each migration includes rollback instructions

### Migration Commands

```bash
# Create new migration
python scripts/setup/create_migration.py "description_of_changes"

# Apply migrations (Supabase)
npx supabase db push --password "$SUPABASE_DB_PASSWORD"

# Verify migration success
python scripts/database/check_tables.py
```

## 🔧 Service Container Integration

### Container Management (`src/core/container.py`)

- **Pool Configuration**: Environment-based pool configuration
- **Automatic Startup**: Background health monitoring tasks
- **Graceful Shutdown**: Proper connection cleanup on application exit
- **Metrics Access**: Container-level methods for pool monitoring

```python
# Container automatically manages database lifecycle
container = Container()
await container.startup()  # Initializes connection pools
# ... application runs ...
await container.shutdown()  # Graceful cleanup
```

## 🧪 Testing

### Comprehensive Test Suite

The database layer includes extensive testing:

- **Pool Configuration Tests**: Verify configuration handling
- **Connection Pool Tests**: Test pool behavior and metrics
- **Adapter Integration Tests**: Verify pooling integration
- **Batch Operations Tests**: Test batch functionality
- **Performance Tests**: Verify performance improvements
- **Concurrent Access Tests**: Test thread safety

### Running Tests

```bash
# Run database tests
pytest tests/unit/test_*database*.py -v
pytest tests/unit/test_*connection*.py -v
pytest tests/unit/test_*repository*.py -v

# Run performance comparison
pytest tests/integration/test_sqlite_adapter_complete.py -v
```

## 🔒 Security Considerations

### Access Control
- **Service Role Tokens**: Administrative operations use service role tokens
- **Anon Key Limitations**: Anonymous keys have restricted permissions
- **Row Level Security**: Enable RLS for production multi-tenant scenarios

### Data Protection
- **UUID Primary Keys**: Prevent enumeration attacks
- **Parameterized Queries**: Avoid SQL injection (handled by adapters)
- **Field Validation**: Validate all inputs before database operations

### Production Readiness

For production deployment:

```sql
-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE plots ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can only access their own data" 
ON users FOR ALL 
USING (auth.uid() = id);

CREATE POLICY "Users can only access their own sessions" 
ON sessions FOR ALL 
USING (auth.uid() = user_id);
```

## 🚀 Architecture Benefits

### Scalability
- **Connection Limits**: Prevents connection exhaustion
- **Resource Management**: Efficient use of database connections
- **Health Monitoring**: Automatic recovery from connection issues

### Performance
- **Reduced Latency**: Connection reuse eliminates setup overhead
- **Batch Operations**: Significant reduction in query round-trips
- **SQLite Optimizations**: WAL mode and memory optimizations

### Monitoring
- **Real-time Metrics**: Live performance monitoring
- **Health Checks**: Proactive connection management
- **Performance Insights**: Data-driven optimization opportunities

## 🔮 Future Enhancements

### Potential Improvements
- **Connection Multiplexing**: Share connections across operations
- **Query Caching**: Cache frequent query results
- **Load Balancing**: Distribute connections across multiple databases
- **Advanced Metrics**: Detailed query performance analytics

### Performance Optimizations
- **Prepared Statements**: Reuse prepared queries
- **Connection Warming**: Pre-warm connections with common queries
- **Adaptive Pool Sizing**: Automatically adjust pool size based on load
- **Query Optimization**: Automatic query performance analysis

## 📚 Related Documentation

- **[Architecture Overview](overview.md)** - Complete system architecture
- **[Database Migrations Guide](../guides/database-migrations.md)** - Migration procedures
- **[MCP Supabase Integration](../integrations/mcp-supabase.md)** - Direct database access
- **[Performance Monitoring](../reference/monitoring.md)** - Monitoring and metrics

---

This database architecture provides a robust, scalable, and monitored foundation that significantly improves BooksWriter's performance while maintaining system reliability and supporting both local development and cloud deployment scenarios.