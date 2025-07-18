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
from src.app import create_app
from src.core.configuration import config

# Create the application
app = create_app()

if __name__ == "__main__":
    print("🚀 Starting Multi-Agent Book Writer (Refactored)")
    print(f"📡 Server: http://{config.server_config.host}:{config.server_config.port}")
    print(f"🤖 AI Model: {config.model_name}")
    print(f"💾 Supabase: {'✅ Enabled' if config.is_supabase_enabled() else '❌ Disabled'}")
    print(f"☁️  Google Cloud: {'✅ Enabled' if config.is_google_cloud_enabled() else '❌ Disabled'}")
    
    uvicorn.run(
        app,
        host=config.server_config.host,
        port=config.server_config.port,
        reload=config.server_config.debug
    )