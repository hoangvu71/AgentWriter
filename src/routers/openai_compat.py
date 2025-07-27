"""
OpenAI-compatible API endpoints for Open-WebUI integration
This allows Open-WebUI to communicate with BooksWriter as if it were an OpenAI API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
import asyncio

from ..core.interfaces import AgentRequest
from ..core.logging import get_logger
from ..agents.agent_factory import AgentFactory
from ..core.container import container

logger = get_logger("openai_compat")

router = APIRouter(prefix="/openai/v1", tags=["OpenAI Compatibility"])


# OpenAI-compatible models
class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "books-writer"
    permission: List[Dict] = []
    root: str
    parent: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


def get_agent_factory():
    """Get AgentFactory from dependency injection"""
    try:
        return container.get(AgentFactory)
    except Exception as e:
        logger.error(f"Failed to get AgentFactory: {e}")
        raise HTTPException(status_code=500, detail="Agent service unavailable")


@router.get("/models")
async def list_models():
    """List available models in OpenAI-compatible format"""
    
    # Map BooksWriter agents to OpenAI-style models
    models_data = {
        "models": [
            Model(
                id="books-writer-orchestrator",
                created=1700000000,
                root="books-writer-orchestrator",
                owned_by="books-writer"
            ),
            Model(
                id="books-writer-plot",
                created=1700000000,
                root="books-writer-plot",
                owned_by="books-writer"
            ),
            Model(
                id="books-writer-author",
                created=1700000000,
                root="books-writer-author",
                owned_by="books-writer"
            ),
            Model(
                id="books-writer-world",
                created=1700000000,
                root="books-writer-world",
                owned_by="books-writer"
            ),
            Model(
                id="books-writer-characters",
                created=1700000000,
                root="books-writer-characters",
                owned_by="books-writer"
            ),
            Model(
                id="books-writer-critique",
                created=1700000000,
                root="books-writer-critique",
                owned_by="books-writer"
            ),
            Model(
                id="books-writer-enhance",
                created=1700000000,
                root="books-writer-enhance",
                owned_by="books-writer"
            )
        ]
    }
    
    return models_data


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model details"""
    
    # Map model IDs to agent names
    model_map = {
        "books-writer-orchestrator": "orchestrator",
        "books-writer-plot": "plot_generator",
        "books-writer-author": "author_generator",
        "books-writer-world": "world_building",
        "books-writer-characters": "characters",
        "books-writer-critique": "critique",
        "books-writer-enhance": "enhancement"
    }
    
    if model_id not in model_map:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    return Model(
        id=model_id,
        created=1700000000,
        root=model_id,
        owned_by="books-writer"
    )


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    agent_factory: AgentFactory = Depends(get_agent_factory)
):
    """
    Create a chat completion using BooksWriter agents
    Maps OpenAI chat format to BooksWriter agent system
    """
    
    try:
        # Extract the user's message
        user_message = ""
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Map model to agent
        model_agent_map = {
            "books-writer-orchestrator": "orchestrator",
            "books-writer-plot": "plot_generator",
            "books-writer-author": "author_generator",
            "books-writer-world": "world_building",
            "books-writer-characters": "characters",
            "books-writer-critique": "critique",
            "books-writer-enhance": "enhancement"
        }
        
        agent_name = model_agent_map.get(request.model, "orchestrator")
        
        # Create agent request
        agent_request = AgentRequest(
            content=user_message,
            user_id=request.user or "openwebui-user",
            session_id=f"openwebui-{uuid.uuid4()}",
            context={}
        )
        
        # Process with agent
        agent = agent_factory.create_agent(agent_name)
        
        if request.stream:
            # Return streaming response
            return await create_streaming_response(agent, agent_request, request)
        else:
            # Get complete response
            response = await agent.process_request(agent_request)
            
            # Format as OpenAI response
            completion_id = f"chatcmpl-{uuid.uuid4()}"
            
            return ChatCompletionResponse(
                id=completion_id,
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=response.content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage={
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response.content.split()),
                    "total_tokens": len(user_message.split()) + len(response.content.split())
                }
            )
            
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def create_streaming_response(agent, agent_request, request):
    """Create a streaming response in OpenAI format"""
    
    async def generate():
        completion_id = f"chatcmpl-{uuid.uuid4()}"
        
        try:
            # Process request (assuming agent supports streaming)
            response = await agent.process_request(agent_request)
            
            # For now, simulate streaming by chunking the response
            # In a real implementation, agents would yield chunks
            content = response.content
            chunk_size = 20  # Words per chunk
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = " ".join(chunk_words)
                
                if i > 0:
                    chunk_content = " " + chunk_content
                
                chunk = ChatCompletionChunk(
                    id=completion_id,
                    created=int(datetime.now().timestamp()),
                    model=request.model,
                    choices=[{
                        "index": 0,
                        "delta": {
                            "role": "assistant" if i == 0 else None,
                            "content": chunk_content
                        },
                        "finish_reason": None
                    }]
                )
                
                yield f"data: {chunk.json()}\n\n"
                await asyncio.sleep(0.05)  # Simulate streaming delay
            
            # Send final chunk
            final_chunk = ChatCompletionChunk(
                id=completion_id,
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            )
            
            yield f"data: {final_chunk.json()}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "internal_error",
                    "code": "streaming_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/embeddings")
async def create_embeddings():
    """
    Placeholder for embeddings endpoint
    Could integrate with VertexRAGService if needed
    """
    raise HTTPException(
        status_code=501, 
        detail="Embeddings not implemented. Use BooksWriter RAG service directly."
    )