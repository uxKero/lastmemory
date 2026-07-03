# Token comparison

<!-- TODO: fill date -->

This is a local example measured on one `/memory` folder. It is not an academic benchmark: it only shows the token cost of a few loading strategies on this particular brain.

| Scenario | Tokens | Percent saved vs baseline |
|---|---:|---:|
| lastmemory on (L0 + BRAIN + 1 zone) | 1435 | 86.6% |
| baseline: dump every .md (22 files) | 10713 | baseline |

Baseline for the percentages: **baseline: dump every .md (22 files)** (10713 tokens).

_Counts are exact, produced with the tiktoken tokenizer._
