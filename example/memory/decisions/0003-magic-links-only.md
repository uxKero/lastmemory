---
id: dec-0003
type: decision
summary: (Superseded) Orbit used magic links as the only sign in method. Replaced after magic links proved unreliable on Safari iOS. See dec-0004.
zone: src/app/auth
tags: [auth, magic-link, supabase, safari]
created: 2026-05-28
valid_from: 2026-05-28
valid_to: 2026-07-01
status: superseded
importance: 6
strength: 2
last_accessed: 2026-07-01
confidence: high
pinned: false
links:
  - superseded_by [[dec-0004]]
  - decided_in [[session-2026-05-28]]
  - relates_to [[zone-auth]]
source_ids: []
---

## Summary
(Past tense: superseded on 2026-07-01 by [[dec-0004]].)
Orbit used Supabase magic links as the single sign in method. There was no
password and no code entry: the user typed their email, received a link and
clicked it to land signed in. This was chosen for speed of build and to avoid
storing passwords.

## Context and problem
At launch we wanted the smallest possible auth surface. Supabase magic links
gave us passwordless sign in with almost no code, so that was what we shipped.

## Decision drivers (as they stood in May 2026)
- No password storage or reset flows to build.
- One Supabase call to send the link.
- Fewest screens to design.

## Considered options (as they stood then)
- Magic links only: chosen at the time.
- Email plus password: more screens, password reset, storage concerns.
- OTP codes by email: not yet considered seriously.

## Decision outcome (historical)
Chosen at the time: magic links only.
- What went wrong: on Safari iOS the link often opened in a different browser
  context than the one that requested it, so the session cookie was not present
  and the user landed logged out. This recurred across sessions (see the
  reflection [[refl-safari-ios-auth]]) and blocked mobile sign in for a real
  share of users.

## Confirmation
Refuted in production. Magic links failed repeatedly on Safari iOS, which drove
the move to an OTP email fallback. This decision was superseded by [[dec-0004]];
its `valid_to` is set to the day the OTP fallback shipped.
