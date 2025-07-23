"""
Refactored main entry point using the new modular architecture.

This demonstrates the improved structure with:
- Proper dependency injection
- Modular agent architecture
- Separated concerns
- Repository pattern
- Controller-based API routes
"""

import uvicorn
import asyncio
import os
from src.app import create_app
from src.core.configuration import config
from src.database.database_factory import db_factory

# Create the application
app = create_app()

async def check_database_mode():
    """Check which database mode we're using"""
    try:
        database_mode = os.getenv("DATABASE_MODE", "supabase").lower()
        db_path = os.getenv("SQLITE_DB_PATH", "development.db")
        
        await db_factory.get_adapter()
        
        if database_mode == "sqlite":
            return f"SQLite (Development Mode - {db_path})"
        elif db_factory.is_offline_mode():
            return f"SQLite (Fallback Mode - {db_path})"
        else:
            return "Supabase (Production)"
    except:
        return "Error - Using SQLite"

if __name__ == "__main__":
    print("Starting Multi-Agent Book Writer (Refactored)")
    print(f"Server: http://{config.server_config.host}:{config.server_config.port}")
    print(f"AI Model: {config.model_name}")
    
    # Check database mode
    database_mode = asyncio.run(check_database_mode())
    print(f"Database: {database_mode}")
    print(f"Google Cloud: {'Enabled' if config.is_google_cloud_enabled() else 'Disabled'}")
    
    if "Development Mode" in database_mode:
        print("\nINFO: Running in DEVELOPMENT MODE with SQLite database")
        print("      All data will be stored locally for development\n")
    elif "Fallback Mode" in database_mode:
        print("\nWARNING: Running in FALLBACK MODE - Supabase unavailable")
        print("         Data will be stored locally and synced when connection is restored\n")
    
    uvicorn.run(
        app,
        host=config.server_config.host,
        port=config.server_config.port,
        reload=config.server_config.debug
    )