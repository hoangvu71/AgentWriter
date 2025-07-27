-- Data Mapping Helper for Migration 005
-- Use this script AFTER running the fixed migration to manually map existing data
-- This ensures semantic integrity is preserved

-- Example mappings (customize based on your actual data)
-- These are just examples - you need to analyze your actual data and create proper mappings

-- Example: Map common fantasy tropes to appropriate microgenres
UPDATE tropes 
SET microgenre_id = (SELECT id FROM microgenres WHERE name = 'High Fantasy' LIMIT 1)
WHERE name IN ('Chosen One', 'Dragons', 'Magic System', 'Quest', 'Dark Lord')
  AND microgenre_id IS NULL;

UPDATE tropes 
SET microgenre_id = (SELECT id FROM microgenres WHERE name = 'Urban Fantasy' LIMIT 1)  
WHERE name IN ('Vampires', 'Werewolves', 'Modern Magic', 'Hidden World')
  AND microgenre_id IS NULL;

UPDATE tropes 
SET microgenre_id = (SELECT id FROM microgenres WHERE name = 'Romance Fantasy' LIMIT 1)
WHERE name IN ('Enemies to Lovers', 'Fated Mates', 'Love Triangle') 
  AND microgenre_id IS NULL;

-- Example: Map common tones to appropriate tropes
UPDATE tones
SET trope_id = (SELECT id FROM tropes WHERE name = 'Dark Lord' LIMIT 1)
WHERE name IN ('Dark and Gritty', 'Grimdark', 'Dystopian')
  AND trope_id IS NULL;

UPDATE tones
SET trope_id = (SELECT id FROM tropes WHERE name = 'Quest' LIMIT 1)  
WHERE name IN ('Heroic', 'Epic', 'Adventure')
  AND trope_id IS NULL;

UPDATE tones
SET trope_id = (SELECT id FROM tropes WHERE name = 'Enemies to Lovers' LIMIT 1)
WHERE name IN ('Romantic', 'Tension', 'Passionate')
  AND trope_id IS NULL;

-- Query to see unmapped data that still needs attention
SELECT 'Unmapped Tropes' as category, COUNT(*) as count
FROM tropes WHERE microgenre_id IS NULL
UNION ALL
SELECT 'Unmapped Tones' as category, COUNT(*) as count  
FROM tones WHERE trope_id IS NULL;

-- Query to see specific unmapped records
SELECT * FROM unmapped_hierarchical_data ORDER BY record_type, name;