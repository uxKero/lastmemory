# supersede: contradictions and the bitemporal model

Load this when a new fact contradicts an existing one. The rule is simple: never hard delete. Supersede.

## Four dates per fact (Zep bitemporal)

Separate when we learned something from when it was true in the world:

- `created`: when we learned or recorded it (required).
- `valid_from`: when it became true in the world (nullable).
- `valid_to`: when it stopped being true (set on supersede).
- `deprecated`: when we retired the record itself (nullable).

This lets memory answer both "what was true during period P" and "what did we believe at time X".

## How to supersede

When a new fact contradicts an old one:

1. On the old neuron set `valid_to = valid_from of the new fact`, set `status: superseded`.
2. Add bidirectional links: old gets `superseded_by [[new-id]]`, new gets `supersedes [[old-id]]`.
3. Rewrite the old body in past tense, for example "Firebase was used for auth until ..." so a naive reader of the file is not misled.
4. The old neuron leaves default retrieval but stays on disk for provenance and as-of queries.

New information wins consistently. Key the supersession on valid time, not on write order, so history that arrives late still resolves correctly.

## Two speed detection

- Fast and deterministic, in a live save: same entity plus same attribute means the newer timestamp wins (last write wins), but only within that one slot, never globally, or you will kill facts that are co-true.
- LLM contradiction check, deferred to dream: run only over semantically similar pairs that were retrieved, not over everything. False positives exist (flagging two co-true facts as a conflict), which is exactly why this path runs in dream, with the approval report, and not in a live save.

## Pitfalls

- Missing `valid_from` when the text has no explicit date: degrade gracefully, use `created` as a proxy and note the uncertainty.
- Do not invalidate co-valid facts. Two things can both be true at once.
- Never lose provenance. A superseded neuron is history, not garbage.
