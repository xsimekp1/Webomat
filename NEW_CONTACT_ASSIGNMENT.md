# New Contact Assignment

## Zadání: Stránka „Nový kontakt“ (ruční zadání)

### Kontext

V CRM potřebujeme stránku pro ruční vložení nového kontaktu (firma/podnik). Kontakt může pocházet z více zdrojů (webomat, ruční, doporučení, import…), ale tato stránka řeší manual entry.

Cíl:
- rychle zadat kontakt s minimem polí,
- co jde, dopočítat / dotáhnout automaticky (geokódování, normalizace, has_website…),
- standardizovat hodnoty přes dropdowny/radia (statusy, zdroje, země…),
- umožnit přiřadit "kdo kontakt sehnal" (kvůli provizi/odměně),
- připravit data tak, aby se dal kontakt rovnou přiřadit obchodníkovi.

### UX principy

Form bude rozdělený do 3 bloků:
- Základ (povinné / nejčastější)
- CRM (stav + vlastník + follow-up)
- Pokročilé (IČO/DIČ, GPS, rating, typy…) – collapsible "Advanced"

Inline validace + autocompletion kde to dává smysl.

"Save" i "Save & New" (uložit a hned nový).

Duplicate detection při psaní (name + city / phone / place_id).

## 1) Form – pole a komponenty

### A) Základní informace (MVP)
- **Název podniku**: Field: name (text, required). Validace: min 2 znaky. Duplicate hint: pokud existuje podobný název ve stejném městě → upozornit.
- **Zdroj kontaktu**: Field: source (dropdown, required). Hodnoty: manual (ručně) (default), webomat, referral (doporučení), scrape, import_csv, partner. Pozn.: u "manual" umožnit volitelné pole "poznámka ke zdroju".
- **Kontakty**: Field: phone (tel, optional), email (email, optional), website (url, optional). Best practice: povol alespoň jedno z {phone, email, website} – jinak je to "dead lead".
- **Adresa**: Field: address_full (textarea / 1-line address input), city (text, optional), postal_code (text, optional), country (dropdown, default CZ). Autofill návrh: Pokud vyplní address_full, klikne na "Doplnit adresu" → systém doplní city, postal_code, country, lat/lng (geocoding).

### B) CRM část (vlastnictví + stav)
- **Kdo kontakt sehnal (finder)**: Field: found_by_user_id (dropdown/roll-up z aktivních uživatelů).
- **Obchodník / vlastník kontaktu**: Field: owner_seller_id (dropdown z aktivních sellerů). Default: aktuálně přihlášený uživatel.
- **Status CRM**: Field: status_crm (radio). Hodnoty: new, contacted, follow_up, qualified, won, lost, do_not_contact.
- **Důvod**: Field: status_reason (textarea, jen když follow_up/lost/do_not_contact).
- **Termíny**: first_contact_at (datetime, tlačítko "Nastavit teď" + datepicker), next_follow_up_at (datetime, datepicker + quick buttons "+2 dny / +7 dní / +14 dní"), last_contact_at (read-only).

### C) Pokročilé (collapsible)
- **Identifikátory**: ico (text, 8 číslic pro CZ), vat_id (text), place_id (text).
- **Web flag**: has_website (radio: Ano/Ne/Neznám, ale automaticky z website).
- **Geodata**: lat, lng (read-only po geocodingu) + "upravit ručně" toggle.
- **Google kvalita**: rating, review_count, price_level, types, editorial_summary (schovat do Advanced).

## 2) Co je zbytečné vyplňovat ručně / co automatizovat
- **Automatizovat**: has_website (z website), created_at/updated_at, lat/lng (geocoding), normalizace (phone E.164, website strip slash, email lowercase).
- **Nevyžadovat**: rating, review_count, price_level, types, editorial_summary, place_id.

## 3) Co dát jako dropdown / radio (best practice)
- **Dropdowny**: source (enum), country (CZ, SK, …), owner_seller_id, found_by_user_id.
- **Radio**: status_crm.
- **Multi-select**: types (jen z Google Places).

## 4) Doporučené změny tabulky (aby UI dávalo smysl)
- **Přidat “kdo kontakt sehnal”**: found_by_user_id uuid nullable (FK na users), found_at timestamptz.
- **Statusy jako enum**: status_crm enum.
- **Source jako enum/constraint**.

## 5) Validace a logika při uložení
- **Minimální požadavky**: name, source, alespoň jeden kontakt (soft warning).
- **Duplicate detection**: place_id hard, (name + city) podobnost warning, phone/email exact match.
- **Po uložení**: redirect na detail nebo "Save & New".

## 6) Layout návrh (rychlé a přehledné)

Levý sloupec: name, source, found_by, owner_seller  
Pravý sloupec: phone, email, website  
Adresa: full width + "Doplnit adresu & souřadnice"  
CRM box: status radio, follow-up date picker, reason (conditional)  
Advanced collapsible: ico, vat_id, place_id, rating/reviews/price/types/editorial_summary, lat/lng override

Poznámka: “co je zbytečně v tabulce?” Ta tabulka je mix contact + enrichment (Google Places) + CRM. To není špatně pro MVP, ale pro čistotu do budoucna: “enrichment fields” by šly do separátní tabulky contact_enrichment (1:1), ale teď to klidně nech v jedné tabulce a jen to schovej do Advanced + automatizuj.