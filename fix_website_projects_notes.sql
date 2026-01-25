-- Fix for missing 'notes' column in website_projects table
-- Run this script in Supabase SQL Editor

-- Add the missing notes column
ALTER TABLE website_projects 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'website_projects' 
AND table_schema = 'public'
ORDER BY column_name;

-- Test inserting a project with notes (this should work after the column is added)
-- INSERT INTO website_projects (business_id, package, status, notes) 
-- VALUES ('test-id', 'start', 'offer', 'test notes')
-- RETURNING *;
