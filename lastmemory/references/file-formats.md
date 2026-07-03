# file-formats: exact neuron skeletons

Load this when creating or editing a neuron. Every neuron uses the universal frontmatter from SKILL.md. Below are the body skeletons per type. Keep the `## Summary` block to 3 or 4 lines: it is the layer the agent reads to decide whether to open the full file.

## Session neuron (sessions/YYYY-MM-DD.md)

If there are two or more sessions the same day, suffix with a letter: `2026-07-02-b.md`.

```markdown
---
id: session-2026-07-02
type: session
summary: one line on what this session was about
zone: src/lib/auth
tags: [otp, safari]
created: 2026-07-02
importance: 7
strength: 1
last_accessed: 2026-07-02
level: default            # min | default | full
links:
  - touched [[zones/auth.md]]
  - decided [[decisions/0003-otp-email-fallback.md]]
---

## Summary
Refactor of the login flow. Added OTP by email as a fallback because
Google Sign In fails on Safari iOS. Pending: test on a real mobile device.

## What was done
- exact commands run, config values set, files touched (not just "did X")

## Decisions made
- OTP as fallback, reason, see [[decisions/0003-otp-email-fallback.md]]

## Scars (if any)
- ...

## Pending
- ...

## Full log (only when level is full)
- discarded reasoning, key conversation fragments, code fragility
```

Record levels:

- min: Summary plus Pending only (5 to 10 lines).
- default: everything except Full log.
- full: everything, including discarded reasoning ("we considered X but not because ...").

Pick the level automatically by session magnitude (files touched, whether there were architecture decisions, whether there were significant errors). The user can force it with `/lastmemory min` or `/lastmemory full`.

## Zone neuron (zones/NAME.md)

```markdown
---
id: zone-auth
type: zone
summary: current state of the auth zone in 3 or 4 lines
zone: src/lib/auth
paths: [src/lib/auth, src/components/auth]   # repo folders this zone covers
tags: [auth, sessions]
created: 2026-05-10
last_accessed: 2026-07-02
strength: 4
importance: 8
status: active
links:
  - governed_by [[decisions/0003-otp-email-fallback.md]]
  - warns [[scars/supabase-rls-recursion.md]]
---

## Summary
Living knowledge of the zone in 3 or 4 lines.

## Current state
- how it works today, what it uses, what it touches

## Active decisions
- current decisions with a link to their decision neuron

## Watch out
- known fragilities, things to break carefully

## History (compressed, past tense)
- 2026-06-15: migrated from X to Y
```

The `paths:` list is verified against the real repo by `dream` (see dream-logic.md).

## Decision neuron (decisions/NNNN-title.md), ADR and MADR format

Numbered with zero padding for chronological order and stable link targets. Offer a full version and a bare minimal version.

```markdown
---
id: dec-0003
type: decision
summary: chose OTP email fallback because Google Sign In fails on Safari iOS
zone: src/lib/auth
tags: [auth, otp]
created: 2026-06-10
valid_from: 2026-06-10
valid_to: null
status: active            # active | superseded | deprecated
importance: 8
links:
  - decided_in [[sessions/2026-06-10.md]]
---

## Summary
Chose OTP by email as the auth fallback over relying on Google Sign In only.

## Context and problem
## Decision drivers
## Considered options
## Decision outcome
- Chosen: OTP email fallback. Positive and negative consequences.
## Confirmation
- how we verify the decision was correct
```

Bare minimal version keeps only Summary, Decision outcome, and Confirmation.

When a decision is superseded: set `status: superseded`, add `superseded_by [[decisions/NNNN-...]]`, set `valid_to`, and rewrite the body in past tense (see supersede.md).

## Scar neuron (scars/NAME.md), with mandatory guardrails

See scars-safety.md for the full reasoning. `confidence`, `scope`, and `expires_hint` are mandatory.

```markdown
---
id: scar-2026-05-020
type: scar
summary: library X breaks the production build on Node 18, do not use it there
severity: high            # high | medium | low
confidence: high          # mandatory: how sure is the lesson
scope: "build in CI on Node 18, not verified on other versions"   # mandatory
zone: build
created: 2026-05-20
last_revalidated: 2026-05-20
expires_hint: 2026-08-20
status: active
links:
  - found_in [[sessions/2026-05-20.md]]
---

## Summary
Library X breaks the production build on Node 18. Do not use it in that config.

## What happened
## What to do instead
## How to re-validate
- the command or test that would confirm whether the problem still holds
```

## Reflection neuron (reflections/NAME.md), produced by dream

```markdown
---
id: reflection-2026-07-01
type: reflection
summary: Safari iOS keeps breaking auth flows across several sessions
zone: src/lib/auth
tags: [safari, auth, pattern]
created: 2026-07-01
importance: 7
source_ids: [session-2026-05-20, session-2026-06-10, session-2026-06-28]
links:
  - relates_to [[zones/auth.md]]
---

## Summary
Higher level insight derived from several neurons, with citations.

## Pattern
- what recurs across the cited sessions

## Implication
- what this means for how we build in this zone
```

Reflections must cite their `source_ids`. A reflection with no provenance is not allowed.
