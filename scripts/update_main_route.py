#!/usr/bin/env python3
"""
Update main.py to use template rendering instead of inline HTML
"""
import re

def update_main_route():
    # Read the original main.py
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the HTMLResponse pattern
    pattern = r'(@app\.get\("/"\)\s*async def get_home\(\):\s*""".*?"""\s*return HTMLResponse\(content=r""".*?"""\))'
    
    # New route implementation
    new_route = '''@app.get("/")
async def get_home():
    """Serve the main HTML page"""
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)'''
    
    # Replace the route
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if matches:
        match = matches[0]
        start, end = match.span()
        
        # Replace the content
        new_content = content[:start] + new_route + content[end:]
        
        # Save the updated file
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("Successfully updated main.py to use template rendering")
        print(f"Replaced content from position {start} to {end}")
    else:
        print("Could not find the HTMLResponse pattern to replace")

if __name__ == "__main__":
    update_main_route()