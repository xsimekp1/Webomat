-- Add missing price columns to website_projects table
-- These columns are required by the ProjectCreate schema

ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS price_setup DECIMAL(12, 2),
ADD COLUMN IF NOT EXISTS price_monthly DECIMAL(12, 2);

-- Add comments for documentation
COMMENT ON COLUMN website_projects.price_setup IS 'One-time setup fee for the project';
COMMENT ON COLUMN website_projects.price_monthly IS 'Monthly recurring fee for the project';

COMMIT;
