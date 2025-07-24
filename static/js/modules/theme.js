/**
 * Theme Management Module - Handles light/dark theme switching
 * Ported from main.js for better separation of concerns
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this._initializeTheme();
    }

    /**
     * Initialize theme from localStorage or default to light
     */
    _initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme, false); // Don't save to localStorage on init
    }

    /**
     * Set the current theme
     */
    setTheme(theme, save = true) {
        if (theme !== 'light' && theme !== 'dark') {
            console.warn('Invalid theme:', theme);
            return;
        }

        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        
        if (save) {
            localStorage.setItem('theme', theme);
        }

        // Update theme icon if it exists
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
        }

        // Trigger theme change event
        this._notifyThemeChange(theme);
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        return newTheme;
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Check if current theme is dark
     */
    isDarkTheme() {
        return this.currentTheme === 'dark';
    }

    /**
     * Check if current theme is light
     */
    isLightTheme() {
        return this.currentTheme === 'light';
    }

    /**
     * Add theme change listener
     */
    onThemeChange(callback) {
        if (typeof callback !== 'function') {
            console.warn('Theme change callback must be a function');
            return;
        }

        if (!this._themeListeners) {
            this._themeListeners = [];
        }
        
        this._themeListeners.push(callback);

        // Return unsubscribe function
        return () => {
            this._themeListeners = this._themeListeners.filter(cb => cb !== callback);
        };
    }

    /**
     * Notify all theme change listeners
     */
    _notifyThemeChange(theme) {
        if (this._themeListeners) {
            this._themeListeners.forEach(callback => {
                try {
                    callback(theme);
                } catch (error) {
                    console.error('Error in theme change callback:', error);
                }
            });
        }
    }

    /**
     * Apply theme-specific styles dynamically
     */
    applyThemeStyles(styles) {
        if (!this._themeStyleSheet) {
            this._themeStyleSheet = document.createElement('style');
            this._themeStyleSheet.id = 'theme-dynamic-styles';
            document.head.appendChild(this._themeStyleSheet);
        }

        const themeStyles = styles[this.currentTheme] || '';
        this._themeStyleSheet.textContent = themeStyles;
    }

    /**
     * Get theme-specific CSS custom properties
     */
    getThemeProperties() {
        const computedStyle = getComputedStyle(document.documentElement);
        
        return {
            primary: computedStyle.getPropertyValue('--primary').trim(),
            secondary: computedStyle.getPropertyValue('--secondary').trim(),
            bgPrimary: computedStyle.getPropertyValue('--bg-primary').trim(),
            bgSecondary: computedStyle.getPropertyValue('--bg-secondary').trim(),
            textPrimary: computedStyle.getPropertyValue('--text-primary').trim(),
            textSecondary: computedStyle.getPropertyValue('--text-secondary').trim(),
            border: computedStyle.getPropertyValue('--border').trim()
        };
    }

    /**
     * Auto-detect system theme preference
     */
    detectSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Set up system theme preference listener
     */
    enableSystemThemeSync() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            const handleSystemThemeChange = (e) => {
                const systemTheme = e.matches ? 'dark' : 'light';
                this.setTheme(systemTheme);
            };

            mediaQuery.addListener(handleSystemThemeChange);
            
            // Return cleanup function
            return () => {
                mediaQuery.removeListener(handleSystemThemeChange);
            };
        }
        
        return null;
    }

    /**
     * Get theme-aware color for dynamic styling
     */
    getThemeColor(colorName, opacity = 1) {
        const properties = this.getThemeProperties();
        const color = properties[colorName];
        
        if (!color) {
            console.warn(`Unknown theme color: ${colorName}`);
            return '#000000';
        }

        // If opacity is specified and color is hex
        if (opacity < 1 && color.startsWith('#')) {
            const hex = color.slice(1);
            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);
            return `rgba(${r}, ${g}, ${b}, ${opacity})`;
        }

        return color;
    }
}

// Create singleton instance
const themeManager = new ThemeManager();

// Export for global access only (not using ES6 modules)
if (typeof window !== 'undefined') {
    window.themeManager = themeManager;
}