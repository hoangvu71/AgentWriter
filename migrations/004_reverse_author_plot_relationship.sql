-- Migration 004: Reverse author-plot relationship
-- Change from: authors.plot_id -> plots.author_id
-- This allows one author to have multiple plots (correct relationship)

-- Step 1: Add author_id column to plots table
ALTER TABLE plots ADD COLUMN author_id UUID REFERENCES authors(id) ON DELETE SET NULL;

-- Step 2: Migrate existing relationships
-- If there are existing author-plot relationships, preserve them
UPDATE plots 
SET author_id = (
    SELECT id 
    FROM authors 
    WHERE authors.plot_id = plots.id 
    LIMIT 1
)
WHERE EXISTS (
    SELECT 1 
    FROM authors 
    WHERE authors.plot_id = plots.id
);

-- Step 3: Remove the old plot_id column from authors table
ALTER TABLE authors DROP COLUMN plot_id;

-- Step 4: Add index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_plots_author_id ON plots(author_id);

-- Drop the old index that's no longer needed
DROP INDEX IF EXISTS idx_authors_plot_id;

-- Step 5: Update any sample data if needed
-- (This will be handled in code migration script)