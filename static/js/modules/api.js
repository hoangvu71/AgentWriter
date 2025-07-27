/**
 * API Module - Handles all HTTP requests and API communication
 * Extracted from monolithic chat.js for better separation of concerns
 */

class APIService {
    constructor() {
        this.baseURL = '';
    }

    /**
     * Generic fetch wrapper with error handling and security
     */
    async fetchJSON(url, options = {}) {
        try {
            // Use security service for secure fetch if available
            if (window.securityService) {
                const secureHeaders = window.securityService.addCSRFToHeaders({
                    'Content-Type': 'application/json',
                    ...options.headers
                });
                
                const response = await window.securityService.secureFetch(url, {
                    headers: secureHeaders,
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } else {
                // Fallback to regular fetch
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            }
        } catch (error) {
            console.error(`API Error for ${url}:`, error);
            throw error;
        }
    }

    /**
     * Load available models from the API
     */
    async loadModels() {
        try {
            const data = await this.fetchJSON('/models');
            return {
                success: true,
                data: data
            };
        } catch (error) {
            console.error('Error loading models:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Switch to a different model
     */
    async switchModel(modelId) {
        try {
            const data = await this.fetchJSON(`/models/${modelId}/switch`, {
                method: 'POST'
            });
            return {
                success: data.success,
                data: data
            };
        } catch (error) {
            console.error('Error switching model:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Load genre hierarchy and parameters
     */
    async loadParameters() {
        try {
            // Load genres with complete hierarchy
            const genresResponse = await this.fetchJSON('/api/genres');
            
            let genresData = {
                success: false,
                genres: [],
                subgenres: [],
                microgenres: [],
                tropes: [],
                tones: []
            };

            if (genresResponse && genresResponse.success) {
                genresData = {
                    success: true,
                    genres: genresResponse.genres || [],
                    subgenres: genresResponse.subgenres || [],
                    microgenres: genresResponse.microgenres || [],
                    tropes: genresResponse.tropes || [],
                    tones: genresResponse.tones || []
                };
            }

            // Load target audiences separately
            const audiencesResponse = await this.fetchJSON('/api/target-audiences');
            
            let audiencesData = {
                success: false,
                audiences: []
            };

            if (audiencesResponse && audiencesResponse.success) {
                audiencesData = {
                    success: true,
                    audiences: audiencesResponse.audiences || []
                };
            }

            return {
                success: genresData.success || audiencesData.success,
                genres: genresData,
                audiences: audiencesData
            };
            
        } catch (error) {
            console.error('Error loading parameters:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Load content for selection
     */
    async loadContent() {
        try {
            const data = await this.fetchJSON('/api/content-selection');
            return {
                success: data.success || false,
                content: data.content || []
            };
        } catch (error) {
            console.error('Error loading content:', error);
            return {
                success: false,
                content: [],
                error: error.message
            };
        }
    }

    /**
     * Search content by query
     */
    async searchContent(query, contentType = 'plot', userId = null) {
        try {
            const params = new URLSearchParams({
                q: query,
                type: contentType
            });
            
            if (userId) {
                params.append('user_id', userId);
            }

            const data = await this.fetchJSON(`/api/search?${params}`);
            return {
                success: true,
                results: data.results || []
            };
        } catch (error) {
            console.error('Error searching content:', error);
            return {
                success: false,
                results: [],
                error: error.message
            };
        }
    }

    /**
     * Submit feedback or rating
     */
    async submitFeedback(feedbackData) {
        try {
            const data = await this.fetchJSON('/api/feedback', {
                method: 'POST',
                body: JSON.stringify(feedbackData)
            });
            return {
                success: data.success || false,
                message: data.message || 'Feedback submitted'
            };
        } catch (error) {
            console.error('Error submitting feedback:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get user preferences
     */
    async getUserPreferences(userId) {
        try {
            const data = await this.fetchJSON(`/api/users/${userId}/preferences`);
            return {
                success: true,
                preferences: data.preferences || {}
            };
        } catch (error) {
            console.error('Error loading user preferences:', error);
            return {
                success: false,
                preferences: {},
                error: error.message
            };
        }
    }

    /**
     * Update user preferences
     */
    async updateUserPreferences(userId, preferences) {
        try {
            const data = await this.fetchJSON(`/api/users/${userId}/preferences`, {
                method: 'PUT',
                body: JSON.stringify(preferences)
            });
            return {
                success: data.success || false,
                message: data.message || 'Preferences updated'
            };
        } catch (error) {
            console.error('Error updating user preferences:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Create singleton instance
const apiService = new APIService();

// Export for ES6 modules and global access
if (typeof window !== 'undefined') {
    window.apiService = apiService;
}

