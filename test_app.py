"""
Test entry point for E2E testing.
This version runs the application with mocked dependencies to enable testing without full infrastructure.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Install mocks before any imports
os.environ['TESTING_MODE'] = 'true'
os.environ['ADK_SERVICE_MODE'] = 'development'

# Import and install mocks first
from tests.mocks.google_adk import install_mocks
install_mocks()

# Now import the application components
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from src.core.configuration import config
from src.core.logging import setup_logging, get_logger
from src.core.security import SecurityHeadersMiddleware
from src.test_startup import test_startup_event, create_test_health_response
from src.routers import plots, authors, websocket, content, models, health, sessions, parameters, openai_compat, metrics

def create_test_app():
    """Create the FastAPI app for testing with mocked dependencies."""
    
    # Set test environment variables
    os.environ.update({
        'DATABASE_MODE': 'sqlite',
        'SQLITE_DB_PATH': 'test_e2e.db',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'GOOGLE_CLOUD_LOCATION': 'us-central1',
        'GOOGLE_APPLICATION_CREDENTIALS': '/tmp/mock-credentials.json',
        'AI_MODEL': 'gemini-2.0-flash-exp',
        'SERVER_HOST': '0.0.0.0',
        'SERVER_PORT': '8000',
        'DEBUG': 'true',
        'LOG_LEVEL': 'INFO',
        'DB_POOL_MIN_CONNECTIONS': '1',
        'DB_POOL_MAX_CONNECTIONS': '3',
        'DB_POOL_ENABLE_METRICS': 'false'
    })
    
    # Setup logging
    setup_logging()
    logger = get_logger("test_app")
    
    # Create FastAPI app with test configuration
    app = FastAPI(
        title="Multi-Agent Book Writer (Test Mode)",
        description="E2E Testing version with mocked dependencies",
        version="2.0.0-test"
    )
    
    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add CORS middleware 
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Mount static files if they exist
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Test-specific startup and shutdown handlers
    app.add_event_handler("startup", test_startup_event)
    
    # Test-friendly health endpoint
    @app.get("/health")
    async def test_health_check():
        """Test-friendly health check endpoint"""
        return create_test_health_response()
    
    # Home page route with error handling
    @app.get("/", response_class=HTMLResponse)
    async def get_home():
        """Serve a simple test homepage"""
        return HTMLResponse(content="""
        <html>
            <head><title>AgentWriter Test Mode</title></head>
            <body>
                <h1>AgentWriter Test Server</h1>
                <p>Running in E2E test mode with mocked services.</p>
                <p><a href="/health">Health Check</a></p>
                <p><a href="/models">Available Models</a></p>
            </body>
        </html>
        """)
    
    # Include routers with error handling
    try:
        app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
        app.include_router(plots.router, prefix="/api", tags=["plots"])
        app.include_router(authors.router, prefix="/api", tags=["authors"])
        app.include_router(content.router, prefix="/api", tags=["content"])
        app.include_router(parameters.router, prefix="/api", tags=["parameters"])
        app.include_router(models.router, prefix="", tags=["models"])
        app.include_router(health.router, tags=["health"])
        app.include_router(sessions.router, tags=["sessions"])
        app.include_router(openai_compat.router, tags=["openai"])
        app.include_router(metrics.router, tags=["metrics"])
    except Exception as e:
        logger.warning(f"Some routers failed to load: {e}")
        # Continue with basic functionality
    
    return app

async def check_test_database():
    """Initialize test database if needed."""
    try:
        from src.database.database_factory import db_factory
        adapter = await db_factory.get_adapter()
        print(f"✅ Database adapter initialized: {type(adapter).__name__}")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main entry point for test application."""
    print("🧪 Starting AgentWriter Test Server for E2E Testing")
    print("=" * 60)
    
    # Check test database
    db_ready = asyncio.run(check_test_database())
    if not db_ready:
        print("❌ Cannot start: Database not ready")
        sys.exit(1)
    
    # Create test app
    app = create_test_app()
    
    print(f"🌐 Test Server: http://{config.server_config.host}:{config.server_config.port}")
    print(f"🤖 AI Model: {config.model_name}")
    print(f"💾 Database: SQLite (test_e2e.db)")
    print(f"🔧 Mode: Development/Testing")
    print("\n🚀 Starting server for E2E tests...")
    print("📝 Note: Using mocked Google ADK services for testing")
    print()
    
    # Run the server
    uvicorn.run(
        app,
        host=config.server_config.host,
        port=config.server_config.port,
        log_level="info",
        reload=False,  # Disable reload for E2E testing stability
        access_log=True
    )

if __name__ == "__main__":
    main()