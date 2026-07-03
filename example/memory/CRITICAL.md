# CRITICAL: Orbit (L0, always loaded)

- Stack: Next.js 14 (App Router) + Supabase (auth + Postgres) + MercadoPago (payments) + Resend (email).
- Prod database is Supabase project `orbit-prod`. NEVER run migrations or seed scripts against it directly; go through `supabase db push` on a reviewed branch.
- Never commit to `main`. All work flows through PRs.
- Money is stored in integer centavos (ARS), never floats. Invoices are immutable once `status = paid`.
- Row Level Security is ON for every table. A query that bypasses RLS is a bug, not a shortcut.
- Secrets (Supabase service key, MercadoPago access token, Resend API key) live only in Vercel env vars, never in the repo.
