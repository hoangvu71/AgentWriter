-- Migration: 001_initial_schema
-- Created: 2025-07-15T14:08:40.789413
-- Description: Initial database schema

-- Multi-Agent Book Writer System Database Schema
-- Run this SQL in your Supabase SQL Editor

-- Users table
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Plots table
CREATE TABLE plots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    plot_summary TEXT NOT NULL,
    genre VARCHAR(100),
    subgenre VARCHAR(100),
    microgenre VARCHAR(100),
    trope VARCHAR(255),
    tone VARCHAR(255),
    target_audience JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Authors table
CREATE TABLE authors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plot_id UUID REFERENCES plots(id) ON DELETE CASCADE,
    author_name VARCHAR(255) NOT NULL,
    pen_name VARCHAR(255),
    biography TEXT NOT NULL,
    writing_style TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orchestrator decisions table (for analytics)
CREATE TABLE orchestrator_decisions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    routing_decision VARCHAR(50) NOT NULL,
    agents_invoked TEXT[],
    extracted_parameters JSONB,
    workflow_plan TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_plots_user_id ON plots(user_id);
CREATE INDEX idx_plots_session_id ON plots(session_id);
CREATE INDEX idx_plots_created_at ON plots(created_at);
CREATE INDEX idx_authors_user_id ON authors(user_id);
CREATE INDEX idx_authors_plot_id ON authors(plot_id);
CREATE INDEX idx_authors_created_at ON authors(created_at);
CREATE INDEX idx_orchestrator_decisions_user_id ON orchestrator_decisions(user_id);
CREATE INDEX idx_orchestrator_decisions_created_at ON orchestrator_decisions(created_at);

-- Insert sample data for testing (optional)
INSERT INTO users (user_id) VALUES ('demo_user');

-- Comments for documentation
COMMENT ON TABLE users IS 'Stores user information for the multi-agent system';
COMMENT ON TABLE sessions IS 'Tracks user sessions and conversations';
COMMENT ON TABLE plots IS 'Stores generated plot data with genre metadata';
COMMENT ON TABLE authors IS 'Stores author profiles linked to plots';
COMMENT ON TABLE orchestrator_decisions IS 'Stores AI routing decisions for analytics';

-- Grant permissions (if needed for RLS later)
-- You can enable Row Level Security (RLS) later for production
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE plots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE authors ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE orchestrator_decisions ENABLE ROW LEVEL SECURITY;