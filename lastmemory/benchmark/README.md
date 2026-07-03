# benchmark: token cost, measured honestly

The headline of `lastmemory` is that it recalls a whole project for a fraction of the context. This folder measures that on a fixed, reproducible scenario, and produces the images that go in the main README.

## The honesty rule

Numbers and images from this benchmark only go in the README if they are true on the bundled scenario. If a measurement does not favor `lastmemory`, the fix is to improve the design or correct the claim, never to tune the benchmark to look good. If a competitor cannot be measured fairly on the same scenario, we say so instead of inventing a number.

## What we measure

The cost, in tokens, of getting an agent up to speed on a project it has worked on before: enough context to answer "where did we leave off, and what should I watch out for" at the same quality.

- Primary metric: input tokens loaded to reach that catch up.
- Secondary metric: latency of the load.

## The scenario

`example/memory/` at the repo root is the fixed scenario: a complete memory network for a fictional SaaS app (Orbit). It is versioned so anyone can reproduce the numbers. Do not measure on a private repo; measure on this one so results are comparable across machines and over time.

## What we compare

1. **lastmemory `on` load**: `CRITICAL.md` plus `BRAIN.md` plus the single most relevant zone summary.
2. **Dump everything baseline**: concatenate every markdown file under the memory folder. This is the worst case, and it sizes the ceiling of the saving.
3. **Anthropic memory tool flow**: the tokens its "view memory" step loads on the same scenario.
4. **The memory skills with the most stars on GitHub**: pick the top by star count that we can install and measure fairly on the same scenario, measured the same way. The exact list is chosen in this phase, with the tools in hand. Known candidates: claude-mem, Serena, Basic Memory, mem0.

Comparisons 3 and 4 are done last, once the skill and the scenario are stable.

## How to run

```
python ../scripts/measure_tokens.py ../../example/memory --out-dir results
```

Token counting uses tiktoken when it is installed (exact counts) and falls back to a documented characters over four heuristic otherwise (results are labeled ESTIMATED in that case). The script writes:

- `results/token-comparison.svg`: a horizontal bar chart, generated without any plotting library so it works offline.
- `results/token-comparison.md`: a table with tokens, percent saved versus the dump baseline, whether counts are exact or estimated, and a note that this is a local example, not an academic benchmark.

## Reading the results

A saving over the dump baseline is expected and easy; that is the floor, not the story. The meaningful comparison is against the Anthropic memory tool and the top starred skills on the identical scenario. Report those plainly, favorable or not.
