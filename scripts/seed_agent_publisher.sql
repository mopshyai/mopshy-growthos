-- Draft migration (NOT applied): register the 04 publisher agent row.
--
-- Context: config/agent-registry.json assigns 04-content-github-publisher.json
-- the slug 'content-publisher' (PR #10 resolved the collision where both the
-- 03 writer and the 04 publisher were slugged 'content-production'). The live
-- agents table (verified 2026-11-13: 16 rows, unique slugs) has no publisher
-- row, so orchestrator dispatch-by-slug cannot address 04 until this row
-- exists. The writer's 'content-production' row is intentionally untouched.
--
-- Owner applies this manually against the live database - idempotent:
insert into agents (name, slug, description, autonomy, schedule)
-- Schedule uses the table's existing convention ('daily'); the registry's
-- descriptive 'daily 8:00 AM ET' maps to the same daily due-check.
values ('Content Production (Publisher)','content-publisher','Publish approved content drafts to GitHub blog','yellow','daily')
on conflict (slug) do nothing;
