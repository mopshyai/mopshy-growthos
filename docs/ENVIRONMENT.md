# Environment Variables

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
N8N_BASE_URL=
N8N_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GSC_SITE_URL=https://mopshy.com/
GA4_PROPERTY_ID=
HUBSPOT_PRIVATE_APP_TOKEN=
GITHUB_REPO_MOPSHY_SITE=mopshyai/mopshy-ai-growth-engine
OUTREACH_API_BASE_URL=
OUTREACH_SHARED_SECRET=

Never commit live secrets.

## Notes

- `GSC_SITE_URL` must match the property exactly as registered in Google
  Search Console, including protocol and trailing slash. It is used both for
  the GSC API path (URL-encoded) and as the sitemap base URL.
- `GA4_PROPERTY_ID` is the numeric GA4 property ID. When empty, workflows 01
  and 05 skip GA4 enrichment and use Search Console data only.
- Google data access (Search Console, GA4) goes through a Google OAuth2
  credential in n8n with the scopes `webmasters.readonly` and
  `analytics.readonly`; `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` back that
  credential.
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` are used by every workflow via
  `$env` — no per-workflow Supabase credentials are needed.
