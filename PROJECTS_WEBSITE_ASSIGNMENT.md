# Projects (Deals) + Website Generation (Versions) + Assets Assignment

## Zadání: Webomat / WebyWeby – Projekty (Dealy) + Generování webu (verze) + Assety

### 1) Principy datového modelu (high level)

#### Entity vztahy
- **Kontakt / Podnik (contacts)** → může mít víc projektů (1:N)
- **Projekt / Zakázka (projects / deals)** → obsahuje kompletní zadání pro web, má víc verzí (1:N)
- **Verze webu (project_versions)** → výstup generátoru, preview, veřejný link, stav, schválení
- **Assety (project_assets)** → fotky / loga / dokumenty (nahrané klientem nebo interně), používají se napříč verzemi bez duplikace
- **Uživatelé (users / profiles)** → admin / sales / reviewer-tester

### 2) UX flow: vytvoření nového projektu z karty podniku

#### UI na kartě podniku (Contact detail)
- Vpravo panel "Projekty / Zakázky"
- Seznam existujících projektů (název, stav, poslední aktivita, cena)
- Tlačítko: ➕ Nová zakázka / projekt

#### Po kliknutí "Nová zakázka / projekt"
- Vytvoří se projects záznam: contact_id = aktuální podnik, owner_seller_id = automaticky převzít z podniku
- Předvyplnit některé pole (např. název projektu = "Web – {název podniku}")

### 3) Tabulka projects (co má projekt obsahovat)

#### A) Identifikace & obchod
- id (uuid), contact_id (uuid, FK -> contacts), owner_seller_id (uuid, FK -> profiles/users)
- name (text), status (enum: draft, ready_for_generation, generating, review, sent_to_client, approved, delivered, cancelled)
- estimated_price (numeric), currency (default CZK), expected_deadline (date), priority (radio: low/normal/high)

#### B) Doména & hosting
- domain_status (radio: unknown / client_has_domain / client_wants_new_domain / we_manage_domain)
- desired_domain (text), current_domain (text), domain_registrar_note (text)
- hosting_status (radio: unknown / client / platform / other), dns_access (radio: have_access / need_access / not_needed_yet)

#### C) Obsah webu
- must_include_text (long text), rewriteable_text (long text)
- sections (jsonb: About / Services / Pricing / Gallery / Reviews / FAQ / Contact)
- contact_form_enabled (bool), contact_form_recipients (text), contact_form_cc (text), contact_form_spam_protection (radio: none / honeypot / recaptcha)

#### D) Design & brand
- style_feel (radio: modern / classy / playful / luxury / minimalist / bold / corporate)
- color_scheme: primary_color (hex), secondary_color (hex), avoid_colors (text)
- typography_preference (radio: clean / elegant / playful / doesn't_matter)
- tone_of_voice (radio: formal / friendly / salesy / expert / casual)
- brand_assets_note (text)

#### E) Inspirace weby
- inspiration_url_1,2,3 (text), inspiration_notes (text)

#### F) Fotky a další assety
- assets_brief (text), pravidla přes asset flagy

#### G) Audit & metadata
- created_at, updated_at, archived_at (nullable), is_test (bool)

### 4) Jak budeme storovat fotky
- **Supabase Storage**: Bucket project-assets, struktura project-assets/{project_id}/{asset_id}/{filename}
- **Tabulka project_assets**:
  - id, project_id, uploaded_by_user_id, storage_bucket, storage_path, filename_original, mime_type, size_bytes, width/height, checksum, kind (photo/logo/doc/other)
  - must_use (bool), allowed (bool), blocked (bool), caption (text), created_at
- **UI**: Grid náhledů, toggles MUST/OK/BLOCK
- **Generátor**: Použije jen allowed=true AND blocked=false + must_use extra

### 5) Tabulka project_versions (verze webu)
- id, project_id, version_number, status (created/generating/ready/failed/archived)
- generator_model, generator_prompt_snapshot
- source_bundle_path (zip ve Storage), preview thumbnail_asset_id
- public_slug (unique), public_enabled (bool), public_expires_at
- created_by_user_id, created_at

### 6) Vazba: které assety použila konkrétní verze
- **Tabulka project_version_assets**: version_id, asset_id, role (hero/gallery/logo/background/misc), created_at

### 7) Mazání a archivace starých verzí
- Retention: Neposlané verze >365 dní → archived_candidate
- Cron job: Označ marked_for_deletion_at
- Admin UI: Smazat zdrojáky/vše po 30 dnech

### 8) Radio buttony / checklisty
- Funkce: Kontaktní formulář, klikatelné tel, mapka, rezervační odkaz, ceník, fotogalerie, recenze, GDPR cookies
- Dodání: Landing/multi-page/one-page, Jazyk CZ/EN, SEO základ, Analytics
- Asset policy: Stock fotky, ikonky, AI obrázky

### 9) Co ještě doplnit do projektu
- delivery_notes, client_approver_name/email, legal_texts (json), billing_note, internal_notes

### 10) Admin / Sales / Reviewer – přístup a testovací režim
- Test projekty: is_test=true, nezobrazují se sales, blokace generátoru, test ledger

### 11) Kde ukládat "vygenerovaný web" a jak ho zobrazit
- Storage: project-versions/{project_id}/{version_id}/build.zip
- Preview: Rozbal/servíruj staticky, nebo deploy na preview hosting

### 12) Proces schválení klientem a automatické generování smlouvy
- Klient vidí preview verze přes public_slug URL
- UI pro klienta: Tlačítka "Odmítnout" (s komentářem), "Schválit s připomínkami", "Finálně potvrdit"
- Při "Finálně potvrdit":
  - Projekt status → approved
  - Automaticky generovat smlouvu (PDF) z templates
  - Smlouva obsahuje: údaje klienta (z contacts), projekt detaily (název, cena, deadline), právní texty (z legal_texts), podpisy
  - Uložit do Storage: project-contracts/{project_id}/contract.pdf
  - Odeslat emailem klientovi + adminovi
  - Vytvořit záznam v tabulce contracts: id, project_id, status (generated/sent/signed), pdf_path, sent_at
- Pokud "Schválit s připomínkami": Zpětná vazba do notes, status → review, notifikace sales
- Pokud "Odmítnout": Status → cancelled, poznámka, notifikace

## DRY RUN Mode (implementováno)
- Endpoint: POST /website/generate
- Parametr: dry_run (boolean)
- Pokud dry_run=true: vrátí dummy HTML stránku místo volání Claude API
- Dummy stránka: kompletní HTML s "Dry run test web" obsahem, gradient background, stylizované tělo
- Umožňuje testovat printscreen a thumbnail funkcionality bez nákladů
- UI: Modal s možností výběru mezi DRY RUN a AI generováním (AI zatím disabled)