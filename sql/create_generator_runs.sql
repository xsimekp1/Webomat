-- Generator runs table for tracking website generation executions
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS generator_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Who ran it
    seller_id UUID REFERENCES sellers(id),
    seller_email VARCHAR(255),

    -- What project
    project_id UUID REFERENCES website_projects(id),
    business_id UUID REFERENCES businesses(id),
    version_id UUID REFERENCES website_versions(id),  -- Created version if any

    -- Run type and status
    run_type VARCHAR(50) NOT NULL,  -- 'dry_run', 'claude_ai', 'openai', etc.
    status VARCHAR(50) NOT NULL DEFAULT 'started',  -- 'started', 'completed', 'failed'

    -- Cost tracking
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0,  -- Cost in USD (6 decimal places for precision)
    cost_czk DECIMAL(10, 2) DEFAULT 0,  -- Cost in CZK
    model_used VARCHAR(100),  -- e.g. 'claude-3-opus', 'gpt-4', etc.

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,  -- Duration in milliseconds

    -- Request details
    prompt_summary TEXT,  -- Brief summary of what was requested
    error_message TEXT,  -- If failed, store error

    -- Metadata
    metadata JSONB,  -- Any additional data (request params, etc.)

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_generator_runs_seller ON generator_runs(seller_id);
CREATE INDEX IF NOT EXISTS idx_generator_runs_project ON generator_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_generator_runs_business ON generator_runs(business_id);
CREATE INDEX IF NOT EXISTS idx_generator_runs_created_at ON generator_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generator_runs_run_type ON generator_runs(run_type);
CREATE INDEX IF NOT EXISTS idx_generator_runs_status ON generator_runs(status);

-- Comment
COMMENT ON TABLE generator_runs IS 'Tracks all website generator executions with cost and performance metrics';

-- Example run_type values:
-- 'dry_run' - Test run without AI (free)
-- 'claude_ai' - Full AI generation with Claude
-- 'openai' - Translation or other OpenAI tasks
-- 'screenshot' - Screenshot capture
