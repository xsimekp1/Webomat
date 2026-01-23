# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Webomat is a CRM + Business Discovery System for finding businesses without websites (via Google Places API) and managing sales/web development projects. The project is in active MVP development.

## Architecture

**Current Stack:**
- **Database:** Supabase (PostgreSQL) - 12-table schema (sellers, businesses, CRM activities, invoices, commissions, etc.)
- **Frontend (in development):** Next.js 14 + React 18 + TypeScript + Tailwind CSS
- **Backend (planned):** FastAPI on port 8000
- **APIs:** Google Places, Supabase, OpenAI/Claude

**Key Components:**
- `frontend/` - Next.js app with API client (`app/lib/api.ts`) using Axios with Bearer token auth
- `backend/` - FastAPI backend (empty structure, implementation pending)
- `streamlit_app/` - Streamlit dashboard (launcher scripts only in repo)

**API Endpoints (planned for FastAPI backend):**
- Auth: `/token`, `/users/me`
- CRM: `/crm/companies-simple`, `/crm/contacts-simple`, `/crm/websites-simple`
- Finance: `/financial/accounts`, `/financial/earnings`, `/financial/payouts`

## Commands

### Frontend (Next.js)
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Development server
npm run build        # Production build
npm run start        # Start production server
```

### Python/CLI
```bash
pip install -r requirements.txt    # Install Python dependencies
```

### Environment Setup
```bash
cp .env.example .env
# Required: GOOGLE_PLACES_API_KEY
# For full CRM: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY
```

## MVP Development

Active MVP implementation following `MVP_PLAN.md`. Current priorities:
- **mvp-0 (High):** Authentication & RBAC (Admin vs Sales roles)
- **mvp-1 to mvp-22 (Medium):** CRM, deals, payments, commissions, website generation

Key MVP patterns:
- CRM Pipeline: New → Calling → Interested → Offer sent → Won/Lost/DNC
- Deal Pipeline: Offer → Won → In production → Delivered → Live
- Packages: Start/Profi/Premium/Custom with setup + monthly pricing
- Commissions tied to actual payments, not promises

## Database Schema

Core tables:
- `sellers` - Sales representatives
- `businesses` - Client companies/leads
- `business_contacts` - Contact persons
- `crm_activities` - Sales activities
- `tasks` - Tasks and follow-ups
- `website_projects`, `project_assets` - Web development
- `client_invoices`, `client_invoice_items` - Invoicing
- `commissions`, `payouts`, `payout_items` - Commission tracking

### Tabulka `businesses` (firmy/leady)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| name | string | Název firmy |
| address | string? | Adresa sídla |
| phone | string? | Telefon |
| email | string? | Email |
| website | string? | Web |
| category | string? | Kategorie/obor |
| notes | string? | Poznámky |
| status_crm | enum | Status v CRM pipeline (new/calling/interested/offer_sent/won/lost/dnc) |
| owner_seller_id | uuid? | FK na sellers - přiřazený obchodník |
| next_follow_up_at | datetime? | Datum příštího follow-upu |
| **ico** | string? | IČO (identifikační číslo) |
| **dic** | string? | DIČ (daňové identifikační číslo) |
| **billing_address** | string? | Fakturační adresa (pokud jiná než sídlo) |
| **bank_account** | string? | Bankovní účet |
| **contact_person** | string? | Kontaktní osoba / jednatel |
| created_at | datetime | Datum vytvoření |
| updated_at | datetime | Datum poslední úpravy |

### CRM Status hodnoty
- `new` - Nový lead
- `calling` - Voláno
- `interested` - Projevil zájem
- `offer_sent` - Nabídka odeslána
- `won` - Vyhráno (klient)
- `lost` - Ztraceno
- `dnc` - Do Not Contact

## Project Language

Primary documentation is in Czech. The project serves Czech market businesses.
