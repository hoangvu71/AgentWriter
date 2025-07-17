/**
 * Jest setup file for BooksWriter JavaScript TDD tests
 * This file runs before each test file to set up the testing environment
 */

import '@testing-library/jest-dom';

// Mock global objects that would normally be available in a browser
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn()
};

// Mock window object
Object.defineProperty(window, 'location', {
    value: {
        href: 'http://localhost:8000',
        origin: 'http://localhost:8000',
        pathname: '/admin',
        search: '',
        hash: ''
    },
    writable: true
});

// Mock localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn()
};
global.sessionStorage = sessionStorageMock;

// Mock alert, confirm, prompt
global.alert = jest.fn();
global.confirm = jest.fn();
global.prompt = jest.fn();

// Mock setTimeout and setInterval
global.setTimeout = jest.fn((callback, delay) => {
    return setTimeout(callback, delay);
});
global.setInterval = jest.fn((callback, delay) => {
    return setInterval(callback, delay);
});
global.clearTimeout = jest.fn();
global.clearInterval = jest.fn();

// Mock fetch globally
global.fetch = jest.fn();

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
    send: jest.fn(),
    close: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    readyState: 1,
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3
}));

// Mock FormData
global.FormData = jest.fn().mockImplementation(() => ({
    append: jest.fn(),
    get: jest.fn(),
    has: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
    entries: jest.fn(),
    keys: jest.fn(),
    values: jest.fn()
}));

// Mock HTMLElement methods
HTMLElement.prototype.scrollIntoView = jest.fn();
HTMLElement.prototype.focus = jest.fn();
HTMLElement.prototype.click = jest.fn();

// Mock DOM methods
document.createRange = jest.fn(() => ({
    setStart: jest.fn(),
    setEnd: jest.fn(),
    commonAncestorContainer: {
        nodeName: 'BODY',
        ownerDocument: document,
    },
    selectNodeContents: jest.fn(),
    selectNode: jest.fn(),
    collapse: jest.fn(),
    cloneRange: jest.fn(),
    deleteContents: jest.fn(),
    extractContents: jest.fn(),
    insertNode: jest.fn(),
    surroundContents: jest.fn(),
    toString: jest.fn(() => ''),
    getBoundingClientRect: jest.fn(() => ({
        top: 0,
        left: 0,
        bottom: 0,
        right: 0,
        width: 0,
        height: 0,
        x: 0,
        y: 0,
    })),
}));

// Mock window.getSelection
window.getSelection = jest.fn(() => ({
    toString: jest.fn(() => ''),
    addRange: jest.fn(),
    removeAllRanges: jest.fn(),
    getRangeAt: jest.fn(),
    rangeCount: 0,
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock CSS functions
global.getComputedStyle = jest.fn(() => ({
    getPropertyValue: jest.fn(() => ''),
    setProperty: jest.fn(),
}));

// Set up custom matchers for TDD testing
expect.extend({
    toHaveBeenCalledWithValidData(received, ...args) {
        const pass = received.mock.calls.some(call => 
            call.length > 0 && typeof call[0] === 'object' && call[0] !== null
        );
        
        if (pass) {
            return {
                message: () => `Expected ${received.getMockName()} not to have been called with valid data`,
                pass: true,
            };
        } else {
            return {
                message: () => `Expected ${received.getMockName()} to have been called with valid data`,
                pass: false,
            };
        }
    },
    
    toHaveValidApiStructure(received) {
        const pass = received && 
                   typeof received === 'object' && 
                   received.hasOwnProperty('success') &&
                   typeof received.success === 'boolean';
        
        if (pass) {
            return {
                message: () => `Expected object not to have valid API structure`,
                pass: true,
            };
        } else {
            return {
                message: () => `Expected object to have valid API structure with 'success' property`,
                pass: false,
            };
        }
    }
});

// Reset all mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset fetch mock to default behavior
    fetch.mockClear();
    fetch.mockResolvedValue({
        ok: true,
        json: async () => ({}),
        text: async () => '',
        status: 200,
        statusText: 'OK'
    });
    
    // Reset localStorage
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
    
    // Reset sessionStorage
    sessionStorageMock.getItem.mockClear();
    sessionStorageMock.setItem.mockClear();
    sessionStorageMock.removeItem.mockClear();
    sessionStorageMock.clear.mockClear();
    
    // Reset console mocks
    console.log.mockClear();
    console.error.mockClear();
    console.warn.mockClear();
    console.info.mockClear();
    console.debug.mockClear();
});

// Clean up after each test
afterEach(() => {
    // Clear any timers that might be running
    jest.clearAllTimers();
    
    // Reset DOM changes
    document.body.innerHTML = '';
    document.head.innerHTML = '';
});

// Global test utilities
global.testUtils = {
    // Create a mock DOM element with common properties
    createMockElement: (tag = 'div', properties = {}) => {
        const element = document.createElement(tag);
        Object.assign(element, {
            innerHTML: '',
            textContent: '',
            style: {},
            classList: {
                add: jest.fn(),
                remove: jest.fn(),
                toggle: jest.fn(),
                contains: jest.fn(() => false)
            },
            setAttribute: jest.fn(),
            getAttribute: jest.fn(),
            hasAttribute: jest.fn(() => false),
            removeAttribute: jest.fn(),
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
            appendChild: jest.fn(),
            removeChild: jest.fn(),
            focus: jest.fn(),
            click: jest.fn(),
            ...properties
        });
        return element;
    },
    
    // Create a mock form with common form properties
    createMockForm: (fields = {}) => {
        const form = global.testUtils.createMockElement('form', {
            reset: jest.fn(),
            submit: jest.fn(),
            checkValidity: jest.fn(() => true),
            reportValidity: jest.fn(() => true),
            ...fields
        });
        return form;
    },
    
    // Create a mock API response
    createMockApiResponse: (data = {}, options = {}) => {
        return {
            ok: options.ok !== undefined ? options.ok : true,
            status: options.status || 200,
            statusText: options.statusText || 'OK',
            json: async () => data,
            text: async () => JSON.stringify(data),
            headers: new Map(Object.entries(options.headers || {}))
        };
    },
    
    // Wait for async operations to complete
    waitForAsync: async () => {
        return new Promise(resolve => setTimeout(resolve, 0));
    }
};

// Add console message for test setup completion
console.log('🧪 BooksWriter TDD Test Environment Setup Complete');
console.log('🚀 Ready for Test-Driven Development!');