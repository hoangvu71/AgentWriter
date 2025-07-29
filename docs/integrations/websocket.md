# WebSocket Integration

Comprehensive guide for BooksWriter's real-time WebSocket communication system enabling streaming responses and live updates.

## Overview

BooksWriter uses WebSocket connections to provide:
- **Real-time streaming responses** from AI agents
- **Live status updates** during multi-agent workflows
- **Session persistence** across browser refreshes
- **Error handling** with automatic reconnection
- **Multi-user support** with isolated sessions

## Connection Setup

### WebSocket Endpoint
```
WebSocket: ws://localhost:8000/ws/{session_id}
```

**Parameters**:
- `session_id` (string): Unique identifier for the user session

### JavaScript Client Example
```javascript
class BooksWriterWebSocket {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect() {
        const wsUrl = `ws://localhost:8000/ws/${this.sessionId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = (event) => {
            console.log('Connected to BooksWriter');
            this.reconnectAttempts = 0;
            this.onConnected(event);
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = (event) => {
            console.log('Disconnected from BooksWriter');
            this.handleReconnection();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.onError(error);
        };
    }

    sendMessage(content, userId = null) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'message',
                content: content,
                user_id: userId || 'anonymous',
                timestamp: new Date().toISOString()
            };
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'stream_chunk':
                this.onStreamChunk(data);
                break;
            case 'agent_switch':
                this.onAgentSwitch(data);
                break;
            case 'tool_execution':
                this.onToolExecution(data);
                break;
            case 'error':
                this.onError(data);
                break;
            case 'completion':
                this.onCompletion(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    // Event handlers (override in implementation)
    onConnected(event) {}
    onStreamChunk(data) {}
    onAgentSwitch(data) {}
    onToolExecution(data) {}
    onError(error) {}
    onCompletion(data) {}
}
```

## Message Protocol

### Client to Server Messages

#### Standard Message Format
```json
{
    "type": "message",
    "content": "Create a fantasy novel with dragons and magic",
    "user_id": "user123",
    "timestamp": "2025-01-28T10:30:00Z",
    "options": {
        "stream": true,
        "model": "gemini-2.0-flash-exp"
    }
}
```

#### Message Types
- **`message`**: Standard user message for processing
- **`ping`**: Keep-alive ping message
- **`model_switch`**: Request to switch AI model
- **`session_restore`**: Restore previous session state

### Server to Client Messages

#### Streaming Response Chunk
```json
{
    "type": "stream_chunk",
    "content": "I'll help you create a fantasy novel...",
    "agent": "OrchestratorAgent",
    "chunk_id": 1,
    "total_chunks": null,
    "timestamp": "2025-01-28T10:30:01Z"
}
```

#### Agent Switch Notification
```json
{
    "type": "agent_switch",
    "from_agent": "OrchestratorAgent",
    "to_agent": "PlotGeneratorAgent",
    "reason": "Routing request to plot generation specialist",
    "timestamp": "2025-01-28T10:30:02Z"
}
```

#### Tool Execution Notification
```json
{
    "type": "tool_execution",
    "tool_name": "save_plot",
    "status": "executing",
    "message": "Saving plot to database...",
    "progress": 0.5,
    "timestamp": "2025-01-28T10:30:05Z"
}
```

#### Error Message
```json
{
    "type": "error",
    "error_code": "AGENT_TIMEOUT",
    "message": "Agent processing timed out after 30 seconds",
    "details": {
        "agent": "PlotGeneratorAgent",
        "timeout_duration": 30000
    },
    "timestamp": "2025-01-28T10:30:30Z"
}
```

#### Completion Notification
```json
{
    "type": "completion",
    "message": "Plot generation completed successfully",
    "results": {
        "plot_id": "plot-uuid-123",
        "title": "The Dragon's Last Stand",
        "agents_used": ["OrchestratorAgent", "PlotGeneratorAgent"]
    },
    "timestamp": "2025-01-28T10:30:15Z"
}
```

## Implementation Examples

### Basic Chat Interface
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BooksWriter Chat</title>
    <style>
        #messages { height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #e3f2fd; text-align: right; }
        .agent-message { background: #f1f8e9; }
        .error-message { background: #ffebee; color: #c62828; }
        .status-message { background: #fff3e0; font-style: italic; }
    </style>
</head>
<body>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Enter your message..." style="width: 70%;">
    <button onclick="sendMessage()">Send</button>
    <button onclick="clearMessages()">Clear</button>

    <script>
        const sessionId = 'session-' + Math.random().toString(36).substr(2, 9);
        const ws = new BooksWriterWebSocket(sessionId);
        
        ws.onConnected = () => {
            addMessage('Connected to BooksWriter', 'status-message');
        };

        ws.onStreamChunk = (data) => {
            appendToLastMessage(data.content);
        };

        ws.onAgentSwitch = (data) => {
            addMessage(`→ Switching to ${data.to_agent}`, 'status-message');
        };

        ws.onToolExecution = (data) => {
            addMessage(`🔧 ${data.message}`, 'status-message');
        };

        ws.onError = (error) => {
            addMessage(`Error: ${error.message}`, 'error-message');
        };

        ws.onCompletion = (data) => {
            addMessage('✅ Complete', 'status-message');
        };

        ws.connect();

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const content = input.value.trim();
            
            if (content) {
                addMessage(content, 'user-message');
                ws.sendMessage(content);
                input.value = '';
                
                // Prepare for streaming response
                addMessage('', 'agent-message', 'streaming-response');
            }
        }

        function addMessage(content, className, id = null) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${className}`;
            messageDiv.textContent = content;
            
            if (id) {
                messageDiv.id = id;
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function appendToLastMessage(content) {
            const streamingResponse = document.getElementById('streaming-response');
            if (streamingResponse) {
                streamingResponse.textContent += content;
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            }
        }

        function clearMessages() {
            document.getElementById('messages').innerHTML = '';
        }

        // Send message on Enter key
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

### Advanced React Integration
```jsx
import React, { useState, useEffect, useRef } from 'react';

const BooksWriterChat = () => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [currentAgent, setCurrentAgent] = useState(null);
    const wsRef = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        const sessionId = `session-${Date.now()}`;
        const ws = new BooksWriterWebSocket(sessionId);
        
        ws.onConnected = () => {
            setIsConnected(true);
            addMessage('Connected to BooksWriter', 'system');
        };

        ws.onStreamChunk = (data) => {
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                
                if (lastMessage && lastMessage.type === 'assistant' && lastMessage.streaming) {
                    lastMessage.content += data.content;
                } else {
                    newMessages.push({
                        id: Date.now(),
                        type: 'assistant',
                        content: data.content,
                        agent: data.agent,
                        streaming: true,
                        timestamp: new Date()
                    });
                }
                return newMessages;
            });
        };

        ws.onAgentSwitch = (data) => {
            setCurrentAgent(data.to_agent);
            addMessage(`Switching to ${data.to_agent}`, 'system');
        };

        ws.onCompletion = (data) => {
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage && lastMessage.streaming) {
                    lastMessage.streaming = false;
                }
                return newMessages;
            });
            addMessage('Response complete', 'system');
        };

        ws.onError = (error) => {
            addMessage(`Error: ${error.message}`, 'error');
        };

        ws.connect();
        wsRef.current = ws;

        return () => {
            if (wsRef.current) {
                wsRef.current.ws.close();
            }
        };
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const addMessage = (content, type, agent = null) => {
        setMessages(prev => [...prev, {
            id: Date.now(),
            content,
            type,
            agent,
            timestamp: new Date(),
            streaming: false
        }]);
    };

    const sendMessage = () => {
        if (inputValue.trim() && wsRef.current && isConnected) {
            addMessage(inputValue, 'user');
            wsRef.current.sendMessage(inputValue);
            setInputValue('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>BooksWriter Chat</h2>
                <div className="status">
                    <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
                    {isConnected ? 'Connected' : 'Disconnected'}
                    {currentAgent && <span className="current-agent">• {currentAgent}</span>}
                </div>
            </div>
            
            <div className="messages-container">
                {messages.map(message => (
                    <div key={message.id} className={`message ${message.type}-message`}>
                        <div className="message-content">
                            {message.content}
                            {message.streaming && <span className="typing-indicator">▋</span>}
                        </div>
                        {message.agent && (
                            <div className="message-meta">
                                {message.agent} • {message.timestamp.toLocaleTimeString()}
                            </div>
                        )}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
            
            <div className="input-container">
                <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask BooksWriter to create plots, authors, worlds, or characters..."
                    rows={3}
                    disabled={!isConnected}
                />
                <button onClick={sendMessage} disabled={!isConnected || !inputValue.trim()}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default BooksWriterChat;
```

## Performance Optimization

### Connection Management
```javascript
class ConnectionManager {
    constructor() {
        this.connections = new Map();
        this.heartbeatInterval = 30000; // 30 seconds
        this.maxIdleTime = 300000; // 5 minutes
    }

    createConnection(sessionId) {
        const connection = new BooksWriterWebSocket(sessionId);
        this.connections.set(sessionId, {
            ws: connection,
            lastActivity: Date.now(),
            heartbeatTimer: null
        });
        
        this.startHeartbeat(sessionId);
        return connection;
    }

    startHeartbeat(sessionId) {
        const connection = this.connections.get(sessionId);
        if (connection) {
            connection.heartbeatTimer = setInterval(() => {
                if (Date.now() - connection.lastActivity > this.maxIdleTime) {
                    this.closeConnection(sessionId);
                } else {
                    connection.ws.sendMessage('ping');
                }
            }, this.heartbeatInterval);
        }
    }

    closeConnection(sessionId) {
        const connection = this.connections.get(sessionId);
        if (connection) {
            clearInterval(connection.heartbeatTimer);
            connection.ws.ws.close();
            this.connections.delete(sessionId);
        }
    }
}
```

### Message Batching
```javascript
class MessageBatcher {
    constructor(ws, batchSize = 10, flushInterval = 100) {
        this.ws = ws;
        this.batchSize = batchSize;
        this.flushInterval = flushInterval;
        this.messageQueue = [];
        this.flushTimer = null;
    }

    queueMessage(message) {
        this.messageQueue.push(message);
        
        if (this.messageQueue.length >= this.batchSize) {
            this.flush();
        } else if (!this.flushTimer) {
            this.flushTimer = setTimeout(() => this.flush(), this.flushInterval);
        }
    }

    flush() {
        if (this.messageQueue.length > 0) {
            const batch = {
                type: 'batch',
                messages: this.messageQueue.splice(0),
                timestamp: new Date().toISOString()
            };
            
            this.ws.send(JSON.stringify(batch));
        }
        
        if (this.flushTimer) {
            clearTimeout(this.flushTimer);
            this.flushTimer = null;
        }
    }
}
```

## Error Handling

### Connection Recovery
```javascript
class RobustWebSocket extends BooksWriterWebSocket {
    constructor(sessionId, options = {}) {
        super(sessionId);
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;
        this.backoffMultiplier = options.backoffMultiplier || 2;
        this.messageQueue = [];
        this.isReconnecting = false;
    }

    sendMessage(content, userId = null) {
        const message = {
            type: 'message',
            content: content,
            user_id: userId || 'anonymous',
            timestamp: new Date().toISOString()
        };

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            // Queue message for when connection is restored
            this.messageQueue.push(message);
            if (!this.isReconnecting) {
                this.handleReconnection();
            }
        }
    }

    handleReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.onMaxReconnectAttemptsReached();
            return;
        }

        this.isReconnecting = true;
        const delay = Math.min(
            this.reconnectDelay * Math.pow(this.backoffMultiplier, this.reconnectAttempts),
            this.maxReconnectDelay
        );

        setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
        }, delay);
    }

    onConnected(event) {
        super.onConnected(event);
        this.isReconnecting = false;
        
        // Send queued messages
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.ws.send(JSON.stringify(message));
        }
    }

    onMaxReconnectAttemptsReached() {
        console.error('Max reconnection attempts reached');
        this.onError({ message: 'Failed to reconnect after maximum attempts' });
    }
}
```

## Security Considerations

### Message Validation
```javascript
function validateMessage(data) {
    const requiredFields = ['type', 'content', 'timestamp'];
    const validTypes = ['message', 'ping', 'model_switch', 'session_restore'];
    
    // Check required fields
    for (const field of requiredFields) {
        if (!data.hasOwnProperty(field)) {
            throw new Error(`Missing required field: ${field}`);
        }
    }
    
    // Validate message type
    if (!validTypes.includes(data.type)) {
        throw new Error(`Invalid message type: ${data.type}`);
    }
    
    // Validate content length
    if (data.content && data.content.length > 10000) {
        throw new Error('Message content too long');
    }
    
    // Validate timestamp
    const timestamp = new Date(data.timestamp);
    if (isNaN(timestamp.getTime())) {
        throw new Error('Invalid timestamp format');
    }
    
    return true;
}
```

### Rate Limiting
```javascript
class RateLimiter {
    constructor(maxMessages = 60, windowMs = 60000) {
        this.maxMessages = maxMessages;
        this.windowMs = windowMs;
        this.sessions = new Map();
    }

    checkLimit(sessionId) {
        const now = Date.now();
        let sessionData = this.sessions.get(sessionId);
        
        if (!sessionData) {
            sessionData = { messages: [], windowStart: now };
            this.sessions.set(sessionId, sessionData);
        }
        
        // Remove old messages outside the window
        sessionData.messages = sessionData.messages.filter(
            timestamp => now - timestamp < this.windowMs
        );
        
        // Check if limit exceeded
        if (sessionData.messages.length >= this.maxMessages) {
            return false;
        }
        
        // Add current message
        sessionData.messages.push(now);
        return true;
    }
}
```

## Related Documentation

- **[API Reference](../reference/api.md)** - REST API endpoints
- **[Architecture Overview](../architecture/overview.md)** - System architecture
- **[Multi-Agent System](../architecture/agents.md)** - Agent coordination
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - WebSocket troubleshooting

---

*This integration guide provides comprehensive information for implementing and customizing WebSocket communication with BooksWriter.*