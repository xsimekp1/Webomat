-- Invoice and Ledger tables for Webomat
-- Run this in Supabase SQL Editor

-- ===========================================
-- LEDGER ENTRIES - Provizní účet obchodníků
-- ===========================================
CREATE TABLE IF NOT EXISTS ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),

    -- Type of entry
    -- commission_earned: Provize za uzavřený obchod
    -- admin_adjustment: Manuální úprava adminem (bonus/srážka)
    -- payout_reserved: Rezervace při schválení faktury
    -- payout_paid: Označení vyplacení
    entry_type VARCHAR(50) NOT NULL,

    amount DECIMAL(12, 2) NOT NULL,  -- Kladné = příjem, záporné = výdaj

    -- Reference na související entity
    related_invoice_id UUID,  -- FK přidáme později po vytvoření tabulek
    related_project_id UUID REFERENCES website_projects(id),
    related_business_id UUID REFERENCES businesses(id),

    description TEXT,
    notes TEXT,

    is_test BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES sellers(id)
);

-- Indexy pro ledger
CREATE INDEX IF NOT EXISTS idx_ledger_seller ON ledger_entries(seller_id);
CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_ledger_created ON ledger_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_test ON ledger_entries(is_test) WHERE is_test = TRUE;

COMMENT ON TABLE ledger_entries IS 'Provizní účet obchodníků - všechny pohyby';

-- ===========================================
-- INVOICES ISSUED - Vydané faktury klientům
-- (Webomat fakturuje klientovi za web)
-- ===========================================
CREATE TABLE IF NOT EXISTS invoices_issued (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Vazby
    business_id UUID NOT NULL REFERENCES businesses(id),
    project_id UUID REFERENCES website_projects(id),
    seller_id UUID REFERENCES sellers(id),  -- Obchodník, který deal uzavřel

    -- Číslo faktury
    invoice_number VARCHAR(50) NOT NULL,

    -- Datumy
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,

    -- Částky
    amount_without_vat DECIMAL(12, 2) NOT NULL,
    vat_rate DECIMAL(5, 2) DEFAULT 21.00,
    vat_amount DECIMAL(12, 2),
    amount_total DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',

    -- Typ platby
    payment_type VARCHAR(20) DEFAULT 'setup',  -- setup, monthly, other

    -- Stav faktury
    -- draft: Koncept
    -- issued: Vydaná (odeslána klientovi)
    -- paid: Zaplacená
    -- overdue: Po splatnosti
    -- cancelled: Stornovaná
    status VARCHAR(20) DEFAULT 'draft',

    -- Text faktury
    description TEXT,

    -- PDF
    pdf_path TEXT,

    -- Variabilní symbol
    variable_symbol VARCHAR(20),

    -- Odeslání účetní
    sent_to_accountant BOOLEAN DEFAULT FALSE,
    sent_to_accountant_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES sellers(id),

    CONSTRAINT unique_invoice_issued_number UNIQUE (invoice_number)
);

-- Indexy pro vydané faktury klientům
CREATE INDEX IF NOT EXISTS idx_inv_issued_business ON invoices_issued(business_id);
CREATE INDEX IF NOT EXISTS idx_inv_issued_seller ON invoices_issued(seller_id);
CREATE INDEX IF NOT EXISTS idx_inv_issued_status ON invoices_issued(status);
CREATE INDEX IF NOT EXISTS idx_inv_issued_due ON invoices_issued(due_date);
CREATE INDEX IF NOT EXISTS idx_inv_issued_issue ON invoices_issued(issue_date DESC);

COMMENT ON TABLE invoices_issued IS 'Vydané faktury klientům za weby';

-- ===========================================
-- INVOICES RECEIVED - Přijaté faktury od obchodníků
-- (obchodník fakturuje Webomatu za provize)
-- ===========================================
CREATE TABLE IF NOT EXISTS invoices_received (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Obchodník, který fakturuje
    seller_id UUID NOT NULL REFERENCES sellers(id),

    -- Číslo faktury (od obchodníka)
    invoice_number VARCHAR(50) NOT NULL,

    -- Datumy
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    period_from DATE,  -- Období, za které se fakturuje
    period_to DATE,

    -- Částky
    amount_total DECIMAL(12, 2) NOT NULL,
    amount_to_payout DECIMAL(12, 2),  -- Může být menší než total
    currency VARCHAR(3) DEFAULT 'CZK',

    -- Stav faktury
    -- draft: Koncept (obchodník připravuje)
    -- submitted: Odesláno ke schválení
    -- approved: Schváleno adminem
    -- paid: Vyplaceno
    -- rejected: Zamítnuto
    status VARCHAR(20) DEFAULT 'draft',

    -- Důvod zamítnutí
    rejected_reason TEXT,

    -- Text faktury (editovatelný obchodníkem)
    description_text TEXT,

    -- PDF
    pdf_path TEXT,

    -- Testovací faktura
    is_test BOOLEAN DEFAULT FALSE,

    -- Schvalování
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES sellers(id),
    paid_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_invoice_received_per_seller UNIQUE (seller_id, invoice_number)
);

-- Indexy pro přijaté faktury od obchodníků
CREATE INDEX IF NOT EXISTS idx_inv_received_seller ON invoices_received(seller_id);
CREATE INDEX IF NOT EXISTS idx_inv_received_status ON invoices_received(status);
CREATE INDEX IF NOT EXISTS idx_inv_received_test ON invoices_received(is_test) WHERE is_test = TRUE;
CREATE INDEX IF NOT EXISTS idx_inv_received_created ON invoices_received(created_at DESC);

COMMENT ON TABLE invoices_received IS 'Přijaté faktury od obchodníků za provize';

-- ===========================================
-- Přidání FK do ledger_entries
-- ===========================================
-- FK na invoices_received (pro payout_reserved a payout_paid - faktury od obchodníků)
ALTER TABLE ledger_entries
ADD CONSTRAINT fk_ledger_invoice_received
FOREIGN KEY (related_invoice_id) REFERENCES invoices_received(id);

-- ===========================================
-- PLATFORM SETTINGS - Nastavení platformy
-- (fakturační údaje Webomatu)
-- ===========================================
CREATE TABLE IF NOT EXISTS platform_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES sellers(id)
);

-- Vložení výchozích fakturačních údajů platformy
INSERT INTO platform_settings (key, value) VALUES
('billing_info', '{
    "company_name": "Webomat s.r.o.",
    "ico": "",
    "dic": "",
    "street": "",
    "city": "",
    "postal_code": "",
    "country": "CZ",
    "bank_account": "",
    "iban": "",
    "email": "",
    "phone": ""
}'::jsonb)
ON CONFLICT (key) DO NOTHING;

INSERT INTO platform_settings (key, value) VALUES
('invoice_settings', '{
    "default_due_days": 14,
    "max_due_days": 30,
    "min_payout_amount": 0,
    "min_payout_days": 30,
    "min_payout_threshold": 20000,
    "vat_rate": 21,
    "currency": "CZK",
    "invoice_number_format": "YYYY-NNNN"
}'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMENT ON TABLE platform_settings IS 'Nastavení platformy včetně fakturačních údajů';

-- ===========================================
-- Pomocné funkce
-- ===========================================

-- Funkce pro získání dalšího čísla vydané faktury (pro klienty)
CREATE OR REPLACE FUNCTION get_next_issued_invoice_number(p_year INTEGER DEFAULT NULL)
RETURNS VARCHAR AS $$
DECLARE
    v_year INTEGER;
    v_last_num INTEGER;
    v_new_num VARCHAR;
BEGIN
    v_year := COALESCE(p_year, EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER);

    SELECT COALESCE(MAX(
        CAST(SPLIT_PART(invoice_number, '-', 2) AS INTEGER)
    ), 0)
    INTO v_last_num
    FROM invoices_issued
    WHERE invoice_number LIKE v_year || '-%';

    v_new_num := v_year || '-' || LPAD((v_last_num + 1)::TEXT, 4, '0');

    RETURN v_new_num;
END;
$$ LANGUAGE plpgsql;

-- Funkce pro výpočet salda obchodníka
CREATE OR REPLACE FUNCTION get_seller_balance(p_seller_id UUID, p_include_test BOOLEAN DEFAULT FALSE)
RETURNS DECIMAL AS $$
DECLARE
    v_balance DECIMAL;
BEGIN
    SELECT COALESCE(SUM(amount), 0)
    INTO v_balance
    FROM ledger_entries
    WHERE seller_id = p_seller_id
    AND (p_include_test OR is_test = FALSE);

    RETURN v_balance;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Trigger pro automatické označení po splatnosti
-- ===========================================
CREATE OR REPLACE FUNCTION check_overdue_invoices()
RETURNS TRIGGER AS $$
BEGIN
    -- Aktualizuj vydané faktury klientům po splatnosti
    UPDATE invoices_issued
    SET status = 'overdue'
    WHERE status = 'issued'
    AND due_date < CURRENT_DATE;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger se spustí každý den (nebo můžeš volat ručně)
-- Pro automatické spouštění použij pg_cron nebo Supabase Edge Functions

COMMENT ON FUNCTION get_next_issued_invoice_number IS 'Generuje další číslo vydané faktury ve formátu YYYY-NNNN';
COMMENT ON FUNCTION get_seller_balance IS 'Vypočítá aktuální saldo obchodníka z ledgeru';
