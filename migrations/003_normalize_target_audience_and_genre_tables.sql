-- Migration: 003_normalize_target_audience_and_genre_tables.sql
-- Created: 2025-07-15T14:48:43.113176
-- Description: normalize target audience and genre tables

-- Add your schema changes below
-- Remember to use IF NOT EXISTS for new tables
-- Use ALTER TABLE for modifications to existing tables

-- Create normalized target audience table
CREATE TABLE IF NOT EXISTS target_audiences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    age_group VARCHAR(50) NOT NULL, -- Young Adult, Adult, Teen, etc.
    gender VARCHAR(50), -- Male, Female, All, Non-binary, etc.
    sexual_orientation VARCHAR(50), -- Heterosexual, LGBTQ+, All, etc.
    interests TEXT[], -- Array of interests like ["Magic", "Adventure", "Romance"]
    description TEXT, -- Human-readable description
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create genres table (main categories)
CREATE TABLE IF NOT EXISTS genres (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- Fantasy, Sci-Fi, Romance, Mystery, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create subgenres table (linked to main genres)
CREATE TABLE IF NOT EXISTS subgenres (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    genre_id UUID REFERENCES genres(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- LitRPG, Space Opera, Cozy Mystery, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(genre_id, name) -- Prevent duplicate subgenres within same genre
);

-- Create microgenres table (specific niches)
CREATE TABLE IF NOT EXISTS microgenres (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    subgenre_id UUID REFERENCES subgenres(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- Zombie Apocalypse, Time Travel, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(subgenre_id, name) -- Prevent duplicate microgenres within same subgenre
);

-- Create tropes table (story patterns/themes)
CREATE TABLE IF NOT EXISTS tropes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL, -- Chosen One, Enemies to Lovers, etc.
    description TEXT,
    category VARCHAR(100), -- Character, Plot, Romance, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create tones table (story mood/atmosphere)
CREATE TABLE IF NOT EXISTS tones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- Dark, Humorous, Realistic, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add new foreign key columns to plots table
ALTER TABLE plots ADD COLUMN IF NOT EXISTS target_audience_id UUID REFERENCES target_audiences(id);
ALTER TABLE plots ADD COLUMN IF NOT EXISTS genre_id UUID REFERENCES genres(id);
ALTER TABLE plots ADD COLUMN IF NOT EXISTS subgenre_id UUID REFERENCES subgenres(id);
ALTER TABLE plots ADD COLUMN IF NOT EXISTS microgenre_id UUID REFERENCES microgenres(id);
ALTER TABLE plots ADD COLUMN IF NOT EXISTS trope_id UUID REFERENCES tropes(id);
ALTER TABLE plots ADD COLUMN IF NOT EXISTS tone_id UUID REFERENCES tones(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_target_audiences_age_group ON target_audiences(age_group);
CREATE INDEX IF NOT EXISTS idx_target_audiences_gender ON target_audiences(gender);
CREATE INDEX IF NOT EXISTS idx_genres_name ON genres(name);
CREATE INDEX IF NOT EXISTS idx_subgenres_genre_id ON subgenres(genre_id);
CREATE INDEX IF NOT EXISTS idx_subgenres_name ON subgenres(name);
CREATE INDEX IF NOT EXISTS idx_microgenres_subgenre_id ON microgenres(subgenre_id);
CREATE INDEX IF NOT EXISTS idx_microgenres_name ON microgenres(name);
CREATE INDEX IF NOT EXISTS idx_tropes_name ON tropes(name);
CREATE INDEX IF NOT EXISTS idx_tropes_category ON tropes(category);
CREATE INDEX IF NOT EXISTS idx_tones_name ON tones(name);

-- Create indexes on new foreign keys in plots table
CREATE INDEX IF NOT EXISTS idx_plots_target_audience_id ON plots(target_audience_id);
CREATE INDEX IF NOT EXISTS idx_plots_genre_id ON plots(genre_id);
CREATE INDEX IF NOT EXISTS idx_plots_subgenre_id ON plots(subgenre_id);
CREATE INDEX IF NOT EXISTS idx_plots_microgenre_id ON plots(microgenre_id);
CREATE INDEX IF NOT EXISTS idx_plots_trope_id ON plots(trope_id);
CREATE INDEX IF NOT EXISTS idx_plots_tone_id ON plots(tone_id);

-- Insert some common data to get started
INSERT INTO genres (name, description) VALUES 
    ('Fantasy', 'Stories with magical or supernatural elements'),
    ('Science Fiction', 'Stories based on future scientific and technological advances'),
    ('Romance', 'Stories focused on relationships and romantic love'),
    ('Mystery', 'Stories involving puzzles, crimes, or unexplained events'),
    ('Thriller', 'Stories designed to hold readers in suspense'),
    ('Horror', 'Stories intended to frighten, unsettle, or create suspense')
ON CONFLICT (name) DO NOTHING;

INSERT INTO target_audiences (age_group, gender, sexual_orientation, interests, description) VALUES 
    ('Young Adult', 'All', 'All', ARRAY['Adventure', 'Coming of Age'], 'Teens and young adults seeking adventure and growth stories'),
    ('Adult', 'Female', 'Heterosexual', ARRAY['Romance', 'Drama'], 'Adult women interested in romantic stories'),
    ('Adult', 'Male', 'Heterosexual', ARRAY['Action', 'Adventure'], 'Adult men interested in action and adventure'),
    ('Adult', 'All', 'LGBTQ+', ARRAY['Romance', 'Identity'], 'LGBTQ+ adults seeking representation in fiction')
ON CONFLICT DO NOTHING;

INSERT INTO tropes (name, description, category) VALUES 
    ('Chosen One', 'A character destined to save the world or fulfill a prophecy', 'Character'),
    ('Enemies to Lovers', 'Romantic relationship that develops between former enemies', 'Romance'),
    ('Survive and Family', 'Characters fighting to survive while protecting family', 'Plot'),
    ('Fish Out of Water', 'Character placed in unfamiliar environment', 'Character'),
    ('The Mentor', 'Wise guide who teaches the protagonist', 'Character')
ON CONFLICT (name) DO NOTHING;

INSERT INTO tones (name, description) VALUES 
    ('Dark', 'Serious, gritty, or pessimistic atmosphere'),
    ('Humorous', 'Light-hearted, funny, comedic elements'),
    ('Realistic', 'Grounded, believable, authentic feeling'),
    ('Heroic', 'Noble, inspiring, uplifting tone'),
    ('Mysterious', 'Enigmatic, puzzling, secretive atmosphere')
ON CONFLICT (name) DO NOTHING;

