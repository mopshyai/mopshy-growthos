# GrowthOS Production Activation

This runbook turns the existing 16-agent GrowthOS fleet into a controlled 24x7 production system for mopshy.com.

## Production principle

Do not add more agents during activation. Reliability, observability, idempotency, safety, and measurable business output come first.

## Safety state

The orchestrator is fail-closed through `GROWTHOS_PAUSED`.

- `GROWTHOS_PAUSED=true` or missing: orchestrator dispatch is blocked.
- `GROWTHOS_PAUSED=false`: orchestrator may continue to due-agent selection and dispatch.

Keep the system paused until the manual canary tests in this document pass.

## Phase 1 - Import, but keep inactive

Import these workflows into the n8n Cloud project `MOPSHY GROWTHOS`:

- `00-growthos-orchestrator.json`
- `01-seo-intelligence.json` through `17-growth-director.json`
- `99-error-handler.json`

Do not enable schedules yet.

Attach credentials/environment:

- Supabase service role (server-only)
- OpenAI
- GitHub with contents + pull-request access to `mopshyai/mopshy-ai-growth-engine`
- Telegram
- Google OAuth2 with Search Console + Analytics readonly scopes
- HubSpot only when Lead Intent is ready

## Phase 2 - Finish the control plane

Before scheduled production runs:

1. Wire the actual n8n workflow IDs into workflow 00 dispatch.
2. Give workflow 00 its own run lifecycle record.
3. Upgrade workflow 99 so a failure:
   - identifies the failing agent,
   - marks the corresponding `agent_runs` row failed,
   - writes `completed_at` and the error,
   - increments `agents.error_count`,
   - writes a `system_events` row,
   - sends a concise Telegram alert.
4. Add stale-run detection. A run left `running` beyond its allowed runtime must become failed/stalled and generate a P1 event.
5. Verify every retry-sensitive write has a deterministic dedupe/idempotency rule.

## Phase 3 - Manual intelligence canary

Run these manually while schedules stay disabled:

1. 01 SEO Intelligence
2. 07 Internal Linking
3. 08 Technical SEO
4. 14 Competitor Intelligence
5. 15 Reputation Intelligence

For every workflow verify:

- one `agent_runs` row is created,
- state moves `running -> completed`,
- `agents.last_run_at` updates,
- expected destination records are written,
- a second identical execution does not create duplicates,
- a forced failure reaches workflow 99 and Telegram.

Require three clean runs per agent before enabling its schedule.

## Phase 4 - Content flywheel

Prove the complete chain manually:

`02 Search Opportunity -> 06 Content Research -> 03 Writer + QA -> 04 GitHub Publisher -> Vercel preview -> human merge -> 05 Content Performance`

Publishing rules remain strict:

- one isolated article PR,
- no direct pushes to `main`,
- no auto-merge,
- human approval before production,
- failed QA never reaches publishing,
- retried publishing never creates duplicate PRs.

## Phase 5 - Commercial agents

After content succeeds end-to-end, activate:

- 09 Citation Engine
- 10 Backlink Intelligence
- 11 Founder Content
- 12 Social Distribution
- 13 CRO Intelligence
- 16 Lead Intent

Consequential yellow-agent actions stay approval-gated.

## Phase 6 - Growth Director

Upgrade 17 from a simple rule-based summary to a deterministic decision queue.

Every open recommendation should be rankable by:

- urgency / priority,
- confidence,
- expected impact,
- revenue relevance,
- age/freshness,
- effort when present,
- whether approval is required.

The daily brief should surface a small actionable queue, not dump every alert.

## Phase 7 - Orchestrator last

Only after the individual schedules are proven:

1. test the 00 dispatcher manually,
2. verify each slug resolves to exactly one imported workflow ID,
3. verify paused mode stops all dispatch,
4. verify unknown slugs fail safely,
5. activate 00 last,
6. set `GROWTHOS_PAUSED=false` only after the control-plane checks pass.

## Monitoring requirements

Track at minimum:

- expected vs actual executions,
- completion rate,
- failed runs,
- stale running runs,
- median/p95 run duration,
- model/API cost,
- tasks produced,
- content opportunities/drafts/PRs/published items,
- website/Vercel production health,
- qualified leads and pipeline when CRM data is connected.

Telegram should alert immediately for P0/P1 events; successful routine runs should not create notification noise.

## 24x7 production exit criteria

Do not call GrowthOS production-ready until:

- >=99% of expected scheduled executions occur during the soak period,
- no stale running execution survives beyond its timeout,
- every failure is persisted and alerted,
- retries are idempotent,
- the global pause switch has been tested,
- the full content flywheel has completed multiple successful cycles,
- publishing remains PR-only/human-approved,
- the Growth Director brief arrives reliably,
- cost/retry limits are enforced,
- website production health remains green,
- at least one complete weekly cycle has run successfully.

## Master tracker

GitHub issue #5 tracks this activation milestone.
