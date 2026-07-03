---
id: scar-react-pdf-build
type: scar
summary: "@react-pdf/renderer breaks the Next.js 14 production build on Vercel when imported into a Server Component. Import it only in a client boundary or render it in a route handler."
zone: src/app/invoices
tags: [react-pdf, nextjs, build, vercel, ssr]
severity: high
confidence: high
scope: "Next.js 14.2 App Router on Vercel, Node 20 build. @react-pdf/renderer 3.4 imported into a Server Component. Not tested on Pages Router or on other Node versions."
created: 2026-06-22
valid_from: 2026-06-22
valid_to: null
status: active
last_revalidated: 2026-06-22
expires_hint: 2026-09-22
importance: 7
strength: 2
last_accessed: 2026-06-22
pinned: false
links:
  - learned_in [[session-2026-06-22]]
  - relates_to [[zone-billing-ui]]
source_ids: []
---

## Summary
`@react-pdf/renderer` breaks the Next.js 14 production build on Vercel when it is
imported (even transitively) into a Server Component. The dev server hides it;
`next build` fails. Confidence high: reproduced three times.

## What happened
We imported the invoice PDF document component at the top of a Server Component
page to generate a download. `next dev` worked. `next build` on Vercel failed
with a module resolution and "self is not defined" style error from a browser
only dependency pulled in during server bundling. It cost most of an afternoon
because the failure only showed in the production build, not locally in dev.

## What to do instead
- Render the PDF in a Route Handler (`app/invoices/[id]/pdf/route.ts`) that runs
  on the server on demand, or
- Isolate the PDF component behind a Client Component boundary (`"use client"`)
  and lazy load it, so it never enters the Server Component bundle.
- Orbit currently uses the Route Handler approach; the billing UI links to it.

## How to re-validate
- Move the PDF import back into a Server Component on a throwaway branch and run
  `next build` locally (not `next dev`).
- If `next build` now succeeds on Next 14.2 plus `@react-pdf/renderer` 3.4, the
  scar is stale: downgrade confidence and note the passing versions.
- Re-check whenever we bump Next.js major or the PDF library major, since either
  bump can change the bundling behavior this scar depends on.
