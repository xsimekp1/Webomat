-- Add missing 'notes' column to website_projects table
-- This column is expected by the frontend code

ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Also add seller_id if it's missing (it should be nullable)
-- The project creation might also need this
ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS seller_id UUID REFERENCES sellers(id);

COMMENT ON COLUMN website_projects.notes IS 'Project notes and additional information';
COMMENT ON COLUMN website_projects.seller_id IS 'Seller who owns this project (nullable)';

COMMIT;
