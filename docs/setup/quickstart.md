# Quick Start Guide

Get BooksWriter running in 5 minutes with this quick start guide.

## 🎯 Prerequisites

- Python 3.11+
- Node.js (for MCP integration)
- Google Cloud account
- Supabase account

## ⚡ Quick Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd AgentWriter
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Start the System
```bash
python main.py
```

### 3. Access the Interface
Open your browser to: **http://localhost:8000**

### 4. Try Example Prompt
```
Create a fantasy novel, LitRPG, Zombie Apocalypse, survive and family, dark/humour/realistic, Male/Heterosexual/Young Adults. Create author too.
```

## ✅ What You Get

- **Multi-agent coordination** - Orchestrator routes to specialized agents
- **Automatic data persistence** - All plots and authors saved to database
- **Real-time WebSocket chat** - Streaming responses from agents
- **5 AI model options** - Choose the best model for your task

## 🔧 Optional Configuration

For full functionality, set up:
1. **[Environment Variables](environment.md)** - Google Cloud and Supabase credentials
2. **[Database Setup](installation.md#database-setup)** - Complete database configuration
3. **[MCP Integration](../integrations/mcp-supabase.md)** - Direct database access

## 🚀 Next Steps

- Read the **[Complete Setup Guide](installation.md)** for full configuration
- Explore **[Project Overview](../architecture/overview.md)** to understand the system
- Check **[Development Workflow](../guides/development.md)** if you plan to contribute

## 🆘 Need Help?

- **Common issues**: Check [Troubleshooting Guide](../guides/troubleshooting.md)
- **Environment setup**: See [Environment Configuration](environment.md)
- **Database problems**: Review [Database Architecture](../architecture/database.md)

---

⚡ **Quick tip**: The system works with minimal configuration. For development, the SQLite database will be created automatically with no additional setup required!