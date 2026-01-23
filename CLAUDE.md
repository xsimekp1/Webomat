# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ DŮLEŽITÉ: Produkční prostředí

**Tento projekt běží v produkci!** Při úpravách kódu pracujeme na živém systému.

## Quick Deploy Commands (pro Claude)

**POSTUP PO ZMĚNÁCH:**
1. `git add <soubory> && git commit -m "message" && git push origin master`
2. Spustit seed testovacích dat: `cd frontend && npx tsx scripts/seed-test-data.ts` (pokud potřeba)
3. Redeploy backend (Railway)
4. Redeploy frontend (Vercel) - pouze pokud změny ve frontend/
5. Ověřit health check

**Railway Backend Redeploy:**
```bash
powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v2' -Method Post -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer 66977604-f06c-4e9c-afd2-0440b57f6150'} -Body '{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"9afdeb2c-17e7-44d5-bfe9-1258121a59aa\\\", serviceId: \\\"54b194dd-644f-4c26-a806-faabaaeacc7b\\\") }\"}'"
```

**Vercel Frontend Redeploy:**
```bash
powershell -ExecutionPolicy Bypass -File ".\scripts\redeploy_vercel.ps1"
```
**POZOR:** Vercel free tier má limit deploymentů! Nevolat redeploy opakovaně. Vercel deployuje automaticky při git push - ruční redeploy jen když je to nutné.

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

## Database Schema (Supabase)

**DŮLEŽITÉ:** Před vytvářením/úpravou tabulek vždy ověř aktuální strukturu v Supabase!

### Tabulka `sellers` (obchodníci/uživatelé)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| seller_code | string? | Kód obchodníka |
| first_name | string | Jméno |
| last_name | string | Příjmení |
| email | string | Email (unique, login) |
| phone | string? | Telefon |
| address | string? | Adresa |
| country | string? | Země |
| date_of_birth | date? | Datum narození |
| onboarded_at | datetime? | Datum onboardingu |
| contract_signed_at | datetime? | Datum podpisu smlouvy |
| status | string | Status (active/inactive) |
| terminated_at | datetime? | Datum ukončení |
| commission_plan_id | uuid? | FK na plán provizí |
| default_commission_rate | decimal? | Výchozí provize % |
| payout_method | string? | Způsob výplaty |
| bank_account_iban | string? | IBAN |
| bank_account | string? | Číslo účtu |
| last_payout_at | datetime? | Poslední výplata |
| payout_balance_due | decimal? | Nevyplacený zůstatek |
| notes | text? | Poznámky |
| password_hash | string | Hash hesla |
| role | string | Role (admin/sales) |
| is_active | boolean | Je aktivní |
| must_change_password | boolean | Musí změnit heslo |
| avatar_url | string? | URL profilové fotky |
| created_at | datetime | Vytvořeno |
| updated_at | datetime | Upraveno |

### Tabulka `businesses` (firmy/leady)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| source | string? | Zdroj leadu |
| place_id | string? | Google Places ID (pro deduplikaci) |
| name | string | Název firmy |
| ico | string? | IČO |
| vat_id | string? | VAT ID |
| dic | string? | DIČ |
| address_full | string? | Plná adresa |
| city | string? | Město |
| postal_code | string? | PSČ |
| country | string? | Země |
| lat | decimal? | Zeměpisná šířka |
| lng | decimal? | Zeměpisná délka |
| phone | string? | Telefon (pro deduplikaci) |
| email | string? | Email |
| website | string? | Web (pro deduplikaci) |
| has_website | boolean? | Má web |
| rating | decimal? | Hodnocení Google |
| review_count | int? | Počet recenzí |
| price_level | int? | Cenová úroveň |
| types | array? | Typy/kategorie z Google |
| editorial_summary | text? | Popis/poznámky |
| status_crm | string | CRM status (new/calling/interested/offer_sent/won/lost/dnc) |
| status_reason | string? | Důvod statusu |
| owner_seller_id | uuid? | FK na sellers |
| first_contact_at | datetime? | První kontakt |
| last_contact_at | datetime? | Poslední kontakt |
| next_follow_up_at | datetime? | Příští follow-up |
| billing_address | string? | Fakturační adresa |
| bank_account | string? | Bankovní účet |
| contact_person | string? | Kontaktní osoba |
| created_at | datetime | Vytvořeno |
| updated_at | datetime | Upraveno |

**Deduplikace:** Kontrolovat podle `place_id`, `phone`, `website` před vytvořením nového leadu.

### Tabulka `crm_activities` (aktivity/komunikace)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| business_id | uuid | FK na businesses |
| seller_id | uuid? | FK na sellers |
| contact_id | uuid? | FK na business_contacts |
| type | string | Typ (call/email/meeting/note/message) |
| direction | string? | Směr (inbound/outbound) |
| subject | string? | Předmět |
| content | text? | Obsah/popis |
| outcome | string? | Výsledek |
| occurred_at | datetime | Kdy proběhlo |
| created_at | datetime | Vytvořeno |

### Tabulka `website_projects` (projekty webů)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| business_id | uuid | FK na businesses |
| seller_id | uuid? | FK na sellers |
| package | string | Balíček (start/profi/premium/custom) |
| status | string | Status projektu (offer/won/in_production/delivered/live/cancelled) |
| status_web | string? | Status webu (brief/design/development/review/live) |
| brief | text? | Brief od klienta |
| domain | string? | Doména |
| hosting | string? | Hosting (internal/external) |
| tech_stack | string? | Technologie |
| price_setup | decimal? | Jednorázová cena |
| price_monthly | decimal? | Měsíční cena |
| notes | text? | Poznámky |
| started_at | datetime? | Zahájeno |
| delivered_at | datetime? | Dodáno |
| created_at | datetime | Vytvořeno |
| updated_at | datetime | Upraveno |

### CRM Status hodnoty
- `new` - Nový lead
- `calling` - Voláno
- `interested` - Projevil zájem
- `offer_sent` - Nabídka odeslána
- `won` - Vyhráno (klient)
- `lost` - Ztraceno
- `dnc` - Do Not Contact

### Project Status hodnoty
- `offer` - Nabídka
- `won` - Vyhráno
- `in_production` - Ve výrobě
- `delivered` - Dodáno
- `live` - Živé
- `cancelled` - Zrušeno

### Tabulka `audit_log` (audit log)

**Nutné vytvořit:** Spusť `sql/create_audit_log.sql` v Supabase SQL Editor.

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| user_id | uuid? | FK na sellers |
| user_email | string? | Email uživatele |
| action | string | Akce (login/logout/login_failed/business_create/etc.) |
| entity_type | string? | Typ entity (business/project/user) |
| entity_id | uuid? | ID entity |
| old_values | jsonb? | Staré hodnoty |
| new_values | jsonb? | Nové hodnoty |
| ip_address | string? | IP adresa |
| user_agent | text? | User agent |
| created_at | datetime | Kdy |

### Deduplikace leadů

Při vytváření leadu se kontroluje:
1. **Blokující** (409 Conflict): `place_id`, `phone`, `website`
2. **Varování** (vrátí similar_names): `name` - pro soukromé osoby bez IČO

Endpoint: `GET /crm/businesses/check-duplicate?phone=&website=&name=`

## DRY RUN Mode (implementováno)
- Endpoint: POST /website/generate
- Parametr: dry_run (boolean)
- Pokud dry_run=true: vrátí dummy HTML stránku místo volání Claude API
- Dummy stránka: kompletní HTML s "Dry run test web" obsahem, gradient background, stylizované tělo
- Umožňuje testovat printscreen a thumbnail funkcionality bez nákladů
- UI: Modal s možností výběru mezi DRY RUN a AI generováním (AI zatím disabled)

## Project Language

Primary documentation is in Czech. The project serves Czech market businesses.
