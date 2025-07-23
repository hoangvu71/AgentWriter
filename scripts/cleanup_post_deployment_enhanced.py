#!/usr/bin/env python3
"""
Enhanced post-deployment cleanup script with configurable patterns.
Run this after successful deployment to clean up repository.

Features:
- Configurable file patterns via JSON config
- Pattern-based discovery instead of hardcoded lists
- Dry-run mode for safety
- Exclusion patterns to protect important files
- Verbose logging and confirmation prompts
"""

import os
import json
import shutil
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class CleanupManager:
    """Manages post-deployment cleanup with configurable patterns"""
    
    def __init__(self, config_path: str = "scripts/cleanup_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.dry_run = self.config.get("settings", {}).get("dry_run", False)
        self.verbose = self.config.get("settings", {}).get("verbose", True)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self._log(f"Config file not found: {self.config_path}")
            self._log("Using fallback configuration...")
            return self._get_fallback_config()
        except json.JSONDecodeError as e:
            self._log(f"Invalid JSON in config file: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if config file is missing"""
        return {
            "cleanup_patterns": {
                "one_time_scripts": [
                    "scripts/migration/apply_migration_*.py",
                    "scripts/update_*.py"
                ],
                "archival_docs": [
                    "*REFACTORING*.md",
                    "WORKSPACE_DOCUMENTATION.md"
                ],
                "critical_files": [
                    "src/app.py",
                    "main.py",
                    "requirements.txt"
                ]
            },
            "settings": {
                "archive_directory": "docs/archive",
                "dry_run": False,
                "verbose": True
            },
            "exclusions": {
                "never_remove": [
                    "scripts/cleanup_*.py"
                ]
            }
        }
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        if self.verbose or level == "ERROR":
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = "[DRY RUN] " if self.dry_run else ""
            print(f"[{timestamp}] {prefix}{level}: {message}")
    
    def _find_files_by_patterns(self, patterns: List[str]) -> List[str]:
        """Find files matching glob patterns"""
        found_files = []
        for pattern in patterns:
            matches = glob.glob(pattern, recursive=True)
            found_files.extend(matches)
        
        # Remove duplicates and sort
        return sorted(list(set(found_files)))
    
    def _is_excluded(self, file_path: str) -> bool:
        """Check if file should be excluded from cleanup"""
        exclusions = self.config.get("exclusions", {})
        
        # Check never_remove patterns
        never_remove = exclusions.get("never_remove", [])
        for pattern in never_remove:
            if glob.fnmatch.fnmatch(file_path, pattern):
                self._log(f"File excluded (never_remove): {file_path}")
                return True
        
        # Check protected patterns
        protected = exclusions.get("protected_patterns", [])
        for pattern in protected:
            if glob.fnmatch.fnmatch(file_path, pattern):
                self._log(f"File excluded (protected): {file_path}")
                return True
        
        return False
    
    def cleanup_one_time_scripts(self) -> int:
        """Remove one-time utility scripts based on patterns"""
        self._log("Cleaning up one-time utility scripts...")
        
        patterns = self.config.get("cleanup_patterns", {}).get("one_time_scripts", [])
        if not patterns:
            self._log("No one-time script patterns configured")
            return 0
        
        found_files = self._find_files_by_patterns(patterns)
        removed_count = 0
        
        for file_path in found_files:
            if self._is_excluded(file_path):
                continue
                
            if os.path.exists(file_path):
                self._log(f"Removing script: {file_path}")
                if not self.dry_run:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except OSError as e:
                        self._log(f"Failed to remove {file_path}: {e}", "ERROR")
                else:
                    removed_count += 1
            else:
                self._log(f"Already removed: {file_path}")
        
        self._log(f"Removed {removed_count} one-time scripts")
        return removed_count
    
    def archive_docs(self) -> int:
        """Archive documentation files based on patterns"""
        self._log("Archiving documentation files...")
        
        patterns = self.config.get("cleanup_patterns", {}).get("archival_docs", [])
        if not patterns:
            self._log("No archival doc patterns configured")
            return 0
        
        # Create archive directory
        archive_dir = Path(self.config.get("settings", {}).get("archive_directory", "docs/archive"))
        if not self.dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
        
        found_files = self._find_files_by_patterns(patterns)
        archived_count = 0
        
        for file_path in found_files:
            if self._is_excluded(file_path):
                continue
                
            if os.path.exists(file_path):
                destination = archive_dir / Path(file_path).name
                self._log(f"Archiving: {file_path} -> {destination}")
                
                if not self.dry_run:
                    try:
                        shutil.move(file_path, destination)
                        archived_count += 1
                    except OSError as e:
                        self._log(f"Failed to archive {file_path}: {e}", "ERROR")
                else:
                    archived_count += 1
            else:
                self._log(f"Already archived: {file_path}")
        
        self._log(f"Archived {archived_count} documentation files")
        return archived_count
    
    def validate_critical_files(self) -> bool:
        """Validate that critical system files remain intact"""
        self._log("Validating critical system files...")
        
        critical_patterns = self.config.get("cleanup_patterns", {}).get("critical_files", [])
        if not critical_patterns:
            self._log("No critical files configured for validation")
            return True
        
        all_present = True
        missing_files = []
        
        for file_path in critical_patterns:
            if os.path.exists(file_path):
                self._log(f"Critical file present: {file_path}")
            else:
                self._log(f"CRITICAL: Missing file: {file_path}", "ERROR")
                missing_files.append(file_path)
                all_present = False
        
        if all_present:
            self._log("All critical system files intact")
        else:
            self._log(f"CRITICAL: {len(missing_files)} core files missing", "ERROR")
            for file_path in missing_files:
                self._log(f"  Missing: {file_path}", "ERROR")
        
        return all_present
    
    def get_cleanup_summary(self) -> Dict[str, Any]:
        """Get summary of what would be cleaned up"""
        summary = {
            "one_time_scripts": [],
            "archival_docs": [],
            "critical_files": [],
            "excluded_files": []
        }
        
        # Find scripts to remove
        script_patterns = self.config.get("cleanup_patterns", {}).get("one_time_scripts", [])
        scripts = self._find_files_by_patterns(script_patterns)
        for script in scripts:
            if self._is_excluded(script):
                summary["excluded_files"].append(script)
            else:
                summary["one_time_scripts"].append(script)
        
        # Find docs to archive
        doc_patterns = self.config.get("cleanup_patterns", {}).get("archival_docs", [])
        docs = self._find_files_by_patterns(doc_patterns)
        for doc in docs:
            if self._is_excluded(doc):
                summary["excluded_files"].append(doc)
            else:
                summary["archival_docs"].append(doc)
        
        # Check critical files
        critical_patterns = self.config.get("cleanup_patterns", {}).get("critical_files", [])
        summary["critical_files"] = critical_patterns
        
        return summary
    
    def run_cleanup(self, confirm: bool = True) -> bool:
        """Run the complete cleanup process"""
        self._log("POST-DEPLOYMENT CLEANUP (Enhanced)")
        self._log("=" * 50)
        
        if self.dry_run:
            self._log("DRY RUN MODE - No files will be modified")
        
        # Show summary if confirmation required
        if confirm and not self.dry_run:
            summary = self.get_cleanup_summary()
            
            print("\nCLEANUP SUMMARY:")
            print(f"Scripts to remove: {len(summary['one_time_scripts'])}")
            for script in summary['one_time_scripts']:
                print(f"  - {script}")
            
            print(f"\nDocs to archive: {len(summary['archival_docs'])}")
            for doc in summary['archival_docs']:
                print(f"  - {doc}")
            
            if summary['excluded_files']:
                print(f"\nExcluded files: {len(summary['excluded_files'])}")
                for excluded in summary['excluded_files']:
                    print(f"  - {excluded}")
            
            response = input("\nProceed with cleanup? (y/N): ").lower().strip()
            if response != 'y':
                self._log("Cleanup cancelled by user")
                return False
        
        # Validate system integrity first
        if not self.validate_critical_files():
            self._log("Cleanup aborted - critical files missing", "ERROR")
            return False
        
        # Perform cleanup
        scripts_removed = self.cleanup_one_time_scripts()
        docs_archived = self.archive_docs()
        
        # Final summary
        self._log("POST-DEPLOYMENT CLEANUP COMPLETE")
        self._log("=" * 50)
        self._log(f"Scripts removed: {scripts_removed}")
        self._log(f"Documents archived: {docs_archived}")
        self._log("Core functionality preserved")
        
        if not self.dry_run:
            self._log("NEXT STEPS:")
            self._log("1. git add . && git commit -m 'Post-deployment cleanup'")
            self._log("2. Run integration tests to verify system functionality")
        
        return True


def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description="Enhanced post-deployment cleanup")
    parser.add_argument("--config", "-c", default="scripts/cleanup_config.json",
                       help="Path to cleanup configuration file")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--no-confirm", "-y", action="store_true",
                       help="Skip confirmation prompt")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress verbose output")
    parser.add_argument("--summary", "-s", action="store_true",
                       help="Show cleanup summary and exit")
    
    args = parser.parse_args()
    
    # Initialize cleanup manager
    cleanup = CleanupManager(args.config)
    
    # Override config with command line args
    if args.dry_run:
        cleanup.dry_run = True
    if args.quiet:
        cleanup.verbose = False
    
    # Show summary if requested
    if args.summary:
        summary = cleanup.get_cleanup_summary()
        print("CLEANUP SUMMARY:")
        print(f"One-time scripts: {len(summary['one_time_scripts'])}")
        print(f"Archival docs: {len(summary['archival_docs'])}")
        print(f"Critical files: {len(summary['critical_files'])}")
        print(f"Excluded files: {len(summary['excluded_files'])}")
        return 0
    
    # Run cleanup
    success = cleanup.run_cleanup(confirm=not args.no_confirm)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())