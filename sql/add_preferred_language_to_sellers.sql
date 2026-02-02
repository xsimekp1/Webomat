-- Add preferred_language column to sellers table
-- Migration: 2025-02-01_add_preferred_language_to_sellers.sql

ALTER TABLE sellers 
ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'cs' 
CHECK (preferred_language IN ('cs', 'en'));

-- Add comment for documentation
COMMENT ON COLUMN sellers.preferred_language IS 'User interface language preference (cs = Czech, en = English)';