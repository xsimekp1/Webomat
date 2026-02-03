-- Add preferred_language column to sellers table
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS preferred_language TEXT DEFAULT 'cs';

-- Update existing records to default Czech
UPDATE sellers SET preferred_language = 'cs' WHERE preferred_language IS NULL;