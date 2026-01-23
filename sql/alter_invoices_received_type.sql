-- Add invoice_type to invoices_received
-- Run this in Supabase SQL Editor

-- Typ přijaté faktury:
-- commission: Faktura od obchodníka za provize
-- service: Faktura za služby (AI, hosting, apod.)
-- other: Ostatní faktury

ALTER TABLE invoices_received
ADD COLUMN invoice_type VARCHAR(20) DEFAULT 'commission';

-- Volitelně: přidat vendor_name pro faktury za služby
ALTER TABLE invoices_received
ADD COLUMN vendor_name VARCHAR(255);

-- Komentář
COMMENT ON COLUMN invoices_received.invoice_type IS 'Typ faktury: commission (provize od obchodníka), service (služby třetích stran), other';
COMMENT ON COLUMN invoices_received.vendor_name IS 'Název dodavatele (pro faktury za služby, ne od obchodníků)';

-- Index pro filtrování podle typu
CREATE INDEX IF NOT EXISTS idx_inv_received_type ON invoices_received(invoice_type);
