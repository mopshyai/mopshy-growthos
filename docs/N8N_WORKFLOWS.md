# n8n Workflow Registry

All 16 registered agents have workflows in `n8n/` (import into the `MOPSHY GROWTHOS` n8n Cloud project). Schedules run in `America/New_York` (Eastern) and are staggered so crawl and OpenAI usage never collide.

Infrastructure workflows:
- **00 Orchestrator** — fail-closed (`GROWTHOS_PAUSED`); dispatches due agents through an Execute Workflow node whose workflow ID resolves at runtime from `agents.n8n_workflow_id` (wired post-import). Due agents without a wired ID are reported in a `system_events` row instead of silently disappearing.
- **98 Stale Run Watchdog** — every 15 minutes, marks `agent_runs` stuck in `running` beyond `GROWTHOS_RUN_TIMEOUT_MINUTES` (default 45) as failed with an explicit timeout error, bumps agent error counts, writes a P1 `system_events` row, and sends one concise Telegram summary. Idempotent: a run marked failed leaves the `running` set and can never be reprocessed.
- **99 Error Handler** — on any workflow failure: normalizes the error, resolves the failing agent via exact `agents.n8n_workflow_name` lookup (never free-text matching), marks only the newest `running` run of that agent failed within a 6-hour recency boundary, bumps `agents.error_count`, writes a structured `system_events` row, and sends one Telegram alert. Unmapped workflows still log and alert without crashing the handler. Every Supabase call in 99 is failure-tolerant.

Every agent workflow also carries an `Execute Workflow Trigger` so the orchestrator can invoke it; manual and schedule triggers are unaffected. Validate the repo anytime with `npm run validate:growthos`.

| File | Workflow | Agent (slug) | Autonomy | Schedule |
|------|----------|--------------|----------|----------|
| `00-growthos-orchestrator.json` | GrowthOS Orchestrator | — | — | every 15 min |
| `01-seo-intelligence.json` | SEO Intelligence v3 | `seo-intelligence` | green | daily 5:30 AM ET |
| `02-content-opportunity-agent.json` | Autonomous Content Opportunity Agent | `search-opportunity` | green | daily 6:30 AM ET |
| `03-content-writer-qa-agent.json` | Autonomous Content Writer + QA | `content-production` | yellow | daily 7:15 AM ET |
| `04-content-github-publisher.json` | Guarded GitHub Blog Publisher | `content-production` | yellow | daily 8:00 AM ET |
| `05-content-performance-agent.json` | Content Performance Agent | `content-performance` | green | daily 8:30 AM ET |
| `06-content-research.json` | Content Research Agent | `content-research` | green | daily 7:00 AM ET |
| `07-internal-linking.json` | Internal Linking Agent | `internal-linking` | yellow | daily 5:45 AM ET |
| `08-technical-seo.json` | Technical SEO Agent | `technical-seo` | yellow | daily 6:15 AM ET |
| `09-citation-engine.json` | Citation Engine Agent | `citation-engine` | yellow | daily 6:45 AM ET |
| `10-backlink-intelligence.json` | Backlink Intelligence Agent | `backlink-intelligence` | green | weekly Sun 7:30 AM ET |
| `11-founder-content.json` | Founder Content Agent | `founder-content` | yellow | daily 9:00 AM ET |
| `12-social-distribution.json` | Social Distribution Agent | `social-distribution` | yellow | daily 9:30 AM ET |
| `13-cro-intelligence.json` | CRO Intelligence Agent | `cro-intelligence` | yellow | daily 10:00 AM ET |
| `14-competitor-intelligence.json` | Competitor Intelligence Agent | `competitor-intelligence` | green | daily 4:30 PM ET |
| `15-reputation-intelligence.json` | Reputation Intelligence Agent | `reputation-intelligence` | green | hourly |
| `16-lead-intent.json` | Lead Intent Agent | `lead-intent` | green | hourly at :15 |
| `17-growth-director.json` | Growth Director Agent | `growth-director` | green | daily 7:30 AM ET |
| `98-stale-run-watchdog.json` | Stale Run Watchdog | — | — | every 15 min |
| `99-error-handler.json` | GrowthOS Error Handler | — | — | on error |

## What each agent does

- **01 SEO Intelligence** — GSC (queries/pages/query+page, current + previous 28d), optional GA4, sitemap crawl. Deterministic scoring → `keywords`/`pages` upserts + daily SEO task list (CTR opportunities, striking distance, declining pages, emerging queries, cannibalization, zero-visibility pages).
- **02 Content Opportunity** — OpenAI web-search trend scouting and scoring into `content_opportunities`, deduped against existing topics/keywords.
- **03 Content Writer + QA** — drafts from the best `publish` candidate, independent fact check + QA, evidence-gated (`content_drafts`).
- **04 GitHub Publisher** — publishes one isolated `*.article.json` file on a review PR in `mopshyai/mopshy-ai-growth-engine`; auto-merge disabled.
- **05 Content Performance** — reconciles publishing PRs (merged → `published`), captures 7/14/30-day GSC + GA4 + AI-referral snapshots per article.
- **06 Content Research** — builds evidence-backed research packets for `research` candidates; approves (→ writer queue) or downgrades to `backlog`.
- **07 Internal Linking** — crawls sitemap sample (25 pages/run, rotating), builds the internal link graph, flags orphans, weakly linked and unreachable pages.
- **08 Technical SEO** — audits a rotating 20-page sample: status codes, noindex, title/meta lengths, canonical, h1; writes `pages` status.
- **09 Citation Engine** — tracks 13 seeded citation directories in `growth_citations` (NOT the Studio-owned `citations` table), opens pending citations, creates approval tasks for submissions (never auto-submits). Insert is an `on_conflict` upsert (retry-safe).
- **10 Backlink Intelligence** — weekly web-search hunt for unlinked mentions and resource/directory/guest-post pages into `backlink_opportunities`; outreach stays external.
- **11 Founder Content** — turns real evidence (website repo commits + published articles from the last 7 days) into 3 founder-post drafts in `content_assets`; approval-gated.
- **12 Social Distribution** — adapts recently published articles into LinkedIn/X/newsletter drafts; approval-gated, deduped per article.
- **13 CRO Intelligence** — GA4 landing-page and device analysis; proposes conversion experiments into `experiments` + approval tasks.
- **14 Competitor Intelligence** — scans the competitor watchlist (seeded in `20260912_agent_fleet.sql`) for 14-day changes; logs `competitor_events`.
- **15 Reputation Intelligence** — hourly web search for mentions/reviews of Mopshy into `mentions`; P1 tasks for negative or response-required mentions.
- **16 Lead Intent** — scores recent HubSpot contacts (stage + recency model) into `leads.intent_score`; P1 tasks for hot (>=70) leads. Skips gracefully without `HUBSPOT_PRIVATE_APP_TOKEN`.
- **17 Growth Director** — aggregates open tasks, 24h run health, and stale agents into `daily_briefs` and sends the daily brief to Telegram.

## Contract for every agent workflow
Input:
- run_id
- agent_slug
- trigger
- context

Output:
- status
- findings[]
- tasks[]
- metrics[]
- errors[]

No agent workflow should write to external systems without checking autonomy/approval state. Yellow agents never execute consequential writes — they create approval-gated tasks (`requires_approval: true`).

## Conventions

- **Supabase access:** every workflow calls the REST API with `$env.SUPABASE_URL` +
  `$env.SUPABASE_SERVICE_ROLE_KEY` (apikey + Authorization headers). No hardcoded project URLs, no per-workflow Supabase credentials.
- **Run lifecycle:** every agent looks up its `agents` row by slug, creates an
  `agent_runs` row, completes it with an output summary, and updates
  `agents.last_run_at`. Every recommendation becomes a `tasks` record, deduped against open tasks of the same type.
- **OpenAI:** `gpt-5.6-sol` via the Mopshy OpenAI credential (02, 03, 06, 10, 11, 12, 14, 15).
- **Google OAuth2** (`webmasters.readonly`, `analytics.readonly`): 01, 05, 13; GSC sitemap fetches in 07/08 need no credential.
- **GitHub** (`mopshyai/mopshy-ai-growth-engine`, Contents + PR read/write): 04, 05, 11.
- **Telegram:** 17 (daily brief), 99 (failure alerts). `TELEGRAM_CHAT_ID` env var.
- **Optional integrations:** GA4 skips gracefully without `GA4_PROPERTY_ID` (01, 05, 13); HubSpot skips gracefully without `HUBSPOT_PRIVATE_APP_TOKEN` (16).
- **Cost note:** 15 (reputation) runs hourly with one web-search call per run; lower the cron if usage matters.
