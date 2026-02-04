-- Add contact_name field to businesses table
-- Migration for single contact person field instead of first_name + last_name

ALTER TABLE businesses 
ADD COLUMN contact_name VARCHAR(255) NULL;

-- Create comment explaining the field purpose
COMMENT ON COLUMN businesses.contact_name IS 'Kontaktní osoba (jedno pole pro jméno a příjmení)';

-- Optional: Create index for better performance on contact searches
CREATE INDEX IF NOT EXISTS idx_businesses_contact_name ON businesses(contact_name);

-- Note: Keep contact_person field for backward compatibility
-- Frontend can gradually migrate from contact_person to contact_name