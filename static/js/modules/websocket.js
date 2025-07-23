/**
 * WebSocket Module - Handles WebSocket connections and message management
 * Extracted from monolithic chat.js for better separation of concerns
 */

class WebSocketService {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.userId = "user_" + Math.random().toString(36).substr(2, 9);
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = new Map();
        this.connectionStateHandlers = [];
    }

    /**
     * Register a message handler for specific message types
     */
    onMessage(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type).push(handler);
    }

    /**
     * Register connection state change handlers
     */
    onConnectionStateChange(handler) {
        this.connectionStateHandlers.push(handler);
    }

    /**
     * Notify connection state handlers
     */
    notifyConnectionState(state, message = '') {
        this.connectionStateHandlers.forEach(handler => {
            try {
                handler(state, message);
            } catch (error) {
                console.error('Error in connection state handler:', error);
            }
        });
    }

    /**
     * Connect to WebSocket server
     */
    connect(serverUrl = null) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.warn('WebSocket already connected');
            return;
        }

        this.sessionId = "session_" + Math.random().toString(36).substr(2, 9);
        const wsUrl = serverUrl || `ws://localhost:8000/ws/${this.sessionId}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.handleConnectionError(error);
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.notifyConnectionState('connected', 'Connected to server');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
                this.handleMessage({
                    type: 'error',
                    content: 'Failed to parse server message'
                });
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.notifyConnectionState('disconnected', 'Disconnected from server');
            
            // Attempt reconnection if not a normal closure
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.attemptReconnection();
            }
        };

        this.ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            this.handleConnectionError(event);
        };
    }

    /**
     * Handle incoming messages and route to appropriate handlers
     */
    handleMessage(data) {
        const messageType = data.type || 'unknown';
        
        // Call registered handlers for this message type
        if (this.messageHandlers.has(messageType)) {
            this.messageHandlers.get(messageType).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${messageType} handler:`, error);
                }
            });
        }

        // Call general message handlers
        if (this.messageHandlers.has('*')) {
            this.messageHandlers.get('*').forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error('Error in general message handler:', error);
                }
            });
        }
    }

    /**
     * Send message through WebSocket
     */
    sendMessage(message, context = null) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            this.notifyConnectionState('error', 'Cannot send message - not connected');
            return false;
        }

        try {
            const messageData = {
                type: 'message',
                content: message,
                user_id: this.userId,
                timestamp: new Date().toISOString()
            };

            // Add context if provided
            if (context) {
                messageData.context = context;
            }

            this.ws.send(JSON.stringify(messageData));
            return true;
        } catch (error) {
            console.error('Error sending message:', error);
            return false;
        }
    }

    /**
     * Send structured data through WebSocket
     */
    sendData(type, data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return false;
        }

        try {
            const messageData = {
                type: type,
                data: data,
                user_id: this.userId,
                timestamp: new Date().toISOString()
            };

            this.ws.send(JSON.stringify(messageData));
            return true;
        } catch (error) {
            console.error('Error sending data:', error);
            return false;
        }
    }

    /**
     * Handle connection errors
     */
    handleConnectionError(error) {
        this.notifyConnectionState('error', 'Connection error occurred');
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.notifyConnectionState('failed', 'Failed to reconnect after multiple attempts');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
        this.notifyConnectionState('reconnecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close(1000, 'Normal closure');
            this.ws = null;
        }
        this.sessionId = null;
    }

    /**
     * Get connection state
     */
    getConnectionState() {
        if (!this.ws) return 'disconnected';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'connecting';
            case WebSocket.OPEN:
                return 'connected';
            case WebSocket.CLOSING:
                return 'closing';
            case WebSocket.CLOSED:
                return 'disconnected';
            default:
                return 'unknown';
        }
    }

    /**
     * Get session info
     */
    getSessionInfo() {
        return {
            sessionId: this.sessionId,
            userId: this.userId,
            connectionState: this.getConnectionState(),
            reconnectAttempts: this.reconnectAttempts
        };
    }

    /**
     * Format message text (utility function)
     */
    static formatMessage(text) {
        if (!text) return '';
        
        // Convert numbered lists to HTML
        text = text.replace(/^(\d+\.\s\*\*)(.+?)(\*\*)/gm, '<strong>$1$2</strong>');
        text = text.replace(/^(\d+\.\s)(.+?)$/gm, '<strong>$1</strong>$2');
        
        // Convert bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
}

// Create singleton instance
const webSocketService = new WebSocketService();

// Export for ES6 modules and global access
if (typeof window !== 'undefined') {
    window.webSocketService = webSocketService;
}

export default webSocketService;