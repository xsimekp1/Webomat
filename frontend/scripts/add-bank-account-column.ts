/**
 * SQL pro přidání sloupce bank_account
 * Spusť tento SQL v Supabase SQL Editoru
 */

console.log(`
=====================================
SQL pro přidání sloupce bank_account:
=====================================

ALTER TABLE sellers ADD COLUMN IF NOT EXISTS bank_account TEXT;

=====================================
`)
