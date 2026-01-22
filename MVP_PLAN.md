# MVP Platform Plan (v1) – "Sellable and Deliverable"

This plan outlines the MVP for the platform, structured into prioritized, implementable tasks. The order ensures iterative development with progress visible in multiple directions (sales/business features alternating with product/technical features).

## Prioritization
- **High**: Foundation items (authentication/roles) - essential for security and access.
- **Medium**: All core features - balanced importance for MVP delivery.

## Order Rationale
Starts with foundation, then alternates between sales focus (CRM, deals, payments, commissions) and product focus (web generation, change requests). This creates balanced progress without stagnation in one area.

## Todo List

1. **mvp-0 (High)**: Implement detailed authentication and roles: Login/logout (email/password, forgot password reset, change password), session handling (token/cookie with expiration, optional remember me), basic protections (rate limit, account lock). RBAC: Admin (Pavel) sees all + edits global settings; Sales (Andrea + others) see only own entities. Guardrails for sales (select packages, discounts up to limit, exceptions require approval). Admin user management: Create/deactivate users, reset passwords, invites, overview. Data model: users table with roles/permissions. UI: Role-based dashboards/menus. Audit: Log login/logout, role changes, deactivations, reassignments.

2. **mvp-1 (Medium)**: Build CRM minimum: Lead list with filters/search, detail page (name, address, phone, email, notes, status pipeline, assigned sales, next follow-up, communication log)  
   - Pipeline: New → Calling → Interested → Offer sent → Won/Lost/DNC  
   - Result: Sales have a "call list" and know what to do today

3. **mvp-3 (Medium)**: Add website generation from templates: Template library (2-3 segments), generate flow (select template, fill fields, build + preview, deploy + version control)  
   - Fields: name, phone, address, service description  
   - Result: Deliver websites quickly and repeatably

4. **mvp-2 (Medium)**: Implement deals from leads: Create deal from lead, include package (Start/Profi/Premium/Custom), prices, status (Offer → Won → In production → Delivered → Live), terms, domain/URL evidence  
   - Setup price + monthly management (nullable)  
   - Result: Pipeline extends from "Won" into production and delivery

5. **mvp-4 (Medium)**: Add change requests for deals: Create request (text, scope small/medium/large, status New → In progress → Ready for review → Done), save AI diff/proposal, audit log  
   - Result: Changes are trackable, not chaotic chats

6. **mvp-5 (Medium)**: Record payments for deals: Amount, type (setup/monthly), status (due/paid), paid_at; commissions only after paid  
   - Result: Commissions tied to real money, not promises

7. **mvp-6 (Medium)**: Build commission ledger and dashboards: Ledger (earned/reversed/paid), dashboards for sales (earned/waiting/paid) and admin (overview per sales/period)  
   - Result: Scale sales without Excel and disputes

8. **mvp-7 (Medium)**: Implement commission invoicing workflow: Generate invoice for period, draft from un-invoiced earned, statuses draft → pending_approval → approved/rejected → paid, PDF export  
   - Result: Close the commission cycle

9. **mvp-8 (Medium)**: Add onboarding flow for sales: First login -> profile setup, commission %, bank details (filled/not filled)

10. **mvp-9 (Medium)**: Implement tasks/follow-up for leads: 'Call tomorrow', 'Send offer' + simple 'what to do today' list

11. **mvp-10 (Medium)**: Add notifications: Internal changes (status, new request, deal waiting, invoice approval) - email or in-app badge

12. **mvp-11 (Medium)**: Create simple offer templates: Generate offer text from deal + price summary

13. **mvp-12 (Medium)**: Implement attachments/documents: Upload photos, logo, texts, PDF pricing to company/deal/change request

14. **mvp-13 (Medium)**: Add basic audit log: Who changed status, deployed, approved invoice

15. **mvp-14 (Medium)**: Implement rollback/versions for websites: Last 2 deploys + rollback button

16. **mvp-15 (Medium)**: Build user management for admin: Create/disable sales, reset password, set roles, default commission

17. **mvp-16 (Medium)**: Add Kanban view for pipeline + bulk actions: Drag&drop statuses + bulk mark DNC/move/assign

18. **mvp-17 (Medium)**: Implement lead deduplication: By place_id/phone/website: 'already in system'

19. **mvp-18 (Medium)**: Add lead import: CSV or from scraper (Google Maps) + field mapping

20. **mvp-19 (Medium)**: Record domains & hosting evidence: Owner, DNS, hosting, access/notes, expiry (alerts)

21. **mvp-20 (Medium)**: Add basic handoff to production: Deal checklist: logo ✓, photos ✓, text ✓, content approval ✓ -> then Generate

22. **mvp-21 (Medium)**: Implement payment status and reminders: 'Waiting for payment' + auto reminders for sales/admin

23. **mvp-22 (Medium)**: Set up unified pricing rules: Package pricing in admin + simple exceptions (discounts), clear commission calculation

24. **mvp-23 (Medium)**: Implement advanced audit logging: Track all user actions (login/logout, role/deactivation changes, lead/deal reassignments), with timestamps and user IDs for disputes and oversight

25. **mvp-24 (Medium)**: Implement AI website generation based on [WEBSITE_GENERATION_ASSIGNMENT.md](./WEBSITE_GENERATION_ASSIGNMENT.md)

26. **mvp-25 (Medium)**: Implement new contact page based on [NEW_CONTACT_ASSIGNMENT.md](./NEW_CONTACT_ASSIGNMENT.md)

## Current State
- Platform is visible and login works.  
- Now adding first real value through iterative implementation.