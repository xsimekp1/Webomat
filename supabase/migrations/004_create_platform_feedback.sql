-- Migration 004: Create platform_feedback table
-- Internal feedback system for platform improvements

CREATE TABLE IF NOT EXISTS platform_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submitted_by UUID NOT NULL REFERENCES sellers(id),
    content TEXT NOT NULL,
    category VARCHAR(20) DEFAULT 'idea' CHECK (category IN ('bug', 'idea', 'ux', 'other')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'done', 'rejected')),
    admin_note TEXT,
    handled_by UUID REFERENCES sellers(id),
    handled_at TIMESTAMP WITH TIME ZONE,
    -- Metadata
    page_url TEXT, -- URL where feedback was submitted from
    user_agent TEXT,
    screenshot_url TEXT, -- Optional screenshot attachment
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_platform_feedback_submitted_by ON platform_feedback(submitted_by);
CREATE INDEX IF NOT EXISTS idx_platform_feedback_status ON platform_feedback(status);
CREATE INDEX IF NOT EXISTS idx_platform_feedback_category ON platform_feedback(category);
CREATE INDEX IF NOT EXISTS idx_platform_feedback_priority ON platform_feedback(priority);
CREATE INDEX IF NOT EXISTS idx_platform_feedback_created_at ON platform_feedback(created_at DESC);

-- Trigger for updating updated_at
CREATE OR REPLACE FUNCTION update_platform_feedback_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_platform_feedback_updated_at ON platform_feedback;
CREATE TRIGGER trigger_platform_feedback_updated_at
    BEFORE UPDATE ON platform_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_platform_feedback_timestamp();

-- Comments for documentation
COMMENT ON TABLE platform_feedback IS 'Internal feedback from users about the platform';
COMMENT ON COLUMN platform_feedback.category IS 'Type of feedback: bug, idea, ux, other';
COMMENT ON COLUMN platform_feedback.priority IS 'User-assigned priority: low, medium, high';
COMMENT ON COLUMN platform_feedback.status IS 'Processing status: open, in_progress, done, rejected';
