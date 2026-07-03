---
name: lastmemory
description: Persistent, token-efficient memory network for coding projects. Records sessions, decisions, learnings and failures as interconnected markdown files anchored to repo zones. Use this skill whenever the user runs any /lastmemory command, asks to save or recall session context, mentions "memory", "remember this", "what did we decide", "where did we leave off", wants a session summary saved, or asks why a past technical decision was made. Also trigger at session start if a /memory folder exists in the project.
---

# lastmemory

Persistent memory for coding agents, stored as a network of interconnected markdown files inside the project. Each file is a "neuron"; the links between files are "synapses". The agent navigates links instead of loading everything, so context stays small.

Read this file top to bottom the first time. Load the `references/` files only when a task needs them (progressive disclosure): this skill practices the token efficiency it preaches.

## Opening protocol (do this first, every session)

1. VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE. If a `/memory` folder exists at the project root, read `memory/CRITICAL.md` and `memory/BRAIN.md` before answering anything about the project.
2. ASSUME INTERRUPTION. The context window can reset at any moment. Flush durable facts to memory files before they are lost, not only at the end.
3. THE REPO IS THE TRUTH. When memory disagrees with the code, the code wins and the memory gets corrected.

If no `/memory` folder exists and the user runs a save command, run the onboarding in "First run" below.

## The brain: the /memory folder

```
/memory
  BRAIN.md          index map (MOC). Loaded every session. 50 lines max.
  CRITICAL.md       layer L0: facts that must never be forgotten. ~120 tokens. Always loaded.
  config.md         user configuration.
  .changelog.jsonl  log of memory changes (old to new) for rollback.
  sessions/         one neuron per work session.
  zones/            one neuron per repo zone (auth, payments, ...).
  decisions/        ADR style decision records, numbered NNNN-title.md.
  scars/            failures and dead ends, with confidence and scope.
  reflections/      higher level insights produced by dream.
```

Loading has layers, cheapest first:

1. L0: `CRITICAL.md` (always).
2. Index: `BRAIN.md`, a map of pointers with one line each (always).
3. Summaries: the `## Summary` block at the top of a neuron (read to decide if you open the file).
4. Full content: only for the neurons that matter to the current task.

Never dump the whole `/memory` folder into context. Load by identifier (path), just in time.

## Neuron frontmatter (universal)

Every neuron starts with this frontmatter. Omit fields that do not apply. Full skeletons per type live in `references/file-formats.md`.

```yaml
---
id: dec-2026-07-042
type: decision            # session | zone | decision | scar | reflection
summary: one line, cheap to read
zone: src/api/auth
tags: [otp, safari]
created: 2026-07-02        # required: when we learned it
valid_from: 2026-07-02     # nullable: when it was true in the world
valid_to: null             # set on supersede
status: active             # active | superseded | deprecated
importance: 7              # 1 to 10, rated on write
strength: 1                # +1 per recall (feeds temperature)
last_accessed: 2026-07-02  # reset on recall
confidence: high           # high | medium | low (mandatory on scars)
pinned: false              # true = exempt from decay
links:
  - supersedes [[dec-2026-05-017]]
  - learned_in [[session-2026-07-01]]
source_ids: []
---
```

The `## Summary` block right after the frontmatter is 3 to 4 lines maximum. It is the layer used to decide whether to open the full file. Keep summaries accurate and short at all times.

## Synapses (links)

Use typed wikilinks when there is meaning, and plain ones when generic:

`- supersedes [[dec-2026-05-017]]`, `- learned_in [[session-2026-07-01]]`, `- contradicts [[...]]`, `- relates_to [[...]]`.

Rules:

- Forward links only. Backlinks are derived by the graph script, never hand kept.
- The verb goes before the `[[...]]` and is greppable, so `generate_graph.py` can color edges by relation.
- Normalize slugs to avoid name drift (do not let `[[auth]]` and `[[Auth-flow]]` fork the graph).
- Every new neuron links to at least one other (at minimum its origin session). Orphan neurons are dead memory.

## Commands

| Command | Action |
|---|---|
| `/lastmemory` | Save the current session. Automatic level. Runs the retrieve then decide loop. |
| `/lastmemory min` or `full` | Force the record level. |
| `/lastmemory on` | Session start. Runs the opening protocol and returns a 2 paragraph catch up. |
| `/lastmemory init` | Bootstrap an initial memory from an existing repo (run once on adoption). |
| `/lastmemory remember <note>` | Mark something important mid session. Goes to a buffer the save prioritizes. |
| `/lastmemory ask "<question>"` | Query the network with RRF retrieval. Answers with the cited source. |
| `/lastmemory dream` | Consolidation. The only command allowed to rewrite destructively. |
| `/lastmemory view` | Generate or refresh the HTML graph. |
| `/lastmemory status` | Brain health. Uses `scripts/brain_stats.py`. |
| `/lastmemory export` | Pack all of `/memory` into one clean portable markdown file. |
| `/lastmemory benchmark` | Run the token measurement and regenerate the proof images. |

## /lastmemory (save): retrieve then decide

Authority rule: a live save only ADDS and lightly UPDATES. It never compresses or deletes. Destructive rewriting belongs to `dream` only. This separation prevents self edit drift.

1. Check the `remember` buffer first. Those notes have priority.
2. Regress the session: which files changed, which decisions were made, what failed, what is pending. Rate the session `importance` (1 to 10).
3. Group by repo zone, not chronologically.
4. Create the session neuron at the right level (see `references/file-formats.md`).
5. For each durable fact going into zones, decisions, or scars, run the retrieve then decide loop:
   - Retrieve the ~10 most similar existing neurons (by tags, zone, keyword; embeddings optional).
   - Show them to yourself next to the new fact and choose ONE action: ADD (no equivalent exists), UPDATE (complementary info about the same topic, edit in place keeping the same id), SUPERSEDE (contradiction, see `references/supersede.md`, never hard delete in a live save), NOOP (already known).
   - Record the change in `.changelog.jsonl` (old to new, event, timestamp placeholder if no clock is available).
6. Create decision neurons (ADR format) or scar neurons (with guardrails, see `references/scars-safety.md`) if warranted.
7. Update `last_accessed` and `strength` on touched neurons.
8. Update `BRAIN.md` (entries, temperatures, "Pick up here").
9. Show a short report: what was saved, what was updated, what was superseded.

Record state, not narrative: exact commands run, config values set, paths touched. Future sessions need the real state, not a story.

## /lastmemory on (start)

1. Read `CRITICAL.md` (L0) and `BRAIN.md` (always).
2. Read the Summary of the last session.
3. If the user says what they will work on, read only the summaries of the relevant zones (just in time, no dump).
4. Respect `token_budget` in `config.md`. If the material exceeds it, compress the catch up.
5. Return: context in 2 paragraphs, the "Pick up here" note, and warnings from scars relevant to the mentioned zones (respecting each scar confidence).
6. Turn on session mode: note important moments internally for the close, and flush early if interruption looks likely.

## /lastmemory ask

Run several cheap retrievers in parallel (keyword, tag overlap, link traversal, embeddings if enabled) and fuse them with Reciprocal Rank Fusion. Take the top 3 to 5. Answer with the cited neuron. Update `last_accessed` on what you read. Details in `references/scoring.md`.

## /lastmemory dream

Consolidation, the only command with destructive authority. Never deletes without explicit user approval, and every delete is soft (the original stays on disk). Trigger it by accumulated importance (sum of importance of new neurons since the last dream crosses `dream_trigger`), not by calendar. Full procedure in `references/dream-logic.md`. Summary of steps: cluster, merge duplicates, recursive summarize, evolve neighbors, verify against the real repo, supersede contradictions, re-validate scars, generate reflections with citations, recompute temperatures, soft prune cold low importance neurons, rebuild `BRAIN.md`, and show an approval report before any destructive change.

## /lastmemory view

Run `python scripts/generate_graph.py memory` to produce `memory/graph.html`, a self contained offline HTML graph. Nodes are colored by type, sized by connections, dimmed by temperature; orphans get a dashed outline; superseded neurons are muted. The graph includes a deterministic keyword search (no model, no network) that points to where each thing is documented, and a node panel whose relations are clickable to walk the network. Spec in `references/graph-spec.md`.

## /lastmemory status and benchmark

`status` runs `python scripts/brain_stats.py memory` and reports neuron counts, temperatures, orphans, size, and whether a dream is recommended. `benchmark` runs `python scripts/measure_tokens.py memory` and regenerates the token proof images under `benchmark/results/`. Only publish those numbers if they are true.

## Scoring in one line

Temperature (forgetting): `temperature = exp(-t / S)` where t is weeks since `last_accessed` and S is `strength` (S grows by 1 on each recall, so reused memory stops decaying). Hot above 0.6, warm 0.15 to 0.6, cold below 0.15. Importance is rated 1 to 10 on write. Retrieval ranks by recency plus importance plus relevance, fused with RRF. See `references/scoring.md`.

## Scars are dangerous (read before writing one)

A wrong scar becomes a self reinforcing false belief that makes the agent avoid a valid path forever. Every scar requires `confidence`, `scope`, and an `expires_hint` with a "How to re-validate" section. Confidence high means avoid and warn; medium means warn and proceed with care; low means mention as a possible risk, do not block. Full rules in `references/scars-safety.md`. This is not optional.

## First run (onboarding)

1. Ask: "Shared memory with the team, or personal?" Then write `config.md` accordingly and set up `.gitignore` (team keeps `/memory` in the repo except `private_folders`; personal gitignores all of `/memory`). Suggested default: team with `sessions/` private.
2. Create `BRAIN.md`, `CRITICAL.md`, the empty subfolders, and `config.md`.
3. Populate `CRITICAL.md` by asking for the hard invariants (main stack, prod rules, things that must never break).
4. If the project already has substantial code, offer `/lastmemory init` to bootstrap zones and critical facts from the repo instead of starting empty.

## /lastmemory init (bootstrap from an existing repo)

For a project that already has a lot of code, build a useful first memory instead of an empty one. Run `python scripts/scan_repo.py <repo_root>` to get a cheap map, read only the files it flags (README, manifest, existing ADRs), then propose a `CRITICAL.md`, one zone per meaningful area, and imports of any existing decision records. Bootstrapped memory is inferred, not observed: mark it with `origin: bootstrap`, low strength and confidence, and never create scars from it. Show the proposal for approval before writing. Full procedure and cautions in `references/bootstrap.md`.

## Writing principles

- Consolidate, do not accumulate. Live saves use retrieve then decide. Contradictions supersede, never hard delete.
- Everything has a why. A decision with no recorded reason is useless: what plus why plus what was discarded.
- Summaries are sacred: 3 to 4 lines, always accurate and short.
- Synapses always: every neuron links to at least one other.
- The repo is the truth.
- Scars need guardrails: confidence, scope, expiry.
- Live adds, dream rewrites. Every delete is reversible.
- Assume interruption: flush durable facts before losing context.
