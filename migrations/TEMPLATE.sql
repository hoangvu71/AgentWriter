-- Migration: XXX_description_here
-- Created: {date}
-- Description: Brief description of changes

-- Add your schema changes below
-- Remember to use IF NOT EXISTS for new tables
-- Use ALTER TABLE for modifications

-- Example: Adding a new agent table
/*
CREATE TABLE IF NOT EXISTS agent_name (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    -- Add your columns here
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_name_session_id ON agent_name(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_name_user_id ON agent_name(user_id);
*/
