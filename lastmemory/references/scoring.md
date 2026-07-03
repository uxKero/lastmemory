# scoring: temperature, importance, retrieval

Load this for `/lastmemory ask`, for temperature updates, and when ranking `BRAIN.md`. All formulas are cheap and need no model call at read time.

## Temperature (forgetting), MemoryBank

```
temperature = exp(-t / S)
  t = time since last_accessed, measured in weeks
  S = strength (starts at 1, grows by 1 on each recall)

on recall:  strength += 1;  last_accessed = now
```

Reused memory reheats and stops decaying; untouched memory cools. The time unit is weeks on purpose: with days the decay is too aggressive for code (retention would be 0.37 after a single day). If `last_accessed` is missing, fall back to `created`. If both are missing, treat t as 0.

Visual and behavior thresholds:

- temperature above 0.6: hot. Bright in the graph. Kept in full.
- temperature 0.15 to 0.6: warm. Normal.
- temperature below 0.15: cold. Dim in the graph. Candidate for compression in dream.

Pinned neurons are exempt from decay (identity and hard invariants).

## Importance, Generative Agents

Rate every neuron 1 to 10 on write with this framing: "How significant is this for the project? 1 is trivial (a rename), 10 is an architecture decision or a serious failure." Importance is used to rank `BRAIN.md` and to trigger dream (see dream-logic.md). LLM importance ratings drift upward, so bias slightly conservative.

## Retrieval for /lastmemory ask, RRF fusion

Run several cheap retrievers in parallel, then fuse. No score calibration is needed.

Retrievers:

- keyword or BM25 style match over summaries and bodies (grep is enough).
- tag and zone overlap with the question.
- link traversal: start from the best hit and follow synapses one or two hops.
- embeddings: only if `use_embeddings` is true in config.

Fuse with Reciprocal Rank Fusion:

```
score(neuron) = sum over retrievers of  1 / (60 + rank_in_that_retriever)
```

Take the top 3 to 5. Answer with the cited neuron id. Update `last_accessed` and `strength` on what you actually read (that feeds temperature).

## Ranking BRAIN.md

Order entries within each section by a weighted blend:

```
rank = w_recency * temperature + w_importance * (importance / 10) + w_relevance * relevance
```

Weights come from `scoring_weights` in config (default all 1). Relevance is optional at index build time; recency and importance alone are enough to keep BRAIN.md useful. Equal weights are fragile, so expose them and let the user tune.

## Notes and pitfalls

- Always update `last_accessed` on retrieval. That single write is what makes the whole scheme work.
- Keep the retrieved set small (3 to 5). More than 10 retrieved neurons drown the question.
- The top failure mode in the literature is failing to retrieve the right memory, not storing too much. Favor good summaries and good tags over clever scoring.
