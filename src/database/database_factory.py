"""
Database factory for selecting appropriate database adapter.
Supports explicit database mode selection via environment variable.
"""

import os
import asyncio
from typing import Union, Optional
from .supabase_adapter import SupabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from ..core.configuration import config
from ..core.logging import get_logger
import httpx


class DatabaseFactory:
    """Factory for creating database adapters with automatic fallback"""
    
    def __init__(self):
        self.logger = get_logger("database_factory")
        self._supabase_available = None
        self._adapter = None
    
    async def get_adapter(self) -> Union[SupabaseAdapter, SQLiteAdapter]:
        """Get appropriate database adapter based on configuration"""
        
        # Return cached adapter if already initialized
        if self._adapter is not None:
            return self._adapter
        
        # Check DATABASE_MODE environment variable
        database_mode = os.getenv("DATABASE_MODE", "supabase").lower()
        
        if database_mode == "sqlite":
            # Force SQLite mode for development
            self.logger.info("Using SQLite for database storage (DATABASE_MODE=sqlite)")
            db_path = os.getenv("SQLITE_DB_PATH", "development.db")
            self._adapter = SQLiteAdapter(db_path)
            self._supabase_available = False
        elif database_mode == "supabase" and config.is_supabase_enabled():
            # Try Supabase if explicitly set and configured
            is_available = await self._check_supabase_connectivity()
            
            if is_available:
                self.logger.info("Using Supabase for database storage")
                self._adapter = SupabaseAdapter(
                    url=config.supabase_config["url"],
                    key=config.supabase_config["anon_key"]
                )
                self._supabase_available = True
            else:
                self.logger.warning("Supabase unavailable, falling back to SQLite")
                db_path = os.getenv("SQLITE_DB_PATH", "development.db")
                self._adapter = SQLiteAdapter(db_path)
                self._supabase_available = False
        else:
            # Default to SQLite if Supabase not configured
            self.logger.info("Using SQLite for database storage (default)")
            db_path = os.getenv("SQLITE_DB_PATH", "development.db")
            self._adapter = SQLiteAdapter(db_path)
            self._supabase_available = False
        
        return self._adapter
    
    async def _check_supabase_connectivity(self) -> bool:
        """Check if Supabase is reachable"""
        try:
            async with httpx.AsyncClient() as client:
                # Test connection with a short timeout
                response = await client.get(
                    f"{config.supabase_config['url']}/rest/v1/",
                    timeout=5.0,
                    headers={"apikey": config.supabase_config["anon_key"]}
                )
                return response.status_code < 500
        except Exception as e:
            self.logger.warning(f"Supabase connectivity check failed: {e}")
            return False
    
    
    def is_using_supabase(self) -> bool:
        """Check if currently using Supabase"""
        return self._supabase_available is True
    
    def is_offline_mode(self) -> bool:
        """Check if in offline mode (using SQLite)"""
        return self._supabase_available is False
    
    async def sync_offline_data(self):
        """Sync offline SQLite data to Supabase when connection is restored"""
        if not self.is_offline_mode():
            self.logger.info("Not in offline mode, no sync needed")
            return
        
        # Check if Supabase is now available
        if config.is_supabase_enabled() and await self._check_supabase_connectivity():
            self.logger.info("Supabase connection restored, syncing offline data...")
            
            try:
                # Get both adapters
                sqlite_adapter = SQLiteAdapter()
                supabase_adapter = SupabaseAdapter(
                    url=config.supabase_config["url"],
                    key=config.supabase_config["anon_key"]
                )
                
                # Sync each table
                tables_to_sync = [
                    'users', 'sessions', 'authors', 'plots', 
                    'world_building', 'characters', 'orchestrator_decisions',
                    'genres', 'target_audiences'
                ]
                
                for table in tables_to_sync:
                    # Get all records from SQLite
                    records = await sqlite_adapter.select(table)
                    
                    if records:
                        self.logger.info(f"Syncing {len(records)} records from {table}")
                        
                        for record in records:
                            try:
                                # Check if record exists in Supabase
                                existing = await supabase_adapter.select(
                                    table, 
                                    filters={'id': record['id']}
                                )
                                
                                if not existing:
                                    # Insert new record
                                    await supabase_adapter.insert(table, record)
                                else:
                                    # Update existing record if offline version is newer
                                    if record.get('created_at', '') > existing[0].get('created_at', ''):
                                        await supabase_adapter.update(
                                            table, 
                                            record['id'], 
                                            record
                                        )
                            except Exception as e:
                                self.logger.error(f"Error syncing record {record['id']} in {table}: {e}")
                
                self.logger.info("Offline data sync completed")
                
                # Switch to Supabase adapter
                self._adapter = supabase_adapter
                self._supabase_available = True
                
            except Exception as e:
                self.logger.error(f"Error during offline data sync: {e}")
        else:
            self.logger.warning("Supabase still unavailable, continuing in offline mode")


# Global database factory instance
db_factory = DatabaseFactory()