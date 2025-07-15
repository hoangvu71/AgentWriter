from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
import logging
from typing import Dict, Set
from agent_service import book_agent
from multi_agent_system import multi_agent_system

# Import Supabase service
try:
    from supabase_service import supabase_service
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
    print("Supabase not available - data persistence endpoints disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Book Writer Agent", description="Agentic web app for book writing assistance")

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
    return HTMLResponse(content=r"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Writer Agent</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .chat-container {
                height: 400px;
                border: 1px solid #ddd;
                border-radius: 5px;
                overflow-y: auto;
                padding: 10px;
                margin-bottom: 20px;
                background-color: #fafafa;
            }
            .message {
                margin-bottom: 10px;
                padding: 8px;
                border-radius: 5px;
            }
            .user-message {
                background-color: #007bff;
                color: white;
                margin-left: 20%;
            }
            .agent-message {
                background-color: #e9ecef;
                color: #333;
                margin-right: 20%;
            }
            .input-container {
                display: flex;
                gap: 10px;
            }
            .input-container input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .input-container button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .input-container button:hover {
                background-color: #0056b3;
            }
            .status {
                margin-top: 10px;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
            }
            .status.connected {
                background-color: #d4edda;
                color: #155724;
            }
            .status.disconnected {
                background-color: #f8d7da;
                color: #721c24;
            }
            .typing {
                font-style: italic;
                color: #666;
            }
            .model-selector {
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
            .model-selector label {
                font-weight: bold;
                margin-right: 10px;
            }
            .model-selector select {
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #ccc;
                margin-right: 10px;
            }
            .model-selector span {
                font-size: 12px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <h1>📚 Multi-Agent Book Writer System</h1>
                    <p>Advanced AI system with orchestrator, plot generator, and author generator agents.</p>
                </div>
                <a href="/library" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📖 View Library</a>
            </div>
            
            <div class="model-selector">
                <label for="modelSelect">AI Model:</label>
                <select id="modelSelect" onchange="switchModel()">
                    <option value="">Loading models...</option>
                </select>
                <span id="modelInfo"></span>
            </div>
            
            <div class="chat-container" id="chat"></div>
            
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Try: 'Create a fantasy novel, LitRPG, Zombie Apocalypse, survive and family, dark/humour/realistic, Male/Heterosexual/Young Adults. Create author too.'" />
                <button onclick="sendMessage()">Send</button>
            </div>
            
            <div class="status disconnected" id="status">Disconnected</div>
        </div>

        <script>
            let ws = null;
            let sessionId = null;
            let userId = "user_" + Math.random().toString(36).substr(2, 9);
            
            function connect() {
                sessionId = "session_" + Math.random().toString(36).substr(2, 9);
                ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').className = 'status connected';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').className = 'status disconnected';
                };
                
                ws.onerror = function(event) {
                    console.error('WebSocket error:', event);
                };
            }
            
            function handleMessage(data) {
                const chatContainer = document.getElementById('chat');
                
                if (data.type === 'stream_chunk') {
                    let currentMessage = document.getElementById('current-agent-message');
                    if (!currentMessage) {
                        currentMessage = document.createElement('div');
                        currentMessage.className = 'message agent-message';
                        currentMessage.id = 'current-agent-message';
                        currentMessage.style.whiteSpace = 'pre-wrap';
                        chatContainer.appendChild(currentMessage);
                    }
                    currentMessage.textContent += data.content;
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else if (data.type === 'structured_response') {
                    // Handle structured JSON responses
                    const structuredMessage = document.createElement('div');
                    structuredMessage.className = 'message agent-message structured-response';
                    structuredMessage.style.border = '2px solid #007bff';
                    structuredMessage.style.borderRadius = '8px';
                    structuredMessage.style.padding = '15px';
                    structuredMessage.style.backgroundColor = '#f8f9fa';
                    
                    // Add agent name header
                    const agentHeader = document.createElement('h4');
                    agentHeader.textContent = `📊 ${data.agent.replace('_', ' ').toUpperCase()} - Structured Response`;
                    agentHeader.style.color = '#007bff';
                    agentHeader.style.marginBottom = '10px';
                    structuredMessage.appendChild(agentHeader);
                    
                    // Add JSON data as formatted text
                    const jsonContent = document.createElement('pre');
                    jsonContent.style.backgroundColor = '#ffffff';
                    jsonContent.style.border = '1px solid #ddd';
                    jsonContent.style.borderRadius = '4px';
                    jsonContent.style.padding = '10px';
                    jsonContent.style.overflow = 'auto';
                    jsonContent.style.fontSize = '12px';
                    jsonContent.textContent = JSON.stringify(data.json_data, null, 2);
                    structuredMessage.appendChild(jsonContent);
                    
                    chatContainer.appendChild(structuredMessage);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else if (data.type === 'stream_end') {
                    const currentMessage = document.getElementById('current-agent-message');
                    if (currentMessage) {
                        currentMessage.id = '';
                        // Format the final message
                        currentMessage.innerHTML = formatMessage(currentMessage.textContent);
                    }
                    
                    // Log structured responses for debugging
                    if (data.structured_responses) {
                        console.log('Structured responses received:', data.structured_responses);
                    }
                } else if (data.type === 'error') {
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'message agent-message';
                    errorMessage.textContent = 'Error: ' + data.content;
                    errorMessage.style.backgroundColor = '#f8d7da';
                    errorMessage.style.color = '#721c24';
                    chatContainer.appendChild(errorMessage);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            
            function formatMessage(text) {
                // Convert numbered lists to HTML
                text = text.replace(/^(\d+\.\s\*\*)(.+?)(\*\*)/gm, '<strong>$1$2</strong>');
                text = text.replace(/^(\d+\.\s)(.+?)$/gm, '<strong>$1</strong>$2');
                
                // Convert bold text
                text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                
                // Convert line breaks
                text = text.replace(/\n/g, '<br>');
                
                return text;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    // Display user message
                    const chatContainer = document.getElementById('chat');
                    const userMessage = document.createElement('div');
                    userMessage.className = 'message user-message';
                    userMessage.textContent = message;
                    chatContainer.appendChild(userMessage);
                    
                    // Send to server
                    ws.send(JSON.stringify({
                        type: 'message',
                        content: message,
                        user_id: userId
                    }));
                    
                    input.value = '';
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            
            // Enter key support
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // Model management functions
            function loadModels() {
                fetch('/models')
                    .then(response => response.json())
                    .then(data => {
                        const select = document.getElementById('modelSelect');
                        select.innerHTML = '';
                        
                        Object.entries(data.available_models).forEach(([modelId, info]) => {
                            const option = document.createElement('option');
                            option.value = modelId;
                            option.textContent = info.name;
                            if (modelId === data.current_model) {
                                option.selected = true;
                            }
                            select.appendChild(option);
                        });
                        
                        updateModelInfo(data.current_model, data.available_models);
                    })
                    .catch(error => console.error('Error loading models:', error));
            }
            
            function updateModelInfo(modelId, models) {
                const info = models[modelId];
                if (info) {
                    document.getElementById('modelInfo').textContent = 
                        `${info.description} - Best for: ${info.best_for}`;
                }
            }
            
            function switchModel() {
                const select = document.getElementById('modelSelect');
                const modelId = select.value;
                
                fetch(`/models/${modelId}/switch`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('Model switched successfully');
                            loadModels(); // Refresh model info
                        } else {
                            console.error('Failed to switch model:', data.message);
                        }
                    })
                    .catch(error => console.error('Error switching model:', error));
            }
            
            // Connect on page load
            window.onload = function() {
                connect();
                loadModels();
            };
        </script>
    </body>
    </html>
    """)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat with the agent"""
    client_id = f"client_{session_id}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "message")
            content = message_data.get("content", "")
            user_id = message_data.get("user_id", "anonymous")
            
            if message_type == "message":
                try:
                    # Process through multi-agent system
                    result = await multi_agent_system.process_request(content, session_id, user_id)
                    
                    if result["success"]:
                        # Stream responses from all agents
                        for response in result["responses"]:
                            if response.success:
                                # Send agent header
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": f"\n🤖 {response.agent_name.replace('_', ' ').title()}:\n"
                                }, client_id)
                                
                                # Send structured JSON response if available
                                if response.parsed_json:
                                    # Format JSON nicely for display
                                    formatted_json = json.dumps(response.parsed_json, indent=2)
                                    await manager.send_json_message({
                                        "type": "structured_response",
                                        "agent": response.agent_name,
                                        "json_data": response.parsed_json,
                                        "raw_content": response.content
                                    }, client_id)
                                    
                                    # Also send formatted JSON as text for display
                                    await manager.send_json_message({
                                        "type": "stream_chunk",
                                        "content": f"```json\n{formatted_json}\n```\n\n"
                                    }, client_id)
                                else:
                                    # Send raw response if JSON parsing failed
                                    await manager.send_json_message({
                                        "type": "stream_chunk",
                                        "content": f"⚠️ JSON parsing failed. Raw response:\n{response.content}\n\n"
                                    }, client_id)
                            else:
                                # Send error for failed agent
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": f"⚠️ {response.agent_name} failed: {response.error}\n\n"
                                }, client_id)
                        
                        # Send end signal with structured data
                        await manager.send_json_message({
                            "type": "stream_end",
                            "workflow_completed": result["workflow_completed"],
                            "orchestrator_routing": result.get("orchestrator_routing", {}),
                            "structured_responses": {
                                response.agent_name: response.parsed_json 
                                for response in result["responses"] 
                                if response.parsed_json
                            }
                        }, client_id)
                    else:
                        # Send error message
                        await manager.send_json_message({
                            "type": "error",
                            "content": result["error"]
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
        return {"error": "Supabase not configured"}
    
    try:
        plot_data = await supabase_service.get_plot_with_author(plot_id)
        return {"success": True, "data": plot_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/data/search/{user_id}")
async def search_plots(user_id: str, q: str, limit: int = 20):
    """Search plots by title or summary"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        plots = await supabase_service.search_plots(user_id, q, limit)
        return {"success": True, "plots": plots}
    except Exception as e:
        return {"error": str(e)}

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

@app.get("/library")
async def library_page():
    """Library page to view all plots and authors"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Library - Multi-Agent Book Writer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .nav-buttons {
                display: flex;
                gap: 10px;
            }
            .nav-button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                border: none;
                cursor: pointer;
            }
            .nav-button:hover {
                background-color: #0056b3;
            }
            .nav-button.active {
                background-color: #28a745;
            }
            .content {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .filters {
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
            }
            .filter-group {
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            .filter-group label {
                font-weight: bold;
                font-size: 12px;
                color: #666;
            }
            .filter-group select, .filter-group input {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                min-width: 120px;
            }
            .search-box {
                flex: 1;
                min-width: 200px;
            }
            .items-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .item-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                cursor: pointer;
            }
            .item-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            }
            
            /* Modal styles */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                animation: fadeIn 0.3s;
            }
            .modal-content {
                background-color: white;
                margin: 50px auto;
                padding: 0;
                border-radius: 10px;
                width: 90%;
                max-width: 800px;
                max-height: 80vh;
                overflow-y: auto;
                animation: slideIn 0.3s;
            }
            .modal-header {
                background-color: #007bff;
                color: white;
                padding: 20px;
                border-radius: 10px 10px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .modal-header h2 {
                margin: 0;
                font-size: 24px;
            }
            .close {
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                color: white;
                background: none;
                border: none;
            }
            .close:hover {
                opacity: 0.7;
            }
            .modal-body {
                padding: 20px;
                line-height: 1.6;
            }
            .modal-section {
                margin-bottom: 20px;
            }
            .modal-section h3 {
                margin: 0 0 10px 0;
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 5px;
            }
            .modal-meta-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 15px 0;
            }
            .modal-meta-item {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .modal-meta-label {
                font-weight: bold;
                color: #666;
                font-size: 12px;
                text-transform: uppercase;
            }
            .modal-meta-value {
                margin-top: 5px;
                color: #333;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideIn {
                from { transform: translateY(-50px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .item-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 10px;
            }
            .item-title {
                font-weight: bold;
                font-size: 16px;
                color: #333;
                margin: 0;
            }
            .item-date {
                font-size: 12px;
                color: #666;
            }
            .item-summary {
                color: #555;
                line-height: 1.4;
                margin: 10px 0;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .item-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin: 10px 0;
            }
            .meta-tag {
                background-color: #e9ecef;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 11px;
                color: #495057;
            }
            .meta-tag.genre { background-color: #d4edda; color: #155724; }
            .meta-tag.audience { background-color: #cce5ff; color: #004085; }
            .meta-tag.tone { background-color: #fff3cd; color: #856404; }
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            .empty {
                text-align: center;
                padding: 40px;
                color: #999;
            }
            .stats {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }
            .stat-card {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
                flex: 1;
            }
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }
            .stat-label {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Book Library</h1>
            <div class="nav-buttons">
                <a href="/" class="nav-button">← Back to Writer</a>
                <button class="nav-button active" id="plotsBtn" onclick="showPlots()">Plots</button>
                <button class="nav-button" id="authorsBtn" onclick="showAuthors()">Authors</button>
            </div>
        </div>

        <div class="content">
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="plotCount">-</div>
                    <div class="stat-label">Total Plots</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="authorCount">-</div>
                    <div class="stat-label">Total Authors</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="genreCount">-</div>
                    <div class="stat-label">Genres</div>
                </div>
            </div>

            <div class="filters">
                <div class="filter-group">
                    <label>Search</label>
                    <input type="text" id="searchBox" placeholder="Search titles, summaries..." class="search-box" onkeyup="filterItems()">
                </div>
                <div class="filter-group" id="genreFilter" style="display: none;">
                    <label>Genre</label>
                    <select id="genreSelect" onchange="filterItems()">
                        <option value="">All Genres</option>
                    </select>
                </div>
                <div class="filter-group" id="audienceFilter" style="display: none;">
                    <label>Audience</label>
                    <select id="audienceSelect" onchange="filterItems()">
                        <option value="">All Audiences</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Sort By</label>
                    <select id="sortSelect" onchange="sortItems()">
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="title">Title A-Z</option>
                    </select>
                </div>
            </div>

            <div id="loadingMessage" class="loading">Loading...</div>
            <div id="emptyMessage" class="empty" style="display: none;">No items found</div>
            <div id="itemsGrid" class="items-grid"></div>
        </div>

        <!-- Modal for detailed view -->
        <div id="detailModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Item Details</h2>
                    <button class="close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body" id="modalBody">
                    <!-- Content will be populated by JavaScript -->
                </div>
            </div>
        </div>

        <script>
            let currentView = 'plots';
            let allPlots = [];
            let allAuthors = [];
            let filteredItems = [];

            async function loadData() {
                try {
                    // Load plots
                    const plotsResponse = await fetch('/api/plots');
                    if (plotsResponse.ok) {
                        const plotsData = await plotsResponse.json();
                        allPlots = plotsData.plots || [];
                    }

                    // Load authors
                    const authorsResponse = await fetch('/api/authors');
                    if (authorsResponse.ok) {
                        const authorsData = await authorsResponse.json();
                        allAuthors = authorsData.authors || [];
                    }

                    updateStats();
                    updateFilters();
                    showPlots();

                } catch (error) {
                    console.error('Error loading data:', error);
                    document.getElementById('loadingMessage').textContent = 'Error loading data';
                }
            }

            function updateStats() {
                document.getElementById('plotCount').textContent = allPlots.length;
                document.getElementById('authorCount').textContent = allAuthors.length;
                
                const genres = new Set();
                allPlots.forEach(plot => {
                    if (plot.genre_name) genres.add(plot.genre_name);
                });
                document.getElementById('genreCount').textContent = genres.size;
            }

            function updateFilters() {
                // Update genre filter
                const genreSelect = document.getElementById('genreSelect');
                const genres = new Set();
                allPlots.forEach(plot => {
                    if (plot.genre_name) genres.add(plot.genre_name);
                });
                
                genreSelect.innerHTML = '<option value="">All Genres</option>';
                Array.from(genres).sort().forEach(genre => {
                    genreSelect.innerHTML += `<option value="${genre}">${genre}</option>`;
                });

                // Update audience filter
                const audienceSelect = document.getElementById('audienceSelect');
                const audiences = new Set();
                allPlots.forEach(plot => {
                    if (plot.target_audience_description) audiences.add(plot.target_audience_description);
                });
                
                audienceSelect.innerHTML = '<option value="">All Audiences</option>';
                Array.from(audiences).sort().forEach(audience => {
                    audienceSelect.innerHTML += `<option value="${audience}">${audience}</option>`;
                });
            }

            function showPlots() {
                currentView = 'plots';
                document.getElementById('plotsBtn').classList.add('active');
                document.getElementById('authorsBtn').classList.remove('active');
                document.getElementById('genreFilter').style.display = 'block';
                document.getElementById('audienceFilter').style.display = 'block';
                
                filteredItems = [...allPlots];
                filterItems();
            }

            function showAuthors() {
                currentView = 'authors';
                document.getElementById('authorsBtn').classList.add('active');
                document.getElementById('plotsBtn').classList.remove('active');
                document.getElementById('genreFilter').style.display = 'none';
                document.getElementById('audienceFilter').style.display = 'none';
                
                filteredItems = [...allAuthors];
                filterItems();
            }

            function filterItems() {
                const searchTerm = document.getElementById('searchBox').value.toLowerCase();
                const selectedGenre = document.getElementById('genreSelect').value;
                const selectedAudience = document.getElementById('audienceSelect').value;

                if (currentView === 'plots') {
                    filteredItems = allPlots.filter(plot => {
                        const matchesSearch = !searchTerm || 
                            plot.title.toLowerCase().includes(searchTerm) ||
                            plot.plot_summary.toLowerCase().includes(searchTerm);
                        
                        const matchesGenre = !selectedGenre || plot.genre_name === selectedGenre;
                        const matchesAudience = !selectedAudience || plot.target_audience_description === selectedAudience;
                        
                        return matchesSearch && matchesGenre && matchesAudience;
                    });
                } else {
                    filteredItems = allAuthors.filter(author => {
                        const matchesSearch = !searchTerm || 
                            author.author_name.toLowerCase().includes(searchTerm) ||
                            author.biography.toLowerCase().includes(searchTerm);
                        
                        return matchesSearch;
                    });
                }

                sortItems();
            }

            function sortItems() {
                const sortBy = document.getElementById('sortSelect').value;
                
                switch (sortBy) {
                    case 'newest':
                        filteredItems.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                        break;
                    case 'oldest':
                        filteredItems.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                        break;
                    case 'title':
                        filteredItems.sort((a, b) => {
                            const titleA = currentView === 'plots' ? a.title : a.author_name;
                            const titleB = currentView === 'plots' ? b.title : b.author_name;
                            return titleA.localeCompare(titleB);
                        });
                        break;
                }

                renderItems();
            }

            function renderItems() {
                const grid = document.getElementById('itemsGrid');
                const loading = document.getElementById('loadingMessage');
                const empty = document.getElementById('emptyMessage');

                loading.style.display = 'none';
                
                if (filteredItems.length === 0) {
                    empty.style.display = 'block';
                    grid.innerHTML = '';
                    return;
                }

                empty.style.display = 'none';
                
                if (currentView === 'plots') {
                    grid.innerHTML = filteredItems.map((plot, index) => `
                        <div class="item-card" onclick="showPlotModal(${index})">
                            <div class="item-header">
                                <h3 class="item-title">${plot.title}</h3>
                                <div class="item-date">${new Date(plot.created_at).toLocaleDateString()}</div>
                            </div>
                            <div class="item-summary">${plot.plot_summary}</div>
                            <div class="item-meta">
                                ${plot.genre_name ? `<span class="meta-tag genre">${plot.genre_name}</span>` : ''}
                                ${plot.subgenre_name ? `<span class="meta-tag genre">${plot.subgenre_name}</span>` : ''}
                                ${plot.microgenre_name ? `<span class="meta-tag genre">${plot.microgenre_name}</span>` : ''}
                                ${plot.trope_name ? `<span class="meta-tag">${plot.trope_name}</span>` : ''}
                                ${plot.tone_name ? `<span class="meta-tag tone">${plot.tone_name}</span>` : ''}
                                ${plot.target_audience_age_group ? `<span class="meta-tag audience">${plot.target_audience_age_group}</span>` : ''}
                            </div>
                        </div>
                    `).join('');
                } else {
                    grid.innerHTML = filteredItems.map((author, index) => `
                        <div class="item-card" onclick="showAuthorModal(${index})">
                            <div class="item-header">
                                <h3 class="item-title">${author.author_name}</h3>
                                <div class="item-date">${new Date(author.created_at).toLocaleDateString()}</div>
                            </div>
                            ${author.pen_name ? `<div style="font-style: italic; color: #666; margin-bottom: 10px;">Pen Name: ${author.pen_name}</div>` : ''}
                            <div class="item-summary">${author.biography}</div>
                            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                                <strong>Writing Style:</strong> ${author.writing_style}
                            </div>
                        </div>
                    `).join('');
                }
            }

            // Modal functions
            function showPlotModal(index) {
                const plot = filteredItems[index];
                const modal = document.getElementById('detailModal');
                const title = document.getElementById('modalTitle');
                const body = document.getElementById('modalBody');
                
                title.textContent = plot.title;
                
                body.innerHTML = `
                    <div class="modal-section">
                        <h3>Plot Summary</h3>
                        <p>${plot.plot_summary}</p>
                    </div>
                    
                    <div class="modal-section">
                        <h3>Metadata</h3>
                        <div class="modal-meta-grid">
                            ${plot.genre_name ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Genre</div>
                                    <div class="modal-meta-value">${plot.genre_name}</div>
                                </div>
                            ` : ''}
                            ${plot.subgenre_name ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Subgenre</div>
                                    <div class="modal-meta-value">${plot.subgenre_name}</div>
                                </div>
                            ` : ''}
                            ${plot.microgenre_name ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Microgenre</div>
                                    <div class="modal-meta-value">${plot.microgenre_name}</div>
                                </div>
                            ` : ''}
                            ${plot.trope_name ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Trope</div>
                                    <div class="modal-meta-value">${plot.trope_name}</div>
                                </div>
                            ` : ''}
                            ${plot.tone_name ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Tone</div>
                                    <div class="modal-meta-value">${plot.tone_name}</div>
                                </div>
                            ` : ''}
                            ${plot.target_audience_age_group ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Target Audience</div>
                                    <div class="modal-meta-value">${plot.target_audience_age_group}</div>
                                </div>
                            ` : ''}
                            ${plot.target_audience_description ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Audience Description</div>
                                    <div class="modal-meta-value">${plot.target_audience_description}</div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="modal-section">
                        <h3>Details</h3>
                        <div class="modal-meta-grid">
                            <div class="modal-meta-item">
                                <div class="modal-meta-label">Created</div>
                                <div class="modal-meta-value">${new Date(plot.created_at).toLocaleString()}</div>
                            </div>
                            <div class="modal-meta-item">
                                <div class="modal-meta-label">Plot ID</div>
                                <div class="modal-meta-value">${plot.id}</div>
                            </div>
                        </div>
                    </div>
                `;
                
                modal.style.display = 'block';
            }
            
            function showAuthorModal(index) {
                const author = filteredItems[index];
                const modal = document.getElementById('detailModal');
                const title = document.getElementById('modalTitle');
                const body = document.getElementById('modalBody');
                
                title.textContent = author.author_name;
                
                body.innerHTML = `
                    <div class="modal-section">
                        <h3>Author Information</h3>
                        <div class="modal-meta-grid">
                            <div class="modal-meta-item">
                                <div class="modal-meta-label">Full Name</div>
                                <div class="modal-meta-value">${author.author_name}</div>
                            </div>
                            ${author.pen_name ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Pen Name</div>
                                    <div class="modal-meta-value">${author.pen_name}</div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="modal-section">
                        <h3>Biography</h3>
                        <p>${author.biography}</p>
                    </div>
                    
                    <div class="modal-section">
                        <h3>Writing Style</h3>
                        <p>${author.writing_style}</p>
                    </div>
                    
                    <div class="modal-section">
                        <h3>Details</h3>
                        <div class="modal-meta-grid">
                            <div class="modal-meta-item">
                                <div class="modal-meta-label">Created</div>
                                <div class="modal-meta-value">${new Date(author.created_at).toLocaleString()}</div>
                            </div>
                            <div class="modal-meta-item">
                                <div class="modal-meta-label">Author ID</div>
                                <div class="modal-meta-value">${author.id}</div>
                            </div>
                            ${author.plot_id ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Associated Plot</div>
                                    <div class="modal-meta-value">${author.plot_id}</div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
                
                modal.style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('detailModal').style.display = 'none';
            }
            
            // Close modal when clicking outside of it
            window.onclick = function(event) {
                const modal = document.getElementById('detailModal');
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            }

            // Load data when page loads
            loadData();
        </script>
    </body>
    </html>
    """)

@app.get("/api/plots")
async def get_all_plots():
    """Get all plots with metadata"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
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