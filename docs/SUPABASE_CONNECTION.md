# Supabase Connection — Mopshy GrowthOS

This repository is scoped to the hosted Supabase project:

- Project name: `mopshy-growthos`
- Project ref: `ftchgfwahjeqbyilsmjn`
- Region: `us-west-2`
- API URL: `https://ftchgfwahjeqbyilsmjn.supabase.co`

## AI coding/MCP connection

The repository contains a project-scoped, **read-only** `.mcp.json` for the production Supabase project:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?project_ref=ftchgfwahjeqbyilsmjn&read_only=true&features=database%2Cdocs%2Cdebugging%2Cdevelopment"
    }
  }
}
```

This file contains no access token or database secret. Authenticate through Supabase OAuth in the coding client. Production MCP stays read-only so an AI coding session can inspect/debug the live project without ambient write access.

Use the linked Supabase CLI or an explicitly approved migration action for deliberate production writes.

## Supabase CLI link

From the repository root:

```bash
npx supabase --help
npx supabase login
npx supabase link --project-ref ftchgfwahjeqbyilsmjn
```

The repository has been successfully linked to `mopshy-growthos`. Local link state under `supabase/.temp/` must not be committed; that directory is ignored by `.gitignore`.

Verify the target before any write:

```bash
npx supabase projects list
```

When deploying future repo migrations through the CLI, preview first:

```bash
npx supabase db push --dry-run
```

Do **not** run `supabase db reset --linked` against this production project.

## Production credentials

Do not commit credentials. Runtime secrets belong in n8n Cloud or another server-side secret store, never GitHub or browser code.

GrowthOS currently expects server-side Supabase access through:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

The service-role credential bypasses RLS and must remain server-only.

## Production hardening status

The `production_hardening` migration was applied to the hosted project on 2026-09-14 and recorded in the Supabase migration history as version `20260914035014`.

Verified outcomes:

- `public.workflow_runtime_map` exists with n8n workflow IDs stored as opaque `text`.
- `public.legacy_citations` was safely renamed to `public.growth_citations`.
- Studio/media `public.citations` was not renamed or modified; it still has the Studio shape (`claim_id`, `title`, `publisher`, `url`, etc.).
- RLS is enabled on `workflow_runtime_map` and `growth_citations`.
- direct table privileges for `anon` and `authenticated` are revoked on both internal GrowthOS tables.
- `service_role` has server-side Data API access for n8n.
- idempotency/watchdog/publisher indexes from the hardening migration exist.
- preflight found zero duplicate groups on all new unique-index targets.

The runtime map is pre-seeded with all 20 workflow names/slugs/roles, but every `workflow_id` is still `NULL` and every `dispatch_enabled` value is `false`. This is intentional: real n8n Cloud workflow IDs must be written only after the Cloud import, and native n8n schedules remain the execution source of truth.

## Live schema boundary

The GrowthOS project still contains some Mopshy Studio/media-era tables in `public`. Do not broadly modify or delete them during GrowthOS activation.

The key citation collision is now resolved safely:

- `public.citations` = Studio/media citations — leave untouched.
- `public.growth_citations` = GrowthOS directory/citation automation state.

Workflow 09 must use only `growth_citations`.

## Advisor status

After the hardening migration, Supabase security/performance advisors were rerun.

The two new internal tables appear in the informational `rls_enabled_no_policy` lint because they intentionally have RLS enabled with no browser policies; `anon`/`authenticated` grants are revoked and n8n uses the server-only service role.

Pre-existing warnings remain around mixed Studio-era functions/policies (mutable `search_path`, publicly executable `SECURITY DEFINER` functions, and some performance/index notices). Do not change those blindly as part of GrowthOS activation; resolve them only after their Studio dependencies are understood.
