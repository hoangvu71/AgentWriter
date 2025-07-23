"""
Base repository implementation with common database operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from datetime import datetime
from ..core.interfaces import IDatabase
from ..core.logging import get_logger

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, database: IDatabase, table_name: str):
        self._database = database
        self._table_name = table_name
        self._logger = get_logger(f"repo.{table_name}")
    
    @abstractmethod
    def _serialize(self, entity: T) -> Dict[str, Any]:
        """Convert entity to database format"""
        pass
    
    @abstractmethod
    def _deserialize(self, data: Dict[str, Any]) -> T:
        """Convert database data to entity"""
        pass
    
    async def create(self, entity: T) -> str:
        """Create a new entity and return its ID"""
        try:
            data = self._serialize(entity)
            entity_id = await self._database.insert(self._table_name, data)
            self._logger.info(f"Created {self._table_name} with ID: {entity_id}")
            return entity_id
        except Exception as e:
            self._logger.error(f"Error creating {self._table_name}: {e}", error=e)
            raise
    
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        try:
            data = await self._database.get_by_id(self._table_name, entity_id)
            if data:
                return self._deserialize(data)
            return None
        except Exception as e:
            self._logger.error(f"Error getting {self._table_name} by ID {entity_id}: {e}", error=e)
            raise
    
    async def update(self, entity_id: str, entity: T) -> bool:
        """Update an existing entity"""
        try:
            data = self._serialize(entity)
            success = await self._database.update(self._table_name, entity_id, data)
            if success:
                self._logger.info(f"Updated {self._table_name} with ID: {entity_id}")
            return success
        except Exception as e:
            self._logger.error(f"Error updating {self._table_name} {entity_id}: {e}", error=e)
            raise
    
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID"""
        try:
            success = await self._database.delete(self._table_name, entity_id)
            if success:
                self._logger.info(f"Deleted {self._table_name} with ID: {entity_id}")
            return success
        except Exception as e:
            self._logger.error(f"Error deleting {self._table_name} {entity_id}: {e}", error=e)
            raise
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination"""
        try:
            data_list = await self._database.get_all(self._table_name, limit, offset)
            return [self._deserialize(data) for data in data_list]
        except Exception as e:
            self._logger.error(f"Error getting all {self._table_name}: {e}", error=e)
            raise
    
    async def search(self, criteria: Dict[str, Any], limit: int = 50) -> List[T]:
        """Search entities by criteria"""
        try:
            data_list = await self._database.search(self._table_name, criteria, limit)
            return [self._deserialize(data) for data in data_list]
        except Exception as e:
            self._logger.error(f"Error searching {self._table_name}: {e}", error=e)
            raise
    
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching criteria"""
        try:
            return await self._database.count(self._table_name, criteria)
        except Exception as e:
            self._logger.error(f"Error counting {self._table_name}: {e}", error=e)
            raise
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None