# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog, and the project aims to follow semantic versioning once it stabilizes.

## Unreleased

### Added
- Core skill: `SKILL.md` with the opening protocol, the retrieve then decide save loop, and all commands.
- Reference docs: `file-formats`, `scoring`, `dream-logic`, `supersede`, `scars-safety`, `graph-spec`.
- Scripts: `generate_graph.py` (offline HTML graph), `brain_stats.py` (brain health), `measure_tokens.py` (token benchmark).
- Self contained offline graph template with a hand written canvas force simulation, no CDN.
- In graph logic search: a deterministic keyword finder (no model, no network) that points to where each thing is documented, with snippets and click to navigate.
- Clickable relations in the node panel (Links out and Linked from) to walk the network by hand.
- Example memory network for a fictional project (Orbit) showing every neuron type.
- Benchmark harness with an honesty rule: numbers only ship if they are true on the bundled scenario.
- README with banner, badges, and an about section.

### Notes
- This is an alpha. The token benchmark comparisons against the Anthropic memory tool and the most starred memory skills are defined and will be run in the benchmark phase.
