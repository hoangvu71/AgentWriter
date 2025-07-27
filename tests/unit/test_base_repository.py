"""
TDD Test Suite for BaseRepository pattern.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- BaseRepository CRUD operations
- Entity serialization/deserialization
- Database adapter integration
- Error handling and logging
- Search and pagination functionality
- Data validation and type safety
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from src.repositories.base_repository import BaseRepository
from src.core.interfaces import IDatabase
from src.models.entities import Plot


class MockEntity:
    """Mock entity for testing repository patterns"""
    
    def __init__(self, id: str = None, name: str = "Test", created_at: datetime = None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.created_at = created_at  # Don't default to datetime.now() to allow None


class ConcreteTestRepository(BaseRepository[MockEntity]):
    """Concrete test repository implementation"""
    
    def _serialize(self, entity: MockEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "name": entity.name,
            "created_at": entity.created_at.isoformat() if entity.created_at else None
        }
    
    def _deserialize(self, data: Dict[str, Any]) -> MockEntity:
        return MockEntity(
            id=data.get("id"),
            name=data.get("name", ""),
            created_at=self._parse_datetime(data.get("created_at"))
        )


class TestBaseRepositoryInitialization:
    """Test BaseRepository initialization"""
    
    def test_repository_initialization(self, mock_database):
        """
        RED: Test repository initialization with database and table name
        Should properly initialize with database interface and table name
        """
        # Arrange
        table_name = "test_entities"
        
        # Act
        repo = ConcreteTestRepository(mock_database, table_name)
        
        # Assert
        assert repo._database == mock_database
        assert repo._table_name == table_name
        assert repo._logger is not None


class TestBaseRepositoryCRUDOperations:
    """Test CRUD operations in BaseRepository"""
    
    @pytest.mark.asyncio
    async def test_create_entity_success(self, mock_database):
        """
        RED: Test successful entity creation
        Should serialize entity and call database insert
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity = MockEntity(name="Test Entity")
        expected_id = str(uuid.uuid4())
        mock_database.insert.return_value = expected_id
        
        # Act
        result_id = await repo.create(entity)
        
        # Assert
        assert result_id == expected_id
        mock_database.insert.assert_called_once()
        call_args = mock_database.insert.call_args
        assert call_args[0][0] == "test_table"  # table_name
        assert call_args[0][1]["name"] == "Test Entity"  # serialized data
    
    @pytest.mark.asyncio
    async def test_create_entity_handles_database_error(self, mock_database):
        """
        RED: Test entity creation with database error
        Should propagate database errors
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity = MockEntity(name="Error Entity")
        mock_database.insert.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await repo.create(entity)
        
        assert "Database connection failed" in str(exc_info.value)
        mock_database.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_existing_entity(self, mock_database):
        """
        RED: Test retrieving existing entity by ID
        Should call database get_by_id and deserialize result
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        db_data = {
            "id": entity_id,
            "name": "Retrieved Entity",
            "created_at": datetime.now().isoformat()
        }
        mock_database.get_by_id.return_value = db_data
        
        # Act
        entity = await repo.get_by_id(entity_id)
        
        # Assert
        assert entity is not None
        assert entity.id == entity_id
        assert entity.name == "Retrieved Entity"
        mock_database.get_by_id.assert_called_once_with("test_table", entity_id)
    
    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_entity(self, mock_database):
        """
        RED: Test retrieving non-existent entity by ID
        Should return None when entity doesn't exist
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        mock_database.get_by_id.return_value = None
        
        # Act
        entity = await repo.get_by_id(entity_id)
        
        # Assert
        assert entity is None
        mock_database.get_by_id.assert_called_once_with("test_table", entity_id)
    
    @pytest.mark.asyncio
    async def test_update_entity_success(self, mock_database):
        """
        RED: Test successful entity update
        Should serialize entity and call database update
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        entity = MockEntity(id=entity_id, name="Updated Entity")
        mock_database.update.return_value = True
        
        # Act
        success = await repo.update(entity_id, entity)
        
        # Assert
        assert success is True
        mock_database.update.assert_called_once()
        call_args = mock_database.update.call_args
        assert call_args[0][0] == "test_table"  # table_name
        assert call_args[0][1] == entity_id     # entity_id
        assert call_args[0][2]["name"] == "Updated Entity"  # serialized data
    
    @pytest.mark.asyncio
    async def test_update_entity_failure(self, mock_database):
        """
        RED: Test entity update failure
        Should return False when update fails
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        entity = MockEntity(id=entity_id, name="Failed Update")
        mock_database.update.return_value = False
        
        # Act
        success = await repo.update(entity_id, entity)
        
        # Assert
        assert success is False
        mock_database.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_entity_success(self, mock_database):
        """
        RED: Test successful entity deletion
        Should call database delete and return success status
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        mock_database.delete.return_value = True
        
        # Act
        success = await repo.delete(entity_id)
        
        # Assert
        assert success is True
        mock_database.delete.assert_called_once_with("test_table", entity_id)
    
    @pytest.mark.asyncio
    async def test_delete_entity_failure(self, mock_database):
        """
        RED: Test entity deletion failure
        Should return False when deletion fails
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        mock_database.delete.return_value = False
        
        # Act
        success = await repo.delete(entity_id)
        
        # Assert
        assert success is False
        mock_database.delete.assert_called_once_with("test_table", entity_id)


class TestBaseRepositoryQueryOperations:
    """Test query and search operations"""
    
    @pytest.mark.asyncio
    async def test_get_all_entities_with_pagination(self, mock_database):
        """
        RED: Test retrieving all entities with pagination
        Should call database get_all with limit and offset
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        db_data = [
            {"id": str(uuid.uuid4()), "name": "Entity 1", "created_at": datetime.now().isoformat()},
            {"id": str(uuid.uuid4()), "name": "Entity 2", "created_at": datetime.now().isoformat()}
        ]
        mock_database.get_all.return_value = db_data
        
        # Act
        entities = await repo.get_all(limit=10, offset=0)
        
        # Assert
        assert len(entities) == 2
        assert entities[0].name == "Entity 1"
        assert entities[1].name == "Entity 2"
        mock_database.get_all.assert_called_once_with("test_table", 10, 0)
    
    @pytest.mark.asyncio
    async def test_get_all_entities_default_pagination(self, mock_database):
        """
        RED: Test retrieving all entities with default pagination
        Should use default limit and offset values
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        mock_database.get_all.return_value = []
        
        # Act
        entities = await repo.get_all()
        
        # Assert
        assert entities == []
        mock_database.get_all.assert_called_once_with("test_table", 100, 0)
    
    @pytest.mark.asyncio
    async def test_search_entities_with_criteria(self, mock_database):
        """
        RED: Test searching entities with specific criteria
        Should call database search with criteria and deserialize results
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        search_criteria = {"name": "Test", "status": "active"}
        db_data = [
            {"id": str(uuid.uuid4()), "name": "Test Entity", "created_at": datetime.now().isoformat()}
        ]
        mock_database.search.return_value = db_data
        
        # Act
        entities = await repo.search(search_criteria, limit=25)
        
        # Assert
        assert len(entities) == 1
        assert entities[0].name == "Test Entity"
        mock_database.search.assert_called_once_with("test_table", search_criteria, 25)
    
    @pytest.mark.asyncio
    async def test_search_entities_default_limit(self, mock_database):
        """
        RED: Test searching entities with default limit
        Should use default limit when not specified
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        search_criteria = {"status": "active"}
        mock_database.search.return_value = []
        
        # Act
        entities = await repo.search(search_criteria)
        
        # Assert
        assert entities == []
        mock_database.search.assert_called_once_with("test_table", search_criteria, 50)
    
    @pytest.mark.asyncio
    async def test_count_entities_with_criteria(self, mock_database):
        """
        RED: Test counting entities with criteria
        Should call database count with criteria
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        criteria = {"status": "active"}
        expected_count = 5
        mock_database.count.return_value = expected_count
        
        # Act
        count = await repo.count(criteria)
        
        # Assert
        assert count == expected_count
        mock_database.count.assert_called_once_with("test_table", criteria)
    
    @pytest.mark.asyncio
    async def test_count_entities_without_criteria(self, mock_database):
        """
        RED: Test counting all entities without criteria
        Should call database count with None criteria
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        expected_count = 10
        mock_database.count.return_value = expected_count
        
        # Act
        count = await repo.count()
        
        # Assert
        assert count == expected_count
        mock_database.count.assert_called_once_with("test_table", None)


class TestBaseRepositorySerializationDeserialization:
    """Test entity serialization and deserialization"""
    
    def test_serialize_entity(self, mock_database):
        """
        RED: Test entity serialization
        Should convert entity to dictionary format for database storage
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity = MockEntity(
            id="test-id",
            name="Test Entity",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        # Act
        serialized = repo._serialize(entity)
        
        # Assert
        assert serialized["id"] == "test-id"
        assert serialized["name"] == "Test Entity"
        assert serialized["created_at"] == "2024-01-01T12:00:00"
    
    def test_deserialize_entity_complete_data(self, mock_database):
        """
        RED: Test entity deserialization with complete data
        Should convert database data to entity object
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        data = {
            "id": "test-id",
            "name": "Deserialized Entity",
            "created_at": "2024-01-01T12:00:00"
        }
        
        # Act
        entity = repo._deserialize(data)
        
        # Assert
        assert entity.id == "test-id"
        assert entity.name == "Deserialized Entity"
        assert entity.created_at.year == 2024
        assert entity.created_at.month == 1
        assert entity.created_at.day == 1
    
    def test_deserialize_entity_partial_data(self, mock_database):
        """
        RED: Test entity deserialization with partial data
        Should handle missing fields gracefully with defaults
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        data = {"id": "partial-id"}  # Missing name and created_at
        
        # Act
        entity = repo._deserialize(data)
        
        # Assert
        assert entity.id == "partial-id"
        assert entity.name == ""  # Default empty string
        assert entity.created_at is None  # No created_at provided
    
    def test_parse_datetime_valid_iso_format(self, mock_database):
        """
        RED: Test datetime parsing with valid ISO format
        Should parse ISO datetime strings correctly
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        iso_datetime = "2024-01-01T12:00:00"
        
        # Act
        parsed = repo._parse_datetime(iso_datetime)
        
        # Assert
        assert parsed is not None
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 1
        assert parsed.hour == 12
    
    def test_parse_datetime_with_timezone(self, mock_database):
        """
        RED: Test datetime parsing with timezone info
        Should handle timezone-aware datetime strings
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        tz_datetime = "2024-01-01T12:00:00Z"
        
        # Act
        parsed = repo._parse_datetime(tz_datetime)
        
        # Assert
        assert parsed is not None
        assert parsed.year == 2024
        # Should handle timezone conversion
    
    def test_parse_datetime_invalid_format(self, mock_database):
        """
        RED: Test datetime parsing with invalid format
        Should return None for invalid datetime strings
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        invalid_datetime = "not-a-datetime"
        
        # Act
        parsed = repo._parse_datetime(invalid_datetime)
        
        # Assert
        assert parsed is None
    
    def test_parse_datetime_none_value(self, mock_database):
        """
        RED: Test datetime parsing with None value
        Should return None when input is None
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        
        # Act
        parsed = repo._parse_datetime(None)
        
        # Assert
        assert parsed is None


class TestBaseRepositoryErrorHandling:
    """Test error handling and logging"""
    
    @pytest.mark.asyncio
    async def test_create_entity_logs_success(self, mock_database):
        """
        RED: Test that successful entity creation is logged
        Should log creation with entity ID
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity = MockEntity(name="Logged Entity")
        expected_id = str(uuid.uuid4())
        mock_database.insert.return_value = expected_id
        
        # Mock logger
        with patch.object(repo._logger, 'info') as mock_log:
            # Act
            await repo.create(entity)
            
            # Assert
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "Created test_table" in log_message
            assert expected_id in log_message
    
    @pytest.mark.asyncio
    async def test_create_entity_logs_error(self, mock_database):
        """
        RED: Test that entity creation errors are logged
        Should log errors with details and re-raise exception
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity = MockEntity(name="Error Entity")
        mock_database.insert.side_effect = Exception("Database error")
        
        # Mock logger
        with patch.object(repo._logger, 'error') as mock_log:
            # Act & Assert
            with pytest.raises(Exception):
                await repo.create(entity)
            
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "Error creating test_table" in log_message
    
    @pytest.mark.asyncio
    async def test_update_entity_logs_success(self, mock_database):
        """
        RED: Test that successful entity updates are logged
        Should log successful updates
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        entity = MockEntity(id=entity_id, name="Updated Entity")
        mock_database.update.return_value = True
        
        # Mock logger
        with patch.object(repo._logger, 'info') as mock_log:
            # Act
            await repo.update(entity_id, entity)
            
            # Assert
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "Updated test_table" in log_message
            assert entity_id in log_message
    
    @pytest.mark.asyncio
    async def test_delete_entity_logs_success(self, mock_database):
        """
        RED: Test that successful entity deletions are logged
        Should log successful deletions
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        mock_database.delete.return_value = True
        
        # Mock logger
        with patch.object(repo._logger, 'info') as mock_log:
            # Act
            await repo.delete(entity_id)
            
            # Assert
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "Deleted test_table" in log_message
            assert entity_id in log_message
    
    @pytest.mark.asyncio
    async def test_get_by_id_logs_error_on_exception(self, mock_database):
        """
        RED: Test that get_by_id errors are logged and re-raised
        Should log database errors and propagate them
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "test_table")
        entity_id = str(uuid.uuid4())
        mock_database.get_by_id.side_effect = Exception("Database connection lost")
        
        # Mock logger
        with patch.object(repo._logger, 'error') as mock_log:
            # Act & Assert
            with pytest.raises(Exception):
                await repo.get_by_id(entity_id)
            
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "Error getting test_table by ID" in log_message
            assert entity_id in log_message


class TestBaseRepositoryIntegration:
    """Integration tests for BaseRepository with real entities"""
    
    @pytest.mark.asyncio
    async def test_repository_with_plot_entity(self, mock_database, sample_plot_data):
        """
        RED: Test repository operations with Plot entity
        Should handle Plot entity serialization and deserialization
        """
        # This test would be implemented once we have the actual Plot repository
        # For now, we establish the pattern that will be used
        pass
    
    @pytest.mark.asyncio
    async def test_repository_batch_operations(self, mock_database):
        """
        RED: Test repository with multiple entities in sequence
        Should handle multiple CRUD operations correctly
        """
        # Arrange
        repo = ConcreteTestRepository(mock_database, "batch_table")
        entities = [
            MockEntity(name="Entity 1"),
            MockEntity(name="Entity 2"),
            MockEntity(name="Entity 3")
        ]
        
        # Mock database responses
        mock_database.insert.side_effect = ["id1", "id2", "id3"]
        mock_database.get_by_id.side_effect = [
            {"id": "id1", "name": "Entity 1", "created_at": datetime.now().isoformat()},
            {"id": "id2", "name": "Entity 2", "created_at": datetime.now().isoformat()},
            {"id": "id3", "name": "Entity 3", "created_at": datetime.now().isoformat()}
        ]
        
        # Act - Create entities
        created_ids = []
        for entity in entities:
            entity_id = await repo.create(entity)
            created_ids.append(entity_id)
        
        # Act - Retrieve entities
        retrieved_entities = []
        for entity_id in created_ids:
            entity = await repo.get_by_id(entity_id)
            retrieved_entities.append(entity)
        
        # Assert
        assert len(created_ids) == 3
        assert len(retrieved_entities) == 3
        assert mock_database.insert.call_count == 3
        assert mock_database.get_by_id.call_count == 3
        
        for i, entity in enumerate(retrieved_entities):
            assert entity.name == f"Entity {i + 1}"