// Dispatch plan contract test for 00 - GrowthOS Orchestrator.
// Runs the ACTUAL "Build Dispatch Plan" jsCode from n8n/00-growthos-orchestrator.json
// against synthetic due-agent rows and pins the fail-closed dispatch contracts:
//   autonomy gate (green/yellow/red/unknown), dispatch-map sync, deterministic
//   run_key idempotency windows, and no silent drops (every input yields a decision).
// No network, no Supabase, no Execute Workflow calls - logic contract only.
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const wf = JSON.parse(fs.readFileSync(path.join(ROOT, "n8n/00-growthos-orchestrator.json"), "utf8"));
const node = wf.nodes.find((n) => n.name === "Build Dispatch Plan");
assert.ok(node, "00 must contain a Build Dispatch Plan node");
const code = node.parameters.jsCode;

// 1. Embedded DISPATCH_MAP stays byte-equal to config/dispatch-map.json's map.
const m = code.match(/\/\/ DISPATCH_MAP_START[^\n]*\nconst DISPATCH_MAP = ([\s\S]*?);\n\/\/ DISPATCH_MAP_END/);
assert.ok(m, "DISPATCH_MAP markers missing from jsCode");
const embedded = JSON.parse(m[1]);
const onDisk = JSON.parse(fs.readFileSync(path.join(ROOT, "config/dispatch-map.json"), "utf8")).map;
assert.deepStrictEqual(embedded, onDisk, "embedded DISPATCH_MAP drifted from config/dispatch-map.json");

// 2. Registry coverage: every registry slug is mapped, and every mapped slug
//    resolves to a parseable workflow file.
const registry = JSON.parse(fs.readFileSync(path.join(ROOT, "config/agent-registry.json"), "utf8"));
const agents = Array.isArray(registry.agents) ? registry.agents : registry;
for (const a of agents) {
  assert.ok(onDisk[a.slug], `registry slug '${a.slug}' missing from dispatch map`);
  JSON.parse(fs.readFileSync(path.join(ROOT, onDisk[a.slug].workflow_file), "utf8"));
}

function runPlan(rows) {
  const fn = new Function("items", code);
  return fn([{ json: rows }]).map((r) => r.json);
}

const AT = "2026-11-13T23:30:00.000Z"; // Friday
const fixtures = [
  { slug: "seo-intelligence", name: "SEO Intelligence", autonomy: "green", schedule: "daily", dispatch_requested_at: AT },
  { slug: "growth-director", name: "Growth Director", autonomy: "yellow", schedule: "daily", dispatch_requested_at: AT },
  { slug: "lead-intent", name: "Lead Intent", autonomy: "red", schedule: "hourly", dispatch_requested_at: AT },
  { slug: "ghost-agent", name: "Ghost", autonomy: "green", schedule: "daily", dispatch_requested_at: AT },
  { slug: "content-research", name: "Content Research", schedule: "weekly", dispatch_requested_at: AT }, // no autonomy -> fail closed
  { slug: "technical-seo", name: "Technical SEO", autonomy: "green", schedule: "weekly", dispatch_requested_at: AT },
];
const out = runPlan(fixtures);
const bySlug = Object.fromEntries(out.map((r) => [r.slug, r]));

// 3. Fail closed, never silent: one decision per input row.
assert.strictEqual(out.length, fixtures.length, "every input row must yield exactly one decision");

// 4. Autonomy gate: with nothing imported yet, even green is BLOCKED
//    (workflow_not_imported) - dispatch can never fire before import.
assert.deepStrictEqual(
  out.map((r) => [r.slug, r.decision, r.reason]),
  [
    ["seo-intelligence", "BLOCKED", "workflow_not_imported"],
    ["growth-director", "APPROVAL_REQUIRED", "autonomy_yellow"],
    ["lead-intent", "BLOCKED", "manual_only"],
    ["ghost-agent", "BLOCKED", "unmapped_slug"],
    ["content-research", "BLOCKED", "unknown_autonomy"],
    ["technical-seo", "BLOCKED", "workflow_not_imported"],
  ],
  "decision matrix mismatch"
);
assert.ok(bySlug["growth-director"].approval_route, "APPROVAL_REQUIRED rows carry an approval route marker");

// 5. Deterministic run_key idempotency windows.
assert.strictEqual(bySlug["seo-intelligence"].run_key, "seo-intelligence:daily:2026-11-13");
assert.strictEqual(bySlug["lead-intent"].run_key, "lead-intent:hourly:2026-11-13T23");
assert.ok(/^\d{4}-W\d{2}$/.test(bySlug["technical-seo"].dispatch_window), "weekly window must be ISO week");
assert.deepStrictEqual(runPlan(fixtures).map((r) => r.run_key), out.map((r) => r.run_key),
  "run_key must be deterministic across runs in the same window");
const nextDay = runPlan([{ ...fixtures[0], dispatch_requested_at: "2026-11-14T00:30:00.000Z" }]);
assert.notStrictEqual(nextDay[0].run_key, bySlug["seo-intelligence"].run_key, "daily window must roll at midnight UTC");
const nextHour = runPlan([{ ...fixtures[2], dispatch_requested_at: "2026-11-14T00:05:00.000Z" }]);
assert.notStrictEqual(nextHour[0].run_key, bySlug["lead-intent"].run_key, "hourly window must roll each hour");

// 6. ISO week correctness on known dates: 2026-11-13 is ISO week 46;
//    2026-01-01 belongs to ISO week 2026-W01.
const w = runPlan([{ slug: "seo-intelligence", autonomy: "yellow", schedule: "weekly", dispatch_requested_at: "2026-01-01T12:00:00.000Z" }]);
assert.strictEqual(w[0].dispatch_window, "2026-W01", "ISO week of 2026-01-01");
const w46 = runPlan([{ slug: "seo-intelligence", autonomy: "yellow", schedule: "weekly", dispatch_requested_at: AT }]);
assert.strictEqual(w46[0].dispatch_window, "2026-W46", "ISO week of 2026-11-13");

console.log("dispatch-plan: all assertions passed");
