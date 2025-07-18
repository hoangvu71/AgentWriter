#!/usr/bin/env python3
"""
Script to extract inline HTML, CSS, and JavaScript from main.py
"""
import re
import os

def extract_html_assets():
    """Extract HTML, CSS, and JS from main.py"""
    
    # Read main.py
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the HTML response content
    html_match = re.search(r'return HTMLResponse\(content=r"""(.*?)"""\)', content, re.DOTALL)
    
    if not html_match:
        print("Could not find HTML content")
        return
    
    html_content = html_match.group(1).strip()
    
    # Extract CSS from style tags
    css_parts = []
    style_pattern = r'<style>(.*?)</style>'
    style_matches = re.findall(style_pattern, html_content, re.DOTALL)
    
    for css in style_matches:
        css_parts.append(css.strip())
    
    # Combine all CSS
    combined_css = '\n\n/* ===== Combined CSS from main.py ===== */\n\n'.join(css_parts)
    
    # Extract JavaScript from script tags
    js_parts = []
    script_pattern = r'<script>(.*?)</script>'
    script_matches = re.findall(script_pattern, html_content, re.DOTALL)
    
    for js in script_matches:
        js_parts.append(js.strip())
    
    # Combine all JS
    combined_js = '\n\n// ===== Combined JavaScript from main.py =====\n\n'.join(js_parts)
    
    # Remove style and script tags from HTML
    html_clean = re.sub(r'<style>.*?</style>', '', html_content, flags=re.DOTALL)
    html_clean = re.sub(r'<script>.*?</script>', '', html_clean, flags=re.DOTALL)
    
    # Add links to external CSS and JS files
    html_clean = html_clean.replace(
        '</head>',
        '    <link rel="stylesheet" href="/static/css/main.css">\n</head>'
    )
    html_clean = html_clean.replace(
        '</body>',
        '    <script src="/static/js/main.js"></script>\n</body>'
    )
    
    # Clean up extra whitespace
    html_clean = re.sub(r'\n\s*\n', '\n', html_clean)
    
    # Save files
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_clean)
    
    with open('static/css/main.css', 'w', encoding='utf-8') as f:
        f.write(combined_css)
    
    with open('static/js/main.js', 'w', encoding='utf-8') as f:
        f.write(combined_js)
    
    print("Extracted files:")
    print("- templates/index.html")
    print("- static/css/main.css")
    print("- static/js/main.js")
    
    # Create updated main.py with template rendering
    create_updated_main()

def create_updated_main():
    """Create updated main.py that uses templates"""
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the HTMLResponse section
    new_route = '''@app.get("/")
async def get_home():
    """Serve the main HTML page"""
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)'''
    
    # Replace the old route
    pattern = r'@app\.get\("/"\)\s*async def get_home\(\):\s*""".*?"""\s*return HTMLResponse\(content=r""".*?"""\)'
    content = re.sub(pattern, new_route, content, flags=re.DOTALL)
    
    # Save backup
    with open('main.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Created main.py.backup")
    print("\nNext steps:")
    print("1. Add static file mounting to main.py")
    print("2. Test the application")

if __name__ == "__main__":
    extract_html_assets()