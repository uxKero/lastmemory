---
id: zone-billing-ui
type: zone
summary: Next.js App Router billing surface. Invoice list, editor and detail. PDF is rendered in a Route Handler, never in a Server Component, because the PDF library breaks the build.
zone: src/app/invoices
paths: [src/app/invoices, src/components/billing]
tags: [nextjs, billing, invoices, pdf, ui]
created: 2026-06-22
valid_from: 2026-06-22
valid_to: null
status: active
importance: 6
strength: 2
last_accessed: 2026-06-22
confidence: high
pinned: false
links:
  - relates_to [[scar-react-pdf-build]]
  - relates_to [[zone-database]]
  - relates_to [[zone-payments]]
source_ids: []
---

## Summary
The billing surface: invoice list, the invoice editor and the invoice detail
view, all in the Next.js App Router. Invoice PDFs are generated in a Route
Handler on demand, never imported into a Server Component.

## Current state
- `src/app/invoices/page.tsx`: list, backed by the `invoices(user_id, status,
  created_at)` index for fast filtering.
- Invoice editor: line items in integer centavos ARS, live total.
- Detail view: shows status, a MercadoPago pay link, and a PDF download button.
- PDF: `app/invoices/[id]/pdf/route.ts` renders with `@react-pdf/renderer` at
  request time, keeping it out of the server bundle.

## Active decisions
- Inherits [[dec-0001]] (Supabase) and [[dec-0002]] (MercadoPago) for its data
  and pay link; no billing UI specific ADR yet.

## Watch out
- NEVER import `@react-pdf/renderer` into a Server Component; it passes
  `next dev` and fails `next build`. See [[scar-react-pdf-build]].
- The invoice is immutable once `paid`; the editor must hard disable on paid
  invoices, not just hide the save button.

## History
- 2026-06-22: built the list, editor and detail; moved PDF to a Route Handler
  after the build break ([[scar-react-pdf-build]], [[session-2026-06-22]]).
