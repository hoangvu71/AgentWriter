"""
Conversation continuity manager leveraging ADK's persistent session and memory services.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .logging import get_logger
from .adk_services import ADKServiceFactory, ServiceMode

logger = get_logger("conversation_manager")


class ConversationManager:
    """Manages conversation continuity and memory across sessions"""
    
    def __init__(self, adk_factory: ADKServiceFactory):
        self.adk_factory = adk_factory
        self.session_service = adk_factory.create_session_service() 
        self.memory_service = adk_factory.create_memory_service()
        self.is_persistent = adk_factory.service_mode != ServiceMode.DEVELOPMENT
        
        logger.info(f"ConversationManager initialized (persistent: {self.is_persistent})")
    
    async def get_conversation_context(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get conversation context for continuing previous conversations"""
        
        if not self.is_persistent:
            logger.debug("Non-persistent mode, no conversation context available")
            return {}
        
        try:
            # Get recent session history
            session_history = await self._get_session_history(session_id, user_id)
            
            # Get relevant memories
            user_memories = await self._get_user_memories(user_id)
            
            # Get user preferences from previous interactions
            user_preferences = await self._get_user_preferences(user_id)
            
            context = {
                "has_conversation_history": len(session_history) > 0,
                "recent_interactions": session_history,
                "user_memories": user_memories,
                "user_preferences": user_preferences,
                "context_summary": self._generate_context_summary(session_history, user_memories)
            }
            
            logger.info(f"Retrieved conversation context for user {user_id}: {len(session_history)} interactions, {len(user_memories)} memories")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {e}")
            return {}
    
    async def save_interaction_to_memory(self, session_id: str, user_id: str, 
                                       interaction_data: Dict[str, Any]) -> bool:
        """Save important interaction data to long-term memory"""
        
        if not self.is_persistent:
            logger.debug("Non-persistent mode, skipping memory save")
            return False
        
        try:
            # Create memory entry from interaction
            memory_entry = {
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "interaction_type": interaction_data.get("type", "general"),
                "content_summary": interaction_data.get("summary", ""),
                "key_entities": interaction_data.get("entities", []),
                "user_preferences": interaction_data.get("preferences", {}),
                "generated_content": interaction_data.get("generated_content", {})
            }
            
            # Save to memory service
            if hasattr(self.memory_service, 'add_memory'):
                await self.memory_service.add_memory(
                    content=memory_entry["content_summary"],
                    metadata=memory_entry
                )
            elif hasattr(self.memory_service, 'store'):
                await self.memory_service.store(
                    content=memory_entry["content_summary"],
                    metadata=memory_entry
                )
            else:
                logger.debug("Memory service doesn't support storing, skipping save")
            
            logger.info(f"Saved interaction to memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving interaction to memory: {e}")
            return False
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences based on interactions"""
        
        if not self.is_persistent:
            return False
        
        try:
            # Store preferences in user-scoped state
            preference_key = f"user:{user_id}:preferences"
            
            # This would be handled by the session service's state management
            # For now, we'll save to memory service with special metadata
            await self.memory_service.add_memory(
                content=f"User preferences for {user_id}",
                metadata={
                    "type": "user_preferences",
                    "user_id": user_id,
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    async def _get_session_history(self, session_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent session history"""
        try:
            # Query memory service for recent interactions
            if hasattr(self.memory_service, 'search'):
                memories = await self.memory_service.search(
                    query=f"session:{session_id} user:{user_id}",
                    limit=limit
                )
            elif hasattr(self.memory_service, 'query'):
                # Alternative API
                memories = await self.memory_service.query(
                    f"session:{session_id} user:{user_id}",
                    limit=limit
                )
            else:
                # In-memory service fallback
                logger.debug("Memory service doesn't support search, returning empty history")
                return []
            
            return [self._format_memory_as_interaction(memory) for memory in memories]
            
        except Exception as e:
            logger.error(f"Error retrieving session history: {e}")
            return []
    
    async def _get_user_memories(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's relevant memories"""
        try:
            if hasattr(self.memory_service, 'search'):
                memories = await self.memory_service.search(
                    query=f"user:{user_id}",
                    limit=limit
                )
            elif hasattr(self.memory_service, 'query'):
                memories = await self.memory_service.query(
                    f"user:{user_id}",
                    limit=limit
                )
            else:
                logger.debug("Memory service doesn't support search, returning empty memories")
                return []
            
            return [self._format_memory_as_context(memory) for memory in memories]
            
        except Exception as e:
            logger.error(f"Error retrieving user memories: {e}")
            return []
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from memory"""
        try:
            if hasattr(self.memory_service, 'search'):
                preferences_memories = await self.memory_service.search(
                    query=f"user_preferences user:{user_id}",
                    limit=1
                )
            elif hasattr(self.memory_service, 'query'):
                preferences_memories = await self.memory_service.query(
                    f"user_preferences user:{user_id}",
                    limit=1
                )
            else:
                logger.debug("Memory service doesn't support search, returning empty preferences")
                return {}
            
            if preferences_memories:
                return preferences_memories[0].get("metadata", {}).get("preferences", {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {e}")
            return {}
    
    def _format_memory_as_interaction(self, memory) -> Dict[str, Any]:
        """Format memory entry as interaction data"""
        metadata = getattr(memory, 'metadata', {})
        return {
            "timestamp": metadata.get("timestamp", ""),
            "type": metadata.get("interaction_type", "general"),
            "summary": getattr(memory, 'content', ''),
            "entities": metadata.get("key_entities", [])
        }
    
    def _format_memory_as_context(self, memory) -> Dict[str, Any]:
        """Format memory entry as context data"""
        metadata = getattr(memory, 'metadata', {})
        return {
            "content": getattr(memory, 'content', ''),
            "type": metadata.get("type", "general"),
            "timestamp": metadata.get("timestamp", ""),
            "relevance_score": getattr(memory, 'score', 0.0)
        }
    
    def _generate_context_summary(self, session_history: List[Dict[str, Any]], 
                                user_memories: List[Dict[str, Any]]) -> str:
        """Generate a summary of conversation context"""
        
        if not session_history and not user_memories:
            return "This is a new conversation with no previous context."
        
        summary_parts = []
        
        if session_history:
            recent_count = len(session_history)
            summary_parts.append(f"User has {recent_count} recent interactions in this session.")
            
            # Extract key themes from recent interactions
            recent_types = [interaction.get("type", "general") for interaction in session_history[:3]]
            if recent_types:
                summary_parts.append(f"Recent activities: {', '.join(set(recent_types))}")
        
        if user_memories:
            memory_count = len(user_memories)
            summary_parts.append(f"User has {memory_count} relevant memories from previous sessions.")
        
        return " ".join(summary_parts)


async def get_conversation_manager(adk_factory: ADKServiceFactory) -> ConversationManager:
    """Get conversation manager instance"""
    return ConversationManager(adk_factory)