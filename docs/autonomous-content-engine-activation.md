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
2. **Supabase account** — existing Supabase API credential for the GrowthOS Supabase project.
3. **Mopshy Content Publisher** — GitHub API credential using the fine-grained token scoped to `mopshyai/mopshy-ai-growth-engine` with Contents read/write and Pull requests read/write.

The content workflows use the model `gpt-5.6-sol` directly. No `OPENAI_CONTENT_MODEL` or `OPENAI_QA_MODEL` variables are required.

## Prerequisite — website publishing boundary

Before activating the publisher, website PR #15 must be merged into `mopshyai/mopshy-ai-growth-engine`.

That change adds build-time validation and the one-file-per-article loader while preserving all existing posts through the legacy registry. The publisher depends on this website capability being present on `main`.

## Step 1 — Apply the GrowthOS Supabase migration

In the Supabase project connected to GrowthOS, open SQL Editor and run:

`supabase/migrations/20260823_autonomous_content_engine.sql`

This creates:

- `content_opportunities`
- `content_drafts`
- `content_performance_snapshots`

The migration is idempotent (`create table if not exists`). These are internal GrowthOS/editorial tables; they are not the public website's content database.

## Step 2 — Import workflows into MOPSHY GROWTHOS

Import these three JSON workflows from the GrowthOS repository:

- `n8n/02-content-opportunity-agent.json`
- `n8n/03-content-writer-qa-agent.json`
- `n8n/04-content-github-publisher.json`

Keep the existing GrowthOS workflows in place.

## Step 3 — Assign credentials after import

### 02 — Autonomous Content Opportunity Agent

- `Research + Score Opportunities` → **Mopshy OpenAI**
- `Store Opportunities` → **Supabase account**

### 03 — Autonomous Content Writer + QA

Use **Supabase account** for:

- `Get Best Publish Candidate`
- `Mark Researching`
- `Store QA'd Draft`
- `Update Opportunity Status`

Use **Mopshy OpenAI** for:

- `Research + Draft`
- `Independent Fact Check + QA`

### 04 — Guarded GitHub Blog Publisher

Use **Supabase account** for:

- `Get Ready Draft`
- `Record PR`

Use **Mopshy Content Publisher** for:

- `Get Website Main SHA`
- `Create Article Branch`
- `Create Article File Only`
- `Open Review PR`

The code node `Prepare Isolated Article File` does not need a credential. It converts the approved GrowthOS draft into the website's validated JSON article schema.

## Step 4 — Manual end-to-end test

Do not activate the schedules immediately.

1. Leave 02, 03, and 04 inactive.
2. Manually execute **02**.
3. Confirm rows appear in `content_opportunities` and inspect the winning topics/scores.
4. Manually execute **03**.
5. Confirm one `content_drafts` row is created and inspect its `qa_report`, sources, internal links, and final body.
6. Only if the draft status is `ready`, manually execute **04**.
7. Confirm 04 creates a `content/<slug>-YYYY-MM-DD` branch in `mopshyai/mopshy-ai-growth-engine`.
8. Confirm the branch contains exactly one new file under `src/content/blog/articles/`.
9. Confirm a review PR opens against website `main` and auto-merge does not occur.
10. Confirm the Vercel preview is READY and the new `/blog/<slug>` page renders correctly before merging the article PR.

## Step 5 — Activate schedules

After the manual end-to-end test passes, publish/activate in this order:

- **02** — daily 6:30 AM America/Denver
- **03** — daily 7:15 AM America/Denver
- **04** — daily 8:00 AM America/Denver

Auto-merge remains disabled during the initial rollout. The publisher only creates a review PR after the quality gates pass.

## Safety gates

A new article can reach publishing only when:

- opportunity score >= 82
- cannibalization risk <= 0.65
- quality score >= 90
- fact-check passes
- unsupported material factual claims = 0
- source/primary-source requirements pass
- slug matches the safe filename pattern
- body contains enough structured content to render
- meta description and keyword fields pass the publisher/build checks

The website build independently validates every `*.article.json` file again. A malformed article fails the Vercel/GitHub build rather than reaching production.

If no candidate meets the threshold, the correct behavior is to publish nothing.
