-- Migration 001: Enhance website_projects table
-- Adds fields for project management: deadline, budget, domain status, notes

ALTER TABLE website_projects
ADD COLUMN IF NOT EXISTS required_deadline DATE,
ADD COLUMN IF NOT EXISTS budget DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS domain_status VARCHAR(50) DEFAULT 'planned'
    CHECK (domain_status IN ('planned', 'purchased', 'deployed', 'not_needed', 'other')),
ADD COLUMN IF NOT EXISTS internal_notes TEXT,
ADD COLUMN IF NOT EXISTS client_notes TEXT;

-- Index for filtering by domain status
CREATE INDEX IF NOT EXISTS idx_website_projects_domain_status ON website_projects(domain_status);

-- Comment for documentation
COMMENT ON COLUMN website_projects.required_deadline IS 'Client-requested deadline for project delivery';
COMMENT ON COLUMN website_projects.budget IS 'Total budget for the project';
COMMENT ON COLUMN website_projects.domain_status IS 'Status of domain: planned, purchased, deployed, not_needed, other';
COMMENT ON COLUMN website_projects.internal_notes IS 'Internal notes visible only to team';
COMMENT ON COLUMN website_projects.client_notes IS 'Notes from client communication';
