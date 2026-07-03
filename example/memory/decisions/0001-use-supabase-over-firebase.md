---
id: dec-0001
type: decision
summary: Chose Supabase over Firebase for auth plus a relational Postgres store, because invoicing needs real SQL joins and row level security.
zone: src/lib/db
tags: [supabase, firebase, database, auth, postgres]
created: 2026-05-12
valid_from: 2026-05-12
valid_to: null
status: active
importance: 9
strength: 4
last_accessed: 2026-06-28
confidence: high
pinned: true
links:
  - decided_in [[session-2026-05-12]]
  - relates_to [[zone-database]]
  - relates_to [[zone-auth]]
source_ids: []
---

## Summary
Chose Supabase over Firebase. Orbit is invoicing: clients, invoices and line
items are deeply relational and we need real SQL joins, aggregates and Row Level
Security. Supabase gives us managed Postgres plus auth in one place.

## Context and problem
We needed auth plus a primary datastore on day one. Firebase (Firestore) is
document oriented; modelling invoice totals, tax breakdowns and per client
reporting on it means denormalizing and hand rolling aggregation. We also wanted
per row tenant isolation without writing it in application code.

## Decision drivers
- Relational data with joins and aggregates (invoice reporting).
- Row Level Security enforced at the database, not in app code.
- Single vendor for auth plus DB to cut integration surface.
- SQL is a portable, hireable skill; Firestore query model is not.

## Considered options
- Firebase (Firestore + Firebase Auth): fast start, weak for relational reporting.
- Supabase (Postgres + Supabase Auth + RLS): SQL, RLS, open source, self hostable.
- Plain Postgres on a VPS plus a separate auth provider: most control, most ops.

## Decision outcome
Chosen: Supabase.
- Positive: real SQL, RLS as a hard tenant boundary, one dashboard, generous
  free tier, migrations in git via `supabase db push`.
- Negative: coupling to Supabase specifics (auth helpers, RLS policy language);
  cold starts on the free tier; we own our RLS policies and their bugs.

## Confirmation
By 2026-06 all tenant isolation is enforced by RLS policies and invoice
reporting runs as SQL views. No app level tenant filtering was needed. See
[[zone-database]] for the live state.
