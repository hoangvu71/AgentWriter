# Performance Monitoring Reference

Comprehensive monitoring and metrics reference for BooksWriter system performance.

## Overview

BooksWriter includes built-in monitoring capabilities for database performance, agent execution metrics, and system health monitoring.

## Database Monitoring

### Connection Pool Metrics

#### Real-time Pool Statistics
```bash
GET /metrics/database/pool
```

**Response**:
```json
{
  "pool_type": "supabase",
  "active_connections": 8,
  "idle_connections": 12,
  "total_connections": 20,
  "hit_rate": 0.92,
  "miss_count": 15,
  "health_failures": 0,
  "average_connection_time_ms": 32,
  "peak_connections_used": 18,
  "connection_timeouts": 0
}
```

#### Health Status Monitoring
```bash
GET /metrics/database/health
```

**Response**:
```json
{
  "status": "healthy",
  "last_health_check": "2025-01-28T10:30:00Z",
  "total_connections": 20,
  "healthy_connections": 20,
  "failed_connections": 0,
  "database_type": "supabase",
  "response_time_ms": 45,
  "uptime_seconds": 86400
}
```

### Query Performance Metrics

#### Slow Query Detection
- Queries > 1000ms logged as warnings
- Queries > 5000ms logged as errors
- Automatic query optimization suggestions

#### Database Performance Tracking
```python
# Query execution time tracking
@monitor_query_performance
def get_plots_with_authors():
    # Database query implementation
    pass

# Connection pool monitoring
@monitor_connection_usage
def database_operation():
    # Database operation implementation
    pass
```

## Agent Performance Monitoring

### Agent Execution Metrics

#### Individual Agent Performance
```bash
GET /metrics/agents/{agent_name}
```

**Response**:
```json
{
  "agent_name": "PlotGeneratorAgent",
  "total_invocations": 156,
  "success_rate": 0.97,
  "average_processing_time_ms": 2850,
  "min_processing_time_ms": 1200,
  "max_processing_time_ms": 8500,
  "error_count": 5,
  "timeout_count": 2,
  "last_execution": "2025-01-28T10:30:00Z"
}
```

#### Multi-Agent Workflow Metrics
```bash
GET /metrics/workflows
```

**Response**:
```json
{
  "total_workflows": 45,
  "successful_workflows": 42,
  "average_workflow_duration_ms": 12500,
  "agent_coordination_time_ms": 250,
  "workflow_patterns": {
    "plot_only": 15,
    "plot_author": 12,
    "full_foundation": 18
  }
}
```

### AI Model Performance

#### Model Response Metrics
```bash
GET /metrics/models/{model_id}
```

**Response**:
```json
{
  "model_id": "gemini-2.0-flash-exp",
  "total_requests": 234,
  "success_rate": 0.99,
  "average_response_time_ms": 1850,
  "average_tokens_per_request": 750,
  "error_rate": 0.01,
  "rate_limit_hits": 0,
  "cost_per_request": 0.002
}
```

## System Performance Monitoring

### Overall System Metrics

#### Performance Summary
```bash
GET /metrics/performance/summary
```

**Response**:
```json
{
  "timestamp": "2025-01-28T10:30:00Z",
  "uptime_seconds": 86400,
  "requests_total": 2500,
  "requests_per_second": 0.029,
  "average_response_time_ms": 285,
  "error_rate": 0.003,
  "memory_usage_mb": 512,
  "cpu_usage_percent": 15.5,
  "database": {
    "connection_pool_hit_rate": 0.92,
    "average_query_time_ms": 32,
    "active_connections": 8
  },
  "agents": {
    "total_invocations": 680,
    "average_processing_time_ms": 2400,
    "success_rate": 0.98
  }
}
```

### WebSocket Connection Monitoring

#### Active Connections
```bash
GET /metrics/websocket/connections
```

**Response**:
```json
{
  "active_connections": 12,
  "total_connections_created": 156,
  "average_session_duration_seconds": 1800,
  "messages_per_second": 0.8,
  "connection_errors": 3,
  "disconnection_rate": 0.02
}
```

## Alerting and Notifications

### Performance Thresholds

#### Database Alerts
- Connection pool utilization > 80%
- Query response time > 1000ms
- Health check failures > 3 consecutive
- Connection timeouts > 5 per hour

#### Agent Alerts  
- Agent success rate < 95%
- Average processing time > 10 seconds
- Error rate > 5%
- Timeout rate > 2%

#### System Alerts
- Memory usage > 80%
- CPU usage > 70% sustained
- Error rate > 1%
- Response time > 5 seconds

### Alert Configuration
```python
# alerts.py
ALERT_THRESHOLDS = {
    "database": {
        "pool_utilization": 0.8,
        "query_time_ms": 1000,
        "health_check_failures": 3
    },
    "agents": {
        "success_rate": 0.95,
        "processing_time_ms": 10000,
        "error_rate": 0.05
    },
    "system": {
        "memory_usage": 0.8,
        "cpu_usage": 0.7,
        "error_rate": 0.01
    }
}
```

## Logging and Observability

### Structured Logging
```python
import logging
import structlog

# Configure structured logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

logger = structlog.get_logger()

# Agent execution logging
logger.info(
    "agent_execution_completed",
    agent_name="PlotGeneratorAgent",
    processing_time_ms=2850,
    success=True,
    user_id="user123"
)

# Database operation logging
logger.info(
    "database_query_executed",
    query_type="SELECT",
    table="plots",
    execution_time_ms=45,
    rows_returned=15
)
```

### Performance Profiling

#### Agent Performance Profiling
```python
from functools import wraps
import time

def profile_agent_execution(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Log performance metrics
            logger.info(
                "agent_performance",
                function=func.__name__,
                execution_time_ms=execution_time,
                success=True
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                "agent_performance",
                function=func.__name__,
                execution_time_ms=execution_time,
                success=False,
                error=str(e)
            )
            raise
    return wrapper
```

## Monitoring Dashboard

### Key Performance Indicators (KPIs)

#### System Health Dashboard
- **Uptime**: 99.9% target
- **Response Time**: < 500ms average
- **Error Rate**: < 0.5%
- **Database Performance**: < 100ms average query time

#### Agent Performance Dashboard
- **Agent Success Rate**: > 95%
- **Processing Time**: < 5 seconds average  
- **Workflow Completion**: > 90%
- **Tool Execution**: > 98% success rate

#### Database Dashboard
- **Connection Pool Health**: < 80% utilization
- **Query Performance**: < 100ms average
- **Connection Success**: > 99%
- **Health Check Status**: All passing

### Monitoring Tools Integration

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Agent metrics
agent_requests_total = Counter(
    'agent_requests_total',
    'Total agent requests',
    ['agent_name', 'status']
)

agent_processing_time = Histogram(
    'agent_processing_seconds',
    'Agent processing time',
    ['agent_name']
)

# Database metrics
db_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)
```

## Performance Optimization

### Database Optimization
- Connection pool sizing based on load
- Query caching for frequently accessed data
- Index optimization for common queries
- Connection health monitoring

### Agent Optimization
- Model selection based on task complexity
- Response caching for similar requests
- Parallel agent execution where possible
- Timeout optimization based on historical data

### System Optimization
- Memory usage monitoring and optimization
- CPU usage balancing across processes
- Network optimization for external API calls
- Disk I/O optimization for database operations

## Related Documentation

- **[Database Architecture](../architecture/database.md)** - Database design and performance
- **[Multi-Agent System](../architecture/agents.md)** - Agent coordination and performance
- **[API Reference](api.md)** - API endpoints for metrics
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Performance troubleshooting

---

*This reference provides comprehensive monitoring information for maintaining optimal BooksWriter system performance.*