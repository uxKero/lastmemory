# dream-logic: consolidation, the only destructive pass

Load this for `/lastmemory dream`. Dream is the sole command with authority to rewrite destructively. It never deletes without explicit user approval, and every delete is soft (the original stays on disk, because summarization loss compounds across passes and must be reversible).

## When to run

Trigger by accumulated importance, not by calendar: run when the sum of `importance` of new neurons since the last dream crosses `dream_trigger` (default 40 in config). This fires in proportion to how much significant material piled up. `/lastmemory status` also suggests a dream when any of these hold:

- 3 or more cold neurons.
- BRAIN.md is over 50 lines.
- one or more scars are past their `expires_hint`.

## Content hash gating (Cognee)

Do not reprocess neurons that have not changed since the last dream. Keep a hash per neuron; skip unchanged ones. This makes the pass idempotent, resumable, and cheap.

## Steps

1. Cluster recent and neighboring neurons (by tags and zone; embeddings optional).
2. Merge (batch retrieve then decide): if 3 or more sessions feed the same conclusion, lift the conclusion into the zone or decision neuron and compress those sessions down to their Summary. Merge semantic duplicates keeping the same id.
3. Recursive summarize: `new_summary = LLM(old_summary + new_items)`. Loss compounds, so keep originals recoverable.
4. Evolve neighbors (A-MEM): when integrating a new neuron, rewrite only the derived fields of its neighbors (context, tags, links), never the original content.
5. Verify against the real repo: for each zone neuron, check that the `paths:` exist. If the referenced code is gone, mark the neuron obsolete and propose archiving. Do not guess, verify.
6. Supersede sweep: resolve contradictions between neurons (see supersede.md).
7. Re-validate scars (see scars-safety.md): scars past `expires_hint` get re-tested or downgraded in confidence.
8. Reflections: generate higher level insights about recurring patterns, each with mandatory `source_ids` citing the neurons it came from. Save to `reflections/`.
9. Recompute temperatures (see scoring.md) and soft prune neurons that are cold, low importance, and not pinned.
10. Rebuild BRAIN.md from the post consolidation state.
11. Approval report: BEFORE any destructive change, show "I propose to delete N, merge M, compress K, supersede J. Confirm?" and execute only on confirmation.

## Sleep time framing

This is the manual, batch version of Letta sleep time compute: the expensive reorganizing work happens off the hot path, so live sessions stay fast and append only. Prefer running dream when the user is idle or explicitly asks, not mid task.

## Safety invariants

- Live saves never call dream logic. Only `/lastmemory dream` rewrites.
- Every destructive op is soft and logged to `.changelog.jsonl` (old to new).
- Never hard delete a scar that turned out false: mark it `deprecated` with the reason, so the inverse mistake is not re-learned.
- If unsure whether two facts conflict, keep both and flag for the next dream rather than silently dropping one.
