#!/usr/bin/env python3
"""
Workspace Documentation Generator

This script generates a comprehensive markdown documentation of the entire workspace,
including folder structure, file listings, and code contents.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import mimetypes

# File extensions to include code content for
CODE_EXTENSIONS = {
    '.py', '.js', '.html', '.css', '.sql', '.md', '.json', '.yml', '.yaml',
    '.txt', '.env', '.gitignore', '.ini', '.cfg', '.conf', '.sh', '.bat',
    '.ps1', '.xml', '.toml', '.requirements'
}

# Files to exclude from documentation
EXCLUDE_FILES = {
    '__pycache__', '.pyc', '.git', '.DS_Store', 'node_modules',
    '.vscode', '.idea', '*.log', '*.tmp', 'tmp_*'
}

# Directories to exclude
EXCLUDE_DIRS = {
    '__pycache__', '.git', 'node_modules', '.vscode', '.idea', 
    'venv', 'env', '.env', 'dist', 'build'
}

def should_exclude_path(path):
    """Check if a path should be excluded from documentation."""
    path_str = str(path)
    name = path.name
    
    # Check if it's in exclude list
    if name in EXCLUDE_FILES or name in EXCLUDE_DIRS:
        return True
    
    # Check for pattern matches
    for exclude_pattern in EXCLUDE_FILES:
        if '*' in exclude_pattern:
            pattern = exclude_pattern.replace('*', '')
            if pattern in name:
                return True
    
    return False

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

def is_text_file(file_path):
    """Check if file is likely a text file."""
    try:
        # Check by extension first
        if file_path.suffix.lower() in CODE_EXTENSIONS:
            return True
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text/'):
            return True
        
        # Try to read a small portion to check if it's text
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:  # Binary files often contain null bytes
                return False
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
    except:
        return False

def read_file_content(file_path):
    """Read and return file content safely."""
    try:
        # Skip very large files entirely
        file_size = os.path.getsize(file_path)
        if file_size > 100000:  # 100KB limit
            return f"File too large ({get_file_size(file_path)}) - content not displayed to prevent memory issues"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Additional safety check
            if len(content) > 50000:  # 50KB limit
                content = content[:50000] + "\n\n... (file truncated due to size) ..."
            return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def generate_tree_structure(root_path, prefix="", max_depth=10, current_depth=0):
    """Generate a tree structure of the workspace."""
    if current_depth >= max_depth:
        return ""
    
    tree_output = ""
    root = Path(root_path)
    
    try:
        # Get all items and sort them (directories first, then files)
        items = []
        for item in root.iterdir():
            if not should_exclude_path(item):
                items.append(item)
        
        # Sort: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x.is_file(), x.name.lower()))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            tree_output += f"{prefix}{current_prefix}{item.name}"
            
            if item.is_file():
                size = get_file_size(item)
                tree_output += f" ({size})\n"
            else:
                tree_output += "/\n"
                # Recursively add subdirectory contents
                next_prefix = prefix + ("    " if is_last else "│   ")
                tree_output += generate_tree_structure(
                    item, next_prefix, max_depth, current_depth + 1
                )
    
    except PermissionError:
        tree_output += f"{prefix}└── [Permission Denied]\n"
    
    return tree_output

def generate_file_contents(root_path):
    """Generate detailed file contents section."""
    content_output = ""
    root = Path(root_path)
    
    # Walk through all files
    all_files = []
    print("📂 Scanning files...")
    for file_path in root.rglob("*"):
        if file_path.is_file() and not should_exclude_path(file_path):
            all_files.append(file_path)
    
    print(f"📊 Found {len(all_files)} files to process")
    
    # Sort files by path
    all_files.sort(key=lambda x: str(x).lower())
    
    for i, file_path in enumerate(all_files):
        relative_path = file_path.relative_to(root)
        
        # Progress indicator
        if i % 10 == 0 or i == len(all_files) - 1:
            print(f"📄 Processing file {i+1}/{len(all_files)}: {relative_path}")
        
        content_output += f"\n## 📄 {relative_path}\n\n"
        content_output += f"**Path:** `{relative_path}`\n"
        content_output += f"**Size:** {get_file_size(file_path)}\n"
        
        if is_text_file(file_path):
            content_output += f"**Type:** Text file\n\n"
            file_content = read_file_content(file_path)
            
            # Determine language for syntax highlighting
            extension = file_path.suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.md': 'markdown',
                '.json': 'json',
                '.yml': 'yaml',
                '.yaml': 'yaml',
                '.sh': 'bash',
                '.bat': 'batch',
                '.ps1': 'powershell',
                '.xml': 'xml',
                '.toml': 'toml'
            }
            
            language = language_map.get(extension, 'text')
            
            content_output += f"```{language}\n{file_content}\n```\n\n"
        else:
            content_output += f"**Type:** Binary file (content not displayed)\n\n"
    
    return content_output

def generate_workspace_documentation(workspace_path="."):
    """Generate complete workspace documentation."""
    workspace_path = Path(workspace_path).resolve()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Start building the markdown document
    doc = f"""# 📁 Workspace Documentation

**Generated on:** {timestamp}  
**Workspace Path:** `{workspace_path}`

---

## 📋 Table of Contents

1. [Workspace Overview](#-workspace-overview)
2. [Directory Structure](#-directory-structure)
3. [File Contents](#-file-contents)

---

## 🏗️ Workspace Overview

This document provides a comprehensive overview of the workspace structure and contents.

**Total Items:** {len(list(workspace_path.rglob("*")))} (including excluded items)

---

## 🌳 Directory Structure

```
{workspace_path.name}/
{generate_tree_structure(workspace_path)}
```

---

## 📚 File Contents

The following section contains the complete contents of all text files in the workspace:
{generate_file_contents(workspace_path)}

---

*Documentation generated by Workspace Documentation Generator*
"""
    
    return doc

def main():
    """Main function to generate and save workspace documentation."""
    # Get workspace path from command line argument or use current directory
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print("🚀 Generating workspace documentation...")
    print(f"📁 Workspace: {Path(workspace_path).resolve()}")
    
    try:
        # Generate documentation
        documentation = generate_workspace_documentation(workspace_path)
        
        # Save to file
        output_file = "WORKSPACE_DOCUMENTATION.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        print(f"✅ Documentation generated successfully!")
        print(f"📄 Output file: {output_file}")
        print(f"📊 File size: {get_file_size(output_file)}")
        
    except Exception as e:
        print(f"❌ Error generating documentation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()