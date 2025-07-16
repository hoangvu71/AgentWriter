-- Migration 007: Iterative Improvement System
-- Tracks improvement sessions, iterations, critiques, enhancements, and scores

-- Improvement Sessions Table
CREATE TABLE IF NOT EXISTS improvement_sessions (
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
CREATE TABLE IF NOT EXISTS iterations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    improvement_session_id UUID REFERENCES improvement_sessions(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Critiques Table
CREATE TABLE IF NOT EXISTS critiques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID REFERENCES iterations(id) ON DELETE CASCADE,
    critique_json JSONB NOT NULL,
    agent_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enhancements Table
CREATE TABLE IF NOT EXISTS enhancements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID REFERENCES iterations(id) ON DELETE CASCADE,
    enhanced_content TEXT NOT NULL,
    changes_made JSONB NOT NULL,
    rationale TEXT NOT NULL,
    confidence_score INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scores Table
CREATE TABLE IF NOT EXISTS scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iteration_id UUID REFERENCES iterations(id) ON DELETE CASCADE,
    overall_score DECIMAL(3,1) NOT NULL,
    category_scores JSONB NOT NULL,
    score_rationale TEXT NOT NULL,
    improvement_trajectory VARCHAR NOT NULL,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_improvement_sessions_user_id ON improvement_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_improvement_sessions_session_id ON improvement_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_improvement_sessions_status ON improvement_sessions(status);
CREATE INDEX IF NOT EXISTS idx_iterations_improvement_session_id ON iterations(improvement_session_id);
CREATE INDEX IF NOT EXISTS idx_critiques_iteration_id ON critiques(iteration_id);
CREATE INDEX IF NOT EXISTS idx_enhancements_iteration_id ON enhancements(iteration_id);
CREATE INDEX IF NOT EXISTS idx_scores_iteration_id ON scores(iteration_id);

-- Helper view for improvement session summary
CREATE OR REPLACE VIEW improvement_session_summary AS
SELECT 
    s.id,
    s.user_id,
    s.session_id,
    s.content_type,
    s.status,
    s.created_at,
    s.completed_at,
    s.completion_reason,
    s.final_score,
    s.target_score,
    s.max_iterations,
    COUNT(DISTINCT i.id) as total_iterations,
    MIN(sc.overall_score) as min_score,
    MAX(sc.overall_score) as max_score,
    MAX(sc.overall_score) - MIN(sc.overall_score) as score_improvement
FROM improvement_sessions s
LEFT JOIN iterations i ON s.id = i.improvement_session_id
LEFT JOIN scores sc ON i.id = sc.iteration_id
GROUP BY s.id;

-- Sample data for testing
INSERT INTO improvement_sessions (user_id, session_id, original_content, content_type, status)
VALUES 
    ('test_user', 'test_session', 'A young boy discovers magic powers and must save the world.', 'plot_summary', 'in_progress');

-- Add comment for documentation
COMMENT ON TABLE improvement_sessions IS 'Tracks iterative improvement sessions for content enhancement';
COMMENT ON TABLE iterations IS 'Individual iterations within an improvement session';
COMMENT ON TABLE critiques IS 'Critique feedback for each iteration';
COMMENT ON TABLE enhancements IS 'Enhanced content based on critique feedback';
COMMENT ON TABLE scores IS 'Scoring evaluations for each iteration';