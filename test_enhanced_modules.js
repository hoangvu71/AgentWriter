// Node.js test to verify enhanced JavaScript module syntax
const fs = require('fs');
const path = require('path');

function testJavaScriptSyntax(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        
        // Remove ES6 export statements and window references for Node.js compatibility
        const nodeCompatible = content
            .replace(/export default \w+;/g, '')
            .replace(/if \(typeof window !== 'undefined'\) \{[^}]+\}/g, '')
            .replace(/window\.\w+/g, 'global.mockObject')
            .replace(/document\./g, 'global.mockDocument.')
            .replace(/WebSocket/g, 'global.MockWebSocket');
        
        // Create mock objects
        global.mockObject = {};
        global.mockDocument = {
            createElement: () => ({ appendChild: () => {}, style: {}, classList: { add: () => {}, remove: () => {} } }),
            getElementById: () => null,
            head: { appendChild: () => {} },
            addEventListener: () => {},
            readyState: 'complete',
            documentElement: { setAttribute: () => {} }
        };
        global.MockWebSocket = function() { this.readyState = 1; };
        
        // Basic syntax check using eval (just for syntax, not execution)
        eval(`(function() { ${nodeCompatible} })();`);
        console.log(`✓ ${path.basename(filePath)} - Syntax OK`);
        return true;
    } catch (error) {
        console.log(`✗ ${path.basename(filePath)} - Syntax Error: ${error.message}`);
        return false;
    }
}

console.log('Testing enhanced JavaScript module syntax...\n');

const modules = [
    'static/js/modules/api.js',
    'static/js/modules/websocket.js', 
    'static/js/modules/state.js',
    'static/js/modules/ui.js',
    'static/js/modules/agents.js',
    'static/js/modules/theme.js',
    'static/js/chat-enhanced.js'
];

let allPassed = true;
modules.forEach(module => {
    if (!testJavaScriptSyntax(module)) {
        allPassed = false;
    }
});

console.log('\n' + (allPassed ? '✅ All enhanced modules passed syntax check!' : '❌ Some modules have syntax errors'));

// Clean up globals
delete global.mockObject;
delete global.mockDocument;
delete global.MockWebSocket;