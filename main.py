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
    <html lang="en" data-theme="light">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BooksWriter AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                /* Light theme colors (inspired by OpenAI) */
                --bg-primary: #ffffff;
                --bg-secondary: #f7f7f8;
                --bg-tertiary: #ececf1;
                --text-primary: #0d0d0d;
                --text-secondary: #676767;
                --text-tertiary: #8e8ea0;
                --border: #e6e6ea;
                --accent: #10a37f;
                --accent-hover: #0d8765;
                --accent-light: #10a37f10;
                --chat-user: #10a37f;
                --chat-assistant: #f7f7f8;
                --shadow: rgba(0, 0, 0, 0.05);
                --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }

            [data-theme="dark"] {
                /* Dark theme colors */
                --bg-primary: #0d1117;
                --bg-secondary: #161b22;
                --bg-tertiary: #21262d;
                --text-primary: #f0f6fc;
                --text-secondary: #9198a1;
                --text-tertiary: #656d76;
                --border: #30363d;
                --accent: #10a37f;
                --accent-hover: #0d8765;
                --accent-light: #10a37f20;
                --chat-user: #10a37f;
                --chat-assistant: #161b22;
                --shadow: rgba(0, 0, 0, 0.3);
                --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: var(--bg-secondary);
                color: var(--text-primary);
                line-height: 1.6;
                transition: all 0.3s ease;
            }

            .header {
                background: var(--bg-primary);
                border-bottom: 1px solid var(--border);
                position: sticky;
                top: 0;
                z-index: 100;
                backdrop-filter: blur(20px);
                background: var(--bg-primary)f0;
            }

            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 1rem 2rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .logo {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-weight: 700;
                font-size: 1.25rem;
                color: var(--text-primary);
                text-decoration: none;
            }

            .logo-icon {
                width: 32px;
                height: 32px;
                background: var(--gradient);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            }

            .nav-actions {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .theme-toggle {
                background: none;
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.5rem;
                color: var(--text-primary);
                cursor: pointer;
                transition: all 0.2s ease;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .theme-toggle:hover {
                background: var(--bg-tertiary);
            }

            .nav-link {
                background: var(--accent);
                color: white;
                padding: 0.5rem 1rem;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.2s ease;
                border: none;
                cursor: pointer;
            }

            .nav-link:hover {
                background: var(--accent-hover);
                transform: translateY(-1px);
            }

            .nav-link.secondary {
                background: var(--bg-tertiary);
                color: var(--text-primary);
            }

            .nav-link.secondary:hover {
                background: var(--border);
            }

            .main-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 2rem;
                min-height: calc(100vh - 80px);
            }
            .sidebar {
                background: var(--bg-primary);
                border-radius: 12px;
                padding: 1.5rem;
                height: fit-content;
                border: 1px solid var(--border);
                box-shadow: 0 4px 6px var(--shadow);
            }

            .sidebar-section {
                margin-bottom: 2rem;
            }

            .sidebar-section:last-child {
                margin-bottom: 0;
            }

            .section-title {
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--text-secondary);
                margin-bottom: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .model-selector {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            .model-selector select {
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.75rem;
                color: var(--text-primary);
                font-size: 0.875rem;
                transition: all 0.2s ease;
            }

            .model-selector select:focus {
                outline: none;
                border-color: var(--accent);
                box-shadow: 0 0 0 3px var(--accent-light);
            }

            .model-info {
                font-size: 0.75rem;
                color: var(--text-tertiary);
                line-height: 1.4;
            }

            .parameters-section {
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 12px;
                overflow: hidden;
            }

            .parameters-header {
                padding: 1rem 1.5rem;
                background: var(--bg-primary);
                border-bottom: 1px solid var(--border);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .parameters-title {
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
            }

            .toggle-btn {
                background: none;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                font-size: 1.25rem;
                transition: transform 0.2s ease;
            }

            .toggle-btn:hover {
                color: var(--text-primary);
            }

            .toggle-btn.expanded {
                transform: rotate(180deg);
            }

            .parameters-content {
                padding: 1.5rem;
            }

            .param-group {
                margin-bottom: 1.5rem;
            }

            .param-label {
                display: block;
                font-weight: 500;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
                font-size: 0.875rem;
            }

            .param-select {
                width: 100%;
                background: var(--bg-primary);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.75rem;
                color: var(--text-primary);
                font-size: 0.875rem;
                transition: all 0.2s ease;
            }

            .param-select:focus {
                outline: none;
                border-color: var(--accent);
                box-shadow: 0 0 0 3px var(--accent-light);
            }

            .param-select:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .chat-main {
                background: var(--bg-primary);
                border-radius: 12px;
                border: 1px solid var(--border);
                display: flex;
                flex-direction: column;
                height: calc(100vh - 140px);
                box-shadow: 0 4px 6px var(--shadow);
            }

            .chat-header {
                padding: 1rem 1.5rem;
                border-bottom: 1px solid var(--border);
                background: var(--bg-primary);
                border-radius: 12px 12px 0 0;
            }

            .chat-title {
                font-size: 1.125rem;
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
            }

            .chat-subtitle {
                font-size: 0.875rem;
                color: var(--text-secondary);
                margin: 0.25rem 0 0 0;
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                gap: 1.5rem;
            }

            .message {
                display: flex;
                gap: 1rem;
                max-width: 100%;
                margin-bottom: 0.5rem;
            }
            
            .message:last-child {
                margin-bottom: 0;
            }

            .message.user {
                justify-content: flex-end;
            }

            .message-content {
                max-width: 65%;
                padding: 1rem 1.25rem;
                border-radius: 12px;
                font-size: 0.95rem;
                line-height: 1.6;
                word-wrap: break-word;
                word-break: break-word;
                overflow-wrap: break-word;
                min-height: 44px;
                display: flex;
                align-items: flex-start;
                flex-direction: column;
                justify-content: center;
                max-height: 500px;
                overflow-y: auto;
                position: relative;
            }

            .message.user .message-content {
                background: var(--chat-user);
                color: white;
                border-bottom-right-radius: 4px;
            }

            .message.assistant .message-content {
                background: var(--chat-assistant);
                color: var(--text-primary);
                border: 1px solid var(--border);
                border-bottom-left-radius: 4px;
            }

            .message-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.875rem;
                flex-shrink: 0;
            }
            
            .message-timestamp {
                font-size: 0.75rem;
                color: var(--text-tertiary);
                margin-top: 0.25rem;
                opacity: 0.7;
                font-weight: 400;
            }

            /* Custom scrollbar for long messages */
            .message-content::-webkit-scrollbar {
                width: 4px;
            }

            .message-content::-webkit-scrollbar-track {
                background: transparent;
            }

            .message-content::-webkit-scrollbar-thumb {
                background: var(--text-tertiary);
                border-radius: 2px;
                opacity: 0.3;
            }

            .message-content::-webkit-scrollbar-thumb:hover {
                opacity: 0.6;
            }

            /* Long message indicator */
            .message-content.long-message::after {
                content: "📄 Long message - scroll to read more";
                position: absolute;
                bottom: 0;
                right: 0;
                background: var(--bg-tertiary);
                color: var(--text-tertiary);
                font-size: 0.7rem;
                padding: 2px 6px;
                border-radius: 4px;
                opacity: 0.8;
                pointer-events: none;
            }

            /* Fade effect for long messages */
            .message-content.long-message {
                background: linear-gradient(to bottom, 
                    var(--chat-assistant) 0%, 
                    var(--chat-assistant) 85%, 
                    var(--bg-tertiary) 100%);
            }

            .message.user .message-content.long-message {
                background: linear-gradient(to bottom, 
                    var(--chat-user) 0%, 
                    var(--chat-user) 85%, 
                    rgba(16, 163, 127, 0.7) 100%);
            }

            .message.user .message-avatar {
                background: var(--chat-user);
                color: white;
            }

            .message.assistant .message-avatar {
                background: var(--gradient);
                color: white;
            }

            .chat-input-container {
                padding: 1rem 1.5rem;
                border-top: 1px solid var(--border);
                background: var(--bg-primary);
                border-radius: 0 0 12px 12px;
            }

            .chat-input {
                display: flex;
                gap: 0.75rem;
                align-items: flex-end;
            }

            .input-field {
                flex: 1;
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 0.75rem 1rem;
                color: var(--text-primary);
                font-size: 0.95rem;
                resize: none;
                min-height: 44px;
                max-height: 120px;
                transition: all 0.2s ease;
            }

            .input-field:focus {
                outline: none;
                border-color: var(--accent);
                box-shadow: 0 0 0 3px var(--accent-light);
            }

            .send-btn {
                background: var(--accent);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 0.75rem 1.5rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .send-btn:hover:not(:disabled) {
                background: var(--accent-hover);
                transform: translateY(-1px);
            }

            .send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }

            .status-bar {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-top: 0.5rem;
                padding: 0.5rem 0;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                flex-shrink: 0;
            }

            .status-indicator.connected {
                background: #10a37f;
            }

            .status-indicator.disconnected {
                background: #ef4444;
            }

            .status-text {
                font-size: 0.75rem;
                color: var(--text-tertiary);
            }

            .typing-indicator {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 1rem 1.25rem;
                color: var(--text-secondary);
                font-style: italic;
                font-size: 0.875rem;
            }

            .typing-dots {
                display: flex;
                gap: 2px;
            }

            .typing-dots span {
                width: 4px;
                height: 4px;
                background: var(--text-tertiary);
                border-radius: 50%;
                animation: typing 1.4s infinite;
            }

            .typing-dots span:nth-child(2) {
                animation-delay: 0.2s;
            }

            .typing-dots span:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes typing {
                0%, 60%, 100% {
                    transform: translateY(0);
                    opacity: 0.4;
                }
                30% {
                    transform: translateY(-10px);
                    opacity: 1;
                }
            }

            .structured-response {
                background: var(--bg-secondary) !important;
                border: 2px solid var(--accent) !important;
                border-radius: 12px !important;
                margin: 1rem 0;
            }

            .structured-response h4 {
                color: var(--accent);
                margin-bottom: 1rem;
                font-size: 0.875rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .structured-response pre {
                background: var(--bg-primary);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 1rem;
                overflow-x: auto;
                font-size: 0.8rem;
                color: var(--text-primary);
            }

            @media (max-width: 768px) {
                .main-container {
                    grid-template-columns: 1fr;
                    gap: 1rem;
                    padding: 1rem;
                }

                .header-content {
                    padding: 1rem;
                }

                .chat-main {
                    height: calc(100vh - 200px);
                }

                .nav-actions {
                    flex-direction: column;
                    gap: 0.5rem;
                }

                /* Adjust message width for mobile */
                .message-content {
                    max-width: 85%;
                    max-height: 300px;
                }

                /* Smaller long message indicator on mobile */
                .message-content.long-message::after {
                    content: "📄 Scroll to read more";
                    font-size: 0.65rem;
                    padding: 1px 4px;
                }
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <a href="/" class="logo">
                    <div class="logo-icon">AI</div>
                    BooksWriter AI
                </a>
                <div class="nav-actions">
                    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">
                        <span id="theme-icon">🌙</span>
                    </button>
                    <a href="/admin" class="nav-link secondary">Admin</a>
                    <a href="/library" class="nav-link">View Library</a>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="main-container">
            <!-- Sidebar -->
            <aside class="sidebar">
                <!-- Model Selection -->
                <div class="sidebar-section">
                    <h3 class="section-title">AI Model</h3>
                    <div class="model-selector">
                        <select id="modelSelect" onchange="switchModel()">
                            <option value="">Loading models...</option>
                        </select>
                        <div class="model-info" id="modelInfo">Select a model to get started</div>
                    </div>
                </div>

                <!-- Content Parameters -->
                <div class="sidebar-section">
                    <div class="parameters-section">
                        <div class="parameters-header">
                            <h3 class="parameters-title">Content Parameters</h3>
                            <button class="toggle-btn" id="toggleParams" onclick="toggleParameters()">
                                ▼
                            </button>
                        </div>
                        <div class="parameters-content" id="parametersContent" style="display: none;">
                            <!-- Genre Hierarchy -->
                            <div class="param-group">
                                <label class="param-label">Genre</label>
                                <select class="param-select" id="genreSelect" onchange="onGenreChange()">
                                    <option value="">Select Genre...</option>
                                </select>
                            </div>
                            
                            <div class="param-group">
                                <label class="param-label">Subgenre</label>
                                <select class="param-select" id="subgenreSelect" onchange="onSubgenreChange()" disabled>
                                    <option value="">Select Subgenre...</option>
                                </select>
                            </div>
                            
                            <div class="param-group">
                                <label class="param-label">Microgenre</label>
                                <select class="param-select" id="microgenreSelect" onchange="onMicrogenreChange()" disabled>
                                    <option value="">Select Microgenre...</option>
                                </select>
                            </div>
                            
                            <div class="param-group">
                                <label class="param-label">Trope</label>
                                <select class="param-select" id="tropeSelect" onchange="onTropeChange()" disabled>
                                    <option value="">Select Trope...</option>
                                </select>
                            </div>
                            
                            <div class="param-group">
                                <label class="param-label">Tone</label>
                                <select class="param-select" id="toneSelect" onchange="updateContext()" disabled>
                                    <option value="">Select Tone...</option>
                                </select>
                            </div>
                            
                            <div class="param-group">
                                <label class="param-label">Target Audience</label>
                                <select class="param-select" id="audienceSelect" onchange="updateContext()">
                                    <option value="">Select Audience...</option>
                                </select>
                            </div>
                            
                            <div class="param-group">
                                <label class="param-label">Content to Improve</label>
                                <select class="param-select" id="contentSelect" onchange="onContentChange()">
                                    <option value="">Select Content...</option>
                                </select>
                            </div>
                            
                            <div id="selectedParams" style="padding: 0.75rem; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; font-size: 0.75rem; color: var(--text-tertiary);">
                                No parameters selected. Use "specified genres and audience params" in your message.
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Chat Interface -->
            <section class="chat-main">
                <div class="chat-header">
                    <h1 class="chat-title">Multi-Agent Book Writer</h1>
                    <p class="chat-subtitle">Advanced AI system with orchestrator, plot generator, and author generator agents</p>
                </div>
                
                <div class="chat-messages" id="chat">
                    <!-- Messages will be added here dynamically -->
                </div>
                
                <div class="chat-input-container">
                    <div class="chat-input">
                        <textarea 
                            class="input-field" 
                            id="messageInput" 
                            placeholder="Try: 'Create a plot and author based on the specified genres and audience params' or describe what you want!"
                            rows="1"
                        ></textarea>
                        <button class="send-btn" onclick="sendMessage()" id="sendButton">
                            <span>Send</span>
                            <span>→</span>
                        </button>
                    </div>
                    <div class="status-bar">
                        <div class="status-indicator disconnected" id="statusIndicator"></div>
                        <span class="status-text" id="statusText">Disconnected</span>
                    </div>
                </div>
            </section>
        </main>

        <script>
            let ws = null;
            let sessionId = null;
            let userId = "user_" + Math.random().toString(36).substr(2, 9);
            
            // Theme management
            function toggleTheme() {
                const html = document.documentElement;
                const currentTheme = html.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                
                // Update theme icon
                const themeIcon = document.getElementById('theme-icon');
                themeIcon.textContent = newTheme === 'light' ? '🌙' : '☀️';
            }

            // Initialize theme
            function initializeTheme() {
                const savedTheme = localStorage.getItem('theme') || 'light';
                document.documentElement.setAttribute('data-theme', savedTheme);
                
                const themeIcon = document.getElementById('theme-icon');
                themeIcon.textContent = savedTheme === 'light' ? '🌙' : '☀️';
            }

            function connect() {
                sessionId = "session_" + Math.random().toString(36).substr(2, 9);
                ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
                
                ws.onopen = function(event) {
                    updateStatus('connected');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function(event) {
                    updateStatus('disconnected');
                };
                
                ws.onerror = function(event) {
                    console.error('WebSocket error:', event);
                    updateStatus('error');
                };
            }

            function updateStatus(status) {
                const indicator = document.getElementById('statusIndicator');
                const text = document.getElementById('statusText');
                
                indicator.className = `status-indicator ${status}`;
                
                switch(status) {
                    case 'connected':
                        text.textContent = 'Connected';
                        break;
                    case 'disconnected':
                        text.textContent = 'Disconnected';
                        break;
                    case 'error':
                        text.textContent = 'Connection Error';
                        break;
                }
            }
            
            function showTypingIndicator() {
                const chatContainer = document.getElementById('chat');
                
                // Remove existing typing indicator
                const existingIndicator = document.getElementById('typing-indicator');
                if (existingIndicator) {
                    existingIndicator.remove();
                }
                
                const messageWrapper = document.createElement('div');
                messageWrapper.className = 'message assistant';
                messageWrapper.id = 'typing-indicator';
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = 'AI';
                
                const typingContent = document.createElement('div');
                typingContent.className = 'typing-indicator';
                typingContent.innerHTML = `
                    <span>AI is thinking</span>
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                
                messageWrapper.appendChild(avatar);
                messageWrapper.appendChild(typingContent);
                chatContainer.appendChild(messageWrapper);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            function hideTypingIndicator() {
                const indicator = document.getElementById('typing-indicator');
                if (indicator) {
                    indicator.remove();
                }
            }

            function handleMessage(data) {
                const chatContainer = document.getElementById('chat');
                
                if (data.type === 'stream_chunk') {
                    // Hide typing indicator when first chunk arrives
                    hideTypingIndicator();
                    
                    let currentMessage = document.getElementById('current-agent-message');
                    if (!currentMessage) {
                        const messageWrapper = document.createElement('div');
                        messageWrapper.className = 'message assistant';
                        
                        const avatar = document.createElement('div');
                        avatar.className = 'message-avatar';
                        avatar.textContent = 'AI';
                        
                        currentMessage = document.createElement('div');
                        currentMessage.className = 'message-content';
                        currentMessage.id = 'current-agent-message';
                        currentMessage.style.whiteSpace = 'pre-wrap';
                        
                        // Store timestamp for later addition
                        currentMessage.dataset.timestamp = new Date().toISOString();
                        
                        // AI: avatar first, then content (avatar on left)
                        messageWrapper.appendChild(avatar);
                        messageWrapper.appendChild(currentMessage);
                        chatContainer.appendChild(messageWrapper);
                    }
                    currentMessage.textContent += data.content;
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else if (data.type === 'structured_response') {
                    // Handle structured JSON responses  
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message assistant';
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = 'AI';
                    
                    const structuredMessage = document.createElement('div');
                    structuredMessage.className = 'message-content structured-response';
                    
                    // Add agent name header
                    const agentHeader = document.createElement('h4');
                    agentHeader.textContent = `[DATA] ${data.agent.replace('_', ' ').toUpperCase()} - Structured Response`;
                    structuredMessage.appendChild(agentHeader);
                    
                    // Add JSON data as formatted text
                    const jsonContent = document.createElement('pre');
                    jsonContent.textContent = JSON.stringify(data.json_data, null, 2);
                    structuredMessage.appendChild(jsonContent);
                    
                    // Add timestamp to structured response
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    structuredMessage.appendChild(timestamp);
                    
                    // Check if structured message is too long
                    setTimeout(() => handleLongMessage(structuredMessage), 100);
                    
                    // AI: avatar first, then content (avatar on left)
                    messageWrapper.appendChild(avatar);
                    messageWrapper.appendChild(structuredMessage);
                    chatContainer.appendChild(messageWrapper);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else if (data.type === 'stream_end') {
                    const currentMessage = document.getElementById('current-agent-message');
                    if (currentMessage) {
                        currentMessage.id = '';
                        // Format the final message
                        const messageText = currentMessage.textContent;
                        currentMessage.innerHTML = formatMessage(messageText);
                        
                        // Add timestamp to AI message
                        const timestamp = document.createElement('div');
                        timestamp.className = 'message-timestamp';
                        const messageTime = new Date(currentMessage.dataset.timestamp);
                        timestamp.textContent = formatTimestamp(messageTime);
                        currentMessage.appendChild(timestamp);
                        
                        // Check if message is too long
                        setTimeout(() => handleLongMessage(currentMessage), 100);
                    }
                    
                    // Log structured responses for debugging
                    if (data.structured_responses) {
                        console.log('Structured responses received:', data.structured_responses);
                    }
                } else if (data.type === 'error') {
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message assistant';
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = '⚠️';
                    
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'message-content';
                    errorMessage.textContent = 'Error: ' + data.content;
                    errorMessage.style.backgroundColor = 'var(--bg-tertiary)';
                    errorMessage.style.color = '#ef4444';
                    errorMessage.style.border = '1px solid #ef4444';
                    
                    // Add timestamp to error message
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    errorMessage.appendChild(timestamp);
                    
                    // Check if error message is too long
                    setTimeout(() => handleLongMessage(errorMessage), 100);
                    
                    // AI: avatar first, then content (avatar on left)
                    messageWrapper.appendChild(avatar);
                    messageWrapper.appendChild(errorMessage);
                    chatContainer.appendChild(messageWrapper);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            
            function formatTimestamp(date) {
                const now = new Date();
                const diff = now - date;
                const seconds = Math.floor(diff / 1000);
                const minutes = Math.floor(seconds / 60);
                const hours = Math.floor(minutes / 60);
                
                if (seconds < 60) {
                    return 'just now';
                } else if (minutes < 60) {
                    return `${minutes}m ago`;
                } else if (hours < 24) {
                    return `${hours}h ago`;
                } else {
                    return date.toLocaleDateString();
                }
            }

            function handleLongMessage(messageElement) {
                // Check if message content is too long
                const contentHeight = messageElement.scrollHeight;
                const visibleHeight = messageElement.clientHeight;
                
                if (contentHeight > visibleHeight) {
                    messageElement.classList.add('long-message');
                    
                    // Add click handler to expand/collapse
                    messageElement.addEventListener('click', function() {
                        if (messageElement.style.maxHeight === 'none') {
                            messageElement.style.maxHeight = '500px';
                            messageElement.classList.add('long-message');
                        } else {
                            messageElement.style.maxHeight = 'none';
                            messageElement.classList.remove('long-message');
                        }
                    });
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
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message user';
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = message;
                    
                    // Add timestamp to user message
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    messageContent.appendChild(timestamp);
                    
                    // Check if message is too long
                    setTimeout(() => handleLongMessage(messageContent), 100);
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = 'You';
                    
                    // User: content first, then avatar (avatar on right)
                    messageWrapper.appendChild(messageContent);
                    messageWrapper.appendChild(avatar);
                    chatContainer.appendChild(messageWrapper);
                    
                    // Send to server
                    ws.send(JSON.stringify({
                        type: 'message',
                        content: message,
                        user_id: userId
                    }));
                    
                    // Show typing indicator
                    showTypingIndicator();
                    
                    input.value = '';
                    input.style.height = 'auto';
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            
            // Auto-resize textarea
            function autoResize(textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            }
            
            // Enter key support (with Shift+Enter for new lines)
            document.getElementById('messageInput').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Auto-resize textarea on input
            document.getElementById('messageInput').addEventListener('input', function(e) {
                autoResize(e.target);
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
            
            // Parameter management
            let selectedGenre = null;
            let selectedSubgenre = null;
            let selectedMicrogenre = null;
            let selectedTrope = null;
            let selectedTone = null;
            let selectedAudience = null;
            let selectedContent = null;
            
            function toggleParameters() {
                const content = document.getElementById('parametersContent');
                const button = document.getElementById('toggleParams');
                
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    button.textContent = '▲';
                    button.classList.add('expanded');
                } else {
                    content.style.display = 'none';
                    button.textContent = '▼';
                    button.classList.remove('expanded');
                }
            }
            
            // Global data storage for hierarchical relationships
            let allGenres = [];
            let allSubgenres = [];
            let allMicrogenres = [];
            let allTropes = [];
            let allTones = [];
            let allAudiences = [];

            async function loadParameters() {
                try {
                    // Load all data from the complete hierarchy API
                    const genresResponse = await fetch('/api/genres');
                    if (genresResponse.ok) {
                        const data = await genresResponse.json();
                        
                        if (data.success) {
                            // Store all data globally
                            allGenres = data.genres || [];
                            allSubgenres = data.subgenres || [];
                            allMicrogenres = data.microgenres || [];
                            allTropes = data.tropes || [];
                            allTones = data.tones || [];
                            
                            // Populate genre dropdown
                            populateGenreDropdown();
                            
                            // Build complete packages for easy selection
                            buildCompletePackages();
                        }
                    }
                    
                    // Load audiences separately
                    const audiencesResponse = await fetch('/api/target-audiences');
                    if (audiencesResponse.ok) {
                        const audiencesData = await audiencesResponse.json();
                        if (audiencesData.success && audiencesData.audiences) {
                            allAudiences = audiencesData.audiences;
                            populateAudienceDropdown();
                        }
                    }
                } catch (error) {
                    console.error('Error loading parameters:', error);
                }
            }
            
            function populateGenreDropdown() {
                const genreSelect = document.getElementById('genreSelect');
                genreSelect.innerHTML = '<option value="">Select Genre...</option>';
                
                allGenres.forEach(genre => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify(genre);
                    option.textContent = genre.name;
                    genreSelect.appendChild(option);
                });
            }
            
            function populateAudienceDropdown() {
                const audienceSelect = document.getElementById('audienceSelect');
                audienceSelect.innerHTML = '<option value="">Select Audience...</option>';
                
                allAudiences.forEach(audience => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify(audience);
                    option.textContent = `${audience.age_group} - ${audience.gender} - ${audience.sexual_orientation}`;
                    audienceSelect.appendChild(option);
                });
            }
            
            function buildCompletePackages() {
                const packageSelect = document.getElementById('completePackageSelect');
                packageSelect.innerHTML = '<option value="">Choose a Complete Genre Package...</option>';
                
                // Build packages for complete chains: Genre -> Subgenre -> Microgenre -> Trope -> Tone
                allTones.forEach(tone => {
                    if (tone.trope_id) {
                        const trope = allTropes.find(t => t.id === tone.trope_id);
                        if (trope && trope.microgenre_id) {
                            const microgenre = allMicrogenres.find(m => m.id === trope.microgenre_id);
                            if (microgenre && microgenre.subgenre_id) {
                                const subgenre = allSubgenres.find(s => s.id === microgenre.subgenre_id);
                                if (subgenre && subgenre.genre_id) {
                                    const genre = allGenres.find(g => g.id === subgenre.genre_id);
                                    if (genre) {
                                        // Create complete package
                                        const packageData = {
                                            genre, subgenre, microgenre, trope, tone
                                        };
                                        
                                        const option = document.createElement('option');
                                        option.value = JSON.stringify(packageData);
                                        option.textContent = `${genre.name} > ${subgenre.name} > ${microgenre.name} > ${trope.name} > ${tone.name}`;
                                        packageSelect.appendChild(option);
                                    }
                                }
                            }
                        }
                    }
                });
            }
            
            // Complete package selection
            function selectCompletePackage() {
                const packageSelect = document.getElementById('completePackageSelect');
                
                if (packageSelect.value) {
                    const packageData = JSON.parse(packageSelect.value);
                    
                    // Set all selections based on the complete package
                    selectedGenre = packageData.genre;
                    selectedSubgenre = packageData.subgenre;
                    selectedMicrogenre = packageData.microgenre;
                    selectedTrope = packageData.trope;
                    selectedTone = packageData.tone;
                    
                    // Update all dropdowns to reflect the selection
                    updateDropdownsFromSelection();
                    updateContext();
                } else {
                    // Clear all selections
                    clearAllSelections();
                }
            }
            
            function updateDropdownsFromSelection() {
                // Update genre dropdown
                const genreSelect = document.getElementById('genreSelect');
                if (selectedGenre) {
                    genreSelect.value = JSON.stringify(selectedGenre);
                    populateSubgenreDropdown();
                }
                
                // Update subgenre dropdown
                const subgenreSelect = document.getElementById('subgenreSelect');
                if (selectedSubgenre) {
                    subgenreSelect.value = JSON.stringify(selectedSubgenre);
                    populateMicrogenreDropdown();
                }
                
                // Update microgenre dropdown
                const microgenreSelect = document.getElementById('microgenreSelect');
                if (selectedMicrogenre) {
                    microgenreSelect.value = JSON.stringify(selectedMicrogenre);
                    populateTropeDropdown();
                }
                
                // Update trope dropdown
                const tropeSelect = document.getElementById('tropeSelect');
                if (selectedTrope) {
                    tropeSelect.value = JSON.stringify(selectedTrope);
                    populateToneDropdown();
                }
                
                // Update tone dropdown
                const toneSelect = document.getElementById('toneSelect');
                if (selectedTone) {
                    toneSelect.value = JSON.stringify(selectedTone);
                }
            }
            
            // Hierarchical genre selection functions
            function onGenreChange() {
                const genreSelect = document.getElementById('genreSelect');
                selectedGenre = genreSelect.value ? JSON.parse(genreSelect.value) : null;
                selectedSubgenre = null;
                selectedMicrogenre = null;
                selectedTrope = null;
                selectedTone = null;
                
                populateSubgenreDropdown();
                updateContext();
            }
            
            function onSubgenreChange() {
                const subgenreSelect = document.getElementById('subgenreSelect');
                selectedSubgenre = subgenreSelect.value ? JSON.parse(subgenreSelect.value) : null;
                selectedMicrogenre = null;
                selectedTrope = null;
                selectedTone = null;
                
                populateMicrogenreDropdown();
                updateContext();
            }
            
            function onMicrogenreChange() {
                const microgenreSelect = document.getElementById('microgenreSelect');
                selectedMicrogenre = microgenreSelect.value ? JSON.parse(microgenreSelect.value) : null;
                selectedTrope = null;
                selectedTone = null;
                
                populateTropeDropdown();
                updateContext();
            }
            
            function onTropeChange() {
                const tropeSelect = document.getElementById('tropeSelect');
                selectedTrope = tropeSelect.value ? JSON.parse(tropeSelect.value) : null;
                selectedTone = null;
                
                populateToneDropdown();
                updateContext();
            }
            
            // Population functions for hierarchical dropdowns
            function populateSubgenreDropdown() {
                const subgenreSelect = document.getElementById('subgenreSelect');
                subgenreSelect.innerHTML = '<option value="">Select Subgenre...</option>';
                
                if (selectedGenre) {
                    subgenreSelect.disabled = false;
                    const genreSubgenres = allSubgenres.filter(sub => sub.genre_id === selectedGenre.id);
                    genreSubgenres.forEach(subgenre => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(subgenre);
                        option.textContent = subgenre.name;
                        subgenreSelect.appendChild(option);
                    });
                } else {
                    subgenreSelect.disabled = true;
                }
                
                resetDownstreamDropdowns('microgenre');
            }
            
            function populateMicrogenreDropdown() {
                const microgenreSelect = document.getElementById('microgenreSelect');
                microgenreSelect.innerHTML = '<option value="">Select Microgenre...</option>';
                
                if (selectedSubgenre) {
                    microgenreSelect.disabled = false;
                    const subgenreMicrogenres = allMicrogenres.filter(micro => micro.subgenre_id === selectedSubgenre.id);
                    subgenreMicrogenres.forEach(microgenre => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(microgenre);
                        option.textContent = microgenre.name;
                        microgenreSelect.appendChild(option);
                    });
                } else {
                    microgenreSelect.disabled = true;
                }
                
                resetDownstreamDropdowns('trope');
            }
            
            function populateTropeDropdown() {
                const tropeSelect = document.getElementById('tropeSelect');
                tropeSelect.innerHTML = '<option value="">Select Trope...</option>';
                
                if (selectedMicrogenre) {
                    tropeSelect.disabled = false;
                    const microgenreTropes = allTropes.filter(trope => trope.microgenre_id === selectedMicrogenre.id);
                    microgenreTropes.forEach(trope => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(trope);
                        option.textContent = trope.name;
                        tropeSelect.appendChild(option);
                    });
                } else {
                    tropeSelect.disabled = true;
                }
                
                resetDownstreamDropdowns('tone');
            }
            
            function populateToneDropdown() {
                const toneSelect = document.getElementById('toneSelect');
                toneSelect.innerHTML = '<option value="">Select Tone...</option>';
                
                if (selectedTrope) {
                    toneSelect.disabled = false;
                    const tropeTones = allTones.filter(tone => tone.trope_id === selectedTrope.id);
                    tropeTones.forEach(tone => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(tone);
                        option.textContent = tone.name;
                        toneSelect.appendChild(option);
                    });
                } else {
                    toneSelect.disabled = true;
                }
            }
            
            function resetDownstreamDropdowns(startFrom) {
                const dropdowns = ['microgenre', 'trope', 'tone'];
                const startIndex = dropdowns.indexOf(startFrom);
                
                for (let i = startIndex; i < dropdowns.length; i++) {
                    const select = document.getElementById(dropdowns[i] + 'Select');
                    select.innerHTML = `<option value="">Select ${dropdowns[i].charAt(0).toUpperCase() + dropdowns[i].slice(1)}...</option>`;
                    select.disabled = true;
                }
            }
            
            function clearAllSelections() {
                selectedGenre = null;
                selectedSubgenre = null;
                selectedMicrogenre = null;
                selectedTrope = null;
                selectedTone = null;
                selectedAudience = null;
                
                // Reset all dropdowns
                document.getElementById('genreSelect').value = '';
                document.getElementById('completePackageSelect').value = '';
                populateSubgenreDropdown();
                updateContext();
            }
            
            function updateContext() {
                const microgenreSelect = document.getElementById('microgenreSelect');
                const tropeSelect = document.getElementById('tropeSelect');
                const toneSelect = document.getElementById('toneSelect');
                const audienceSelect = document.getElementById('audienceSelect');
                const selectedParamsDiv = document.getElementById('selectedParams');
                
                // Update all selections
                selectedMicrogenre = microgenreSelect.value ? JSON.parse(microgenreSelect.value) : null;
                selectedTrope = tropeSelect.value ? JSON.parse(tropeSelect.value) : null;
                selectedTone = toneSelect.value ? JSON.parse(toneSelect.value) : null;
                selectedAudience = audienceSelect.value ? JSON.parse(audienceSelect.value) : null;
                
                let paramsText = '';
                
                if (selectedGenre || selectedSubgenre || selectedMicrogenre || selectedTrope || selectedTone || selectedAudience || selectedContent) {
                    paramsText = '<strong>Selected Parameters:</strong><br>';
                    
                    // Selected content for improvement
                    if (selectedContent) {
                        paramsText += `<span style="background: #6f42c1; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Content: ${selectedContent.type.toUpperCase()} - ${selectedContent.title}</span><br>`;
                    }
                    
                    // Genre hierarchy
                    if (selectedGenre) {
                        paramsText += `<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Genre: ${selectedGenre.name}</span>`;
                    }
                    if (selectedSubgenre) {
                        paramsText += `<span style="background: #0056b3; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Subgenre: ${selectedSubgenre.name}</span>`;
                    }
                    if (selectedMicrogenre) {
                        paramsText += `<span style="background: #003d82; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Microgenre: ${selectedMicrogenre.name}</span>`;
                    }
                    
                    // Tropes and Tones
                    if (selectedTrope) {
                        paramsText += `<br><span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Trope: ${selectedTrope.name} (${selectedTrope.category})</span>`;
                    }
                    if (selectedTone) {
                        paramsText += `<span style="background: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Tone: ${selectedTone.name}</span>`;
                    }
                    
                    // Target Audience
                    if (selectedAudience) {
                        paramsText += `<br><span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Audience: ${selectedAudience.age_group} - ${selectedAudience.gender} - ${selectedAudience.sexual_orientation}</span>`;
                    }
                    
                    // Add descriptions
                    if (selectedMicrogenre && selectedMicrogenre.description) {
                        paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Microgenre: ${selectedMicrogenre.description}</em>`;
                    }
                    if (selectedTrope && selectedTrope.description) {
                        paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Trope: ${selectedTrope.description}</em>`;
                    }
                    if (selectedTone && selectedTone.description) {
                        paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Tone: ${selectedTone.description}</em>`;
                    }
                    // Target audience details are shown in the main tag above
                } else {
                    paramsText = '<em style="color: #6c757d;">No parameters selected. Select parameters above to automatically include them in your requests.</em>';
                }
                
                selectedParamsDiv.innerHTML = paramsText;
            }
            
            // Content selection functions
            async function loadContent() {
                try {
                    const response = await fetch('/api/content-selection');
                    const data = await response.json();
                    
                    if (data.success) {
                        const contentSelect = document.getElementById('contentSelect');
                        contentSelect.innerHTML = '<option value="">Select Content...</option>';
                        
                        data.content.forEach(item => {
                            const option = document.createElement('option');
                            const value = JSON.stringify({
                                id: item.id,
                                type: item.type,
                                title: item.title
                            });
                            option.value = value;
                            option.textContent = `${item.type.toUpperCase()}: ${item.title}`;
                            contentSelect.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('Error loading content:', error);
                }
            }
            
            function onContentChange() {
                const contentSelect = document.getElementById('contentSelect');
                selectedContent = contentSelect.value ? JSON.parse(contentSelect.value) : null;
                updateContext();
            }
            
            function refreshContent() {
                loadContent();
            }
            
            function injectParametersIntoMessage(message) {
                // Always inject parameters if any are selected
                if (!selectedGenre && !selectedSubgenre && !selectedMicrogenre && !selectedTrope && !selectedTone && !selectedAudience && !selectedContent) {
                    return message;
                }
                
                let contextText = '\n\n========== DETAILED CONTENT SPECIFICATIONS ==========';
                contextText += '\nUse these detailed specifications to guide content creation:\n';
                
                // Selected content for improvement
                if (selectedContent) {
                    contextText += '\n--- SELECTED CONTENT FOR IMPROVEMENT ---';
                    contextText += `\nCONTENT_ID: ${selectedContent.id}`;
                    contextText += `\nCONTENT_TYPE: ${selectedContent.type}`;
                    contextText += `\nCONTENT_TITLE: ${selectedContent.title}`;
                    contextText += '\nNOTE: This content should be fetched from the database for iterative improvement.';
                }
                
                // Complete Genre Hierarchy with detailed descriptions
                if (selectedGenre || selectedSubgenre || selectedMicrogenre) {
                    contextText += '\n--- GENRE HIERARCHY ---';
                    
                    if (selectedGenre) {
                        contextText += `\nMAIN GENRE: ${selectedGenre.name}`;
                        if (selectedGenre.description) {
                            contextText += `\n  Description: ${selectedGenre.description}`;
                        }
                    }
                    
                    if (selectedSubgenre) {
                        contextText += `\nSUBGENRE: ${selectedSubgenre.name}`;
                        if (selectedSubgenre.description) {
                            contextText += `\n  Description: ${selectedSubgenre.description}`;
                        }
                    }
                    
                    if (selectedMicrogenre) {
                        contextText += `\nMICROGENRE: ${selectedMicrogenre.name}`;
                        if (selectedMicrogenre.description) {
                            contextText += `\n  Description: ${selectedMicrogenre.description}`;
                        }
                    }
                }
                
                // Story Elements
                if (selectedTrope || selectedTone) {
                    contextText += '\n\n--- STORY ELEMENTS ---';
                    
                    if (selectedTrope) {
                        contextText += `\nTROPE: ${selectedTrope.name}`;
                        if (selectedTrope.description) {
                            contextText += `\n  Description: ${selectedTrope.description}`;
                        }
                        contextText += '\n  IMPORTANT: Integrate this trope naturally into the story structure.';
                    }
                    
                    if (selectedTone) {
                        contextText += `\nTONE: ${selectedTone.name}`;
                        if (selectedTone.description) {
                            contextText += `\n  Description: ${selectedTone.description}`;
                        }
                        contextText += '\n  IMPORTANT: Maintain this tone consistently throughout the content.';
                    }
                }
                
                // Target Audience Analysis
                if (selectedAudience) {
                    contextText += '\n\n--- TARGET AUDIENCE ANALYSIS ---';
                    contextText += `\nAUDIENCE PROFILE:`;
                    contextText += `\n  Age Group: ${selectedAudience.age_group}`;
                    contextText += `\n  Gender: ${selectedAudience.gender}`;
                    contextText += `\n  Sexual Orientation: ${selectedAudience.sexual_orientation}`;
                    
                    // Target audience is defined by the three core demographic fields above
                    
                    contextText += '\n  IMPORTANT: Tailor content complexity, themes, and language to this specific audience.';
                }
                
                // Creative Guidelines
                contextText += '\n\n--- CREATIVE GUIDELINES ---';
                contextText += '\n• Follow the genre conventions while being original';
                contextText += '\n• Ensure all story elements work together cohesively';
                contextText += '\n• Consider the target audience in every creative decision';
                contextText += '\n• Maintain consistency with the specified tone throughout';
                if (selectedTrope) {
                    contextText += '\n• Weave the trope into the story naturally, avoiding clichés';
                }
                
                contextText += '\n========================================\n';
                
                return message + contextText;
            }
            
            // Override the sendMessage function to inject parameters
            const originalSendMessage = sendMessage;
            sendMessage = function() {
                const input = document.getElementById('messageInput');
                let message = input.value.trim();
                
                if (message) {
                    // Inject parameters if referenced
                    message = injectParametersIntoMessage(message);
                    
                    // Display user message
                    const chatContainer = document.getElementById('chat');
                    const userMessage = document.createElement('div');
                    userMessage.className = 'message user-message';
                    userMessage.textContent = input.value; // Show original message to user
                    chatContainer.appendChild(userMessage);
                    
                    // Send enhanced message to server
                    ws.send(JSON.stringify({
                        type: 'message',
                        content: message, // Send enhanced message with parameters
                        user_id: userId
                    }));
                    
                    input.value = '';
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }

            // Connect on page load
            window.onload = function() {
                initializeTheme();
                connect();
                loadModels();
                loadParameters();
                loadContent();
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
                    result = await multi_agent_system.process_message(content, user_id, session_id)
                    
                    if result["success"]:
                        # Stream responses from all agents
                        for response in result["responses"]:
                            if response.success:
                                # Send agent header
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": f"\n[AI] {response.agent_name.replace('_', ' ').title()}:\n"
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
                                        "content": f"[WARNING] JSON parsing failed. Raw response:\n{response.content}\n\n"
                                    }, client_id)
                            else:
                                # Send error for failed agent
                                await manager.send_json_message({
                                    "type": "stream_chunk",
                                    "content": f"[ERROR] {response.agent_name} failed: {response.error}\n\n"
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

@app.get("/admin")
async def admin_page():
    """Content management interface for managing genres and target audiences"""
    import os
    file_path = os.path.join(os.path.dirname(__file__), 'new_admin_interface.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/library")
async def library_page():
    """Library page to view all plots and authors"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Book Library - Multi-Agent Book Writer</title>
                gap: 30px;
            }
            @media (max-width: 1024px) {
                .grid-layout {
                    grid-template-columns: 1fr;
                }
                .form-row {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Content Parameters Manager</h1>
            <div class="nav-buttons">
                <a href="/" class="nav-button">🏠 Home</a>
                <a href="/library" class="nav-button">📖 Library</a>
            </div>
        </div>

        <div class="content">
            <!-- Tab Navigation -->
            <div class="tabs">
                <button class="tab active" onclick="showTab('genres')">📖 Genre Hierarchy</button>
                <button class="tab" onclick="showTab('tropes')">🎭 Tropes & Tones</button>
                <button class="tab" onclick="showTab('audiences')">👥 Target Audiences</button>
            </div>

            <!-- Genre Hierarchy Tab -->
            <div id="genres" class="tab-content active">
                <div class="grid-layout">
                    <!-- Genre Creation -->
                    <div class="section">
                        <h3>📚 Create Genre</h3>
                        <div id="genreMessage"></div>
                        
                        <div class="form-group">
                            <label>Genre Name</label>
                            <input type="text" id="genreName" placeholder="e.g., Fantasy, Science Fiction, Romance">
                        </div>
                        
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="genreDescription" placeholder="Describe this genre and its characteristics..."></textarea>
                        </div>
                        
                        <button class="btn" onclick="createGenre()">Add Genre</button>
                        
                        <div class="items-list">
                            <h4>Existing Genres</h4>
                            <div id="genresList" class="loading">Loading genres...</div>
                        </div>
                    </div>

                    <!-- Subgenre Creation -->
                    <div class="section">
                        <h3>📑 Create Subgenre</h3>
                        <div id="subgenreMessage"></div>
                        
                        <div class="form-group">
                            <label>Parent Genre</label>
                            <select id="subgenreParent">
                                <option value="">Select parent genre...</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Subgenre Name</label>
                            <input type="text" id="subgenreName" placeholder="e.g., Epic Fantasy, Urban Fantasy">
                        </div>
                        
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="subgenreDescription" placeholder="Describe this subgenre..."></textarea>
                        </div>
                        
                        <button class="btn" onclick="createSubgenre()">Add Subgenre</button>
                        
                        <div class="items-list">
                            <h4>Existing Subgenres</h4>
                            <div id="subgenresList" class="loading">Loading subgenres...</div>
                        </div>
                    </div>
                </div>

                <!-- Microgenre Creation -->
                <div class="section">
                    <h3>🔬 Create Microgenre</h3>
                    <div class="grid-layout">
                        <div>
                            <div id="microgenreMessage"></div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Parent Genre</label>
                                    <select id="microgenreParentGenre" onchange="loadSubgenresForMicro()">
                                        <option value="">Select parent genre...</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Parent Subgenre</label>
                                    <select id="microgenreParent">
                                        <option value="">Select parent subgenre...</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>Microgenre Name</label>
                                <input type="text" id="microgenreName" placeholder="e.g., Cozy Mystery, Space Opera">
                            </div>
                            
                            <div class="form-group">
                                <label>Description</label>
                                <textarea id="microgenreDescription" placeholder="Describe this microgenre..."></textarea>
                            </div>
                            
                            <button class="btn" onclick="createMicrogenre()">Add Microgenre</button>
                        </div>
                        
                        <div class="items-list">
                            <h4>Existing Microgenres</h4>
                            <div id="microgenresList" class="loading">Loading microgenres...</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tropes & Tones Tab -->
            <div id="tropes" class="tab-content">
                <div class="grid-layout">
                    <!-- Tropes Section -->
                    <div class="section">
                        <h3>🎭 Create Trope</h3>
                        <div id="tropeMessage"></div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Trope Name</label>
                                <input type="text" id="tropeName" placeholder="e.g., Chosen One, Enemies to Lovers">
                            </div>
                            <div class="form-group">
                                <label>Category</label>
                                <select id="tropeCategory">
                                    <option value="Plot">Plot</option>
                                    <option value="Character">Character</option>
                                    <option value="Setting">Setting</option>
                                    <option value="Relationship">Relationship</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="tropeDescription" placeholder="Describe this trope and how it's used..."></textarea>
                        </div>
                        
                        <button class="btn" onclick="createTrope()">Add Trope</button>
                        
                        <div class="items-list">
                            <h4>Existing Tropes</h4>
                            <div id="tropesList" class="loading">Loading tropes...</div>
                        </div>
                    </div>

                    <!-- Tones Section -->
                    <div class="section">
                        <h3>🎵 Create Tone</h3>
                        <div id="toneMessage"></div>
                        
                        <div class="form-group">
                            <label>Tone Name</label>
                            <input type="text" id="toneName" placeholder="e.g., Dark, Humorous, Melancholic">
                        </div>
                        
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="toneDescription" placeholder="Describe the mood and atmosphere this tone creates..."></textarea>
                        </div>
                        
                        <button class="btn" onclick="createTone()">Add Tone</button>
                        
                        <div class="items-list">
                            <h4>Existing Tones</h4>
                            <div id="tonesList" class="loading">Loading tones...</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Target Audiences Tab -->
            <div id="audiences" class="tab-content">
                <div class="grid-layout">
                    <div class="section">
                        <h3>👥 Create Target Audience</h3>
                        <div id="audienceMessage"></div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Age Group</label>
                                <select id="audienceAgeGroup">
                                    <option value="Children">Children (5-12)</option>
                                    <option value="Middle Grade">Middle Grade (8-12)</option>
                                    <option value="Young Adult">Young Adult (13-17)</option>
                                    <option value="New Adult">New Adult (18-25)</option>
                                    <option value="Adult" selected>Adult (25+)</option>
                                    <option value="Senior">Senior (65+)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Gender</label>
                                <select id="audienceGender">
                                    <option value="All" selected>All Genders</option>
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                    <option value="Non-binary">Non-binary</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label>Sexual Orientation</label>
                            <select id="audienceOrientation">
                                <option value="All" selected>All Orientations</option>
                                <option value="Heterosexual">Heterosexual</option>
                                <option value="LGBTQ+">LGBTQ+</option>
                                <option value="Gay">Gay</option>
                                <option value="Lesbian">Lesbian</option>
                                <option value="Bisexual">Bisexual</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Interests (comma-separated)</label>
                            <input type="text" id="audienceInterests" placeholder="e.g., Adventure, Romance, Technology, Gaming">
                        </div>
                        
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="audienceDescription" placeholder="Describe this target audience, their preferences, and characteristics..."></textarea>
                        </div>
                        
                        <button class="btn" onclick="createAudience()">Add Target Audience</button>
                    </div>
                    
                    <div class="items-list">
                        <h3>Existing Target Audiences</h3>
                        <div id="audiencesList" class="loading">Loading audiences...</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Global data storage
            let allGenres = [];
            let allSubgenres = [];
            let allMicrogenres = [];
            let allTropes = [];
            let allTones = [];
            let allAudiences = [];

            // Tab management
            function showTab(tabName) {
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all tabs
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                
                // Mark selected tab as active
                event.target.classList.add('active');
            }

            // Load all data on page load
            async function loadAllData() {
                await loadGenres();
                await loadSubgenres();
                await loadMicrogenres();
                await loadTropes();
                await loadTones();
                await loadAudiences();
                populateDropdowns();
            }

            // API calls
            async function loadGenres() {
                try {
                    const response = await fetch('/api/genres');
                    const data = await response.json();
                    if (data.success) {
                        allGenres = data.genres;
                        displayGenres();
                    }
                } catch (error) {
                    console.error('Error loading genres:', error);
                }
            }

            async function loadSubgenres() {
                try {
                    const response = await fetch('/api/genres');
                    const data = await response.json();
                    if (data.success) {
                        allSubgenres = data.subgenres || [];
                        displaySubgenres();
                    }
                } catch (error) {
                    console.error('Error loading subgenres:', error);
                }
            }

            async function loadMicrogenres() {
                try {
                    const response = await fetch('/api/genres');
                    const data = await response.json();
                    if (data.success) {
                        allMicrogenres = data.microgenres || [];
                        displayMicrogenres();
                    }
                } catch (error) {
                    console.error('Error loading microgenres:', error);
                }
            }

            async function loadTropes() {
                try {
                    const response = await fetch('/api/tropes');
                    const data = await response.json();
                    if (data.success) {
                        allTropes = data.tropes;
                        displayTropes();
                    }
                } catch (error) {
                    console.error('Error loading tropes:', error);
                }
            }

            async function loadTones() {
                try {
                    const response = await fetch('/api/tones');
                    const data = await response.json();
                    if (data.success) {
                        allTones = data.tones;
                        displayTones();
                    }
                } catch (error) {
                    console.error('Error loading tones:', error);
                }
            }

            async function loadAudiences() {
                try {
                    const response = await fetch('/api/target-audiences');
                    const data = await response.json();
                    if (data.success) {
                        allAudiences = data.audiences;
                        displayAudiences();
                    }
                } catch (error) {
                    console.error('Error loading audiences:', error);
                }
            }

            // Display functions
            function displayGenres() {
                const container = document.getElementById('genresList');
                if (allGenres.length === 0) {
                    container.innerHTML = '<div class="item-card">No genres found</div>';
                    return;
                }
                
                container.innerHTML = allGenres.map(genre => `
                    <div class="item-card">
                        <div class="item-header">${genre.name}</div>
                        <div class="item-description">${genre.description || 'No description'}</div>
                        ${getSubgenresForGenre(genre.id)}
                    </div>
                `).join('');
            }

            function getSubgenresForGenre(genreId) {
                const subgenres = allSubgenres.filter(sub => sub.genre_id === genreId);
                if (subgenres.length === 0) return '';
                
                return `<div class="hierarchy-tree">
                    <strong>Subgenres:</strong><br>
                    ${subgenres.map(sub => `
                        <div style="margin: 5px 0;">
                            <strong>${sub.name}</strong>
                            ${sub.description ? `<br><em style="color: #666; font-size: 12px;">${sub.description}</em>` : ''}
                            ${getMicrogenresForSubgenre(sub.id)}
                        </div>
                    `).join('')}
                </div>`;
            }

            function getMicrogenresForSubgenre(subgenreId) {
                const microgenres = allMicrogenres.filter(micro => micro.subgenre_id === subgenreId);
                if (microgenres.length === 0) return '';
                
                return `<div style="margin-left: 15px; margin-top: 5px;">
                    <strong style="font-size: 12px;">Microgenres:</strong>
                    ${microgenres.map(micro => `<span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin: 2px;">${micro.name}</span>`).join(' ')}
                </div>`;
            }

            function displaySubgenres() {
                const container = document.getElementById('subgenresList');
                if (allSubgenres.length === 0) {
                    container.innerHTML = '<div class="item-card">No subgenres found</div>';
                    return;
                }
                
                container.innerHTML = allSubgenres.map(subgenre => {
                    const parentGenre = allGenres.find(g => g.id === subgenre.genre_id);
                    return `
                        <div class="item-card">
                            <div class="item-header">${subgenre.name}</div>
                            <div class="item-meta">Parent: ${parentGenre ? parentGenre.name : 'Unknown'}</div>
                            <div class="item-description">${subgenre.description || 'No description'}</div>
                        </div>
                    `;
                }).join('');
            }

            function displayMicrogenres() {
                const container = document.getElementById('microgenresList');
                if (allMicrogenres.length === 0) {
                    container.innerHTML = '<div class="item-card">No microgenres found</div>';
                    return;
                }
                
                container.innerHTML = allMicrogenres.map(microgenre => {
                    const parentSubgenre = allSubgenres.find(s => s.id === microgenre.subgenre_id);
                    const parentGenre = parentSubgenre ? allGenres.find(g => g.id === parentSubgenre.genre_id) : null;
                    return `
                        <div class="item-card">
                            <div class="item-header">${microgenre.name}</div>
                            <div class="item-meta">Path: ${parentGenre ? parentGenre.name : 'Unknown'} > ${parentSubgenre ? parentSubgenre.name : 'Unknown'}</div>
                            <div class="item-description">${microgenre.description || 'No description'}</div>
                        </div>
                    `;
                }).join('');
            }

            function displayTropes() {
                const container = document.getElementById('tropesList');
                if (allTropes.length === 0) {
                    container.innerHTML = '<div class="item-card">No tropes found</div>';
                    return;
                }
                
                container.innerHTML = allTropes.map(trope => `
                    <div class="item-card">
                        <div class="item-header">${trope.name}</div>
                        <div class="item-meta">Category: ${trope.category}</div>
                        <div class="item-description">${trope.description || 'No description'}</div>
                    </div>
                `).join('');
            }

            function displayTones() {
                const container = document.getElementById('tonesList');
                if (allTones.length === 0) {
                    container.innerHTML = '<div class="item-card">No tones found</div>';
                    return;
                }
                
                container.innerHTML = allTones.map(tone => `
                    <div class="item-card">
                        <div class="item-header">${tone.name}</div>
                        <div class="item-description">${tone.description || 'No description'}</div>
                    </div>
                `).join('');
            }

            function displayAudiences() {
                const container = document.getElementById('audiencesList');
                if (allAudiences.length === 0) {
                    container.innerHTML = '<div class="item-card">No target audiences found</div>';
                    return;
                }
                
                container.innerHTML = allAudiences.map(audience => `
                    <div class="item-card">
                        <div class="item-header">${audience.age_group} - ${audience.gender} - ${audience.sexual_orientation}</div>
                        <div class="item-description">${audience.description || 'No description'}</div>
                        ${audience.interests && audience.interests.length > 0 ? 
                            `<div style="margin-top: 5px;"><strong>Interests:</strong> ${audience.interests.join(', ')}</div>` : ''
                        }
                    </div>
                `).join('');
            }

            // Populate dropdowns
            function populateDropdowns() {
                // Populate subgenre parent dropdown
                const subgenreParent = document.getElementById('subgenreParent');
                subgenreParent.innerHTML = '<option value="">Select parent genre...</option>' +
                    allGenres.map(genre => `<option value="${genre.id}">${genre.name}</option>`).join('');
                
                // Populate microgenre parent genre dropdown
                const microgenreParentGenre = document.getElementById('microgenreParentGenre');
                microgenreParentGenre.innerHTML = '<option value="">Select parent genre...</option>' +
                    allGenres.map(genre => `<option value="${genre.id}">${genre.name}</option>`).join('');
            }

            function loadSubgenresForMicro() {
                const genreId = document.getElementById('microgenreParentGenre').value;
                const subgenreSelect = document.getElementById('microgenreParent');
                
                if (!genreId) {
                    subgenreSelect.innerHTML = '<option value="">Select parent subgenre...</option>';
                    return;
                }
                
                const subgenres = allSubgenres.filter(sub => sub.genre_id === genreId);
                subgenreSelect.innerHTML = '<option value="">Select parent subgenre...</option>' +
                    subgenres.map(sub => `<option value="${sub.id}">${sub.name}</option>`).join('');
            }

            // Create functions
            async function createGenre() {
                const name = document.getElementById('genreName').value.trim();
                const description = document.getElementById('genreDescription').value.trim();
                
                if (!name) {
                    showMessage('genreMessage', 'Genre name is required', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/genres', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, description })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showMessage('genreMessage', 'Genre created successfully!', 'success');
                        document.getElementById('genreName').value = '';
                        document.getElementById('genreDescription').value = '';
                        await loadGenres();
                        populateDropdowns();
                    } else {
                        showMessage('genreMessage', data.error || 'Failed to create genre', 'error');
                    }
                } catch (error) {
                    showMessage('genreMessage', 'Error creating genre', 'error');
                }
            }

            async function createSubgenre() {
                const genreId = document.getElementById('subgenreParent').value;
                const name = document.getElementById('subgenreName').value.trim();
                const description = document.getElementById('subgenreDescription').value.trim();
                
                if (!genreId || !name) {
                    showMessage('subgenreMessage', 'Parent genre and subgenre name are required', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/subgenres', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ genre_id: genreId, name, description })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showMessage('subgenreMessage', 'Subgenre created successfully!', 'success');
                        document.getElementById('subgenreName').value = '';
                        document.getElementById('subgenreDescription').value = '';
                        await loadSubgenres();
                        await loadGenres(); // Refresh to show hierarchy
                    } else {
                        showMessage('subgenreMessage', data.error || 'Failed to create subgenre', 'error');
                    }
                } catch (error) {
                    showMessage('subgenreMessage', 'Error creating subgenre', 'error');
                }
            }

            async function createMicrogenre() {
                const subgenreId = document.getElementById('microgenreParent').value;
                const name = document.getElementById('microgenreName').value.trim();
                const description = document.getElementById('microgenreDescription').value.trim();
                
                if (!subgenreId || !name) {
                    showMessage('microgenreMessage', 'Parent subgenre and microgenre name are required', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/microgenres', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ subgenre_id: subgenreId, name, description })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showMessage('microgenreMessage', 'Microgenre created successfully!', 'success');
                        document.getElementById('microgenreName').value = '';
                        document.getElementById('microgenreDescription').value = '';
                        await loadMicrogenres();
                        await loadGenres(); // Refresh to show hierarchy
                    } else {
                        showMessage('microgenreMessage', data.error || 'Failed to create microgenre', 'error');
                    }
                } catch (error) {
                    showMessage('microgenreMessage', 'Error creating microgenre', 'error');
                }
            }

            async function createTrope() {
                const name = document.getElementById('tropeName').value.trim();
                const category = document.getElementById('tropeCategory').value;
                const description = document.getElementById('tropeDescription').value.trim();
                
                if (!name) {
                    showMessage('tropeMessage', 'Trope name is required', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/tropes', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, category, description })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showMessage('tropeMessage', 'Trope created successfully!', 'success');
                        document.getElementById('tropeName').value = '';
                        document.getElementById('tropeDescription').value = '';
                        await loadTropes();
                    } else {
                        showMessage('tropeMessage', data.error || 'Failed to create trope', 'error');
                    }
                } catch (error) {
                    showMessage('tropeMessage', 'Error creating trope', 'error');
                }
            }

            async function createTone() {
                const name = document.getElementById('toneName').value.trim();
                const description = document.getElementById('toneDescription').value.trim();
                
                if (!name) {
                    showMessage('toneMessage', 'Tone name is required', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/tones', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, description })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showMessage('toneMessage', 'Tone created successfully!', 'success');
                        document.getElementById('toneName').value = '';
                        document.getElementById('toneDescription').value = '';
                        await loadTones();
                    } else {
                        showMessage('toneMessage', data.error || 'Failed to create tone', 'error');
                    }
                } catch (error) {
                    showMessage('toneMessage', 'Error creating tone', 'error');
                }
            }

            async function createAudience() {
                const ageGroup = document.getElementById('audienceAgeGroup').value;
                const gender = document.getElementById('audienceGender').value;
                const orientation = document.getElementById('audienceOrientation').value;
                const interests = document.getElementById('audienceInterests').value.trim();
                const description = document.getElementById('audienceDescription').value.trim();
                
                const interestsArray = interests ? interests.split(',').map(i => i.trim()).filter(i => i.length > 0) : [];
                
                try {
                    const response = await fetch('/api/target-audiences', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            age_group: ageGroup,
                            gender: gender,
                            sexual_orientation: orientation,
                            interests: interestsArray,
                            description: description
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        showMessage('audienceMessage', 'Target audience created successfully!', 'success');
                        document.getElementById('audienceInterests').value = '';
                        document.getElementById('audienceDescription').value = '';
                        await loadAudiences();
                    } else {
                        showMessage('audienceMessage', data.error || 'Failed to create target audience', 'error');
                    }
                } catch (error) {
                    showMessage('audienceMessage', 'Error creating target audience', 'error');
                }
            }

            // Utility function for messages
            function showMessage(elementId, message, type) {
                const element = document.getElementById(elementId);
                element.innerHTML = `<div class="${type}">${message}</div>`;
                setTimeout(() => {
                    element.innerHTML = '';
                }, 5000);
            }

            // Load data when page loads
            window.onload = loadAllData;
        </script>
    </body>
    </html>
    """)

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
                    
                    ${plot.author_id ? (() => {
                        const author = allAuthors.find(a => a.id === plot.author_id);
                        return author ? `
                            <div class="modal-section">
                                <h3>Author</h3>
                                <div style="border: 1px solid #007bff; border-radius: 5px; padding: 15px; background-color: #f8f9ff;">
                                    <div style="font-weight: bold; color: #007bff; margin-bottom: 5px;">${author.author_name}</div>
                                    ${author.pen_name ? `<div style="font-style: italic; color: #666; margin-bottom: 8px;">Pen Name: ${author.pen_name}</div>` : ''}
                                    <div style="color: #555; font-size: 14px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">${author.biography}</div>
                                </div>
                            </div>
                        ` : '';
                    })() : ''}
                    
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
                            ${plot.author_id ? `
                                <div class="modal-meta-item">
                                    <div class="modal-meta-label">Author ID</div>
                                    <div class="modal-meta-value">${plot.author_id}</div>
                                </div>
                            ` : ''}
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
                
                // Find all plots by this author
                const authorPlots = allPlots.filter(plot => plot.author_id === author.id);
                
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
                            <div class="modal-meta-item">
                                <div class="modal-meta-label">Number of Plots</div>
                                <div class="modal-meta-value">${authorPlots.length}</div>
                            </div>
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
                    
                    ${authorPlots.length > 0 ? `
                        <div class="modal-section">
                            <h3>Plots by this Author</h3>
                            <div style="max-height: 300px; overflow-y: auto;">
                                ${authorPlots.map(plot => `
                                    <div style="border: 1px solid #eee; border-radius: 5px; padding: 15px; margin-bottom: 10px; background-color: #f9f9f9;">
                                        <div style="font-weight: bold; color: #007bff; margin-bottom: 5px;">${plot.title}</div>
                                        <div style="color: #666; font-size: 14px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${plot.plot_summary}</div>
                                        <div style="margin-top: 8px; display: flex; gap: 5px; flex-wrap: wrap;">
                                            ${plot.genre_name ? `<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${plot.genre_name}</span>` : ''}
                                            ${plot.subgenre_name ? `<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${plot.subgenre_name}</span>` : ''}
                                            ${plot.tone_name ? `<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${plot.tone_name}</span>` : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
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
async def create_genre(data: dict):
    """Create a new genre"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("genres").insert({
            "name": data["name"],
            "description": data.get("description", "")
        }).execute()
        
        return {"success": True, "genre": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/subgenres")
async def create_subgenre(data: dict):
    """Create a new subgenre"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("subgenres").insert({
            "genre_id": data["genre_id"],
            "name": data["name"],
            "description": data.get("description", "")
        }).execute()
        
        return {"success": True, "subgenre": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

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
async def create_target_audience(data: dict):
    """Create a new target audience"""
    if not SUPABASE_ENABLED:
        return {"error": "Supabase not configured"}
    
    try:
        response = supabase_service.client.table("target_audiences").insert({
            "age_group": data["age_group"],
            "gender": data.get("gender", "All"),
            "sexual_orientation": data.get("sexual_orientation", "All")
        }).execute()
        
        return {"success": True, "audience": response.data[0]}
    except Exception as e:
        return {"error": str(e)}

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