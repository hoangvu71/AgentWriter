# Database Migrations

This directory contains all database schema changes for the Multi-Agent Book Writer system.

## How to Add a New Feature/Agent

1. **Create a new migration:**
   ```bash
   python create_migration.py "add character development agent"
   ```

2. **Edit the generated file** in `migrations/XXX_your_description.sql`

3. **Apply the migration:**
   - Open Supabase SQL Editor
   - Copy and paste the migration SQL
   - Click Run

4. **Track the migration** in `applied_migrations.json`

## Migration Files

- `001_initial_schema.sql` - Base schema with all core tables
- `002_add_character_development_agent.sql` - Character profiles for character development
- `003_normalize_target_audience_and_genre_tables.sql` - Normalize metadata into foreign key tables
- `004_reverse_author_plot_relationship.sql` - Fix relationship: multiple plots per author

## Example: Adding a Writing Style Agent

```sql
-- Migration: 002_add_writing_style_agent
CREATE TABLE IF NOT EXISTS writing_styles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    author_id UUID REFERENCES authors(id) ON DELETE CASCADE,
    style_name VARCHAR(255),
    style_attributes JSONB,
    example_passages TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_writing_styles_author_id ON writing_styles(author_id);
```

## Best Practices

1. Always use `IF NOT EXISTS` for new tables
2. Use `IF NOT EXISTS` for new indexes
3. Include rollback instructions in comments
4. Test locally first if possible
5. Keep migrations small and focused
