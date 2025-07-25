#!/usr/bin/env python3
"""
Database Migration and Testing Tool for BooksWriter
Command-line utility to manage database schema migrations and consistency testing
"""

import asyncio
import sys
import argparse
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.migration_manager import MigrationManager
from src.database.schema_synchronizer import SchemaSynchronizer
from src.database.adapter_consistency_tester import AdapterConsistencyTester


def main():
    parser = argparse.ArgumentParser(description="BooksWriter Database Migration Tool")
    parser.add_argument("--db-path", default="local_database.db", help="Path to SQLite database")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Migration commands
    migrate_parser = subparsers.add_parser("migrate", help="Run database migration")
    migrate_parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without applying changes")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run consistency tests")
    test_parser.add_argument("--output", help="Output file for test results")
    
    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to previous version")
    rollback_parser.add_argument("version", help="Target version to rollback to")
    
    # Schema validation
    validate_parser = subparsers.add_parser("validate", help="Validate schema consistency")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the appropriate command
    if args.command == "migrate":
        run_migration(args)
    elif args.command == "status":
        show_status(args)
    elif args.command == "test":
        asyncio.run(run_tests(args))
    elif args.command == "rollback":
        run_rollback(args)
    elif args.command == "validate":
        validate_schema(args)


def run_migration(args):
    """Run database migration"""
    print(f"Starting database migration for {args.db_path}...")
    
    migration_manager = MigrationManager(args.db_path)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be applied")
        synchronizer = SchemaSynchronizer(args.db_path)
        migration_sql = synchronizer.generate_migration_sql()
        print("\nGenerated migration SQL:")
        print("-" * 50)
        print(migration_sql)
        return
    
    # Create backup
    print("Creating backup...")
    backup_path = migration_manager.synchronizer.create_schema_backup()
    if backup_path:
        print(f"Backup created: {backup_path}")
    else:
        print("Warning: Could not create backup")
    
    # Run migration
    success = migration_manager.run_full_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        
        # Show final status
        status = migration_manager.get_migration_status()
        print(f"Database version: {status['current_version']}")
        print(f"Schema valid: {status['validation']['valid']}")
    else:
        print("❌ Migration failed!")
        print("Check logs for details. You may need to restore from backup.")


def show_status(args):
    """Show migration status"""
    print(f"Checking status for {args.db_path}...")
    
    migration_manager = MigrationManager(args.db_path)
    status = migration_manager.get_migration_status()
    
    if "error" in status:
        print(f"❌ Error getting status: {status['error']}")
        return
    
    print(f"Current version: {status['current_version']}")
    print(f"Target version: {status['target_version']}")
    print(f"Needs migration: {'Yes' if status['needs_migration'] else 'No'}")
    
    validation = status['validation']
    print(f"Schema valid: {'Yes' if validation['valid'] else 'No'}")
    
    if validation['missing_tables']:
        print(f"Missing tables: {', '.join(validation['missing_tables'])}")
    
    if validation['schema_issues']:
        print("Schema issues:")
        for issue in validation['schema_issues']:
            print(f"  - {issue['table']}: {issue['issue']}")
    
    print("\nRecommendations:")
    for rec in status['recommendations']:
        print(f"  • {rec}")
    
    backup_files = status.get('backup_files', [])
    if backup_files:
        print(f"\nAvailable backups: {len(backup_files)}")
        for backup in backup_files[-3:]:  # Show last 3
            print(f"  - {backup}")


async def run_tests(args):
    """Run consistency tests"""
    print(f"Running consistency tests for {args.db_path}...")
    
    tester = AdapterConsistencyTester(args.db_path)
    test_results = await tester.run_full_test_suite()
    
    if "error" in test_results:
        print(f"❌ Test error: {test_results['error']}")
        return
    
    # Generate and display report
    report = tester.generate_test_report(test_results)
    print(report)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\nTest results saved to: {args.output}")
    
    # Also save raw JSON results
    json_output = args.output.replace('.txt', '.json') if args.output else 'test_results.json'
    with open(json_output, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"Raw test data saved to: {json_output}")


def run_rollback(args):
    """Run database rollback"""
    print(f"Rolling back {args.db_path} to version {args.version}...")
    
    migration_manager = MigrationManager(args.db_path)
    success = migration_manager.rollback_migration(args.version)
    
    if success:
        print("✅ Rollback completed successfully!")
    else:
        print("❌ Rollback failed!")
        print("Check logs for details.")


def validate_schema(args):
    """Validate schema consistency"""
    print(f"Validating schema for {args.db_path}...")
    
    synchronizer = SchemaSynchronizer(args.db_path)
    validation = synchronizer.validate_schema_consistency()
    
    if validation['valid']:
        print("✅ Schema is consistent!")
    else:
        print("❌ Schema inconsistencies found:")
        
        if validation['missing_tables']:
            print(f"Missing tables: {', '.join(validation['missing_tables'])}")
        
        for issue in validation['schema_issues']:
            print(f"Issue in {issue['table']}: {issue['issue']}")
            if 'details' in issue:
                print(f"  Details: {issue['details']}")
    
    print("\nRecommendations:")
    for rec in validation['recommendations']:
        print(f"  • {rec['action'] if isinstance(rec, dict) else rec}")


if __name__ == "__main__":
    main()