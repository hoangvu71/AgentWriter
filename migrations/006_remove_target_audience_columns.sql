-- Migration 006: Remove interests and description columns from target_audiences table
-- Simplify target_audiences to only include core demographic fields

-- Remove interests column
ALTER TABLE target_audiences DROP COLUMN IF EXISTS interests;

-- Remove description column
ALTER TABLE target_audiences DROP COLUMN IF EXISTS description;

-- Verify the simplified table structure
-- Final target_audiences table should only have:
-- - id (UUID, Primary Key)
-- - age_group (VARCHAR)
-- - gender (VARCHAR)
-- - sexual_orientation (VARCHAR)
-- - created_at (TIMESTAMP)