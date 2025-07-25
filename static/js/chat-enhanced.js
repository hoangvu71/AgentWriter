/**
 * Enhanced Chat Application - Full-featured modular architecture
 * Combines the modular system with advanced features from main.js
 */

class EnhancedChatApplication {
    constructor() {
        this.initialized = false;
        this.cleanup = [];
        this.currentWorkflow = null;
    }

    /**
     * Initialize the enhanced chat application
     */
    async init() {
        if (this.initialized) return;

        try {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                await new Promise(resolve => {
                    document.addEventListener('DOMContentLoaded', resolve);
                });
            }

            // Initialize modules in order
            this.setupTheme();
            this.setupWebSocket();
            this.setupStateManagement();
            this.setupEventHandlers();
            this.setupUIEnhancements();
            await this.loadInitialData();

            this.initialized = true;
            console.log('Enhanced chat application initialized successfully');
        } catch (error) {
            console.error('Failed to initialize enhanced chat application:', error);
        }
    }

    /**
     * Setup theme management
     */
    setupTheme() {
        // Theme is already initialized by themeManager
        // Add theme toggle button if it exists
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const cleanup = uiManager.addEventListener('theme-toggle', 'click', () => {
                themeManager.toggleTheme();
            });
            this.cleanup.push(cleanup);
        }
    }

    /**
     * Setup WebSocket connection and message handlers
     */
    setupWebSocket() {
        // Handle connection state changes
        webSocketService.onConnectionStateChange((state, message) => {
            uiManager.updateStatus(state, message);
        });

        // Handle different message types with enhanced processing
        webSocketService.onMessage('stream_chunk', (data) => {
            this.handleStreamChunk(data);
        });

        webSocketService.onMessage('structured_response', (data) => {
            this.handleStructuredResponse(data);
        });

        webSocketService.onMessage('stream_end', (data) => {
            this.handleStreamEnd(data);
        });

        webSocketService.onMessage('error', (data) => {
            this.handleError(data);
        });

        // Handle typing indicators
        webSocketService.onMessage('typing_start', () => {
            uiManager.showTypingIndicator();
        });

        webSocketService.onMessage('typing_end', () => {
            uiManager.hideTypingIndicator();
        });

        // Connect to WebSocket
        webSocketService.connect();
    }

    /**
     * Setup state management and subscriptions
     */
    setupStateManagement() {
        // Subscribe to state changes for UI updates
        stateManager.subscribe('selectedGenre', () => this.onGenreChange());
        stateManager.subscribe('selectedSubgenre', () => this.onSubgenreChange());
        stateManager.subscribe('selectedMicrogenre', () => this.onMicrogenreChange());
        stateManager.subscribe('selectedTrope', () => this.onTropeChange());
        stateManager.subscribe('selectedTone', () => this.updateContext());
        stateManager.subscribe('selectedAudience', () => this.updateContext());
        stateManager.subscribe('selectedContent', () => this.updateContext());

        // Subscribe to data changes
        stateManager.subscribe('allGenres', () => this.populateGenreDropdown());
        stateManager.subscribe('allAudiences', () => this.populateAudienceDropdown());
        stateManager.subscribe('availableContent', () => this.populateContentDropdown());
        stateManager.subscribe('currentModel', () => this.updateModelDisplay());
        stateManager.subscribe('availableModels', () => this.updateModelDisplay());

        // Subscribe to workflow changes
        stateManager.subscribe('currentWorkflow', (workflow) => {
            this.currentWorkflow = workflow;
        });
    }

    /**
     * Setup DOM event handlers
     */
    setupEventHandlers() {
        // Message input and send button handlers with enhanced features
        const cleanup1 = uiManager.addEventListener('messageInput', 'keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.cleanup.push(cleanup1);

        const cleanupSend = uiManager.addEventListener('sendButton', 'click', () => {
            this.sendMessage();
        });
        this.cleanup.push(cleanupSend);

        // Model selection handler
        const cleanup2 = uiManager.addEventListener('modelSelect', 'change', () => {
            this.switchModel();
        });
        this.cleanup.push(cleanup2);

        // Parameters toggle handler
        const cleanup3 = uiManager.addEventListener('toggleParams', 'click', () => {
            this.toggleParameters();
        });
        this.cleanup.push(cleanup3);

        // Genre hierarchy handlers
        const cleanupHandlers = [
            ['genreSelect', () => {
                const selected = uiManager.getDropdownValue('genreSelect');
                stateManager.set('selectedGenre', selected);
            }],
            ['subgenreSelect', () => {
                const selected = uiManager.getDropdownValue('subgenreSelect');
                stateManager.set('selectedSubgenre', selected);
            }],
            ['microgenreSelect', () => {
                const selected = uiManager.getDropdownValue('microgenreSelect');
                stateManager.set('selectedMicrogenre', selected);
            }],
            ['tropeSelect', () => {
                const selected = uiManager.getDropdownValue('tropeSelect');
                stateManager.set('selectedTrope', selected);
            }],
            ['toneSelect', () => {
                const selected = uiManager.getDropdownValue('toneSelect');
                stateManager.set('selectedTone', selected);
            }],
            ['audienceSelect', () => {
                const selected = uiManager.getDropdownValue('audienceSelect');
                stateManager.set('selectedAudience', selected);
            }],
            ['contentSelect', () => {
                const selected = uiManager.getDropdownValue('contentSelect');
                stateManager.set('selectedContent', selected);
            }],
            ['completePackageSelect', () => {
                this.selectCompletePackage();
            }],
            ['refreshContent', () => {
                this.refreshContent();
            }]
        ];

        cleanupHandlers.forEach(([elementId, handler], index) => {
            const cleanup = uiManager.addEventListener(elementId, 'change', handler);
            if (cleanup) this.cleanup.push(cleanup);
        });
    }

    /**
     * Setup enhanced UI features
     */
    setupUIEnhancements() {
        // Setup auto-resize for message input
        const autoResizeCleanup = uiManager.setupAutoResize('messageInput');
        if (autoResizeCleanup) {
            this.cleanup.push(autoResizeCleanup);
        }

        // Setup suggestion list click handlers
        this.setupSuggestionHandlers();

        // Add enhanced styles for features
        this.addEnhancedStyles();
    }

    /**
     * Setup suggestion list click handlers
     */
    setupSuggestionHandlers() {
        const suggestionItems = document.querySelectorAll('.suggestion-list li');
        suggestionItems.forEach(item => {
            const cleanup = uiManager.addEventListenerToElement(item, 'click', () => {
                const messageInput = uiManager.getElement('messageInput');
                if (messageInput) {
                    // Extract text from suggestion, removing the emoji
                    const suggestionText = item.textContent.replace(/^[📖✍️🌟🌍]\s*"/, '').replace(/"$/, '');
                    messageInput.value = suggestionText;
                    messageInput.focus();
                    
                    // Trigger auto-resize
                    messageInput.style.height = 'auto';
                    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
                }
            });
            if (cleanup) this.cleanup.push(cleanup);
        });
    }

    /**
     * Add enhanced CSS styles
     */
    addEnhancedStyles() {
        const styleSheet = document.createElement('style');
        styleSheet.id = 'enhanced-chat-styles';
        styleSheet.textContent = `
            /* Typing indicator styles */
            .typing-content {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.75rem;
                background: var(--bg-secondary);
                border-radius: 8px;
                opacity: 0.8;
            }
            
            .typing-dots {
                display: flex;
                gap: 0.25rem;
            }
            
            .typing-dots span {
                width: 4px;
                height: 4px;
                border-radius: 50%;
                background: var(--text-secondary);
                animation: typing-pulse 1.4s infinite ease-in-out;
            }
            
            .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
            .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes typing-pulse {
                0%, 80%, 100% {
                    transform: scale(0.8);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            
            /* Expandable message styles */
            .expandable-message .message-full {
                display: none !important;
            }
            
            .expandable-message.expanded .message-preview {
                display: none !important;
            }
            
            .expandable-message.expanded .message-full {
                display: block !important;
            }
            
            .expand-btn, .collapse-btn {
                background: var(--primary);
                color: white;
                border: none;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
                cursor: pointer;
                margin-top: 0.5rem;
            }
            
            .expand-btn:hover, .collapse-btn:hover {
                background: var(--primary-hover);
            }
            
            /* Enhanced message styles */
            .message-content {
                flex: 1;
            }
            
            .message-timestamp {
                font-size: 0.75rem;
                color: var(--text-tertiary);
                opacity: 0.7;
                margin-top: 0.25rem;
                text-align: right;
            }
            
            /* JSON response styles */
            .json-response {
                margin: 0.5rem 0;
                border: 1px solid var(--border);
                border-radius: 6px;
                background: var(--bg-tertiary);
            }
            
            .json-preview, .json-full {
                padding: 0.75rem;
            }
            
            .json-preview pre, .json-full pre {
                margin: 0;
                background: none;
                font-size: 0.875rem;
                line-height: 1.4;
            }
            
            .json-toggle {
                background: var(--secondary);
                color: white;
                border: none;
                padding: 0.375rem 0.75rem;
                border-radius: 4px;
                font-size: 0.75rem;
                cursor: pointer;
                margin-top: 0.5rem;
            }
            
            .json-toggle:hover {
                background: var(--secondary-hover);
            }
        `;
        document.head.appendChild(styleSheet);
    }

    /**
     * Load initial data from APIs
     */
    async loadInitialData() {
        console.log('Starting loadInitialData...');
        stateManager.set('loading', true);

        try {
            // Load models with enhanced error handling
            console.log('Loading models...');
            const modelsResult = await apiService.loadModels();
            console.log('Models result:', modelsResult);
            
            if (modelsResult.success && modelsResult.data) {
                console.log('Setting model data:', modelsResult.data.current_model, modelsResult.data.available_models);
                console.log('Available models count:', Object.keys(modelsResult.data.available_models).length);
                
                stateManager.setModelData(
                    modelsResult.data.current_model,
                    modelsResult.data.available_models
                );
                
                // Force UI update after a short delay to ensure DOM is ready
                setTimeout(() => {
                    console.log('Forcing model display update...');
                    this.updateModelDisplay();
                }, 100);
            } else {
                console.error('Models result unsuccessful or missing data:', modelsResult);
                // Show error in UI
                const modelSelect = document.getElementById('modelSelect');
                if (modelSelect) {
                    modelSelect.innerHTML = '<option value="">Error loading models</option>';
                }
            }

            // Load parameters with enhanced error handling
            console.log('Loading parameters...');
            const paramsResult = await apiService.loadParameters();
            console.log('Parameters result:', paramsResult);
            
            if (paramsResult.success) {
                if (paramsResult.genres && paramsResult.genres.success) {
                    console.log('Setting genre data - genres:', paramsResult.genres.genres.length);
                    stateManager.setGenreData(paramsResult.genres);
                } else {
                    console.error('Genres data unsuccessful:', paramsResult.genres);
                }
                
                if (paramsResult.audiences && paramsResult.audiences.success) {
                    console.log('Setting audience data - audiences:', paramsResult.audiences.audiences.length);
                    stateManager.set('allAudiences', paramsResult.audiences.audiences);
                } else {
                    console.error('Audiences data unsuccessful:', paramsResult.audiences);
                }
            } else {
                console.error('Parameters result unsuccessful:', paramsResult);
            }

            // Load content
            const contentResult = await apiService.loadContent();
            if (contentResult.success) {
                stateManager.set('availableContent', contentResult.content);
            }

        } catch (error) {
            console.error('Error loading initial data:', error);
            stateManager.set('error', error.message);
        } finally {
            stateManager.set('loading', false);
        }
    }

    /**
     * Handle stream chunk messages with enhanced processing
     */
    handleStreamChunk(data) {
        uiManager.hideTypingIndicator();
        
        let currentMessage = document.getElementById('current-agent-message');
        if (!currentMessage) {
            // Create assistant message with modern structure
            currentMessage = uiManager.appendChatMessage('', 'message assistant');
            currentMessage.id = 'current-agent-message';
        }
        
        // Get the content div within the message bubble
        const contentDiv = currentMessage.querySelector('.message-content');
        if (contentDiv) {
            contentDiv.textContent += data.content;
        } else {
            // Fallback - find any content container
            const fallbackContent = currentMessage.querySelector('.message-bubble') || currentMessage;
            if (fallbackContent.querySelector('.message-content')) {
                fallbackContent.querySelector('.message-content').textContent += data.content;
            } else {
                fallbackContent.textContent += data.content;
            }
        }
        
        uiManager.scrollChatToBottom();
    }

    /**
     * Handle structured response messages with enhanced processing
     */
    handleStructuredResponse(data) {
        const chatContainer = uiManager.getElement('chat');
        if (chatContainer) {
            // Use enhanced message creation
            const structuredMessage = uiManager.appendEnhancedChatMessage(
                'Structured response received',
                'message agent-message structured-response',
                data
            );
            
            // Update workflow if applicable
            if (data.workflow_step) {
                this.updateWorkflowStep(data.workflow_step);
            }
        }
    }

    /**
     * Handle stream end messages with enhanced processing
     */
    handleStreamEnd(data) {
        const currentMessage = document.getElementById('current-agent-message');
        if (currentMessage) {
            currentMessage.id = '';
            
            // Apply enhanced formatting
            const contentDiv = currentMessage.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.innerHTML = uiManager.constructor.formatMessage(contentDiv.textContent);
            }
            
            // Handle long messages
            uiManager.handleLongMessage(currentMessage);
        }
        
        // Log structured responses for debugging
        if (data.structured_responses) {
            console.log('Structured responses received:', data.structured_responses);
        }
        
        uiManager.hideTypingIndicator();
    }

    /**
     * Handle error messages with enhanced processing
     */
    handleError(data) {
        uiManager.hideTypingIndicator();
        uiManager.appendEnhancedChatMessage(
            'Error: ' + data.content, 
            'message agent-message error-message',
            data
        );
    }

    /**
     * Send message through WebSocket with enhanced features
     */
    sendMessage() {
        const messageInput = uiManager.getElement('messageInput');
        const message = messageInput.value.trim();
        if (!message) return;

        // Show typing indicator
        uiManager.showTypingIndicator();

        // Display user message with modern structure
        uiManager.appendChatMessage(message, 'message user');

        // Build context from current state
        const context = stateManager.buildContextObject();

        // Send message with context
        const success = webSocketService.sendMessage(message, context);
        
        if (success) {
            messageInput.value = '';
            // Trigger auto-resize
            messageInput.style.height = 'auto';
        } else {
            uiManager.hideTypingIndicator();
            uiManager.showError('chat', 'Failed to send message - not connected');
        }
    }

    /**
     * Update workflow step visualization
     */
    updateWorkflowStep(stepData) {
        if (this.currentWorkflow && window.agentManager) {
            const workflowCards = document.querySelectorAll('.workflow-card');
            const latestCard = workflowCards[workflowCards.length - 1];
            
            if (latestCard) {
                window.agentManager.updateWorkflowStep(latestCard, stepData.step, stepData.status);
            }
        }
    }

    // Include all the existing methods from chat-modular.js
    async switchModel() {
        const modelId = uiManager.getDropdownValue('modelSelect', false);
        if (!modelId) return;

        try {
            const result = await apiService.switchModel(modelId);
            if (result.success) {
                console.log('Model switched successfully');
                const modelsResult = await apiService.loadModels();
                if (modelsResult.success) {
                    stateManager.setModelData(
                        modelsResult.data.current_model,
                        modelsResult.data.available_models
                    );
                }
            } else {
                console.error('Failed to switch model:', result.error);
            }
        } catch (error) {
            console.error('Error switching model:', error);
        }
    }

    toggleParameters() {
        const isVisible = uiManager.toggleVisibility('parametersContent');
        const button = uiManager.getElement('toggleParams');
        if (button) {
            button.textContent = isVisible ? '▲' : '▼';
        }
        stateManager.set('parametersVisible', isVisible);
    }

    onGenreChange() {
        const selectedGenre = stateManager.get('selectedGenre');
        stateManager.update({
            selectedSubgenre: null,
            selectedMicrogenre: null,
            selectedTrope: null,
            selectedTone: null
        });
        this.populateSubgenreDropdown();
        this.updateContext();
    }

    onSubgenreChange() {
        stateManager.update({
            selectedMicrogenre: null,
            selectedTrope: null,
            selectedTone: null
        });
        this.populateMicrogenreDropdown();
        this.updateContext();
    }

    onMicrogenreChange() {
        stateManager.update({
            selectedTrope: null,
            selectedTone: null
        });
        this.populateTropeDropdown();
        this.updateContext();
    }

    onTropeChange() {
        stateManager.set('selectedTone', null);
        this.populateToneDropdown();
        this.updateContext();
    }

    populateGenreDropdown() {
        const genres = stateManager.get('allGenres');
        uiManager.populateDropdown('genreSelect', genres, 'Select Genre...');
    }

    populateAudienceDropdown() {
        const audiences = stateManager.get('allAudiences');
        const formattedAudiences = audiences.map(audience => ({
            ...audience,
            name: `${audience.age_group} - ${audience.gender} - ${audience.sexual_orientation}`
        }));
        uiManager.populateDropdown('audienceSelect', formattedAudiences, 'Select Audience...');
    }

    populateContentDropdown() {
        const content = stateManager.get('availableContent');
        const formattedContent = content.map(item => ({
            ...item,
            name: `${item.type.toUpperCase()} - ${item.title}`
        }));
        uiManager.populateDropdown('contentSelect', formattedContent, 'Select Content...');
    }

    populateSubgenreDropdown() {
        const selectedGenre = stateManager.get('selectedGenre');
        const allSubgenres = stateManager.get('allSubgenres');

        if (selectedGenre) {
            const genreSubgenres = allSubgenres.filter(sub => sub.genre_id === selectedGenre.id);
            uiManager.populateDropdown('subgenreSelect', genreSubgenres, 'Select Subgenre...');
            uiManager.setDropdownEnabled('subgenreSelect', true);
        } else {
            uiManager.populateDropdown('subgenreSelect', [], 'Select Subgenre...');
            uiManager.setDropdownEnabled('subgenreSelect', false);
        }
        uiManager.resetDownstreamDropdowns('microgenre');
    }

    populateMicrogenreDropdown() {
        const selectedSubgenre = stateManager.get('selectedSubgenre');
        const allMicrogenres = stateManager.get('allMicrogenres');

        if (selectedSubgenre) {
            const subgenreMicrogenres = allMicrogenres.filter(micro => micro.subgenre_id === selectedSubgenre.id);
            uiManager.populateDropdown('microgenreSelect', subgenreMicrogenres, 'Select Microgenre...');
            uiManager.setDropdownEnabled('microgenreSelect', true);
        } else {
            uiManager.populateDropdown('microgenreSelect', [], 'Select Microgenre...');
            uiManager.setDropdownEnabled('microgenreSelect', false);
        }
        uiManager.resetDownstreamDropdowns('trope');
    }

    populateTropeDropdown() {
        const selectedMicrogenre = stateManager.get('selectedMicrogenre');
        const allTropes = stateManager.get('allTropes');

        if (selectedMicrogenre) {
            const microgenreTropes = allTropes.filter(trope => trope.microgenre_id === selectedMicrogenre.id);
            uiManager.populateDropdown('tropeSelect', microgenreTropes, 'Select Trope...');
            uiManager.setDropdownEnabled('tropeSelect', true);
        } else {
            uiManager.populateDropdown('tropeSelect', [], 'Select Trope...');
            uiManager.setDropdownEnabled('tropeSelect', false);
        }
        uiManager.resetDownstreamDropdowns('tone');
    }

    populateToneDropdown() {
        const selectedTrope = stateManager.get('selectedTrope');
        const allTones = stateManager.get('allTones');

        if (selectedTrope) {
            const tropeTones = allTones.filter(tone => tone.trope_id === selectedTrope.id);
            uiManager.populateDropdown('toneSelect', tropeTones, 'Select Tone...');
            uiManager.setDropdownEnabled('toneSelect', true);
        } else {
            uiManager.populateDropdown('toneSelect', [], 'Select Tone...');
            uiManager.setDropdownEnabled('toneSelect', false);
        }
    }

    selectCompletePackage() {
        const packageData = uiManager.getDropdownValue('completePackageSelect');
        
        if (packageData) {
            stateManager.update({
                selectedGenre: packageData.genre,
                selectedSubgenre: packageData.subgenre,
                selectedMicrogenre: packageData.microgenre,
                selectedTrope: packageData.trope,
                selectedTone: packageData.tone
            });
            this.updateDropdownsFromSelection();
        } else {
            stateManager.clearSelections();
        }
    }

    updateDropdownsFromSelection() {
        const state = stateManager.getState();

        if (state.selectedGenre) {
            uiManager.setDropdownValue('genreSelect', state.selectedGenre);
            this.populateSubgenreDropdown();
        }
        if (state.selectedSubgenre) {
            uiManager.setDropdownValue('subgenreSelect', state.selectedSubgenre);
            this.populateMicrogenreDropdown();
        }
        if (state.selectedMicrogenre) {
            uiManager.setDropdownValue('microgenreSelect', state.selectedMicrogenre);
            this.populateTropeDropdown();
        }
        if (state.selectedTrope) {
            uiManager.setDropdownValue('tropeSelect', state.selectedTrope);
            this.populateToneDropdown();
        }
        if (state.selectedTone) {
            uiManager.setDropdownValue('toneSelect', state.selectedTone);
        }
    }

    updateContext() {
        const state = stateManager.getState();
        uiManager.updateParametersDisplay(state);
    }

    updateModelDisplay() {
        console.log('updateModelDisplay called');
        const currentModel = stateManager.get('currentModel');
        const availableModels = stateManager.get('availableModels');
        
        console.log('Current model:', currentModel);
        console.log('Available models count:', availableModels ? Object.keys(availableModels).length : 0);
        
        // Check if DOM element exists
        const modelSelectElement = document.getElementById('modelSelect');
        if (!modelSelectElement) {
            console.error('Model select element not found in DOM!');
            return;
        }
        
        if (currentModel && availableModels && Object.keys(availableModels).length > 0) {
            console.log('Updating UI with model data');
            try {
                uiManager.updateModelSelector(currentModel, availableModels);
                uiManager.updateModelInfo(currentModel, availableModels);
                console.log('Model UI update completed successfully');
            } catch (error) {
                console.error('Error updating model UI:', error);
                modelSelectElement.innerHTML = '<option value="">Error updating models</option>';
            }
        } else {
            console.log('Missing model data - currentModel:', !!currentModel, 'availableModels:', !!availableModels);
            if (modelSelectElement) {
                modelSelectElement.innerHTML = '<option value="">Models not loaded</option>';
            }
        }
    }

    async refreshContent() {
        try {
            stateManager.set('contentLoading', true);
            const result = await apiService.loadContent();
            if (result.success) {
                stateManager.set('availableContent', result.content);
            }
        } catch (error) {
            console.error('Error refreshing content:', error);
        } finally {
            stateManager.set('contentLoading', false);
        }
    }

    destroy() {
        // Clean up event listeners
        this.cleanup.forEach(cleanupFn => cleanupFn());
        this.cleanup = [];

        // Disconnect WebSocket
        webSocketService.disconnect();

        // Clear UI manager
        uiManager.cleanup();

        this.initialized = false;
    }
}

// Initialize the enhanced chat application
const enhancedChatApp = new EnhancedChatApplication();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => enhancedChatApp.init());
} else {
    enhancedChatApp.init();
}

// Export for debugging and testing
if (typeof window !== 'undefined') {
    window.enhancedChatApp = enhancedChatApp;
}