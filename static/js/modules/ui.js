/**
 * UI Components Module - Handles DOM manipulation and UI updates
 * Extracted from monolithic chat.js for better separation of concerns
 */

class UIManager {
    constructor() {
        this.elements = new Map();
        this.eventListeners = new Map();
    }

    /**
     * Cache DOM element for reuse
     */
    getElement(id) {
        if (!this.elements.has(id)) {
            const element = document.getElementById(id);
            if (element) {
                this.elements.set(id, element);
            } else {
                console.warn(`Element with ID '${id}' not found`);
                return null;
            }
        }
        return this.elements.get(id);
    }

    /**
     * Clear element cache (useful when DOM changes)
     */
    clearElementCache() {
        this.elements.clear();
    }

    /**
     * Safely set element content with security validation
     */
    setContent(elementId, content, isHTML = false) {
        const element = this.getElement(elementId);
        if (element) {
            if (isHTML) {
                // Use security service for safe HTML setting
                if (window.securityService) {
                    window.securityService.safeSetHTML(element, content);
                } else {
                    // Fallback to textContent if security service not available
                    console.warn('Security service not available, falling back to text content');
                    element.textContent = content;
                }
            } else {
                element.textContent = content;
            }
        }
    }

    /**
     * Safely get element content
     */
    getContent(elementId) {
        const element = this.getElement(elementId);
        return element ? element.textContent : '';
    }

    /**
     * Set element visibility
     */
    setVisible(elementId, visible) {
        const element = this.getElement(elementId);
        if (element) {
            element.style.display = visible ? 'block' : 'none';
        }
    }

    /**
     * Toggle element visibility
     */
    toggleVisibility(elementId) {
        const element = this.getElement(elementId);
        if (element) {
            const isVisible = element.style.display !== 'none';
            element.style.display = isVisible ? 'none' : 'block';
            return !isVisible;
        }
        return false;
    }

    /**
     * Add CSS class to element
     */
    addClass(elementId, className) {
        const element = this.getElement(elementId);
        if (element) {
            element.classList.add(className);
        }
    }

    /**
     * Remove CSS class from element
     */
    removeClass(elementId, className) {
        const element = this.getElement(elementId);
        if (element) {
            element.classList.remove(className);
        }
    }

    /**
     * Toggle CSS class on element
     */
    toggleClass(elementId, className) {
        const element = this.getElement(elementId);
        if (element) {
            element.classList.toggle(className);
            return element.classList.contains(className);
        }
        return false;
    }

    /**
     * Update connection status display
     */
    updateConnectionStatus(status, message = '') {
        const statusElement = this.getElement('status');
        if (statusElement) {
            statusElement.textContent = message || status;
            statusElement.className = `status ${status}`;
        }
    }

    /**
     * Populate dropdown with options
     */
    populateDropdown(selectId, options, defaultText = 'Select...', valueKey = null, textKey = 'name') {
        const select = this.getElement(selectId);
        if (!select) return;

        // Clear existing options safely
        select.textContent = ''; // Clear all content first
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultText;
        select.appendChild(defaultOption);

        // Add new options
        options.forEach(option => {
            const optionElement = document.createElement('option');
            
            if (valueKey) {
                optionElement.value = option[valueKey];
            } else {
                optionElement.value = JSON.stringify(option);
            }
            
            optionElement.textContent = option[textKey] || option;
            select.appendChild(optionElement);
        });
    }

    /**
     * Set dropdown selection
     */
    setDropdownValue(selectId, value) {
        const select = this.getElement(selectId);
        if (select) {
            if (typeof value === 'object') {
                select.value = JSON.stringify(value);
            } else {
                select.value = value;
            }
        }
    }

    /**
     * Get dropdown selected value
     */
    getDropdownValue(selectId, parseJSON = true) {
        const select = this.getElement(selectId);
        if (!select || !select.value) return null;

        if (parseJSON) {
            try {
                return JSON.parse(select.value);
            } catch (e) {
                return select.value;
            }
        }
        return select.value;
    }

    /**
     * Enable/disable dropdown
     */
    setDropdownEnabled(selectId, enabled) {
        const select = this.getElement(selectId);
        if (select) {
            select.disabled = !enabled;
        }
    }

    /**
     * Clear downstream dropdowns in hierarchy
     */
    resetDownstreamDropdowns(startFrom) {
        const dropdowns = ['microgenre', 'trope', 'tone'];
        const startIndex = dropdowns.indexOf(startFrom);
        
        for (let i = startIndex; i < dropdowns.length; i++) {
            const selectId = dropdowns[i] + 'Select';
            const select = this.getElement(selectId);
            if (select) {
                const defaultText = dropdowns[i].charAt(0).toUpperCase() + dropdowns[i].slice(1);
                select.innerHTML = `<option value="">Select ${defaultText}...</option>`;
                select.disabled = true;
            }
        }
    }

    /**
     * Create and append message element to chat with modern UI structure
     */
    appendChatMessage(content, className = 'message', isHTML = false) {
        const chatContainer = this.getElement('chat');
        if (!chatContainer) return null;

        // Remove welcome message if it exists
        const welcomeMessage = chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Create message wrapper
        const messageElement = document.createElement('div');
        messageElement.className = className;
        
        // Create message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        // Create message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isHTML) {
            // Use security service for safe HTML setting
            if (window.securityService) {
                window.securityService.safeSetHTML(messageContent, content);
            } else {
                messageContent.textContent = content;
            }
        } else {
            messageContent.textContent = content;
        }
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'message-time';
        timestamp.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        // Assemble message
        messageBubble.appendChild(messageContent);
        messageBubble.appendChild(timestamp);
        messageElement.appendChild(messageBubble);

        chatContainer.appendChild(messageElement);
        this.scrollChatToBottom();
        
        return messageElement;
    }

    /**
     * Create structured response element
     */
    createStructuredResponse(data) {
        const structuredMessage = document.createElement('div');
        structuredMessage.className = 'message agent-message structured-response';
        structuredMessage.style.border = '2px solid #007bff';
        structuredMessage.style.borderRadius = '8px';
        structuredMessage.style.padding = '15px';
        structuredMessage.style.backgroundColor = '#f8f9fa';
        
        // Add agent name header
        const agentHeader = document.createElement('h4');
        agentHeader.textContent = `[DATA] ${data.agent.replace('_', ' ').toUpperCase()} - Structured Response`;
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
        
        return structuredMessage;
    }

    /**
     * Scroll chat container to bottom
     */
    scrollChatToBottom() {
        const chatContainer = this.getElement('chat');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    /**
     * Update model selector
     */
    updateModelSelector(currentModel, availableModels) {
        const select = this.getElement('modelSelect');
        console.log('updateModelSelector - select element:', select);
        if (!select) {
            console.error('Model select element not found!');
            return;
        }

        // Clear existing options safely
        while (select.firstChild) {
            select.removeChild(select.firstChild);
        }
        
        Object.entries(availableModels).forEach(([modelId, info]) => {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = info.name;
            if (modelId === currentModel) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    /**
     * Update model info display
     */
    updateModelInfo(modelId, models) {
        const info = models[modelId];
        if (info) {
            this.setContent('modelInfo', `${info.description} - Best for: ${info.best_for}`);
        }
    }

    /**
     * Update parameters display
     */
    updateParametersDisplay(state) {
        const selectedParamsDiv = this.getElement('selectedParams');
        if (!selectedParamsDiv) return;

        let paramsText = '';
        
        if (state.selectedGenre || state.selectedSubgenre || state.selectedMicrogenre || 
            state.selectedTrope || state.selectedTone || state.selectedAudience || state.selectedContent) {
            
            paramsText = '<strong>Selected Parameters:</strong><br>';
            
            // Selected content for improvement
            if (state.selectedContent) {
                paramsText += `<span style="background: #6f42c1; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Content: ${state.selectedContent.type.toUpperCase()} - ${state.selectedContent.title}</span><br>`;
            }
            
            // Genre hierarchy
            if (state.selectedGenre) {
                paramsText += `<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Genre: ${state.selectedGenre.name}</span>`;
            }
            if (state.selectedSubgenre) {
                paramsText += `<span style="background: #0056b3; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Subgenre: ${state.selectedSubgenre.name}</span>`;
            }
            if (state.selectedMicrogenre) {
                paramsText += `<span style="background: #003d82; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Microgenre: ${state.selectedMicrogenre.name}</span>`;
            }
            
            // Tropes and Tones
            if (state.selectedTrope) {
                paramsText += `<br><span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Trope: ${state.selectedTrope.name} (${state.selectedTrope.category})</span>`;
            }
            if (state.selectedTone) {
                paramsText += `<span style="background: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Tone: ${state.selectedTone.name}</span>`;
            }
            
            // Target Audience
            if (state.selectedAudience) {
                paramsText += `<br><span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Audience: ${state.selectedAudience.age_group} - ${state.selectedAudience.gender} - ${state.selectedAudience.sexual_orientation}</span>`;
            }
            
            // Add descriptions
            if (state.selectedMicrogenre && state.selectedMicrogenre.description) {
                paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Microgenre: ${state.selectedMicrogenre.description}</em>`;
            }
            if (state.selectedTrope && state.selectedTrope.description) {
                paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Trope: ${state.selectedTrope.description}</em>`;
            }
            if (state.selectedTone && state.selectedTone.description) {
                paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Tone: ${state.selectedTone.description}</em>`;
            }
        } else {
            paramsText = '<em style="color: #6c757d;">No parameters selected. Select parameters above to automatically include them in your requests.</em>';
        }
        
        // Use security service for safe HTML setting
        if (window.securityService) {
            window.securityService.safeSetHTML(selectedParamsDiv, paramsText);
        } else {
            selectedParamsDiv.textContent = paramsText.replace(/<[^>]*>/g, ''); // Strip HTML as fallback
        }
    }

    /**
     * Show loading state
     */
    showLoading(elementId, message = 'Loading...') {
        const element = this.getElement(elementId);
        if (element) {
            // Create loading element safely
            element.textContent = ''; // Clear existing content
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = message;
            element.appendChild(loadingDiv);
            element.classList.add('loading-state');
        }
    }

    /**
     * Hide loading state
     */
    hideLoading(elementId) {
        const element = this.getElement(elementId);
        if (element) {
            element.classList.remove('loading-state');
        }
    }

    /**
     * Show error message
     */
    showError(elementId, message) {
        const element = this.getElement(elementId);
        if (element) {
            // Create error element safely
            element.textContent = ''; // Clear existing content
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            element.appendChild(errorDiv);
            element.classList.add('error-state');
        }
    }

    /**
     * Clear error state
     */
    clearError(elementId) {
        const element = this.getElement(elementId);
        if (element) {
            element.classList.remove('error-state');
        }
    }

    /**
     * Add event listener with cleanup tracking
     */
    addEventListener(elementId, event, handler, options = {}) {
        const element = this.getElement(elementId);
        if (!element) return null;

        element.addEventListener(event, handler, options);

        // Track for cleanup
        const key = `${elementId}-${event}`;
        if (!this.eventListeners.has(key)) {
            this.eventListeners.set(key, []);
        }
        this.eventListeners.get(key).push({ element, handler, options });

        // Return cleanup function
        return () => {
            element.removeEventListener(event, handler, options);
            const listeners = this.eventListeners.get(key);
            if (listeners) {
                const index = listeners.findIndex(l => l.handler === handler);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
            }
        };
    }

    /**
     * Add event listener to element directly (for dynamic elements without IDs)
     */
    addEventListenerToElement(element, event, handler, options = {}) {
        if (!element) return null;

        element.addEventListener(event, handler, options);

        // Generate unique key for tracking
        const elementKey = `element-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const key = `${elementKey}-${event}`;
        
        if (!this.eventListeners.has(key)) {
            this.eventListeners.set(key, []);
        }
        this.eventListeners.get(key).push({ element, handler, options });

        // Return cleanup function
        return () => {
            element.removeEventListener(event, handler, options);
            const listeners = this.eventListeners.get(key);
            if (listeners) {
                const index = listeners.findIndex(l => l.handler === handler);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
                if (listeners.length === 0) {
                    this.eventListeners.delete(key);
                }
            }
        };
    }

    /**
     * Remove all event listeners for cleanup
     */
    cleanup() {
        this.eventListeners.forEach((listeners, key) => {
            listeners.forEach(({ element, handler, options }) => {
                const [, event] = key.split('-');
                element.removeEventListener(event, handler, options);
            });
        });
        this.eventListeners.clear();
        this.elements.clear();
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        // Hide the static typing indicator in the input container
        const staticIndicator = this.getElement('typingIndicator');
        if (staticIndicator) {
            staticIndicator.style.display = 'none';
        }

        const existingIndicator = document.getElementById('typing-indicator');
        if (existingIndicator) {
            return; // Already showing
        }

        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message assistant typing';
        
        const typingBubble = document.createElement('div');
        typingBubble.className = 'message-bubble';
        
        // Create typing indicator safely without innerHTML
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        
        const typingDots = document.createElement('div');
        typingDots.className = 'typing-dots';
        
        // Create three dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingDots.appendChild(dot);
        }
        
        const typingText = document.createElement('span');
        typingText.className = 'typing-text';
        typingText.textContent = 'AI is thinking...';
        
        typingIndicator.appendChild(typingDots);
        typingIndicator.appendChild(typingText);
        typingBubble.appendChild(typingIndicator);

        typingDiv.appendChild(typingBubble);

        const chatContainer = this.getElement('chat');
        if (chatContainer) {
            chatContainer.appendChild(typingDiv);
            this.scrollChatToBottom();
        }
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Handle long messages with expand/collapse (Security-Fixed)
     */
    handleLongMessage(messageElement, threshold = 500) {
        const textContent = messageElement.textContent || '';
        
        if (textContent.length > threshold) {
            const preview = textContent.substring(0, threshold) + '...';
            const fullText = textContent;
            
            // Clear existing content safely
            messageElement.textContent = '';
            
            // Create preview section
            const previewDiv = document.createElement('div');
            previewDiv.className = 'message-preview';
            
            const previewContent = document.createElement('div');
            if (window.securityService) {
                const safePreview = window.securityService.formatMessageSafely(preview);
                window.securityService.safeSetHTML(previewContent, safePreview);
            } else {
                previewContent.textContent = preview;
            }
            
            const expandBtn = document.createElement('button');
            expandBtn.className = 'expand-btn';
            expandBtn.textContent = 'Read More';
            
            // Create full message section  
            const fullDiv = document.createElement('div');
            fullDiv.className = 'message-full';
            fullDiv.style.display = 'none';
            
            const fullContent = document.createElement('div');
            if (window.securityService) {
                const safeFullText = window.securityService.formatMessageSafely(fullText);
                window.securityService.safeSetHTML(fullContent, safeFullText);
            } else {
                fullContent.textContent = fullText;
            }
            
            const collapseBtn = document.createElement('button');
            collapseBtn.className = 'collapse-btn';
            collapseBtn.textContent = 'Show Less';
            
            // Add secure event listeners instead of inline onclick
            const expandHandler = () => {
                messageElement.classList.add('expanded');
                previewDiv.style.display = 'none';
                fullDiv.style.display = 'block';
            };
            
            const collapseHandler = () => {
                messageElement.classList.remove('expanded');
                previewDiv.style.display = 'block';
                fullDiv.style.display = 'none';
            };
            
            expandBtn.addEventListener('click', expandHandler);
            collapseBtn.addEventListener('click', collapseHandler);
            
            // Assemble the elements
            previewDiv.appendChild(previewContent);
            previewDiv.appendChild(expandBtn);
            fullDiv.appendChild(fullContent);
            fullDiv.appendChild(collapseBtn);
            
            messageElement.appendChild(previewDiv);
            messageElement.appendChild(fullDiv);
            messageElement.classList.add('expandable-message');
            
            // Track event listeners for cleanup
            this.addEventListenerToElement(expandBtn, 'click', expandHandler);
            this.addEventListenerToElement(collapseBtn, 'click', collapseHandler);
        }
    }

    /**
     * Auto-resize textarea
     */
    setupAutoResize(textareaId) {
        const textarea = this.getElement(textareaId);
        if (!textarea) return;

        const autoResize = () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        };

        textarea.addEventListener('input', autoResize);
        textarea.addEventListener('paste', () => setTimeout(autoResize, 0));
        
        // Initial resize
        autoResize();

        return () => {
            textarea.removeEventListener('input', autoResize);
            textarea.removeEventListener('paste', autoResize);
        };
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(date) {
        if (!date) return '';
        
        const now = new Date();
        const messageDate = new Date(date);
        const diffInSeconds = Math.floor((now - messageDate) / 1000);
        
        if (diffInSeconds < 60) {
            return 'just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else {
            return messageDate.toLocaleDateString();
        }
    }

    /**
     * Create enhanced message element with agent styling
     */
    createMessageElement(content, className = 'message', agent = null, timestamp = null) {
        return this.createModernMessageElement(content, className, agent, timestamp);
    }

    /**
     * Create modern message element with bubble design
     */
    createModernMessageElement(content, className = 'message', agent = null, timestamp = null) {
        // Remove welcome message if it exists
        const chatContainer = this.getElement('chat');
        if (chatContainer) {
            const welcomeMessage = chatContainer.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
        }

        // Create message wrapper
        const messageElement = document.createElement('div');
        messageElement.className = className;
        
        // Add agent-specific styling
        if (agent && window.agentManager) {
            const agentConfig = window.agentManager.getAgentConfig(agent);
            messageElement.classList.add(`${agent}-message`);
            window.agentManager.addAgentStyle(agent);
        }
        
        // Create message bubble
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        // Add agent header if applicable
        if (agent && window.agentManager) {
            const agentConfig = window.agentManager.getAgentConfig(agent);
            const agentHeader = window.agentManager.createAgentHeader(agentConfig);
            messageBubble.appendChild(agentHeader);
        }
        
        // Add content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        // Use security service for safe message formatting
        if (window.securityService) {
            const safeContent = window.securityService.formatMessageSafely(content);
            window.securityService.safeSetHTML(contentDiv, safeContent);
        } else {
            contentDiv.textContent = content;
        }
        messageBubble.appendChild(contentDiv);
        
        // Add timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-time';
        if (timestamp) {
            timestampDiv.textContent = this.formatTimestamp(timestamp);
        } else {
            timestampDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
        messageBubble.appendChild(timestampDiv);
        
        messageElement.appendChild(messageBubble);
        
        return messageElement;
    }

    /**
     * Append enhanced chat message with agent detection
     */
    appendEnhancedChatMessage(content, className = 'message', data = {}) {
        const chatContainer = this.getElement('chat');
        if (!chatContainer) return null;

        // Remove welcome message if it exists
        const welcomeMessage = chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Detect agent from message data
        const agent = window.agentManager ? window.agentManager.detectAgentFromMessage(data) : null;
        
        // Create message element with modern structure
        const messageElement = this.createModernMessageElement(content, className, agent, data.timestamp);
        
        // Handle workflow visualization
        if (agent === 'orchestrator' && window.agentManager && window.agentManager.isOrchestratorWorkflow(content)) {
            const workflow = window.agentManager.parseWorkflowFromContent(content);
            const workflowCard = window.agentManager.createWorkflowCard(workflow);
            chatContainer.appendChild(workflowCard);
        }
        
        // Handle JSON responses
        if (data.json_data && window.agentManager) {
            const jsonElement = window.agentManager.createCollapsibleJSON(data.json_data, agent);
            const messageBubble = messageElement.querySelector('.message-bubble');
            if (messageBubble) {
                messageBubble.appendChild(jsonElement);
            }
        }
        
        chatContainer.appendChild(messageElement);
        
        // Handle long messages
        this.handleLongMessage(messageElement);
        
        this.scrollChatToBottom();
        return messageElement;
    }

    /**
     * Update status with enhanced styling
     */
    updateStatus(status, message = '') {
        // Update connection status in chat header
        const statusElement = this.getElement('statusIndicator');
        const statusText = this.getElement('statusText');
        
        if (statusElement) {
            statusElement.className = `status-indicator ${status}`;
        }
        
        if (statusText) {
            statusText.textContent = message || this.getStatusMessage(status);
        }
        
        // Also update status bar if it exists
        const statusBarIndicator = document.querySelector('.status-bar .status-indicator');
        const statusBarText = document.querySelector('.status-bar .status-text');
        
        if (statusBarIndicator) {
            statusBarIndicator.className = `status-indicator ${status}`;
        }
        
        if (statusBarText) {
            statusBarText.textContent = message || this.getStatusMessage(status);
        }
    }

    /**
     * Get human-readable status message
     */
    getStatusMessage(status) {
        const statusMessages = {
            'connected': 'Connected',
            'connecting': 'Connecting...',
            'disconnected': 'Disconnected',
            'reconnecting': 'Reconnecting...',
            'error': 'Connection Error'
        };
        return statusMessages[status] || status;
    }

    /**
     * Utility: Enhanced message formatting with security
     * @deprecated Use securityService.formatMessageSafely() instead
     */
    static formatMessage(text) {
        console.warn('formatMessage is deprecated, use securityService.formatMessageSafely() instead');
        
        // Delegate to security service if available
        if (window.securityService) {
            return window.securityService.formatMessageSafely(text);
        }
        
        // Fallback to safe text content
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create singleton instance
const uiManager = new UIManager();

// Export for ES6 modules and global access
if (typeof window !== 'undefined') {
    window.uiManager = uiManager;
}

