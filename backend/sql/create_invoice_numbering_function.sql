-- Vytvoření funkcí pro inteligentní číslování faktur
-- Varianta A: FV-YYYY-NNN (Faktura za provize) + KOR-YYYY-NNN (Korekce)

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS get_next_commission_invoice_number(year);
DROP FUNCTION IF EXISTS get_next_correction_invoice_number(year);

-- Function: generate next commission invoice number
CREATE OR REPLACE FUNCTION get_next_commission_invoice_number(year_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    last_number INTEGER;
    next_number TEXT;
    prefix TEXT;
BEGIN
    -- Prefix: FV-YYYY (Faktura za provize)
    prefix := 'FV-' || year_param::TEXT || '-';
    
    -- Najdi poslední číslo pro daný rok
    SELECT COALESCE(
        MAX(
            CASE 
                WHEN invoice_number LIKE prefix || '%'
                THEN CAST(SUBSTRING(invoice_number FROM LENGTH(prefix) + 1) AS INTEGER)
                ELSE 0
            END
        ), 
        0
    ) INTO last_number
    FROM invoices_issued
    WHERE invoice_number LIKE prefix || '%';
    
    -- Další číslo
    next_number := prefix || LPAD((last_number + 1)::TEXT, 3, '0');
    
    RETURN next_number;
END;
$$ LANGUAGE plpgsql;

-- Function: generate next correction invoice number
CREATE OR REPLACE FUNCTION get_next_correction_invoice_number(year_param INTEGER)
RETURNS TEXT AS $$
DECLARE
    last_number INTEGER;
    next_number TEXT;
    prefix TEXT;
BEGIN
    -- Prefix: KOR-YYYY (Korekce)
    prefix := 'KOR-' || year_param::TEXT || '-';
    
    -- Najdi poslední číslo pro daný rok
    SELECT COALESCE(
        MAX(
            CASE 
                WHEN invoice_number LIKE prefix || '%'
                THEN CAST(SUBSTRING(invoice_number FROM LENGTH(prefix) + 1) AS INTEGER)
                ELSE 0
            END
        ), 
        0
    ) INTO last_number
    FROM invoices_issued
    WHERE invoice_number LIKE prefix || '%';
    
    -- Další číslo
    next_number := prefix || LPAD((last_number + 1)::TEXT, 3, '0');
    
    RETURN next_number;
END;
$$ LANGUAGE plpgsql;

-- Indexy pro lepší výkon
CREATE INDEX IF NOT EXISTS idx_invoices_issued_number_year ON invoices_issued(invoice_number, issue_date);
CREATE INDEX IF NOT EXISTS idx_invoices_issued_payment_type ON invoices_issued(payment_type);