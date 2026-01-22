# Sales Representative Management Assignment

## Zadání: Správa sales zástupců (vytváření / editace / deaktivace / „mazání“)

### Cíl
Admin (případně omezeně i reviewer) musí umět spravovat sales zástupce, kteří používají platformu pro prodej webů:
- vytvořit nového sales uživatele (pozvánka / účet / profil / role)
- upravit jeho profil a fakturační údaje
- (bezpečně) „smazat“ = ve skutečnosti **deaktivovat / archivovat**
- zajistit, že data o provizích, fakturách a klientech zůstanou auditovatelná

> Doporučení: **neprovádět hard delete** sales zástupců. Vždy soft-delete (archivace), aby seděla historie (faktury, ledger, projekty).

---

## Role a oprávnění
### Admin
- může vytvořit / editovat / deaktivovat sales zástupce
- může resetovat přístupy (vynutit změnu hesla / zneplatnit session)
- může měnit roli (agent ↔ reviewer / test) dle potřeby
- může nastavovat provizní parametry a výplatní údaje

### Sales agent
- může upravovat pouze svůj profil (omezeně): kontaktní údaje, fakturační údaje, bankovní účet
- nesmí měnit provizní pravidla, status účtu, aktivaci

### Reviewer / Tester
- může vytvořit **testovacího** sales uživatele nebo testovat UX nad test účty
- nemá právo aktivovat reálné proplácení ani měnit citlivé parametry produkčních agentů

---

## Datové entity (co to typicky ovlivňuje)
Sales zástupce je provázaný na:
- `deals / projects` (obchody / web projekty)
- `contacts / clients` (kontakty, leady)
- `ledger_entries` (pohyby: provize, penalizace, payout rezervace)
- `invoices` (fakturace)

Proto: mazání musí zachovat vazby.

---

## Stavové atributy sales zástupce
Minimální „lifecycle“:
- **invited** – pozván, účet ještě nedokončen
- **active** – používá platformu
- **suspended** – dočasně vypnut (např. problém / průser / čeká se na doplnění údajů)
- **archived** – definitivně ukončená spolupráce (soft delete)
- **test** – testovací uživatel (pro reviewera/UX)

---

## 1) Vytvoření sales zástupce (Admin)

### Spouštěč
Admin klikne na **„Přidat sales zástupce“**.

### Předpoklady
- Admin je přihlášen
- Platforma má nastavený „billing profil“ (aspoň základ), aby šla později fakturace
- Nastavené výchozí provizní schéma (globální) nebo možnost vybrat schéma při vytváření

### UI: Formulář „Nový sales zástupce“
**Sekce A – Identita**
- Jméno
- Příjmení
- Email (unikátní, login)
- Telefon (volitelně)
- Role:
  - Sales agent (default)
  - Reviewer (pokud dává smysl)
  - Admin (typicky NE přes tuto stránku)

**Sekce B – Status a typ**
- Status: `invited` (default)
- Checkbox: `test účet` (vytvoří test salesáka)
- Poznámka admina (interní)

**Sekce C – Provize**
- Provizní schéma (dropdown):
  - výchozí
  - vlastní (pokud zavedeš)
- Výchozí provize / odměna (pokud máte jednoduchý model):
  - % nebo fix (radio)
  - hodnota
- Datum podpisu smlouvy (volitelně, ale dobré pro audit)
- Datum založení (auto)

**Sekce D – Fakturační údaje (volitelné při startu)**
- Fakturační jméno / firma
- IČO / DIČ
- Adresa
- Bankovní účet / IBAN

**Akce**
- `Uložit a poslat pozvánku`
- `Uložit bez pozvánky` (draft/čeká)

### Validace
- Email unikátní
- Pokud není `test`, role nesmí být „Reviewer + Admin zároveň“ (pokud nechceš)
- Pokud nastavuješ provize: hodnoty v povoleném rozsahu

### Výstupy
- vytvoří se záznam sales uživatele
- vytvoří se auth účet / pozvánka (ideálně email magic link)
- log/audit: kdo vytvořil, kdy, jaká role, jestli test

---

## 2) Editace sales zástupce (Admin)

### Spouštěč
Admin otevře detail sales zástupce → klikne „Upravit“.

### Co admin může měnit
**A) Profil**
- jméno, telefon, interní poznámky

**B) Role a oprávnění**
- role (agent/reviewer)
- povolit/zakázat přístup k vybraným modulům (pokud budeš mít permissions)

**C) Status**
- active / suspended / archived / test
- důvod změny statusu (povinné při suspend/archived)

**D) Provize**
- změna provizního schématu
- změna sazby (od kdy platí)
- případně “lock” (zamknout provize, pokud je spor)

**E) Fakturační údaje**
- vše, co je potřeba pro faktury (IČO, adresa, účet)
- validace formátu účtu/IBAN (lehce, bez přehnané přísnosti)

### Doporučení: historizace citlivých změn
- pokud změníš provizi, ukládej:
  - `effective_from`
  - kdo změnil
  - poznámka proč

### Výstupy
- update profilu
- audit log (kdo změnil co)

---

## 3) Editace sales zástupce (Self-service)

### Spouštěč
Sales agent → stránka „Můj profil“.

### Co může agent měnit
- telefon
- fakturační údaje (firma/IČO/adresa)
- bankovní účet pro výplatu
- preferovaný formát čísla faktury (volitelně)
- (volitelně) notifikace (pokud budou)

### Co agent nesmí měnit
- role
- provizní parametry
- status účtu
- přidělení klientů / dealů (pokud je to admin-only)

---

## 4) „Mazání“ sales zástupce (správně: deaktivace/archivace)

### Proč ne hard delete
Protože:
- faktury musí zůstat dohledatelné
- ledger (pohyby) musí zůstat auditovatelné
- projekty/dealy musí mít „owner“ v historii

### Spouštěč
Admin klikne „Deaktivovat / Archivovat“.

### Flow: Deaktivace (suspend)
Použít když:
- dočasný problém, čeká se na doplnění údajů, spor, porušení pravidel

**Akce**
- status → `suspended`
- agent se nemůže přihlásit (nebo se přihlásí jen read-only)
- agent nevidí možnost vytvářet faktury / nové kontakty (dle pravidel)

**Validace**
- pokud má agent faktury ve stavu `submitted`, admin dostane varování:
  - „Má otevřené faktury – chcete je nejdřív vyřešit?“

### Flow: Archivace (soft delete)
Použít když:
- spolupráce skončila

**Akce**
- status → `archived`
- disable login
- zabránit vytváření nových akcí
- ale zachovat read-only historii (admin vždy, agent typicky ne)

**Před archivací zkontrolovat**
- saldo v ledgeru:
  - pokud > 0: doporučit vyřešit (vyplatit / dohodnout)
  - pokud < 0: upozornit (dluh / penalizace)
- otevřené faktury: `draft/submitted/approved`
- aktivní dealy: převést na jiného salesáka nebo označit jako „unassigned“

**Výstupy**
- status změněn
- audit log s důvodem
- (volitelně) automatické přeřazení dealů/klientů

---

## 5) Převod portfolia (reassign) – důležitý vedlejší use case
Když sales končí, admin často potřebuje převést:
- kontakty / klienty
- dealy / projekty
- rozpracované follow-upy

### UI
- dropdown „převést na sales zástupce“
- checkboxy:
  - převést pouze aktivní dealy
  - převést i kontakty
  - převést i follow-upy
- potvrzení + audit log

---

## UI návrh stránek
### A) Seznam sales zástupců
Tabulka + filtry:
- status: active/suspended/archived/test
- role
- datum vytvoření
- saldo (read-only)
- počet aktivních dealů
- poslední aktivita

Akce z listu:
- detail
- suspend
- archive
- reassign portfolio

### B) Detail sales zástupce
Karty:
1. Profil + status
2. Provize / nastavení
3. Fakturační údaje
4. Aktivita (poslední login, poslední faktura, poslední deal)
5. Finance (saldo, pending payout, poslední payout)

---

## Doporučené DB pole (high-level)
`sellers` (nebo `users` s rolí)
- id (uuid)
- email (unique)
- first_name, last_name, phone
- role (agent/reviewer/admin)
- status (invited/active/suspended/archived)
- is_test (bool)
- created_at, updated_at
- contract_signed_at, ended_at
- commission_scheme_id / commission_rate
- billing_profile (nebo FK na tabulku)
- last_login_at (volitelně, nebo přes auth logy)
- notes_internal

`billing_profiles`
- seller_id
- company_name, ico, vat_id
- address
- iban / account_number
- invoice_number_format (optional)
- updated_at

---

## Bezpečnost a audit
- RLS:
  - agent vidí jen svůj profil a svoje finanční data
  - admin vidí všechno
  - reviewer vidí:
    - test uživatele + test data
    - případně anonymizované produkční pohledy (bez citlivých údajů)
- Audit log:
  - změny role/status/provize vždy logovat (kdo, kdy, co, proč)

---

## Edge cases
- Admin změní provizi uprostřed měsíce:
  - vyjasnit „od kdy platí“ (effective_from)
- Archivace salesáka s aktivními dealy:
  - nabídnout reassign, jinak zůstane orphaned (nedoporučeno)
- Email už existuje:
  - možnost „pozvat znovu“ nebo „přiřadit roli“ existujícímu účtu
- Test sales účet:
  - nesmí vytvářet reálné payout / faktury do schvalování (jen test flow)