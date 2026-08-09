# n8n Workflow Registry

Create these workflows in n8n:

00 - GrowthOS Orchestrator
01 - SEO Intelligence
02 - Search Opportunity
03 - Content Research
04 - Content Production
05 - Internal Linking
06 - Technical SEO
07 - Citation Engine
08 - Backlink Intelligence
09 - Founder Content
10 - Social Distribution
11 - CRO Intelligence
12 - Competitor Intelligence
13 - Reputation Intelligence
14 - Lead Intent
15 - Growth Director
99 - Error Handler

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

No agent workflow should write to external systems without checking autonomy/approval state.
