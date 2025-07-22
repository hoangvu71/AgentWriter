-- SAFE MIGRATION TEMPLATE
-- Use this template for all future migrations to ensure data integrity
--
-- Migration: XXX_description_here.sql
-- Purpose: [Describe what this migration does]
-- Risk Level: [LOW|MEDIUM|HIGH] 
-- Data Impact: [NONE|ADDITIVE|TRANSFORMATIVE|DESTRUCTIVE]
-- Rollback Strategy: [Describe how to undo this migration]

-- =============================================================================
-- SAFETY CHECKS AND PREREQUISITES
-- =============================================================================

-- Verify migration hasn't already been applied
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'your_new_table'
    ) THEN
        RAISE EXCEPTION 'Migration already appears to be applied - your_new_table exists';
    END IF;
END $$;

-- Verify prerequisite tables exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'prerequisite_table'
    ) THEN
        RAISE EXCEPTION 'Prerequisite table missing - ensure previous migrations are applied';
    END IF;
END $$;

-- =============================================================================
-- TRANSACTION BOUNDARY START
-- =============================================================================

BEGIN;

-- Set error handling
SET statement_timeout = '30min';
SET lock_timeout = '5min';

-- =============================================================================
-- BACKUP EXISTING DATA (if data transformation required)
-- =============================================================================

-- Create backup table for data being modified
CREATE TABLE IF NOT EXISTS migration_backup_xxx AS 
SELECT * FROM existing_table WHERE 1=0; -- Structure only, no data yet

-- Backup data that will be modified
INSERT INTO migration_backup_xxx 
SELECT * FROM existing_table 
WHERE [conditions for data being modified];

-- Log backup creation
INSERT INTO migration_log (migration_file, operation, timestamp, details)
VALUES ('XXX_description_here.sql', 'BACKUP_CREATED', NOW(), 
        'Backed up ' || (SELECT COUNT(*) FROM migration_backup_xxx) || ' records');

-- =============================================================================
-- SCHEMA CHANGES (DDL)
-- =============================================================================

-- Add new tables
CREATE TABLE IF NOT EXISTS new_table (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Your columns here
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Foreign keys with proper cascade behavior
    parent_id UUID REFERENCES parent_table(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT new_table_name_not_empty CHECK (name != '')
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_new_table_parent_id ON new_table(parent_id);
CREATE INDEX IF NOT EXISTS idx_new_table_created_at ON new_table(created_at);

-- Add new columns to existing tables
ALTER TABLE existing_table 
ADD COLUMN IF NOT EXISTS new_column VARCHAR(255);

-- Add constraints to new columns
ALTER TABLE existing_table 
ADD CONSTRAINT existing_table_new_column_check 
CHECK (new_column IS NULL OR new_column != '');

-- =============================================================================
-- DATA TRANSFORMATION (DML) - SAFE APPROACH
-- =============================================================================

-- Method 1: Additive approach (safest)
-- Insert new data based on existing data, don't modify original

INSERT INTO new_table (name, description, parent_id)
SELECT 
    source.name,
    source.description,
    parent.id
FROM existing_table source
JOIN parent_table parent ON parent.name = source.parent_name
WHERE source.processed IS NULL; -- Only process unprocessed records

-- Method 2: Update approach (if modification required)
-- Update in batches with validation

WITH updates AS (
    SELECT 
        id,
        CASE 
            WHEN condition1 THEN 'value1'
            WHEN condition2 THEN 'value2'
            ELSE current_value
        END as new_value
    FROM existing_table
    WHERE needs_update = true
    LIMIT 1000  -- Batch processing
)
UPDATE existing_table 
SET 
    column_name = updates.new_value,
    updated_at = NOW()
FROM updates 
WHERE existing_table.id = updates.id
AND existing_table.column_name != updates.new_value; -- Only update if changed

-- Verify data transformation results
DO $$
DECLARE
    expected_count INTEGER;
    actual_count INTEGER;
BEGIN
    -- Count expected results
    SELECT COUNT(*) INTO expected_count FROM existing_table WHERE condition;
    
    -- Count actual results  
    SELECT COUNT(*) INTO actual_count FROM new_table;
    
    -- Validate transformation
    IF actual_count != expected_count THEN
        RAISE EXCEPTION 'Data transformation failed - expected % records, got %', 
                       expected_count, actual_count;
    END IF;
    
    -- Log success
    INSERT INTO migration_log (migration_file, operation, timestamp, details)
    VALUES ('XXX_description_here.sql', 'TRANSFORM_SUCCESS', NOW(), 
            'Transformed ' || actual_count || ' records successfully');
END $$;

-- =============================================================================
-- CLEANUP (DESTRUCTIVE OPERATIONS)
-- =============================================================================

-- Only perform destructive operations after validation
-- Remove old columns (only if data successfully migrated)
-- ALTER TABLE existing_table DROP COLUMN IF EXISTS old_column;

-- Remove old constraints
-- ALTER TABLE existing_table DROP CONSTRAINT IF EXISTS old_constraint;

-- Note: Keep commented until migration is verified in production
-- DROP TABLE IF EXISTS old_table;

-- =============================================================================
-- POST-MIGRATION VALIDATION
-- =============================================================================

-- Verify foreign key integrity
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM new_table n 
        LEFT JOIN parent_table p ON n.parent_id = p.id 
        WHERE n.parent_id IS NOT NULL AND p.id IS NULL
    ) THEN
        RAISE EXCEPTION 'Foreign key integrity violation detected in new_table';
    END IF;
END $$;

-- Verify data consistency
DO $$
DECLARE
    inconsistent_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO inconsistent_count 
    FROM new_table 
    WHERE [consistency check condition];
    
    IF inconsistent_count > 0 THEN
        RAISE EXCEPTION 'Data consistency check failed - % inconsistent records', 
                       inconsistent_count;
    END IF;
END $$;

-- Create monitoring view for ongoing validation
CREATE OR REPLACE VIEW migration_xxx_status AS
SELECT 
    'records_migrated' as metric,
    COUNT(*) as value
FROM new_table
UNION ALL
SELECT 
    'backup_records' as metric,
    COUNT(*) as value  
FROM migration_backup_xxx
UNION ALL
SELECT
    'integrity_violations' as metric,
    COUNT(*) as value
FROM new_table n 
LEFT JOIN parent_table p ON n.parent_id = p.id 
WHERE n.parent_id IS NOT NULL AND p.id IS NULL;

-- =============================================================================
-- COMMIT TRANSACTION
-- =============================================================================

-- Log migration completion
INSERT INTO migration_log (migration_file, operation, timestamp, details)
VALUES ('XXX_description_here.sql', 'MIGRATION_COMPLETE', NOW(), 
        'Migration completed successfully');

-- Final validation before commit
DO $$
BEGIN
    -- Perform final sanity checks
    IF NOT EXISTS (SELECT 1 FROM new_table LIMIT 1) THEN
        RAISE EXCEPTION 'Migration appears incomplete - no data in new_table';
    END IF;
    
    RAISE NOTICE 'Migration XXX_description_here.sql completed successfully';
END $$;

COMMIT;

-- =============================================================================
-- POST-COMMIT OPERATIONS
-- =============================================================================

-- Update applied migrations tracking
-- (This should be done by your migration runner, not in the migration itself)

-- =============================================================================
-- ROLLBACK INSTRUCTIONS (for manual use if needed)
-- =============================================================================

/*
ROLLBACK PROCEDURE (run only if migration needs to be undone):

BEGIN;

-- 1. Restore backed up data
INSERT INTO existing_table 
SELECT * FROM migration_backup_xxx;

-- 2. Remove new structures
DROP TABLE IF EXISTS new_table CASCADE;
DROP VIEW IF EXISTS migration_xxx_status;

-- 3. Remove new columns
ALTER TABLE existing_table DROP COLUMN IF EXISTS new_column;

-- 4. Clean up backup
DROP TABLE IF EXISTS migration_backup_xxx;

-- 5. Log rollback
INSERT INTO migration_log (migration_file, operation, timestamp, details)
VALUES ('XXX_description_here.sql', 'ROLLBACK_COMPLETE', NOW(), 
        'Migration rolled back successfully');

COMMIT;
*/

-- =============================================================================
-- MIGRATION LOG TABLE (create once, use in all migrations)
-- =============================================================================

/*
CREATE TABLE IF NOT EXISTS migration_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    migration_file VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details TEXT,
    user_name VARCHAR(100) DEFAULT current_user,
    application_name VARCHAR(100) DEFAULT current_setting('application_name')
);

CREATE INDEX IF NOT EXISTS idx_migration_log_file ON migration_log(migration_file);
CREATE INDEX IF NOT EXISTS idx_migration_log_timestamp ON migration_log(timestamp);
*/