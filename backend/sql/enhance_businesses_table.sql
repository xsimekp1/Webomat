-- Add all missing business detail fields to businesses table

-- Contact Information
ALTER TABLE businesses 
ADD COLUMN IF NOT EXISTS email VARCHAR(255),
ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255),
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS website VARCHAR(500);

-- Address Information  
ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS address_full VARCHAR(500),
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS country VARCHAR(100),
ADD COLUMN IF NOT EXISTS lat DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS lng DECIMAL(11, 8);

-- Business Details
ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS category VARCHAR(100),
ADD COLUMN IF NOT EXISTS rating DECIMAL(3, 2),
ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS price_level INTEGER,
ADD COLUMN IF NOT EXISTS types TEXT,
ADD COLUMN IF NOT EXISTS editorial_summary TEXT;

-- CRM Fields
ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS owner_seller_id UUID REFERENCES sellers(id),
ADD COLUMN IF NOT EXISTS owner_seller_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS first_contact_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_contact_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS next_follow_up_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Billing Information
ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS ico VARCHAR(8),
ADD COLUMN IF NOT EXISTS vat_id VARCHAR(20),
ADD COLUMN IF NOT EXISTS dic VARCHAR(12),
ADD COLUMN IF NOT EXISTS billing_address VARCHAR(500),
ADD COLUMN IF NOT EXISTS bank_account VARCHAR(50);

-- Notes and Status
ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS notes TEXT,
ADD COLUMN IF NOT EXISTS status_crm VARCHAR(20) DEFAULT 'new',
ADD COLUMN IF NOT EXISTS status_reason VARCHAR(255);

-- Source Information
ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS source VARCHAR(50),
ADD COLUMN IF NOT EXISTS place_id VARCHAR(255);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_businesses_owner_seller_id ON businesses(owner_seller_id);
CREATE INDEX IF NOT EXISTS idx_businesses_status_crm ON businesses(status_crm);
CREATE INDEX IF NOT EXISTS idx_businesses_next_follow_up ON businesses(next_follow_up_at);
CREATE INDEX IF NOT EXISTS idx_businesses_email ON businesses(email);
CREATE INDEX IF NOT EXISTS idx_businesses_phone ON businesses(phone);
CREATE INDEX IF NOT EXISTS idx_businesses_website ON businesses(website);
CREATE INDEX IF NOT EXISTS idx_businesses_ico ON businesses(ico);
CREATE INDEX IF NOT EXISTS idx_businesses_place_id ON businesses(place_id);

-- Add comments for documentation
COMMENT ON TABLE businesses IS 'Complete business information including contact, address, billing, and CRM data';
COMMENT ON COLUMN businesses.email IS 'Business contact email address';
COMMENT ON COLUMN businesses.contact_person IS 'Primary contact person at the business';
COMMENT ON COLUMN businesses.phone IS 'Business phone number for deduplication';
COMMENT ON COLUMN businesses.website IS 'Business website for deduplication';
COMMENT ON COLUMN businesses.ico IS 'Czech company identification number (8 digits)';
COMMENT ON COLUMN businesses.vat_id IS 'VAT identification number';
COMMENT ON COLUMN businesses.dic IS 'Czech tax identification number';
COMMENT ON COLUMN businesses.status_crm IS 'CRM pipeline status: new/calling/interested/offer_sent/won/lost/dnc';
COMMENT ON COLUMN businesses.next_follow_up_at IS 'Next follow-up date for sales activities';
COMMENT ON COLUMN businesses.owner_seller_id IS 'Assigned sales representative';
COMMENT ON COLUMN businesses.place_id IS 'Google Places ID for deduplication';