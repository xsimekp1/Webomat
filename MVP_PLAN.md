# MVP Platform Plan (v1) – "Sellable and Deliverable"

This plan outlines the MVP for the platform, structured into prioritized, implementable tasks. The order ensures iterative development with progress visible in multiple directions (sales/business features alternating with product/technical features).

## Prioritization
- **High**: Foundation items (authentication/roles) - essential for security and access.
- **Medium**: All core features - balanced importance for MVP delivery.

## Order Rationale
Starts with foundation, then alternates between sales focus (CRM, deals, payments, commissions) and product focus (web generation, change requests). This creates balanced progress without stagnation in one area.

## Todo List

1. **mvp-0 (High)**: Implement authentication and roles: Login/logout, Admin (Pavel) and Sales (Andrea + others) roles with RBAC permissions  
   - Sales see only their leads/deals  
   - Admin sees everything + can edit pricing/commissions/templates

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

## Current State
- Platform is visible and login works.  
- Now adding first real value through iterative implementation.