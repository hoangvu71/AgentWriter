# Database Migration Strategy for Multi-Agent Book Writer

## Problem
Supabase doesn't allow CREATE TABLE operations via their client API for security reasons. This makes automated schema changes challenging.

## Solutions for Future Schema Changes

### 1. **Supabase Migrations (Recommended)**
Use Supabase CLI for version-controlled migrations:

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize Supabase in your project
supabase init

# Create a new migration
supabase migration new add_new_agent_table

# This creates a file like: supabase/migrations/20240115_add_new_agent_table.sql
# Edit this file with your SQL changes

# Apply migrations
supabase db push
```

### 2. **Database Migration Tool (Alembic)**
Use a Python migration tool:

```bash
pip install alembic

# Initialize Alembic
alembic init alembic

# Create a migration
alembic revision -m "add character development agent table"

# Apply migrations
alembic upgrade head
```

### 3. **Direct PostgreSQL Connection**
Connect directly to Supabase's PostgreSQL:

```python
import psycopg2
from urllib.parse import urlparse

# Get connection string from Supabase dashboard
DATABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create new tables
cur.execute("""
    CREATE TABLE IF NOT EXISTS character_developments (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        plot_id UUID REFERENCES plots(id),
        character_name VARCHAR(255),
        character_arc TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

conn.commit()
```

### 4. **Supabase Database Webhooks**
Use Supabase's database functions and triggers:

```sql
-- Create a function that can be called via RPC
CREATE OR REPLACE FUNCTION create_new_agent_tables()
RETURNS void AS $$
BEGIN
    CREATE TABLE IF NOT EXISTS new_agent_data (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        -- your columns
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Then call via API:
-- supabase.rpc('create_new_agent_tables')
```

### 5. **Schema Version Management**
Create a schema versioning system:

```sql
-- Version tracking table
CREATE TABLE schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

-- Migration scripts as files:
-- migrations/001_initial_schema.sql
-- migrations/002_add_character_agent.sql
-- migrations/003_add_chapter_outlines.sql
```

## Recommended Approach for Your Project

1. **For Development**: Use the Supabase CLI
   - Install: `npm install -g supabase`
   - Link to your project: `supabase link --project-ref YOUR_PROJECT_ID`
   - Create migrations: `supabase migration new [description]`
   - Apply: `supabase db push`

2. **For Production**: Set up a migration pipeline
   - Store all schema changes as numbered SQL files
   - Use GitHub Actions to apply migrations automatically
   - Keep a migrations/ folder in your project

## Example: Adding a New Agent

Let's say you want to add a "Character Development Agent":

### Step 1: Create Migration File
`migrations/002_add_character_agent.sql`:

```sql
-- Add character development tables
CREATE TABLE character_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plot_id UUID REFERENCES plots(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    character_name VARCHAR(255) NOT NULL,
    role VARCHAR(100), -- protagonist, antagonist, supporting
    personality_traits TEXT[],
    backstory TEXT,
    character_arc TEXT,
    relationships JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE character_interactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    character1_id UUID REFERENCES character_profiles(id),
    character2_id UUID REFERENCES character_profiles(id),
    relationship_type VARCHAR(100),
    interaction_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_character_profiles_plot_id ON character_profiles(plot_id);
CREATE INDEX idx_character_profiles_session_id ON character_profiles(session_id);
```

### Step 2: Python Migration Runner
`run_migration.py`:

```python
import os
from pathlib import Path
from supabase import create_client

def run_migration(migration_file):
    """Run a single migration file"""
    # For now, this would need to be done manually
    # But you could automate with Supabase CLI
    
    print(f"Please run this migration in Supabase SQL Editor:")
    print(f"File: {migration_file}")
    
    with open(migration_file, 'r') as f:
        print(f.read())

def get_pending_migrations():
    """Check which migrations haven't been applied"""
    migrations_dir = Path("migrations")
    return sorted(migrations_dir.glob("*.sql"))

if __name__ == "__main__":
    for migration in get_pending_migrations():
        run_migration(migration)
```

## Best Practices

1. **Always use IF NOT EXISTS** for CREATE TABLE statements
2. **Version your schema changes** with numbered files
3. **Test migrations locally** before applying to production
4. **Keep migrations idempotent** (can run multiple times safely)
5. **Document each schema change** with comments

## Quick Setup for Future Changes

1. Create a `migrations/` folder in your project
2. Add new SQL files for each schema change
3. Use Supabase CLI or manual SQL Editor to apply
4. Keep track of applied migrations

This way, adding new agents or modifying tables becomes:
1. Create a new migration file
2. Run one command or paste into SQL Editor
3. Done!

Much better than modifying the entire schema each time!