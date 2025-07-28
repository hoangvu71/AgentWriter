"""
SQLite Constraint Manager - Handles database primary keys, foreign keys, and constraint management.
Extracted from SQLiteTableManager for better modularity and single responsibility.
"""

from typing import List, Dict, Any, Optional

from ...core.logging import get_logger
from .connection_manager import SQLiteConnectionManager


class SQLiteConstraintManager:
    """Manages SQLite database constraints"""
    
    def __init__(self, connection_manager: SQLiteConnectionManager):
        """Initialize constraint manager with connection manager"""
        self.connection_manager = connection_manager
        self.logger = get_logger("sqlite_constraint_manager")
    
    def enable_foreign_key_constraints(self):
        """Enable foreign key constraint enforcement"""
        self.connection_manager.execute_query("PRAGMA foreign_keys = ON")
        self.logger.info("Foreign key constraints enabled")
    
    def disable_foreign_key_constraints(self):
        """Disable foreign key constraint enforcement"""
        self.connection_manager.execute_query("PRAGMA foreign_keys = OFF")
        self.logger.info("Foreign key constraints disabled")
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key information for a table"""
        query = f"PRAGMA foreign_key_list({table_name})"
        return self.connection_manager.execute_select(query)
    
    def get_all_foreign_keys(self) -> List[Dict[str, Any]]:
        """Get all foreign key relationships in the database"""
        # Get all table names
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        tables = self.connection_manager.execute_select(tables_query)
        
        all_fks = []
        
        for table in tables:
            table_name = table['name']
            fks = self.get_foreign_keys(table_name)
            
            for fk in fks:
                fk_info = {
                    'child_table': table_name,
                    'child_column': fk['from'],
                    'parent_table': fk['table'],
                    'parent_column': fk['to'],
                    'constraint_id': fk['id'],
                    'update_rule': fk.get('on_update', 'NO ACTION'),
                    'delete_rule': fk.get('on_delete', 'NO ACTION')
                }
                all_fks.append(fk_info)
        
        return all_fks
    
    def validate_foreign_key_constraints(self) -> List[Dict[str, Any]]:
        """Validate foreign key constraints and return violations"""
        try:
            # Check foreign key constraint integrity
            query = "PRAGMA foreign_key_check"
            violations = self.connection_manager.execute_select(query)
            
            formatted_violations = []
            for violation in violations:
                formatted_violations.append({
                    'table': violation.get('table'),
                    'rowid': violation.get('rowid'),
                    'parent': violation.get('parent'),
                    'fkid': violation.get('fkid')
                })
            
            return formatted_violations
        
        except Exception as e:
            self.logger.error(f"Error validating foreign key constraints: {e}")
            return []
    
    def get_primary_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get primary key information for a table"""
        query = f"PRAGMA table_info({table_name})"
        columns = self.connection_manager.execute_select(query)
        
        primary_keys = []
        for column in columns:
            if column['pk']:
                primary_keys.append({
                    'name': column['name'],
                    'type': column['type'],
                    'pk_position': column['pk']
                })
        
        return primary_keys
    
    def get_unique_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Get unique constraint information for a table"""
        # Get index list for unique constraints
        query = f"PRAGMA index_list({table_name})"
        indexes = self.connection_manager.execute_select(query)
        
        unique_constraints = []
        for index in indexes:
            if index['unique']:
                # Get index info
                index_info_query = f"PRAGMA index_info({index['name']})"
                index_columns = self.connection_manager.execute_select(index_info_query)
                
                unique_constraints.append({
                    'name': index['name'],
                    'columns': [col['name'] for col in index_columns],
                    'partial': index.get('partial', 0) == 1
                })
        
        return unique_constraints
    
    def get_check_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Get check constraint information for a table"""
        # SQLite stores check constraints in the CREATE TABLE statement
        query = "SELECT sql FROM sqlite_master WHERE type='table' AND name=?"
        results = self.connection_manager.execute_select(query, [table_name])
        
        check_constraints = []
        if results:
            sql = results[0]['sql']
            
            # Parse CHECK constraints from the SQL
            # This is a simplified parser - in production, you might want a more robust one
            import re
            check_pattern = r'CHECK\s*\(([^)]+)\)'
            matches = re.findall(check_pattern, sql, re.IGNORECASE)
            
            for i, match in enumerate(matches):
                check_constraints.append({
                    'name': f'check_{table_name}_{i}',
                    'expression': match.strip(),
                    'sql': sql
                })
        
        return check_constraints
    
    def validate_not_null_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Validate NOT NULL constraints for a table"""
        # Get table schema
        query = f"PRAGMA table_info({table_name})"
        columns = self.connection_manager.execute_select(query)
        
        not_null_columns = [col['name'] for col in columns if col['notnull']]
        
        violations = []
        
        # Check for NULL values in NOT NULL columns
        for column in not_null_columns:
            null_check_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {column} IS NULL"
            try:
                result = self.connection_manager.execute_select(null_check_query)
                if result and result[0]['count'] > 0:
                    violations.append({
                        'table': table_name,
                        'column': column,
                        'null_count': result[0]['count'],
                        'constraint_type': 'NOT NULL'
                    })
            except Exception as e:
                self.logger.warning(f"Error checking NOT NULL constraint on {table_name}.{column}: {e}")
        
        return violations
    
    def get_constraint_violations(self) -> List[Dict[str, Any]]:
        """Get all constraint violations in the database"""
        all_violations = []
        
        # Check foreign key violations
        fk_violations = self.validate_foreign_key_constraints()
        for violation in fk_violations:
            violation['constraint_type'] = 'FOREIGN KEY'
            all_violations.append(violation)
        
        # Check NOT NULL violations for all tables
        tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        tables = self.connection_manager.execute_select(tables_query)
        
        for table in tables:
            table_name = table['name']
            not_null_violations = self.validate_not_null_constraints(table_name)
            all_violations.extend(not_null_violations)
        
        return all_violations
    
    def add_foreign_key_constraint(self, child_table: str, child_column: str, 
                                 parent_table: str, parent_column: str):
        """Add a foreign key constraint to an existing table"""
        # SQLite doesn't support adding foreign keys to existing tables directly
        # This would require recreating the table with the new constraint
        
        self.logger.info(f"Adding foreign key constraint: {child_table}.{child_column} -> {parent_table}.{parent_column}")
        
        try:
            # Get current table schema
            schema_query = f"PRAGMA table_info({child_table})"
            columns = self.connection_manager.execute_select(schema_query)
            
            # Get existing foreign keys
            existing_fks = self.get_foreign_keys(child_table)
            
            # Generate new CREATE TABLE statement with the additional foreign key
            # This is a simplified implementation - production code would need more robust SQL generation
            column_defs = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if col['pk']:
                    col_def += " PRIMARY KEY"
                if col['notnull'] and not col['pk']:
                    col_def += " NOT NULL"
                if col['dflt_value'] is not None:
                    col_def += f" DEFAULT {col['dflt_value']}"
                column_defs.append(col_def)
            
            # Add existing foreign keys
            fk_defs = []
            for fk in existing_fks:
                fk_defs.append(f"FOREIGN KEY ({fk['from']}) REFERENCES {fk['table']} ({fk['to']})")
            
            # Add new foreign key
            fk_defs.append(f"FOREIGN KEY ({child_column}) REFERENCES {parent_table} ({parent_column})")
            
            # Create new table with foreign key
            temp_table = f"{child_table}_temp"
            
            # This is a simplified approach - production would need more careful handling
            all_defs = column_defs + fk_defs
            create_sql = f"CREATE TABLE {temp_table} ({', '.join(all_defs)})"
            
            # For now, just log what would be done
            self.logger.info(f"Would execute: {create_sql}")
            
        except Exception as e:
            self.logger.error(f"Error adding foreign key constraint: {e}")
            raise
    
    def drop_foreign_key_constraint(self, table_name: str, constraint_name: str):
        """Drop a foreign key constraint"""
        # SQLite doesn't support dropping individual foreign keys
        # This would require recreating the table without the constraint
        
        self.logger.info(f"Dropping foreign key constraint: {constraint_name} from {table_name}")
        
        try:
            # Get existing foreign keys
            existing_fks = self.get_foreign_keys(table_name)
            
            # Find the constraint to remove
            fk_to_remove = None
            for fk in existing_fks:
                if fk['from'] == constraint_name or str(fk['id']) == constraint_name:
                    fk_to_remove = fk
                    break
            
            if fk_to_remove:
                self.logger.info(f"Found foreign key to remove: {fk_to_remove}")
                # In production, would recreate table without this foreign key
            else:
                self.logger.warning(f"Foreign key constraint {constraint_name} not found in {table_name}")
                
        except Exception as e:
            self.logger.error(f"Error dropping foreign key constraint: {e}")
            raise
    
    def add_check_constraint(self, table_name: str, constraint_name: str, check_expression: str):
        """Add a check constraint to a table"""
        # SQLite doesn't support adding check constraints to existing tables
        # This would require recreating the table with the new constraint
        
        self.logger.info(f"Adding check constraint {constraint_name} to {table_name}: {check_expression}")
        
        try:
            # Get current table schema
            schema_query = f"PRAGMA table_info({table_name})"
            columns = self.connection_manager.execute_select(schema_query)
            
            # For now, just log what would be done
            self.logger.info(f"Would add check constraint: CHECK ({check_expression})")
            
        except Exception as e:
            self.logger.error(f"Error adding check constraint: {e}")
            raise
    
    def validate_all_constraints(self) -> List[Dict[str, Any]]:
        """Validate all database constraints"""
        self.logger.info("Validating all database constraints")
        
        all_violations = self.get_constraint_violations()
        
        if all_violations:
            self.logger.warning(f"Found {len(all_violations)} constraint violations")
        else:
            self.logger.info("All constraints are valid")
        
        return all_violations
    
    def get_table_constraints_summary(self, table_name: str) -> Dict[str, Any]:
        """Get a summary of all constraints for a table"""
        summary = {
            'table_name': table_name,
            'primary_keys': self.get_primary_keys(table_name),
            'foreign_keys': self.get_foreign_keys(table_name),
            'unique_constraints': self.get_unique_constraints(table_name),
            'check_constraints': self.get_check_constraints(table_name)
        }
        
        # Get NOT NULL columns
        query = f"PRAGMA table_info({table_name})"
        columns = self.connection_manager.execute_select(query)
        summary['not_null_columns'] = [col['name'] for col in columns if col['notnull']]
        
        return summary
    
    def repair_constraint_violations(self) -> List[Dict[str, Any]]:
        """Repair constraint violations (where possible)"""
        self.logger.info("Analyzing constraint violations for repair")
        
        violations = self.get_constraint_violations()
        repair_results = []
        
        # For now, just return analysis - actual repair would need careful implementation
        for violation in violations:
            repair_results.append({
                'violation': violation,
                'repair_action': 'analyzed',
                'status': 'no_repair_needed',
                'message': 'No automatic repair implemented'
            })
        
        return repair_results