-- Content engine hardening: writer metadata, query-path indexes, performance agent identity.

alter table public.content_drafts add column if not exists read_time text;

-- Publisher queue lookup (04 - Guarded GitHub Blog Publisher).
create index if not exists content_drafts_publish_queue_idx
  on public.content_drafts (status, created_at asc)
  where status = 'ready';

-- Writer candidate lookup (03 - Autonomous Content Writer + QA).
create index if not exists content_opportunities_candidate_idx
  on public.content_opportunities (recommended_action, opportunity_score desc)
  where status = 'discovered';

-- Performance agent identity (05 - Content Performance Agent).
insert into agents (name, slug, description, autonomy, schedule)
values ('Content Performance','content-performance','Measure published article performance and raise refresh signals','green','daily')
on conflict (slug) do nothing;
