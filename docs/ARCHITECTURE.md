# Architecture

## System boundary
GrowthOS owns inbound growth intelligence, organic visibility, content, technical SEO, authority, conversion, reputation, and lead intent.

`mopshy-outreach` remains a separate system that owns prospecting, enrichment, personalized outbound, campaign execution, reply handling, and outbound analytics.

Both systems share company and lead identifiers through Supabase.

## Event model
Agents never directly command other agents. They create tasks or system events. The orchestrator and Growth Director decide what runs next.

## Approval model
- GREEN: read/analyze/log/score/generate drafts automatically.
- YELLOW: prepare action, create approval, wait for explicit decision.
- RED: prohibited from autonomous execution.

## Core flow
Data source -> agent -> structured finding -> task -> approval (if required) -> executor -> result -> metrics -> Growth Director.

## Outreach integration
GrowthOS may push a qualified company/opportunity into Outreach. Outreach writes replies, meetings, campaign outcomes, and attributed results back to shared records.
