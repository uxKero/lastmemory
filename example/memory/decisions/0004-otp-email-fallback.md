---
id: dec-0004
type: decision
summary: Added an OTP email code as the primary sign in path, keeping magic links as a secondary option, because magic links broke on Safari iOS.
zone: src/app/auth
tags: [auth, otp, magic-link, safari, resend]
created: 2026-07-01
valid_from: 2026-07-01
valid_to: null
status: active
importance: 8
strength: 3
last_accessed: 2026-07-01
confidence: high
pinned: true
links:
  - supersedes [[dec-0003]]
  - decided_in [[session-2026-07-01]]
  - relates_to [[zone-auth]]
  - relates_to [[zone-email]]
  - relates_to [[refl-safari-ios-auth]]
source_ids: []
---

## Summary
Made a six digit OTP code sent by email the primary sign in path, with magic
links kept as a secondary option on desktop. The user enters the code in the
same tab they started in, so the session is bound to the right browser context.
This fixes the Safari iOS failure that broke magic links.

## Context and problem
Magic links (see [[dec-0003]]) failed on Safari iOS because the link frequently
opened in a different browser context, dropping the session cookie. The pattern
recurred across several sessions and is documented in [[refl-safari-ios-auth]].
We needed a flow that never leaves the originating tab.

## Decision drivers
- Sign in must complete in the same tab it started in (the root cause fix).
- Keep it passwordless (no password storage or reset flows).
- Reuse existing email infrastructure (Resend, see [[zone-email]]).

## Considered options
- OTP code by email, same tab entry: chosen.
- Native passwords: reintroduces storage and reset flows we deliberately avoided.
- Drop Safari iOS support: unacceptable, it is a large share of mobile traffic.

## Decision outcome
Chosen: OTP email code primary, magic link secondary on desktop.
- Positive: works on Safari iOS, still passwordless, same tab means no lost
  session context. Reuses the Resend transactional pipeline.
- Negative: users must switch to email and copy a code (one extra step);
  OTP emails add load to the Resend quota; codes need a short expiry and rate
  limiting to stay safe.

## Confirmation
Manually verified sign in on a real iPhone with Safari on 2026-07-01: the code
flow completed where magic links had failed. Mobile end to end test on real
devices is still pending (see [[session-2026-07-01]]).
