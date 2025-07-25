/**
 * Security Module - Handles HTML sanitization, CSRF protection, and input validation
 * This module provides security utilities to prevent XSS and other security vulnerabilities
 */

class SecurityService {
    constructor() {
        this.csrfToken = null;
        this.sanitizerConfig = {
            ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'span', 'div'],
            ALLOWED_ATTR: ['href', 'target', 'class', 'id'],
            ALLOW_DATA_ATTR: false,
            KEEP_CONTENT: true,
            RETURN_DOM_FRAGMENT: false,
            RETURN_DOM: false,
            FORBID_TAGS: ['script', 'object', 'embed', 'iframe', 'form', 'input', 'textarea', 'select', 'button'],
            FORBID_ATTR: ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur', 'onchange', 'onsubmit']
        };
        this.initCSRFToken();
    }

    /**
     * Initialize CSRF token from meta tag
     */
    initCSRFToken() {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            this.csrfToken = csrfMeta.getAttribute('content');
        }
    }

    /**
     * Get CSRF token for requests
     */
    getCSRFToken() {
        return this.csrfToken;
    }

    /**
     * Sanitize HTML content using DOMPurify
     */
    sanitizeHTML(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }

        // Check if DOMPurify is available
        if (typeof DOMPurify === 'undefined') {
            console.warn('DOMPurify not available, falling back to text content');
            return this.escapeHTML(html);
        }

        try {
            // Use DOMPurify with our security configuration
            return DOMPurify.sanitize(html, this.sanitizerConfig);
        } catch (error) {
            console.error('Error sanitizing HTML:', error);
            return this.escapeHTML(html);
        }
    }

    /**
     * Escape HTML entities as fallback
     */
    escapeHTML(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }

        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Safely set HTML content with sanitization
     */
    safeSetHTML(element, html) {
        if (!element) {
            console.warn('Element not provided for safeSetHTML');
            return;
        }

        const sanitizedHTML = this.sanitizeHTML(html);
        element.innerHTML = sanitizedHTML;
    }

    /**
     * Validate and sanitize user input
     */
    validateInput(input, type = 'text', maxLength = 2000) {
        if (!input || typeof input !== 'string') {
            return '';
        }

        // Basic length validation
        if (input.length > maxLength) {
            console.warn(`Input exceeds maximum length of ${maxLength} characters`);
            input = input.substring(0, maxLength);
        }

        // Type-specific validation
        switch (type) {
            case 'message':
                return this.validateMessage(input);
            case 'json':
                return this.validateJSON(input);
            case 'url':
                return this.validateURL(input);
            default:
                return this.sanitizeText(input);
        }
    }

    /**
     * Validate message content
     */
    validateMessage(message) {
        if (!message || typeof message !== 'string') {
            return '';
        }

        // Remove potentially dangerous patterns
        const dangerousPatterns = [
            /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
            /javascript:/gi,
            /vbscript:/gi,
            /data:text\/html/gi,
            /on\w+\s*=/gi
        ];

        let cleanMessage = message;
        dangerousPatterns.forEach(pattern => {
            cleanMessage = cleanMessage.replace(pattern, '');
        });

        return cleanMessage.trim();
    }

    /**
     * Validate JSON data
     */
    validateJSON(jsonString) {
        try {
            const parsed = JSON.parse(jsonString);
            // Re-stringify to ensure clean JSON
            return JSON.stringify(parsed);
        } catch (error) {
            console.warn('Invalid JSON provided:', error);
            return '';
        }
    }

    /**
     * Validate URL
     */
    validateURL(url) {
        if (!url || typeof url !== 'string') {
            return '';
        }

        try {
            // Check if it's a relative URL starting with /
            if (url.startsWith('/')) {
                // Relative URLs are valid for same-origin requests
                return url;
            }
            
            // Check if it's a protocol-relative URL
            if (url.startsWith('//')) {
                // Protocol-relative URLs are valid
                return url;
            }
            
            // For absolute URLs, validate protocol
            const urlObj = new URL(url);
            // Only allow http, https, ws, and wss protocols
            const allowedProtocols = ['http:', 'https:', 'ws:', 'wss:'];
            if (!allowedProtocols.includes(urlObj.protocol)) {
                console.warn('Invalid URL protocol:', urlObj.protocol);
                return '';
            }
            return urlObj.toString();
        } catch (error) {
            // If URL constructor fails, it might be a relative URL without leading /
            // Return empty string for safety
            console.warn('Invalid URL format:', url, error);
            return '';
        }
    }

    /**
     * Sanitize plain text content
     */
    sanitizeText(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }

        // Remove null bytes and control characters except newlines and tabs
        return text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
    }

    /**
     * Validate WebSocket message data
     */
    validateWebSocketMessage(data) {
        if (!data || typeof data !== 'object') {
            console.warn('Invalid WebSocket message data');
            return null;
        }

        const validatedData = {};

        // Validate message type
        if (data.type && typeof data.type === 'string') {
            validatedData.type = this.sanitizeText(data.type);
        }

        // Validate content
        if (data.content && typeof data.content === 'string') {
            validatedData.content = this.validateMessage(data.content);
        }

        // Validate context
        if (data.context && typeof data.context === 'object') {
            validatedData.context = this.validateContext(data.context);
        }

        // Validate user_id
        if (data.user_id && typeof data.user_id === 'string') {
            validatedData.user_id = this.sanitizeText(data.user_id);
        }

        // Validate timestamp
        if (data.timestamp && typeof data.timestamp === 'string') {
            const date = new Date(data.timestamp);
            if (!isNaN(date.getTime())) {
                validatedData.timestamp = data.timestamp;
            }
        }

        return validatedData;
    }

    /**
     * Validate context object
     */
    validateContext(context) {
        if (!context || typeof context !== 'object') {
            return {};
        }

        const validatedContext = {};
        const allowedKeys = ['selectedGenre', 'selectedSubgenre', 'selectedMicrogenre', 'selectedTrope', 'selectedTone', 'selectedAudience', 'selectedContent'];

        allowedKeys.forEach(key => {
            if (context[key]) {
                if (typeof context[key] === 'object') {
                    validatedContext[key] = this.validateContextObject(context[key]);
                } else if (typeof context[key] === 'string') {
                    validatedContext[key] = this.sanitizeText(context[key]);
                }
            }
        });

        return validatedContext;
    }

    /**
     * Validate context object properties
     */
    validateContextObject(obj) {
        if (!obj || typeof obj !== 'object') {
            return {};
        }

        const validated = {};
        const allowedProps = ['id', 'name', 'description', 'type', 'title', 'genre_id', 'subgenre_id', 'microgenre_id', 'trope_id', 'age_group', 'gender', 'sexual_orientation'];

        allowedProps.forEach(prop => {
            if (obj[prop] && typeof obj[prop] === 'string') {
                validated[prop] = this.sanitizeText(obj[prop]);
            } else if (obj[prop] && typeof obj[prop] === 'number') {
                validated[prop] = obj[prop];
            }
        });

        return validated;
    }

    /**
     * Add CSRF token to fetch requests
     */
    addCSRFToHeaders(headers = {}) {
        if (this.csrfToken) {
            headers['X-CSRF-Token'] = this.csrfToken;
        }
        return headers;
    }

    /**
     * Create secure fetch wrapper
     */
    async secureFetch(url, options = {}) {
        // Add CSRF token to headers
        options.headers = this.addCSRFToHeaders(options.headers || {});

        // Validate URL
        const validatedURL = this.validateURL(url);
        if (!validatedURL) {
            throw new Error('Invalid URL provided: ' + url);
        }

        try {
            const response = await fetch(validatedURL, options);
            return response;
        } catch (error) {
            console.error('Secure fetch error:', error);
            throw error;
        }
    }

    /**
     * Format message text safely (replacement for direct innerHTML usage)
     */
    formatMessageSafely(text) {
        if (!text) return '';
        
        // First escape any HTML to prevent XSS
        let safeText = this.escapeHTML(text);
        
        // Then apply safe formatting
        safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        safeText = safeText.replace(/\*(.*?)\*/g, '<em>$1</em>');
        safeText = safeText.replace(/`(.*?)`/g, '<code>$1</code>');
        safeText = safeText.replace(/\n/g, '<br>');
        
        // Apply number list formatting safely
        safeText = safeText.replace(/^(\d+\.\s)(.+?)$/gm, '<strong>$1</strong>$2');
        
        // Sanitize the final result
        return this.sanitizeHTML(safeText);
    }

    /**
     * Create safe DOM element with text content
     */
    createSafeElement(tagName, textContent = '', className = '') {
        const element = document.createElement(tagName);
        if (textContent) {
            element.textContent = textContent; // Use textContent instead of innerHTML
        }
        if (className) {
            element.className = className;
        }
        return element;
    }

    /**
     * Remove all event handlers from inline attributes (security cleanup)
     */
    cleanupInlineEventHandlers(element) {
        if (!element) return;

        const eventAttributes = ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur', 'onchange', 'onsubmit', 'onkeyup', 'onkeydown'];
        
        eventAttributes.forEach(attr => {
            if (element.hasAttribute(attr)) {
                element.removeAttribute(attr);
                console.warn(`Removed potentially dangerous ${attr} attribute`);
            }
        });

        // Also clean child elements
        const children = element.querySelectorAll('*');
        children.forEach(child => {
            eventAttributes.forEach(attr => {
                if (child.hasAttribute(attr)) {
                    child.removeAttribute(attr);
                    console.warn(`Removed potentially dangerous ${attr} attribute from child element`);
                }
            });
        });
    }
}

// Create singleton instance
const securityService = new SecurityService();

// Export for global access
if (typeof window !== 'undefined') {
    window.securityService = securityService;
}