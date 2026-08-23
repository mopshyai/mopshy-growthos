# Mopshy Autonomous Content Engine — n8n Cloud Activation

## Architecture

n8n Cloud runs the agents. Supabase stores state and content data. GitHub is the guarded publishing target. Vercel deploys mopshy.com after approved website changes merge.

## Required n8n credentials

Create/select these credentials inside the `MOPSHY GROWTHOS` n8n Cloud project:

1. **Mopshy OpenAI** — OpenAI API credential using Mopshy's own OpenAI API key. Do not rely on n8n free OpenAI credits for this production workflow.
2. **Supabase account** — existing Supabase API credential.
3. **Mopshy Content Publisher** — GitHub API credential using the fine-grained token scoped to `mopshyai/mopshy-ai-growth-engine` with Contents read/write and Pull requests read/write.

The content workflows use the model `gpt-5.6-sol` directly. No `OPENAI_CONTENT_MODEL` or `OPENAI_QA_MODEL` variables are required.

## Step 1 — Apply the Supabase migration

In the Supabase project connected to GrowthOS, open SQL Editor and run:

`supabase/migrations/20260823_autonomous_content_engine.sql`

This creates:

- `content_opportunities`
- `content_drafts`
- `content_performance_snapshots`

The migration is idempotent (`create table if not exists`).

## Step 2 — Import workflows into MOPSHY GROWTHOS

Import these three JSON workflows from this repository branch:

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
- `Fetch Article Registry`
- `Create Article Branch`
- `Commit Article Only`
- `Open Review PR`

## Step 4 — Test in this order

Do not publish all three workflows immediately.

1. Leave all three inactive.
2. Manually execute **02** first.
3. Confirm rows appear in `content_opportunities`.
4. Manually execute **03**.
5. Confirm one `content_drafts` row is created and inspect its `qa_report`.
6. Only if the draft is `ready`, manually execute **04**.
7. Confirm it opens a PR in `mopshyai/mopshy-ai-growth-engine` and does not merge it.
8. Review the website build/CI result.

## Step 5 — Activate schedules

After the manual end-to-end test passes, publish/activate in this order:

- **02** — daily 6:30 AM America/Denver
- **03** — daily 7:15 AM America/Denver
- **04** — daily 8:00 AM America/Denver

Auto-merge remains disabled. The publisher only creates a review PR after the quality gates pass.

## Safety gates

A new article can reach publishing only when:

- opportunity score >= 82
- cannibalization risk <= 0.65
- quality score >= 90
- fact-check passes
- unsupported material factual claims = 0
- source/primary-source requirements pass

If no candidate meets the threshold, the correct behavior is to publish nothing.
