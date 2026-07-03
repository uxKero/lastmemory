# scars-safety: guardrails for failure memory

Load this before creating or acting on a scar. This is the most valuable and the most dangerous neuron type. The guardrails here are mandatory, not optional.

## The danger

A wrong scar is worse than a one time hallucination. It gets retrieved, acted on, and reinforced every session, creating a self reinforcing false belief. A bad scar can make the agent avoid a valid path forever, never gathering the evidence that would overturn it. The research on memory confabulation and on Reflexion style self reflection is consistent on this point: unbounded negative memory is a trap.

## Mandatory fields on every scar

- `confidence`: high, medium, or low. How sure is the lesson.
- `scope`: the exact zone, context, and versions where it applies. "It broke here with this version" is not "it is always bad". This prevents overgeneralization, which is the number one failure mode.
- `expires_hint`: a date after which dream re-tests or downgrades the scar.
- A `## How to re-validate` section: the exact command or test that would confirm whether the problem still holds.

## How the agent uses a scar

- confidence high: avoid the path and warn the user.
- confidence medium: warn and proceed with care.
- confidence low: mention it as a possible risk, do not block.

A scar is a warning with a strength, not an absolute law.

## Write time checks

- If a new scar contradicts existing knowledge, flag it for review instead of letting both coexist silently.
- Scope the lesson to the smallest true context. When in doubt, lower the confidence.

## Dream time maintenance

- Scars past `expires_hint` are re-tested using their re-validate section, or their confidence is downgraded.
- A scar that turns out false is never hard deleted. Mark it `deprecated` with the reason, so the inverse mistake is not re-learned later.
- Old, high confidence, never re-validated scars are the most dangerous. Surface them in `/lastmemory status`.
