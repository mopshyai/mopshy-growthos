insert into agents (name, slug, description, autonomy, schedule)
values
('SEO Intelligence','seo-intelligence','Find organic search opportunities and anomalies','green','daily'),
('Search Opportunity','search-opportunity','Turn demand signals into prioritized keyword/page opportunities','green','daily'),
('Content Research','content-research','Build evidence-backed research packets','green','daily'),
('Content Production','content-production','Create content drafts from approved research','yellow','on-demand'),
('Internal Linking','internal-linking','Improve internal linking and find orphan/broken paths','yellow','daily'),
('Technical SEO','technical-seo','Detect technical search/indexing issues','yellow','daily'),
('Citation Engine','citation-engine','Discover, prepare, submit, and monitor business citations','yellow','daily'),
('Backlink Intelligence','backlink-intelligence','Discover legitimate backlink opportunities','green','weekly'),
('Founder Content','founder-content','Turn real Mopshy work into founder-led content drafts','yellow','daily'),
('Social Distribution','social-distribution','Adapt and distribute approved content','yellow','daily'),
('CRO Intelligence','cro-intelligence','Analyze funnel behavior and propose experiments','yellow','daily'),
('Competitor Intelligence','competitor-intelligence','Track competitor changes and strategic gaps','green','daily'),
('Reputation Intelligence','reputation-intelligence','Track brand mentions, reviews, and response needs','green','hourly'),
('Lead Intent','lead-intent','Score buying intent and enrich qualified accounts','green','hourly'),
('Growth Director','growth-director','Prioritize work across GrowthOS toward pipeline and authority','green','daily')
on conflict (slug) do nothing;
