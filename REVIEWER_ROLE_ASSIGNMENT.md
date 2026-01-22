# Reviewer Role Assignment

## Rozšíření: Třetí role reviewer s testovacím prostředím

### Klíčový koncept: environment = production | test

Aby tester mohl "vytvořit nevalidní kontakt" a sales ho neviděl, potřebuješ oddělit data.

Nejjednodušší: do hlavních tabulek přidat sloupec env (text/enum) s default production.

Tester vytváří vše do env = 'test', seller v UI + RLS uvidí jen production, admin vidí oboje.

### Role a oprávnění

1. **admin**: všechno: konfigurace, uživatelé, finance, audit, RLS override přes service role.
2. **seller (nebo sales_agent)**: vidí svoje leady/projekty (a sdílené týmové), může vytvářet kontakt/deal/zadání, finance jen číst "své provize".
3. **reviewer / tester**: defaultně jako seller (vidí UI "agent"), ale má přístup k "test sandbox", může vidět admin přehledy read-only, nemůže destruktivní akce "naostro".

### Co reviewer vidí / nevidí / může

- **Vidí (read)**: kontakty, deály, projekty, zadání webu, aktivity, pipeline, reporting, náhled faktur, šablony, položky, workflow.
- **Může (write) ale jen v test**: vytvořit/edit kontakt/deal (env=test), přidat aktivity/poznámky/statusy/follow-upy, simulované provize/odměny/adjustments.
- **Nesmí (production write)**: nic do env=production (kromě komentářů k UX).
- **Zakázat drahé/rizikové**: AI generování (jen "Generate (Preview)" → status blocked_simulated), faktury (jen "Generate invoice preview" v test, bez Send/Paid/Export), provize (jen simulace, nezapočítá se).

### Provize: jak oddělit simulace

Tabulka commission_entries s:
- env (production/test)
- mode enum: real | simulated
- Výpočty filtrují: env='production' AND mode='real'
- Reviewer: env='test' AND mode='simulated'

### AI generování webu: Preview bez tokenů

- website_generation_requests: env, status enum (draft, queued, running, done, blocked_simulated, failed)
- Reviewer: může request, ale "Generate" → verze s placeholder, status blocked_simulated, UI "Generování zablokováno — jen preview"
- Admin/seller: mohou reálně queue-nout

### Faktury: náhled ano, účetnictví ne

- Rozdělit na draft (výpočet/layout) a finalize (číslování, PDF, odeslání, stavy)
- invoices: env, status: draft | issued | sent | paid | void, number (nullable v draft)
- Reviewer: jen draft v test, bez issued/sent/paid

### Citlivé věci schovat

- API klíče, integrační nastavení, tokeny, webhooky (admin only)
- finanční agregace "skutečné payouty" v production
- osobní údaje (např. interní poznámky, marže)

### Test badge UX

- Badge: TEST MODE (env=test), REVIEWER MODE (role=reviewer)
- Test záznamy: štítek "TEST" (seller nevidí)

### Supabase implementace

1. **Role v profilu**: profiles: role enum (admin | seller | reviewer), active bool
2. **env sloupec**: v klíčových tabulkách (contacts, deals, projects, website_generation_requests, invoices, commission_entries)
3. **RLS pravidla**:
   - Seller: env='production' AND owner_seller_id = auth.uid()
   - Reviewer: env='test' (read/write) + read-only agregace
   - Admin: env in ('production','test') (full)
4. **Server-side enforcement**: Endpointy kontrolují role/env (např. "Generate web" zakáže LLM pro reviewer)

### Shrnutí pravidel

- Admin: vše, production i test
- Seller: production pouze své
- Reviewer: jako seller UX, ale data jen test, simulace workflow

### DB rozšíření: testovací příznaky

- **Contacts/Deals**: is_test bool (auto-set v test env), UI blur emails/phones pro reviewer
- **Users**: test_account bool (reviewer může impersonate test seller/admin)
- **Commission_entries**: mode (real/simulated)

Toto rozšíření umožňuje bezpečné testování UX a procesů bez vlivu na production.