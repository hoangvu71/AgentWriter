"""
Core interfaces and abstract base classes for the multi-agent book writing system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator, Protocol
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ContentType(Enum):
    """Types of content that can be generated"""
    PLOT = "plot"
    AUTHOR = "author"
    WORLD_BUILDING = "world_building"
    CHARACTERS = "characters"
    CRITIQUE = "critique"
    ENHANCEMENT = "enhancement"
    SCORING = "scoring"


@dataclass
class AgentRequest:
    """Base request structure for all agents with structured context support"""
    content: str
    user_id: str
    session_id: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize context and timestamp if not provided"""
        if self.context is None:
            self.context = {}
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            from datetime import datetime
            self.timestamp = datetime.now()
    
    def has_context_parameters(self) -> bool:
        """Check if request has structured context parameters"""
        return bool(self.context and any(
            key in self.context for key in [
                'genre_hierarchy', 'story_elements', 'target_audience', 'content_selection'
            ]
        ))
    
    def get_context_types(self) -> List[str]:
        """Get list of context parameter types present in request"""
        if not self.context:
            return []
            
        types = []
        if 'genre_hierarchy' in self.context:
            types.append('genre')
        if 'story_elements' in self.context:
            types.append('story_elements')
        if 'target_audience' in self.context:
            types.append('audience')
        if 'content_selection' in self.context:
            types.append('content_improvement')
            
        return types


@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    agent_name: str
    content: str
    content_type: ContentType
    parsed_json: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None


@dataclass
class StreamChunk:
    """Streaming response chunk"""
    chunk: str
    agent_name: str
    is_complete: bool = False
    metadata: Optional[Dict[str, Any]] = None


class IAgent(ABC):
    """Interface for all agents in the system"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description and capabilities"""
        pass
    
    @abstractmethod
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process a request and return a response"""
        pass
    
    @abstractmethod
    async def process_request_streaming(self, request: AgentRequest) -> AsyncGenerator[StreamChunk, None]:
        """Process a request with streaming response"""
        pass


class IOrchestrator(ABC):
    """Interface for the orchestrator agent"""
    
    @abstractmethod
    async def route_request(self, request: AgentRequest) -> List[str]:
        """Determine which agents should handle the request"""
        pass
    
    @abstractmethod
    async def coordinate_workflow(self, request: AgentRequest, agent_names: List[str]) -> AgentResponse:
        """Coordinate execution across multiple agents"""
        pass


class IDatabase(ABC):
    """Interface for database operations"""
    
    @abstractmethod
    async def save_plot(self, plot_data: Dict[str, Any]) -> str:
        """Save plot data and return ID"""
        pass
    
    @abstractmethod
    async def save_author(self, author_data: Dict[str, Any]) -> str:
        """Save author data and return ID"""
        pass
    
    @abstractmethod
    async def get_plot(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve plot by ID"""
        pass
    
    @abstractmethod
    async def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve author by ID"""
        pass
    
    @abstractmethod
    async def search_content(self, query: str, content_type: ContentType, user_id: str) -> List[Dict[str, Any]]:
        """Search for content"""
        pass


class IConnectionManager(ABC):
    """Interface for WebSocket connection management"""
    
    @abstractmethod
    async def connect(self, websocket: Any, client_id: str) -> None:
        """Connect a new WebSocket client"""
        pass
    
    @abstractmethod
    def disconnect(self, client_id: str) -> None:
        """Disconnect a WebSocket client"""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, client_id: str) -> None:
        """Send message to specific client"""
        pass
    
    @abstractmethod
    async def send_json(self, data: Dict[str, Any], client_id: str) -> None:
        """Send JSON data to specific client"""
        pass


class IConfiguration(Protocol):
    """Interface for configuration management"""
    
    @property
    def model_name(self) -> str:
        """Current AI model name"""
        ...
    
    @property
    def database_url(self) -> str:
        """Database connection URL"""
        ...
    
    @property
    def supabase_config(self) -> Dict[str, str]:
        """Supabase configuration"""
        ...
    
    @property
    def google_cloud_config(self) -> Dict[str, str]:
        """Google Cloud configuration"""
        ...


class IValidator(ABC):
    """Interface for input validation"""
    
    @abstractmethod
    def validate_uuid(self, value: str) -> str:
        """Validate and return UUID"""
        pass
    
    @abstractmethod
    def validate_text(self, value: str, max_length: int = 1000) -> str:
        """Validate and sanitize text input"""
        pass
    
    @abstractmethod
    def validate_request(self, request: AgentRequest) -> AgentRequest:
        """Validate an agent request"""
        pass


class ILogger(ABC):
    """Interface for logging operations"""
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        pass
    
    @abstractmethod
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message"""
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        pass


class IAgentFactory(ABC):
    """Interface for creating agents"""
    
    @abstractmethod
    def create_agent(self, agent_type: str, config: IConfiguration) -> IAgent:
        """Create an agent of the specified type"""
        pass
    
    @abstractmethod
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        pass