from typing import AsyncGenerator, Dict, Any
import os
import asyncio
import re
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load environment variables
load_dotenv()


class BookWriterAgent:
    """A sophisticated agent for book writing assistance with search capabilities"""
    
    # Available Google AI models
    AVAILABLE_MODELS = {
        "gemini-2.0-flash": {
            "name": "Gemini 2.0 Flash",
            "description": "Fast, efficient model optimized for speed and cost-effectiveness",
            "capabilities": ["Speed", "Tool Use", "1M token context"],
            "best_for": "General writing tasks, quick responses, real-time chat"
        },
        "gemini-2.5-flash": {
            "name": "Gemini 2.5 Flash", 
            "description": "Latest Flash model with thinking capabilities",
            "capabilities": ["Thinking", "Speed", "Large-scale processing"],
            "best_for": "Complex reasoning, agentic tasks, high-volume processing"
        },
        "gemini-2.5-pro-preview-03-25": {
            "name": "Gemini 2.5 Pro Preview",
            "description": "Most capable model with advanced reasoning",
            "capabilities": ["Advanced reasoning", "Thinking", "Complex tasks"],
            "best_for": "Research, complex writing projects, detailed analysis"
        },
        "gemini-1.5-pro": {
            "name": "Gemini 1.5 Pro",
            "description": "Stable production model with broad capabilities",
            "capabilities": ["Balanced performance", "Reliable", "Production-ready"],
            "best_for": "Production applications, consistent quality"
        },
        "gemini-1.5-flash": {
            "name": "Gemini 1.5 Flash",
            "description": "Previous generation Flash model",
            "capabilities": ["Speed", "Cost-effective", "Reliable"],
            "best_for": "Basic writing tasks, cost-sensitive applications"
        }
    }
    
    def __init__(self, app_name: str = "book_writer_app", model: str = "gemini-2.0-flash"):
        self.app_name = app_name
        self.current_model = model
        
        # Validate model
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not supported. Available models: {list(self.AVAILABLE_MODELS.keys())}")
        
        self.agent = Agent(
            name="book_writer_assistant",
            model=model,
            instruction="""You are a sophisticated book writing assistant with the following capabilities:
            
            1. SEARCH CAPABILITIES: Use Google Search to research topics, facts, and information
            2. MEMORY: Remember our conversation history and user preferences
            3. PLANNING: Break down complex writing tasks into manageable steps
            4. WRITING ASSISTANCE: Help with:
               - Plot development and story structure
               - Character development
               - Research for non-fiction writing
               - Grammar and style improvements
               - Chapter organization
               - Citation and fact-checking
            
            Always be helpful, creative, and maintain context from our conversation.
            When asked to search for information, use the search tool and provide accurate, well-sourced responses.
            Format your responses in a clean, readable way with proper line breaks and formatting.
            """,
            description="A book writing assistant with search, memory, and planning capabilities",
            tools=[google_search]
        )
        
        # Initialize runner
        self.runner = InMemoryRunner(self.agent, app_name=self.app_name)
        
        # Track sessions
        self.sessions: Dict[str, Any] = {}
    
    def _clean_response_text(self, text: str) -> str:
        """Clean and format response text for better readability"""
        if not text:
            return text
            
        # Remove any raw Part() or Content() formatting - more comprehensive patterns
        text = re.sub(r'parts=\[Part\(\s*text="""([^"]*?)"""\s*\)\]', r'\1', text)
        text = re.sub(r'parts=\[Part\(\s*text=\'([^\']*?)\'\s*\)\]', r'\1', text)
        text = re.sub(r'parts=\[Part\(\s*text="([^"]*?)"\s*\)\]', r'\1', text)
        
        # Handle Content() patterns with different quote types - more specific patterns first
        text = re.sub(r'Content\(parts=\[Part\(text="([^"]*?)"\)\], role=\'model\'\)', r'\1', text)
        text = re.sub(r'Content\(parts=\[Part\(text=\'([^\']*?)\'\)\], role=\'model\'\)', r'\1', text)
        
        # Handle simpler Content patterns without role
        text = re.sub(r'Content\(parts=\[Part\(text="([^"]*?)"\)\]\)', r'\1', text)
        text = re.sub(r'Content\(parts=\[Part\(text=\'([^\']*?)\'\)\]\)', r'\1', text)
        
        # Handle multiline parts patterns
        text = re.sub(r'parts=\[Part\(\s*text=\'([^\']*?)\'\s*\)\]', r'\1', text, flags=re.DOTALL)
        
        # Remove remaining Part() patterns
        text = re.sub(r'Part\(\s*text=\'([^\']*?)\'\s*\)', r'\1', text)
        text = re.sub(r'Part\(\s*text="([^"]*?)"\s*\)', r'\1', text)
        
        # Remove role and other metadata
        text = re.sub(r'role=\'model\'', '', text)
        
        # Clean up any remaining Content() patterns (but only after extracting text)
        text = re.sub(r'Content\([^)]*?\)', '', text)
        text = re.sub(r'Content\(.*?\)', '', text, flags=re.DOTALL)
        
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'^\s+|\s+$', '', text)  # Trim whitespace
        text = re.sub(r'^,\s*\)\s*$', '', text)  # Remove trailing comma and parentheses
        text = re.sub(r'^\s*\]\s*$', '', text)  # Remove trailing brackets
        
        return text
    
    async def create_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Create a new session for the user"""
        session = await self.runner.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "session": session,
            "created_at": asyncio.get_event_loop().time()
        }
        
        return session
    
    async def get_or_create_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            return await self.create_session(user_id, session_id)
        return self.sessions[session_id]["session"]
    
    async def chat(self, user_id: str, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Chat with the agent and yield response chunks"""
        # Ensure session exists
        await self.get_or_create_session(user_id, session_id)
        
        # Create message content
        content = types.Content(
            role='user', 
            parts=[types.Part(text=message)]
        )
        
        # Stream response
        try:
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                # Extract text content from events
                raw_text = None
                if hasattr(event, 'content') and event.content:
                    raw_text = str(event.content)
                elif hasattr(event, 'text') and event.text:
                    raw_text = event.text
                elif hasattr(event, 'delta') and event.delta:
                    raw_text = event.delta
                
                if raw_text:
                    # Clean and format the text
                    cleaned_text = self._clean_response_text(raw_text)
                    if cleaned_text:
                        yield cleaned_text
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def search_and_respond(self, user_id: str, session_id: str, query: str) -> AsyncGenerator[str, None]:
        """Perform search and respond with results"""
        search_message = f"Please search for: {query}"
        async for chunk in self.chat(user_id, session_id, search_message):
            yield chunk
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        return self.sessions.get(session_id, {})
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all active sessions"""
        return {
            sid: {
                "user_id": info["user_id"],
                "created_at": info["created_at"]
            }
            for sid, info in self.sessions.items()
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available AI models"""
        return self.AVAILABLE_MODELS
    
    def get_current_model(self) -> str:
        """Get the currently active model"""
        return self.current_model
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        return self.AVAILABLE_MODELS.get(model_id, {})
    
    def switch_model(self, model_id: str) -> bool:
        """Switch to a different AI model"""
        if model_id not in self.AVAILABLE_MODELS:
            return False
        
        try:
            # Create new agent with different model
            self.agent = Agent(
                name="book_writer_assistant",
                model=model_id,
                instruction="""You are a sophisticated book writing assistant with the following capabilities:
                
                1. SEARCH CAPABILITIES: Use Google Search to research topics, facts, and information
                2. MEMORY: Remember our conversation history and user preferences
                3. PLANNING: Break down complex writing tasks into manageable steps
                4. WRITING ASSISTANCE: Help with:
                   - Plot development and story structure
                   - Character development
                   - Research for non-fiction writing
                   - Grammar and style improvements
                   - Chapter organization
                   - Citation and fact-checking
                
                Always be helpful, creative, and maintain context from our conversation.
                When asked to search for information, use the search tool and provide accurate, well-sourced responses.
                Format your responses in a clean, readable way with proper line breaks and formatting.
                """,
                description="A book writing assistant with search, memory, and planning capabilities",
                tools=[google_search]
            )
            
            # Create new runner
            self.runner = InMemoryRunner(self.agent, app_name=self.app_name)
            
            # Update current model
            self.current_model = model_id
            
            return True
        except Exception as e:
            print(f"Error switching model: {e}")
            return False


# Global agent instance
book_agent = BookWriterAgent()