-- Website Versions and Assets Tables
-- Add to existing Webomat database

-- Website Versions table
CREATE TABLE IF NOT EXISTS website_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'created' CHECK (status IN ('created', 'generating', 'ready', 'failed', 'archived')),
    source_bundle_path TEXT,
    preview_image_path TEXT,
    notes TEXT,
    created_by UUID REFERENCES sellers(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(project_id, version_number)
);

-- Project Assets table
CREATE TABLE IF NOT EXISTS project_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('logo', 'photos', 'contract', 'brief', 'invoice', 'other')),
    file_path TEXT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_by UUID REFERENCES sellers(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_website_versions_project ON website_versions(project_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_website_versions_status ON website_versions(status);
CREATE INDEX IF NOT EXISTS idx_project_assets_project ON project_assets(project_id, uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_assets_type ON project_assets(type);

-- Update existing website_projects table to include version tracking
ALTER TABLE website_projects
ADD COLUMN IF NOT EXISTS latest_version_id UUID REFERENCES website_versions(id),
ADD COLUMN IF NOT EXISTS versions_count INTEGER DEFAULT 0;

-- Function to update latest_version_id and versions_count
CREATE OR REPLACE FUNCTION update_project_version_info()
RETURNS TRIGGER AS $$
BEGIN
    -- Update latest_version_id and versions_count for the project
    UPDATE website_projects
    SET
        latest_version_id = (
            SELECT id FROM website_versions
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
            ORDER BY version_number DESC
            LIMIT 1
        ),
        versions_count = (
            SELECT COUNT(*) FROM website_versions
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id)
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for website_versions table
DROP TRIGGER IF EXISTS trigger_update_project_version_info ON website_versions;
CREATE TRIGGER trigger_update_project_version_info
    AFTER INSERT OR UPDATE OR DELETE ON website_versions
    FOR EACH ROW EXECUTE FUNCTION update_project_version_info();