# Advanced Project Features Assignment

## Zadání: Pokročilé funkce pro projekty (1-4 + komentáře)

### 1) Kopírování projektu mezi klienty
- **Popis**: Umožnit duplikaci projektu (s/bez verzí/assets) na jiného klienta, aktualizovat contact_id a owner_seller_id.
- **UI**: Tlačítko "Kopírovat projekt" v detailu projektu, výběr cílového klienta, checkboxy pro verze/assets.
- **Validace**: Kontrola práv (admin/sales), audit log kopírování.
- **DB**: Nové záznamy s novými ID, vazby na cílového klienta.

### 2) Přiřazení projektu jinému obchodníkovi
- **Popis**: Admin/sales mohou převést vlastnictví projektu (owner_seller_id), s notifikací a audit logem.
- **UI**: Dropdown "Přiřadit obchodníkovi" v detailu projektu, potvrzení.
- **Workflow**: Email notifikace novému/starému vlastníkovi.
- **DB**: Update owner_seller_id, log v audit tabulce.

### 3) Žádost o projekt od jiného obchodníka
- **Popis**: Sales může požádat o převod projektu od jiného sales, s potvrzením.
- **UI**: Tlačítko "Požádat o převod" v cizím projektu, textové pole pro důvod.
- **Workflow**: Email žádost vlastníkovi, tlačítko "Schválit/Zamítnout" v notifikaci, audit log.
- **DB**: Nová tabulka transfer_requests (id, from_user_id, to_user_id, project_id, status, reason).

### 4) Šablony projektů
- **Popis**: Předdefinované šablony (e.g., "Basic Website") s default sekcemi/texty, přizpůsobitelné per typ klienta.
- **UI**: Při vytváření projektu, výběr šablony místo prázdného formuláře.
- **DB**: Tabulka project_templates (id, name, default_sections jsonb, default_texts jsonb, client_type text).
- **Management**: Admin může vytvářet/editovat šablony.

### 5) Komentáře pod stránkou pro klienty
- **Popis**: Nástroj pod preview stránky pro klienty k psaní komentářů, které spadnou pod projekt/verzi.
- **UI**: Pod preview iframe/form, textové pole + submit, seznam komentářů s timestamp/autorem.
- **Workflow**: Komentáře vidí sales/admin, mohou odpovědět, spustit novou verzi na základě feedback.
- **DB**: Nová tabulka project_comments (id, project_id, version_id nullable, user_id, comment text, created_at, is_client bool).
- **Přístup**: Klienti jen své projekty, sales/admin všechny.