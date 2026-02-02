-- Webomat Database Schema
-- Automatické vytvorenie všetkých tabuliek pre CRM systém

-- 1. Prodejci (sellers)
CREATE TABLE IF NOT EXISTS sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    address TEXT,
    country VARCHAR(100) DEFAULT 'Czech Republic',
    date_of_birth DATE,
    onboarded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    contract_signed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'terminated')),
    terminated_at TIMESTAMP WITH TIME ZONE,
    commission_plan_id UUID,
    default_commission_rate DECIMAL(5,4) DEFAULT 0.15,
    payout_method VARCHAR(50) DEFAULT 'bank_transfer',
    bank_account_iban VARCHAR(50),
    last_payout_at TIMESTAMP WITH TIME ZONE,
    payout_balance_due DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Firmy/Leady (businesses)
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) DEFAULT 'manual',
    place_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    ico VARCHAR(50),
    vat_id VARCHAR(50),
    address_full TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'Czech Republic',
    lat DECIMAL(10,8),
    lng DECIMAL(11,8),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    has_website BOOLEAN DEFAULT FALSE,
    rating DECIMAL(3,2),
    review_count INTEGER DEFAULT 0,
    price_level INTEGER,
    types JSONB DEFAULT '[]'::jsonb,
    editorial_summary TEXT,
    status_crm VARCHAR(50) DEFAULT 'new' CHECK (status_crm IN ('new', 'contacted', 'follow_up', 'interested', 'won', 'lost', 'do_not_contact')),
    status_reason TEXT,
    owner_seller_id UUID REFERENCES sellers(id),
    first_contact_at TIMESTAMP WITH TIME ZONE,
    last_contact_at TIMESTAMP WITH TIME ZONE,
    next_follow_up_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Kontaktní osoby (business_contacts)
CREATE TABLE IF NOT EXISTS business_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'other' CHECK (role IN ('owner', 'manager', 'receptionist', 'marketing', 'other')),
    email VARCHAR(255),
    phone VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    consent_status VARCHAR(20) DEFAULT 'unknown' CHECK (consent_status IN ('unknown', 'ok', 'do_not_contact')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. CRM aktivity (crm_activities)
CREATE TABLE IF NOT EXISTS crm_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES sellers(id),
    contact_id UUID REFERENCES business_contacts(id),
    type VARCHAR(50) NOT NULL CHECK (type IN ('call', 'email', 'sms', 'whatsapp', 'meeting', 'note', 'other')),
    direction VARCHAR(20) CHECK (direction IN ('outbound', 'inbound')),
    subject VARCHAR(255),
    content TEXT,
    outcome VARCHAR(100),
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Úkoly (tasks)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    assigned_to_seller_id UUID REFERENCES sellers(id),
    title VARCHAR(255) NOT NULL,
    due_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'done', 'cancelled')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 6. Web projekty (website_projects)
CREATE TABLE IF NOT EXISTS website_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES sellers(id),
    status_web VARCHAR(50) DEFAULT 'brief' CHECK (status_web IN ('brief', 'in_progress', 'waiting_client', 'review', 'done', 'cancelled')),
    brief TEXT,
    domain VARCHAR(255),
    hosting VARCHAR(50) DEFAULT 'internal',
    tech_stack VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Projektové přílohy (project_assets)
CREATE TABLE IF NOT EXISTS project_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES website_projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('logo', 'photos', 'contract', 'brief', 'invoice', 'other')),
    file_path TEXT,
    filename VARCHAR(255),
    mime_type VARCHAR(100),
    size_bytes INTEGER,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by UUID REFERENCES sellers(id)
);

-- 8. Faktury klientům (client_invoices)
CREATE TABLE IF NOT EXISTS client_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    business_id UUID NOT NULL REFERENCES businesses(id),
    project_id UUID REFERENCES website_projects(id),
    issued_at DATE NOT NULL,
    due_at DATE NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',
    subtotal DECIMAL(10,2) NOT NULL,
    vat DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    paid_at TIMESTAMP WITH TIME ZONE,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Položky faktur (client_invoice_items)
CREATE TABLE IF NOT EXISTS client_invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES client_invoices(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    qty DECIMAL(10,2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    vat_rate DECIMAL(5,4) DEFAULT 0.21,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Provize (commissions)
CREATE TABLE IF NOT EXISTS commissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),
    business_id UUID REFERENCES businesses(id),
    project_id UUID REFERENCES website_projects(id),
    invoice_id UUID REFERENCES client_invoices(id),
    plan_id UUID,
    base_amount DECIMAL(10,2) NOT NULL,
    commission_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'eligible', 'paid', 'void')),
    eligible_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Výplaty (payouts)
CREATE TABLE IF NOT EXISTS payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),
    period_from DATE NOT NULL,
    period_to DATE NOT NULL,
    currency VARCHAR(3) DEFAULT 'CZK',
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'sent', 'paid', 'cancelled')),
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. Položky výplat (payout_items)
CREATE TABLE IF NOT EXISTS payout_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payout_id UUID NOT NULL REFERENCES payouts(id) ON DELETE CASCADE,
    commission_id UUID NOT NULL REFERENCES commissions(id),
    amount DECIMAL(10,2) NOT NULL
);

-- Indexy pro výkon
CREATE INDEX IF NOT EXISTS idx_businesses_owner_seller ON businesses(owner_seller_id);
CREATE INDEX IF NOT EXISTS idx_businesses_status_crm ON businesses(status_crm);
CREATE INDEX IF NOT EXISTS idx_businesses_next_follow_up ON businesses(next_follow_up_at);
CREATE INDEX IF NOT EXISTS idx_contacts_business ON business_contacts(business_id);
CREATE INDEX IF NOT EXISTS idx_crm_activities_business ON crm_activities(business_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_crm_activities_seller ON crm_activities(seller_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_business ON tasks(business_id);
CREATE INDEX IF NOT EXISTS idx_projects_business ON website_projects(business_id);
CREATE INDEX IF NOT EXISTS idx_invoices_business ON client_invoices(business_id);
CREATE INDEX IF NOT EXISTS idx_commissions_seller ON commissions(seller_id);