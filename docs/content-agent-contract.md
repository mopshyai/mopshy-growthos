# Mopshy Autonomous Content Engine — Agent Contract

## Mission
Grow qualified organic discovery for Mopshy across traditional search and AI-assisted search without becoming a scaled-content farm.

The system researches every day. Publishing is conditional, not mandatory.

## Pipeline

1. Trend Scout
2. Opportunity Scorer
3. Researcher
4. Cannibalization / Refresh Decider
5. Mopshy POV Builder
6. Writer
7. Fact Checker
8. SEO + AEO Reviewer
9. Publisher
10. Performance / Refresh Agent

## 1. Trend Scout

Inputs:
- Fresh web/news/product announcements
- Google Search Console query data when connected
- Existing Mopshy article inventory
- Priority commercial topics in `config/content-engine.json`

Output: 10–30 candidates per run.

Each candidate must include:
- topic
- why now
- likely query/user question
- entities
- freshness signal
- commercial relationship to Mopshy
- 2+ candidate source URLs

Do not select a topic solely because it is popular.

## 2. Opportunity Scorer

Score each candidate 0–100 using the configured weights.

Hard rejects:
- unrelated to AI, automation, product/ops workflows, sales systems, or Mopshy buyers
- no credible source path
- obvious duplicate of an existing Mopshy article
- gossip/rumor without primary confirmation
- topic requires unsupported prediction presented as fact

Recommended action:
- 82–100: publish candidate
- 70–81: research further
- 50–69: backlog
- <50: ignore

A high cannibalization risk can override the score and convert `publish` into `refresh`.

## 3. Researcher

Research before writing.

Source hierarchy:
1. Primary source: vendor documentation, release notes, standards body, official company announcement, filing, original research paper/data.
2. High-quality secondary reporting.
3. Practitioner/community sources only for experience, sentiment, or examples.

Rules:
- At least 3 useful sources for a publishable article.
- At least 1 primary source for changing product/news/policy claims.
- Record URL, publisher, title, publication date, access date, and the exact claim(s) it supports.
- If a key claim cannot be verified, remove it.

## 4. Cannibalization / Refresh Decider

Compare the target query and angle with existing Mopshy content.

Prefer refreshing an existing page when:
- search intent is substantially the same
- the old page already has backlinks/impressions
- the new event changes an existing guide more than it creates a new intent

Create a new page when:
- user intent is distinct
- the topic represents a genuinely new entity/problem/workflow
- a separate URL improves information architecture

## 5. Mopshy POV Builder

Every published piece needs at least one non-commodity contribution:
- implementation architecture
- workflow pattern
- decision framework
- original calculation
- trade-off analysis
- teardown
- experiment/test
- checklist
- failure mode analysis
- practical SMB/enterprise application

A summary of sources is not enough.

## 6. Writer

Required fields:
- slug
- category
- title
- excerpt
- read time
- published date
- meta title
- meta description
- keywords
- body blocks
- FAQs when useful
- source block
- internal links

Writing requirements:
- Answer the primary user question immediately.
- Use descriptive H2/H3s.
- Keep paragraphs information-dense.
- Explain consequences and implementation, not only announcements.
- Avoid filler introductions, generic AI hype, and keyword repetition.
- Never invent customer numbers, benchmarks, statistics, pricing, quotations, product capabilities, or dates.

## 7. Fact Checker

The fact checker is independent of the writer.

It returns:
- quality score 0–100
- unsupported claims with exact text
- outdated claims
- contradictory claims
- source-quality issues
- missing primary-source evidence
- suggested corrections
- PASS / BLOCK

Automatic BLOCK when:
- unsupported_claim_count > 0 for material factual claims
- primary source is required but absent
- headline overstates the evidence
- article contains fabricated first-hand experience or customer outcomes

Minimum quality score: 90.

## 8. SEO + AEO Reviewer

Check:
- primary intent is obvious
- title/meta are specific and non-clickbait
- canonical URL is deterministic
- article is internally linked
- relevant service/commercial page is linked naturally
- entities are named explicitly
- source links are visible
- answer-first structure
- Article/Breadcrumb structured-data compatibility
- no near-duplicate page targeting
- image alt text when a custom image exists

Do not add unsupported FAQ answers or schema content merely to increase markup.

## 9. Publisher

Default publishing mode is `pull_request`.

Publisher may touch only:
- approved content files
- approved blog assets
- generated content index/registry files when required
- `llms.txt` only when its curated article list needs updating

Publisher must never change application/auth/payment/security code.

Before PR creation:
- validate article shape
- verify unique slug
- run build/typecheck in CI
- record sources and QA report in GrowthOS

Production auto-merge remains disabled until the pipeline has a proven clean run history.

## 10. Performance / Refresh Agent

Capture 7-, 14-, and 30-day snapshots when Search Console/analytics are connected.

Signals:
- impressions
- clicks
- CTR
- average position
- organic sessions
- conversions
- ChatGPT/AI referral sessions when identifiable

Actions:
- rising: leave alone and strengthen related cluster
- impressions up + CTR weak: title/meta test
- position falling: refresh evidence/depth/internal links
- outdated source/product details: refresh immediately
- overlapping pages: recommend merge/consolidation

## Safety principle
Autonomy applies to execution, not truth.

The system may research and draft freely, but it must earn publication through evidence, originality, relevance, and QA.
