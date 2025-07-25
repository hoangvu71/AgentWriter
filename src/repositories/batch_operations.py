"""
Batch operations to reduce N+1 query problems in repositories.
Provides efficient methods for bulk data operations.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod
from ..core.interfaces import IDatabase
from ..core.logging import get_logger

T = TypeVar('T')


class BatchOperationsMixin:
    """Mixin class to add batch operations to repositories"""
    
    def __init__(self, database: IDatabase, table_name: str):
        self._database = database
        self._table_name = table_name
        self._logger = get_logger(f"{self.__class__.__name__}")
    
    async def batch_get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple entities by their IDs in a single query"""
        if not ids:
            return []
        
        try:
            # Use database batch select if available
            if hasattr(self._database, 'batch_select_by_ids'):
                return await self._database.batch_select_by_ids(self._table_name, ids)
            
            # Fallback to individual queries
            results = []
            for id in ids:
                entity = await self._database.get_by_id(self._table_name, id)
                if entity:
                    results.append(entity)
            return results
            
        except Exception as e:
            self._logger.error(f"Error in batch get by IDs: {e}")
            raise
    
    async def batch_create(self, entities: List[T]) -> List[str]:
        """Create multiple entities in a single transaction"""
        if not entities:
            return []
        
        try:
            # Serialize entities
            serialized_entities = []
            for entity in entities:
                if hasattr(self, '_serialize'):
                    serialized_entities.append(self._serialize(entity))
                else:
                    # Fallback to entity as dict
                    serialized_entities.append(entity.__dict__ if hasattr(entity, '__dict__') else entity)
            
            # Use database batch insert if available
            if hasattr(self._database, 'batch_insert'):
                return await self._database.batch_insert(self._table_name, serialized_entities)
            
            # Fallback to individual inserts
            ids = []
            for entity_data in serialized_entities:
                id = await self._database.insert(self._table_name, entity_data)
                ids.append(id)
            return ids
            
        except Exception as e:
            self._logger.error(f"Error in batch create: {e}")
            raise
    
    async def batch_update_by_criteria(self, criteria: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update multiple entities matching criteria"""
        try:
            # First get all entities matching criteria
            entities = await self._database.search(self._table_name, criteria, limit=1000)
            if not entities:
                return 0
            
            # Prepare batch updates
            batch_updates = []
            for entity in entities:
                batch_updates.append({
                    'id': entity['id'],
                    'data': updates
                })
            
            # Use database batch update if available
            if hasattr(self._database, 'batch_update'):
                return await self._database.batch_update(self._table_name, batch_updates)
            
            # Fallback to individual updates
            updated_count = 0
            for entity in entities:
                success = await self._database.update(self._table_name, entity['id'], updates)
                if success:
                    updated_count += 1
            return updated_count
            
        except Exception as e:
            self._logger.error(f"Error in batch update by criteria: {e}")
            raise
    
    async def get_with_related_data(self, entity_id: str, related_tables: List[str]) -> Dict[str, Any]:
        """Get an entity with its related data in a single operation to avoid N+1"""
        try:
            # Get the main entity
            entity = await self._database.get_by_id(self._table_name, entity_id)
            if not entity:
                return {}
            
            # Get related data
            for related_table in related_tables:
                # Common foreign key patterns
                foreign_key_patterns = [
                    f"{self._table_name[:-1]}_id",  # plots -> plot_id
                    f"{self._table_name}_id",       # plots -> plots_id
                    "parent_id",
                    "owner_id",
                    "user_id"
                ]
                
                for fk_pattern in foreign_key_patterns:
                    related_data = await self._database.search(
                        related_table, 
                        {fk_pattern: entity_id}, 
                        limit=100
                    )
                    if related_data:
                        entity[f"{related_table}"] = related_data
                        break
            
            return entity
            
        except Exception as e:
            self._logger.error(f"Error getting entity with related data: {e}")
            raise
    
    async def get_multiple_with_related_data(self, entity_ids: List[str], related_tables: List[str]) -> List[Dict[str, Any]]:
        """Get multiple entities with their related data efficiently"""
        if not entity_ids:
            return []
        
        try:
            # Get all main entities in one query
            entities = await self.batch_get_by_ids(entity_ids)
            if not entities:
                return []
            
            # Create entity lookup map
            entity_map = {entity['id']: entity for entity in entities}
            
            # Get related data for all entities at once
            for related_table in related_tables:
                foreign_key_patterns = [
                    f"{self._table_name[:-1]}_id",
                    f"{self._table_name}_id",
                    "parent_id",
                    "owner_id",
                    "user_id"
                ]
                
                for fk_pattern in foreign_key_patterns:
                    # Get all related records in one query
                    all_related = []
                    for entity_id in entity_ids:
                        related_data = await self._database.search(
                            related_table,
                            {fk_pattern: entity_id},
                            limit=100
                        )
                        for record in related_data:
                            record['parent_entity_id'] = entity_id
                            all_related.append(record)
                    
                    # Group related data by parent entity
                    if all_related:
                        for record in all_related:
                            parent_id = record.get('parent_entity_id')
                            if parent_id in entity_map:
                                if related_table not in entity_map[parent_id]:
                                    entity_map[parent_id][related_table] = []
                                entity_map[parent_id][related_table].append(record)
                        break
            
            return list(entity_map.values())
            
        except Exception as e:
            self._logger.error(f"Error getting multiple entities with related data: {e}")
            raise
    
    async def search_with_pagination_and_related(
        self, 
        criteria: Dict[str, Any], 
        related_tables: List[str] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search entities with pagination and optional related data"""
        try:
            # Get total count
            total_count = await self._database.count(self._table_name, criteria)
            
            # Get entities with limit and offset
            entities = await self._database.search(self._table_name, criteria, limit=limit)
            
            # Skip entities based on offset (if database doesn't support it natively)
            if offset > 0:
                entities = entities[offset:]
            
            # Get related data if requested
            if related_tables and entities:
                entity_ids = [entity['id'] for entity in entities]
                entities_with_related = await self.get_multiple_with_related_data(entity_ids, related_tables)
                entities = entities_with_related
            
            return {
                'data': entities,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(entities)) < total_count
            }
            
        except Exception as e:
            self._logger.error(f"Error in search with pagination and related data: {e}")
            raise


class OptimizedPlotRepository:
    """Plot repository with optimized batch operations"""
    
    def __init__(self, database: IDatabase):
        self.batch_ops = BatchOperationsMixin(database, "plots")
        self._database = database
        self._logger = get_logger("OptimizedPlotRepository")
    
    async def get_user_plots_with_authors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's plots with their authors in an optimized way"""
        try:
            # Get all plots for user
            plots = await self._database.search("plots", {"user_id": user_id}, limit=limit)
            if not plots:
                return []
            
            # Get unique author IDs from plots
            author_ids = list(set([plot.get("author_id") for plot in plots if plot.get("author_id")]))
            
            # Batch get all authors
            authors = []
            if author_ids:
                authors = await self.batch_ops.batch_get_by_ids(author_ids)
            
            # Create author lookup map
            author_map = {author['id']: author for author in authors}
            
            # Attach authors to plots
            for plot in plots:
                author_id = plot.get("author_id")
                if author_id and author_id in author_map:
                    plot['author'] = author_map[author_id]
            
            return plots
            
        except Exception as e:
            self._logger.error(f"Error getting user plots with authors: {e}")
            raise
    
    async def get_session_content_batch(self, session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all session content (plots, authors, world building, characters) in batch"""
        try:
            # Get all content for session in parallel
            import asyncio
            
            plots_task = self._database.search("plots", {"session_id": session_id}, limit=100)
            authors_task = self._database.search("authors", {"session_id": session_id}, limit=100)
            worlds_task = self._database.search("world_building", {"session_id": session_id}, limit=100)
            characters_task = self._database.search("characters", {"session_id": session_id}, limit=100)
            
            plots, authors, worlds, characters = await asyncio.gather(
                plots_task, authors_task, worlds_task, characters_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            result = {
                "plots": plots if not isinstance(plots, Exception) else [],
                "authors": authors if not isinstance(authors, Exception) else [],
                "world_building": worlds if not isinstance(worlds, Exception) else [],
                "characters": characters if not isinstance(characters, Exception) else []
            }
            
            return result
            
        except Exception as e:
            self._logger.error(f"Error getting session content batch: {e}")
            raise


class OptimizedAuthorRepository:
    """Author repository with optimized batch operations"""
    
    def __init__(self, database: IDatabase):
        self.batch_ops = BatchOperationsMixin(database, "authors")
        self._database = database
        self._logger = get_logger("OptimizedAuthorRepository")
    
    async def get_authors_with_plot_counts(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get authors with their plot counts efficiently"""
        try:
            # Get all authors for user
            authors = await self._database.search("authors", {"user_id": user_id}, limit=limit)
            if not authors:
                return []
            
            # Get plot counts for all authors in batch
            author_ids = [author['id'] for author in authors]
            
            # Count plots for each author
            for author in authors:
                plot_count = await self._database.count("plots", {"author_id": author['id']})
                author['plot_count'] = plot_count
            
            return authors
            
        except Exception as e:
            self._logger.error(f"Error getting authors with plot counts: {e}")
            raise


class OptimizedCharactersRepository:
    """Characters repository with optimized batch operations"""
    
    def __init__(self, database: IDatabase):
        self.batch_ops = BatchOperationsMixin(database, "characters")
        self._database = database
        self._logger = get_logger("OptimizedCharactersRepository")
    
    async def get_characters_with_world_context(self, plot_ids: List[str]) -> List[Dict[str, Any]]:
        """Get characters with their world building context efficiently"""
        try:
            if not plot_ids:
                return []
            
            # Get all characters for the plots
            all_characters = []
            for plot_id in plot_ids:
                characters = await self._database.search("characters", {"plot_id": plot_id}, limit=100)
                all_characters.extend(characters)
            
            if not all_characters:
                return []
            
            # Get unique world IDs
            world_ids = list(set([char.get("world_id") for char in all_characters if char.get("world_id")]))
            
            # Batch get world building data
            worlds = []
            if world_ids:
                worlds = await self.batch_ops.batch_get_by_ids(world_ids)
            
            # Create world lookup map
            world_map = {world['id']: world for world in worlds}
            
            # Attach world context to characters
            for character in all_characters:
                world_id = character.get("world_id")
                if world_id and world_id in world_map:
                    character['world_context'] = world_map[world_id]
            
            return all_characters
            
        except Exception as e:
            self._logger.error(f"Error getting characters with world context: {e}")
            raise