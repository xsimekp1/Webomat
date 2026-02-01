-- Insert/update platform billing info for PDF invoices
-- Run this in Supabase Dashboard SQL Editor

-- First ensure platform_settings table exists
CREATE TABLE IF NOT EXISTS platform_settings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key text UNIQUE NOT NULL,
    value jsonb NOT NULL,
    updated_at timestamp with time zone DEFAULT now(),
    updated_by uuid REFERENCES sellers(id)
);

-- Insert billing info (placeholder - update with real values later)
INSERT INTO platform_settings (id, key, value, updated_at)
VALUES (
    gen_random_uuid(),
    'billing_info',
    '{
        "company_name": "Webomat s.r.o.",
        "street": "Ukázková 123",
        "city": "Praha",
        "postal_code": "110 00",
        "country": "Česká republika",
        "ico": "12345678",
        "dic": "CZ12345678",
        "iban": "CZ6508000000192000145399",
        "bank_account": "1920001453/0800",
        "email": "info@webomat.cz",
        "phone": "+420 123 456 789"
    }'::jsonb,
    NOW()
)
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

-- Verify
SELECT * FROM platform_settings WHERE key = 'billing_info';
