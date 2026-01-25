-- Enhanced Business Details Page Improvements
-- Adds all missing contact and billing information fields
-- Improves UI for better user experience

-- 1. Update Business Interface in Frontend
-- File: frontend/app/dashboard/crm/[id]/page.tsx

-- 2. Backend Changes Required
-- File: backend/app/routers/crm.py

-- 3. Database Schema Updates
-- Run SQL: backend/sql/enhance_businesses_table.sql

-- Priority Issues to Fix:

-- ISSUE 1: Missing Contact Information Display
-- Problem: Email, phone, contact person not showing in UI
-- Solution: Update Business interface and display logic
-- Status: HIGH - Critical for sales operations

-- ISSUE 2: Missing Billing Information Display  
-- Problem: ICO, DIC, billing address, bank account not visible
-- Solution: Add billing section to client detail page
-- Status: HIGH - Essential for invoicing

-- ISSUE 3: Email Field Missing in CRM List
-- Problem: Can't see email addresses in business list
-- Solution: Add email column to CRM table
-- Status: MEDIUM - Important for communication

-- ISSUE 4: Incomplete Data Transfer from ARES
-- Problem: Not all ARES fields being populated correctly
-- Solution: Fix ARES API integration
-- Status: MEDIUM - Affects data quality

-- ISSUE 5: Missing Business Categories
-- Problem: No categorization of business types
-- Solution: Add category field with dropdown
-- Status: LOW - Nice to have for filtering

-- IMPLEMENTATION PLAN:

-- Phase 1: Database Updates (Immediate)
-- 1. Run enhance_businesses_table.sql in Supabase
-- 2. Verify all columns exist and are indexed
-- 3. Test data insertion with new fields

-- Phase 2: Backend API Updates (1 day)
-- 1. Update Business schema in Pydantic models
-- 2. Modify GET/POST endpoints to handle new fields
-- 3. Update ARES integration to populate all fields
-- 4. Add data validation for new fields

-- Phase 3: Frontend UI Updates (2 days)
-- 1. Update Business interface with all new fields
-- 2. Add missing fields to client detail page display
-- 3. Add email column to CRM business list
-- 4. Create/edit forms to capture all information
-- 5. Add field validation and error handling

-- Phase 4: Testing & Polish (1 day)
-- 1. Test ARES lookup with complete data
-- 2. Verify form submissions work correctly
-- 3. Test display of all business information
-- 4. Add responsive design for mobile
-- 5. Test data validation and error messages

-- CRITICAL FIELDS TO ADD:

-- CONTACT INFORMATION:
- email (contact@business.cz)
- phone (+420 123 456 789) 
- contact_person (Jan Novák)
- website (https://www.business.cz)

-- BILLING INFORMATION:
- ico (12345678)
- dic (CZ12345678)
- vat_id (CZ12345678)
- billing_address (Hlavní 123, 110 00 Praha)
- bank_account (123456789/0800)

-- BUSINESS DETAILS:
- category (Restaurace, Služby, Obchod)
- subcategory (Italská restaurace, Webové služby)
- employees_count (10-50, 51-200, 201+)
- annual_revenue (CZK ranges)

-- CRM ENHANCEMENTS:
- lead_source (Google, ARES, Manual, Referral)
- lead_value (High, Medium, Low)
- conversion_probability (1-100%)
- last_activity_date
- follow_up_count

-- Display Priorities:
-- 1. Email and Phone - Always visible in CRM list
-- 2. Contact Person - Shown in detail view
-- 3. Billing Info - Collapsible section in detail view
-- 4. Business Category - Filter and display in list
-- 5. Last Activity - When was last contact made

-- Database Indexes for Performance:
CREATE INDEX IF NOT EXISTS idx_businesses_email ON businesses(email);
CREATE INDEX IF NOT EXISTS idx_businesses_phone ON businesses(phone);  
CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(category);
CREATE INDEX IF NOT EXISTS idx_businesses_owner_contact ON businesses(owner_seller_id, contact_person);

-- Migration Script:
-- This will be executed in Supabase SQL Editor
-- BACKUP YOUR DATA BEFORE RUNNING!

-- ARES Integration Improvements:
-- 1. Parse more fields from ARES response
-- 2. Handle different company types (s.r.o., a.s., etc.)
-- 3. Extract address components properly
-- 4. Get additional identifiers (VAT, DIC)
-- 5. Handle missing data gracefully

-- UI/UX Improvements:
-- 1. Add "Copy" buttons for email, phone
-- 2. Show "Click-to-call" for phone numbers
-- 3. Add email composition button
-- 4. Show map for address
-- 5. Add "Edit" button in detail view

-- GDPR Compliance:
-- 1. Add data processing consent tracking
-- 2. Implement data retention policies
-- 3. Add right to be forgotten functionality
-- 4. Audit trail for business data changes
-- 5. Secure sensitive information (bank details)

-- Email Integration:
-- 1. Email template library for business communication
-- 2. Bulk email sending to selected businesses
-- 3. Email tracking and open rates
-- 4. Automated follow-up sequences
-- 5. Email signature integration

-- Mobile Responsiveness:
-- 1. Ensure all new fields work on mobile
-- 2. Add horizontal scrolling for wide tables
-- 3. Optimize touch targets for mobile interaction
-- 4. Test on different screen sizes
-- 5. Add mobile-specific features (click-to-call)

This comprehensive enhancement will provide complete business information management
essential for effective sales operations and customer relationship management.