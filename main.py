from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import uuid
import logging
from typing import Dict, Set
from agent_service import book_agent
from multi_agent_system import multi_agent_system

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
            <h1>📚 Multi-Agent Book Writer System</h1>
            <p>Advanced AI system with orchestrator, plot generator, and author generator agents.</p>
            
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
                } else if (data.type === 'stream_end') {
                    const currentMessage = document.getElementById('current-agent-message');
                    if (currentMessage) {
                        currentMessage.id = '';
                        // Format the final message
                        currentMessage.innerHTML = formatMessage(currentMessage.textContent);
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
                                
                                # Send agent response
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": response.content + "\n\n"
                                }, client_id)
                            else:
                                # Send error for failed agent
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": f"⚠️ {response.agent_name} failed: {response.error}\n\n"
                                }, client_id)
                        
                        # Send end signal
                        await manager.send_json_message({
                            "type": "stream_end",
                            "workflow_completed": result["workflow_completed"]
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