#!/usr/bin/env node
/**
 * GrowthOS repository validator.
 *
 * Fails non-zero when any invariant of the workflow fleet is violated.
 * Run: npm run validate:growthos  (or: node scripts/validate-workflows.mjs)
 */
import { readFileSync, readdirSync, existsSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { join, basename } from "node:path";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";

const root = join(import.meta.dirname, "..");
const n8nDir = join(root, "n8n");
const errors = [];
const warnings = [];
const check = (cond, msg) => { if (!cond) errors.push(msg); };
const warn = (cond, msg) => { if (!cond) warnings.push(msg); };

// 1. Every n8n JSON file parses; collect structure
const files = readdirSync(n8nDir).filter((f) => f.endsWith(".json")).sort();
check(files.length === 20, `expected 20 workflow files (00-17, 98, 99), found ${files.length}`);

const workflows = new Map();
for (const f of files) {
  const path = join(n8nDir, f);
  try {
    workflows.set(f, JSON.parse(readFileSync(path, "utf8")));
  } catch (e) {
    errors.push(`${f}: invalid JSON (${e.message})`);
  }
}

const EXPECTED_AGENTS = [
  "seo-intelligence", "search-opportunity", "content-production", "content-performance",
  "content-research", "internal-linking", "technical-seo", "citation-engine",
  "backlink-intelligence", "founder-content", "social-distribution", "cro-intelligence",
  "competitor-intelligence", "reputation-intelligence", "lead-intent", "growth-director",
];
const INFRA = ["00-growthos-orchestrator.json", "98-stale-run-watchdog.json", "99-error-handler.json"];

const agentFiles = new Set();
const envRefs = new Set();

for (const [f, wf] of workflows) {
  const tag = basename(f, ".json");
  const names = new Set((wf.nodes || []).map((n) => n.name));

  // 2/3. Connections reference real nodes; node names unique
  const allNames = (wf.nodes || []).map((n) => n.name);
  check(new Set(allNames).size === allNames.length, `${f}: duplicate node names`);
  for (const [src, conns] of Object.entries(wf.connections || {})) {
    check(names.has(src), `${f}: connection source "${src}" is not a node`);
    for (const branch of conns.main || []) {
      for (const cc of branch || []) {
        check(names.has(cc.node), `${f}: connection target "${cc.node}" (from ${src}) is not a node`);
      }
    }
  }

  // 4. Committed workflows stay inactive
  check(wf.active === false, `${f}: must be "active": false in the repository`);

  // 7. Timezone
  check(wf.settings?.timezone === "America/New_York", `${f}: timezone must be America/New_York`);

  // 5/6. No hardcoded Supabase project URL; Supabase via env
  const blob = JSON.stringify(wf);
  check(!blob.includes("ftchgfwahjeqbyilsmjn"), `${f}: hardcoded Supabase project URL`);
  if (/rest\/v1\//.test(blob)) {
    check(blob.includes("$env.SUPABASE_URL"), `${f}: Supabase REST calls must use $env.SUPABASE_URL`);
    check(blob.includes("$env.SUPABASE_SERVICE_ROLE_KEY"), `${f}: Supabase calls must use $env.SUPABASE_SERVICE_ROLE_KEY`);
  }
  for (const m of blob.matchAll(/\$env\.([A-Z_][A-Z0-9_]*)/g)) envRefs.add(m[1]);

  // Agent workflow invariants
  if (!INFRA.includes(f)) {
    agentFiles.add(f);
    const slugMatch = blob.match(/agents\?slug=eq\.([a-z-]+)/);
    check(Boolean(slugMatch), `${f}: agent identity lookup (agents?slug=) missing`);
    if (slugMatch) check(EXPECTED_AGENTS.includes(slugMatch[1]), `${f}: unknown agent slug ${slugMatch[1]}`);
    for (const req of ["Create Agent Run", "Complete Agent Run", "Update Agent Last Run"]) {
      check(names.has(req), `${f}: run-lifecycle node "${req}" missing`);
    }
    check(names.has("Execute Workflow Trigger"), `${f}: Execute Workflow Trigger missing (orchestrator dispatch)`);
  }
}

// 8/9/10/11/12. Registry, expected agents, infra workflows
const registry = JSON.parse(readFileSync(join(root, "config", "agent-registry.json"), "utf8"));
const registrySlugs = new Set(registry.agents.map((a) => a.slug));
for (const slug of EXPECTED_AGENTS) {
  check(registrySlugs.has(slug), `agent-registry.json: missing agent ${slug}`);
  check(
    [...agentFiles].some((f) => readFileSync(join(n8nDir, f), "utf8").includes(`slug=eq.${slug}`)),
    `no workflow file implements registered agent ${slug}`,
  );
}
check(existsSync(join(n8nDir, "99-error-handler.json")), "workflow 99 (error handler) missing");
check(existsSync(join(n8nDir, "98-stale-run-watchdog.json")), "workflow 98 (stale-run watchdog) missing");
check(existsSync(join(root, "config", "workflow-agent-map.json")), "config/workflow-agent-map.json missing");
const map = JSON.parse(readFileSync(join(root, "config", "workflow-agent-map.json"), "utf8"));
for (const slug of EXPECTED_AGENTS) {
  check(Object.values(map.workflows).includes(slug), `workflow-agent-map.json: no workflow mapped to ${slug}`);
}

// 13. Code-node JavaScript syntax (via node --check)
const tmp = mkdtempSync(join(tmpdir(), "growthos-validate-"));
try {
  for (const [f, wf] of workflows) {
    for (const node of wf.nodes || []) {
      const js = node?.parameters?.jsCode;
      if (!js) continue;
      const p = join(tmp, "code.js");
      writeFileSync(p, js);
      try {
        execFileSync(process.execPath, ["--check", p], { stdio: "pipe" });
      } catch (e) {
        errors.push(`${f} :: ${node.name}: Code node JS syntax error: ${String(e.stderr).slice(0, 200)}`);
      }
    }
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

// 14. Env vars referenced by workflows exist in .env.example / docs
const envExample = readFileSync(join(root, ".env.example"), "utf8");
const envDocs = readFileSync(join(root, "docs", "ENVIRONMENT.md"), "utf8");
const declared = new Set([...envExample.matchAll(/^([A-Z_][A-Z0-9_]*)=/gm)].map((m) => m[1]));
for (const v of envRefs) {
  check(declared.has(v), `.env.example: workflows reference $env.${v} which is not declared`);
  warn(envDocs.includes(v), `docs/ENVIRONMENT.md does not mention ${v}`);
}

// Registry consistency: statuses valid
for (const a of registry.agents) {
  check(
    ["READY", "READY BUT NEEDS CREDENTIAL", "PARTIALLY_IMPLEMENTED", "STUB", "BROKEN"].includes(a.status),
    `agent-registry.json: ${a.slug} has invalid status "${a.status}"`,
  );
}

if (warnings.length) console.log("warnings:");
for (const w of warnings) console.log("  ⚠", w);
if (errors.length) {
  console.error(`\n${errors.length} validation error(s):`);
  for (const e of errors) console.error("  ✗", e);
  process.exit(1);
}
console.log(`\nOK: ${files.length} workflows, ${agentFiles.size} agents, ${envRefs.size} env vars — all invariants hold.`);
