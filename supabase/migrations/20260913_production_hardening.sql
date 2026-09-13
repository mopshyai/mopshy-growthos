-- Production hardening: n8n wiring columns, idempotency guarantees, watchdog support.
-- Safe to run on an existing database: additive only, idempotent.

-- 1. Runtime wiring for orchestrator dispatch and error-handler resolution.
--    Populated AFTER workflows are imported into n8n (see docs/PRODUCTION_ACTIVATION.md).
alter table public.agents add column if not exists n8n_workflow_id uuid;
alter table public.agents add column if not exists n8n_workflow_name text;

-- 2. Idempotency guarantees for fleet writers. The system is pre-launch, so
--    duplicate rows cannot exist yet; if applying to a database that already
--    has duplicates, de-duplicate before running these statements.
create unique index if not exists citations_directory_unique
  on public.citations (directory_id) where directory_id is not null;

create unique index if not exists backlink_opportunities_url_unique
  on public.backlink_opportunities (url);

create unique index if not exists content_assets_slug_unique
  on public.content_assets (slug);

create unique index if not exists mentions_url_unique
  on public.mentions (url);

create unique index if not exists leads_hubspot_contact_unique
  on public.leads (hubspot_contact_id) where hubspot_contact_id is not null;

-- 3. Watchdog lookup path: stale running runs by age.
create index if not exists agent_runs_running_started_idx
  on public.agent_runs (started_at asc) where status = 'running';

-- 4. Publisher reconciliation lookup: drafts stuck in publishing.
create index if not exists content_drafts_publishing_idx
  on public.content_drafts (created_at asc) where status = 'publishing';
