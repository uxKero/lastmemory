---
id: zone-database
type: zone
summary: Supabase Postgres. Tenant isolation is enforced entirely by Row Level Security. Invoice reporting runs as SQL views; recent work added indexes for the invoice list.
zone: src/lib/db
paths: [supabase/migrations, src/lib/db]
tags: [supabase, postgres, rls, migrations, indexes]
created: 2026-05-12
valid_from: 2026-05-12
valid_to: null
status: active
importance: 8
strength: 2
last_accessed: 2026-06-22
confidence: high
pinned: false
links:
  - active_decision [[dec-0001]]
  - relates_to [[zone-payments]]
  - relates_to [[zone-billing-ui]]
source_ids: []
---

## Summary
Supabase managed Postgres. Every table has Row Level Security ON; tenant
isolation lives in RLS policies, never in app code. Invoice reporting is exposed
as SQL views. Migrations are versioned in `supabase/migrations` and shipped with
`supabase db push`.

## Current state
- Tables: `users`, `clients`, `invoices`, `invoice_items`, `payments`.
- RLS: every policy checks `auth.uid()` against the owning user.
- Unique constraint `(invoice_id, mp_payment_id)` on `payments` for webhook
  idempotency (see [[scar-mp-webhook-race]]).
- Reporting views: `invoice_totals`, `client_balances`.
- Indexes added 2026-06-22 on `invoices(user_id, status, created_at)` to speed
  the billing list.

## Active decisions
- [[dec-0001]]: Supabase over Firebase (SQL, RLS, one vendor).

## Watch out
- Never bypass RLS with the service key from app code; that silently breaks
  tenant isolation. The service key is for migrations and trusted webhooks only.
- Prod is `orbit-prod`; never migrate against it directly (see CRITICAL.md).
- A missing RLS policy on a new table means it is invisible, not open; add the
  policy in the same migration that creates the table.

## History
- 2026-05-12: schema and RLS policies created ([[session-2026-05-12]]).
- 2026-06-22: added billing list indexes ([[session-2026-06-22]]).
