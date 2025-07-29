# ADK Hybrid Architecture: Persistent Sessions + Custom Repositories

This document details BooksWriter's hybrid approach combining Google ADK's native persistent session/memory management with custom repository patterns for structured content.

## 🎯 Overview

This project implements a **hybrid approach** that gives us the best of both worlds:

- **ADK handles conversation continuity** - Agents remember context across sessions
- **Custom repositories handle structured data** - Plots, authors, worlds stored relationally
- **Flexible deployment options** - Development, database, or cloud persistence

## 🏗️ Architecture Components

### 1. ADK Service Factory (`src/core/adk_services.py`)

Manages creation of appropriate ADK services based on deployment mode:

```python
from src.core.adk_services import get_adk_service_factory

# Factory determines service mode from environment
factory = get_adk_service_factory(config)
runner = factory.create_runner(agent, app_name="my_app")
```

#### Service Modes:

- **`development`**: In-memory services (fast, non-persistent)
- **`database`**: Database-backed persistence 
- **`vertex_ai`**: Google Cloud Vertex AI services

### 2. Conversation Manager (`src/core/conversation_manager.py`)

Handles conversation continuity and memory management:

```python
# Retrieves conversation context
context = await conversation_manager.get_conversation_context(session_id, user_id)

# Saves important interactions to memory
await conversation_manager.save_interaction_to_memory(session_id, user_id, interaction_data)
```

### 3. Enhanced BaseAgent (`src/core/base_agent.py`)

Automatically integrates conversation continuity:

- Injects conversation history into agent messages
- Saves successful tool interactions to memory
- Maintains user preferences across sessions

## ⚙️ Configuration

### Environment Variables

Set these in your `.env` file:

```bash
# ADK Service Mode
ADK_SERVICE_MODE=development  # Options: development, database, vertex_ai

# Google Cloud (for vertex_ai mode)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AI_AGENT_ENGINE_ID=your-agent-engine-id

# Database (for database mode)  
DATABASE_URL=sqlite:///development.db
```

## 🚀 Deployment Scenarios

### Development Mode (Default)
```bash
ADK_SERVICE_MODE=development
```

- **Session Service**: `InMemorySessionService` (non-persistent)
- **Memory Service**: `InMemoryMemoryService` (non-persistent)
- **Benefits**: Fast startup, no configuration needed
- **Trade-offs**: No conversation continuity across restarts

### Database Mode
```bash
ADK_SERVICE_MODE=database
DATABASE_URL=sqlite:///production.db
```

- **Session Service**: `DatabaseSessionService` (persistent)
- **Memory Service**: `DatabaseMemoryService` (persistent)
- **Benefits**: Full conversation continuity, local control
- **Trade-offs**: Requires database setup

### Vertex AI Mode  
```bash
ADK_SERVICE_MODE=vertex_ai
GOOGLE_CLOUD_PROJECT=my-project
VERTEX_AI_AGENT_ENGINE_ID=my-engine-id
```

- **Session Service**: `VertexAiSessionService` (cloud-persistent)
- **Memory Service**: `VertexAiMemoryBankService` (semantic search)
- **Benefits**: Advanced semantic memory, cloud-managed
- **Trade-offs**: Requires Google Cloud setup

## 🔄 How It Works

### 1. Agent Initialization
```python
# BaseAgent automatically detects service mode
agent = PlotGeneratorAgent(config)
# Logs: "Initialized with ADK service mode: database"
```

### 2. Conversation Context Loading
```python
async def _prepare_message(self, request: AgentRequest) -> str:
    # Automatically loads conversation history
    conversation_context = await self._conversation_manager.get_conversation_context(
        request.session_id, request.user_id
    )
    
    if conversation_context.get("has_conversation_history"):
        # Injects context into agent's message
        message += f"\\n\\nCONVERSATION HISTORY:\\n{context_summary}"
```

### 3. Memory Saving After Tool Use
```python
# Automatically triggered after successful tool calls
await self._save_interaction_to_memory(request, tool_calls, content)

# Extracts and saves:
# - Generated content (plots, authors, worlds)
# - Key entities for search
# - User preferences
# - Interaction summaries
```

## ✅ Benefits Achieved

### **Conversation Continuity**
- Agents remember previous interactions
- User preferences maintained across sessions
- Context-aware responses

### **Structured Data Control**  
- Custom repositories for business logic
- Relational data for complex queries
- Full schema control

### **Deployment Flexibility**
- Single codebase works across environments
- Graceful fallback to simpler services
- Environment-based configuration

### **Best of Both Worlds**
- ADK handles conversational memory automatically
- Custom code handles structured content creation
- No compromise on either capability

## 💻 Usage Examples

### Basic Agent Usage (No Changes Required)
```python
# Existing code works unchanged
agent = PlotGeneratorAgent(config)
response = await agent.process_request(request)
# Now includes conversation continuity automatically!
```

### Accessing Conversation Context
```python
# Get conversation history for a user
conversation_manager = await get_conversation_manager(adk_factory)
context = await conversation_manager.get_conversation_context(session_id, user_id)

if context["has_conversation_history"]:
    print(f"User has {len(context['recent_interactions'])} recent interactions")
    print(f"Context summary: {context['context_summary']}")
```

### Updating User Preferences
```python
# Automatically learned from interactions and saved
preferences = {
    "preferred_genre": "fantasy",
    "writing_style": "descriptive",
    "target_audience": "young_adult"
}
await conversation_manager.update_user_preferences(user_id, preferences)
```

## 📊 Implementation Impact

### Before (JSON-only approach):
- Agents generated JSON responses
- No conversation memory
- Manual orchestration required

### After (Hybrid ADK approach):
- ✅ Agents use tools for structured data
- ✅ Automatic conversation continuity  
- ✅ ADK handles orchestration
- ✅ Memory persists across sessions
- ✅ User preferences maintained
- ✅ Context-aware responses

## 📝 Monitoring and Debugging

The system provides comprehensive logging:

```
INFO:adk_services:ADK Service Mode: database
INFO:conversation_manager:ConversationManager initialized (persistent: True)
INFO:agent.plot_generator:Retrieved conversation context for user xyz: 3 interactions, 5 memories
DEBUG:conversation_manager:Saved interaction to memory: 2 entities
```

## 🔮 Future Enhancements

1. **Advanced Memory Search**: Semantic search across user's creative history
2. **Preference Learning**: ML-based preference inference from interactions  
3. **Cross-Session Recommendations**: Suggest content based on user's creative patterns
4. **Collaborative Memory**: Shared context across multiple users/sessions

## 📚 Related Documentation

- **[Architecture Overview](overview.md)** - Complete system architecture
- **[Multi-Agent System](agents.md)** - Agent coordination patterns
- **[Database Architecture](database.md)** - Database layer design
- **[Environment Configuration](../setup/environment.md)** - Configuration options

---

This hybrid architecture successfully implements enterprise-grade conversation continuity while maintaining full control over structured creative content, providing the foundation for sophisticated multi-agent book writing workflows.