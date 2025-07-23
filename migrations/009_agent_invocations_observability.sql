-- Migration 009: Agent Invocations and Observability
-- Adds comprehensive tracking of agent invocations, LLM interactions, and performance metrics

-- Agent invocations table for detailed execution tracking
CREATE TABLE agent_invocations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    invocation_id VARCHAR(255) UNIQUE NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Request details
    request_content TEXT NOT NULL,
    request_context JSONB,
    
    -- Execution timing
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms NUMERIC(10,2),
    
    -- LLM interaction details
    llm_model VARCHAR(100),
    final_prompt TEXT,
    raw_response TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Tool usage details
    tool_calls JSONB DEFAULT '[]'::jsonb,
    tool_results JSONB DEFAULT '[]'::jsonb,
    
    -- Performance metrics
    latency_ms NUMERIC(10,2),
    cost_estimate NUMERIC(10,6), -- USD cost estimate
    
    -- Result details
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    response_content TEXT,
    parsed_json JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance metrics table for time-series data
CREATE TABLE performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15,6) NOT NULL,
    tags JSONB DEFAULT '{}'::jsonb,
    agent_name VARCHAR(100),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Trace events table for OpenTelemetry integration
CREATE TABLE trace_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    span_id VARCHAR(16) NOT NULL,
    parent_span_id VARCHAR(16),
    span_name VARCHAR(255) NOT NULL,
    span_kind VARCHAR(50) DEFAULT 'INTERNAL',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ns BIGINT,
    attributes JSONB DEFAULT '{}'::jsonb,
    events JSONB DEFAULT '[]'::jsonb,
    status_code VARCHAR(20) DEFAULT 'OK',
    status_message TEXT,
    resource_attributes JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_agent_invocations_agent_name ON agent_invocations(agent_name);
CREATE INDEX idx_agent_invocations_user_id ON agent_invocations(user_id);
CREATE INDEX idx_agent_invocations_session_id ON agent_invocations(session_id);
CREATE INDEX idx_agent_invocations_start_time ON agent_invocations(start_time);
CREATE INDEX idx_agent_invocations_success ON agent_invocations(success);
CREATE INDEX idx_agent_invocations_duration ON agent_invocations(duration_ms);

CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_agent ON performance_metrics(agent_name);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_performance_metrics_tags ON performance_metrics USING GIN (tags);

CREATE INDEX idx_trace_events_trace_id ON trace_events(trace_id);
CREATE INDEX idx_trace_events_span_id ON trace_events(span_id);
CREATE INDEX idx_trace_events_parent_span_id ON trace_events(parent_span_id);
CREATE INDEX idx_trace_events_span_name ON trace_events(span_name);
CREATE INDEX idx_trace_events_start_time ON trace_events(start_time);

-- Comments for documentation
COMMENT ON TABLE agent_invocations IS 'Detailed tracking of individual agent executions with LLM interactions and performance metrics';
COMMENT ON TABLE performance_metrics IS 'Time-series performance metrics for agents, tools, and system components';
COMMENT ON TABLE trace_events IS 'OpenTelemetry trace events for distributed tracing and debugging';

COMMENT ON COLUMN agent_invocations.invocation_id IS 'Unique identifier for this specific agent invocation';
COMMENT ON COLUMN agent_invocations.final_prompt IS 'The exact prompt sent to the LLM after all templating and context injection';
COMMENT ON COLUMN agent_invocations.raw_response IS 'The unprocessed response from the LLM before any parsing';
COMMENT ON COLUMN agent_invocations.cost_estimate IS 'Estimated API cost in USD based on token usage and model pricing';
COMMENT ON COLUMN agent_invocations.tool_calls IS 'JSON array of tool calls made during this invocation';
COMMENT ON COLUMN agent_invocations.tool_results IS 'JSON array of tool results returned during this invocation';

COMMENT ON COLUMN performance_metrics.tags IS 'Key-value pairs for metric dimensions (agent, model, tool, etc.)';
COMMENT ON COLUMN performance_metrics.metric_value IS 'Numeric value of the metric (latency, tokens, cost, etc.)';

COMMENT ON COLUMN trace_events.trace_id IS 'OpenTelemetry trace ID for correlating spans across services';
COMMENT ON COLUMN trace_events.span_id IS 'OpenTelemetry span ID for this specific operation';
COMMENT ON COLUMN trace_events.attributes IS 'Span attributes as key-value pairs';
COMMENT ON COLUMN trace_events.events IS 'Array of span events with timestamps and attributes';

-- Enable Row Level Security for production
-- ALTER TABLE agent_invocations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trace_events ENABLE ROW LEVEL SECURITY;