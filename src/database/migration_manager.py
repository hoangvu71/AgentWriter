"""
Database Migration Manager for BooksWriter
Handles data migration between schema versions and ensures data integrity
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from ..core.logging import get_logger
from .schema_synchronizer import SchemaSynchronizer


class MigrationManager:
    """Manages database schema migrations and data transformations"""
    
    def __init__(self, db_path: str = "local_database.db"):
        self.db_path = db_path
        self.logger = get_logger("migration_manager")
        self.synchronizer = SchemaSynchronizer(db_path)
        self.migrations_applied_file = "migrations_applied.json"
        
    def get_current_schema_version(self) -> str:
        """Get the current schema version from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if we have a schema_version table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)
                
                if not cursor.fetchone():
                    # No version table, assume version 0
                    return "000"
                
                cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else "000"
                
        except Exception as e:
            self.logger.warning(f"Could not determine schema version: {e}")
            return "000"
    
    def create_schema_version_table(self):
        """Create the schema version tracking table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL,
                        migration_name TEXT NOT NULL,
                        applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        checksum TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error creating schema_version table: {e}")
            raise
    
    def record_migration(self, version: str, migration_name: str, checksum: str = ""):
        """Record that a migration has been applied"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO schema_version (version, migration_name, checksum)
                    VALUES (?, ?, ?)
                """, (version, migration_name, checksum))
                conn.commit()
                self.logger.info(f"Recorded migration {version}: {migration_name}")
        except Exception as e:
            self.logger.error(f"Error recording migration: {e}")
            raise
    
    def migrate_world_building_data(self) -> bool:
        """Migrate world_building table from old simple structure to new complex structure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if old structure exists (has world_content column)
                cursor.execute("PRAGMA table_info(world_building)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'world_content' not in columns:
                    self.logger.info("World building table already has new structure")
                    return True
                
                self.logger.info("Migrating world_building table structure...")
                
                # Create backup
                cursor.execute("""
                    CREATE TABLE world_building_backup AS 
                    SELECT * FROM world_building
                """)
                
                # Drop old table
                cursor.execute("DROP TABLE world_building")
                
                # Create new table with updated structure
                cursor.execute("""
                    CREATE TABLE world_building (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        user_id TEXT,
                        plot_id TEXT,
                        world_name TEXT NOT NULL,
                        world_type TEXT NOT NULL DEFAULT 'fantasy',
                        overview TEXT NOT NULL DEFAULT '',
                        geography TEXT NOT NULL DEFAULT '{}',
                        political_landscape TEXT NOT NULL DEFAULT '{}',
                        cultural_systems TEXT NOT NULL DEFAULT '{}',
                        economic_framework TEXT NOT NULL DEFAULT '{}',
                        historical_timeline TEXT NOT NULL DEFAULT '{}',
                        power_systems TEXT NOT NULL DEFAULT '{}',
                        languages_and_communication TEXT NOT NULL DEFAULT '{}',
                        religious_and_belief_systems TEXT NOT NULL DEFAULT '{}',
                        unique_elements TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id),
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (plot_id) REFERENCES plots (id)
                    )
                """)
                
                # Migrate data from backup
                cursor.execute("""
                    INSERT INTO world_building (
                        id, session_id, user_id, plot_id, world_name, world_type, 
                        overview, created_at, updated_at
                    )
                    SELECT 
                        id, session_id, user_id, plot_id, world_name, world_type,
                        COALESCE(world_content, '') as overview,
                        created_at, created_at as updated_at
                    FROM world_building_backup
                """)
                
                # Drop backup table
                cursor.execute("DROP TABLE world_building_backup")
                conn.commit()
                
                self.logger.info("Successfully migrated world_building table")
                return True
                
        except Exception as e:
            self.logger.error(f"Error migrating world_building data: {e}")
            return False
    
    def migrate_target_audiences_data(self) -> bool:
        """Migrate target_audiences table to include new fields"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check current structure
                cursor.execute("PRAGMA table_info(target_audiences)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Add missing columns if they don't exist
                migrations_needed = []
                if 'interests' not in columns:
                    migrations_needed.append("ALTER TABLE target_audiences ADD COLUMN interests TEXT DEFAULT '[]'")
                if 'description' not in columns:
                    migrations_needed.append("ALTER TABLE target_audiences ADD COLUMN description TEXT")
                
                if not migrations_needed:
                    self.logger.info("Target audiences table already up to date")
                    return True
                
                self.logger.info("Updating target_audiences table structure...")
                for migration in migrations_needed:
                    cursor.execute(migration)
                
                conn.commit()
                self.logger.info("Successfully updated target_audiences table")
                return True
                
        except Exception as e:
            self.logger.error(f"Error migrating target_audiences data: {e}")
            return False
    
    def create_missing_tables(self) -> bool:
        """Create any missing tables from the latest schema"""
        try:
            validation = self.synchronizer.validate_schema_consistency()
            
            if not validation["missing_tables"]:
                self.logger.info("No missing tables detected")
                return True
            
            self.logger.info(f"Creating {len(validation['missing_tables'])} missing tables...")
            
            # Apply the migration SQL
            migration_sql = self.synchronizer.generate_migration_sql()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(migration_sql)
                conn.commit()
            
            self.logger.info("Successfully created missing tables")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating missing tables: {e}")
            return False
    
    def run_full_migration(self) -> bool:
        """Run complete migration to bring database up to latest schema"""
        try:
            current_version = self.get_current_schema_version()
            target_version = "009"  # Latest migration version
            
            self.logger.info(f"Starting migration from version {current_version} to {target_version}")
            
            # Create schema version table if it doesn't exist
            self.create_schema_version_table()
            
            # Create backup before migration
            backup_path = self.synchronizer.create_schema_backup()
            if not backup_path:
                self.logger.warning("Could not create backup, proceeding anyway...")
            
            # Step 1: Migrate world_building table
            if not self.migrate_world_building_data():
                raise Exception("Failed to migrate world_building table")
            
            # Step 2: Migrate target_audiences table
            if not self.migrate_target_audiences_data():
                raise Exception("Failed to migrate target_audiences table")
            
            # Step 3: Create missing tables
            if not self.create_missing_tables():
                raise Exception("Failed to create missing tables")
            
            # Step 4: Validate final schema
            validation = self.synchronizer.validate_schema_consistency()
            if not validation["valid"]:
                self.logger.warning("Schema validation failed after migration:")
                for issue in validation["schema_issues"]:
                    self.logger.warning(f"  - {issue}")
                for table in validation["missing_tables"]:
                    self.logger.warning(f"  - Missing table: {table}")
            
            # Record successful migration
            self.record_migration(
                target_version, 
                "Full schema synchronization to match Supabase",
                ""
            )
            
            self.logger.info(f"Migration completed successfully. Database is now at version {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False
    
    def rollback_migration(self, target_version: str) -> bool:
        """Rollback to a specific schema version"""
        try:
            # This is a simplified rollback - in production you'd want more sophisticated rollback logic
            self.logger.warning("Rollback functionality is limited in this implementation")
            
            # For now, we can restore from backup if available
            backup_files = list(Path(".").glob(f"{self.db_path}.backup_*"))
            if not backup_files:
                self.logger.error("No backup files found for rollback")
                return False
            
            # Use the most recent backup
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            
            self.logger.info(f"Restoring from backup: {latest_backup}")
            
            # Replace current database with backup
            import shutil
            shutil.copy2(latest_backup, self.db_path)
            
            self.logger.info("Rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and recommendations"""
        try:
            current_version = self.get_current_schema_version()
            validation = self.synchronizer.validate_schema_consistency()
            
            return {
                "current_version": current_version,
                "target_version": "009",
                "needs_migration": current_version != "009" or not validation["valid"],
                "validation": validation,
                "backup_files": list(Path(".").glob(f"{self.db_path}.backup_*")),
                "recommendations": self._get_migration_recommendations(current_version, validation)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting migration status: {e}")
            return {"error": str(e)}
    
    def _get_migration_recommendations(self, current_version: str, validation: Dict[str, Any]) -> List[str]:
        """Generate migration recommendations based on current state"""
        recommendations = []
        
        if current_version == "000":
            recommendations.append("Database appears to be at initial version - full migration recommended")
        elif current_version != "009":
            recommendations.append(f"Database version {current_version} is outdated - upgrade to 009 recommended")
        
        if validation["missing_tables"]:
            recommendations.append(f"Missing {len(validation['missing_tables'])} tables - schema synchronization needed")
        
        if validation["schema_issues"]:
            recommendations.append("Schema inconsistencies detected - data migration needed")
        
        if not recommendations:
            recommendations.append("Database schema is up to date")
        
        return recommendations