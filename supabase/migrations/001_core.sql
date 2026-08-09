create extension if not exists pgcrypto;

create type autonomy_level as enum ('green','yellow','red');
create type task_status as enum ('queued','running','blocked','awaiting_approval','completed','failed','rejected');
create type priority_level as enum ('P0','P1','P2','P3');

create table if not exists agents (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  description text,
  status text not null default 'active',
  autonomy autonomy_level not null default 'yellow',
  schedule text,
  last_run_at timestamptz,
  next_run_at timestamptz,
  success_rate numeric(5,2) default 0,
  error_count integer default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists agent_runs (
  id uuid primary key default gen_random_uuid(),
  agent_id uuid references agents(id) on delete cascade,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null default 'running',
  input jsonb default '{}'::jsonb,
  output jsonb default '{}'::jsonb,
  error text,
  model text,
  input_tokens integer default 0,
  output_tokens integer default 0,
  estimated_cost numeric(12,6) default 0,
  tasks_created integer default 0
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  created_by_agent uuid references agents(id),
  assigned_to_agent uuid references agents(id),
  task_type text not null,
  title text not null,
  description text,
  priority priority_level not null default 'P2',
  confidence numeric(5,2),
  expected_impact text,
  status task_status not null default 'queued',
  requires_approval boolean not null default false,
  payload jsonb default '{}'::jsonb,
  result jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

create table if not exists approvals (
  id uuid primary key default gen_random_uuid(),
  task_id uuid references tasks(id) on delete cascade,
  status text not null default 'pending',
  requested_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by text,
  decision_note text
);

create table if not exists metrics (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  metric_name text not null,
  dimensions jsonb default '{}'::jsonb,
  value numeric,
  period_start timestamptz,
  period_end timestamptz,
  captured_at timestamptz not null default now()
);

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text,
  domain text unique,
  industry text,
  location text,
  employee_count integer,
  revenue_range text,
  icp_score numeric(5,2),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references companies(id),
  hubspot_contact_id text,
  email text,
  name text,
  source text,
  intent_score numeric(5,2),
  lifecycle_stage text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists pages (
  id uuid primary key default gen_random_uuid(),
  url text unique not null,
  title text,
  canonical_url text,
  status_code integer,
  indexable boolean,
  topic text,
  metrics jsonb default '{}'::jsonb,
  last_crawled_at timestamptz
);

create table if not exists keywords (
  id uuid primary key default gen_random_uuid(),
  keyword text unique not null,
  cluster text,
  intent text,
  icp text,
  opportunity_score numeric(5,2),
  target_page text,
  metrics jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists content_assets (
  id uuid primary key default gen_random_uuid(),
  content_type text,
  title text,
  slug text,
  status text default 'draft',
  primary_keyword text,
  research jsonb default '{}'::jsonb,
  body text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists directories (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  domain text,
  submission_url text,
  api_available boolean default false,
  automation_allowed boolean,
  verification_type text,
  authority_score numeric(5,2),
  relevance_score numeric(5,2),
  total_score numeric(5,2),
  metadata jsonb default '{}'::jsonb
);

create table if not exists citations (
  id uuid primary key default gen_random_uuid(),
  directory_id uuid references directories(id),
  status text default 'not_started',
  profile_url text,
  submitted_at timestamptz,
  verified_at timestamptz,
  last_checked_at timestamptz,
  consistency_score numeric(5,2),
  profile_data jsonb default '{}'::jsonb
);

create table if not exists backlink_opportunities (
  id uuid primary key default gen_random_uuid(),
  domain text,
  url text,
  opportunity_type text,
  relevance_score numeric(5,2),
  authority_score numeric(5,2),
  total_score numeric(5,2),
  contact_data jsonb default '{}'::jsonb,
  status text default 'new',
  created_at timestamptz not null default now()
);

create table if not exists competitors (
  id uuid primary key default gen_random_uuid(),
  name text,
  domain text unique not null,
  category text,
  priority integer default 2,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists competitor_events (
  id uuid primary key default gen_random_uuid(),
  competitor_id uuid references competitors(id),
  event_type text,
  summary text,
  source_url text,
  impact_score numeric(5,2),
  captured_at timestamptz not null default now()
);

create table if not exists mentions (
  id uuid primary key default gen_random_uuid(),
  source text,
  url text,
  mention_text text,
  sentiment text,
  linked boolean default false,
  requires_response boolean default false,
  opportunity boolean default false,
  captured_at timestamptz not null default now()
);

create table if not exists experiments (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  page_url text,
  hypothesis text,
  control text,
  variant text,
  primary_metric text,
  status text default 'planned',
  started_at timestamptz,
  ended_at timestamptz,
  result jsonb default '{}'::jsonb
);

create table if not exists daily_briefs (
  id uuid primary key default gen_random_uuid(),
  brief_date date unique not null,
  executive_summary text,
  priorities jsonb default '[]'::jsonb,
  metrics jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists system_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  severity text default 'info',
  source text,
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_tasks_status_priority on tasks(status, priority);
create index if not exists idx_agent_runs_agent_started on agent_runs(agent_id, started_at desc);
create index if not exists idx_metrics_name_period on metrics(metric_name, period_start desc);
create index if not exists idx_leads_intent on leads(intent_score desc);
