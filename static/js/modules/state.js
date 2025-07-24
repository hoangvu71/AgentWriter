/**
 * State Management Module - Centralized state management with event system
 * Replaces global variables from monolithic chat.js with encapsulated state
 */

class StateManager {
    constructor() {
        // Private state object
        this._state = {
            // Genre hierarchy state
            selectedGenre: null,
            selectedSubgenre: null,
            selectedMicrogenre: null,
            selectedTrope: null,
            selectedTone: null,
            selectedAudience: null,
            selectedContent: null,

            // Data collections
            allGenres: [],
            allSubgenres: [],
            allMicrogenres: [],
            allTropes: [],
            allTones: [],
            allAudiences: [],

            // Model state
            currentModel: null,
            availableModels: {},

            // UI state
            parametersVisible: false,
            loading: false,
            error: null,

            // User state
            userId: "user_" + Math.random().toString(36).substr(2, 9),
            sessionId: null,

            // Content state
            availableContent: [],
            contentLoading: false
        };

        // Event listeners for state changes
        this._listeners = new Map();
        this._stateHistory = [];
        this._maxHistorySize = 50;
    }

    /**
     * Get current state (read-only copy)
     */
    getState() {
        return JSON.parse(JSON.stringify(this._state));
    }

    /**
     * Get specific state value
     */
    get(key) {
        return this._state[key];
    }

    /**
     * Set state value and notify listeners
     */
    set(key, value) {
        const oldValue = this._state[key];
        
        if (oldValue === value) {
            return; // No change
        }

        // Store in history
        this._addToHistory(key, oldValue, value);

        // Update state
        this._state[key] = value;

        // Notify listeners
        this._notifyListeners(key, value, oldValue);
    }

    /**
     * Update multiple state values atomically
     */
    update(updates) {
        const changes = [];
        
        for (const [key, value] of Object.entries(updates)) {
            const oldValue = this._state[key];
            if (oldValue !== value) {
                changes.push({ key, value, oldValue });
                this._state[key] = value;
                this._addToHistory(key, oldValue, value);
            }
        }

        // Notify all listeners for changed values
        changes.forEach(({ key, value, oldValue }) => {
            this._notifyListeners(key, value, oldValue);
        });
    }

    /**
     * Reset specific state values
     */
    reset(keys = null) {
        const keysToReset = keys || Object.keys(this._state);
        const updates = {};

        keysToReset.forEach(key => {
            if (key.startsWith('selected')) {
                updates[key] = null;
            } else if (key.startsWith('all') && Array.isArray(this._state[key])) {
                updates[key] = [];
            } else if (key === 'error') {
                updates[key] = null;
            } else if (key === 'loading' || key === 'contentLoading') {
                updates[key] = false;
            }
        });

        this.update(updates);
    }

    /**
     * Subscribe to state changes
     */
    subscribe(key, listener) {
        if (!this._listeners.has(key)) {
            this._listeners.set(key, []);
        }
        this._listeners.get(key).push(listener);

        // Return unsubscribe function
        return () => {
            const listeners = this._listeners.get(key);
            if (listeners) {
                const index = listeners.indexOf(listener);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
            }
        };
    }

    /**
     * Subscribe to any state changes
     */
    subscribeAll(listener) {
        return this.subscribe('*', listener);
    }

    /**
     * Notify listeners of state changes
     */
    _notifyListeners(key, value, oldValue) {
        // Notify specific key listeners
        if (this._listeners.has(key)) {
            this._listeners.get(key).forEach(listener => {
                try {
                    listener(value, oldValue, key);
                } catch (error) {
                    console.error(`Error in state listener for ${key}:`, error);
                }
            });
        }

        // Notify global listeners
        if (this._listeners.has('*')) {
            this._listeners.get('*').forEach(listener => {
                try {
                    listener(value, oldValue, key);
                } catch (error) {
                    console.error('Error in global state listener:', error);
                }
            });
        }
    }

    /**
     * Add change to history
     */
    _addToHistory(key, oldValue, newValue) {
        this._stateHistory.push({
            key,
            oldValue,
            newValue,
            timestamp: new Date().toISOString()
        });

        // Limit history size
        if (this._stateHistory.length > this._maxHistorySize) {
            this._stateHistory.shift();
        }
    }

    /**
     * Get state history
     */
    getHistory() {
        return [...this._stateHistory];
    }

    /**
     * Clear selections (convenience method)
     */
    clearSelections() {
        this.update({
            selectedGenre: null,
            selectedSubgenre: null,
            selectedMicrogenre: null,
            selectedTrope: null,
            selectedTone: null,
            selectedAudience: null,
            selectedContent: null
        });
    }

    /**
     * Set genre hierarchy data
     */
    setGenreData(data) {
        this.update({
            allGenres: data.genres || [],
            allSubgenres: data.subgenres || [],
            allMicrogenres: data.microgenres || [],
            allTropes: data.tropes || [],
            allTones: data.tones || []
        });
    }

    /**
     * Set model data
     */
    setModelData(currentModel, availableModels) {
        this.update({
            currentModel,
            availableModels
        });
    }

    /**
     * Build context object from current selections
     */
    buildContextObject() {
        const state = this._state;
        
        // Check if any parameters are selected
        if (!state.selectedGenre && !state.selectedSubgenre && !state.selectedMicrogenre && 
            !state.selectedTrope && !state.selectedTone && !state.selectedAudience && !state.selectedContent) {
            return null;
        }
        
        const context = {};
        
        // Content selection for improvement
        if (state.selectedContent) {
            context.content_selection = {
                id: state.selectedContent.id,
                type: state.selectedContent.type,
                title: state.selectedContent.title
            };
        }
        
        // Genre hierarchy - structured instead of verbose text
        const genreHierarchy = {};
        if (state.selectedGenre) {
            genreHierarchy.genre = {
                id: state.selectedGenre.id,
                name: state.selectedGenre.name,
                description: state.selectedGenre.description
            };
        }
        if (state.selectedSubgenre) {
            genreHierarchy.subgenre = {
                id: state.selectedSubgenre.id,
                name: state.selectedSubgenre.name,
                description: state.selectedSubgenre.description
            };
        }
        if (state.selectedMicrogenre) {
            genreHierarchy.microgenre = {
                id: state.selectedMicrogenre.id,
                name: state.selectedMicrogenre.name,
                description: state.selectedMicrogenre.description
            };
        }
        if (Object.keys(genreHierarchy).length > 0) {
            context.genre_hierarchy = genreHierarchy;
        }
        
        // Story elements - structured instead of verbose text
        const storyElements = {};
        if (state.selectedTrope) {
            storyElements.trope = {
                id: state.selectedTrope.id,
                name: state.selectedTrope.name,
                description: state.selectedTrope.description
            };
        }
        if (state.selectedTone) {
            storyElements.tone = {
                id: state.selectedTone.id,
                name: state.selectedTone.name,
                description: state.selectedTone.description
            };
        }
        if (Object.keys(storyElements).length > 0) {
            context.story_elements = storyElements;
        }
        
        // Target audience - clean structure instead of verbose analysis
        if (state.selectedAudience) {
            context.target_audience = {
                age_group: state.selectedAudience.age_group,
                gender: state.selectedAudience.gender,
                sexual_orientation: state.selectedAudience.sexual_orientation
            };
        }
        
        return Object.keys(context).length > 0 ? context : null;
    }

    /**
     * Validate state consistency (for debugging)
     */
    validateState() {
        const issues = [];
        const state = this._state;

        // Check genre hierarchy consistency
        if (state.selectedSubgenre && !state.selectedGenre) {
            issues.push('Subgenre selected without genre');
        }
        if (state.selectedMicrogenre && !state.selectedSubgenre) {
            issues.push('Microgenre selected without subgenre');
        }
        if (state.selectedTrope && !state.selectedMicrogenre) {
            issues.push('Trope selected without microgenre');
        }
        if (state.selectedTone && !state.selectedTrope) {
            issues.push('Tone selected without trope');
        }

        return issues;
    }

    /**
     * Export state for debugging or persistence
     */
    exportState() {
        return {
            state: this.getState(),
            history: this.getHistory(),
            validation: this.validateState()
        };
    }
}

// Create singleton instance
const stateManager = new StateManager();

// Export for ES6 modules and global access
if (typeof window !== 'undefined') {
    window.stateManager = stateManager;
}

