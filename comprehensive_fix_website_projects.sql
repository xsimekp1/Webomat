-- Comprehensive fix for website_projects table
-- Add missing columns expected by frontend
-- Run this script in Supabase SQL Editor

-- Add missing price columns
ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS price_setup DECIMAL(12, 2);

ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS price_monthly DECIMAL(12, 2);

-- Add missing notes column (if not already added)
ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Verify all columns are added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'website_projects' 
AND table_schema = 'public'
ORDER BY column_name;

-- Test inserting a project with all expected fields (commented out for safety)
-- INSERT INTO website_projects (business_id, package, status, price_setup, price_monthly, domain, notes) 
-- VALUES ('test-id', 'start', 'offer', 10000.00, 1000.00, 'test.com', 'Test project notes')
-- RETURNING *;
