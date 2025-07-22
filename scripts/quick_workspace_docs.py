#!/usr/bin/env python3
"""
Quick Workspace Documentation Generator

A fast, efficient script that generates workspace documentation with options
to control what gets included to avoid performance issues.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def get_file_size(file_path):
    """Get human readable file size."""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "Unknown"

def should_include_file(file_path, include_content=True, max_size_kb=50):
    """Check if file should be included based on criteria."""
    # Skip hidden files and common excludes
    name = file_path.name
    if name.startswith('.') and name not in ['.env', '.gitignore']:
        return False
    
    # Skip common exclude patterns
    exclude_patterns = ['__pycache__', '.pyc', '.log', 'node_modules', '.git']
    if any(pattern in str(file_path) for pattern in exclude_patterns):
        return False
    
    # Check file size if including content
    if include_content:
        try:
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb > max_size_kb:
                return False
        except:
            return False
    
    return True

def is_text_file(file_path):
    """Quick check if file is text."""
    text_extensions = {
        '.py', '.js', '.html', '.css', '.sql', '.md', '.json', '.yml', '.yaml',
        '.txt', '.env', '.gitignore', '.ini', '.cfg', '.sh', '.bat', '.ps1', '.xml', '.toml'
    }
    return file_path.suffix.lower() in text_extensions

def generate_quick_tree(root_path, max_depth=3):
    """Generate a quick tree structure with limited depth."""
    tree = []
    root = Path(root_path)
    
    def add_to_tree(path, prefix="", depth=0):
        if depth >= max_depth:
            return
        
        try:
            items = sorted([item for item in path.iterdir() 
                          if not item.name.startswith('.') or item.name in ['.env', '.gitignore']])
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                
                if item.is_file():
                    size = get_file_size(item)
                    tree.append(f"{prefix}{current_prefix}{item.name} ({size})")
                else:
                    tree.append(f"{prefix}{current_prefix}{item.name}/")
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    add_to_tree(item, next_prefix, depth + 1)
        except PermissionError:
            tree.append(f"{prefix}└── [Permission Denied]")
    
    add_to_tree(root)
    return "\n".join(tree)

def generate_file_list(root_path, include_content=False, max_files=100):
    """Generate a list of files with optional content."""
    root = Path(root_path)
    files_processed = 0
    content = []
    
    print(f"🔍 Scanning workspace: {root}")
    
    for file_path in root.rglob("*"):
        if files_processed >= max_files:
            content.append(f"\n⚠️ **Limit reached: Only showing first {max_files} files**\n")
            break
            
        if file_path.is_file() and should_include_file(file_path, include_content):
            relative_path = file_path.relative_to(root)
            files_processed += 1
            
            if files_processed % 20 == 0:
                print(f"📄 Processed {files_processed} files...")
            
            content.append(f"\n### 📄 {relative_path}")
            content.append(f"**Size:** {get_file_size(file_path)}")
            
            if include_content and is_text_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                        if len(file_content) > 10000:  # 10KB limit
                            file_content = file_content[:10000] + "\n... (truncated)"
                    
                    # Get language for syntax highlighting
                    ext = file_path.suffix.lower()
                    lang_map = {
                        '.py': 'python', '.js': 'javascript', '.html': 'html',
                        '.css': 'css', '.sql': 'sql', '.md': 'markdown',
                        '.json': 'json', '.yml': 'yaml', '.yaml': 'yaml'
                    }
                    lang = lang_map.get(ext, 'text')
                    
                    content.append(f"```{lang}\n{file_content}\n```")
                except Exception as e:
                    content.append(f"*Error reading file: {e}*")
            elif include_content:
                content.append("*Binary file - content not displayed*")
    
    print(f"✅ Processed {files_processed} files total")
    return "\n".join(content)

def main():
    """Main function with options."""
    # Parse command line arguments
    workspace_path = "."
    include_content = True
    max_files = 100
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("""
Quick Workspace Documentation Generator

Usage: python quick_workspace_docs.py [options]

Options:
  --no-content    Generate structure only (faster)
  --max-files N   Limit to N files (default: 100)
  --path PATH     Specify workspace path (default: current directory)
  -h, --help      Show this help

Examples:
  python quick_workspace_docs.py                    # Full documentation
  python quick_workspace_docs.py --no-content      # Structure only (fast)
  python quick_workspace_docs.py --max-files 50    # Limit to 50 files
            """)
            return
        
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == '--no-content':
                include_content = False
            elif arg == '--max-files' and i + 1 < len(sys.argv):
                max_files = int(sys.argv[i + 1])
            elif arg == '--path' and i + 1 < len(sys.argv):
                workspace_path = sys.argv[i + 1]
    
    workspace_path = Path(workspace_path).resolve()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("🚀 Generating workspace documentation...")
    print(f"📁 Workspace: {workspace_path}")
    print(f"📄 Include content: {include_content}")
    print(f"🔢 Max files: {max_files}")
    
    # Generate documentation
    doc = f"""# 📁 Quick Workspace Documentation

**Generated:** {timestamp}  
**Path:** `{workspace_path}`  
**Content included:** {'Yes' if include_content else 'No (structure only)'}

## 🌳 Directory Structure

```
{workspace_path.name}/
{generate_quick_tree(workspace_path)}
```

## 📚 Files
{generate_file_list(workspace_path, include_content, max_files)}

---
*Generated by Quick Workspace Documentation Generator*
"""
    
    # Save to file
    output_file = "QUICK_WORKSPACE_DOCS.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc)
    
    print(f"✅ Documentation saved to: {output_file}")
    print(f"📊 File size: {get_file_size(output_file)}")

if __name__ == "__main__":
    main()