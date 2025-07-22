-- Migration 005: Create proper hierarchical genre system (FIXED VERSION)
-- Hierarchy: Genre -> Subgenre -> Microgenre -> Trope -> Tone
-- 
-- CRITICAL FIX: Preserve existing data relationships by setting NULL 
-- instead of forcing arbitrary assignments

-- First, backup existing data
CREATE TABLE IF NOT EXISTS migration_backup_tropes AS SELECT * FROM tropes;
CREATE TABLE IF NOT EXISTS migration_backup_tones AS SELECT * FROM tones;

-- Drop existing foreign key constraints
ALTER TABLE tropes DROP CONSTRAINT IF EXISTS tropes_category_check;
ALTER TABLE microgenres DROP CONSTRAINT IF EXISTS microgenres_subgenre_id_fkey;
ALTER TABLE subgenres DROP CONSTRAINT IF EXISTS subgenres_genre_id_fkey;

-- Update tropes table to reference microgenres
ALTER TABLE tropes ADD COLUMN IF NOT EXISTS microgenre_id UUID;
-- FIXED: Leave as NULL instead of forcing arbitrary assignment
-- Original faulty line: UPDATE tropes SET microgenre_id = (SELECT id FROM microgenres LIMIT 1) WHERE microgenre_id IS NULL;
-- Fixed approach: Leave existing tropes with NULL microgenre_id for manual mapping later
-- This preserves data integrity until proper mapping can be established

ALTER TABLE tropes DROP COLUMN IF EXISTS category;

-- Update tones table to reference tropes  
ALTER TABLE tones ADD COLUMN IF NOT EXISTS trope_id UUID;
-- FIXED: Leave as NULL instead of forcing arbitrary assignment
-- Original faulty line: UPDATE tones SET trope_id = (SELECT id FROM tropes LIMIT 1) WHERE trope_id IS NULL;
-- Fixed approach: Leave existing tones with NULL trope_id for manual mapping later
-- This preserves data integrity until proper mapping can be established

-- Add foreign key constraints for new hierarchy (allowing NULL values)
ALTER TABLE subgenres ADD CONSTRAINT subgenres_genre_id_fkey 
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE;

ALTER TABLE microgenres ADD CONSTRAINT microgenres_subgenre_id_fkey 
    FOREIGN KEY (subgenre_id) REFERENCES subgenres(id) ON DELETE CASCADE;

-- Allow NULL microgenre_id for existing tropes that haven't been mapped yet
ALTER TABLE tropes ADD CONSTRAINT tropes_microgenre_id_fkey 
    FOREIGN KEY (microgenre_id) REFERENCES microgenres(id) ON DELETE SET NULL;

-- Allow NULL trope_id for existing tones that haven't been mapped yet  
ALTER TABLE tones ADD CONSTRAINT tones_trope_id_fkey 
    FOREIGN KEY (trope_id) REFERENCES tropes(id) ON DELETE SET NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_subgenres_genre_id ON subgenres(genre_id);
CREATE INDEX IF NOT EXISTS idx_microgenres_subgenre_id ON microgenres(subgenre_id);
CREATE INDEX IF NOT EXISTS idx_tropes_microgenre_id ON tropes(microgenre_id);
CREATE INDEX IF NOT EXISTS idx_tones_trope_id ON tones(trope_id);

-- FIXED: Remove the dangerous orphan deletion
-- Original faulty lines that would delete valid data:
-- DELETE FROM subgenres WHERE genre_id NOT IN (SELECT id FROM genres);
-- DELETE FROM microgenres WHERE subgenre_id NOT IN (SELECT id FROM subgenres);  
-- DELETE FROM tropes WHERE microgenre_id NOT IN (SELECT id FROM microgenres);
-- DELETE FROM tones WHERE trope_id NOT IN (SELECT id FROM tropes);
--
-- Fixed approach: Only delete records that are genuinely orphaned due to missing parent records
-- This should be done carefully and only if necessary:

-- Only delete subgenres that reference non-existent genres
DELETE FROM subgenres WHERE genre_id IS NOT NULL AND genre_id NOT IN (SELECT id FROM genres);

-- Only delete microgenres that reference non-existent subgenres  
DELETE FROM microgenres WHERE subgenre_id IS NOT NULL AND subgenre_id NOT IN (SELECT id FROM subgenres);

-- Do NOT delete tropes/tones with NULL foreign keys - they're unmapped, not orphaned
-- Only delete if they reference records that don't exist:
DELETE FROM tropes WHERE microgenre_id IS NOT NULL AND microgenre_id NOT IN (SELECT id FROM microgenres);
DELETE FROM tones WHERE trope_id IS NOT NULL AND trope_id NOT IN (SELECT id FROM tropes);

-- Add helpful comments for future reference
COMMENT ON COLUMN tropes.microgenre_id IS 'Foreign key to microgenres. NULL for existing tropes not yet mapped to hierarchy.';
COMMENT ON COLUMN tones.trope_id IS 'Foreign key to tropes. NULL for existing tones not yet mapped to hierarchy.';

-- Create a view to show unmapped records that need manual attention
CREATE OR REPLACE VIEW unmapped_hierarchical_data AS
SELECT 
    'trope' as record_type,
    tropes.id,
    tropes.name,
    'microgenre_id is NULL' as mapping_needed
FROM tropes 
WHERE microgenre_id IS NULL

UNION ALL

SELECT 
    'tone' as record_type,
    tones.id,
    tones.name,
    'trope_id is NULL' as mapping_needed  
FROM tones
WHERE trope_id IS NULL;

COMMENT ON VIEW unmapped_hierarchical_data IS 'Shows tropes and tones that need manual mapping to the hierarchical genre system.';