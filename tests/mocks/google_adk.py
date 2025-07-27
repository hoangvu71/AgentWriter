"""
Mock implementations for Google ADK modules to enable testing without dependencies.
"""
import asyncio
from typing import Any, Dict, Optional, List
from unittest.mock import MagicMock
import uuid


class MockInMemorySessionService:
    """Mock implementation of Google ADK InMemorySessionService"""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, session_id: str = None) -> str:
        if session_id is None:
            session_id = str(uuid.uuid4())
        self.sessions[session_id] = {}
        return session_id
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self.sessions.get(session_id, {})
    
    def update_session(self, session_id: str, data: Dict[str, Any]):
        if session_id in self.sessions:
            self.sessions[session_id].update(data)
    
    def delete_session(self, session_id: str):
        self.sessions.pop(session_id, None)


class MockInMemoryMemoryService:
    """Mock implementation of Google ADK InMemoryMemoryService"""
    
    def __init__(self):
        self.memories = {}
    
    def store_memory(self, session_id: str, memory: Dict[str, Any]):
        if session_id not in self.memories:
            self.memories[session_id] = []
        self.memories[session_id].append(memory)
    
    def get_memories(self, session_id: str) -> List[Dict[str, Any]]:
        return self.memories.get(session_id, [])
    
    def clear_memories(self, session_id: str):
        self.memories.pop(session_id, None)


class MockInMemoryRunner:
    """Mock implementation of Google ADK InMemoryRunner"""
    
    def __init__(self, agent, app_name: str = "test_app"):
        self.agent = agent
        self.app_name = app_name
        self.session_service = MockInMemorySessionService()
        self.memory_service = MockInMemoryMemoryService()
        self._running = False
    
    async def start(self):
        """Start the runner"""
        self._running = True
    
    async def stop(self):
        """Stop the runner"""
        self._running = False
    
    async def run(self, message: str, session_id: str = None) -> str:
        """Run a message through the agent"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Mock agent processing
        if hasattr(self.agent, '_prepare_message'):
            if asyncio.iscoroutinefunction(self.agent._prepare_message):
                prepared = await self.agent._prepare_message(message)
            else:
                prepared = self.agent._prepare_message(message)
            return f"Processed: {prepared}"
        
        return f"Processed: {message}"
    
    @property
    def is_running(self) -> bool:
        return self._running


class MockRunner(MockInMemoryRunner):
    """Mock implementation of Google ADK Runner with additional services"""
    
    def __init__(self, agent, session_service=None, memory_service=None, app_name: str = "test_app"):
        super().__init__(agent, app_name)
        if session_service:
            self.session_service = session_service
        if memory_service:
            self.memory_service = memory_service


class MockAgent:
    """Mock implementation of Google ADK Agent"""
    
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'MockAgent')
        self.instructions = kwargs.get('instructions', '')
        
    def run(self, *args, **kwargs):
        return MagicMock()
        
    async def run_async(self, *args, **kwargs):
        return MagicMock()


# Mock modules to replace google.adk imports
class MockGoogleADK:
    """Container for all Google ADK mocks"""
    
    class agents:
        Agent = MockAgent
    
    class sessions:
        InMemorySessionService = MockInMemorySessionService
        DatabaseSessionService = MockInMemorySessionService  # Fallback to in-memory
        VertexAiSessionService = MockInMemorySessionService  # Fallback to in-memory
    
    class memory:
        InMemoryMemoryService = MockInMemoryMemoryService
        DatabaseMemoryService = MockInMemoryMemoryService  # Fallback to in-memory
        VertexAiMemoryBankService = MockInMemoryMemoryService  # Fallback to in-memory
    
    class runners:
        InMemoryRunner = MockInMemoryRunner
        Runner = MockRunner


def install_mocks():
    """Install mocks into sys.modules for imports"""
    import sys
    
    # Create mock modules
    google_adk = MockGoogleADK()
    sys.modules['google.adk'] = google_adk
    sys.modules['google.adk.agents'] = google_adk.agents
    sys.modules['google.adk.sessions'] = google_adk.sessions
    sys.modules['google.adk.memory'] = google_adk.memory
    sys.modules['google.adk.runners'] = google_adk.runners

# Auto-install when module is imported (for backwards compatibility)
install_mocks()