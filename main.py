from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
import logging
from typing import Dict, Set
from src.agents.agent_service import book_agent
from src.agents.multi_agent_system import multi_agent_system
from src.utils.validation import (
    validate_uuid, validate_alphanumeric, validate_text_content, 
    sanitize_string, ValidationError, GenreCreate, SubgenreCreate, 
    MicrogenreCreate, TropeCreate, ToneCreate, TargetAudienceCreate
)
from src.services.library_service import LibraryService

# Import Supabase service
try:
    from src.database.supabase_service import supabase_service
    SUPABASE_ENABLED = True
    # Initialize library service
    library_service = LibraryService(supabase_service)
except ImportError:
    SUPABASE_ENABLED = False
    library_service = None
    print("Supabase not available - data persistence endpoints disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Book Writer Agent", description="Agentic web app for book writing assistance")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def send_json_message(self, data: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()

@app.get("/")
async def get_home():
    """Serve the main HTML page"""
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat with the agent"""
    try:
        # Validate session_id
        session_id = validate_alphanumeric(session_id)
        client_id = f"client_{session_id}"
        await manager.connect(websocket, client_id)
    except ValidationError as e:
        await websocket.close(code=1008, reason=str(e))
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "message")
            content = sanitize_string(message_data.get("content", ""), max_length=50000)
            user_id = sanitize_string(message_data.get("user_id", "anonymous"), max_length=50)
            
            if message_type == "message":
                try:
                    # Process through multi-agent system with streaming
                    structured_responses = {}
                    
                    async for chunk_data in multi_agent_system.process_message_streaming(content, user_id, session_id):
                        if chunk_data.get("complete", False):
                            # Send completion signal with structured data
                            await manager.send_json_message({
                                "type": "stream_end",
                                "workflow_completed": chunk_data.get("success", False),
                                "orchestrator_routing": chunk_data.get("orchestrator_routing", {}),
                                "structured_responses": structured_responses
                            }, client_id)
                            
                            if not chunk_data.get("success", False):
                                await manager.send_json_message({
                                    "type": "error",
                                    "content": chunk_data.get("error", "Workflow failed")
                                }, client_id)
                                
                        elif "agent_header" in chunk_data:
                            # Skip orchestrator headers - UI handles workflow visualization
                            if chunk_data.get("agent_name", "") != "orchestrator":
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": f"\n[AI] {chunk_data['agent_header']}:\n"
                                }, client_id)
                                
                        elif "chunk" in chunk_data:
                            # Send streaming text chunk
                            await manager.send_json_message({
                                "type": "stream_chunk",
                                "content": chunk_data["chunk"]
                            }, client_id)
                            
                        elif "structured_data" in chunk_data:
                            # Send structured JSON response
                            agent_name = chunk_data.get("agent_name", "unknown")
                            structured_responses[agent_name] = chunk_data["structured_data"]
                            
                            await manager.send_json_message({
                                "type": "structured_response",
                                "agent": agent_name,
                                "json_data": chunk_data["structured_data"],
                                "raw_content": chunk_data.get("raw_content", "")
                            }, client_id)
                            
                        elif chunk_data.get("error"):
                            # Send error chunk
                            await manager.send_json_message({
                                "type": "stream_chunk",
                                "content": f"[ERROR] {chunk_data['error']}\n\n"
                            }, client_id)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await manager.send_json_message({
                        "type": "error",
                        "content": str(e)
                    }, client_id)
            
            elif message_type == "search":
                try:
                    # Handle search request
                    response_chunks = []
                    async for chunk in book_agent.search_and_respond(user_id, session_id, content):
                        response_chunks.append(chunk)
                        await manager.send_json_message({
                            "type": "stream_chunk",
                            "content": chunk
                        }, client_id)
                    
                    await manager.send_json_message({
                        "type": "stream_end",
                        "full_response": "".join(response_chunks)
                    }, client_id)
                    
                except Exception as e:
                    logger.error(f"Error processing search: {e}")
                    await manager.send_json_message({
                        "type": "error",
                        "content": str(e)
                    }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return book_agent.list_sessions()

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session"""
    return book_agent.get_session_info(session_id)

@app.get("/models")
async def list_models():
    """List all available AI models"""
    return {
        "current_model": book_agent.get_current_model(),
        "available_models": book_agent.get_available_models()
    }

@app.get("/models/{model_id}")
async def get_model_info(model_id: str):
    """Get detailed information about a specific model"""
    model_info = book_agent.get_model_info(model_id)
    if not model_info:
        return {"error": "Model not found"}
    return {
        "model_id": model_id,
        "info": model_info,
        "is_current": model_id == book_agent.get_current_model()
    }

@app.post("/models/{model_id}/switch")
async def switch_model(model_id: str):
    """Switch to a different AI model"""
    success = book_agent.switch_model(model_id)
    if success:
        return {
            "success": True,
            "message": f"Successfully switched to {model_id}",
            "current_model": book_agent.get_current_model()
        }
    else:
        return {
            "success": False,
            "message": f"Failed to switch to {model_id}",
            "current_model": book_agent.get_current_model()
        }

@app.get("/agents")
async def list_agents():
    """List all available agents in the multi-agent system"""
    return multi_agent_system.get_agent_info()

# Supabase data persistence endpoints
@app.get("/data/plots/{user_id}")
async def get_user_plots(user_id: str, limit: int = 50):
    """Get all plots for a user"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        plots = await supabase_service.get_user_plots(user_id, limit)
        return {"success": True, "plots": plots}
    except Exception as e:
        return {"error": str(e)}

@app.get("/data/authors/{user_id}")
async def get_user_authors(user_id: str, limit: int = 50):
    """Get all authors for a user"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        authors = await supabase_service.get_user_authors(user_id, limit)
        return {"success": True, "authors": authors}
    except Exception as e:
        return {"error": str(e)}

@app.get("/data/session/{session_id}")
async def get_session_data(session_id: str):
    """Get all data for a specific session"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        session_data = await supabase_service.get_session_data(session_id)
        return {"success": True, "data": session_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/data/plot/{plot_id}")
async def get_plot_with_author(plot_id: str):
    """Get plot with associated author"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        # Validate plot_id as UUID
        validated_plot_id = validate_uuid(plot_id)
        plot_data = await supabase_service.get_plot_with_author(validated_plot_id)
        return {"success": True, "data": plot_data}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/search/{user_id}")
async def search_plots(user_id: str, q: str, limit: int = 20):
    """Search plots by title or summary"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        # Validate inputs
        validated_user_id = sanitize_string(user_id, max_length=50)
        validated_query = sanitize_string(q, max_length=200)
        validated_limit = max(1, min(limit, 100))  # Limit between 1 and 100
        
        plots = await supabase_service.search_plots(validated_user_id, validated_query, validated_limit)
        return {"success": True, "plots": plots}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/analytics")
async def get_analytics(user_id: str = None):
    """Get analytics data"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        analytics = await supabase_service.get_analytics(user_id)
        return {"success": True, "analytics": analytics}
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin")
async def admin_page():
    """Content management interface for managing genres and target audiences"""
    import os
    file_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/library")
async def library_page():
    """Library page to view all saved plots and authors"""
    with open('templates/library.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


# Enhanced Library API Endpoints
@app.get("/api/library/{user_id}")
async def get_user_library(user_id: str, page: int = 1, limit: int = 20):
    """Get paginated library data for a specific user"""
    if not SUPABASE_ENABLED or not library_service:
        return {"success": False, "error": "Library service not available"}
    
    try:
        # Validate inputs
        validated_user_id = validate_alphanumeric(user_id, 50)
        validated_page = max(1, min(page, 100))  # Limit to reasonable range
        validated_limit = max(1, min(limit, 50))  # Limit to reasonable range
        
        result = await library_service.get_user_library_data(validated_user_id, validated_page, validated_limit)
        return result
        
    except ValidationError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error in get_user_library: {e}")
        return {"success": False, "error": "Internal server error"}


@app.get("/api/library/{user_id}/search")
async def search_user_library(user_id: str, q: str, content_type: str = "both", limit: int = 20):
    """Search user's library content"""
    if not SUPABASE_ENABLED or not library_service:
        return {"success": False, "error": "Library service not available"}
    
    try:
        # Validate inputs
        validated_user_id = validate_alphanumeric(user_id, 50)
        validated_query = sanitize_string(q, 100)
        validated_content_type = content_type if content_type in ["plots", "authors", "both"] else "both"
        validated_limit = max(1, min(limit, 50))
        
        result = await library_service.search_user_content(validated_user_id, validated_query, validated_content_type, validated_limit)
        return result
        
    except ValidationError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error in search_user_library: {e}")
        return {"success": False, "error": "Internal server error"}


@app.get("/api/library/content/{content_id}")
async def get_content_details(content_id: str, content_type: str):
    """Get detailed information about a specific plot or author"""
    if not SUPABASE_ENABLED or not library_service:
        return {"success": False, "error": "Library service not available"}
    
    try:
        # Validate inputs
        validated_content_id = validate_uuid(content_id)
        validated_content_type = content_type if content_type in ["plot", "author"] else None
        
        if not validated_content_type:
            return {"success": False, "error": "Invalid content type. Must be 'plot' or 'author'"}
        
        result = await library_service.get_content_details(validated_content_id, validated_content_type)
        return result
        
    except ValidationError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error in get_content_details: {e}")
        return {"success": False, "error": "Internal server error"}


@app.get("/api/library/{user_id}/stats")
async def get_user_library_stats(user_id: str):
    """Get user's library statistics"""
    if not SUPABASE_ENABLED or not library_service:
        return {"success": False, "error": "Library service not available"}
    
    try:
        # Validate inputs
        validated_user_id = validate_alphanumeric(user_id, 50)
        
        result = await library_service.get_user_statistics(validated_user_id)
        return result
        
    except ValidationError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Error in get_user_library_stats: {e}")
        return {"success": False, "error": "Internal server error"}


@app.get("/api/plots")
async def get_all_plots():
    """Get all plots with metadata"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        # Note: get_all_plots_with_metadata is synchronous
        plots = supabase_service.get_all_plots_with_metadata()
        return {"success": True, "plots": plots}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/authors")
async def get_all_authors():
    """Get all authors"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        authors = await supabase_service.get_all_authors()
        return {"success": True, "authors": authors}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/content-selection")
async def get_content_for_selection():
    """Get simplified content lists for selection in improvement workflow"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        # Get plots with just ID, title, and creation date
        plots_response = supabase_service.client.table("plots").select("id, title, created_at").order("created_at", desc=True).limit(100).execute()
        plots = [{"id": plot["id"], "title": plot["title"], "type": "plot", "created_at": plot["created_at"]} for plot in plots_response.data]
        
        # Get authors with just ID, name, and creation date
        authors_response = supabase_service.client.table("authors").select("id, author_name, created_at").order("created_at", desc=True).limit(100).execute()
        authors = [{"id": author["id"], "title": author["author_name"], "type": "author", "created_at": author["created_at"]} for author in authors_response.data]
        
        # Combine and sort by creation date
        all_content = plots + authors
        all_content.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"success": True, "content": all_content}
    except Exception as e:
        return {"error": str(e)}

# Genre management endpoints
@app.get("/api/genres")
async def get_all_genres():
    """Get complete hierarchy: genres, subgenres, microgenres, tropes, and tones"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        genres = supabase_service.client.table("genres").select("*").order("name").execute()
        subgenres = supabase_service.client.table("subgenres").select("*").order("name").execute()
        microgenres = supabase_service.client.table("microgenres").select("*").order("name").execute()
        tropes = supabase_service.client.table("tropes").select("*").order("name").execute()
        tones = supabase_service.client.table("tones").select("*").order("name").execute()
        
        return {
            "success": True,
            "genres": genres.data,
            "subgenres": subgenres.data,
            "microgenres": microgenres.data,
            "tropes": tropes.data,
            "tones": tones.data
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/genres")
async def create_genre(data: GenreCreate):
    """Create a new genre"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        response = supabase_service.client.table("genres").insert({
            "name": data.name,
            "description": data.description or ""
        }).execute()
        
        return {"success": True, "genre": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/subgenres")
async def create_subgenre(data: SubgenreCreate):
    """Create a new subgenre"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        response = supabase_service.client.table("subgenres").insert({
            "genre_id": data.genre_id,
            "name": data.name,
            "description": data.description or ""
        }).execute()
        
        return {"success": True, "subgenre": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/microgenres")
async def create_microgenre(data: dict):
    """Create a new microgenre"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("microgenres").insert({
            "subgenre_id": data["subgenre_id"],
            "name": data["name"],
            "description": data.get("description", "")
        }).execute()
        
        return {"success": True, "microgenre": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/tropes")
async def get_all_tropes():
    """Get all tropes"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        tropes = supabase_service.client.table("tropes").select("*").order("name").execute()
        return {"success": True, "tropes": tropes.data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/tropes")
async def create_trope(data: dict):
    """Create a new trope"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        # Check if the new schema is available (after migration)
        insert_data = {
            "name": data["name"],
            "description": data.get("description", "")
        }
        
        # If microgenre_id is provided, we're using the new schema
        if "microgenre_id" in data:
            insert_data["microgenre_id"] = data["microgenre_id"]
        else:
            # Otherwise use the old schema with category
            insert_data["category"] = data.get("category", "Plot")
            
        response = supabase_service.client.table("tropes").insert(insert_data).execute()
        
        return {"success": True, "trope": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/tones")
async def get_all_tones():
    """Get all tones"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        tones = supabase_service.client.table("tones").select("*").order("name").execute()
        return {"success": True, "tones": tones.data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/tones")
async def create_tone(data: dict):
    """Create a new tone"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        insert_data = {
            "name": data["name"],
            "description": data.get("description", "")
        }
        
        # If trope_id is provided, we're using the new schema
        if "trope_id" in data:
            insert_data["trope_id"] = data["trope_id"]
            
        response = supabase_service.client.table("tones").insert(insert_data).execute()
        
        return {"success": True, "tone": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/target-audiences")
async def get_all_target_audiences():
    """Get all target audiences"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        audiences = supabase_service.client.table("target_audiences").select("*").order("age_group").execute()
        return {"success": True, "audiences": audiences.data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/target-audiences")
async def create_target_audience(data: TargetAudienceCreate):
    """Create a new target audience"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        response = supabase_service.client.table("target_audiences").insert({
            "age_group": data.age_group,
            "gender": data.gender,
            "sexual_orientation": data.sexual_orientation
        }).execute()
        
        return {"success": True, "audience": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/target-audiences/{audience_id}")
async def delete_target_audience(audience_id: str):
    """Delete a target audience"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("target_audiences").delete().eq("id", audience_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

# Individual GET endpoints for hierarchical data

@app.get("/api/subgenres")
async def get_subgenres():
    """Get all subgenres"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("subgenres").select("*").order("name").execute()
        return {"success": True, "subgenres": response.data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/microgenres")
async def get_microgenres():
    """Get all microgenres"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("microgenres").select("*").order("name").execute()
        return {"success": True, "microgenres": response.data}
    except Exception as e:
        return {"error": str(e)}

# UPDATE and DELETE endpoints for hierarchical management

@app.put("/api/genres/{genre_id}")
async def update_genre(genre_id: str, data: dict):
    """Update a genre"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("genres").update({
            "name": data["name"],
            "description": data.get("description", "")
        }).eq("id", genre_id).execute()
        
        return {"success": True, "genre": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/genres/{genre_id}")
async def delete_genre(genre_id: str):
    """Delete a genre and all its children"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("genres").delete().eq("id", genre_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/subgenres/{subgenre_id}")
async def update_subgenre(subgenre_id: str, data: dict):
    """Update a subgenre"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("subgenres").update({
            "name": data["name"],
            "description": data.get("description", "")
        }).eq("id", subgenre_id).execute()
        
        return {"success": True, "subgenre": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/subgenres/{subgenre_id}")
async def delete_subgenre(subgenre_id: str):
    """Delete a subgenre and all its children"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("subgenres").delete().eq("id", subgenre_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/microgenres/{microgenre_id}")
async def update_microgenre(microgenre_id: str, data: dict):
    """Update a microgenre"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("microgenres").update({
            "name": data["name"],
            "description": data.get("description", "")
        }).eq("id", microgenre_id).execute()
        
        return {"success": True, "microgenre": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/microgenres/{microgenre_id}")
async def delete_microgenre(microgenre_id: str):
    """Delete a microgenre and all its children"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("microgenres").delete().eq("id", microgenre_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/tropes/{trope_id}")
async def update_trope(trope_id: str, data: dict):
    """Update a trope"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("tropes").update({
            "name": data["name"],
            "description": data.get("description", "")
        }).eq("id", trope_id).execute()
        
        return {"success": True, "trope": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/tropes/{trope_id}")
async def delete_trope(trope_id: str):
    """Delete a trope and all its children"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("tropes").delete().eq("id", trope_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.put("/api/tones/{tone_id}")
async def update_tone(tone_id: str, data: dict):
    """Update a tone"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("tones").update({
            "name": data["name"],
            "description": data.get("description", "")
        }).eq("id", tone_id).execute()
        
        return {"success": True, "tone": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/tones/{tone_id}")
async def delete_tone(tone_id: str):
    """Delete a tone"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("tones").delete().eq("id", tone_id).execute()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "multi_agent_book_writer",
        "current_model": book_agent.get_current_model(),
        "agents": list(multi_agent_system.agents.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)