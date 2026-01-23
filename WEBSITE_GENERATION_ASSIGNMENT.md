# Website Generation Assignment

## Zadání: Okno „Automatizovaná tvorba webu“ (vázané na Deal/Projekt)

### Kontext a cíl

V aplikaci (admin/tenant/klient portál) potřebujeme nový modul/okno pro automatizovanou tvorbu webové stránky pomocí AI (Claude). Funkce bude vázaná na Deal (alias Projekt). Jeden klient může mít více dealů/projektů. Cílem je:

- zadat strukturovaný brief (co musí být přesně / co lze přeformulovat),
- přiložit inspirace a assety,
- spustit generování,
- ukládat výstupy jako verze pod daný deal (včetně náhledu),
- umožnit iterace (verzování),
- řešit ukládání zdrojového kódu i assetů efektivně (bez duplikace obrázků).

## Klíčové entity (doménový model)

1. **Client (Klient)**  
   může mít N dealů/projektů

2. **Deal / Project (Projekt)**  
   vazba na Client  
   má své stavy (lead, zadání, in progress, hotovo, fakturace…)

3. **Website Generation Request (Zadání generování)**  
   patří pod Deal  
   obsahuje všechny inputy (texty, inspirace, volby assetů)  
   může mít více běhů/generací (job runs)

4. **Website Version (Výstup / Verze webu)**  
   patří pod Deal (nebo přímo pod Request)  
   obsahuje vygenerovaný kód, metadata, náhled  
   navazuje na předchozí verzi (optional)

5. **Asset (Soubor)**  
   obrázky/loga/fotky od klienta atd.  
   ukládají se jednou, více verzí je jen referencuje

## UI: „Okno“ / stránka v aplikaci (pod Dealem)

### Navigace
Detail Dealu → tab/sekce: Web / Generování webu

Zobrazuje:
- Formulář zadání (request)
- Historii verzí (timeline/list)
- Preview aktuální verze + diff / compare (v budoucnu)

### 1) Formulář zadání (Website Generation Request)

#### A) „Co musí být přesně“ (word-for-word)
- Pole: Exact copy (must be used verbatim)
- multi-line textarea
- explicitní instrukce: „Tento text musí být na webu slovo od slova, bez úprav.“
- Doporučená struktura uvnitř: H1 headline, claim, kontakty, právní texty / disclaimers, ceník / služby (pokud přesně)
- Validace: minimálně 1 znak pokud uživatel chce „Strict“ režim
- ukládat včetně formátování (Markdown / plain text — rozhodni; doporučuju Markdown)

#### B) „Text, který lze přeformulovat“ (AI může upravit)
- Pole: Flexible copy (can be paraphrased)
- multi-line textarea
- instrukce: „Můžeš přeformulovat, zachovej význam.“

#### C) Struktura webu (co tam má být)
- Pole: Required sections (checkboxy + reorder)
- checkboxy + možnost přidat vlastní: Hero (headline, subheadline, CTA), Služby, Reference / ukázky, O nás, FAQ, Ceník, Kontakt, Footer (copyright, GDPR link)
- každý section může mít „notes“ pole

#### D) Brand / styl
- Pole: Brand name, Tone of voice (friendly / pro / luxury / playful / minimal), Primary color, Secondary color (volitelné), Font preference (volitelné), Design style (minimal / bold / corporate / cute / modern / brutalist / …), Language (CS default), Target audience (1–2 věty)

#### E) Inspirace (až 3 weby)
- 3 okénka — repeatable field, limit 3.
- Pro každý inspirační web: URL input, „Co se mi líbí“ textarea (např. layout / barvy / menu / sekce), volba „přiblížit styl / jen inspirace“
- Pozn.: URL samotné nestačí; AI často potřebuje popis „co konkrétně“.

#### F) Funkce a omezení (checkboxy)
- Jednostránkový web (landing)
- Vícestránkový (Home / Služby / Kontakt)
- Formulář (odeslání na email / webhook)
- Cookie lišta (placeholder)
- SEO basics (title, meta description, h1/h2)
- Přístupnost základ (kontrast, alt text)
- Performance: minimal JS
- Hosting target (Netlify/Vercel/“static export”)

#### G) Assety od klienta (upload + výběr)
- Upload zóna: drag&drop soubory (jpg/png/webp/svg/pdf)
- kategorizace: logo, photos, icons, documents
- automatická deduplikace (hash)
- Asset picker: U každého assetu náhled, název, typ, tagy, přepínač použití: MUST_USE (musí být použito), MAY_USE (může použít), DO_NOT_USE (nesmí použít), volitelné: „kde“ (Hero / About / Gallery / Services), volitelné: „poznámka“

#### H) Výstupní formát (co má Claude vytvořit)
- volba: Static HTML/CSS/JS (nejjednodušší), Next.js (budoucí scaling)
- pro start doporučuju: Static (rychlejší, méně problémů)
- volitelné: „1 zip“ vs „repo struktura“

#### I) Generování loga s Midjourney
- Radio button: „Chcete logo k projektu?“ (Ano/Ne)
- Pokud Ano: Automatické generování loga přes Midjourney API
- Prompt: Založeno na brand name, tone, style z formuláře
- Výsledek: Přidáno do project_assets jako logo (kind=logo)
- Pozn.: API pro Midjourney bude integrováno samostatně

#### J) Spuštění generování
- Button: Vygenerovat novou verzi
- před spuštěním: vytvořit generation_request, vytvořit generation_run (status queued/running/failed/done)
- po dokončení: vytvořit website_version (včetně preview), ukázat logy / progress

### 2) Výsledek: Verze pod dealem
Každá verze by měla obsahovat: version_number (1,2,3…), created_at, created_by (admin/tenant), prompt_snapshot (co přesně šlo do AI), output_format (static/nextjs), status (draft/approved/published), notes (volitelné: co se změnilo oproti minule)

#### Co ukládat jako artefakty
- **Zdrojový kód**: Supabase Storage = ZIP + metadata v DB
- **Náhled (JPG/PNG)**: Ulož do Storage jako image
- **Neduplicitní obrázky**: Assety se ukládají jednou do assets, Verze má jen vazbu website_version_assets s referencí na assety

## Supabase: návrh ukládání (DB + Storage)

### Storage buckety
- assets — klientské fotky, loga, uploady
- website_versions — zipy verzí + preview images

### Tabulky (minimální návrh)
```sql
clients
  id (uuid)
  name
  ico (optional)

deals
  id (uuid)
  client_id (fk)
  name
  status
  owner_seller_id (fk -> sellers/users)

assets
  id (uuid)
  client_id (fk) nebo deal_id
  storage_path (text)
  file_name
  mime_type
  size_bytes
  sha256 (text) ← deduplikace
  width/height (optional)
  created_at

deal_assets
  deal_id
  asset_id
  role/tag (logo, photo, doc)

website_generation_requests
  id (uuid)
  deal_id
  exact_copy (text/markdown)
  flexible_copy (text/markdown)
  sections (jsonb)
  brand (jsonb)
  inspirations (jsonb) ← max 3
  constraints (jsonb)
  output_format (text)
  created_by
  created_at

website_request_asset_rules
  request_id
  asset_id
  rule (enum: MUST_USE / MAY_USE / DO_NOT_USE)
  preferred_section (text, optional)
  note (text, optional)

website_generation_runs
  id
  request_id
  status (queued/running/failed/done)
  started_at
  finished_at
  error (text)
  ai_model (text)
  prompt_snapshot (text)
  token_usage (jsonb, optional)

website_versions
  id
  deal_id
  request_id
  run_id
  version_number (int)
  storage_zip_path (text)
  preview_image_path (text)
  commit_message / notes (text)
  created_at
  created_by

website_version_assets
  version_id
  asset_id
  usage_note (optional)
```

## Co bych přidal navíc (hodně užitečné v praxi)
- **Approval flow**: verze má status: draft → approved → published, klient může „approve“
- **Komentáře k verzi**: klient/tenant může napsat feedback
- **Changelog**: prompt obsahuje „co změnit oproti minule“, UI pole „Změny proti poslední verzi“
- **Generování více variant**: checkbox „vygeneruj 3 varianty“, ukládá jako 1a/1b/1c
- **Bezpečné použití externích fotek**: toggle „Smí použít pouze klientské assety“, „placeholder fotky“, „icon set“

## Jak to má Claude dělat (logika generování)
Claude dostane: prompt = strukturované zadání + pravidla pro exact/flexible text, seznam assetů s MUST/MAY/DO_NOT, inspirace URL + „co se mi líbí“, cílový tech output.

Claude musí vrátit: strukturovaný výstup: index.html, styles.css, script.js, assets_used[], notes. Systém pak uloží do Storage.

## Praktické rozhodnutí: kam ukládat verze a náhled
Supabase Storage na: zip s kódem, preview image, assety.

Deduplikace: spočítat sha256 při uploadu, pokud už existuje, jen vazba.

Preview: server-side (Playwright screenshot), uložit jako website_versions/{deal_id}/{version_id}/preview.jpg

## Výstupy, které chci implementovat teď (MVP)
- Form zadání (exact + flexible + inspirace 3 + asset picker s MUST/MAY/NO)
- Button generovat → vznikne verze (zip + preview)
- Seznam verzí pod dealem + možnost otevřít preview a stáhnout zip
- Bez duplikace assetů mezi verzemi

Aby to bylo v kontextu se současnou architekturou, pravděpodobně bude doplňovat nějaké nové sloupce v databázi, nejspíš i nové tabulky... zatím řešíme tu vrstvu vstupu, nepotřebujeme definovat tu vrstvu posílání zadání do claude code, které vytvoří tu samotnou webovou stránku, případně se mě ptej, kde si nebudeš jistý.