# Supabase Connection — Mopshy GrowthOS

This repository is scoped to the hosted Supabase project:

- Project name: `mopshy-growthos`
- Project ref: `ftchgfwahjeqbyilsmjn`
- Region: `us-west-2`
- API URL: `https://ftchgfwahjeqbyilsmjn.supabase.co`

## AI coding/MCP connection

The repository contains a project-scoped `.mcp.json` for Supabase MCP:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?project_ref=ftchgfwahjeqbyilsmjn&features=database%2Cdocs%2Cdebugging%2Cdevelopment"
    }
  }
}
```

This file contains no access token or database secret. The developer must authenticate the MCP connection through Supabase OAuth in the coding client. Keep manual approval enabled for write operations against production.

## Supabase CLI link

From the repository root, use the current Supabase CLI and inspect its help before running commands:

```bash
npx supabase --help
npx supabase login
npx supabase link --project-ref ftchgfwahjeqbyilsmjn
```

The link is local developer state under `supabase/.temp/` and must not be committed. That directory is already ignored by `.gitignore`.

Verify the linked project before any write:

```bash
npx supabase projects list
```

Before applying migrations to production, preview them:

```bash
npx supabase db push --dry-run
```

Do **not** run `supabase db reset --linked` against this production project.

## Production credentials

Do not commit credentials. Runtime secrets belong in the execution environment (n8n Cloud or another server-side secret store), not GitHub.

GrowthOS currently expects server-side Supabase access through:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

The service-role credential must never be exposed to browser/client code. Supabase is moving new projects toward modern secret keys; any credential migration should be done separately and verified with the deployed n8n version before replacing the existing server-side variable contract.

## Current production-schema warning

Do not apply the draft production-hardening migration until PR #7's schema-collision review is resolved.

The live project currently contains both GrowthOS data and Mopshy Studio/media tables in `public`.

In particular:

- `public.citations` belongs to the Studio/media schema (`claim_id`, `title`, `publisher`, `url`, etc.).
- the GrowthOS directory citation table currently exists as `public.legacy_citations` (`directory_id`, `status`, `profile_url`, etc.).

GrowthOS must not mutate the Studio `citations` table. The final migration/workflow 09 must move GrowthOS citation tracking to a collision-safe table such as `public.growth_citations`.

## Current connection status

The hosted project is reachable and healthy. Read-only live checks and Supabase advisors can be run now. Production DDL should wait until the PR #7 blockers are fixed and the migration has been revalidated against the live schema.
