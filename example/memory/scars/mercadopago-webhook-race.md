---
id: scar-mp-webhook-race
type: scar
summary: MercadoPago can deliver the payment webhook more than once and before the checkout redirect returns, causing double invoice marking. Make webhook handling idempotent, keyed on payment id.
zone: src/app/api/webhooks/mercadopago
tags: [mercadopago, webhook, race-condition, idempotency, payments]
severity: high
confidence: medium
scope: "MercadoPago Checkout Pro webhooks (topic=payment) in production, 2026-06. Observed duplicate and out of order delivery; frequency not precisely measured. Sandbox did not reproduce it reliably."
created: 2026-06-10
valid_from: 2026-06-10
valid_to: null
status: active
last_revalidated: 2026-06-10
expires_hint: 2026-09-10
importance: 8
strength: 2
last_accessed: 2026-06-10
pinned: false
links:
  - learned_in [[session-2026-06-10]]
  - relates_to [[zone-payments]]
  - relates_to [[dec-0002]]
source_ids: []
---

## Summary
MercadoPago delivered the payment webhook twice, and once before the browser
finished the checkout redirect. Our handler marked the invoice paid on each call
and sent two receipt emails. Confidence medium: the fix works, but exact
delivery guarantees are not documented and we could not force the race on demand
in sandbox.

## What happened
On the first real ARS payment the invoice flipped to `paid` from the webhook
before the redirect handler ran, and then a second webhook for the same payment
id arrived and re ran the "mark paid plus send receipt" logic. The client got
two receipt emails and the ledger briefly showed a double entry.

## What to do instead
- Treat the webhook as at least once delivery, never exactly once.
- Make the handler idempotent: look up the MercadoPago `payment.id`, and if the
  invoice is already `paid` for that id, return 200 and do nothing else.
- Do the "mark paid" write inside a single transaction with a unique constraint
  on `(invoice_id, mp_payment_id)` so a duplicate insert is rejected by the DB.
- Do NOT rely on the checkout redirect as the source of truth; the webhook wins.

## How to re-validate
- Replay a captured production webhook payload twice against a staging invoice
  and confirm exactly one paid transition and one receipt email.
- Check MercadoPago's current webhook docs for a documented dedupe or ordering
  guarantee; if they now guarantee exactly once, downgrade this scar.
- Re-check after any change to the payments schema or the receipt email trigger.
