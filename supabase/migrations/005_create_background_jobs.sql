-- Migration 005: Create background_jobs table
-- Simple DB-polling job queue for async tasks (screenshots, deployments)

CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN (
        'screenshot_capture',
        'deploy_version',
        'undeploy_version',
        'generate_thumbnail',
        'send_notification',
        'cleanup_expired_links'
    )),
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending',
        'processing',
        'completed',
        'failed',
        'cancelled'
    )),
    priority INTEGER DEFAULT 0, -- Higher = more urgent
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    result JSONB,
    error_message TEXT,
    -- Scheduling
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    -- Related entities
    related_version_id UUID REFERENCES website_versions(id) ON DELETE SET NULL,
    related_project_id UUID REFERENCES website_projects(id) ON DELETE SET NULL,
    -- Worker tracking
    worker_id VARCHAR(100), -- Identifier of worker processing this job
    locked_until TIMESTAMP WITH TIME ZONE, -- Lock expiration for job claiming
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient job polling
CREATE INDEX IF NOT EXISTS idx_background_jobs_pending
    ON background_jobs(scheduled_for, priority DESC)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_background_jobs_type ON background_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_background_jobs_related_version ON background_jobs(related_version_id);
CREATE INDEX IF NOT EXISTS idx_background_jobs_locked ON background_jobs(locked_until) WHERE status = 'processing';

-- Function to claim next available job (with locking)
CREATE OR REPLACE FUNCTION claim_next_job(
    p_job_types VARCHAR(50)[],
    p_worker_id VARCHAR(100),
    p_lock_duration INTERVAL DEFAULT INTERVAL '5 minutes'
)
RETURNS TABLE (
    job_id UUID,
    job_type VARCHAR(50),
    payload JSONB,
    attempts INTEGER
) AS $$
DECLARE
    v_job_id UUID;
BEGIN
    -- Find and lock the next available job
    SELECT j.id INTO v_job_id
    FROM background_jobs j
    WHERE j.status = 'pending'
      AND j.job_type = ANY(p_job_types)
      AND j.scheduled_for <= NOW()
      AND j.attempts < j.max_attempts
      AND (j.locked_until IS NULL OR j.locked_until < NOW())
    ORDER BY j.priority DESC, j.scheduled_for ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF v_job_id IS NULL THEN
        RETURN;
    END IF;

    -- Claim the job
    UPDATE background_jobs
    SET status = 'processing',
        worker_id = p_worker_id,
        locked_until = NOW() + p_lock_duration,
        started_at = COALESCE(started_at, NOW()),
        attempts = attempts + 1,
        updated_at = NOW()
    WHERE id = v_job_id;

    -- Return the job details
    RETURN QUERY
    SELECT j.id, j.job_type, j.payload, j.attempts
    FROM background_jobs j
    WHERE j.id = v_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to complete a job
CREATE OR REPLACE FUNCTION complete_job(
    p_job_id UUID,
    p_result JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE background_jobs
    SET status = 'completed',
        result = p_result,
        completed_at = NOW(),
        locked_until = NULL,
        updated_at = NOW()
    WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to fail a job
CREATE OR REPLACE FUNCTION fail_job(
    p_job_id UUID,
    p_error_message TEXT
)
RETURNS VOID AS $$
DECLARE
    v_attempts INTEGER;
    v_max_attempts INTEGER;
BEGIN
    SELECT attempts, max_attempts INTO v_attempts, v_max_attempts
    FROM background_jobs
    WHERE id = p_job_id;

    IF v_attempts >= v_max_attempts THEN
        -- Permanently failed
        UPDATE background_jobs
        SET status = 'failed',
            error_message = p_error_message,
            completed_at = NOW(),
            locked_until = NULL,
            updated_at = NOW()
        WHERE id = p_job_id;
    ELSE
        -- Retry later (exponential backoff)
        UPDATE background_jobs
        SET status = 'pending',
            error_message = p_error_message,
            locked_until = NULL,
            scheduled_for = NOW() + (INTERVAL '1 minute' * POWER(2, v_attempts)),
            updated_at = NOW()
        WHERE id = p_job_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to enqueue a new job
CREATE OR REPLACE FUNCTION enqueue_job(
    p_job_type VARCHAR(50),
    p_payload JSONB DEFAULT '{}',
    p_priority INTEGER DEFAULT 0,
    p_scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    p_related_version_id UUID DEFAULT NULL,
    p_related_project_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_job_id UUID;
BEGIN
    INSERT INTO background_jobs (
        job_type, payload, priority, scheduled_for,
        related_version_id, related_project_id
    )
    VALUES (
        p_job_type, p_payload, p_priority, p_scheduled_for,
        p_related_version_id, p_related_project_id
    )
    RETURNING id INTO v_job_id;

    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE background_jobs IS 'Simple DB-polling job queue for async tasks';
COMMENT ON FUNCTION claim_next_job IS 'Atomically claim the next available job for processing';
COMMENT ON FUNCTION complete_job IS 'Mark a job as successfully completed';
COMMENT ON FUNCTION fail_job IS 'Mark a job as failed with optional retry';
COMMENT ON FUNCTION enqueue_job IS 'Add a new job to the queue';
