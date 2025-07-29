# Database Migrations Guide

This guide explains how to create, apply, and manage database migrations for BooksWriter using both the Supabase CLI and the project's migration system.

## 🎯 Overview

BooksWriter uses a version-controlled migration system that supports both:
- **Supabase CLI migrations** - For cloud database schema changes
- **Project migration tracking** - For consistency and rollback capabilities
- **Automated validation** - Safety checks before applying changes

## 📋 Prerequisites

1. **Supabase CLI**: Available via `npx supabase` (already installed)
2. **Project Linked**: Link to your Supabase project (get project reference from Supabase Dashboard)
3. **Database Password**: Required for remote operations
4. **Python Environment**: For local validation and tracking

## 🚀 Standard Migration Process

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

## ⚙️ Project Configuration

- **Project Reference**: `<your-project-ref>` (get from Supabase Dashboard → Settings → General)
- **Database Host**: `<your-database-host>` (get from Supabase Dashboard → Settings → Database)
- **Migration Directory**: `supabase/migrations/`
- **Tracking File**: `migrations/applied_migrations.json`

## ✅ Migration Examples

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

### Example Migration Template
```sql
-- Migration: Add new feature table
-- Description: Adds support for new feature X
-- Date: YYYY-MM-DD

BEGIN;

-- Create main table
CREATE TABLE IF NOT EXISTS new_feature (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    feature_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_new_feature_user_id ON new_feature(user_id);
CREATE INDEX IF NOT EXISTS idx_new_feature_session_id ON new_feature(session_id);
CREATE INDEX IF NOT EXISTS idx_new_feature_created_at ON new_feature(created_at);

-- Add constraints
ALTER TABLE new_feature ADD CONSTRAINT chk_feature_data_not_empty 
CHECK (jsonb_typeof(feature_data) = 'object');

COMMIT;

-- Rollback instructions (for documentation):
-- DROP TABLE IF EXISTS new_feature;
```

## 🚨 Troubleshooting

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

### Foreign Key Constraint Errors
```
ERROR: insert or update on table violates foreign key constraint
```
**Solutions**:
- Ensure referenced tables exist before creating foreign keys
- Check that referenced columns have the correct data type
- Verify the migration order is correct

### Schema Conflicts
```
ERROR: relation "table_name" already exists
```
**Solutions**:
- Always use `IF NOT EXISTS` for tables and indexes
- Check existing schema before creating new objects
- Consider using `ALTER TABLE` instead of `CREATE TABLE`

## 📊 Environment Variables

Add to `.env` file for easier password management:
```bash
SUPABASE_DB_PASSWORD=your_password_here
```

Then use:
```bash
npx supabase db push --password "$SUPABASE_DB_PASSWORD"
```

## 📝 Migration Tracking

BooksWriter maintains migration tracking in two places:
1. **Supabase's internal tracking**: Managed by CLI automatically
2. **Project tracking**: `migrations/applied_migrations.json` for consistency

The verification script updates both to keep them in sync.

### Applied Migrations Format
```json
{
  "applied_migrations": [
    {
      "filename": "20250118000001_initial_schema.sql",
      "applied_at": "2025-01-18T10:30:00Z",
      "checksum": "sha256hash",
      "success": true
    }
  ],
  "last_updated": "2025-01-18T10:30:00Z"
}
```

## 🔧 Advanced Migration Techniques

### Batch Operations
```sql
-- Use transactions for atomicity
BEGIN;

-- Multiple related changes
CREATE TABLE parent_table (...);
CREATE TABLE child_table (...);
ALTER TABLE child_table ADD CONSTRAINT fk_parent ...;

COMMIT;
```

### Data Migrations
```sql
-- Schema change with data migration
BEGIN;

-- Add new column
ALTER TABLE plots ADD COLUMN new_field VARCHAR(255);

-- Migrate existing data
UPDATE plots SET new_field = 'default_value' WHERE new_field IS NULL;

-- Make column required
ALTER TABLE plots ALTER COLUMN new_field SET NOT NULL;

COMMIT;
```

### Conditional Migrations
```sql
-- Only create if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'new_table') THEN
        CREATE TABLE new_table (...);
    END IF;
END $$;
```

## 📋 Best Practices

1. **Always use `IF NOT EXISTS`** for tables and indexes
2. **Test locally first** if possible with `--local` flag
3. **Verify after applying** with verification script
4. **Keep migrations atomic** - one logical change per migration
5. **Document complex changes** in migration comments
6. **Use descriptive migration names** for easy identification
7. **Include rollback instructions** in comments
8. **Validate before applying** using automated tools

### Migration Naming Convention
```
YYYYMMDDHHMMSS_descriptive_name.sql

Examples:
20250118123000_add_user_preferences.sql
20250118124500_create_notification_system.sql
20250118130000_update_plots_schema.sql
```

## 🛠️ Migration Safety Tools

### Automated Migration Validator
```bash
# Validate all migrations for safety issues
python scripts/migration/automated_migration_validator.py migrations/

# Output:
# ✅ Migration 001: Safe
# ⚠️  Migration 002: Warning - Missing rollback instructions
# ❌ Migration 003: Error - Destructive operation without backup
```

### Rollback Testing
```bash
# Test rollback procedures (requires test database)
python scripts/migration/test_migration_rollback.py migrations/ "postgresql://user:pass@localhost:5432/postgres"
```

### Safe Migration Template
Use `migrations/SAFE_MIGRATION_TEMPLATE.sql` as a starting point:
```sql
-- SAFE MIGRATION TEMPLATE
-- Description: [Describe what this migration does]
-- Author: [Your name]
-- Date: [YYYY-MM-DD]
-- 
-- ROLLBACK INSTRUCTIONS:
-- [Provide exact SQL to rollback this migration]

BEGIN;

-- Pre-migration checks
DO $$
BEGIN
    -- Check prerequisites
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'prerequisite_table') THEN
        RAISE EXCEPTION 'Prerequisite table does not exist';
    END IF;
END $$;

-- Your migration code here
-- ...

-- Post-migration validation
DO $$
BEGIN
    -- Validate migration success
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'new_table') THEN
        RAISE EXCEPTION 'Migration failed - new table not created';
    END IF;
END $$;

COMMIT;
```

## 📚 Commands Reference

```bash
# Create new migration
npx supabase migration new "description"

# Apply to remote database
npx supabase db push --password "PASSWORD"

# Apply to local database (if running)
npx supabase db push --local

# List applied migrations
npx supabase migration list --linked

# Check migration status
npx supabase migration list

# Verify tables exist (Python)
python scripts/database/check_tables.py

# Check Supabase status
npx supabase status

# Reset local database (destructive)
npx supabase db reset --local

# Generate types from schema
npx supabase gen types typescript --local > types/database.ts
```

## 🔄 Migration Workflow Integration

### With Development
1. Create feature branch
2. Create and test migration locally
3. Apply migration to staging
4. Test application with new schema
5. Apply to production
6. Deploy application code

### With CI/CD
```yaml
# GitHub Actions example
- name: Apply migrations
  run: |
    npx supabase db push --password "${{ secrets.SUPABASE_DB_PASSWORD }}"
    python scripts/database/check_tables.py
```

## 📚 Related Documentation

- **[Database Architecture](../architecture/database.md)** - Complete database design
- **[Environment Configuration](../setup/environment.md)** - Environment setup
- **[Troubleshooting Guide](troubleshooting.md)** - Additional troubleshooting
- **[Development Workflow](development.md)** - TDD and development practices

---

This migration system provides a robust, safe, and trackable way to evolve the BooksWriter database schema while maintaining consistency across development, staging, and production environments.