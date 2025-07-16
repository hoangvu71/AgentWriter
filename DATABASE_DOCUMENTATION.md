# Database Schema Documentation

## Overview
The Multi-Agent Book Writer System uses Supabase (PostgreSQL) for data persistence. All plots, authors, and session data are automatically saved and can be retrieved for future use.

## Database Schema

### 1. **users** table
Stores unique users of the system.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `user_id` | VARCHAR(255) UNIQUE | Human-readable user identifier |
| `created_at` | TIMESTAMP | When user was first created |
| `updated_at` | TIMESTAMP | Last activity timestamp |

**Indexes:**
- `idx_users_user_id` on `user_id`

### 2. **sessions** table
Tracks individual chat sessions/conversations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `session_id` | VARCHAR(255) UNIQUE | Human-readable session identifier |
| `user_id` | UUID (FK → users.id) | Reference to user who owns this session |
| `created_at` | TIMESTAMP | When session started |
| `updated_at` | TIMESTAMP | Last activity in session |

**Indexes:**
- `idx_sessions_session_id` on `session_id`

### 3. **plots** table
Stores all generated plot data with normalized foreign key references.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `session_id` | UUID (FK → sessions.id) | Session where plot was created |
| `user_id` | UUID (FK → users.id) | User who created the plot |
| `title` | TEXT | Generated book title |
| `plot_summary` | TEXT | Complete plot description |
| `genre_id` | UUID (FK → genres.id) | Reference to genre |
| `subgenre_id` | UUID (FK → subgenres.id) | Reference to subgenre |
| `microgenre_id` | UUID (FK → microgenres.id) | Reference to microgenre |
| `trope_id` | UUID (FK → tropes.id) | Reference to trope |
| `tone_id` | UUID (FK → tones.id) | Reference to tone |
| `target_audience_id` | UUID (FK → target_audiences.id) | Reference to target audience |
| `author_id` | UUID (FK → authors.id) | Reference to author (optional) |
| `created_at` | TIMESTAMP | When plot was generated |

**Indexes:**
- `idx_plots_user_id` on `user_id`
- `idx_plots_session_id` on `session_id` 
- `idx_plots_created_at` on `created_at`
- `idx_plots_genre_id` on `genre_id`
- `idx_plots_author_id` on `author_id`

### 4. **authors** table
Stores generated author profiles (can have multiple plots).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `session_id` | UUID (FK → sessions.id) | Session where author was created |
| `user_id` | UUID (FK → users.id) | User who created the author |
| `author_name` | VARCHAR(255) | Full author name |
| `pen_name` | VARCHAR(255) | Author's pen name (optional) |
| `biography` | TEXT | Author's background and biography |
| `writing_style` | TEXT | Description of author's writing style |
| `created_at` | TIMESTAMP | When author was generated |

**Indexes:**
- `idx_authors_user_id` on `user_id`
- `idx_authors_created_at` on `created_at`

**Note:** The relationship is now one-to-many: one author can have multiple plots. Plots reference authors via `plots.author_id`.

### 5. **orchestrator_decisions** table
Analytics table storing AI routing and decision data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `session_id` | UUID (FK → sessions.id) | Session where decision was made |
| `user_id` | UUID (FK → users.id) | User associated with decision |
| `routing_decision` | VARCHAR(50) | Which agent was selected |
| `agents_invoked` | TEXT[] | Array of agents that were called |
| `extracted_parameters` | JSONB | Parameters extracted from user input |
| `workflow_plan` | TEXT | AI's planned workflow |
| `created_at` | TIMESTAMP | When decision was made |

**Indexes:**
- `idx_orchestrator_decisions_user_id` on `user_id`
- `idx_orchestrator_decisions_created_at` on `created_at`

## Normalized Genre System

### 6. **genres** table
Stores main genre categories.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `name` | VARCHAR(100) UNIQUE | Genre name (Fantasy, Romance, etc.) |
| `description` | TEXT | Genre description |
| `created_at` | TIMESTAMP | When genre was created |

### 7. **subgenres** table
Stores subgenre categories linked to genres.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `name` | VARCHAR(100) | Subgenre name (Epic Fantasy, Space Opera, etc.) |
| `genre_id` | UUID (FK → genres.id) | Reference to parent genre |
| `description` | TEXT | Subgenre description |
| `created_at` | TIMESTAMP | When subgenre was created |

### 8. **microgenres** table
Stores microgenre types linked to subgenres.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `name` | VARCHAR(100) | Microgenre name (Zombie Apocalypse, Time Travel, etc.) |
| `subgenre_id` | UUID (FK → subgenres.id) | Reference to parent subgenre |
| `description` | TEXT | Microgenre description |
| `created_at` | TIMESTAMP | When microgenre was created |

### 9. **tropes** table
Stores story tropes linked to microgenres.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `name` | VARCHAR(100) | Trope name (Chosen One, Enemies to Lovers, etc.) |
| `microgenre_id` | UUID (FK → microgenres.id) | Reference to parent microgenre |
| `description` | TEXT | Trope description |
| `created_at` | TIMESTAMP | When trope was created |

### 10. **tones** table
Stores tone variations linked to tropes.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `name` | VARCHAR(100) | Tone name (Dark, Humorous, Realistic, etc.) |
| `trope_id` | UUID (FK → tropes.id) | Reference to parent trope |
| `description` | TEXT | Tone description |
| `created_at` | TIMESTAMP | When tone was created |

### 11. **target_audiences** table
Stores target audience demographics and interests.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated unique identifier |
| `age_group` | VARCHAR(50) | Age group (Young Adult, Adult, etc.) |
| `gender` | VARCHAR(50) | Gender preference (All, Male, Female, Non-binary) |
| `sexual_orientation` | VARCHAR(50) | Orientation (All, Heterosexual, LGBTQ+, etc.) |
| `interests` | TEXT[] | Array of interest keywords |
| `description` | TEXT | Audience description |
| `created_at` | TIMESTAMP | When audience was created |

**Hierarchy:** `Genre → Subgenre → Microgenre → Trope → Tone`

**Indexes:**
- `idx_subgenres_genre_id` on `genre_id`
- `idx_microgenres_subgenre_id` on `subgenre_id`
- `idx_tropes_microgenre_id` on `microgenre_id`
- `idx_tones_trope_id` on `trope_id`

## Database Configuration

### Connection Details
```env
SUPABASE_URL=https://cfqgzbudjnvtyxrrvvmo.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=BTTmSilqcNn9Ynj5
```

### Connection String
```
postgresql://postgres:BTTmSilqcNn9Ynj5@db.cfqgzbudjnvtyxrrvvmo.supabase.co:5432/postgres
```

## Data Flow

1. **User Input** → Creates/gets user in `users` table
2. **Session Start** → Creates session in `sessions` table  
3. **Plot Generation** → Saves to `plots` table with full metadata
4. **Author Generation** → Saves to `authors` table linked to plot
5. **AI Decisions** → Logged to `orchestrator_decisions` for analytics

## Sample Data

### Sample Plot Record
```json
{
  "id": "db6b6da0-9f98-488c-bb53-af3532a8ed37",
  "title": "Test Fantasy Novel",
  "plot_summary": "A young wizard discovers an ancient artifact...",
  "genre_id": "9402fae1-2c08-494e-b37a-9a7e09da5795",
  "subgenre_id": "0511c9d4-4f54-4473-92b6-deef09573e10",
  "microgenre_id": "f0f0f003-1050-4caa-bff5-cbea0a66886c",
  "trope_id": "a1b2c3d4-5e6f-7890-abcd-ef1234567890",
  "tone_id": "b2c3d4e5-6f78-9012-bcde-f23456789012",
  "target_audience_id": "c3d4e5f6-7890-1234-cdef-345678901234",
  "author_id": "d4e5f6a7-8901-2345-defa-456789012345",
  "created_at": "2024-07-16T10:30:00Z"
}
```

**Note:** The plot now uses foreign key references instead of storing text values directly. To get readable names, join with the respective lookup tables.

### Sample Author Record
```json
{
  "id": "b99dc6ca-7781-46e9-a646-82c518dbcb82",
  "author_name": "J.K. Test-Author",
  "pen_name": "J.K. Test",
  "biography": "A renowned fantasy author known for creating immersive magical worlds.",
  "writing_style": "Descriptive and character-driven with rich world-building."
}
```

## API Usage

### SupabaseService Methods

```python
# Initialize service
service = SupabaseService()

# Create/get user
user = await service.create_or_get_user("user_123")

# Create session  
session = await service.create_session("session_123", "user_123")

# Save plot
plot = await service.save_plot(
    session_id="session_123",
    user_id="user_123", 
    plot_data=plot_data
)

# Save author
author = await service.save_author(
    session_id="session_123",
    user_id="user_123",
    plot_id=plot['id'],
    author_data=author_data
)

# Retrieve data
user_plots = await service.get_user_plots("user_123")
user_authors = await service.get_user_authors("user_123")
```

## Schema Migration System

### Current Migrations
- `migrations/001_initial_schema.sql` - Base schema with all 5 tables

### Adding New Tables/Features

1. Create migration:
```bash
python create_migration.py "add new feature"
```

2. Edit the generated SQL file in `migrations/`

3. Apply via Supabase CLI:
```bash
npx supabase db push
```

### Example: Adding Character Development Agent

```sql
-- Migration: 002_add_character_development_agent.sql
CREATE TABLE IF NOT EXISTS character_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plot_id UUID REFERENCES plots(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_name VARCHAR(255) NOT NULL,
    role VARCHAR(100), -- protagonist, antagonist, supporting
    personality_traits TEXT[],
    backstory TEXT,
    character_arc TEXT,
    relationships JSONB,
    physical_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_character_profiles_plot_id ON character_profiles(plot_id);
```

## Performance Notes

- All foreign keys have `ON DELETE CASCADE` for automatic cleanup
- Comprehensive indexing on frequently queried columns
- JSONB fields for flexible metadata storage
- UUIDs for globally unique identifiers
- Timestamps for audit trail and sorting

## Backup and Recovery

- Supabase handles automatic backups
- Point-in-time recovery available
- Database snapshots taken daily
- Migration files provide schema version control

## Security

- Row Level Security (RLS) can be enabled for production
- Service role key required for schema changes
- Anon key used for application access
- All connections use SSL/TLS

## Monitoring

- Supabase dashboard provides query analytics
- Index usage statistics available
- Performance insights and slow query detection
- Real-time database metrics