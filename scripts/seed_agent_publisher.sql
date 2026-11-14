-- Draft migration (NOT applied): register the 04 publisher agent row.
--
-- Context: config/agent-registry.json assigns 04-content-github-publisher.json
-- the slug 'content-publisher' (PR #10 resolved the collision where both the
-- 03 writer and the 04 publisher were slugged 'content-production'). The live
-- agents table (verified 2026-11-13: 16 rows, unique slugs, UNIQUE(slug)) has
-- no publisher row, so orchestrator dispatch-by-slug cannot address 04 until
-- this row exists. The writer's 'content-production' row is intentionally
-- untouched.
--
-- Safety by default (verified live schema 2026-11-13):
-- - status is free text NOT NULL; the orchestrator only dispatches
--   status = 'active', so this row is inserted as 'inactive' and stays
--   non-dispatchable until the owner explicitly flips it after verifying the
--   publisher workflow handoff end to end.
-- - autonomy is an enum (green|yellow|red); 'yellow' = approval-gated.
-- - schedule is free text; the registry describes 04 as "daily 8:00 AM ET"
--   (descriptive wording only - there is no time-of-day field, and the row is
--   inactive anyway, so no schedule takes effect from this insert).
--
-- Owner applies this manually against the live database - idempotent:
insert into agents (name, slug, description, status, autonomy, schedule)
values ('Content Production (Publisher)','content-publisher','Publish approved content drafts to GitHub blog','inactive','yellow','daily')
on conflict (slug) do nothing;
