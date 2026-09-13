# Mopshy GrowthOS

Mopshy's internal AI-powered growth operating system.

## Mission
Continuously improve Mopshy's visibility, authority, qualified pipeline, and revenue through a coordinated network of specialized AI agents with explicit approval gates.

## Architecture
- n8n: orchestration and deterministic execution
- Supabase/Postgres: shared memory and system of record
- OpenAI: reasoning and structured recommendations
- Google Search Console + GA4: organic and traffic intelligence
- HubSpot: leads and CRM
- Telegram: command center and approvals
- GitHub / mopshy.com: website execution layer

## Agents
01 SEO Intelligence
02 Search Opportunity
03 Content Research
04 Content Production
05 Internal Linking
06 Technical SEO
07 Citation Engine
08 Backlink Intelligence
09 Founder Content
10 Social Distribution
11 CRO Intelligence
12 Competitor Intelligence
13 Reputation Intelligence
14 Lead Intent
15 Growth Director
16 Content Performance

All 16 agents have n8n workflows in `n8n/` (see `docs/N8N_WORKFLOWS.md` for the registry, schedules, and credentials).

## Principles
1. Evidence before action.
2. Human approval for consequential writes.
3. Real metrics only.
4. No spam SEO, fake reviews, or manipulative backlinks.
5. Every agent run is logged and measurable.
6. Shared database, separate agent responsibilities.
7. Outreach remains a separate system and integrates through shared company/lead records.

## Build order
1. Database + task queue + approvals
2. Orchestrator + logging + error handling
3. SEO/Search/Technical/Competitor intelligence
4. Content/Internal linking/Founder/Social
5. Citations/Backlinks/Reputation
6. CRO/Lead Intent/HubSpot
7. Growth Director + autonomy scoring
