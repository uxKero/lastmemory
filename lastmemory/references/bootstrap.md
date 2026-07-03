# bootstrap: initial memory from an existing repo

Load this for `/lastmemory init`. It builds a useful first memory for a project that already has a lot of code, instead of starting empty. This runs once, at adoption, on a mature repo. On a fresh project you do not need it: normal sessions grow the memory.

## The core caution

Bootstrapped memory is inferred, not observed. Nobody lived these sessions; the skill is reading structure and docs and guessing. So every bootstrapped neuron is marked as such and is treated as a weak, unconfirmed starting point, not as hard won knowledge:

- Add `origin: bootstrap` to the frontmatter.
- Set `strength: 1` and a low `last_accessed` so the temperature cools quickly unless real work reinforces it.
- For zones and critical facts, set `confidence: low` or `medium`.
- Do NOT create scars from a bootstrap. A scar records a real observed failure. There is nothing to observe yet.

The next `dream` verifies paths against the repo, and the first real sessions confirm or correct the guesses. This keeps a wrong inference from masquerading as a lesson.

## Procedure

1. Run `python scripts/scan_repo.py <repo_root>` to get a compact map: candidate zones by size, key project files, and any existing decision records. This is cheap and reads no file bodies beyond line counts.
2. Read only the files the map flagged: `README`, the manifest (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, and similar), and any existing ADR markdown. Do not read the whole repo.
3. Draft a proposal, do not write yet:
   - `CRITICAL.md` (L0): the main stack, entry points, and hard rules you can infer from the manifest and README (for example "Postgres is the only datastore", "tests run with pytest"). Keep it to about 120 tokens.
   - One zone neuron per meaningful code area from the map, with the real `paths:` filled in, a short Summary of what the area appears to do, and `origin: bootstrap`. Prefer a handful of solid zones over one per folder.
   - Import each existing ADR as a decision neuron (ADR format, `status: active`, `created` from the file if datable, else left blank with a note). These are genuine records, so they do not need the bootstrap discount, but link them to the zone they govern.
4. Show the full proposal for approval, the same way `dream` does: "I propose to create this CRITICAL.md, these N zones, and import these M decisions. Confirm?". Write only on confirmation.
5. Build `BRAIN.md` from what was created, and tell the user plainly that this memory is a bootstrap: it is a scaffold to be confirmed by real sessions, not a lived history.

## What bootstrap does not do

- It does not invent decisions or reasons that are not written down somewhere in the repo. A decision neuron needs a real source; if the README does not say why Supabase was chosen, the zone notes "uses Supabase" without a fabricated rationale.
- It does not create failure memory.
- It does not claim high confidence. Everything is a starting hypothesis that the repo and the next sessions will settle.
