#!/usr/bin/env python3
"""
Migration script to help transition from hardcoded cleanup script to configurable version.
This script backs up the old script and provides information about the new version.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def main():
    """Migrate to enhanced cleanup script"""
    print("CLEANUP SCRIPT MIGRATION")
    print("=" * 40)
    
    old_script = "scripts/cleanup_post_deployment.py"
    new_script = "scripts/cleanup_post_deployment_enhanced.py"
    config_file = "scripts/cleanup_config.json"
    backup_dir = Path("backup/legacy_scripts")
    
    # Create backup directory
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup old script if it exists
    if os.path.exists(old_script):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"cleanup_post_deployment_{timestamp}.py"
        shutil.copy2(old_script, backup_path)
        print(f"✓ Backed up old script to: {backup_path}")
    
    # Check if new files exist
    has_new_script = os.path.exists(new_script)
    has_config = os.path.exists(config_file)
    
    print(f"✓ Enhanced script available: {has_new_script}")
    print(f"✓ Configuration file available: {has_config}")
    
    if has_new_script and has_config:
        print("\nENHANCED CLEANUP FEATURES:")
        print("- Configurable file patterns via JSON")
        print("- Pattern-based discovery instead of hardcoded lists")
        print("- Dry-run mode for safety testing")
        print("- Exclusion patterns to protect important files")
        print("- Command-line options and verbose logging")
        
        print("\nUSAGE EXAMPLES:")
        print("  # Show what would be cleaned up (dry run)")
        print("  python scripts/cleanup_post_deployment_enhanced.py --dry-run")
        print()
        print("  # Show summary without running")
        print("  python scripts/cleanup_post_deployment_enhanced.py --summary")
        print()
        print("  # Run cleanup with confirmation")
        print("  python scripts/cleanup_post_deployment_enhanced.py")
        print()
        print("  # Run cleanup without confirmation")
        print("  python scripts/cleanup_post_deployment_enhanced.py --no-confirm")
        
        print("\nCONFIGURATION:")
        print(f"Edit {config_file} to customize:")
        print("- File patterns for scripts and docs to clean up")
        print("- Archive directory location")
        print("- Files to never remove (exclusions)")
        print("- Critical files to validate")
        
        # Offer to remove old script
        response = input(f"\nRemove old script ({old_script})? (y/N): ").lower().strip()
        if response == 'y':
            if os.path.exists(old_script):
                os.remove(old_script)
                print(f"✓ Removed old script: {old_script}")
            else:
                print(f"Old script already removed: {old_script}")
        
    else:
        print("\n⚠️  Enhanced cleanup files not found")
        print("Please ensure both files are present:")
        print(f"  - {new_script}")
        print(f"  - {config_file}")
    
    print("\nMIGRATION COMPLETE")
    print("You can now use the enhanced cleanup script with configurable patterns!")


if __name__ == "__main__":
    main()