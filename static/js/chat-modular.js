/**
 * Modular Chat Application - Refactored from monolithic chat.js
 * Uses modern modular architecture with separation of concerns
 */

// Since we can't use ES6 imports in browsers without bundlers yet,
// we'll rely on the modules being loaded via script tags and available as globals
// In a production setup, this would use proper ES6 imports with a bundler

class ChatApplication {
    constructor() {
        this.initialized = false;
        this.cleanup = [];
    }

    /**
     * Initialize the chat application
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

            // Initialize modules
            this.setupWebSocket();
            this.setupStateManagement();
            this.setupEventHandlers();
            await this.loadInitialData();

            this.initialized = true;
            console.log('Chat application initialized successfully');
        } catch (error) {
            console.error('Failed to initialize chat application:', error);
        }
    }

    /**
     * Setup WebSocket connection and message handlers
     */
    setupWebSocket() {
        // Handle connection state changes
        webSocketService.onConnectionStateChange((state, message) => {
            uiManager.updateConnectionStatus(state, message);
        });

        // Handle different message types
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
    }

    /**
     * Setup DOM event handlers
     */
    setupEventHandlers() {
        // Message input and send button handlers
        const cleanup1 = uiManager.addEventListener('messageInput', 'keypress', (e) => {
            if (e.key === 'Enter') {
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
        const cleanup4 = uiManager.addEventListener('genreSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('genreSelect');
            stateManager.set('selectedGenre', selected);
        });
        this.cleanup.push(cleanup4);

        const cleanup5 = uiManager.addEventListener('subgenreSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('subgenreSelect');
            stateManager.set('selectedSubgenre', selected);
        });
        this.cleanup.push(cleanup5);

        const cleanup6 = uiManager.addEventListener('microgenreSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('microgenreSelect');
            stateManager.set('selectedMicrogenre', selected);
        });
        this.cleanup.push(cleanup6);

        const cleanup7 = uiManager.addEventListener('tropeSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('tropeSelect');
            stateManager.set('selectedTrope', selected);
        });
        this.cleanup.push(cleanup7);

        const cleanup8 = uiManager.addEventListener('toneSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('toneSelect');
            stateManager.set('selectedTone', selected);
        });
        this.cleanup.push(cleanup8);

        const cleanup9 = uiManager.addEventListener('audienceSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('audienceSelect');
            stateManager.set('selectedAudience', selected);
        });
        this.cleanup.push(cleanup9);

        const cleanup10 = uiManager.addEventListener('contentSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('contentSelect');
            stateManager.set('selectedContent', selected);
        });
        this.cleanup.push(cleanup10);

        // Complete package selection handler
        const cleanup11 = uiManager.addEventListener('completePackageSelect', 'change', () => {
            this.selectCompletePackage();
        });
        this.cleanup.push(cleanup11);

        // Content selection handler
        const cleanup12 = uiManager.addEventListener('contentSelect', 'change', () => {
            const selected = uiManager.getDropdownValue('contentSelect');
            stateManager.set('selectedContent', selected);
        });
        this.cleanup.push(cleanup12);

        // Refresh content button handler
        const cleanup13 = uiManager.addEventListener('refreshContent', 'click', () => {
            this.refreshContent();
        });
        this.cleanup.push(cleanup13);
    }

    /**
     * Load initial data from APIs
     */
    async loadInitialData() {
        stateManager.set('loading', true);

        try {
            // Load models
            const modelsResult = await apiService.loadModels();
            if (modelsResult.success) {
                stateManager.setModelData(
                    modelsResult.data.current_model,
                    modelsResult.data.available_models
                );
            }

            // Load parameters
            const paramsResult = await apiService.loadParameters();
            if (paramsResult.success) {
                if (paramsResult.genres.success) {
                    stateManager.setGenreData(paramsResult.genres);
                }
                if (paramsResult.audiences.success) {
                    stateManager.set('allAudiences', paramsResult.audiences.audiences);
                }
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
     * Handle stream chunk messages
     */
    handleStreamChunk(data) {
        let currentMessage = document.getElementById('current-agent-message');
        if (!currentMessage) {
            currentMessage = uiManager.appendChatMessage('', 'message agent-message');
            currentMessage.id = 'current-agent-message';
            currentMessage.style.whiteSpace = 'pre-wrap';
        }
        currentMessage.textContent += data.content;
        uiManager.scrollChatToBottom();
    }

    /**
     * Handle structured response messages
     */
    handleStructuredResponse(data) {
        const chatContainer = uiManager.getElement('chat');
        if (chatContainer) {
            const structuredMessage = uiManager.createStructuredResponse(data);
            chatContainer.appendChild(structuredMessage);
            uiManager.scrollChatToBottom();
        }
    }

    /**
     * Handle stream end messages
     */
    handleStreamEnd(data) {
        const currentMessage = document.getElementById('current-agent-message');
        if (currentMessage) {
            currentMessage.id = '';
            // Format the final message
            currentMessage.innerHTML = uiManager.constructor.formatMessage(currentMessage.textContent);
        }
        
        // Log structured responses for debugging
        if (data.structured_responses) {
            console.log('Structured responses received:', data.structured_responses);
        }
    }

    /**
     * Handle error messages
     */
    handleError(data) {
        uiManager.appendChatMessage(
            'Error: ' + data.content, 
            'message agent-message error-message'
        );
    }

    /**
     * Send message through WebSocket
     */
    sendMessage() {
        const message = uiManager.getContent('messageInput');
        if (!message.trim()) return;

        // Display user message
        uiManager.appendChatMessage(message, 'message user-message');

        // Build context from current state
        const context = stateManager.buildContextObject();

        // Send message with context
        const success = webSocketService.sendMessage(message, context);
        
        if (success) {
            uiManager.setContent('messageInput', '');
        } else {
            uiManager.showError('chat', 'Failed to send message - not connected');
        }
    }

    /**
     * Switch AI model
     */
    async switchModel() {
        const modelId = uiManager.getDropdownValue('modelSelect', false);
        if (!modelId) return;

        try {
            const result = await apiService.switchModel(modelId);
            if (result.success) {
                console.log('Model switched successfully');
                // Reload models to update display
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

    /**
     * Toggle parameters panel
     */
    toggleParameters() {
        const isVisible = uiManager.toggleVisibility('parametersContent');
        const button = uiManager.getElement('toggleParams');
        if (button) {
            button.textContent = isVisible ? '▲' : '▼';
        }
        stateManager.set('parametersVisible', isVisible);
    }

    /**
     * Handle genre selection change
     */
    onGenreChange() {
        const selectedGenre = stateManager.get('selectedGenre');
        
        // Clear downstream selections
        stateManager.update({
            selectedSubgenre: null,
            selectedMicrogenre: null,
            selectedTrope: null,
            selectedTone: null
        });

        this.populateSubgenreDropdown();
        this.updateContext();
    }

    /**
     * Handle subgenre selection change
     */
    onSubgenreChange() {
        // Clear downstream selections
        stateManager.update({
            selectedMicrogenre: null,
            selectedTrope: null,
            selectedTone: null
        });

        this.populateMicrogenreDropdown();
        this.updateContext();
    }

    /**
     * Handle microgenre selection change
     */
    onMicrogenreChange() {
        // Clear downstream selections
        stateManager.update({
            selectedTrope: null,
            selectedTone: null
        });

        this.populateTropeDropdown();
        this.updateContext();
    }

    /**
     * Handle trope selection change
     */
    onTropeChange() {
        // Clear downstream selections
        stateManager.set('selectedTone', null);

        this.populateToneDropdown();
        this.updateContext();
    }

    /**
     * Populate genre dropdown
     */
    populateGenreDropdown() {
        const genres = stateManager.get('allGenres');
        uiManager.populateDropdown('genreSelect', genres, 'Select Genre...');
    }

    /**
     * Populate audience dropdown
     */
    populateAudienceDropdown() {
        const audiences = stateManager.get('allAudiences');
        const formattedAudiences = audiences.map(audience => ({
            ...audience,
            name: `${audience.age_group} - ${audience.gender} - ${audience.sexual_orientation}`
        }));
        uiManager.populateDropdown('audienceSelect', formattedAudiences, 'Select Audience...');
    }

    /**
     * Populate content dropdown
     */
    populateContentDropdown() {
        const content = stateManager.get('availableContent');
        const formattedContent = content.map(item => ({
            ...item,
            name: `${item.type.toUpperCase()} - ${item.title}`
        }));
        uiManager.populateDropdown('contentSelect', formattedContent, 'Select Content...');
    }

    /**
     * Populate subgenre dropdown based on selected genre
     */
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

    /**
     * Populate microgenre dropdown based on selected subgenre
     */
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

    /**
     * Populate trope dropdown based on selected microgenre
     */
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

    /**
     * Populate tone dropdown based on selected trope
     */
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

    /**
     * Select complete package (all hierarchy at once)
     */
    selectCompletePackage() {
        const packageData = uiManager.getDropdownValue('completePackageSelect');
        
        if (packageData) {
            // Set all selections based on the complete package
            stateManager.update({
                selectedGenre: packageData.genre,
                selectedSubgenre: packageData.subgenre,
                selectedMicrogenre: packageData.microgenre,
                selectedTrope: packageData.trope,
                selectedTone: packageData.tone
            });

            // Update dropdowns to reflect selections
            this.updateDropdownsFromSelection();
        } else {
            // Clear all selections
            stateManager.clearSelections();
        }
    }

    /**
     * Update dropdowns to match current state
     */
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

    /**
     * Update context display
     */
    updateContext() {
        const state = stateManager.getState();
        uiManager.updateParametersDisplay(state);
    }

    /**
     * Update model display
     */
    updateModelDisplay() {
        const currentModel = stateManager.get('currentModel');
        const availableModels = stateManager.get('availableModels');
        
        if (currentModel && availableModels) {
            uiManager.updateModelSelector(currentModel, availableModels);
            uiManager.updateModelInfo(currentModel, availableModels);
        }
    }

    /**
     * Refresh content list
     */
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

    /**
     * Cleanup resources
     */
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

// Initialize the chat application
const chatApp = new ChatApplication();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => chatApp.init());
} else {
    chatApp.init();
}

// Export for debugging and testing
if (typeof window !== 'undefined') {
    window.chatApp = chatApp;
}