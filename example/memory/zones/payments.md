---
id: zone-payments
type: zone
summary: MercadoPago Checkout Pro. Invoice gets a hosted pay link; reconciliation is driven by an idempotent webhook keyed on payment id. Cold zone, untouched since mid June.
zone: src/lib/payments
paths: [src/lib/payments, src/app/api/webhooks/mercadopago]
tags: [mercadopago, payments, webhook, idempotency, ars]
created: 2026-06-10
valid_from: 2026-06-10
valid_to: null
status: active
importance: 8
strength: 1
last_accessed: 2026-06-08
confidence: high
pinned: false
links:
  - active_decision [[dec-0002]]
  - relates_to [[scar-mp-webhook-race]]
  - relates_to [[zone-database]]
source_ids: []
---

## Summary
Payments run on MercadoPago Checkout Pro. Each invoice can mint a hosted pay
link; when the client pays, a webhook (`topic=payment`) drives reconciliation.
The webhook handler is idempotent, keyed on the MercadoPago payment id.

## Current state
- Pay link created via the MercadoPago SDK when an invoice is sent.
- Webhook at `src/app/api/webhooks/mercadopago` verifies, looks up the payment,
  and marks the invoice paid in one transaction.
- Idempotency: unique constraint on `(invoice_id, mp_payment_id)` in the DB.
- Amounts in integer centavos ARS; the invoice becomes immutable once paid.

## Active decisions
- [[dec-0002]]: MercadoPago over Stripe (LatAm methods, ARS payouts).

## Watch out
- Webhooks are at least once and can arrive out of order or before the redirect.
  Never assume exactly once. See [[scar-mp-webhook-race]].
- Sandbox does not faithfully reproduce production webhook timing; test the race
  by replaying a captured payload, not by trusting sandbox.
- The receipt email is triggered from the paid transition; keep it inside the
  idempotent path so a duplicate webhook cannot double send.

## History
- 2026-06-10: first real ARS payment end to end; hit the webhook race and made
  the handler idempotent ([[scar-mp-webhook-race]], [[session-2026-06-10]]).
