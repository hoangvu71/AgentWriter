#!/usr/bin/env python3
"""
Consolidated Workspace Documentation Generator

This script generates workspace documentation with configurable modes:
- Full mode: Comprehensive documentation (default)
- Quick mode: Fast documentation with limits
- Structure-only mode: Directory tree only (fastest)

Usage:
    python generate_docs.py                    # Full documentation
    python generate_docs.py --quick           # Quick mode with limits
    python generate_docs.py --no-content      # Structure only (fastest)
    python generate_docs.py --max-files 50    # Limit file count
    python generate_docs.py --max-depth 5     # Limit directory depth
    python generate_docs.py --help            # Show help
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import mimetypes

# File extensions to include code content for
CODE_EXTENSIONS = {
    '.py', '.js', '.html', '.css', '.sql', '.md', '.json', '.yml', '.yaml',
    '.txt', '.env', '.gitignore', '.ini', '.cfg', '.conf', '.sh', '.bat',
    '.ps1', '.xml', '.toml', '.requirements'
}

# Files and directories to exclude from documentation
EXCLUDE_PATTERNS = {
    '__pycache__', '.pyc', '.git', '.DS_Store', 'node_modules',
    '.vscode', '.idea', '*.log', '*.tmp', 'tmp_*', 'venv', 'env', 
    '.env', 'dist', 'build', 'htmlcov'
}

class DocumentationConfig:
    """Configuration class for documentation generation."""
    
    def __init__(self):
        # Default settings (full mode)
        self.mode = 'full'
        self.include_content = True
        self.max_files = None  # No limit in full mode
        self.max_depth = 10
        self.max_file_size_kb = 100  # 100KB
        self.max_content_size_kb = 50  # 50KB
        self.workspace_path = "."
        self.output_file = None  # Auto-generated based on mode
        
    def set_quick_mode(self):
        """Configure for quick mode."""
        self.mode = 'quick'
        self.max_files = 100
        self.max_depth = 3
        self.max_file_size_kb = 50
        self.max_content_size_kb = 10
        
    def set_structure_only_mode(self):
        """Configure for structure-only mode."""
        self.mode = 'structure'
        self.include_content = False
        self.max_files = None
        self.max_depth = 5

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

def should_exclude_path(path):
    """Check if a path should be excluded from documentation."""
    path_str = str(path)
    name = path.name
    
    # Check if it's in exclude list
    if name in EXCLUDE_PATTERNS:
        return True
    
    # Check for pattern matches
    for exclude_pattern in EXCLUDE_PATTERNS:
        if '*' in exclude_pattern:
            pattern = exclude_pattern.replace('*', '')
            if pattern in name:
                return True
    
    # Skip hidden files except specific ones
    if name.startswith('.') and name not in ['.env', '.gitignore']:
        return True
    
    return False

def should_include_file(file_path, config):
    """Check if file should be included based on configuration."""
    if should_exclude_path(file_path):
        return False
    
    # Check file size if including content
    if config.include_content:
        try:
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb > config.max_file_size_kb:
                return False
        except:
            return False
    
    return True

def is_text_file(file_path, comprehensive=True):
    """Check if file is likely a text file."""
    try:
        # Check by extension first
        if file_path.suffix.lower() in CODE_EXTENSIONS:
            return True
        
        if comprehensive:
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
        else:
            # Quick check - extension only
            return file_path.suffix.lower() in CODE_EXTENSIONS
    except:
        return False

def read_file_content(file_path, config):
    """Read and return file content safely."""
    try:
        # Skip very large files
        file_size = os.path.getsize(file_path)
        max_size_bytes = config.max_file_size_kb * 1024
        if file_size > max_size_bytes:
            return f"File too large ({get_file_size(file_path)}) - content not displayed"
        
        # Read with error handling
        encoding_args = {'encoding': 'utf-8'}
        if config.mode == 'quick':
            encoding_args['errors'] = 'ignore'
            
        with open(file_path, 'r', **encoding_args) as f:
            content = f.read()
            
            # Truncate if too large
            max_content_chars = config.max_content_size_kb * 1024
            if len(content) > max_content_chars:
                content = content[:max_content_chars] + f"\n\n... (file truncated due to size limit: {config.max_content_size_kb}KB) ..."
            
            return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def generate_tree_structure(root_path, config, prefix="", current_depth=0):
    """Generate a tree structure of the workspace."""
    if current_depth >= config.max_depth:
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
                    item, config, next_prefix, current_depth + 1
                )
    
    except PermissionError:
        tree_output += f"{prefix}└── [Permission Denied]\n"
    
    return tree_output

def generate_file_contents(root_path, config):
    """Generate detailed file contents section."""
    if not config.include_content:
        return "\n*Content generation disabled - use --include-content to show file contents*\n"
    
    content_output = ""
    root = Path(root_path)
    
    # Walk through all files
    all_files = []
    print(f">> Scanning files in {config.mode} mode...")
    
    for file_path in root.rglob("*"):
        if file_path.is_file() and should_include_file(file_path, config):
            all_files.append(file_path)
            
            # Apply file limit if set
            if config.max_files and len(all_files) >= config.max_files:
                break
    
    print(f">> Found {len(all_files)} files to process")
    
    # Sort files by path
    all_files.sort(key=lambda x: str(x).lower())
    
    for i, file_path in enumerate(all_files):
        relative_path = file_path.relative_to(root)
        
        # Progress indicator
        if i % 10 == 0 or i == len(all_files) - 1:
            print(f">> Processing file {i+1}/{len(all_files)}: {relative_path}")
        
        content_output += f"\n## 📄 {relative_path}\n\n"
        content_output += f"**Path:** `{relative_path}`\n"
        content_output += f"**Size:** {get_file_size(file_path)}\n"
        
        # Check if it's a text file
        is_text = is_text_file(file_path, comprehensive=(config.mode == 'full'))
        
        if is_text:
            content_output += f"**Type:** Text file\n\n"
            file_content = read_file_content(file_path, config)
            
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
    
    # Add truncation notice if limit was reached
    if config.max_files and len(all_files) >= config.max_files:
        content_output += f"\n⚠️ **File limit reached: Only showing first {config.max_files} files**\n"
    
    return content_output

def generate_workspace_documentation(config):
    """Generate complete workspace documentation."""
    workspace_path = Path(config.workspace_path).resolve()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Mode-specific title and description
    mode_info = {
        'full': ('📁 Complete Workspace Documentation', 'comprehensive'),
        'quick': ('📁 Quick Workspace Documentation', 'quick'),
        'structure': ('📁 Workspace Structure Documentation', 'structure-only')
    }
    
    title, mode_desc = mode_info.get(config.mode, mode_info['full'])
    
    # Start building the markdown document
    doc = f"""{title}

**Generated on:** {timestamp}  
**Workspace Path:** `{workspace_path}`  
**Mode:** {mode_desc}  
**Content included:** {'Yes' if config.include_content else 'No (structure only)'}"""
    
    if config.max_files:
        doc += f"  \n**File limit:** {config.max_files}"
    if config.max_depth < 10:
        doc += f"  \n**Max depth:** {config.max_depth}"
    
    doc += f"""

---

## 📋 Table of Contents

1. [Workspace Overview](#-workspace-overview)
2. [Directory Structure](#-directory-structure)"""
    
    if config.include_content:
        doc += "\n3. [File Contents](#-file-contents)"
    
    doc += f"""

---

## 🏗️ Workspace Overview

This document provides a {'comprehensive' if config.mode == 'full' else 'quick'} overview of the workspace structure and contents.

**Generation Mode:** {config.mode.title()}  
**Total Items:** {len(list(workspace_path.rglob("*")))} (including excluded items)

---

## 🌳 Directory Structure

```
{workspace_path.name}/
{generate_tree_structure(workspace_path, config)}
```

---
"""
    
    if config.include_content:
        doc += f"""
## 📚 File Contents

The following section contains the contents of text files in the workspace:
{generate_file_contents(workspace_path, config)}

---
"""
    
    doc += f"""
*Documentation generated by Consolidated Workspace Documentation Generator (Mode: {config.mode})*
"""
    
    return doc

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate workspace documentation with configurable modes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_docs.py                    # Full documentation
  python generate_docs.py --quick           # Quick mode with limits
  python generate_docs.py --no-content      # Structure only (fastest)
  python generate_docs.py --max-files 50    # Limit to 50 files
  python generate_docs.py --max-depth 5     # Limit directory depth
  python generate_docs.py --path /some/dir  # Specify workspace path
        """
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--quick', action='store_true',
                           help='Quick mode: faster generation with limits (100 files, depth 3)')
    mode_group.add_argument('--no-content', action='store_true',
                           help='Structure only: generate directory tree only (fastest)')
    
    # Configuration options
    parser.add_argument('--max-files', type=int, metavar='N',
                       help='Maximum number of files to process')
    parser.add_argument('--max-depth', type=int, metavar='N',
                       help='Maximum directory depth to traverse')
    parser.add_argument('--max-size', type=int, metavar='KB',
                       help='Maximum file size (KB) to include content for')
    parser.add_argument('--path', type=str, metavar='PATH', default='.',
                       help='Workspace path to document (default: current directory)')
    parser.add_argument('--output', type=str, metavar='FILE',
                       help='Output filename (auto-generated if not specified)')
    
    return parser.parse_args()

def main():
    """Main function to generate and save workspace documentation."""
    args = parse_arguments()
    
    # Create configuration
    config = DocumentationConfig()
    config.workspace_path = args.path
    
    # Apply mode settings
    if args.quick:
        config.set_quick_mode()
    elif args.no_content:
        config.set_structure_only_mode()
    
    # Override with specific arguments
    if args.max_files is not None:
        config.max_files = args.max_files
    if args.max_depth is not None:
        config.max_depth = args.max_depth
    if args.max_size is not None:
        config.max_file_size_kb = args.max_size
        config.max_content_size_kb = min(args.max_size, config.max_content_size_kb)
    
    # Determine output filename
    if args.output:
        config.output_file = args.output
    else:
        filename_map = {
            'full': 'WORKSPACE_DOCUMENTATION.md',
            'quick': 'QUICK_WORKSPACE_DOCS.md',
            'structure': 'WORKSPACE_STRUCTURE.md'
        }
        config.output_file = filename_map.get(config.mode, 'WORKSPACE_DOCS.md')
    
    print(">> Generating workspace documentation...")
    print(f">> Workspace: {Path(config.workspace_path).resolve()}")
    print(f">> Mode: {config.mode}")
    print(f">> Include content: {config.include_content}")
    if config.max_files:
        print(f">> Max files: {config.max_files}")
    print(f">> Max depth: {config.max_depth}")
    
    try:
        # Generate documentation
        documentation = generate_workspace_documentation(config)
        
        # Save to file
        with open(config.output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        print(f">> Documentation generated successfully!")
        print(f">> Output file: {config.output_file}")
        print(f">> File size: {get_file_size(config.output_file)}")
        
    except Exception as e:
        print(f">> Error generating documentation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()