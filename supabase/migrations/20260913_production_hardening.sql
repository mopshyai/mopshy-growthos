-- Production hardening: runtime workflow mapping, citation-table reconciliation,
-- idempotency guarantees, watchdog support.
-- Additive and rerunnable.

-- ============================================================================
-- 1. Runtime mapping: many n8n workflows -> one GrowthOS agent.
--    Workflow IDs are opaque n8n strings (text), not uuids. Infrastructure
--    workflows (00/98/99) carry agent_slug = null. dispatch_enabled defaults
--    to false: the orchestrator only dispatches rows explicitly enabled, so
--    native n8n schedules remain the sole execution source of truth until a
--    workflow row is deliberately enabled under GROWTHOS_PAUSED=false.
-- ============================================================================
create table if not exists public.workflow_runtime_map (
  id uuid primary key default gen_random_uuid(),
  workflow_name text unique not null,
  workflow_id text unique,
  agent_slug text references public.agents(slug) on update cascade,
  workflow_role text,
  dispatch_enabled boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists workflow_runtime_map_agent_idx
  on public.workflow_runtime_map (agent_slug);

-- This table is an internal GrowthOS control-plane table. n8n reaches it over
-- PostgREST using the server-only service role. Browser roles must not have
-- direct table privileges. RLS remains enabled as defense in depth.
alter table public.workflow_runtime_map enable row level security;
revoke all on table public.workflow_runtime_map from anon, authenticated;
grant select, insert, update, delete on table public.workflow_runtime_map to service_role;

-- ============================================================================
-- 2. Citation table reconciliation.
--    In the live production database, public.citations belongs to Mopshy
--    Studio/media (claim_id, title, publisher, ...) and MUST NOT be touched.
--    GrowthOS directory citations live in public.legacy_citations. This block
--    renames legacy_citations -> growth_citations, or — on a fresh GrowthOS-
--    only database where 001_core created a GrowthOS-shaped citations table —
--    renames that, but ONLY after positively verifying the source table has a
--    directory_id column (Studio's citations does not). If growth_citations
--    already exists, nothing is renamed.
-- ============================================================================
do $$
begin
  if to_regclass('public.growth_citations') is null then
    if to_regclass('public.legacy_citations') is not null
       and exists (
         select 1 from information_schema.columns
         where table_schema = 'public' and table_name = 'legacy_citations'
           and column_name = 'directory_id'
       ) then
      alter table public.legacy_citations rename to growth_citations;
    elsif to_regclass('public.citations') is not null
       and exists (
         select 1 from information_schema.columns
         where table_schema = 'public' and table_name = 'citations'
           and column_name = 'directory_id'
       ) then
      alter table public.citations rename to growth_citations;
    end if;
  end if;
end $$;

-- Ensure the table exists even on databases where neither source existed.
create table if not exists public.growth_citations (
  id uuid primary key default gen_random_uuid(),
  directory_id uuid references public.directories(id),
  status text default 'not_started',
  profile_url text,
  submitted_at timestamptz,
  verified_at timestamptz,
  last_checked_at timestamptz,
  consistency_score numeric(5,2),
  profile_data jsonb default '{}'::jsonb
);

-- GrowthOS citations are internal automation state. Preserve service-role REST
-- access for n8n while explicitly blocking anon/authenticated table access.
alter table public.growth_citations enable row level security;
revoke all on table public.growth_citations from anon, authenticated;
grant select, insert, update, delete on table public.growth_citations to service_role;

-- ============================================================================
-- 3. Idempotency guarantees for fleet writers. The system is pre-launch, so
--    duplicate rows cannot exist yet; if applying to a database that already
--    has duplicates, de-duplicate before running these statements.
--    Every target below is a GrowthOS-owned table — no Studio/media tables
--    are referenced.
-- ============================================================================
create unique index if not exists growth_citations_directory_unique
  on public.growth_citations (directory_id);

create unique index if not exists backlink_opportunities_url_unique
  on public.backlink_opportunities (url);

create unique index if not exists content_assets_slug_unique
  on public.content_assets (slug);

create unique index if not exists mentions_url_unique
  on public.mentions (url);

create unique index if not exists leads_hubspot_contact_unique
  on public.leads (hubspot_contact_id);

-- ============================================================================
-- 4. Watchdog and publisher lookup paths.
-- ============================================================================
create index if not exists agent_runs_running_started_idx
  on public.agent_runs (started_at asc) where status = 'running';

create index if not exists content_drafts_publishing_idx
  on public.content_drafts (created_at asc) where status = 'publishing';
