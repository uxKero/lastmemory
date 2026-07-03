# BRAIN: Orbit
> Last updated: 2026-07-02 · 19 neurons · Last dream: 2026-07-01 · Health: OK (1 orphan)

## Zones
- [zones/auth.md]: passwordless auth, OTP primary after Safari iOS broke magic links · 🔥 hot (temp 0.97) · upd 2026-07-01
- [zones/database.md]: Supabase Postgres, RLS on every table, reporting views · 🌤️ warm (temp 0.49) · upd 2026-06-22
- [zones/billing-ui.md]: invoice list, editor, detail; PDF in a Route Handler · 🌤️ warm (temp 0.49) · upd 2026-06-22
- [zones/email.md]: Resend transactional: invoices, receipts, OTP codes · 🌤️ warm (temp 0.37) · upd 2026-06-18
- [zones/payments.md]: MercadoPago Checkout Pro, idempotent webhook · ❄️ cold (temp 0.03, untouched since mid June) · upd 2026-06-08

## Decisions
- [decisions/0001-use-supabase-over-firebase.md]: Supabase over Firebase for SQL and RLS · active
- [decisions/0002-mercadopago-over-stripe.md]: MercadoPago over Stripe for LatAm and ARS · active
- [decisions/0004-otp-email-fallback.md]: OTP email code primary, magic link fallback · active
- [decisions/0003-magic-links-only.md]: magic links only · superseded by 0004

## Scars
- [scars/react-pdf-build-break.md]: @react-pdf/renderer breaks the Next.js build in a Server Component · confidence high
- [scars/mercadopago-webhook-race.md]: MercadoPago webhook is at least once, make it idempotent · confidence medium

## Reflections
- [reflections/safari-ios-auth.md]: Safari iOS breaks any auth flow that leaves the tab · from 3 sessions

## Recent sessions
- [sessions/2026-07-01.md]: OTP fallback shipped, supersedes magic links, verified on iPhone · importance 8
- [sessions/2026-06-22.md]: billing UI, react-pdf build break, list indexes · importance 7
- [sessions/2026-06-15.md]: magic links fail on Safari iOS · importance 6
- [sessions/2026-06-10.md]: first ARS payment, webhook race fixed · importance 8

## Pick up here
> Pending: test the OTP flow on a range of real mobile devices, not just one iPhone.
> Watch the Resend quota now that OTP codes share it with receipts and invoice mail.
> Orphan to clean up: sessions/2026-05-05.md (scaffolding) has no links.
