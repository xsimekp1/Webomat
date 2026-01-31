# TODO: Notifikační systém - Implementační plán

## ✅ Hotovo (fáze 1)
- [x] Vytvořit ToastContext pro globální stav toast notifikací
- [x] Vytvořit Toast komponentu pro jednotlivou notifikaci  
- [x] Vytvořit ToastContainer pro správu více toastů
- [x] Integrovat ToastProvider do providers.tsx
- [x] Opravit import cestu v Toast.tsx
- [x] Přidat testovací toast na stránku projektu

## 🔄 Další notifikační scénáře k implementaci

### Business notifikace (vysoká priorita)
1. **Schválení faktury obchodníkovi**
   - Trigger: `invoices_received.status = 'approved'`
   - Komu: `seller_id` z faktury
   - Zpráva: "Faktura #{invoice_number} schválena k výplatě"
   - Akce: "Zobrazit fakturu" → detail faktury

2. **Dokončení web designu od Claude**
   - Trigger: `website_versions.status = 'published'` a nová verze
   - Komu: `project.seller_id`
   - Zpráva: "Web design pro {project_name} je hotov"
   - Akce: "Zobrazit web" → preview projektu

3. **Příchozí email od klienta**
   - Trigger: `crm_activities.type = 'email'` a `direction = 'inbound'`
   - Komu: `business.owner_seller_id`
   - Zpráva: "Nová zpráva od klienta: {subject}"
   - Akce: "Otevřít CRM" → detail business

4. **Follow-up starší než týden (bombardování)**
   - Trigger: `businesses.next_follow_up_at < NOW() - INTERVAL '7 days'`
   - Komu: `business.owner_seller_id`
   - Zpráva: "Follow-up pro {business_name} je zpožděn o {days} dní"
   - Priorita: High
   - Akce: "Aktualizovat business" → editace

5. **Vygenerování druhé (a další) verze projektu**
   - Trigger: `website_versions.version_number > 1`
   - Komu: `project.seller_id`
   - Zpráva: "Nová verze #{version_number} hotova pro projekt {project_name}"
   - Akce: "Zobrazit verze" → tab versions

6. **Nezafakturováno více než měsíc**
   - Trigger: `invoices_issued.paid_date IS NULL` a `due_date < NOW() - INTERVAL '1 month'`
   - Komu: Admin (pro finanční kontrolu)
   - Frekvence: Jednou denně
   - Priorita: High
   - Zpráva: "{count} faktur nezaplaceno déle než měsíc"
   - Akce: "Zobrazit neplatiče" → filtr faktur

### Systémové notifikace (střední priorita)
7. **5 minut po přihlášení (testovací)**
   - Trigger: `audit_log.action = 'login'` a `created_at < NOW() - INTERVAL '5 minutes'`
   - Komu: `user_id` z audit log
   - Jen pro testování systému
   - Zpráva: "Jste přihlášen 5 minut, vše funguje!"

8. **Nová verze systému nasazena**
   - Trigger: Manual/automatic deployment
   - Komu: Všichni uživatelé
   - Priorita: Info
   - Zpráva: "Systém byl aktualizován na verzi {version}"

9. **Platnost blížící se faktury**
   - Trigger: `invoices_issued.due_date < NOW() + INTERVAL '3 days'`
   - Komu: Admin a příslušný seller
   - Priorita: High
   - Zpráva: "Faktura #{invoice_number} má splatnost za 3 dny"

### Inactivity tracking (nízká priorita)
10. **Inactivity warning se zvukem**
    - Trigger: 15 minut neaktivity
    - Komu: Přihlášený uživatel
    - Zpráva: "Odhlásit za {countdown} sekund kvůli neaktivitě"
    - Akce: "Prodloužit session" / "Odhlásit"
    - Feature: Countdown timer, zvukové varování

## 🏗️ Technická infrastruktura k implementaci

### Backend (FastAPI)
- [ ] Vytvořit `notifications` tabulku v Supabase
- [ ] Vytvořit `notification_settings` tabulku
- [ ] Vytvořit `/api/notifications` router s endpointy:
  - `GET /notifications` - získat notifikace
  - `POST /notifications/{id}/read` - označit jako přečtenou
  - `GET /notifications/settings` - nastavení
  - `PUT /notifications/settings` - upravit nastavení
- [ ] Vytvořit `NotificationService` pro správu notifikací
- [ ] Integrovat notifikace do existujících endpointů

### Frontend (Next.js)
- [ ] Vytvořit `NotificationContext` pro persistentní notifikace
- [ ] Vytvořit `NotificationCenter` UI komponentu
- [ ] Vytvořit `NotificationBadge` pro počet nepřečtených
- [ ] Implementovat real-time polling/WebSocket
- [ ] Vytvořit `useInactivityTracker` hook
- [ ] Přidat audio notifikace (Web Audio API)

### Database schema
```sql
-- Notification settings pro uživatele
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),
    invoice_approval BOOLEAN DEFAULT true,
    website_design_ready BOOLEAN DEFAULT true,
    follow_up_reminders BOOLEAN DEFAULT true,
    system_alerts BOOLEAN DEFAULT true,
    client_communication BOOLEAN DEFAULT true,
    in_app_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    timezone VARCHAR(50) DEFAULT 'Europe/Prague',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(seller_id)
);

-- Samotné notifikace
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    action_url VARCHAR(500),
    action_text VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMPTZ,
    email_error TEXT
);
```

## 🚀 Implementační fáze

### Fáze 1: Core infrastructure
- [x] Základní toast systém (hotovo)
- [ ] Databázové tabulky v Supabase
- [ ] Backend NotificationService
- [ ] Frontend NotificationContext

### Fáze 2: Business integration
- [ ] Schválení faktury notifikace
- [ ] Web design ready notifikace  
- [ ] Email notifikace
- [ ] Follow-up reminder notifikace
- [ ] Multi-verze projektů notifikace
- [ ] Neplatiči notifikace

### Fáze 3: Advanced features
- [ ] Inactivity tracking se zvukem
- [ ] Real-time WebSocket/SSE
- [ ] Notification Center UI
- [ ] Email notifikace (volitelné)
- [ ] Analytics a reporting

### Fáze 4: Polish & optimization
- [ ] Performance testing
- [ ] Cross-tab synchronization
- [ ] Mobile optimization
- [ ] Accessibility testing

---

**Poznámka:** Tento dokument slouží jako technický plán pro postupnou implementaci komplexního notifikačního systému v Webomat platformě.