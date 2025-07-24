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
     * Safely set element content
     */
    setContent(elementId, content, isHTML = false) {
        const element = this.getElement(elementId);
        if (element) {
            if (isHTML) {
                element.innerHTML = content;
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

        // Clear existing options
        select.innerHTML = `<option value="">${defaultText}</option>`;

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
     * Create and append message element to chat
     */
    appendChatMessage(content, className = 'message', isHTML = false) {
        const chatContainer = this.getElement('chat');
        if (!chatContainer) return null;

        const messageElement = document.createElement('div');
        messageElement.className = className;
        
        if (isHTML) {
            messageElement.innerHTML = content;
        } else {
            messageElement.textContent = content;
        }

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

        select.innerHTML = '';
        
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
        
        selectedParamsDiv.innerHTML = paramsText;
    }

    /**
     * Show loading state
     */
    showLoading(elementId, message = 'Loading...') {
        const element = this.getElement(elementId);
        if (element) {
            element.innerHTML = `<div class="loading">${message}</div>`;
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
            element.innerHTML = `<div class="error">${message}</div>`;
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
        const existingIndicator = document.getElementById('typing-indicator');
        if (existingIndicator) {
            return; // Already showing
        }

        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message agent-message typing';
        typingDiv.innerHTML = `
            <div class="typing-content">
                <span class="typing-avatar">🤖</span>
                <span class="typing-text">AI is thinking...</span>
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

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
     * Handle long messages with expand/collapse
     */
    handleLongMessage(messageElement, threshold = 500) {
        const textContent = messageElement.textContent || '';
        
        if (textContent.length > threshold) {
            const preview = textContent.substring(0, threshold) + '...';
            const fullText = textContent;
            
            messageElement.innerHTML = `
                <div class="message-preview">
                    ${this.constructor.formatMessage(preview)}
                    <button class="expand-btn" onclick="this.parentElement.parentElement.classList.add('expanded')">
                        Read More
                    </button>
                </div>
                <div class="message-full" style="display: none;">
                    ${this.constructor.formatMessage(fullText)}
                    <button class="collapse-btn" onclick="this.parentElement.parentElement.classList.remove('expanded')">
                        Show Less
                    </button>
                </div>
            `;
            
            messageElement.classList.add('expandable-message');
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
        const messageElement = document.createElement('div');
        messageElement.className = className;
        
        if (agent && window.agentManager) {
            const agentConfig = window.agentManager.getAgentConfig(agent);
            messageElement.classList.add(`${agent}-message`);
            
            // Add agent header
            const agentHeader = window.agentManager.createAgentHeader(agentConfig);
            messageElement.appendChild(agentHeader);
            
            // Ensure agent styles are loaded
            window.agentManager.addAgentStyle(agent);
        }
        
        // Add content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.constructor.formatMessage(content);
        messageElement.appendChild(contentDiv);
        
        // Add timestamp if provided
        if (timestamp) {
            const timestampDiv = document.createElement('div');
            timestampDiv.className = 'message-timestamp';
            timestampDiv.textContent = this.formatTimestamp(timestamp);
            messageElement.appendChild(timestampDiv);
        }
        
        return messageElement;
    }

    /**
     * Append enhanced chat message with agent detection
     */
    appendEnhancedChatMessage(content, className = 'message', data = {}) {
        const chatContainer = this.getElement('chat');
        if (!chatContainer) return null;

        // Detect agent from message data
        const agent = window.agentManager ? window.agentManager.detectAgentFromMessage(data) : null;
        
        // Create message element
        const messageElement = this.createMessageElement(content, className, agent, data.timestamp);
        
        // Handle workflow visualization
        if (agent === 'orchestrator' && window.agentManager && window.agentManager.isOrchestratorWorkflow(content)) {
            const workflow = window.agentManager.parseWorkflowFromContent(content);
            const workflowCard = window.agentManager.createWorkflowCard(workflow);
            chatContainer.appendChild(workflowCard);
        }
        
        // Handle JSON responses
        if (data.json_data && window.agentManager) {
            const jsonElement = window.agentManager.createCollapsibleJSON(data.json_data, agent);
            messageElement.appendChild(jsonElement);
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
        const statusElement = this.getElement('statusIndicator') || this.getElement('status');
        const statusText = this.getElement('statusText');
        
        if (statusElement) {
            statusElement.className = `status-indicator ${status}`;
        }
        
        if (statusText) {
            statusText.textContent = message || status;
        } else if (statusElement) {
            statusElement.textContent = message || status;
        }
    }

    /**
     * Utility: Enhanced message formatting
     */
    static formatMessage(text) {
        if (!text) return '';
        
        // Convert numbered lists to HTML
        text = text.replace(/^(\d+\.\s\*\*)(.+?)(\*\*)/gm, '<strong>$1$2</strong>');
        text = text.replace(/^(\d+\.\s)(.+?)$/gm, '<strong>$1</strong>$2');
        
        // Convert bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert italic text
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert code blocks
        text = text.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Convert links
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
}

// Create singleton instance
const uiManager = new UIManager();

// Export for ES6 modules and global access
if (typeof window !== 'undefined') {
    window.uiManager = uiManager;
}

