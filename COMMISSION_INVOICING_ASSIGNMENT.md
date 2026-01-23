# Commission Invoicing Assignment

## Zadání: Fakturace provizí (Sales agent → platforma) + schvalování + proplacení

### Cíl
Obchodní zástupce (sales agent) si sám vygeneruje fakturu na provize v aplikaci:
- systém předvyplní data (údaje agent/platforma, období, text, částky)
- agent může upravit číslo faktury i text
- agent může zvolit částku k vyplacení (default: vše)
- po odeslání jde faktura do schvalovacího procesu adminovi
- po schválení se provede účetní dopad do ledgeru (snížení nároku na vyplacení)
- agent stav uvidí na dashboardu (bez potřeby tabulky „zprávy“)

---

## Role a oprávnění
### Sales agent
- Vidí svoje saldo a pohyby (provizní ledger)
- Může vytvořit fakturu
- Může upravit:
  - číslo faktury (v rámci validací)
  - text faktury
  - částku k vyplacení (≤ dostupné saldo)
- Vidí stav faktur (draft → submitted → approved/paid/rejected)

### Admin
- Vidí všechny faktury
- Schvaluje / zamítá
- Nastavuje platform billing profil (název firmy, IČO, DIČ, adresa, bankovní účet, podpis apod.)
- Spouští „send to payout“ (ručně / exportem / webhookem do účetnictví)
- Uzavírá „paid“ po reálném proplacení (nebo automaticky dle napojení)

### Reviewer / Tester
- Může vytvořit **testovací fakturu** (flag test) a poslat ji do schvalování
- Může projít celý flow schválení, ale:
  - nic reálně neodepisuje z ostrého salda (nebo odepisuje jen v test ledgeru)
  - nesmí spustit reálné generování plateb / účetní export
  - vidí UI jako agent (ideálně), s pár admin pohledy navíc jen pro UX kontrolu

---

## Vstupy a data (co se předvyplní)
### 1) Údaje sales agenta (z profilu)
- jméno / firma, IČO, DIČ (pokud má), adresa, email, telefon
- bankovní účet (IBAN / CZ účet) pro výplatu
- preferovaný formát fakturačního čísla (nepovinné)
- poslední použité fakturační číslo (z historie)

### 2) Údaje platformy (z admin nastavení)
- název firmy, IČO, DIČ, adresa
- bankovní účet (kam agent fakturuje)
- kontakt / email pro faktury
- případně „text do patičky“ / podpis

### 3) Provizní data (z ledgeru)
- dostupné saldo k vyplacení (může být i záporné)
- doporučené období fakturace:
  - nejstarší nevyplacená provize → nejnovější nevyplacená provize
- rozpad částek (volitelně pro přílohu)

---

## Business pravidla (validace)
1) Pokud je agentovo saldo **0 nebo < 0**:
   - UI: hláška „Není co fakturovat“ (nebo „Saldo je záporné, kontaktujte admina“)
   - tlačítko vytvořit fakturu disabled

2) Pokud je saldo **< 20 000 Kč**:
   - povolit fakturovat jen pokud agent **nefakturoval posledních 30 dní**
   - kontrola: poslední faktura se stavem `submitted/approved/paid` (dle definice) + datum

3) Částečná výplata:
   - agent může zvolit částku k vyplacení: `0 < amount_to_payout <= available_balance`
   - default je `available_balance` (tj. „vyplatit vše“)

4) Fakturační číslo:
   - systém navrhne číslo na základě poslední faktury agenta
   - agent může číslo upravit ručně, ale musí projít validací:
     - unikátnost per agent (aby neměl duplicity)
     - rozumný formát (min délka, povolené znaky), ale nesmí být přehnaně restriktivní

5) Test faktury:
   - test faktury se nepočítají do 30denního limitu (nebo volitelně ano – doporučení: NE)
   - test faktury nepíšou do ostrého ledgeru

---

## Inteligentní návrh čísla faktury (auto-increment)
### Požadavek
Agent může fakturovat i jinde, takže:
- defaultně navrhni „o 1 víc“ než minule
- ale umožni přepsat

### Logika návrhu (heuristika)
- vezmi poslední fakturační číslo agenta (např. `0001-2026`)
- najdi **poslední číselný blok**, který dává smysl inkrementovat:
  - `0001-2026` → inkrementuj `0001` (rok nech)
  - `INV-2026-0012` → inkrementuj `0012`
  - `2026-15` → inkrementuj `15`
- zachovej šířku s nulami:
  - `0001` → `0002`
  - `0099` → `0100`

Pozn.: pokud algoritmus selže (nebo číslo je “divné”), fallback je:
- `YYYY-0001` nebo `0001-YYYY` (podle nastavení platformy), ale agent může přepsat.

---

## UI flow (Sales agent)
### Stránka: „Vytvořit fakturu“
**Sekce A: Přehled**
- Available balance: `X Kč`
- Doporučené období: `od DD.MM.YYYY do DD.MM.YYYY`
- Poslední fakturováno: `DD.MM.YYYY` + info o pravidle 30 dní (pokud je saldo < 20k)

**Sekce B: Fakturační údaje**
- Fakturační číslo (input) + tlačítko „Navrhnout“
- Datum vystavení (default: dnes)
- Datum splatnosti (default: +14 dní / admin nastavení)
- Měna (default CZK)

**Sekce C: Částka**
- Radio:
  - (x) Vyplatit vše (auto vyplní)
  - ( ) Vyplatit část: [částka input]
- Volitelně detailní rozpad provizí (read-only tabulka pro agentovu kontrolu)

**Sekce D: Text faktury**
- Předvyplněno:
  - „Fakturujeme za obchodní činnost v období {from}–{to} dle partnerské smlouvy.“
- Editor (textarea) – agent může upravit text
- Checkbox „vložit rozpad provizí jako přílohu (PDF)“ (volitelné)

**Sekce E: Náhled a akce**
- Náhled PDF (nebo aspoň HTML preview)
- Buttons:
  - Uložit jako koncept (draft)
  - Odeslat ke schválení (submitted)

Po odeslání:
- stav faktury se změní na `submitted`
- agent uvidí na dashboardu kartu „Čeká na schválení“

---

## Schvalovací proces (Admin)
### Stránka: „Schvalování faktur“
Filtry:
- status: submitted / approved / paid / rejected / test
- agent
- období

Detail faktury:
- kontrola údajů + text + částka
- případně varování:
  - saldo se změnilo od vytvoření faktury (někdo připsal/odepsal ručně)
  - agent zvolil částku < max (OK)
  - fakturační číslo je atypické (jen info)

Akce admina:
1) **Schválit**
   - status → `approved`
   - vytvoří se ledger položka typu `payout_reserved` nebo rovnou `payout_approved` (viz níže)
   - agentovi se tím **sníží dostupné saldo** (nárok na vyplacení)

2) **Zamítnout**
   - status → `rejected`
   - vyplní důvod (textarea), uloží se do faktury
   - žádný dopad do ledgeru
   - agent uvidí důvod v detailu faktury

3) **Odeslat k proplacení**
   - jak: MVP doporučení:
     - vygenerovat PDF + „platební instrukce“ (bankovní účet agenta, částka, VS/číslo faktury)
     - export CSV pro účetní
     - nebo ručně „kliknu zaplaceno“ po převodu
   - status → `paid` až po reálném proplacení

---

## Ledger dopad (aby seděly peníze)
### Doporučení: 2-fázově (rezervace → zaplaceno)
Ať je jasno, co je už schválené, ale ještě neodeslané.

- při schválení faktury:
  - vytvořit ledger entry: `payout_reserved` (negativní částka)
  - tím se sníží available balance a agent už to nemůže fakturovat znovu

- při označení paid:
  - vytvořit ledger entry: `payout_paid` (0 nebo jen metadata)
  - nebo změnit rezervaci na paid (ale radši neměnit historii → jen doplnit paid timestamp)

### Alternativa (jednofázově)
- při schválení rovnou odepsat `payout` a status paid až později jen informativně
- nevýhoda: když admin schválí, ale ještě týden nezaplatí, saldo už je pryč (agent se může ptát)

---

## Notifikace agentovi (bez nové tabulky zpráv)
MVP:
- agent uvidí na dashboardu seznam faktur + status badge
- u rejected zobrazit důvod
- volitelně posílat email (až později) – ale teď stačí UI stav

---

## Testovací faktury (Reviewer)
### Jak to udělat „bez škody“
- V tabulce invoices mít boolean `is_test`
- Reviewer může:
  - vytvořit fakturu s `is_test=true`
  - poslat ke schválení
- Admin může schválit/zamítnout, ale:
  - test faktury nepíšou do ostrého ledgeru
  - nebo mají zvláštní ledger účet `test_ledger` (čistší pro audit UX)

UI:
- test faktury označit štítkem „TEST“ + filtrovatelné

---

## Co to znamená pro DB (stručně)
### Tabulka `invoices`
- id, seller_id
- invoice_number (text)
- issue_date, due_date
- period_from, period_to
- currency
- amount_total
- amount_to_payout (pokud umíš mít jen payout část)
- description_text (editable)
- status: draft/submitted/approved/paid/rejected
- rejected_reason (nullable)
- is_test (bool)
- created_at, updated_at
- approved_at, paid_at
- approved_by (admin user id)
- pdf_path (storage reference) + případně checksum/version

### Tabulka `ledger_entries` (už nejspíš máš / plánuješ)
- id, seller_id
- type: commission_earned / admin_adjustment / payout_reserved / payout_paid
- amount (numeric)
- related_invoice_id (nullable)
- notes, created_at
- is_test (bool) nebo separate test scope

### Storage (Supabase)
- PDF faktury: do Supabase Storage bucketu `invoices/`
- volitelně: export CSV `exports/`

---

## Edge cases (na které nezapomenout)
- Agent upraví fakturační číslo na už existující → error
- Mezi vytvořením draftu a odesláním se saldo změnilo → přepočet a varování
- Admin zamítne → agent může „duplikovat“ fakturu jako nový draft
- Agent chce fakturovat méně než minimum → validace > 0
- Saldo < 20k a fakturoval před 14 dny → zablokovat submit a vysvětlit proč

---

## Rozšíření: Faktury přijaté vs. vydané
Rozdělit na dvě tabulky:
- **invoices_received** (přijaté faktury od klientů za weby).
- **invoices_issued** (vydané faktury pro sales za provize).

## Exporty do Excel
V admin: Export faktur do Excel za vybraný rok nebo měsíc.

## Generování vydané faktury
Po schváleném návrhu: Tlačítko "Fakturovat" v projektu → vygeneruje fakturu z template (PDF), vyplněná z klientových iniciál a systémových proměnných (Webomat IČO, adresa).

## Stav faktury a splatnost
- Přepínání stavu na "splacená".
- Pokud po splatnosti: Automaticky vytvoří aktivitu "faktura po splatnosti" pro sales, přiřazenou den po splatnosti.

## Číslování vydaných faktur
Automatické inkrementální číslování pro vydané faktury (např. 2024-001, 2024-002).

## Změna splatnosti obchodníkem
V UI pro vytvoření faktury: Možnost změnit splatnost ze standardních 14 dnů na max 30 dnů.

## Dashboard pro obchodníka: Dodatečná částka
Pod částkou k fakturaci: Menší číslo "+X Kč" jako součet projektů ve stavu "in progress" nebo "approved" (už se pracuje, ale nefakturováno).

## Nová karta pro obchodníky: Graf odměn + seznam faktur
Karta s:
- Graf týdenních odměn.
- Pod tím seznam fakturovaných faktur (včetně nezaplacených).

## Automatizace zasílání faktur účetní
- Měsíční automatické generování emailu s přijatými fakturami (PDF přílohy).
- Text: "Dobrý den, posíláme přijaté faktury za [měsíc/rok]."
- Příznak u faktur: "zasláno účetní" (boolean).
- Workflow: Před odesláním schválení adminem (pending approval).
- Nástroj: Email service (SendGrid/Mailgun) pro generování mailu.

## Admin přístup: Tabulka faktur
V admin sekci: Tabulka faktur (přijaté + vydané) s:
- Jména klientů/sales.
- Stav faktury.
- Červené zvýraznění pro po splatnosti (overdue).
- Filtry: Typ (přijaté/vydané), stav, datum.