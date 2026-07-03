---
id: zone-auth
type: zone
summary: Passwordless auth on Supabase. OTP email code is now the primary sign in path, with magic links kept as a desktop fallback after magic links failed on Safari iOS.
zone: src/app/auth
paths: [src/app/auth, src/lib/supabase, src/middleware.ts]
tags: [auth, supabase, otp, magic-link, safari, session]
created: 2026-05-28
valid_from: 2026-05-28
valid_to: null
status: active
importance: 8
strength: 6
last_accessed: 2026-07-01
confidence: high
pinned: false
links:
  - active_decision [[dec-0004]]
  - active_decision [[dec-0001]]
  - superseded_decision [[dec-0003]]
  - relates_to [[refl-safari-ios-auth]]
  - relates_to [[zone-email]]
source_ids: []
---

## Summary
Passwordless auth built on Supabase Auth. As of 2026-07-01 the primary path is a
six digit OTP code emailed via Resend and entered in the same tab; magic links
remain as a desktop only fallback. Session is a Supabase cookie refreshed in
`middleware.ts`.

## Current state
- Sign in screen: email field, then a code entry screen (same tab).
- OTP codes: six digits, five minute expiry, rate limited per email.
- Magic link: still wired for desktop, hidden on mobile user agents.
- Session refresh runs in `src/middleware.ts` on every request.
- Tenant identity comes from the Supabase user id, enforced downstream by RLS.

## Active decisions
- [[dec-0004]]: OTP email code primary, magic link secondary (current).
- [[dec-0001]]: Supabase as the auth and DB provider.
- [[dec-0003]]: magic links only (superseded by dec-0004, kept for history).

## Watch out
- Do NOT make sign in depend on landing in the same browser context via a link;
  that is exactly what broke on Safari iOS. Keep same tab code entry.
- OTP emails ride the Resend quota shared with receipts; a spike in sign ins
  eats into transactional headroom (see [[zone-email]]).
- Rate limiting on the OTP endpoint is the only thing between us and email
  bombing; do not loosen it without a plan.

## History
- 2026-05-28: shipped magic links only ([[dec-0003]], [[session-2026-05-28]]).
- 2026-06-15: found magic links fail on Safari iOS ([[session-2026-06-15]]).
- 2026-07-01: added OTP fallback, made it primary ([[dec-0004]], [[session-2026-07-01]]).
