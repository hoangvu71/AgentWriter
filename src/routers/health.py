"""
Health check endpoint for system monitoring.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from ..core.configuration import Configuration
from ..database.database_factory import db_factory

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    System health check endpoint.
    
    Returns:
        Health status including version and service availability
    """
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "api": "operational",
            "websocket": "operational"
        }
    }
    
    # Check database connection
    try:
        import os
        adapter = await db_factory.get_adapter()
        database_mode = os.getenv("DATABASE_MODE", "supabase").lower()
        
        if database_mode == "sqlite":
            db_path = os.getenv("SQLITE_DB_PATH", "development.db")
            health_status["services"]["database"] = f"operational (development mode - SQLite: {db_path})"
            health_status["database_mode"] = "development"
        elif db_factory.is_offline_mode():
            health_status["services"]["database"] = "operational (fallback mode - SQLite)"
            health_status["database_mode"] = "fallback"
        else:
            health_status["services"]["database"] = "operational (production - Supabase)"
            health_status["database_mode"] = "production"
            
        # Test database with a simple query
        await adapter.count("genres")
        
    except Exception as e:
        health_status["services"]["database"] = "error"
        health_status["warnings"] = [f"Database connection issue: {str(e)}"]
        health_status["database_mode"] = "error"
    
    # Check if any critical services are down
    if any(status == "error" for status in health_status["services"].values()):
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/health/detailed")
async def detailed_health_check(config: Configuration = Depends()) -> Dict[str, Any]:
    """
    Detailed health check with configuration information.
    
    Returns:
        Detailed health status including configuration
    """
    basic_health = await health_check()
    
    detailed_health = {
        **basic_health,
        "configuration": {
            "model": config.model_name,
            "supabase_enabled": config.is_supabase_enabled(),
            "google_cloud_enabled": config.is_google_cloud_enabled(),
            "environment": "production" if not config.server_config.debug else "development"
        },
        "endpoints": {
            "websocket": "/ws/{session_id}",
            "api_docs": "/docs",
            "health": "/api/health"
        }
    }
    
    return detailed_health