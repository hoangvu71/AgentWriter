-- Migration 005: Create proper hierarchical genre system
-- Hierarchy: Genre -> Subgenre -> Microgenre -> Trope -> Tone

-- First, backup existing data
CREATE TABLE IF NOT EXISTS migration_backup_tropes AS SELECT * FROM tropes;
CREATE TABLE IF NOT EXISTS migration_backup_tones AS SELECT * FROM tones;

-- Drop existing foreign key constraints
ALTER TABLE tropes DROP CONSTRAINT IF EXISTS tropes_category_check;
ALTER TABLE microgenres DROP CONSTRAINT IF EXISTS microgenres_subgenre_id_fkey;
ALTER TABLE subgenres DROP CONSTRAINT IF EXISTS subgenres_genre_id_fkey;

-- Update tropes table to reference microgenres
ALTER TABLE tropes ADD COLUMN IF NOT EXISTS microgenre_id UUID;
UPDATE tropes SET microgenre_id = (SELECT id FROM microgenres LIMIT 1) WHERE microgenre_id IS NULL;
ALTER TABLE tropes DROP COLUMN IF EXISTS category;

-- Update tones table to reference tropes
ALTER TABLE tones ADD COLUMN IF NOT EXISTS trope_id UUID;
UPDATE tones SET trope_id = (SELECT id FROM tropes LIMIT 1) WHERE trope_id IS NULL;

-- Add foreign key constraints for new hierarchy
ALTER TABLE subgenres ADD CONSTRAINT subgenres_genre_id_fkey 
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE;

ALTER TABLE microgenres ADD CONSTRAINT microgenres_subgenre_id_fkey 
    FOREIGN KEY (subgenre_id) REFERENCES subgenres(id) ON DELETE CASCADE;

ALTER TABLE tropes ADD CONSTRAINT tropes_microgenre_id_fkey 
    FOREIGN KEY (microgenre_id) REFERENCES microgenres(id) ON DELETE CASCADE;

ALTER TABLE tones ADD CONSTRAINT tones_trope_id_fkey 
    FOREIGN KEY (trope_id) REFERENCES tropes(id) ON DELETE CASCADE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_subgenres_genre_id ON subgenres(genre_id);
CREATE INDEX IF NOT EXISTS idx_microgenres_subgenre_id ON microgenres(subgenre_id);
CREATE INDEX IF NOT EXISTS idx_tropes_microgenre_id ON tropes(microgenre_id);
CREATE INDEX IF NOT EXISTS idx_tones_trope_id ON tones(trope_id);

-- Update any orphaned records
DELETE FROM subgenres WHERE genre_id NOT IN (SELECT id FROM genres);
DELETE FROM microgenres WHERE subgenre_id NOT IN (SELECT id FROM subgenres);
DELETE FROM tropes WHERE microgenre_id NOT IN (SELECT id FROM microgenres);
DELETE FROM tones WHERE trope_id NOT IN (SELECT id FROM tropes);