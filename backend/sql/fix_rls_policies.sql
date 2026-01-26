-- RLS (Row Level Security) policies for Webomat
-- This fixes Network errors when creating projects

-- Enable RLS on existing tables
ALTER TABLE website_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE sellers ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_activities ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Service role full access on website_projects" ON website_projects;
DROP POLICY IF EXISTS "Service role full access on businesses" ON businesses;
DROP POLICY IF EXISTS "Service role full access on sellers" ON sellers;
DROP POLICY IF EXISTS "Service role full access on crm_activities" ON crm_activities;

-- Create policies for Service Role (backend has full access)
CREATE POLICY "Service role full access on website_projects" ON website_projects
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on businesses" ON businesses
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on sellers" ON sellers
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on crm_activities" ON crm_activities
    FOR ALL USING (auth.role() = 'service_role');

-- Optional: Client-side policies for frontend (if using anon key in future)
-- These restrict access based on user roles

-- Sellers can only see their own or unassigned businesses
CREATE POLICY "Sellers view own businesses" ON businesses
    FOR SELECT USING (
        auth.role() = 'authenticated' AND 
        (
            owner_seller_id = auth.uid() OR 
            owner_seller_id IS NULL
        )
    );

-- Sellers can create businesses (will be assigned to them automatically)
CREATE POLICY "Sellers create businesses" ON businesses
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated'
    );

-- Sellers can only update their own businesses
CREATE POLICY "Sellers update own businesses" ON businesses
    FOR UPDATE USING (
        auth.role() = 'authenticated' AND 
        owner_seller_id = auth.uid()
    );

-- Project-specific policies
CREATE POLICY "Sellers view own projects" ON website_projects
    FOR SELECT USING (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM businesses 
            WHERE businesses.id = website_projects.business_id 
            AND (businesses.owner_seller_id = auth.uid() OR businesses.owner_seller_id IS NULL)
        )
    );

CREATE POLICY "Sellers create projects" ON website_projects
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM businesses 
            WHERE businesses.id = website_projects.business_id 
            AND (businesses.owner_seller_id = auth.uid() OR businesses.owner_seller_id IS NULL)
        )
    );

-- Allow sellers to update projects they can access
CREATE POLICY "Sellers update own projects" ON website_projects
    FOR UPDATE USING (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM businesses 
            WHERE businesses.id = website_projects.business_id 
            AND (businesses.owner_seller_id = auth.uid() OR businesses.owner_seller_id IS NULL)
        )
    );

-- Activities policies
CREATE POLICY "Sellers view own activities" ON crm_activities
    FOR SELECT USING (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM businesses 
            WHERE businesses.id = crm_activities.business_id 
            AND (businesses.owner_seller_id = auth.uid() OR businesses.owner_seller_id IS NULL)
        )
    );

CREATE POLICY "Sellers create activities" ON crm_activities
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM businesses 
            WHERE businesses.id = crm_activities.business_id 
            AND (businesses.owner_seller_id = auth.uid() OR businesses.owner_seller_id IS NULL)
        )
    );

-- Website versions policies
CREATE POLICY "Sellers view own project versions" ON website_versions
    FOR SELECT USING (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM website_projects wp
            JOIN businesses b ON b.id = wp.business_id
            WHERE wp.id = website_versions.project_id 
            AND (b.owner_seller_id = auth.uid() OR b.owner_seller_id IS NULL)
        )
    );

CREATE POLICY "Sellers create project versions" ON website_versions
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM website_projects wp
            JOIN businesses b ON b.id = wp.business_id
            WHERE wp.id = website_versions.project_id 
            AND (b.owner_seller_id = auth.uid() OR b.owner_seller_id IS NULL)
        )
    );

-- Admin policies (admin users have full access)
CREATE POLICY "Admin full access" ON sellers
    FOR ALL USING (
        auth.role() = 'authenticated' AND 
        EXISTS (
            SELECT 1 FROM sellers 
            WHERE sellers.id = auth.uid() AND sellers.role = 'admin'
        )
    );

-- Fix: Grant necessary permissions for RLS to work properly
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;

-- Grant usage on sequences for auto-incrementing IDs
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, service_role;

COMMIT;