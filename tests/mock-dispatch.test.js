// Offline mocked dispatch test for 00 - GrowthOS Orchestrator.
// Runs the ACTUAL "Filter Due Agents" jsCode from n8n/00-growthos-orchestrator.json
// against synthetic agent rows, then verifies a slug -> workflow_file dispatch
// mapping built from config/agent-registry.json. No network, no Supabase, no
// Execute Workflow calls - this proves mapping/filter logic only, not runtime.
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const orchestrator = JSON.parse(fs.readFileSync(path.join(ROOT, "n8n/00-growthos-orchestrator.json"), "utf8"));
const registry = JSON.parse(fs.readFileSync(path.join(ROOT, "config/agent-registry.json"), "utf8"));
const agents = Array.isArray(registry.agents) ? registry.agents : registry;

function runFilterDue(items) {
  const code = orchestrator.nodes.find((n) => n.name === "Filter Due Agents").parameters.jsCode;
  const fn = new Function("items", code);
  return fn(items);
}

// --- 1. due-schedule logic against synthetic rows (runs the ACTUAL jsCode
// from n8n/00-growthos-orchestrator.json; schedule precedence repaired 2026-11-13) ---
const now = Date.now();
const ago = (min) => new Date(now - min * 60000).toISOString();
const synthetic = [
  { slug: "next-run-past", schedule: "daily", next_run_at: ago(5) },            // due via next_run_at
  { slug: "next-run-future", schedule: "daily", next_run_at: new Date(now + 3600e3).toISOString() }, // not due
  { slug: "next-run-invalid", schedule: "daily", next_run_at: "not-a-date" },   // invalid -> not due, flagged
  { slug: "hourly-stale", schedule: "hourly", last_run_at: ago(61) },            // due
  { slug: "hourly-fresh", schedule: "hourly", last_run_at: ago(30) },            // not due
  { slug: "weekly-stale", schedule: "weekly", last_run_at: ago(10081) },         // due
  { slug: "never-ran-daily", schedule: "daily" },                                // due once (bootstrap)
  { slug: "never-ran-on-demand", schedule: "on-demand" },                        // REGRESSION: pre-repair this was due; must NOT be due
  { slug: "never-ran-unknown", schedule: "fortnightly" },                        // REGRESSION: unknown schedule must NOT be due
  { slug: "on-demand-ran", schedule: "on-demand", last_run_at: ago(5) },         // never auto-due
  { slug: "on-demand-explicit-next", schedule: "on-demand", next_run_at: ago(5) }, // INTENTIONAL: a valid past next_run_at is an explicit override -> due even for on-demand
  { slug: "last-run-invalid", schedule: "daily", last_run_at: "yesterday-ish" }, // invalid -> not due, flagged
];
const out1 = runFilterDue([{ json: synthetic }]).map((r) => r.json);
const due = out1.map((r) => r.slug).sort();
assert.deepStrictEqual(due, ["hourly-stale", "never-ran-daily", "next-run-past", "weekly-stale", "on-demand-explicit-next"].sort(),
  "due filter: next_run_at past/stale/bootstrap due; future/invalid/on-demand/unknown excluded. Got: " + due.join(","));
// flag assertions for invalid inputs
const invalidNext = runFilterDue([{ json: synthetic }]);
assert.ok(invalidNext.length === due.length, "flag check uses same output");
const flaggedSrc = synthetic; // flags are set pre-filter; verify via direct map call
// verify flags directly against the mapper (due() is internal; re-run through filter path)
const full = (() => {
  const code = orchestrator.nodes.find((n) => n.name === "Filter Due Agents").parameters.jsCode;
  const fn = new Function("items", code.replace("return rows.map(due).filter(r => r._due).map(({ _due, ...rest }) => ({ json: rest }));",
    "return rows.map(due);"));
  return fn([{ json: synthetic }]);
})();
const bySlug = Object.fromEntries(full.map((r) => [r.slug, r]));
assert.strictEqual(bySlug["next-run-invalid"].invalid_next_run_at, "not-a-date", "invalid next_run_at flagged");
assert.strictEqual(bySlug["next-run-invalid"]._due, false);
assert.strictEqual(bySlug["never-ran-on-demand"].skipped_schedule, "on-demand");
assert.strictEqual(bySlug["never-ran-on-demand"]._due, false, "never-run on-demand must NOT be due (the repaired defect)");
assert.strictEqual(bySlug["on-demand-explicit-next"]._due, true, "valid past next_run_at intentionally overrides on-demand");
assert.strictEqual(bySlug["never-ran-unknown"].skipped_schedule, "fortnightly");
assert.strictEqual(bySlug["never-ran-unknown"]._due, false, "never-run unknown schedule must NOT be due");
assert.strictEqual(bySlug["last-run-invalid"].invalid_last_run_at, "yesterday-ish");
assert.strictEqual(bySlug["last-run-invalid"]._due, false);
assert.strictEqual(bySlug["never-ran-daily"]._due, true, "bootstrap: never-run daily is due once");

// --- 2. every registry agent maps to an existing workflow file ---
const mapping = {};
for (const a of agents) {
  assert.ok(a.slug, "registry agent has slug");
  assert.ok(a.workflow_file, `${a.slug} has workflow_file`);
  assert.ok(fs.existsSync(path.join(ROOT, a.workflow_file)), `${a.workflow_file} exists`);
  mapping[a.slug] = a.workflow_file;
}
{
  const counts = {};
  for (const a of agents) counts[a.slug] = (counts[a.slug] || 0) + 1;
  const collisions = Object.entries(counts).filter(([, c]) => c > 1);
  assert.deepStrictEqual(collisions, [], "registry slug collisions: " + JSON.stringify(collisions));
}

// --- 3. MOCK dispatch mapping for registry agents (NOTE: this normalizes the
// registry's human schedule strings like "daily 5:30 AM ET" to coarse
// hourly/daily/weekly buckets. It validates the slug -> workflow_file MAPPING
// only; it does NOT validate real schedule semantics or ET cron timing.) ---
const registryRows = agents.map((a) => ({ slug: a.slug, schedule: a.schedule.startsWith("hourly") ? "hourly" : (a.schedule.startsWith("weekly") ? "weekly" : (a.schedule === "on-demand" ? "on-demand" : "daily")) }));
const dueRegistry = runFilterDue([{ json: registryRows }]).map((r) => r.json);
for (const agent of dueRegistry) {
  assert.ok(mapping[agent.slug], `due agent ${agent.slug} has a dispatch target`);
  assert.ok(agent.dispatch_requested_at, "dispatch item carries run timestamp");
}
// every registry workflow file must parse as an n8n workflow with nodes
for (const [slug, file] of Object.entries(mapping)) {
  const wf = JSON.parse(fs.readFileSync(path.join(ROOT, file), "utf8"));
  assert.ok(Array.isArray(wf.nodes) && wf.nodes.length > 0, `${slug}: ${file} is a workflow with nodes`);
}

console.log("MOCK DISPATCH TESTS PASSED");
console.log("due synthetic:", due.join(", "));
console.log("registry agents:", agents.length, "| all workflow files present and parseable");
console.log("due from registry rows (synthetic last_run):", dueRegistry.map((a) => a.slug).join(", ") || "none (fresh schedules)");
