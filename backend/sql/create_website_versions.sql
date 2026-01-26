-- Create website_versions table for project version control
-- This table tracks different versions of websites for each project

CREATE TABLE IF NOT EXISTS website_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'created' NOT NULL,
    source_bundle_path TEXT,
    preview_image_path TEXT,
    notes TEXT,
    created_by UUID REFERENCES sellers(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_website_versions_project_id ON website_versions(project_id);
CREATE INDEX idx_website_versions_status ON website_versions(status);
CREATE INDEX idx_website_versions_created_by ON website_versions(created_by);
CREATE INDEX idx_website_versions_created_at ON website_versions(created_at);

-- Create unique constraint for version numbers per project
CREATE UNIQUE INDEX idx_website_versions_unique_version ON website_versions(project_id, version_number);

-- Add trigger to update updated_at column
CREATE OR REPLACE FUNCTION update_website_versions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_website_versions_updated_at
    BEFORE UPDATE ON website_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_website_versions_updated_at();

-- Update website_projects table to include version tracking
ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS latest_version_id UUID REFERENCES website_versions(id),
ADD COLUMN IF NOT EXISTS versions_count INTEGER DEFAULT 0;

-- Create trigger function to update project version info
CREATE OR REPLACE FUNCTION update_project_version_info()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Update versions count and latest version when new version is created
        UPDATE website_projects 
        SET 
            versions_count = versions_count + 1,
            latest_version_id = NEW.id,
            updated_at = NOW()
        WHERE id = NEW.project_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Update latest version if status changes to 'ready'
        IF NEW.status = 'ready' AND OLD.status != 'ready' THEN
            UPDATE website_projects 
            SET latest_version_id = NEW.id, updated_at = NOW()
            WHERE id = NEW.project_id;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- Update versions count when version is deleted
        UPDATE website_projects 
        SET 
            versions_count = GREATEST(versions_count - 1, 0),
            updated_at = NOW()
        WHERE id = OLD.project_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update project version info
CREATE TRIGGER trigger_update_project_version_info
    AFTER INSERT OR UPDATE OR DELETE ON website_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_project_version_info();

-- Initialize versions count for existing projects
UPDATE website_projects 
SET versions_count = (
    SELECT COUNT(*) 
    FROM website_versions 
    WHERE website_versions.project_id = website_projects.id
)
WHERE id IN (
    SELECT project_id 
    FROM website_versions 
    GROUP BY project_id
);

COMMIT;