# Database Migrations Guide

> **This file has been moved and reorganized.**
> 
> Please see the new location: **[docs/guides/database-migrations.md](guides/database-migrations.md)**
> 
> The content has been updated and integrated into the new documentation structure.

---

# Database Migrations Guide

## How Claude Applies Migrations

Claude can directly apply database migrations using the Supabase CLI. This document explains the exact process and requirements.

## Prerequisites

1. **Supabase CLI**: Available via `npx supabase` (already installed)
2. **Project Linked**: Link to your Supabase project (get project reference from Supabase Dashboard)
3. **Database Password**: Required for remote operations

## Standard Migration Process

### 1. Create Migration
```bash
npx supabase migration new "description_of_changes"
```
This creates: `supabase/migrations/YYYYMMDDHHMMSS_description.sql`

### 2. Write Migration SQL
Edit the generated file with your schema changes:
```sql
-- Create tables
CREATE TABLE IF NOT EXISTS new_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- your columns here
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_new_table_field ON new_table(field);
```

### 3. Apply Migration
```bash
npx supabase db push --password "$SUPABASE_DB_PASSWORD"
```

**Important:** Set database password as environment variable:
- Add `SUPABASE_DB_PASSWORD=your_password` to `.env` file
- Get password from: Supabase Dashboard → Project Settings → Database → Database password
- **NEVER hardcode passwords in documentation or scripts**

### 4. Verify Migration
```bash
python scripts/database/check_tables.py
```
This script:
- Connects to Supabase using Python client
- Checks if tables exist
- Updates `migrations/applied_migrations.json` tracking

## Project Configuration

- **Project Reference**: `<your-project-ref>` (get from Supabase Dashboard → Settings → General)
- **Database Host**: `<your-database-host>` (get from Supabase Dashboard → Settings → Database)
- **Migration Directory**: `supabase/migrations/`
- **Tracking File**: `migrations/applied_migrations.json`

## Successful Migration Examples

### Migration 008: World Building and Characters (July 18, 2025)
```bash
# 1. Created migration file
npx supabase migration new "world_building_and_characters"

# 2. Added tables for world_building and characters with JSONB fields

# 3. Applied successfully
npx supabase db push --password "$SUPABASE_DB_PASSWORD"

# 4. Verified tables exist
python scripts/database/check_tables.py
# Result: Both tables created successfully
```

## Troubleshooting

### Authentication Errors
```
failed SASL auth (invalid SCRAM server-final-message)
```
**Solution**: Wrong password. Get correct password from Supabase Dashboard.

### Connection Refused
```
dial tcp 127.0.0.1:54322: connectex: No connection could be made
```
**Solution**: 
- If using `--local`: Start local Supabase with `npx supabase start`
- For remote: Use `npx supabase db push` (default) with password

### No Project Reference
```
Cannot find project ref. Have you run supabase link?
```
**Solution**: Link your project to Supabase. If issues persist:
```bash
npx supabase link --project-ref <your-project-ref>
```
Get your project reference from: Supabase Dashboard → Settings → General → Reference ID

## Environment Variables

Add to `.env` file for easier password management:
```bash
SUPABASE_DB_PASSWORD=your_password_here
```

Then use:
```bash
npx supabase db push --password "$SUPABASE_DB_PASSWORD"
```

## Migration Tracking

Claude maintains migration tracking in two places:
1. **Supabase's internal tracking**: Managed by CLI automatically
2. **Project tracking**: `migrations/applied_migrations.json` for consistency

The verification script updates both to keep them in sync.

## Best Practices

1. **Always use `IF NOT EXISTS`** for tables and indexes
2. **Test locally first** if possible with `--local` flag
3. **Verify after applying** with verification script
4. **Keep migrations atomic** - one logical change per migration
5. **Document complex changes** in migration comments
6. **Use descriptive migration names** for easy identification

## Commands Reference

```bash
# Create new migration
npx supabase migration new "description"

# Apply to remote database
npx supabase db push --password "PASSWORD"

# Apply to local database (if running)
npx supabase db push --local

# List applied migrations
npx supabase migration list --linked

# Verify tables exist (Python)
python scripts/database/check_tables.py

# Check Supabase status
npx supabase status
```