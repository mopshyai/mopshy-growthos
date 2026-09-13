# Mopshy Autonomous Content Engine — n8n Cloud Activation

## Architecture

The two Mopshy repositories stay deliberately separate:

- `mopshyai/mopshy-growthos` — research, opportunity scoring, writing, fact-checking, editorial state, and performance memory.
- `mopshyai/mopshy-ai-growth-engine` — public website, blog rendering, SEO/schema, sitemap, and the published article files.

n8n Cloud runs the GrowthOS agents. GrowthOS Supabase stores internal editorial state. GitHub is the guarded bridge between the two repositories. Vercel builds a preview for each website PR and deploys mopshy.com after approved website changes merge.

GrowthOS never needs direct database access from the public website. A publish operation creates one isolated website file at:

`src/content/blog/articles/<slug>.article.json`

The publisher is not designed to modify website routes, components, configuration, legacy articles, or the unified article registry.

## Required n8n credentials

Create/select these credentials inside the `MOPSHY GROWTHOS` n8n Cloud project:

1. **Mopshy OpenAI** — OpenAI API credential using Mopshy's own OpenAI API key. Do not rely on n8n free OpenAI credits for this production workflow.
2. **Mopshy Google OAuth2** — generic Google OAuth2 credential used by SEO Intelligence (01) and Content Performance (05) for Search Console and GA4. Scopes: `https://www.googleapis.com/auth/webmasters.readonly` and `https://www.googleapis.com/auth/analytics.readonly`.
3. **Mopshy Content Publisher** — GitHub API credential using the fine-grained token scoped to `mopshyai/mopshy-ai-growth-engine` with Contents read/write and Pull requests read/write.

No Supabase credential is required in n8n: every workflow calls the Supabase REST API using the instance environment variables `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Confirm these (plus `GSC_SITE_URL`, `GA4_PROPERTY_ID`, `TELEGRAM_CHAT_ID`) are configured in the n8n Cloud project environment.

The content workflows use the model `gpt-5.6-sol` directly. No `OPENAI_CONTENT_MODEL` or `OPENAI_QA_MODEL` variables are required.

## Prerequisite — website publishing boundary

Website PR #15 ("Refactor blog for isolated autonomous article publishing") merged into `mopshyai/mopshy-ai-growth-engine` on 2026-08-23. It adds build-time validation and the one-file-per-article loader while preserving all existing posts through the legacy registry. This prerequisite is satisfied.

## Step 1 — Apply the GrowthOS Supabase migrations

In the Supabase project connected to GrowthOS, open SQL Editor and run, in order:

1. `supabase/migrations/20260823_autonomous_content_engine.sql`

   This creates `content_opportunities`, `content_drafts`, and `content_performance_snapshots`. The migration is idempotent (`create table if not exists`).

2. `supabase/migrations/20260912_content_engine_hardening.sql`

   This adds `content_drafts.read_time`, the publisher/writer query-path indexes, and registers the `content-performance` agent used by workflow 05.

These are internal GrowthOS/editorial tables; they are not the public website's content database.

## Step 2 — Import workflows into MOPSHY GROWTHOS

Import these four JSON workflows from the GrowthOS repository:

- `n8n/02-content-opportunity-agent.json`
- `n8n/03-content-writer-qa-agent.json`
- `n8n/04-content-github-publisher.json`
- `n8n/05-content-performance-agent.json`

Keep the existing GrowthOS workflows in place. Workflow 01 (SEO Intelligence) is part of the Sprint-01 foundation and uses the same credential model as 05.

## Step 3 — Assign credentials after import

### 02 — Autonomous Content Opportunity Agent

- `Research + Score Opportunities` → **Mopshy OpenAI**

Supabase nodes (`Get Existing Opportunities`, `Store Opportunities`) need no credential — they read the instance environment variables.

### 03 — Autonomous Content Writer + QA

Use **Mopshy OpenAI** for:

- `Research + Draft`
- `Independent Fact Check + QA`

Supabase nodes (`Get Best Publish Candidate`, `Mark Researching`, `Store QA'd Draft`, `Update Opportunity Status`) need no credential.

### 04 — Guarded GitHub Blog Publisher

Use **Mopshy Content Publisher** for:

- `Get Website Main SHA`
- `Create Article Branch`
- `Create Article File Only`
- `Open Review PR`

Supabase nodes (`Get Ready Draft`, `Record PR`) need no credential.

The code node `Prepare Isolated Article File` does not need a credential. It converts the approved GrowthOS draft into the website's validated JSON article schema.

### 05 — Content Performance Agent

Use **Mopshy Content Publisher** for `Get PR State`, and **Mopshy Google OAuth2** for `GSC Page Performance`, `GSC Page Performance (No GA4)`, and the GA4 nodes. `GA4 Page Sessions` / `GA4 AI Referrals` only execute when `GA4_PROPERTY_ID` is set; without it the workflow captures Search Console data only.

Supabase nodes need no credential.

## Step 4 — Manual end-to-end test

Do not activate the schedules immediately.

1. Leave 02, 03, 04, and 05 inactive.
2. Manually execute **02**.
3. Confirm rows appear in `content_opportunities` and inspect the winning topics/scores. Confirm previously discovered topics are not duplicated.
4. Manually execute **03**.
5. Confirm one `content_drafts` row is created and inspect its `qa_report`, sources, internal links, and final body.
6. Only if the draft status is `ready`, manually execute **04**.
7. Confirm 04 creates a `content/<slug>-YYYY-MM-DD` branch in `mopshyai/mopshy-ai-growth-engine`.
8. Confirm the branch contains exactly one new file under `src/content/blog/articles/`.
9. Confirm a review PR opens against website `main` and auto-merge does not occur.
10. Confirm the Vercel preview is READY and the new `/blog/<slug>` page renders correctly before merging the article PR.
11. Merge the article PR, then manually execute **05** and confirm the draft flips to `published` with `published_url` set.
12. After 7+ days, manually execute **05** again and confirm a `content_performance_snapshots` row with `window_days = 7` appears for that draft.

## Step 5 — Activate schedules

After the manual end-to-end test passes, publish/activate in this order:

- **02** — daily 6:30 AM America/New_York
- **03** — daily 7:15 AM America/New_York
- **04** — daily 8:00 AM America/New_York
- **05** — daily 8:30 AM America/New_York

Auto-merge remains disabled during the initial rollout. The publisher only creates a review PR after the quality gates pass.

## Safety gates

A new article can reach publishing only when:

- opportunity score >= 82
- cannibalization risk <= 0.65
- quality score >= 90
- fact-check passes
- unsupported material factual claims = 0
- QA reported no outdated claims
- category is in the `config/content-engine.json` allowlist
- source/primary-source requirements pass
- slug matches the safe filename pattern
- body contains enough structured content to render
- meta description and keyword fields pass the publisher/build checks

The website build independently validates every `*.article.json` file again. A malformed article fails the Vercel/GitHub build rather than reaching production.

If no candidate meets the threshold, the correct behavior is to publish nothing.
