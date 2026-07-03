---
id: zone-email
type: zone
summary: Transactional email via Resend. Sends invoice notifications, payment receipts and, since July, OTP sign in codes. All three share one Resend quota.
zone: src/lib/email
paths: [src/lib/email, src/emails]
tags: [resend, email, transactional, otp, receipts]
created: 2026-06-18
valid_from: 2026-06-18
valid_to: null
status: active
importance: 6
strength: 2
last_accessed: 2026-06-18
confidence: medium
pinned: false
links:
  - relates_to [[dec-0004]]
  - relates_to [[zone-auth]]
  - relates_to [[zone-payments]]
source_ids: []
---

## Summary
Transactional email runs on Resend. Three message types: invoice sent
notifications, payment receipts, and (since 2026-07-01) OTP sign in codes.
Templates live in `src/emails` as React components.

## Current state
- Sender: `no-reply@orbit.app`, domain verified in Resend (SPF plus DKIM).
- Receipts triggered from the payment paid transition (inside the idempotent
  webhook path, so a duplicate webhook cannot double send).
- OTP codes sent on sign in request; short lived, rate limited upstream.
- All three types draw on the same Resend monthly quota.

## Active decisions
- No standalone email ADR. The OTP dependency comes from [[dec-0004]].

## Watch out
- OTP, receipts and invoice mails share one quota; a sign in spike can starve
  receipts. Watch the Resend dashboard when auth traffic grows.
- Keep the receipt send inside the idempotent webhook path (see
  [[zone-payments]]) so duplicate webhooks do not double email.
- Do not send OTP codes from a new unverified subdomain; deliverability drops and
  codes land in spam.

## History
- 2026-06-18: Resend wired up for invoice notifications and receipts.
- 2026-07-01: OTP code emails added for auth ([[dec-0004]], [[session-2026-07-01]]).
