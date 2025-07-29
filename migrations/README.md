# Database Migrations

> **This file has been moved and reorganized.**
> 
> Please see the new location: **[docs/guides/database-migrations.md](../docs/guides/database-migrations.md)**
> 
> The content has been updated and integrated into the new documentation structure.

---

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

1. **Always use `IF NOT EXISTS`** for new tables and indexes
2. **Include rollback instructions** in comments (use SAFE_MIGRATION_TEMPLATE.sql)
3. **Wrap in transactions** - use BEGIN/COMMIT blocks
4. **Create backups** before destructive operations
5. **Test locally first** - validate in staging environment
6. **Keep migrations small** and focused on one change
7. **Use automated validation** - run migration validator before applying
8. **Test rollback procedures** - ensure rollbacks work correctly

## Migration Safety Tools

- `SAFE_MIGRATION_TEMPLATE.sql` - Template with safety best practices
- `scripts/migration/automated_migration_validator.py` - Validates migrations for risks
- `scripts/migration/test_migration_rollback.py` - Tests rollback procedures

## Validation Commands

```bash
# Validate all migrations for safety issues
python scripts/migration/automated_migration_validator.py migrations/

# Test rollback procedures (requires test database)
python scripts/migration/test_migration_rollback.py migrations/ "postgresql://user:pass@localhost:5432/postgres"
```
