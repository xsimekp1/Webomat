# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ DŮLEŽITÉ: Produkční prostředí

**Tento projekt běží v produkci!** Při úpravách kódu pracujeme na živém systému.

## Quick Deploy Commands (pro Claude)

**POSTUP PO ZMĚNÁCH:**
1. `git add <soubory> && git commit -m "message" && git push origin master`
2. Redeploy backend (Railway)
3. Redeploy frontend (Vercel) - pouze pokud změny ve frontend/
4. Ověřit health check

**Railway Backend Redeploy:**
```bash
powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v2' -Method Post -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer 66977604-f06c-4e9c-afd2-0440b57f6150'} -Body '{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"9afdeb2c-17e7-44d5-bfe9-1258121a59aa\\\", serviceId: \\\"54b194dd-644f-4c26-a806-faabaaeacc7b\\\") }\"}'"
```

**Vercel Frontend Redeploy:**
```bash
powershell -ExecutionPolicy Bypass -File ".\scripts\redeploy_vercel.ps1"
```

**Health Check:**
```bash
curl -s https://webomat-backend-production.up.railway.app/health
```

**Počkat na deploy (45s) a ověřit:**
```bash
powershell -ExecutionPolicy Bypass -Command "Start-Sleep 45; Invoke-RestMethod -Uri 'https://webomat-backend-production.up.railway.app/health'"
```

## Production Deployment

| Služba | URL | Platforma |
|--------|-----|-----------|
| **Frontend** | https://webomat.vercel.app | Vercel |
| **Backend API** | https://webomat-backend-production.up.railway.app | Railway |
| **Database** | cmtvixayfbqhdlftsgqg.supabase.co | Supabase |
| **Supabase Dashboard** | https://supabase.com/dashboard/project/cmtvixayfbqhdlftsgqg | SQL Editor |

**Railway Project ID:** `d6a191b5-bc63-4836-b905-1cdee9fe51e5`
**Railway Service ID:** `54b194dd-644f-4c26-a806-faabaaeacc7b`

### Credentials a .env soubory

**VŽDY první krok při řešení problémů s API/DB:**
- `backend/.env` - Supabase URL, Service Role Key, JWT secret
- `frontend/.env.local` - Vercel/Supabase anon key

**Supabase DDL změny (ALTER TABLE, CREATE TABLE):**
- Nelze přes REST API - nutné provést v Supabase Dashboard SQL Editor
- Po DDL změnách NENÍ potřeba restart backendu

### Debugging databázových chyb

**Při chybě PGRST204 (column not found) nebo 500 erroru:**
1. VŽDY nejdřív ověř strukturu tabulky lokálně:
```python
cd backend && python -c "
from app.database import get_supabase
s = get_supabase()
# Ověř strukturu tabulky
result = s.table('NAZEV_TABULKY').select('*').limit(1).execute()
print(result.data)
"
```
2. Nebo dotaz na sloupce v Supabase SQL Editor:
```sql
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'NAZEV_TABULKY';
```
3. Teprve pak hledej chybu v kódu

### Environment Variables

**Backend (Railway):**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `JWT_SECRET_KEY` - Secret pro JWT tokeny
- `CORS_ORIGINS` - Povolené origins (včetně Vercel URL)
- `PORT` - Port pro uvicorn (8000)

**Frontend (Vercel):**
- `NEXT_PUBLIC_API_URL` - URL backendu (Railway)
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

### Supabase Storage

- **Bucket:** `webomat` (public)
- Používá se pro ukládání avatarů uživatelů

### Redeploy Process

Po pushnutí změn na GitHub je potřeba ručně spustit redeploy (auto-deploy není zapnutý).

**1. Railway Backend:**
```powershell
powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v2' -Method Post -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer 66977604-f06c-4e9c-afd2-0440b57f6150'} -Body '{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"9afdeb2c-17e7-44d5-bfe9-1258121a59aa\\\", serviceId: \\\"54b194dd-644f-4c26-a806-faabaaeacc7b\\\") }\"}'"
```

**2. Vercel Frontend:**
```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\redeploy_vercel.ps1"
```

**3. Ověření stavu:**
```powershell
# Backend health check
Invoke-RestMethod -Uri 'https://webomat-backend-production.up.railway.app/health'

# Frontend check
(Invoke-WebRequest -Uri 'https://webomat.vercel.app' -Method Head).StatusCode
```

**Alternativně pomocí skriptu** (pokud máš povolenou ExecutionPolicy):
```powershell
$env:RAILWAY_TOKEN = "66977604-f06c-4e9c-afd2-0440b57f6150"
$env:VERCEL_TOKEN = "uanxoOOLz8mCzrjFupSNoznD"
.\scripts\redeploy.ps1
```

## Project Overview

Webomat is a CRM + Business Discovery System for finding businesses without websites (via Google Places API) and managing sales/web development projects. The project is in active MVP development.

## Architecture

**Current Stack:**
- **Database:** Supabase (PostgreSQL) - 12-table schema (sellers, businesses, CRM activities, invoices, commissions, etc.)
- **Frontend:** Next.js 14 + React 18 + TypeScript + Tailwind CSS (deployed on Vercel)
- **Backend:** FastAPI + Pydantic (deployed on Railway, port 8000)
- **APIs:** Google Places, Supabase, OpenAI/Claude

**Key Components:**
- `frontend/` - Next.js app with API client (`app/lib/api.ts`) using Axios with Bearer token auth
- `backend/` - FastAPI backend with routers, schemas, Supabase integration

**API Endpoints (FastAPI backend):**
- Auth: `POST /token`, `GET /users/me`, `POST /users/me/password`
- CRM Businesses: `GET/POST /crm/businesses`, `GET/PUT/DELETE /crm/businesses/{id}`
- CRM Activities: `GET/POST /crm/businesses/{id}/activities`
- CRM Projects: `GET/POST/PUT /crm/businesses/{id}/project`
- CRM Dashboard: `GET /crm/dashboard/today`, `GET /crm/dashboard/stats`
- Finance: `/financial/summary`, `/financial/accounts`, `/financial/earnings`, `/financial/payouts`
- Admin: `GET /admin/users`, `GET /admin/users/{id}`, `POST /admin/users/{id}/reset-password`, `POST /admin/users/{id}/toggle-active`
- Health: `GET /health`

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
