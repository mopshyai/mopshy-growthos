// Dispatcher contract test for 00 - GrowthOS Orchestrator.
// The orchestrator dispatches by slug against rows returned from the live
// `agents` table (status = 'active'). This test pins the contract between
// config/agent-registry.json and a supplied set of DB slugs:
//   - every ACTIVE DB row must resolve to a registry entry + parseable workflow file
//   - registry slugs with no active DB row are REPORTED, never dispatched
//   - the current known live gap is exactly ['content-publisher'] until the
//     owner applies scripts/seed_agent_publisher.sql (row inserted as
//     status='inactive', so even then it stays non-dispatchable until the
//     owner flips status after verifying the handoff)
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const registry = JSON.parse(fs.readFileSync(path.join(ROOT, "config/agent-registry.json"), "utf8"));
const agents = Array.isArray(registry.agents) ? registry.agents : registry;

// Live agents-table slugs, verified read-only 2026-11-13 (16 rows, all active).
const LIVE_ACTIVE_SLUGS = [
  "backlink-intelligence", "citation-engine", "competitor-intelligence",
  "content-performance", "content-production", "content-research",
  "cro-intelligence", "founder-content", "growth-director",
  "internal-linking", "lead-intent", "reputation-intelligence",
  "search-opportunity", "seo-intelligence", "social-distribution",
  "technical-seo",
];

const registryBySlug = new Map(agents.map((a) => [a.slug, a]));

// 1. Registry slugs are unique (dispatch-by-slug must address exactly one agent).
const seen = new Set();
for (const a of agents) {
  assert.ok(!seen.has(a.slug), `duplicate registry slug: ${a.slug}`);
  seen.add(a.slug);
}

// 2. Every live ACTIVE row resolves to a registry entry whose workflow file parses.
for (const slug of LIVE_ACTIVE_SLUGS) {
  const entry = registryBySlug.get(slug);
  assert.ok(entry, `live DB slug '${slug}' has no registry entry`);
  const wf = JSON.parse(fs.readFileSync(path.join(ROOT, entry.workflow_file), "utf8"));
  assert.ok(Array.isArray(wf.nodes) && wf.nodes.length > 0, `${entry.workflow_file} not parseable`);
}

// 3. Registry slugs with no active DB row: reported, never dispatched. The only
// tolerated gap today is content-publisher (pending owner-applied seed).
const missing = agents.map((a) => a.slug).filter((s) => !LIVE_ACTIVE_SLUGS.includes(s));
assert.deepStrictEqual(missing, ["content-publisher"],
  `registry slugs without an active DB row changed: ${JSON.stringify(missing)}`);

// 4. A publisher row inserted with status='inactive' must NOT become
// dispatchable: the orchestrator query filters status=eq.active. Pin the
// filter's existence in the converted 00 workflow.
const wf00 = JSON.parse(fs.readFileSync(path.join(ROOT, "n8n/00-growthos-orchestrator.json"), "utf8"));
const getAgents = wf00.nodes.find((n) => n.name === "Get Active Agents");
assert.ok(getAgents.parameters.url.includes("status=eq.active"),
  "00 must keep the status=eq.active dispatch filter");

console.log("dispatch-contract: all assertions passed");
console.log("registry slugs:", agents.length, "| live active:", LIVE_ACTIVE_SLUGS.length, "| known gap:", missing.join(","));
