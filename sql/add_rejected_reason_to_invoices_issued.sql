-- Migration: Add rejected_reason column to invoices_issued table
-- Run this in Supabase SQL Editor
-- Date: 2026-02-01

-- Add rejected_reason column for invoice approval workflow
ALTER TABLE invoices_issued
ADD COLUMN IF NOT EXISTS rejected_reason TEXT;

-- Comment on the new column
COMMENT ON COLUMN invoices_issued.rejected_reason IS 'Reason for rejection when admin rejects an invoice';

-- Update the status comment to include new pending_approval status
COMMENT ON COLUMN invoices_issued.status IS 'Invoice status: draft, pending_approval, issued, paid, overdue, cancelled';
