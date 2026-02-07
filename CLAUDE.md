# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ DŮLEŽITÉ: Produkční prostředí

**Tento projekt běží v produkci!** Při úpravách kódu pracujeme na živém systému.

**i18n:** Při vytváření nových funkcionalit s přesahem do frontendu je potřeba frontend psát rovnou pro oba jazyky (CS i EN) — překlady do `frontend/messages/cs.json` a `frontend/messages/en.json`.

## Quick Deploy Commands (pro Claude)

**POSTUP PO ZMĚNÁCH:**
1. `git add <soubory> && git commit -m "message" && git push origin master`
2. Spustit seed testovacích dat: `cd frontend && npx tsx scripts/seed-test-data.ts` (pokud potřeba)
3. Redeploy backend (Railway)
4. Redeploy frontend (Vercel) - pouze pokud změny ve frontend/
5. Ověřit health check

**Railway Backend Redeploy:**
```bash
# Použij Railway token z env proměnné RAILWAY_TOKEN
# Tokeny a API klíče najdeš v lokálních .env souborech - NEJSOU uloženy v tomto repository
powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v2' -Method Post -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer $env:RAILWAY_TOKEN'} -Body '{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"$env:RAILWAY_ENVIRONMENT_ID\\\", serviceId: \\\"$env:RAILWAY_SERVICE_ID\\\") }\"}'"
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
# Použij Railway token z lokálního .env souboru
powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v2' -Method Post -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer $env:RAILWAY_TOKEN'} -Body '{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"$env:RAILWAY_ENVIRONMENT_ID\\\", serviceId: \\\"$env:RAILWAY_SERVICE_ID\\\") }\"}'"
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

**POVINNOST:** Při jakékoli změně struktury databáze (CREATE TABLE, ALTER TABLE, nové sloupce) MUSÍŠ aktualizovat tuto dokumentaci!

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
| versions_count | integer? | Počet verzí webu |
| latest_version_id | uuid? | FK na nejnovější verzi |
| created_at | datetime | Vytvořeno |
| updated_at | datetime | Upraveno |

### Tabulka `website_versions` (verze webů)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| project_id | uuid | FK na website_projects |
| version_number | integer | Číslo verze (1, 2, 3...) |
| html_content | text | HTML kód verze |
| html_content_en | text? | Anglická verze HTML |
| thumbnail_url | string? | URL náhledu |
| printscreen_url | string? | URL printscreenu |
| status | string | Status (draft/published/archived) |
| title | string? | Titulek verze |
| description | text? | Popis verze |
| changes_summary | text? | Souhrn změn |
| is_active | boolean | Je aktivní verze |
| published_at | datetime? | Publikováno kdy |
| created_at | datetime | Vytvořeno |
| created_by | uuid? | Kdo vytvořil (FK na sellers) |
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

### Tabulka `ledger_entries` (provizní účet obchodníků)

**SQL:** `sql/create_invoices_ledger.sql`

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| seller_id | uuid | FK na sellers |
| entry_type | string | Typ: commission_earned/admin_adjustment/payout_reserved/payout_paid |
| amount | decimal | Částka (kladné = příjem, záporné = výdaj) |
| related_invoice_id | uuid? | FK na invoices_received |
| related_project_id | uuid? | FK na website_projects |
| related_business_id | uuid? | FK na businesses |
| description | text? | Popis |
| notes | text? | Poznámky |
| is_test | boolean | Testovací záznam |
| created_at | datetime | Vytvořeno |
| created_by | uuid? | Kdo vytvořil |

### Tabulka `invoices_issued` (vydané faktury klientům)

Webomat fakturuje klientovi za web.

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| business_id | uuid | FK na businesses |
| project_id | uuid? | FK na website_projects |
| seller_id | uuid? | FK na sellers (kdo uzavřel deal) |
| invoice_number | string | Číslo faktury (unique) |
| issue_date | date | Datum vystavení |
| due_date | date | Datum splatnosti |
| paid_date | date? | Datum zaplacení |
| amount_without_vat | decimal | Částka bez DPH |
| vat_rate | decimal | Sazba DPH (default 21) |
| vat_amount | decimal? | Výše DPH |
| amount_total | decimal | Celková částka |
| currency | string | Měna (default CZK) |
| payment_type | string | Typ: setup/monthly/other |
| status | string | Status: draft/pending_approval/issued/paid/overdue/cancelled |
| rejected_reason | text? | Důvod zamítnutí (pokud admin zamítne) |
| description | text? | Text faktury |
| pdf_path | text? | Cesta k PDF |
| variable_symbol | string? | Variabilní symbol |
| sent_to_accountant | boolean | Odesláno účetní |
| created_at | datetime | Vytvořeno |
| updated_at | datetime | Upraveno |

**Invoice Status Workflow:**
- `draft` - Návrh (obchodník může upravovat)
- `pending_approval` - Čeká na schválení (odesláno adminovi)
- `issued` - Vystaveno (schváleno adminem, odesláno klientovi)
- `paid` - Zaplaceno
- `overdue` - Po splatnosti
- `cancelled` - Stornováno

### Tabulka `invoices_received` (přijaté faktury)

Faktury přijaté platformou - od obchodníků za provize nebo od externích dodavatelů za služby.

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| seller_id | uuid | FK na sellers (může být NULL pro service faktury) |
| invoice_type | string | Typ: commission/service/other |
| vendor_name | string? | Název dodavatele (pro service faktury) |
| invoice_number | string | Číslo faktury (unique per seller) |
| issue_date | date | Datum vystavení |
| due_date | date | Datum splatnosti |
| period_from | date? | Období od |
| period_to | date? | Období do |
| amount_total | decimal | Celková částka |
| amount_to_payout | decimal? | Částka k vyplacení |
| currency | string | Měna (default CZK) |
| status | string | Status: draft/submitted/approved/paid/rejected |
| rejected_reason | text? | Důvod zamítnutí |
| description_text | text? | Text faktury |
| pdf_path | text? | Cesta k PDF |
| is_test | boolean | Testovací faktura |
| approved_at | datetime? | Schváleno kdy |
| approved_by | uuid? | Schváleno kým |
| paid_at | datetime? | Vyplaceno kdy |
| created_at | datetime | Vytvořeno |
| updated_at | datetime | Upraveno |

### Tabulka `platform_settings` (nastavení platformy)

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| key | string | Klíč nastavení (unique) |
| value | jsonb | Hodnota (JSON) |
| updated_at | datetime | Upraveno |
| updated_by | uuid? | Kdo upravil |

**Klíče:**
- `billing_info` - Fakturační údaje Webomatu (company_name, ico, dic, address...)
- `invoice_settings` - Nastavení faktur (default_due_days, vat_rate, min_payout_threshold...)

### Tabulka `generator_runs` (běhy generátoru)

**SQL:** `sql/create_generator_runs.sql`

Sleduje všechna spuštění generátoru webů s metriky nákladů a výkonu.

| Sloupec | Typ | Popis |
|---------|-----|-------|
| id | uuid | Primární klíč |
| seller_id | uuid? | FK na sellers (kdo spustil) |
| seller_email | string? | Email uživatele |
| project_id | uuid? | FK na website_projects |
| business_id | uuid? | FK na businesses |
| version_id | uuid? | FK na website_versions (vytvořená verze) |
| run_type | string | Typ: dry_run/claude_ai/openai/screenshot |
| status | string | Status: started/completed/failed |
| input_tokens | integer | Počet vstupních tokenů |
| output_tokens | integer | Počet výstupních tokenů |
| total_tokens | integer | Celkový počet tokenů |
| cost_usd | decimal | Náklady v USD (6 desetinných míst) |
| cost_czk | decimal | Náklady v CZK |
| model_used | string? | Model: claude-3-opus, gpt-4, etc. |
| started_at | datetime | Začátek běhu |
| completed_at | datetime? | Konec běhu |
| duration_ms | integer? | Trvání v milisekundách |
| prompt_summary | text? | Shrnutí požadavku |
| error_message | text? | Chybová zpráva (pokud failed) |
| metadata | jsonb? | Další metadata |
| created_at | datetime | Vytvořeno |

**run_type hodnoty:**
- `dry_run` - Testovací běh bez AI (zdarma)
- `claude_ai` - Plné AI generování s Claude
- `openai` - Překlad nebo jiné OpenAI úlohy
- `screenshot` - Zachycení screenshotu

### Databázové funkce

- `get_next_issued_invoice_number(year)` - Generuje další číslo vydané faktury (YYYY-NNNN)
- `get_seller_balance(seller_id, include_test)` - Vypočítá aktuální saldo obchodníka z ledgeru

### Deduplikace leadů

Při vytváření leadu se kontroluje:
1. **Blokující** (409 Conflict): `place_id`, `phone`, `website`
2. **Varování** (vrátí similar_names): `name` - pro soukromé osoby bez IČO

Endpoint: `GET /crm/businesses/check-duplicate?phone=&website=&name=`

## Rozpracované funkcionality (WIP)

| Funkce | Stav | Poznámka |
|--------|------|----------|
| **PDF generování faktur** | Placeholder | WeasyPrint enabled, zatím generuje zástupné PDF. Plná šablona s kompletními daty přijde později. |
| **AI generátor webů** | Disabled v UI | Backend endpoint `/website/generate` funguje, ale UI tlačítko pro AI je disabled. Pouze DRY RUN dostupný. |
| **Screenshoty webů** | Opraveno | Playwright + Chromium nainstalován v Dockerfile. Dříve chyběl browser binary na Railway. |

**Debug/WIP indikátory ve frontendu:**
- Na stránce detailu faktury je info banner o WIP stavu PDF generování
- Při přidávání nových WIP funkcí vždy přidat viditelný indikátor v UI (info banner, badge, tooltip)

## DRY RUN Mode (implementováno)
- Endpoint: POST /website/generate
- Parametr: dry_run (boolean)
- Pokud dry_run=true: vrátí dummy HTML stránku místo volání Claude API
- Dummy stránka: kompletní HTML s "Dry run test web" obsahem, gradient background, stylizované tělo
- Umožňuje testovat printscreen a thumbnail funkcionality bez nákladů
- UI: Modal s možností výběru mezi DRY RUN a AI generováním (AI zatím disabled)

## Anglická verze webu & LLM překlady

**Parametr:** `include_english` v endpointech `/website/generate` a `/website/generate-test`

**Hodnoty:**
- `no` - Pouze česká verze (default)
- `auto` - Automatický překlad pomocí OpenAI API
- `client` - Vrátí seznam textů k překladu klientem

**Backend služba:** `backend/app/services/llm.py`

**Požadované env proměnné pro překlad:**
```bash
OPENAI_API_KEY=sk-...  # OpenAI API klíč
```

**Endpoint pro kontrolu dostupnosti:**
```bash
GET /website/translation-status  # Vrátí {"available": true/false}
```

**Response obsahuje:**
- `html_content` - Česká verze HTML
- `html_content_en` - Anglická verze (pokud include_english=auto a API dostupné)
- `translation_status` - completed/unavailable/failed/client_required
- `strings_for_client` - Seznam textů k překladu (pokud include_english=client)

## Deployment & Online Testing

### 🚀 Quick Deploy Commands (Updated)

**FULL DEPLOYMENT:**
```bash
# Deploy all services
npm run deploy:all

# Or deploy individually:
./scripts/deploy-backend.sh    # Railway
./scripts/deploy-frontend.sh   # Vercel
./scripts/deploy-mobile.sh     # EAS
```

**TESTING URLs:**
- **Frontend (Web):** https://webomat.vercel.app
- **Backend API:** https://webomat-backend-production.up.railway.app
- **Mobile:** Expo Go app or downloaded builds

### 📱 Mobile App Testing

**Development:**
```bash
npm run mobile          # Start Expo dev server
npm run mobile:ios      # iOS simulator
npm run mobile:android  # Android emulator
```

**Build & Test:**
```bash
npm run mobile:build:dev    # Development build
npm run mobile:build:preview # Preview build
npm run mobile:build:prod   # Production build
```

**Expo Go Testing:**
1. Install Expo Go on phone
2. Scan QR code from `npm run mobile`
3. Test without full build

### 🔧 Setup Requirements

**For Deployment:**
1. **Railway CLI:** `npm install -g @railway/cli`
2. **Vercel CLI:** `npm install -g vercel`
3. **EAS CLI:** `npm install -g @expo/eas-cli`

**Environment Variables:**
- Vercel: Set `NEXT_PUBLIC_API_URL` in dashboard
- EAS: Configure in `mobile/app.json` or EAS dashboard

### 📊 CI/CD Status

- ✅ **Backend:** Railway (auto-deploy on push)
- ✅ **Frontend:** Vercel (auto-deploy on push)
- ✅ **Mobile:** EAS (manual builds, auto on PR)

## Project Language

Primary documentation is in Czech. The project serves Czech market businesses.

## Unit Testing (Backend)

### Spuštění testů

```bash
cd backend
pip install -r requirements.txt  # Nainstaluje pytest, pytest-asyncio, httpx
pytest                           # Spustí všechny testy
pytest -v                        # Verbose výstup
pytest tests/test_sales_pipeline.py  # Jen konkrétní soubor
pytest -k "test_create_business"     # Jen testy matching pattern
```

### Struktura testů

```
backend/tests/
├── __init__.py
├── conftest.py          # Fixtures (mock Supabase, mock users, sample data)
├── test_sales_pipeline.py  # Testy pro sales flow
├── test_crm_activities.py  # Testy pro CRM aktivity
└── test_seller_dashboard.py # Testy pro dashboard statistiky
```

### Nově implementované funkce

**Payment Reminder System (2025-01-26):**
- Backend endpoint: `POST /crm/invoices/{id}/generate-reminder` - generování textu upomínky
- Backend endpoint: `POST /crm/invoices/{id}/send-reminder` - odeslání a vytvoření aktivity
- Automatické vytvoření follow-up aktivity s konfigurovatelným počtem dní (default 3)
- Frontend modal pro zobrazení a odeslání upomínky
- Generovaný text obsahuje: číslo faktury, částka, datum splatnosti, jméno klienta, doménu

**Profile Management Fix (2025-01-26):**
- Opraveno ukládání jména a příjmení přes backend API
- Změněn frontend z přímého Supabase přístupu na `PUT /users/me` endpoint
- Opravena metoda z `updateUserProfile` na PUT namísto POST

**Pending Projects Filter (2025-01-26):**
- Opraven filtr rozpracovaných projektů - odebrány projekty ve stavu "delivered"
- Zobrazeny pouze projekty se statusem: "offer", "won", "in_production"
- Zlepšena přehlednost dashboardu - relevantní projekty k práci

**Activity Follow-up Management (2025-01-26):**
- Přidáno pole `next_follow_up_at` do formuláře pro vytvoření aktivity
- Validace proti nastavení data v minulosti
- Backend aktualizován pro automatickou aktualizaci `next_follow_up_at` v businesses tabulce
- Vylepšeno UI s datumovým polem a validací

### Co je pokryto (Sales Pipeline)

| Oblast | Testy | Soubor |
|--------|-------|--------|
| Vytvoření businessu | ✅ Úspěšné vytvoření, validace, minimální data | `test_sales_pipeline.py` |
| Deduplikace | ✅ Telefon, web, normalizace | `test_sales_pipeline.py` |
| Projekty | ✅ Všechny balíčky, všechny statusy | `test_sales_pipeline.py` |
| Website verze | ✅ První verze, inkrementace čísla | `test_sales_pipeline.py` |
| Dry run generování | ✅ HTML struktura, styling | `test_sales_pipeline.py` |

### TODO - Další testy k doplnění

**Vysoká priorita:**
- [ ] Autentizace (JWT, login/logout, password change)
- [ ] RBAC (admin vs sales přístup)
- [ ] Ledger výpočty (balance obchodníka)
- [ ] Admin operace (reset password, toggle active)

**Střední priorita:**
- [ ] CRM aktivity (vytvoření, status update)
- [ ] Dashboard statistiky
- [ ] List/filter businessů (pagination, search)
- [ ] Update business/project

**Nižší priorita:**
- [ ] Upload/delete logo
- [ ] ARES lookup
- [ ] Audit log

### Fixtures v conftest.py

- `mock_supabase` - Mockovaný Supabase klient
- `sample_seller` - Testovací obchodník (role: sales)
- `sample_admin` - Testovací admin
- `sample_business` - Testovací lead/firma
- `sample_project` - Testovací projekt
- `sample_version` - Testovací website verze
- `app_client` - FastAPI TestClient s sales rolí
- `admin_client` - FastAPI TestClient s admin rolí

## Test Driven Development (TDD)

**IMPORTANT:** Při vývoji nových funkcí VŽDY používej Test Driven Development:

1. **Napiš testy nejdříve** - Před implementací jakékoliv funkce napiš unit testy
2. **Testy musí selhat** - Ujisti se, že testy selhávají (RED fáze)
3. **Implementuj minimální kód** - Napiš jen tolik kódu, aby testy prošly (GREEN fáze)  
4. **Refaktoruj** - Vylepši kód, dokud testy stále procházejí (REFACTOR fáze)

**Testovací frameworky:**
- Backend: `pytest` v `backend/tests/`
- Frontend: `jest` a `@testing-library/react`

**Struktura testů:**
- `backend/tests/test_nazev_funkce.py` - unit testy backend funkcí
- `frontend/components/__tests__/` - testy React komponent
- Tests by měly pokrývat: happy path, error cases, edge cases

**Povinné pokrytí:**
- Všechny API endpointy musí mít testy
- Klíčové business logiky musí mít testy
- Auth a RBAC musí mít testy
- Nové komponenty musí mít testy

**Spuštění testů:**
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`
- Před commitem: Vždy spusť všechny testy
