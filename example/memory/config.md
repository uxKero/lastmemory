---
# lastmemory config
share_mode: team          # team | personal
# team: all of /memory goes to the repo except folders listed in private_folders
# personal: all of /memory goes to .gitignore
private_folders: [sessions]    # sessions stay local, not pushed to the shared repo
token_budget: 300              # max lines /lastmemory on may load at startup
default_level: auto            # auto | min | default | full
language: auto                 # language of the memories (auto = the user's)
dream_trigger: 40              # accumulated importance threshold that suggests a dream
temperature_unit: weeks        # unit of t in e^(-t/S)
use_embeddings: false          # false = grep/tags/links only (zero setup)
scoring_weights: {recency: 1, importance: 1, relevance: 1}
---

# Orbit memory config

Team share mode: the whole `/memory` folder is versioned in the repo so the
crew shares decisions, zones, scars and reflections. Only `sessions/` is
private (listed in `private_folders`) because per person session logs are noisy
and sometimes personal. The install step wrote `sessions/` into `.gitignore`.

Change any value by editing this file. Nothing here is loaded into context at
runtime except when a command needs it.
