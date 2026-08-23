create table if not exists public.content_opportunities (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  topic text not null,
  angle text,
  source_type text,
  status text not null default 'discovered' check (status in ('discovered','researching','approved','rejected','drafting','qa','ready','published','refresh_candidate')),
  opportunity_score numeric(5,2),
  topical_relevance numeric(5,2),
  search_intent numeric(5,2),
  trend_acceleration numeric(5,2),
  commercial_relevance numeric(5,2),
  original_insight numeric(5,2),
  competition_opportunity numeric(5,2),
  ai_citation_potential numeric(5,2),
  cannibalization_risk numeric(5,4),
  recommended_action text check (recommended_action in ('publish','research','backlog','refresh','ignore')),
  target_keyword text,
  search_intent_label text,
  rationale text,
  source_urls jsonb not null default '[]'::jsonb,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists content_opportunities_status_idx on public.content_opportunities(status);
create index if not exists content_opportunities_score_idx on public.content_opportunities(opportunity_score desc);

create table if not exists public.content_drafts (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid references public.content_opportunities(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  slug text not null unique,
  title text not null,
  category text not null,
  excerpt text,
  meta_title text,
  meta_description text,
  keywords jsonb not null default '[]'::jsonb,
  body jsonb not null default '[]'::jsonb,
  faqs jsonb not null default '[]'::jsonb,
  sources jsonb not null default '[]'::jsonb,
  internal_links jsonb not null default '[]'::jsonb,
  quality_score numeric(5,2),
  fact_check_passed boolean not null default false,
  primary_source_present boolean not null default false,
  unsupported_claim_count integer not null default 0,
  commercial_relevance_score numeric(5,2),
  status text not null default 'draft' check (status in ('draft','qa','blocked','ready','publishing','published','failed')),
  qa_report jsonb not null default '{}'::jsonb,
  published_url text,
  github_pr_url text,
  published_at timestamptz
);

create index if not exists content_drafts_status_idx on public.content_drafts(status);

create table if not exists public.content_performance_snapshots (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid references public.content_drafts(id) on delete cascade,
  captured_at timestamptz not null default now(),
  window_days integer not null,
  impressions bigint,
  clicks bigint,
  ctr numeric(8,6),
  avg_position numeric(8,3),
  organic_sessions bigint,
  conversions bigint,
  chatgpt_referrals bigint,
  other_ai_referrals bigint,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists content_performance_draft_idx on public.content_performance_snapshots(draft_id, captured_at desc);
