---
id: dec-0002
type: decision
summary: Chose MercadoPago over Stripe because most Orbit users and their clients are in Argentina and LatAm, where MercadoPago has local payment methods and payouts.
zone: src/lib/payments
tags: [mercadopago, stripe, payments, latam]
created: 2026-05-12
valid_from: 2026-05-12
valid_to: null
status: active
importance: 8
strength: 3
last_accessed: 2026-06-10
confidence: high
pinned: false
links:
  - decided_in [[session-2026-05-12]]
  - relates_to [[zone-payments]]
  - relates_to [[scar-mp-webhook-race]]
source_ids: []
---

## Summary
Chose MercadoPago over Stripe. Orbit's freelancers and their paying clients are
mostly in Argentina and the rest of LatAm, where MercadoPago has the local
payment methods (Rapipago, Pago Facil, local cards, installments) and can pay
out in ARS. Stripe support in the region is thin.

## Context and problem
Orbit invoices need a "Pay now" button that actually works for a client in
Buenos Aires paying an ARS invoice. The processor had to support local methods,
ARS settlement and reasonable fees, and hand us a webhook we could trust.

## Decision drivers
- Local payment methods and ARS payouts (the deciding factor).
- Installments ("cuotas"), which clients here expect.
- Documented webhook and a checkout link we can attach to an invoice.
- Fees on ARS transactions.

## Considered options
- Stripe: excellent DX, weak local coverage and ARS payouts in the region.
- MercadoPago Checkout Pro: hosted checkout, local methods, ARS, noisier webhooks.
- Manual bank transfer with proof upload: zero fees, terrible UX, no automation.

## Decision outcome
Chosen: MercadoPago Checkout Pro.
- Positive: local methods and installments, ARS settlement, hosted checkout so we
  hold less PCI surface.
- Negative: webhooks can arrive out of order or more than once (see
  [[scar-mp-webhook-race]]); sandbox differs from production in subtle ways; the
  SDK docs are uneven.

## Confirmation
Payment succeeded end to end in production on 2026-06-10 with an ARS test
invoice. Reconciliation is driven by the webhook, made idempotent after the race
condition scar. See [[zone-payments]].
