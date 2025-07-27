# BooksWriter - Complete Setup Guide

## Overview

BooksWriter is a sophisticated AI-powered book writing system using multiple specialized agents to generate plots, create author profiles, and manage book content. All data is persisted in a Supabase (PostgreSQL) database.

## System Architecture

### Core Agents
- **Orchestrator Agent**: Routes requests to appropriate specialized agents
- **Plot Generator Agent**: Creates detailed plot summaries with genre metadata
- **Author Generator Agent**: Creates author profiles and writing styles  
- **Content Agents**: Generate chapters, character development, and book content

### Technology Stack
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Vertex AI (Gemini models)
- **Frontend**: Vanilla JavaScript with WebSocket support

## Prerequisites

1. **Python 3.11+** installed
2. **Google Cloud Project** with Vertex AI enabled
3. **Supabase Account** with a project created
4. **Git** for version control

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd BooksWriter
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:
```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=config/service-account-key.json
GOOGLE_GENAI_USE_VERTEXAI=true

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_PASSWORD=your-database-password
```

### 4. Google Cloud Setup

1. Create a service account in Google Cloud Console
2. Download the service account key JSON
3. Save it as `config/service-account-key.json`
4. Enable Vertex AI API in your project

### 5. Database Setup

#### Option A: Automated Setup (Recommended)
```bash
python scripts/setup/one_click_setup.py
```

#### Option B: Supabase CLI Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Initialize and link project
supabase init
supabase link --project-ref your-project-ref

# Run migrations
supabase db push
```

#### Option C: Manual Setup
1. Connect to Supabase SQL Editor
2. Run all migration files in order from `migrations/` directory
3. Verify tables are created correctly

### 6. Verify Installation
```bash
# Run the application
python main.py

# Open browser to http://localhost:8000
# Test the chat interface
```

## Project Structure

```
BooksWriter/
├── src/               # Source code
│   ├── agents/       # Agent implementations
│   ├── database/     # Database services
│   ├── api/          # API endpoints
│   └── utils/        # Utility functions
├── tests/            # Test files
├── docs/             # Documentation
├── migrations/       # Database migrations
├── scripts/          # Setup and maintenance scripts
├── templates/        # HTML templates
└── static/           # Static assets
```

## Common Issues & Solutions

### Database Connection Issues
- Verify Supabase URL and keys in `.env`
- Check if database password is correct
- Ensure your IP is whitelisted in Supabase settings

### Google Cloud Authentication
- Verify service account key path is correct
- Check if Vertex AI API is enabled
- Ensure service account has necessary permissions

### Migration Failures
- Run migrations in order (001, 002, etc.)
- Check `migrations/applied_migrations.json` for status
- Use manual setup if automated fails

## Getting Supabase Credentials

### Database Password
1. Go to Supabase Dashboard > Settings > Database
2. Find "Connection string" section
3. Password is in the connection string

### Service Role Key  
1. Go to Settings > API
2. Copy the `service_role` key (not anon key)

### Project URL
1. Go to Settings > API
2. Copy the Project URL

## Development Workflow

1. **Start Development Server**
   ```bash
   python main.py
   ```

2. **Run Tests**
   ```bash
   pytest tests/
   ```

3. **Create New Migration**
   ```bash
   python scripts/setup/create_migration.py "migration_name"
   ```

## Support

For issues or questions:
1. Check existing documentation in `docs/`
2. Review migration files for database schema
3. Examine test files for usage examples

Last Updated: January 2025