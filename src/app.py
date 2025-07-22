"""
Refactored FastAPI application with proper dependency injection and modular architecture.
"""

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .core.configuration import config
from .core.container import container
from .core.logging import setup_logging, get_logger
from .websocket.connection_manager import ConnectionManager
from .websocket.websocket_handler import WebSocketHandler
from .agents.agent_factory import AgentFactory
from .routers import plots, authors, websocket, content, admin, models, health, sessions

# Setup logging
setup_logging()
logger = get_logger("app")

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Book Writer",
    description="A sophisticated multi-agent system for book writing powered by Google ADK and Gemini AI",
    version="2.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


async def startup_event():
    """Application startup configuration"""
    logger.info("Starting Multi-Agent Book Writer application")
    
    # Validate configuration
    config_errors = config.validate_configuration()
    if config_errors:
        logger.warning(f"Configuration issues: {', '.join(config_errors)}")
    
    # Validate all required services are available
    try:
        content_saving_service = container.get("content_saving_service")
        logger.info("ContentSavingService loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ContentSavingService: {e}")
        raise RuntimeError("Application startup failed - ContentSavingService unavailable") from e
    
    # Register additional services in container
    container.register_instance("connection_manager", ConnectionManager())
    container.register_instance("agent_factory", AgentFactory(config))
    
    # Register WebSocket handler with required ContentSavingService
    websocket_handler = WebSocketHandler(
        connection_manager=container.get("connection_manager"),
        agent_factory=container.get("agent_factory"),
        config=config,
        content_saving_service=content_saving_service
    )
    container.register_instance("websocket_handler", websocket_handler)
    
    logger.info("Application startup complete")


async def shutdown_event():
    """Application shutdown cleanup"""
    logger.info("Shutting down Multi-Agent Book Writer application")
    # Clean up resources here if needed
    

# Add event handlers
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


# Home page route
@app.get("/", response_class=HTMLResponse)
async def get_home():
    """Serve the main HTML page"""
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Template not found</h1>", status_code=404)


@app.get("/library", response_class=HTMLResponse)
async def library_page():
    """Library page to view all saved plots and authors"""
    try:
        with open('templates/library.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Library template not found</h1>", status_code=404)


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Content management interface for managing genres and target audiences"""
    try:
        with open('templates/admin.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Admin template not found</h1>", status_code=404)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agent_factory = container.get("agent_factory")
    available_agents = agent_factory.get_available_agents()
    
    return {
        "status": "healthy",
        "service": "multi_agent_book_writer",
        "version": "2.0.0",
        "config": {
            "model": config.model_name,
            "supabase_enabled": config.is_supabase_enabled(),
            "google_cloud_enabled": config.is_google_cloud_enabled()
        },
        "agents": available_agents
    }


# Include routers
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(plots.router, prefix="/api", tags=["plots"])
app.include_router(authors.router, prefix="/api", tags=["authors"])
app.include_router(content.router, prefix="/api", tags=["content"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(models.router, prefix="", tags=["models"])
app.include_router(health.router, tags=["health"])
app.include_router(sessions.router, tags=["sessions"])


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app"""
    return app


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=config.server_config.host,
        port=config.server_config.port,
        reload=config.server_config.debug,
        log_level="info"
    )