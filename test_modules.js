// Node.js test to verify JavaScript module syntax
const fs = require('fs');
const path = require('path');

function testJavaScriptSyntax(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        
        // Remove ES6 export statements for Node.js compatibility
        const nodeCompatible = content
            .replace(/export default \w+;/g, '')
            .replace(/if \(typeof window !== 'undefined'\) \{[^}]+\}/g, '');
        
        // Basic syntax check using eval (just for syntax, not execution)
        eval(`(function() { ${nodeCompatible} })();`);
        console.log(`✓ ${path.basename(filePath)} - Syntax OK`);
        return true;
    } catch (error) {
        console.log(`✗ ${path.basename(filePath)} - Syntax Error: ${error.message}`);
        return false;
    }
}

console.log('Testing JavaScript module syntax...\n');

const modules = [
    'static/js/modules/api.js',
    'static/js/modules/websocket.js', 
    'static/js/modules/state.js',
    'static/js/modules/ui.js',
    'static/js/chat-modular.js'
];

let allPassed = true;
modules.forEach(module => {
    if (!testJavaScriptSyntax(module)) {
        allPassed = false;
    }
});

console.log('\n' + (allPassed ? '✓ All modules passed syntax check!' : '✗ Some modules have syntax errors'));