"""
API endpoints for monitoring connection pool and database performance metrics.
Provides insights into connection pool utilization and performance.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..core.container import get_container
from ..core.logging import get_logger

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = get_logger("metrics_router")


@router.get("/database/pool")
async def get_database_pool_metrics() -> Dict[str, Any]:
    """Get database connection pool performance metrics"""
    try:
        container = get_container()
        metrics = await container.get_database_metrics()
        
        if not metrics:
            return {
                "message": "Connection pool metrics not available",
                "metrics": {}
            }
        
        # Add derived metrics
        if metrics.get("pool_hits", 0) + metrics.get("pool_misses", 0) > 0:
            metrics["hit_rate_percentage"] = round(
                (metrics["pool_hits"] / (metrics["pool_hits"] + metrics["pool_misses"])) * 100, 2
            )
        
        # Connection utilization
        if metrics.get("max_connections", 0) > 0:
            metrics["utilization_percentage"] = round(
                (metrics["active_connections"] / metrics.get("max_connections", 1)) * 100, 2
            )
        
        return {
            "message": "Database connection pool metrics retrieved successfully",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error retrieving database pool metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database metrics")


@router.post("/database/pool/reset")
async def reset_database_pool_metrics() -> Dict[str, str]:
    """Reset database connection pool metrics counters"""
    try:
        container = get_container()
        await container.reset_database_metrics()
        
        return {
            "message": "Database connection pool metrics reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Error resetting database pool metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset database metrics")


@router.get("/database/health")
async def get_database_health() -> Dict[str, Any]:
    """Get database connection health status"""
    try:
        container = get_container()
        database = container.get("database")
        
        # Basic health check
        health_status = {
            "status": "unknown",
            "connection_pool_available": hasattr(database, 'connection_pool'),
            "batch_operations_available": (
                hasattr(database, 'batch_insert') and 
                hasattr(database, 'batch_select_by_ids') and 
                hasattr(database, 'batch_update')
            ),
            "metrics_available": hasattr(database, 'get_pool_metrics'),
            "database_type": type(database).__name__
        }
        
        # Try a simple database operation
        try:
            if hasattr(database, 'count'):
                # Test with a likely existing table
                test_count = await database.count("users", {})
                health_status["status"] = "healthy"
                health_status["test_query_successful"] = True
                health_status["users_count"] = test_count
            else:
                health_status["status"] = "degraded"
                health_status["test_query_successful"] = False
                health_status["reason"] = "Database adapter missing count method"
        except Exception as db_error:
            health_status["status"] = "unhealthy"
            health_status["test_query_successful"] = False
            health_status["error"] = str(db_error)
        
        # Get connection pool metrics if available
        if health_status["connection_pool_available"]:
            try:
                pool_metrics = await container.get_database_metrics()
                health_status["pool_metrics"] = pool_metrics
                
                # Assess pool health
                if pool_metrics:
                    total_connections = pool_metrics.get("total_connections", 0)
                    health_check_failures = pool_metrics.get("health_check_failures", 0)
                    
                    if total_connections > 0 and health_check_failures == 0:
                        health_status["pool_status"] = "healthy"
                    elif health_check_failures > 0:
                        health_status["pool_status"] = "degraded"
                        health_status["pool_warning"] = f"{health_check_failures} health check failures"
                    else:
                        health_status["pool_status"] = "no_connections"
                else:
                    health_status["pool_status"] = "metrics_unavailable"
            except Exception:
                health_status["pool_status"] = "error"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check database health")


@router.get("/performance/summary")
async def get_performance_summary() -> Dict[str, Any]:
    """Get overall system performance summary"""
    try:
        container = get_container()
        
        # Database metrics
        db_metrics = await container.get_database_metrics()
        
        # Calculate performance indicators
        performance_summary = {
            "database": {
                "connection_pool_enabled": bool(db_metrics),
                "metrics": db_metrics
            },
            "recommendations": []
        }
        
        # Performance recommendations based on metrics
        if db_metrics:
            hit_rate = db_metrics.get("pool_hits", 0) / (
                db_metrics.get("pool_hits", 0) + db_metrics.get("pool_misses", 0) + 1
            ) * 100
            
            if hit_rate < 80:
                performance_summary["recommendations"].append({
                    "type": "warning",
                    "message": f"Connection pool hit rate is {hit_rate:.1f}%. Consider increasing pool size.",
                    "metric": "pool_hit_rate",
                    "value": hit_rate
                })
            
            health_failures = db_metrics.get("health_check_failures", 0)
            if health_failures > 0:
                performance_summary["recommendations"].append({
                    "type": "error",
                    "message": f"{health_failures} connection health check failures detected.",
                    "metric": "health_failures",
                    "value": health_failures
                })
            
            avg_connection_time = db_metrics.get("avg_connection_time", 0)
            if avg_connection_time > 0.1:  # 100ms
                performance_summary["recommendations"].append({
                    "type": "warning",
                    "message": f"Average connection time is {avg_connection_time:.3f}s. Consider optimizing.",
                    "metric": "avg_connection_time",
                    "value": avg_connection_time
                })
        
        return performance_summary
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance summary")


@router.get("/database/config")
async def get_database_config() -> Dict[str, Any]:
    """Get current database configuration (non-sensitive info only)"""
    try:
        container = get_container()
        database = container.get("database")
        
        config_info = {
            "database_type": type(database).__name__,
            "features": {
                "connection_pooling": hasattr(database, 'connection_pool'),
                "batch_operations": (
                    hasattr(database, 'batch_insert') and 
                    hasattr(database, 'batch_select_by_ids') and 
                    hasattr(database, 'batch_update')
                ),
                "health_monitoring": hasattr(database, 'get_pool_metrics'),
                "async_operations": True  # All our operations are async
            }
        }
        
        # Add pool configuration if available (non-sensitive)
        if hasattr(database, 'pool_config'):
            pool_config = database.pool_config
            config_info["pool_config"] = {
                "min_connections": pool_config.min_connections,
                "max_connections": pool_config.max_connections,
                "max_idle_time": pool_config.max_idle_time,
                "connection_timeout": pool_config.connection_timeout,
                "health_check_interval": pool_config.health_check_interval,
                "metrics_enabled": pool_config.enable_metrics
            }
        
        return config_info
        
    except Exception as e:
        logger.error(f"Error getting database config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database configuration")