"""
Schema Synchronization System for BooksWriter Database
Ensures consistency between SQLite and Supabase schemas
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from ..core.logging import get_logger


class SchemaSynchronizer:
    """Synchronizes database schemas between SQLite and Supabase"""
    
    def __init__(self, sqlite_path: str = "local_database.db"):
        self.sqlite_path = sqlite_path
        self.logger = get_logger("schema_synchronizer")
        self.schema_version = "009"  # Current migration version
        
    def get_sqlite_schema_info(self) -> Dict[str, Any]:
        """Get complete schema information from SQLite database"""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                schema_info = {
                    "version": self.schema_version,
                    "tables": {},
                    "indexes": {},
                    "foreign_keys": {}
                }
                
                for table in tables:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [
                        {
                            "name": row[1],
                            "type": row[2],
                            "nullable": not bool(row[3]),
                            "default": row[4],
                            "primary_key": bool(row[5])
                        }
                        for row in cursor.fetchall()
                    ]
                    schema_info["tables"][table] = columns
                    
                    # Get indexes
                    cursor.execute(f"PRAGMA index_list({table})")
                    indexes = []
                    for idx_row in cursor.fetchall():
                        idx_name = idx_row[1]
                        cursor.execute(f"PRAGMA index_info({idx_name})")
                        idx_columns = [col_row[2] for col_row in cursor.fetchall()]
                        indexes.append({
                            "name": idx_name,
                            "columns": idx_columns,
                            "unique": bool(idx_row[2])
                        })
                    schema_info["indexes"][table] = indexes
                    
                    # Get foreign keys
                    cursor.execute(f"PRAGMA foreign_key_list({table})")
                    fks = [
                        {
                            "column": row[3],
                            "referenced_table": row[2],
                            "referenced_column": row[4],
                            "on_delete": row[6],
                            "on_update": row[5]
                        }
                        for row in cursor.fetchall()
                    ]
                    schema_info["foreign_keys"][table] = fks
                
                return schema_info
        except Exception as e:
            self.logger.error(f"Error getting SQLite schema info: {e}")
            return {}
    
    def validate_schema_consistency(self) -> Dict[str, Any]:
        """Validate that SQLite schema matches expected Supabase schema"""
        expected_tables = {
            # Core tables
            "users", "sessions", "authors", "plots", 
            # Enhanced world building and characters
            "world_building", "characters",
            # Genre hierarchy
            "genres", "subgenres", "microgenres", "tropes", "tones", "target_audiences",
            # Orchestrator decisions
            "orchestrator_decisions",
            # Iterative improvement system
            "improvement_sessions", "iterations", "critiques", "enhancements", "scores",
            # Observability and performance
            "agent_invocations", "performance_metrics", "trace_events"
        }
        
        schema_info = self.get_sqlite_schema_info()
        current_tables = set(schema_info.get("tables", {}).keys())
        
        validation_result = {
            "valid": True,
            "missing_tables": expected_tables - current_tables,
            "extra_tables": current_tables - expected_tables,
            "schema_issues": [],
            "recommendations": []
        }
        
        # Check world_building table structure
        if "world_building" in current_tables:
            wb_columns = {col["name"] for col in schema_info["tables"]["world_building"]}
            expected_wb_columns = {
                "id", "session_id", "user_id", "plot_id", "world_name", "world_type",
                "overview", "geography", "political_landscape", "cultural_systems",
                "economic_framework", "historical_timeline", "power_systems",
                "languages_and_communication", "religious_and_belief_systems",
                "unique_elements", "created_at", "updated_at"
            }
            
            missing_wb_columns = expected_wb_columns - wb_columns
            if missing_wb_columns:
                validation_result["schema_issues"].append({
                    "table": "world_building",
                    "issue": "missing_columns",
                    "details": list(missing_wb_columns)
                })
                validation_result["valid"] = False
        
        # Check characters table structure
        if "characters" in current_tables:
            char_columns = {col["name"] for col in schema_info["tables"]["characters"]}
            # Current characters table is compatible, but could be enhanced
            if "updated_at" not in char_columns:
                validation_result["recommendations"].append({
                    "table": "characters",
                    "recommendation": "add_updated_at_column",
                    "priority": "low"
                })
        
        if validation_result["missing_tables"]:
            validation_result["valid"] = False
            validation_result["recommendations"].append({
                "action": "create_missing_tables",
                "tables": list(validation_result["missing_tables"]),
                "priority": "high"
            })
        
        return validation_result
    
    def generate_migration_sql(self) -> str:
        """Generate SQL migration script to bring SQLite schema up to date"""
        validation = self.validate_schema_consistency()
        
        migration_sql = [
            "-- SQLite Schema Synchronization Migration",
            f"-- Generated: {datetime.utcnow().isoformat()}",
            f"-- Target Schema Version: {self.schema_version}",
            "",
            "BEGIN TRANSACTION;",
            "",
            "-- Enable foreign keys",
            "PRAGMA foreign_keys = ON;",
            ""
        ]
        
        # Create missing tables
        if validation["missing_tables"]:
            migration_sql.extend(self._generate_missing_tables_sql(validation["missing_tables"]))
        
        # Fix schema issues
        for issue in validation["schema_issues"]:
            if issue["table"] == "world_building" and issue["issue"] == "missing_columns":
                migration_sql.extend(self._generate_world_building_fix_sql())
        
        migration_sql.extend([
            "",
            "COMMIT;",
            "",
            f"-- Schema version updated to {self.schema_version}"
        ])
        
        return "\n".join(migration_sql)
    
    def _generate_missing_tables_sql(self, missing_tables: set) -> List[str]:
        """Generate SQL for creating missing tables"""
        sql_parts = ["-- Create missing tables", ""]
        
        table_sql_map = {
            "genres": """
CREATE TABLE IF NOT EXISTS genres (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "subgenres": """
CREATE TABLE IF NOT EXISTS subgenres (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    genre_id TEXT REFERENCES genres(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(genre_id, name)
);""",
            
            "microgenres": """
CREATE TABLE IF NOT EXISTS microgenres (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    subgenre_id TEXT REFERENCES subgenres(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subgenre_id, name)
);""",
            
            "tropes": """
CREATE TABLE IF NOT EXISTS tropes (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    category TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "tones": """
CREATE TABLE IF NOT EXISTS tones (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "improvement_sessions": """
CREATE TABLE IF NOT EXISTS improvement_sessions (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    original_content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    target_score REAL DEFAULT 9.5,
    max_iterations INTEGER DEFAULT 4,
    status TEXT DEFAULT 'in_progress',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    completion_reason TEXT,
    final_content TEXT,
    final_score REAL
);""",
            
            "iterations": """
CREATE TABLE IF NOT EXISTS iterations (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    improvement_session_id TEXT REFERENCES improvement_sessions(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "critiques": """
CREATE TABLE IF NOT EXISTS critiques (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
    critique_json TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "enhancements": """
CREATE TABLE IF NOT EXISTS enhancements (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
    enhanced_content TEXT NOT NULL,
    changes_made TEXT NOT NULL,
    rationale TEXT NOT NULL,
    confidence_score INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "scores": """
CREATE TABLE IF NOT EXISTS scores (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    iteration_id TEXT REFERENCES iterations(id) ON DELETE CASCADE,
    overall_score REAL NOT NULL,
    category_scores TEXT NOT NULL,
    score_rationale TEXT NOT NULL,
    improvement_trajectory TEXT NOT NULL,
    recommendations TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "agent_invocations": """
CREATE TABLE IF NOT EXISTS agent_invocations (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    invocation_id TEXT UNIQUE NOT NULL,
    agent_name TEXT NOT NULL,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    request_content TEXT NOT NULL,
    request_context TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_ms REAL,
    llm_model TEXT,
    final_prompt TEXT,
    raw_response TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    tool_calls TEXT DEFAULT '[]',
    tool_results TEXT DEFAULT '[]',
    latency_ms REAL,
    cost_estimate REAL,
    success BOOLEAN DEFAULT 0,
    error_message TEXT,
    response_content TEXT,
    parsed_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "performance_metrics": """
CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    tags TEXT DEFAULT '{}',
    agent_name TEXT,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            
            "trace_events": """
CREATE TABLE IF NOT EXISTS trace_events (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    span_name TEXT NOT NULL,
    span_kind TEXT DEFAULT 'INTERNAL',
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_ns INTEGER,
    attributes TEXT DEFAULT '{}',
    events TEXT DEFAULT '[]',
    status_code TEXT DEFAULT 'OK',
    status_message TEXT,
    resource_attributes TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);"""
        }
        
        for table in missing_tables:
            if table in table_sql_map:
                sql_parts.append(table_sql_map[table])
                sql_parts.append("")
        
        return sql_parts
    
    def _generate_world_building_fix_sql(self) -> List[str]:
        """Generate SQL to fix world_building table structure"""
        return [
            "-- Fix world_building table structure",
            "",
            "-- Create new world_building table with correct structure",
            """CREATE TABLE IF NOT EXISTS world_building_new (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    plot_id TEXT REFERENCES plots(id) ON DELETE SET NULL,
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
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);""",
            "",
            "-- Migrate existing data",
            """INSERT INTO world_building_new (id, session_id, user_id, plot_id, world_name, world_type, overview, created_at)
SELECT id, session_id, user_id, plot_id, world_name, world_type, 
       COALESCE(world_content, '') as overview, created_at
FROM world_building;""",
            "",
            "-- Drop old table and rename new one",
            "DROP TABLE world_building;",
            "ALTER TABLE world_building_new RENAME TO world_building;",
            ""
        ]
    
    def apply_migration(self) -> bool:
        """Apply the migration to bring SQLite schema up to date"""
        try:
            migration_sql = self.generate_migration_sql()
            
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.executescript(migration_sql)
                conn.commit()
            
            self.logger.info(f"Successfully applied schema migration to {self.sqlite_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying migration: {e}")
            return False
    
    def create_schema_backup(self) -> str:
        """Create a backup of the current schema"""
        backup_path = f"{self.sqlite_path}.backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        try:
            with sqlite3.connect(self.sqlite_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            self.logger.info(f"Schema backup created at {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating schema backup: {e}")
            return ""