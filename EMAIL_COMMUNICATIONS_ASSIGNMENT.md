# Email Communications Assignment

## Zadání: Email komunikace, revize webu, varianty

### 1) Doménový e-mail → ukládání do tabulky komunikací
- **Varianta A (doporučená)**: Email provider s inbound webhookem (Mailgun/Postmark/SendGrid).
  - Nastavit DNS MX na providera.
  - Provider zavolá webhook (Supabase Edge / FastAPI), najde kontakt/projekt podle adresy/tracking ID, uloží do DB/Storage.
- **Varianta B**: Vlastní IMAP polling worker (každou minutu čte, ukládá).

### 2) Odpověď zpátky do mailu
- Přes provider API nebo SMTP.
- Threading: In-Reply-To, References pro správné vlákna.

### 3) Zprávy se zpožděním (scheduled sending)
- Tabulka scheduled_messages: id, channel, to_email, subject, body, related_ids, send_at, status, error, created_by, timestamps.
- Worker každých X sekund/minut odešle queued s send_at <= now(), uloží do communications.

### 4) Automatické odeslání mailu klientovi po vygenerování webu
- Přepínač v projektu: "Odeslat po dokončení" (ON/OFF).
- Šablona textu, příjemci (klient + CC sales), odkaz na preview.
- Po job done: Vytvořit scheduled_messages s send_at=now().

### 5) Workflow připomínek a úprav webu (revize)
- Tabulka version_feedback: id, version_id, author_user_id, source (client_portal/email/internal), notes_text, structured jsonb, created_at.
- Revision jobs: Použít ai_generation_jobs s job_type=revision, input_version_id, feedback_ids/snapshot.
- Revizní prompt: Předchozí HTML, assety, připomínky, instrukce minimální změny.
- Výstup: Nová verze s changelog.

### 6) “Radio button: zpracovat zadání dvakrát se stejným zadáním”
- UI: Počet variant (1/2/3), checkbox "odlišný layout/tone".
- Backend: Vytvoří joby/varianty s variant_label A/B/C, variant_group_id pro UI.

### 7) Kam uložit komunikaci + přílohy
- E-maily: DB tabulka communications (id, direction inbound/outbound, channel email, status, emails, subject, body, thread_key, related_ids, timestamps).
- Přílohy: Supabase Storage bucket message-attachments, tabulka communication_attachments (id, comm_id, file_name, mime_type, size_bytes, storage_path).

### 8) MVP pořadí
1. Outbox + posílání mailů.
2. Automatické maily po generování.
3. Inbound e-maily přes webhook.
4. Revize webu.
5. A/B varianty.

### 9) Bezpečnostní poznámka
- Generování jen server-side API klíčem.
- UI jen insert job (RLS).
- Dashboard tokenů/cost per user/měsíc.

### Doporučené DB rozšíření
- communications (jako výše).
- scheduled_messages (jako výše).
- version_feedback (jako výše).
- ai_generation_jobs: Přidat job_type (initial/revision/regenerate_variants), variant_group_id, input_version_id.
- project_versions: Přidat change_summary text.