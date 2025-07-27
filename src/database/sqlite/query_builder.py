"""
SQLite Query Builder - Builds safe SQL queries with parameterized inputs.
Extracted from SQLiteAdapter for better modularity and security.
"""

import re
from typing import Dict, Any, List, Tuple, Optional

from ...core.logging import get_logger


class SQLiteQueryBuilder:
    """Builds safe SQL queries for SQLite operations"""
    
    def __init__(self):
        """Initialize query builder"""
        self.logger = get_logger("sqlite_query_builder")
        
        # Regex for validating SQL identifiers (table/column names)
        self._identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    def sanitize_table_name(self, table_name: str) -> str:
        """Sanitize table name to prevent SQL injection"""
        if not self._identifier_pattern.match(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name
    
    def sanitize_column_name(self, column_name: str) -> str:
        """Sanitize column name to prevent SQL injection"""
        if not self._identifier_pattern.match(column_name):
            raise ValueError(f"Invalid column name: {column_name}")
        return column_name
    
    def build_insert(self, table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build INSERT query with parameterized values"""
        if not data:
            raise ValueError("Insert data cannot be empty")
        
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        # Sanitize column names and build query
        columns = [self.sanitize_column_name(col) for col in data.keys()]
        placeholders = ['?' for _ in columns]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        params = list(data.values())
        
        return query, params
    
    def build_select(self, table: str, filters: Optional[Dict[str, Any]] = None,
                    order_by: Optional[str] = None, desc: bool = False,
                    limit: Optional[int] = None) -> Tuple[str, List[Any]]:
        """Build SELECT query with optional filters, ordering, and limit"""
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        query = f"SELECT * FROM {table}"
        params = []
        
        # Add WHERE clause
        if filters:
            conditions = []
            for key, value in filters.items():
                sanitized_key = self.sanitize_column_name(key)
                conditions.append(f"{sanitized_key} = ?")
                params.append(value)
            query += f" WHERE {' AND '.join(conditions)}"
        
        # Add ORDER BY clause
        if order_by:
            sanitized_order = self.sanitize_column_name(order_by)
            direction = "DESC" if desc else "ASC"
            query += f" ORDER BY {sanitized_order} {direction}"
        
        # Add LIMIT clause
        if limit:
            query += f" LIMIT {limit}"
        
        return query, params
    
    def build_update(self, table: str, record_id: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build UPDATE query with parameterized values"""
        if not data:
            raise ValueError("Update data cannot be empty")
        
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        # Build SET clause
        set_clauses = []
        params = []
        for key, value in data.items():
            sanitized_key = self.sanitize_column_name(key)
            set_clauses.append(f"{sanitized_key} = ?")
            params.append(value)
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(record_id)
        
        return query, params
    
    def build_delete(self, table: str, record_id: str) -> Tuple[str, List[Any]]:
        """Build DELETE query"""
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        query = f"DELETE FROM {table} WHERE id = ?"
        params = [record_id]
        
        return query, params
    
    def build_count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Any]]:
        """Build COUNT query with optional filters"""
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        query = f"SELECT COUNT(*) FROM {table}"
        params = []
        
        # Add WHERE clause
        if filters:
            conditions = []
            for key, value in filters.items():
                sanitized_key = self.sanitize_column_name(key)
                conditions.append(f"{sanitized_key} = ?")
                params.append(value)
            query += f" WHERE {' AND '.join(conditions)}"
        
        return query, params
    
    def build_search(self, table: str, search_criteria: Dict[str, str], 
                    limit: Optional[int] = None) -> Tuple[str, List[Any]]:
        """Build search query with LIKE conditions"""
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        query = f"SELECT * FROM {table}"
        params = []
        
        if search_criteria:
            conditions = []
            for key, value in search_criteria.items():
                sanitized_key = self.sanitize_column_name(key)
                conditions.append(f"{sanitized_key} LIKE ?")
                params.append(value)
            query += f" WHERE {' AND '.join(conditions)}"
        
        # Add LIMIT clause
        if limit:
            query += f" LIMIT {limit}"
        
        return query, params
    
    def build_batch_insert(self, table: str, records: List[Dict[str, Any]]) -> Tuple[str, List[Any]]:
        """Build batch INSERT query for multiple records"""
        if not records:
            raise ValueError("Batch insert records cannot be empty")
        
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        # Use first record to determine columns
        first_record = records[0]
        columns = [self.sanitize_column_name(col) for col in first_record.keys()]
        
        # Build VALUES clause for all records
        placeholders = ', '.join(['?' for _ in columns])
        values_clauses = []
        params = []
        
        for record in records:
            values_clauses.append(f"({placeholders})")
            params.extend([record[col] for col in first_record.keys()])
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES {', '.join(values_clauses)}"
        
        return query, params
    
    def build_select_by_ids(self, table: str, ids: List[str]) -> Tuple[str, List[Any]]:
        """Build SELECT query for multiple IDs"""
        if not ids:
            raise ValueError("IDs list cannot be empty")
        
        # Sanitize table name
        table = self.sanitize_table_name(table)
        
        placeholders = ', '.join(['?' for _ in ids])
        query = f"SELECT * FROM {table} WHERE id IN ({placeholders})"
        
        return query, ids