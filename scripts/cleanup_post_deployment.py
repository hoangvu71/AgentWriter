#!/usr/bin/env python3
"""
Post-deployment cleanup script to remove one-time utility scripts.
Run this after successful deployment to clean up repository.
"""

import os
import shutil
from pathlib import Path
from typing import List

# Scripts to remove after deployment
ONE_TIME_SCRIPTS = [
    "scripts/update_main_route.py",
    "scripts/migration/apply_migration_008.py", 
    "scripts/migration/apply_migration_008_direct.py",
    "scripts/migration/apply_migration_via_api.py",
    "scripts/migration/apply_migration_direct.py",
    "scripts/migration/apply_migration_supabase.py"
]

# Documentation files that can be archived
ARCHIVAL_DOCS = [
    "SCHEMA_ALIGNED_REFACTORING.md",
    "REFACTORING_SUMMARY.md", 
    "WORKSPACE_DOCUMENTATION.md"
]

def cleanup_one_time_scripts():
    """Remove one-time utility scripts"""
    print("Cleaning up one-time utility scripts...")
    
    removed_count = 0
    for script_path in ONE_TIME_SCRIPTS:
        if os.path.exists(script_path):
            print(f"  Removing: {script_path}")
            os.remove(script_path)
            removed_count += 1
        else:
            print(f"  Already removed: {script_path}")
    
    print(f"Removed {removed_count} one-time scripts")

def archive_refactoring_docs():
    """Move refactoring documentation to archive"""
    print("\nArchiving refactoring documentation...")
    
    # Create docs/archive directory if it doesn't exist
    archive_dir = Path("docs/archive")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    archived_count = 0
    for doc_path in ARCHIVAL_DOCS:
        if os.path.exists(doc_path):
            destination = archive_dir / Path(doc_path).name
            print(f"  Archiving: {doc_path} -> {destination}")
            shutil.move(doc_path, destination)
            archived_count += 1
        else:
            print(f"  Already archived: {doc_path}")
    
    print(f"Archived {archived_count} documentation files")

def validate_core_functionality():
    """Validate that core system files remain intact"""
    print("\nValidating core system integrity...")
    
    critical_files = [
        "src/database/supabase_service.py",
        "src/repositories/plot_repository.py",
        "src/services/content_saving_service.py",
        "main.py",
        "requirements.txt"
    ]
    
    all_present = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"  Core file present: {file_path}")
        else:
            print(f"  CRITICAL: Missing file: {file_path}")
            all_present = False
    
    if all_present:
        print("All core system files intact")
        return True
    else:
        print("CRITICAL: Core system files missing - do not proceed")
        return False

def main():
    """Main cleanup process"""
    print("POST-DEPLOYMENT CLEANUP")
    print("=" * 50)
    
    # Validate system integrity first
    if not validate_core_functionality():
        print("\nCleanup aborted - core files missing")
        return False
    
    # Clean up one-time scripts
    cleanup_one_time_scripts()
    
    # Archive refactoring documentation
    archive_refactoring_docs()
    
    print("\nPOST-DEPLOYMENT CLEANUP COMPLETE")
    print("=" * 50)
    print("Repository cleaned of temporary files")
    print("Documentation archived appropriately") 
    print("Core functionality preserved")
    print("\nNEXT STEPS:")
    print("1. Commit cleanup changes: git add . && git commit -m 'Post-deployment cleanup'")
    print("2. Complete repository pattern migration if desired")
    print("3. Run integration tests to verify system functionality")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)