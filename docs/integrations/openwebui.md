# Open-WebUI Integration

Complete guide for integrating BooksWriter with Open-WebUI for an enhanced, customizable frontend experience.

## Overview

Open-WebUI provides a modern, feature-rich interface for BooksWriter that includes:
- **Chat Interface**: Advanced chat with conversation history
- **Model Management**: Easy switching between AI models
- **User Authentication**: Multi-user support with role-based access
- **Customization**: Themes, plugins, and personalization options
- **File Handling**: Document upload and processing capabilities

## Quick Setup

### 1. Start BooksWriter Backend
```bash
# Ensure BooksWriter is running on port 8000
python main.py
```

### 2. Launch Open-WebUI
```bash
# Using Docker Compose (Recommended)
docker-compose -f docker-compose.openwebui.yml up -d

# Or using Docker directly
docker run -d \
  --name open-webui \
  --add-host=host.docker.internal:host-gateway \
  -p 3000:8080 \
  -e OPENAI_API_BASE_URL=http://host.docker.internal:8000/openai/v1 \
  -e OPENAI_API_KEY=dummy \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

### 3. Access Interface
- **Open-WebUI**: http://localhost:3000
- **BooksWriter Direct**: http://localhost:8000

## Configuration

### Docker Compose Configuration

#### docker-compose.openwebui.yml
```yaml
version: '3.8'

services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui-bookswriter
    ports:
      - "3000:8080"
    environment:
      # BooksWriter API Configuration
      - OPENAI_API_BASE_URL=http://host.docker.internal:8000/openai/v1
      - OPENAI_API_KEY=dummy-key-for-bookswriter
      
      # Open-WebUI Configuration
      - WEBUI_NAME=BooksWriter
      - WEBUI_URL=http://localhost:3000
      - WEBUI_SECRET_KEY=your-secret-key-here
      
      # Authentication (Optional)
      - ENABLE_SIGNUP=true
      - DEFAULT_USER_ROLE=user
      
      # Features
      - ENABLE_RAG=false
      - ENABLE_WEB_SEARCH=false
      - ENABLE_IMAGE_GENERATION=false
      
    volumes:
      - open-webui-data:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

volumes:
  open-webui-data:
```

### Environment Variables

#### BooksWriter Integration
```bash
# API Configuration
OPENAI_API_BASE_URL=http://host.docker.internal:8000/openai/v1
OPENAI_API_KEY=dummy-key-for-bookswriter

# Custom Branding
WEBUI_NAME=BooksWriter
WEBUI_URL=http://localhost:3000
WEBUI_SECRET_KEY=your-unique-secret-key

# Feature Control
ENABLE_RAG=false              # Disable RAG (use BooksWriter's agents)
ENABLE_WEB_SEARCH=false       # Disable web search
ENABLE_IMAGE_GENERATION=false # Disable image generation
ENABLE_SIGNUP=true            # Allow user registration
```

## API Integration

### OpenAI-Compatible Endpoints

BooksWriter provides OpenAI-compatible endpoints for seamless integration:

#### Available Models
```bash
GET /openai/v1/models
```

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
    },
    {
      "id": "gpt-4",
      "object": "model", 
      "created": 1677610602,
      "owned_by": "bookswriter"
    }
  ]
}
```

#### Chat Completions
```bash
POST /openai/v1/chat/completions
```

**Request**:
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Create a fantasy plot about a young mage discovering ancient powers"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response**:
```json
{
  "id": "chatcmpl-bookswriter-123",
  "object": "chat.completion",
  "created": 1706472000,
  "model": "gemini-2.0-flash-exp",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'll create a compelling fantasy plot for you...\n\n**Title: The Resonance of Forgotten Realms**\n\n**Plot Summary:**\nSeventeen-year-old Lyra discovers she can hear the 'resonance' - ancient magical frequencies..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 450,
    "total_tokens": 475
  }
}
```

### Streaming Support

#### Streaming Chat Completions
```bash
POST /openai/v1/chat/completions
Content-Type: application/json

{
  "model": "gpt-3.5-turbo",
  "messages": [...],
  "stream": true
}
```

**Streaming Response**:
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1706472000,"model":"gemini-2.0-flash-exp","choices":[{"index":0,"delta":{"content":"I'll"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1706472000,"model":"gemini-2.0-flash-exp","choices":[{"index":0,"delta":{"content":" create"},"finish_reason":null}]}

data: [DONE]
```

## Feature Integration

### BooksWriter-Specific Features

#### Multi-Agent Prompts
Open-WebUI users can access BooksWriter's specialized agents through specific prompts:

```
# Plot Generation
Create a detailed fantasy plot with dragons, magic system, and coming-of-age themes

# Author Creation  
Generate an author profile for Sarah Mitchell who writes young adult fantasy novels

# World Building
Build a comprehensive fantasy world with unique magic system, politics, and geography

# Character Development
Create main characters for a space opera with diverse backgrounds and motivations

# Complete Foundation
Create complete book foundation: plot, world, characters, and author for cyberpunk thriller
```

#### Model Selection
Users can switch between different Gemini models:
- **gpt-3.5-turbo** → Maps to `gemini-2.0-flash-exp` (recommended)
- **gpt-4** → Maps to `gemini-1.5-pro` (for complex tasks)

### Conversation Management

#### Persistent Sessions
Open-WebUI automatically maintains conversation history, allowing users to:
- Continue previous book creation sessions
- Build upon existing plots and characters
- Maintain context across multiple interactions

#### Export Capabilities
Users can export their book creations in various formats:
- **Markdown**: Complete book outlines
- **JSON**: Structured data for further processing
- **PDF**: Formatted book proposals

## Customization

### Theme Configuration

#### Custom CSS
```css
/* Custom BooksWriter Theme */
:root {
  --primary-color: #2563eb;
  --secondary-color: #7c3aed;
  --accent-color: #059669;
  --background-color: #f8fafc;
  --text-color: #1e293b;
}

.chat-message.user {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
}

.chat-message.assistant {
  background: var(--background-color);
  border-left: 4px solid var(--accent-color);
}
```

#### Logo and Branding
```bash
# Mount custom assets
-v /path/to/custom/logo.png:/app/backend/static/logo.png
-v /path/to/custom/favicon.ico:/app/backend/static/favicon.ico
```

### Plugin Integration

#### BooksWriter Plugin (Custom)
```javascript
// bookswriter-plugin.js
const BookWriterPlugin = {
  name: 'BooksWriter Enhanced',
  version: '1.0.0',
  
  // Add custom buttons for common BooksWriter operations
  addQuickActions: function() {
    return [
      {
        label: '📖 Create Plot',
        prompt: 'Create a detailed plot for a [GENRE] novel with [THEMES]'
      },
      {
        label: '✍️ Generate Author',
        prompt: 'Create an author profile for someone who writes [GENRE] novels'
      },
      {
        label: '🌍 Build World',
        prompt: 'Create a comprehensive fictional world for [GENRE] with detailed geography, politics, and culture'
      },
      {
        label: '👥 Develop Characters',
        prompt: 'Create main characters for a [GENRE] story with diverse backgrounds and clear motivations'
      }
    ];
  }
};
```

## Advanced Configuration

### Multi-User Setup

#### User Authentication
```yaml
environment:
  - ENABLE_SIGNUP=true
  - DEFAULT_USER_ROLE=user
  - ENABLE_LOGIN_FORM=true
  - ENABLE_OAUTH=false
  
  # Admin Configuration
  - ADMIN_EMAIL=admin@bookswriter.com
  - ADMIN_PASSWORD=your-secure-password
```

#### Role-Based Access
```yaml
environment:
  # User Roles
  - DEFAULT_USER_ROLE=user
  - ENABLE_ADMIN_EXPORT=true
  - ENABLE_USER_EXPORT=true
  
  # Feature Access Control
  - USER_PERMISSIONS=chat,export
  - ADMIN_PERMISSIONS=chat,export,admin,users
```

### Production Deployment

#### SSL/HTTPS Configuration
```yaml
services:
  open-webui:
    # ... other config
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.openwebui.rule=Host(`bookswriter.yourdomain.com`)"
      - "traefik.http.routers.openwebui.tls=true"
      - "traefik.http.routers.openwebui.tls.certresolver=letsencrypt"
```

#### Database Persistence
```yaml
volumes:
  - open-webui-data:/app/backend/data
  - ./backups:/app/backend/data/backups:ro
```

## Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check BooksWriter is accessible
curl http://localhost:8000/health

# Check Open-WebUI can reach BooksWriter
docker exec open-webui-bookswriter curl http://host.docker.internal:8000/health

# Check model availability
curl http://localhost:8000/openai/v1/models
```

#### Model Selection Issues
```bash
# Verify model mapping in Open-WebUI
# Check that models appear in the dropdown
# Test with simple prompt to verify functionality
```

#### Performance Issues
```bash
# Monitor container resources
docker stats open-webui-bookswriter

# Check BooksWriter performance
curl http://localhost:8000/metrics/performance/summary

# Increase container resources if needed
docker-compose -f docker-compose.openwebui.yml up -d --scale open-webui=1 --memory=2g
```

### Debug Mode

#### Enable Debug Logging
```yaml
environment:
  - WEBUI_SECRET_KEY=debug-key
  - LOG_LEVEL=DEBUG
  - ENABLE_DEV_MODE=true
```

#### Container Logs
```bash
# View Open-WebUI logs
docker logs -f open-webui-bookswriter

# View BooksWriter logs
python main.py --log-level DEBUG
```

## Related Documentation

- **[API Reference](../reference/api.md)** - Complete API documentation
- **[Architecture Overview](../architecture/overview.md)** - System architecture
- **[Installation Guide](../setup/installation.md)** - Setup instructions
- **[Troubleshooting Guide](../guides/troubleshooting.md)** - Additional troubleshooting

---

*This integration guide provides comprehensive information for setting up and customizing Open-WebUI with BooksWriter.*