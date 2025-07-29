# API Reference

This document provides comprehensive API reference for BooksWriter's REST endpoints and WebSocket interface.

## 🌐 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## 🔌 WebSocket Interface

### Connection Endpoint
```
WebSocket: /ws/{session_id}
```

**Parameters**:
- `session_id` (string): Unique session identifier

**Connection Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/my-session-123');

ws.onopen = function(event) {
    console.log('Connected to BooksWriter');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### Message Formats

#### Client to Server
```json
{
    "type": "message",
    "content": "Create a fantasy novel with strong female protagonist",
    "user_id": "user-123",
    "timestamp": "2025-01-28T10:30:00Z"
}
```

#### Server to Client
```json
{
    "type": "stream_chunk",
    "content": "I'll help you create a fantasy novel...",
    "agent": "OrchestratorAgent",
    "timestamp": "2025-01-28T10:30:01Z"
}
```

**Message Types**:
- `stream_chunk`: Streaming response content
- `agent_switch`: Agent coordination message
- `tool_execution`: Tool execution notification
- `error`: Error messages
- `completion`: Response completion notification

## 🔧 REST API Endpoints

### Health & Status

#### GET /health
**Purpose**: System health check with multi-agent system info
**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-01-28T10:30:00Z",
    "services": {
        "database": "connected",
        "agents": "operational",
        "models": "available"
    },
    "version": "1.0.0"
}
```

#### GET /models
**Purpose**: List available AI models and current selection
**Response**:
```json
{
    "models": [
        {
            "id": "gemini-2.0-flash-exp",
            "name": "Gemini 2.0 Flash Experimental",
            "description": "Latest model with enhanced capabilities",
            "active": true
        },
        {
            "id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "description": "Stable production model",
            "active": false
        }
    ],
    "current_model": "gemini-2.0-flash-exp"
}
```

#### GET /models/{model_id}
**Purpose**: Get detailed information about a specific model
**Parameters**:
- `model_id` (string): Model identifier
**Response**:
```json
{
    "id": "gemini-2.0-flash-exp",
    "name": "Gemini 2.0 Flash Experimental",
    "description": "Latest generation model with thinking capabilities",
    "capabilities": ["text_generation", "reasoning", "tool_use"],
    "context_window": 1048576,
    "max_output_tokens": 8192,
    "active": true
}
```

#### POST /models/{model_id}/switch
**Purpose**: Switch to a different AI model
**Parameters**:
- `model_id` (string): Target model identifier
**Response**:
```json
{
    "success": true,
    "previous_model": "gemini-1.5-pro",
    "current_model": "gemini-2.0-flash-exp",
    "message": "Model switched successfully"
}
```

### Session Management

#### GET /sessions
**Purpose**: List active sessions
**Response**:
```json
{
    "sessions": [
        {
            "session_id": "session-123",
            "user_id": "user-456",
            "created_at": "2025-01-28T10:00:00Z",
            "last_activity": "2025-01-28T10:30:00Z",
            "active": true
        }
    ],
    "total": 1
}
```

#### GET /sessions/{session_id}
**Purpose**: Get session information
**Parameters**:
- `session_id` (string): Session identifier
**Response**:
```json
{
    "session_id": "session-123",
    "user_id": "user-456",
    "created_at": "2025-01-28T10:00:00Z",
    "last_activity": "2025-01-28T10:30:00Z",
    "message_count": 15,
    "agents_used": ["OrchestratorAgent", "PlotGeneratorAgent", "AuthorGeneratorAgent"],
    "active": true
}
```

### Content Management

#### GET /api/plots
**Purpose**: List all plots with metadata and author information
**Query Parameters**:
- `user_id` (string, optional): Filter by user
- `genre` (string, optional): Filter by genre
- `limit` (integer, optional): Number of results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response**:
```json
{
    "plots": [
        {
            "id": "plot-uuid-123",
            "title": "The Dragon's Last Stand",
            "plot_summary": "A young warrior must unite the divided kingdoms...",
            "genre": "fantasy",
            "subgenre": "epic_fantasy",
            "tone": "heroic",
            "created_at": "2025-01-28T10:00:00Z",
            "author": {
                "id": "author-uuid-456",
                "author_name": "Sarah Mitchell",
                "pen_name": "S.M. Mitchell"
            }
        }
    ],
    "total": 10,
    "limit": 50,
    "offset": 0
}
```

#### GET /api/plots/{plot_id}
**Purpose**: Get detailed plot information
**Parameters**:
- `plot_id` (string): Plot UUID
**Response**:
```json
{
    "id": "plot-uuid-123",
    "title": "The Dragon's Last Stand",
    "plot_summary": "A young warrior must unite the divided kingdoms to face an ancient evil that threatens to consume the world. Through trials of courage, wisdom, and sacrifice, she discovers that true strength comes not from power, but from the bonds formed with those who share her cause.",
    "genre": "fantasy",
    "subgenre": "epic_fantasy",
    "microgenre": "dragon_fantasy",
    "trope": "chosen_one",
    "tone": "heroic",
    "target_audience": {
        "age_range": "young_adult",
        "interests": ["adventure", "magic", "strong_female_leads"]
    },
    "created_at": "2025-01-28T10:00:00Z",
    "updated_at": "2025-01-28T10:00:00Z",
    "user_id": "user-456",
    "session_id": "session-123"
}
```

#### GET /api/authors
**Purpose**: List all authors with plot counts and relationships
**Query Parameters**:
- `user_id` (string, optional): Filter by user
- `limit` (integer, optional): Number of results (default: 50)
- `offset` (integer, optional): Pagination offset (default: 0)

**Response**:
```json
{
    "authors": [
        {
            "id": "author-uuid-456",
            "author_name": "Sarah Mitchell",
            "pen_name": "S.M. Mitchell",
            "biography": "Born in the Pacific Northwest, Sarah Mitchell draws inspiration from misty forests and ancient legends...",
            "writing_style": "Mitchell's prose combines lyrical descriptions with fast-paced action...",
            "plot_count": 3,
            "created_at": "2025-01-28T10:00:00Z"
        }
    ],
    "total": 28,
    "limit": 50,
    "offset": 0
}
```

#### GET /api/authors/{author_id}
**Purpose**: Get detailed author information with related plots
**Parameters**:
- `author_id` (string): Author UUID
**Response**:
```json
{
    "id": "author-uuid-456",
    "author_name": "Sarah Mitchell",
    "pen_name": "S.M. Mitchell",
    "biography": "Born in Portland, Oregon, Sarah Jane Mitchell grew up surrounded by the misty forests of the Pacific Northwest, which deeply influenced her love for fantasy literature. With a PhD in Medieval History from Stanford University, she brings scholarly depth to her fantastical worlds.",
    "writing_style": "Mitchell's prose is lyrical yet accessible, blending rich world-building with emotionally resonant character development. Her writing features vivid sensory details and a talent for weaving complex magic systems into relatable human stories.",
    "plots": [
        {
            "id": "plot-uuid-123",
            "title": "The Dragon's Last Stand",
            "genre": "fantasy",
            "created_at": "2025-01-28T10:00:00Z"
        }
    ],
    "created_at": "2025-01-28T10:00:00Z",
    "updated_at": "2025-01-28T10:00:00Z"
}
```

### Genre & Classification

#### GET /api/genres
**Purpose**: List all genres with subgenres and microgenres
**Response**:
```json
{
    "genres": [
        {
            "id": "genre-1",
            "name": "fantasy",
            "description": "Stories with magical or supernatural elements",
            "subgenres": [
                {
                    "id": "subgenre-1",
                    "name": "epic_fantasy",
                    "description": "Large-scale fantasy with detailed world-building",
                    "microgenres": [
                        {
                            "id": "microgenre-1",
                            "name": "dragon_fantasy",
                            "description": "Fantasy stories centered around dragons"
                        }
                    ]
                }
            ]
        }
    ]
}
```

#### POST /api/genres
**Purpose**: Create new genre with name and description
**Request Body**:
```json
{
    "name": "cyberpunk",
    "description": "High-tech, low-life science fiction subgenre"
}
```
**Response**:
```json
{
    "id": "genre-uuid-789",
    "name": "cyberpunk",
    "description": "High-tech, low-life science fiction subgenre",
    "created_at": "2025-01-28T10:30:00Z"
}
```

#### GET /api/target-audiences
**Purpose**: List all target audiences
**Response**:
```json
{
    "target_audiences": [
        {
            "id": "audience-1",
            "age_range": "young_adult",
            "interests": ["adventure", "romance", "coming_of_age"],
            "demographics": {
                "gender": "all",
                "reading_level": "intermediate"
            }
        }
    ]
}
```

#### POST /api/target-audiences
**Purpose**: Create new target audience with structured data
**Request Body**:
```json
{
    "age_range": "middle_grade",
    "interests": ["mystery", "friendship", "school"],
    "demographics": {
        "gender": "all",
        "reading_level": "beginner"
    }
}
```

### Agent System

#### GET /agents
**Purpose**: List all available agents and their capabilities
**Response**:
```json
{
    "agents": [
        {
            "name": "OrchestratorAgent",
            "description": "Coordinates multi-agent workflows and routes requests",
            "capabilities": ["routing", "coordination", "workflow_planning"],
            "tools": ["all_agent_tools"],
            "status": "active"
        },
        {
            "name": "PlotGeneratorAgent", 
            "description": "Creates detailed book plots with genre-specific elements",
            "capabilities": ["plot_generation", "genre_analysis", "story_structure"],
            "tools": ["save_plot"],
            "status": "active"
        }
    ],
    "total": 9
}
```

## 🔌 OpenAI-Compatible API

### Chat Completions

#### POST /openai/v1/chat/completions
**Purpose**: OpenAI-compatible chat completion endpoint
**Request Body**:
```json
{
    "model": "gpt-3.5-turbo",
    "messages": [
        {
            "role": "user",
            "content": "Create a fantasy plot about a young mage"
        }
    ],
    "stream": false
}
```

**Response**:
```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1706472000,
    "model": "gemini-2.0-flash-exp",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "I'll create a fantasy plot for you..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 15,
        "completion_tokens": 200,
        "total_tokens": 215
    }
}
```

#### GET /openai/v1/models
**Purpose**: List available models in OpenAI format
**Response**:
```json
{
    "object": "list",
    "data": [
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "created": 1677610602,
            "owned_by": "bookswriter"
        }
    ]
}
```

## 📊 Metrics & Monitoring

#### GET /metrics/database/pool
**Purpose**: Real-time database connection pool statistics
**Response**:
```json
{
    "pool_type": "sqlite",
    "active_connections": 5,
    "idle_connections": 10,
    "total_connections": 15,
    "hit_rate": 0.85,
    "miss_count": 12,
    "health_failures": 0,
    "average_connection_time_ms": 45
}
```

#### GET /metrics/database/health
**Purpose**: Database connection health status
**Response**:
```json
{
    "status": "healthy",
    "last_health_check": "2025-01-28T10:30:00Z",
    "total_connections": 15,
    "healthy_connections": 15,
    "failed_connections": 0,
    "database_type": "supabase"
}
```

#### GET /metrics/performance/summary
**Purpose**: Overall system performance metrics
**Response**:
```json
{
    "timestamp": "2025-01-28T10:30:00Z",
    "uptime_seconds": 86400,
    "requests_total": 1500,
    "requests_per_second": 0.017,
    "average_response_time_ms": 250,
    "error_rate": 0.002,
    "database": {
        "connection_pool_hit_rate": 0.85,
        "average_query_time_ms": 45
    },
    "agents": {
        "total_invocations": 450,
        "average_processing_time_ms": 2500,
        "success_rate": 0.98
    }
}
```

## 🚨 Error Responses

### Standard Error Format
```json
{
    "error": {
        "type": "ValidationError",
        "message": "Invalid request parameters",
        "code": 400,
        "details": {
            "field": "title",
            "reason": "Title must be at least 3 characters"
        },
        "timestamp": "2025-01-28T10:30:00Z"
    }
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error
- `503` - Service Unavailable

## 🔐 Authentication

### Development
No authentication required for development environment.

### Production
- API Key authentication (planned)
- OAuth2 integration (planned)
- Rate limiting per API key

## 📚 Related Documentation

- **[Architecture Overview](../architecture/overview.md)** - System design
- **[WebSocket Integration](../integrations/websocket.md)** - Real-time communication
- **[Database Architecture](../architecture/database.md)** - Database operations
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - API troubleshooting

---

This API reference provides comprehensive information for integrating with BooksWriter's REST and WebSocket interfaces, supporting both direct integration and OpenAI-compatible usage.