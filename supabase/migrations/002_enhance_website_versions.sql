-- Migration 002: Enhance website_versions table
-- Adds fields for HTML content, screenshots, deployment, and versioning

ALTER TABLE website_versions
ADD COLUMN IF NOT EXISTS html_content TEXT,
ADD COLUMN IF NOT EXISTS html_content_en TEXT,
ADD COLUMN IF NOT EXISTS thumbnail_url TEXT,
ADD COLUMN IF NOT EXISTS screenshot_desktop_url TEXT,
ADD COLUMN IF NOT EXISTS screenshot_mobile_url TEXT,
ADD COLUMN IF NOT EXISTS public_url TEXT,
ADD COLUMN IF NOT EXISTS deployment_status VARCHAR(50) DEFAULT 'none'
    CHECK (deployment_status IN ('none', 'deploying', 'deployed', 'failed', 'unpublished')),
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS deployment_platform VARCHAR(50),
ADD COLUMN IF NOT EXISTS deployment_id TEXT,
ADD COLUMN IF NOT EXISTS parent_version_id UUID REFERENCES website_versions(id),
ADD COLUMN IF NOT EXISTS generation_instructions TEXT;

-- Index for quickly finding the current version of a project
CREATE INDEX IF NOT EXISTS idx_website_versions_is_current
    ON website_versions(project_id, is_current) WHERE is_current = TRUE;

-- Index for finding versions by deployment status
CREATE INDEX IF NOT EXISTS idx_website_versions_deployment_status
    ON website_versions(deployment_status);

-- Function to ensure only one version is marked as current per project
CREATE OR REPLACE FUNCTION ensure_single_current_version()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_current = TRUE THEN
        -- Unmark all other versions as not current
        UPDATE website_versions
        SET is_current = FALSE
        WHERE project_id = NEW.project_id
          AND id != NEW.id
          AND is_current = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for ensuring single current version
DROP TRIGGER IF EXISTS trigger_ensure_single_current_version ON website_versions;
CREATE TRIGGER trigger_ensure_single_current_version
    BEFORE INSERT OR UPDATE OF is_current ON website_versions
    FOR EACH ROW
    WHEN (NEW.is_current = TRUE)
    EXECUTE FUNCTION ensure_single_current_version();

-- Comments for documentation
COMMENT ON COLUMN website_versions.html_content IS 'Full HTML content of the website version (Czech)';
COMMENT ON COLUMN website_versions.html_content_en IS 'English translation of the HTML content';
COMMENT ON COLUMN website_versions.thumbnail_url IS 'URL to small thumbnail image for list views';
COMMENT ON COLUMN website_versions.screenshot_desktop_url IS 'URL to full desktop screenshot (1920x1080)';
COMMENT ON COLUMN website_versions.screenshot_mobile_url IS 'URL to mobile screenshot (375x812)';
COMMENT ON COLUMN website_versions.public_url IS 'Public preview URL (Vercel deployment)';
COMMENT ON COLUMN website_versions.deployment_status IS 'Status: none, deploying, deployed, failed, unpublished';
COMMENT ON COLUMN website_versions.is_current IS 'Whether this is the current/active version';
COMMENT ON COLUMN website_versions.deployment_platform IS 'Platform used for deployment (vercel, cloudflare, etc.)';
COMMENT ON COLUMN website_versions.deployment_id IS 'ID from deployment platform for management';
COMMENT ON COLUMN website_versions.parent_version_id IS 'ID of version this was generated from (for A/B testing)';
COMMENT ON COLUMN website_versions.generation_instructions IS 'Instructions used to generate this version';
