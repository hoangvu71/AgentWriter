# Multi-Agent Book Writer System

A sophisticated multi-agent system for book writing powered by Google's Agent Development Kit (ADK) and Gemini AI. The system features specialized agents that work together to create comprehensive book writing solutions.

## Multi-Agent Architecture

### **🎯 Orchestrator Agent**
- Routes user requests to appropriate agents
- Coordinates sequential workflows between agents
- Manages inter-agent communication
- Makes intelligent routing decisions based on user intent

### **📖 Plot Generator Agent**
- Creates detailed plots based on comprehensive parameters:
  - **Genre**: Fantasy, Romance, Sci-Fi, Mystery, etc.
  - **Subgenre**: LitRPG, Space Opera, Cozy Mystery, etc.
  - **Microgenre**: Zombie Apocalypse, Time Travel, etc.
  - **Tropes**: Survive and family, Chosen one, etc.
  - **Tone**: Dark, humorous, realistic, etc.
  - **Target Audience**: Age range, sexual orientation, gender

### **✍️ Author Generator Agent**
- Creates author profiles matching microgenre and target audience:
  - Author name and pen name suggestions
  - Comprehensive biography and background
  - Writing voice and style descriptions
  - Genre expertise and credentials
  - Target audience appeal analysis

## Features

- **🤖 Multi-Agent Coordination**: Orchestrator routes requests to specialized agents
- **📊 Sequential Workflows**: Plot → Author → Final Response coordination
- **🎭 Genre Specialization**: Comprehensive genre, subgenre, and microgenre support
- **👥 Target Audience Matching**: Age, orientation, and gender considerations
- **🧠 Memory**: Maintains conversation history and user preferences across agents
- **🤖 Model Selection**: Choose from 5 different Google AI models:
  - **Gemini 2.0 Flash**: Fast, efficient for general writing tasks
  - **Gemini 2.5 Flash**: Latest with thinking capabilities
  - **Gemini 2.5 Pro Preview**: Advanced reasoning for complex projects
  - **Gemini 1.5 Pro**: Stable production model
  - **Gemini 1.5 Flash**: Cost-effective for basic tasks
- **⚡ Real-time Chat**: WebSocket-based streaming responses from all agents
- **🔄 Session Management**: Persistent conversations across sessions and agents
- **🎨 Clean Formatting**: Automatically formats responses for readability

## System Architecture

- **Backend**: FastAPI with WebSocket support
- **Multi-Agent System**: Google Agent Development Kit (ADK) with specialized agents
- **Frontend**: Simple HTML/CSS/JavaScript interface with multi-agent support
- **Communication**: Inter-agent communication via orchestrator coordination

## Prerequisites

1. **Google Cloud Setup**:
   - Google Cloud Project with billing enabled
   - Vertex AI API enabled
   - Service account with appropriate permissions

2. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd BooksWriter
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   - Update `.env` with your Google Cloud project details
   - Place your service account key as `service-account-key.json`

4. **Environment variables**:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
   GOOGLE_GENAI_USE_VERTEXAI=true
   ```

## Usage

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Access the interface**:
   - Open your browser to `http://localhost:8000`
   - Start chatting with the multi-agent book writing system

3. **Example interactions**:
   - "Create a fantasy novel, LitRPG, Zombie Apocalypse, survive and family, dark/humour/realistic, Male/Heterosexual/Young Adults. Create author too."
   - "Generate a plot for a romance novel with enemies-to-lovers trope"
   - "Create an author profile for a mystery writer targeting middle-aged women"
   - "I need both a plot and author for a sci-fi thriller"

## API Endpoints

- `GET /` - Web interface
- `GET /health` - Health check with multi-agent system info
- `GET /sessions` - List active sessions
- `GET /sessions/{session_id}` - Get session info
- `WebSocket /ws/{session_id}` - Multi-agent chat interface

### Multi-Agent System
- `GET /agents` - List all available agents and their capabilities

### Model Management
- `GET /models` - List available AI models and current selection
- `GET /models/{model_id}` - Get detailed information about a specific model
- `POST /models/{model_id}/switch` - Switch to a different AI model

## Testing

Run the test suite:
```bash
python test_app.py
```

For integration tests:
```bash
python -m pytest test_agent_integration.py -v
```

For multi-agent system tests:
```bash
python -m pytest test_multi_agent_integration.py -v
```

## File Structure

```
BooksWriter/
├── main.py                 # FastAPI application with multi-agent support
├── agent_service.py        # Legacy single agent implementation  
├── multi_agent_system.py   # Multi-agent system implementation
├── test_app.py            # Application tests
├── test_agent_integration.py # Integration tests
├── test_multi_agent_integration.py # Multi-agent system tests
├── test_websocket_integration.py # WebSocket tests
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── service-account-key.json # Google Cloud credentials
├── CLAUDE.md             # Development guidelines
└── README.md             # This file
```

## Development

The project follows Test-Driven Development (TDD) principles:

1. **Write tests first** - All functionality starts with failing tests
2. **Keep it simple** - No overengineering or unnecessary complexity  
3. **Ask for clarification** - Never assume requirements
4. **Focus on root causes** - Fix core issues, not symptoms
5. **Multi-agent design** - Each agent has a single, well-defined responsibility

## WebSocket Message Format

### Client to Server:
```json
{
  "type": "message",
  "content": "Your message here",
  "user_id": "user123"
}
```

### Server to Client:
```json
{
  "type": "stream_chunk",
  "content": "Response chunk..."
}
```

## Troubleshooting

1. **Authentication errors**: Ensure Google Cloud credentials are properly configured
2. **Connection issues**: Check if Vertex AI API is enabled in your project
3. **Search not working**: Verify Google Search API permissions
4. **WebSocket disconnections**: Check network connectivity and firewall settings

## Contributing

1. Follow the TDD approach outlined in `CLAUDE.md`
2. Write tests for all new functionality
3. Keep code simple and focused
4. Ask for clarification when requirements are unclear

## License

This project is for educational and demonstration purposes.