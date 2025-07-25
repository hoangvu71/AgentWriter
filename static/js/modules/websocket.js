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
                
                // Validate and sanitize incoming message data
                const validatedData = this.validateIncomingMessage(data);
                if (validatedData) {
                    this.handleMessage(validatedData);
                } else {
                    console.warn('Received invalid message data, ignoring');
                }
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
     * Send message through WebSocket with validation
     */
    sendMessage(message, context = null) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            this.notifyConnectionState('error', 'Cannot send message - not connected');
            return false;
        }

        // Validate and sanitize message before sending
        const validatedMessage = this.validateOutgoingMessage(message);
        if (!validatedMessage) {
            console.error('Invalid message content');
            return false;
        }

        try {
            const messageData = {
                type: 'message',
                content: validatedMessage,
                user_id: this.userId,
                timestamp: new Date().toISOString()
            };

            // Validate and add context if provided
            if (context) {
                const validatedContext = this.validateContext(context);
                if (validatedContext) {
                    messageData.context = validatedContext;
                }
            }

            this.ws.send(JSON.stringify(messageData));
            return true;
        } catch (error) {
            console.error('Error sending message:', error);
            return false;
        }
    }

    /**
     * Send structured data through WebSocket with validation
     */
    sendData(type, data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return false;
        }

        // Validate message type
        const validatedType = this.validateMessageType(type);
        if (!validatedType) {
            console.error('Invalid message type');
            return false;
        }

        try {
            const messageData = {
                type: validatedType,
                data: data, // Data validation depends on type
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
     * Validate incoming WebSocket message
     */
    validateIncomingMessage(data) {
        if (window.securityService) {
            return window.securityService.validateWebSocketMessage(data);
        }
        
        // Basic validation fallback
        if (!data || typeof data !== 'object') {
            return null;
        }
        
        const validated = {};
        
        if (data.type && typeof data.type === 'string') {
            validated.type = data.type.replace(/[^a-zA-Z0-9_-]/g, '');
        }
        
        if (data.content && typeof data.content === 'string') {
            validated.content = data.content.substring(0, 10000); // Limit content length
        }
        
        return validated;
    }

    /**
     * Validate outgoing message content
     */
    validateOutgoingMessage(message) {
        if (window.securityService) {
            return window.securityService.validateInput(message, 'message');
        }
        
        // Basic validation fallback
        if (!message || typeof message !== 'string') {
            return '';
        }
        
        // Basic length check and dangerous pattern removal
        if (message.length > 2000) {
            message = message.substring(0, 2000);
        }
        
        // Remove potentially dangerous patterns
        return message.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                     .replace(/javascript:/gi, '')
                     .replace(/on\w+\s*=/gi, '');
    }

    /**
     * Validate context object
     */
    validateContext(context) {
        if (window.securityService) {
            return window.securityService.validateContext(context);
        }
        
        // Basic validation fallback
        if (!context || typeof context !== 'object') {
            return null;
        }
        
        // Only allow specific known context properties
        const allowedKeys = ['selectedGenre', 'selectedSubgenre', 'selectedMicrogenre', 'selectedTrope', 'selectedTone', 'selectedAudience', 'selectedContent'];
        const validated = {};
        
        allowedKeys.forEach(key => {
            if (context[key]) {
                validated[key] = context[key];
            }
        });
        
        return validated;
    }

    /**
     * Validate message type
     */
    validateMessageType(type) {
        if (!type || typeof type !== 'string') {
            return null;
        }
        
        // Only allow alphanumeric characters, underscores, and hyphens
        const cleanType = type.replace(/[^a-zA-Z0-9_-]/g, '');
        
        // Limit length
        return cleanType.substring(0, 50);
    }

    /**
     * Format message text (utility function)
     * @deprecated Use securityService.formatMessageSafely() instead
     */
    static formatMessage(text) {
        console.warn('WebSocketService.formatMessage is deprecated, use securityService.formatMessageSafely() instead');
        
        if (window.securityService) {
            return window.securityService.formatMessageSafely(text);
        }
        
        // Safe fallback
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create singleton instance
const webSocketService = new WebSocketService();

// Export for global access only (not using ES6 modules)
if (typeof window !== 'undefined') {
    window.webSocketService = webSocketService;
}