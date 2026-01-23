# Sales Dashboard Assignment

## Zadání: Dashboard „Moje rozdělané projekty“ (nahrazuje "Aktivní dealy" box)

### Nový název sekce
Moje rozdělané projekty (nejvíce sales-friendly).

### Cíl
Na sales dashboard zobrazit všechny aktivní projekty patřící přihlášenému uživateli, s přehledem klientů, follow-upů, cen, statusů a náhledů webu.

### UI návrh: layout dashboardu

#### 1) Horní "strip" (rychlé info – nice-to-have)
Úzký řádek s metrikami:
- Aktivní projekty: X
- Dnes volat: Y (projekty s next_follow_up_at <= today)
- Čeká na tebe: Z (status "Needs info", "Waiting client", "Review needed")
- Očekávaný obrat: suma expected_price z aktivních

#### 2) Grid karet
- Desktop: 2–3 sloupce (responsive)
- Mobil: 1 sloupec
- Filtr/search: Search input (client/project/phone/city), filter status (multi-select), sort (follow-up, cena, updated)

### Projektová karta

#### Header
- Název klienta (bold, klik → detail projektu)
- Badge: status (Offer, Won, In production, Delivered, Live)

#### Subheader
- Název projektu / doména (nebo "Doména: zatím nezadaná")

#### Big money
- expected_price velkým
- Vedle: záloha / zaplaceno (pokud payments)

#### Co mám udělat (highlight)
- Další krok: Call, Send offer, Waiting assets, Approve text, …

#### Kdy volat / follow-up
- next_follow_up_at (zvýraznit pokud dnes/zpožděné)
- Pokud není: "Follow-up nenastaveno" + varování

#### Kontakt (rychlá akce)
- Telefon (klik → zavolat)
- Email (pokud existuje)

#### Thumbnail
- Náhled poslední verze (z website_versions)
- Placeholder: "Zatím bez návrhu"

#### Footer akce
- Otevřít projekt
- Přidat poznámku / log kontaktu
- Generovat web (podmíněně)

### Data model

#### Projects/Deals
- id, client_id, owner_seller_id, status, expected_price, domain, next_follow_up_at, updated_at

#### Clients/Contacts
- name, phone, email, city

#### Website Versions
- id, project_id, version_number, preview_thumbnail_url, public_preview_url, is_public, created_at

### Query logika
- Filtr: owner_seller_id = current_user.id, status NOT IN ('Closed','Lost','Canceled')
- Join: client data, last_version subquery
- Sort: next_follow_up_at (nulls last), updated_at desc

### UX detaily
- Pokud není follow-up: CTA "Nastavit follow-up" (mini modal s date picker)
- Pokud není cena: CTA "Doplnit cenu"
- Pokud není verze: CTA "Vytvořit první návrh"
- Starý MVP box: Přesunout na admin-only "MVP roadmap" stránku

### Bonus: Call list panel
- Seznam "Dnes volat": klient + čas + "Otevřít" tlačítko

### Jak projekt funguje (přehled pro dokumentaci)
1. **Přihlášení**: Sales se přihlásí do dashboardu.
2. **Přehled projektů**: Vidí "Moje rozdělané projekty" jako karty s klienty, statusy, cenami, follow-upy.
3. **Akce**: Klik na kartu → detail projektu, přidat poznámku, generovat web.
4. **Filtry/Sort**: Hledání a filtrování pro rychlé nalezení.
5. **Call list**: Denní seznam kontaktů k zavolání.
6. **Notifikace**: Highlight zpožděných follow-upů, čekajících akcí.
7. **Integrace**: Propojení s CRM, verzemi webu, fakturací.

Tento dashboard je operativní nástroj pro sales, zaměřený na denní workflow bez zbytečných detailů.