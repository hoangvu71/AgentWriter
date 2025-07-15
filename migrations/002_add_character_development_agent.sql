-- Migration: 002_add_character_development_agent.sql
-- Created: 2025-07-15T14:09:36.612925
-- Description: add character development agent

-- Add your schema changes below
-- Remember to use IF NOT EXISTS for new tables
-- Use ALTER TABLE for modifications to existing tables

-- Character profiles table
CREATE TABLE IF NOT EXISTS character_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    plot_id UUID REFERENCES plots(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_name VARCHAR(255) NOT NULL,
    role VARCHAR(100), -- protagonist, antagonist, supporting
    personality_traits TEXT[],
    backstory TEXT,
    character_arc TEXT,
    relationships JSONB,
    physical_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Character dialogue samples
CREATE TABLE IF NOT EXISTS character_dialogues (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    character_id UUID REFERENCES character_profiles(id) ON DELETE CASCADE,
    dialogue_sample TEXT,
    context VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_character_profiles_plot_id ON character_profiles(plot_id);
CREATE INDEX IF NOT EXISTS idx_character_profiles_session_id ON character_profiles(session_id);
CREATE INDEX IF NOT EXISTS idx_character_profiles_user_id ON character_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_character_dialogues_character_id ON character_dialogues(character_id);
