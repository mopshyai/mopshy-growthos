# Autonomous Content Engine — Activation

The code and importable workflows are committed, but they are intentionally inactive until credentials and the database migration are applied.

## Required secrets in n8n

- `OPENAI_API_KEY` — OpenAI API key with Responses API access.
- `OPENAI_CONTENT_MODEL` — optional model override.
- `OPENAI_QA_MODEL` — optional independent QA model override.
- `GITHUB_CONTENT_TOKEN` — fine-grained token limited to `mopshyai/mopshy-ai-growth-engine`, with Contents read/write and Pull requests read/write.

Do not use an organization-wide classic token.

## Existing n8n credential

The workflows reuse the existing n8n `supabaseApi` credential already used by GrowthOS.

## Database

Apply:

`supabase/migrations/20260823_autonomous_content_engine.sql`

This adds:
- `content_opportunities`
- `content_drafts`
- `content_performance_snapshots`

## Import order

Import and test in this order:

1. `n8n/02-content-opportunity-agent.json`
2. `n8n/03-content-writer-qa-agent.json`
3. `n8n/04-content-github-publisher.json`

Keep all three inactive during manual testing.

## Manual smoke test

### Opportunity agent
Expected result: ~15 rows appear in `content_opportunities` with scores and source URLs.

Check manually:
- sources are real
- topics are relevant to Mopshy
- obviously duplicative ideas are marked refresh/backlog rather than publish
- no rumor is treated as confirmed news

### Writer + QA
Expected result: at most one top candidate is researched and a row is inserted in `content_drafts`.

A draft may be `blocked`. That is a successful safety outcome.

For a `ready` draft verify:
- quality score >= 90
- fact_check_passed = true
- unsupported_claim_count = 0
- sources include a primary source when the topic requires one
- article has useful implementation detail and is not a generic news summary

### GitHub publisher
Expected result:
- a new branch `content/<slug>-<date>` is created in the Mopshy website repo
- only `src/content/insights.ts` changes
- a PR opens against `main`
- existing GitHub Build CI runs
- no automatic merge occurs

## Initial production mode

After a clean smoke test, activate schedules but KEEP PR auto-merge disabled.

Recommended proving period:
- review the first 10–20 generated PRs
- measure QA false positives/negatives
- confirm no cannibalization or poor sourcing

Only then consider conditional auto-merge after successful CI.

## Schedule

- 06:30 MT — opportunity discovery
- 07:15 MT — research, draft, independent QA
- 08:00 MT — open PR for any draft that cleared every gate

Publishing is conditional. If nothing is worthy, nothing should publish.

## Next integration

Connect Google Search Console and GA4 to the existing SEO Intelligence workflow, then add the weekly performance/refresh agent so GrowthOS can choose between refresh, consolidate, and new content using real query/page data.
