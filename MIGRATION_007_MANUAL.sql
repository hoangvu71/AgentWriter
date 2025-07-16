-- Migration 007: Iterative Improvement System
-- Copy and paste this ENTIRE block into Supabase SQL Editor

-- Improvement Sessions Table
CREATE TABLE improvement_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    original_content TEXT NOT NULL,
    content_type VARCHAR NOT NULL,
    target_score DECIMAL(3,1) DEFAULT 9.5,
    max_iterations INTEGER DEFAULT 4,
    status VARCHAR DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    completion_reason VARCHAR,
    final_content TEXT,
    final_score DECIMAL(3,1)
);

-- Iterations Table
CREATE TABLE iterations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    improvement_session_id UUID REFERENCES improvement_sessions(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Critiques Table
CREATE TABLE critiques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID REFERENCES iterations(id) ON DELETE CASCADE,
    critique_json JSONB NOT NULL,
    agent_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enhancements Table
CREATE TABLE enhancements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID REFERENCES iterations(id) ON DELETE CASCADE,
    enhanced_content TEXT NOT NULL,
    changes_made JSONB NOT NULL,
    rationale TEXT NOT NULL,
    confidence_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scores Table
CREATE TABLE scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID REFERENCES iterations(id) ON DELETE CASCADE,
    overall_score DECIMAL(3,1) NOT NULL,
    category_scores JSONB NOT NULL,
    score_rationale TEXT NOT NULL,
    improvement_trajectory VARCHAR NOT NULL,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_improvement_sessions_user_id ON improvement_sessions(user_id);
CREATE INDEX idx_improvement_sessions_session_id ON improvement_sessions(session_id);
CREATE INDEX idx_improvement_sessions_status ON improvement_sessions(status);
CREATE INDEX idx_iterations_improvement_session_id ON iterations(improvement_session_id);
CREATE INDEX idx_critiques_iteration_id ON critiques(iteration_id);
CREATE INDEX idx_enhancements_iteration_id ON enhancements(iteration_id);
CREATE INDEX idx_scores_iteration_id ON scores(iteration_id);

-- Test data
INSERT INTO improvement_sessions (user_id, session_id, original_content, content_type, status)
VALUES ('test_user', 'test_session', 'A young boy discovers magic powers.', 'plot_summary', 'in_progress');