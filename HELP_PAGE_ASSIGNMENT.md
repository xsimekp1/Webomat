# Help Page Assignment

## Zadání: Stránka „Nápověda (beta)“ — Webomat / Webomat Platform

> Tohle je zatím rámcová nápověda „jak to celé funguje“. Budeme ji postupně zpřesňovat podle toho, jak bude aplikace růst.

---

## 1) Co je Webomat

Webomat je platforma pro:
- **sběr leadů / kontaktů** (firmy, které typicky nemají web, ale mají dobré hodnocení),
- **řízení obchodního procesu** (CRM: kontakt → deal/projekt → follow-up),
- **automatizovanou tvorbu webu** (generování webové stránky pomocí AI),
- **správu verzí webu** pod jedním projektem,
- a do budoucna **fakturaci a provize** (pro klienty i obchodníky).

---

## 2) Jak vypadá tok práce (high-level workflow)

### A) Získání kontaktu
Kontakt může přijít z více zdrojů:
- **automaticky** (Webomat skript hledá podniky z Google Places a filtruje dle ratingu / recenzí a hlavně bez webu),
- **ručně** (někdo zadá kontakt v UI – typicky obchodník nebo admin),
- (do budoucna) import / externí zdroje.

### B) CRM kvalifikace a práce s kontaktem
Na kontaktu držíme:
- identifikační info (název, IČO, adresa, telefon, email),
- stav v CRM (např. *nový, osloven, ozvat později, jednáme, vyhráno, prohráno*),
- plánování (datum prvního kontaktu, poslední kontakt, další follow-up),
- vlastníka (komu kontakt patří / kdo za něj nese odpovědnost),
- poznámky a důvod stavu (proč je *ozvat později* apod.).

### C) Deal / Projekt
Z kontaktu typicky vznikne:
- **Deal (obchodní případ)** = obchodní „obal“,
- který se váže na **Klienta (kontakt / firmu)**,
- a klient může mít **více dealů / projektů** (víc webů nebo víc iterací v čase).

### D) Zadání webu a generování
U dealu/projektu se vyplní zadání:
- **přesný text** (co musí být na stránce slovo od slova),
- **volná část** (může se přeformulovat),
- **inspirace** (až 3 odkazy na weby, které se klientovi líbí),
- **asset management** (které fotky/logo *musí* být použité a které jsou jen *volitelné*),
- případně další volby (styl, tone of voice, sekce webu, barvy).

Generování vytvoří:
- **novou verzi webu** v rámci dealu,
- uloží se **zdrojový kód** (HTML/CSS/JS nebo jiný formát),
- uloží se **náhled** (např. JPG screenshot),
- a ideálně se neukládají duplicitně stejné assety.

---

## 3) Role a přístupy (RBAC)

### `admin`
- vidí a spravuje vše (uživatele, nastavení, data, finance),
- má přístup na produkční i test data,
- řeší konfigurace, schvalování, audit.

### `seller` (sales agent)
- pracuje s produkčními daty,
- vidí hlavně své kontakty/dealy (podle ownership),
- může zakládat kontakty, dealy, psát poznámky, plánovat follow-upy,
- do budoucna vidí své provize (spíš read-only).

### `reviewer` (tester / UX reviewer)
- slouží k ukázkám a testování bez rizika,
- vidí aplikaci „jako seller“ (agent UI),
- ale pracuje jen v **TEST režimu**:
  - může zakládat test kontakty a test dealy,
  - může simulovat provize a faktury,
  - **nesmí spouštět drahé akce** (např. AI generování tokeny) → jen preview/simulace.

> Základní princip: produkční data = reálný provoz, test data = sandbox.

---

## 4) Test režim (sandbox)

Platforma může mít vedle běžných dat také **testovací data**:
- Test kontakt/deal se označí jako `TEST` (např. `env=test`).
- `seller` standardně **nevidí** test data.
- `admin` vidí oboje.
- `reviewer` vytváří a upravuje jen test data.

Proč:
- aby šlo bezpečně zkoušet validace, formuláře, workflow a UI bez toho,
  že se „zašpiní“ reálná pipeline nebo se spálí tokeny.

---

## 5) Data v databázi (Supabase / Postgres)

Aktuální kontakt (zjednodušeně) má pole jako:
- `id` (uuid)
- `source` (odkud kontakt přišel)
- `place_id` (pokud přišlo z Google Places)
- `name, ico, vat_id`
- `address_full, city, postal_code, country, lat, lng`
- `phone, email, website, has_website`
- `rating, review_count, price_level, types (json)`
- `editorial_summary`
- `status_crm, status_reason`
- `owner_seller_id`
- `first_contact_at, last_contact_at, next_follow_up_at`
- `created_at, updated_at`

Důležité koncepty:
- **owner** (komu kontakt patří)
- **status** (jaký je stav v pipeline)
- **follow-up** (co je další krok a kdy)
- (doporučeno) `env` / `is_test` pro oddělení test dat.

---

## 6) Fakturace a provize (výhled)

### Faktury (výhled)
Budou typicky dvě větve:
- faktury **pro klienty** (za web / služby),
- faktury nebo výplaty **pro obchodníky** (provize).

V systému se bude hodit:
- `invoice drafts` (náhled, bez čísla),
- `issued/sent/paid` (produkční režim),
- reviewer může dělat jen **preview v testu**.

### Provize (výhled)
Doporučený přístup je „ledger“:
- provize se počítají z transakcí (earned / adjustment / payout),
- reviewer může vytvářet jen **simulované** položky (bez dopadu).

---

## 7) UI: hlavní stránky (co se očekává)

### Kontakty (CRM)
- seznam kontaktů (filtry: status, owner, zdroj, město, má web/nemá web, rating),
- detail kontaktu (timeline aktivit, změny statusu, plán follow-upu),
- vytvoření / edit kontaktu (ruční zadání).

### Dealy / Projekty
- seznam dealů (pipeline),
- detail dealu:
  - základní info,
  - zadání webu,
  - verze webu a náhledy,
  - soubory a assety,
  - historie a poznámky.

### Generování webu
- formulář zadání (exact text, flexible text, inspirace, assety),
- vytvoření nové verze,
- náhled, diff, stažení/preview, publikace (výhled).

### Admin sekce
- uživatelé a role,
- nastavení (zdroje, integrace, šablony),
- finanční přehledy (faktury, provize),
- audit a logy.

---

## 8) Backend a provoz (současný stav)

Aktuálně:
- backend logika je v **Pythonu** (Webomat skripty),
- UI je **Streamlit** (server běží a vystaví se na port),
- databáze je **Supabase (Postgres)**.

Skripty v Pythonu typicky řeší:
- sběr dat (Google Places / geocoding),
- filtrování (rating, recenze, bez webu),
- ukládání do DB,
- správu gridu (prohledané oblasti),
- exporty,
- a generování webu (zatím placeholder / budoucí AI worker).

---

## 9) Bezpečnost a náklady (API / tokeny)

- platforma počítá náklady na API volání (cost tracking),
- "drahé operace" mají potvrzení (např. grid search),
- AI generování má být řízené (role gating + budget),
- reviewer nesmí spouštět generování, jen simulovat.

---

## 10) Často kladené otázky (zatím základ)

### Proč některé kontakty nevidím?
- můžeš mít filtr (status, owner),
- nebo jsi v roli `seller` a kontakt je v `TEST` režimu,
- nebo kontakt patří jinému obchodníkovi.

### Jak poznám, že je něco testovací?
- v seznamu a detailu bude badge `TEST`,
- (do budoucna) bude přepínač prostředí nebo jasný banner.

### Proč mi nejde vygenerovat web?
- můžeš být `reviewer` → generování je zablokované,
- nebo je vyčerpán budget,
- nebo není vyplněné zadání.

---

## 11) Co doplníme do další verze nápovědy
- přesné definice statusů v CRM (jednotná pipeline),
- jak přesně funguje "owner / assignment",
- jak se ukládají assety a jak funguje jejich výběr,
- jak přesně funguje verzování webu (co je "verze", co je "release"),
- pravidla fakturace a provizí,
- doporučené best practices pro obchodníky (skripty, follow-upy, timing).