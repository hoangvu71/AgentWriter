"""
Open-WebUI Pipe Function for BooksWriter Integration
This function acts as a bridge between Open-WebUI and the BooksWriter multi-agent system
"""

from typing import List, Union, Generator, Iterator, Dict, Any
from pydantic import BaseModel
import aiohttp
import json
import asyncio


class Pipe:
    """
    BooksWriter Pipe - Integrates with the multi-agent book writing system
    """
    
    def __init__(self):
        self.type = "pipe"
        self.id = "books_writer"
        self.name = "BooksWriter Assistant"
        self.description = "Professional multi-agent system for creative book writing"
        self.version = "1.0.0"
        self.author = "BooksWriter Team"
        
        # Backend configuration
        self.backend_url = "http://host.docker.internal:8000"
        self.ws_url = "ws://host.docker.internal:8000/ws"
        
        # Available functions in the UI
        self.functions = {
            "plot": "Generate a book plot",
            "author": "Create an author profile", 
            "world": "Build a fictional world",
            "characters": "Develop characters",
            "critique": "Get critique on content",
            "enhance": "Enhance existing content",
            "full": "Complete book writing workflow"
        }

    class Valves(BaseModel):
        """Configuration for the pipe"""
        BOOKS_WRITER_API_URL: str = "http://host.docker.internal:8000"
        BOOKS_WRITER_WS_URL: str = "ws://host.docker.internal:8000/ws"
        DEFAULT_USER_ID: str = "openwebui-user"
        SESSION_PREFIX: str = "openwebui-session"
        ENABLE_STREAMING: bool = True
        REQUEST_TIMEOUT: int = 300  # 5 minutes for long operations

    def __init__(self):
        self.type = "pipe"
        self.valves = self.Valves()

    def get_function_description(self) -> str:
        """Returns a description of available functions"""
        return """
Available BooksWriter commands:
- `/plot [description]` - Generate a book plot
- `/author [genre]` - Create an author profile
- `/world [plot_id]` - Build a fictional world
- `/characters [plot_id] [world_id]` - Develop characters
- `/critique [content]` - Get critique on content
- `/enhance [content]` - Enhance existing content
- `/workflow [description]` - Run complete book writing workflow

You can also just describe what you want and I'll help you create it!
"""

    async def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipe function that processes messages and interacts with BooksWriter backend
        """
        
        # Extract user preferences from body
        user_id = body.get("user", {}).get("id", self.valves.DEFAULT_USER_ID)
        session_id = f"{self.valves.SESSION_PREFIX}-{user_id}-{int(asyncio.get_event_loop().time())}"
        
        try:
            # Parse command or infer intent
            command, content = self._parse_command(user_message)
            
            if command == "help":
                return self.get_function_description()
            
            # Determine the appropriate workflow
            workflow_message = self._build_workflow_message(command, content, messages)
            
            if self.valves.ENABLE_STREAMING:
                # Stream responses from WebSocket
                return self._stream_response(workflow_message, session_id, user_id)
            else:
                # Get complete response
                return await self._get_complete_response(workflow_message, session_id, user_id)
                
        except Exception as e:
            return f"Error: Failed to process request - {str(e)}"

    def _parse_command(self, message: str) -> tuple[str, str]:
        """Parse user message to extract command and content"""
        message = message.strip()
        
        # Check for explicit commands
        if message.startswith("/"):
            parts = message.split(" ", 1)
            command = parts[0][1:].lower()  # Remove / and lowercase
            content = parts[1] if len(parts) > 1 else ""
            
            # Map commands to agent names
            command_map = {
                "plot": "plot",
                "author": "author",
                "world": "world",
                "characters": "characters",
                "critique": "critique",
                "enhance": "enhance",
                "workflow": "full",
                "help": "help"
            }
            
            return command_map.get(command, "full"), content
        
        # Infer intent from natural language
        lower_message = message.lower()
        if any(word in lower_message for word in ["plot", "story idea", "premise"]):
            return "plot", message
        elif any(word in lower_message for word in ["author", "writer profile", "pen name"]):
            return "author", message
        elif any(word in lower_message for word in ["world", "setting", "universe"]):
            return "world", message
        elif any(word in lower_message for word in ["character", "protagonist", "hero"]):
            return "characters", message
        elif any(word in lower_message for word in ["critique", "feedback", "review"]):
            return "critique", message
        elif any(word in lower_message for word in ["enhance", "improve", "better"]):
            return "enhance", message
        
        # Default to full workflow
        return "full", message

    def _build_workflow_message(self, command: str, content: str, messages: List[dict]) -> dict:
        """Build the message to send to BooksWriter backend"""
        
        # Extract context from previous messages if needed
        context = self._extract_context_from_messages(messages)
        
        # Build request based on command
        if command == "full":
            # Full workflow - let orchestrator handle it
            request_content = content or "Create a complete book concept"
        elif command == "plot":
            request_content = f"Generate a book plot: {content}"
        elif command == "author":
            request_content = f"Create an author profile for: {content}"
        elif command == "world":
            request_content = f"Build a fictional world based on: {content}"
            if context.get("plot_id"):
                request_content += f" (Using plot: {context['plot_id']})"
        elif command == "characters":
            request_content = f"Develop characters: {content}"
            if context.get("plot_id"):
                request_content += f" (Plot: {context['plot_id']})"
            if context.get("world_id"):
                request_content += f" (World: {context['world_id']})"
        elif command == "critique":
            request_content = f"Critique this content: {content}"
        elif command == "enhance":
            request_content = f"Enhance this content: {content}"
        else:
            request_content = content
        
        return {
            "type": "message",
            "content": request_content,
            "context": context
        }

    def _extract_context_from_messages(self, messages: List[dict]) -> dict:
        """Extract relevant context (plot_id, world_id, etc.) from message history"""
        context = {}
        
        # Look for IDs in previous assistant messages
        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                
                # Simple pattern matching for IDs
                if "plot_id:" in content:
                    try:
                        plot_id = content.split("plot_id:")[1].split()[0].strip()
                        context["plot_id"] = plot_id
                    except:
                        pass
                
                if "world_id:" in content:
                    try:
                        world_id = content.split("world_id:")[1].split()[0].strip()
                        context["world_id"] = world_id
                    except:
                        pass
                
                if "author_id:" in content:
                    try:
                        author_id = content.split("author_id:")[1].split()[0].strip()
                        context["author_id"] = author_id
                    except:
                        pass
        
        return context

    async def _stream_response(self, message: dict, session_id: str, user_id: str) -> Generator:
        """Stream responses from WebSocket connection"""
        import websockets
        
        ws_url = f"{self.valves.BOOKS_WRITER_WS_URL}/{session_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                # Send message
                await websocket.send(json.dumps({
                    **message,
                    "user_id": user_id,
                    "session_id": session_id
                }))
                
                # Stream responses
                while True:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=self.valves.REQUEST_TIMEOUT
                        )
                        data = json.loads(response)
                        
                        if data.get("type") == "stream_chunk":
                            yield data.get("content", "")
                        elif data.get("type") == "stream_end":
                            break
                        elif data.get("type") == "error":
                            yield f"\n\nError: {data.get('error', 'Unknown error')}"
                            break
                        elif data.get("type") == "workflow_complete":
                            # Add summary of completed operations
                            summary = data.get("summary", {})
                            if summary:
                                yield f"\n\n✅ Workflow completed: {summary.get('successful', 0)} successful operations"
                            break
                            
                    except asyncio.TimeoutError:
                        yield "\n\nError: Request timed out"
                        break
                    
        except Exception as e:
            yield f"\n\nError: WebSocket connection failed - {str(e)}"

    async def _get_complete_response(self, message: dict, session_id: str, user_id: str) -> str:
        """Get complete response without streaming"""
        responses = []
        
        async for chunk in self._stream_response(message, session_id, user_id):
            responses.append(chunk)
        
        return "".join(responses)