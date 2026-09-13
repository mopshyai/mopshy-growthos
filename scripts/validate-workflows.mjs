#!/usr/bin/env node
/**
 * GrowthOS repository validator.
 *
 * Fails non-zero when any invariant of the workflow fleet is violated.
 * Run: npm run validate:growthos  (or: node scripts/validate-workflows.mjs)
 * Self-test (expression linter against known-bad fixtures): --self-test
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

// ---------------------------------------------------------------------------
// n8n expression extraction and validation
// ---------------------------------------------------------------------------

/**
 * Extract every `{{ ... }}` expression body from an n8n parameter string.
 * The scanner tracks '', "", `` (template literals, including nested ${...}),
 * so braces inside strings do not break the depth matching.
 */
export function extractExpressions(s) {
  const exprs = [];
  let i = 0;
  while (i < s.length) {
    const start = s.indexOf("{{", i);
    if (start === -1) break;
    let depth = 0;
    const depthStack = [];
    let j = start + 2; // skip the {{ wrapper itself
    let end = -1;
    let state = "normal";
    while (j < s.length) {
      const ch = s[j];
      const next = s[j + 1];
      if (state === "normal") {
        if (ch === "'") { state = "squote"; j += 1; continue; }
        if (ch === '"') { state = "dquote"; j += 1; continue; }
        if (ch === "`") { state = "backtick"; j += 1; continue; }
        if (ch === "{" || ch === "(" || ch === "[") depth += 1;
        else if (ch === "}") {
          depth -= 1;
          if (depth <= 0) {
            if (next === "}") { end = j + 2; break; }
            end = -1; break; // unbalanced closer: malformed expression
          }
        } else if (ch === ")" || ch === "]") {
          depth -= 1;
          if (depth < 0) { end = -1; break; } // unbalanced closer
        }
        j += 1; continue;
      }
      if (state === "squote" || state === "dquote") {
        if (ch === "\\") { j += 2; continue; }
        if ((state === "squote" && ch === "'") || (state === "dquote" && ch === '"')) state = "normal";
        j += 1; continue;
      }
      if (state === "backtick") {
        if (ch === "\\") { j += 2; continue; }
        if (ch === "$" && next === "{") { depthStack.push(depth); depth = 0; state = "tplexpr"; j += 2; continue; }
        if (ch === "`") state = "normal";
        j += 1; continue;
      }
      if (state === "tplexpr") {
        if (ch === "'") { state = "tplsquote"; j += 1; continue; }
        if (ch === '"') { state = "tpldquote"; j += 1; continue; }
        if (ch === "`") { state = "backtick"; j += 1; continue; }
        if (ch === "(" || ch === "[" || ch === "{") depth += 1;
        else if (ch === "}" || ch === ")" || ch === "]") {
          depth -= 1;
          if (depth < 0) {
            depth = depthStack.pop() ?? 0; // ${ } segment closed — restore outer depth
            state = "backtick";
          }
        }
        j += 1; continue;
      }
      if (state === "tplsquote" || state === "tpldquote") {
        if (ch === "\\") { j += 2; continue; }
        if ((state === "tplsquote" && ch === "'") || (state === "tpldquote" && ch === '"')) state = "tplexpr";
        j += 1; continue;
      }
      j += 1;
    }
    if (end === -1) { exprs.push({ body: s.slice(start + 2), unterminated: true }); break; }
    exprs.push({ body: s.slice(start + 2, end - 2) });
    i = end;
  }
  return exprs;
}

/** Parse-check a single expression body the way n8n's evaluator would. */
export function expressionIsParsable(body) {
  try {
    // eslint-disable-next-line no-new-func
    new Function(`"use strict"; return (${body});`);
    return true;
  } catch {
    return false;
  }
}

const MALFORMED_SAMPLE = "JSON.stringify({ model: 'gpt-5.6-sol',, tools: [{ type: 'web_search' }], input: `x ${1} y` })";

if (process.argv.includes("--self-test")) {
  const good = expressionIsParsable(MALFORMED_SAMPLE.replace("',,", "',"));
  const bad = expressionIsParsable(MALFORMED_SAMPLE);
  const extracted = extractExpressions(`prefix =={{ ${MALFORMED_SAMPLE} }} suffix`).length;
  if (good && !bad && extracted === 1) {
    console.log("self-test OK: linter accepts valid expressions, rejects malformed ones, extracts correctly");
    process.exit(0);
  }
  console.error(`self-test FAILED: good=${good} badRejected=${!bad} extracted=${extracted}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Workflow checks
// ---------------------------------------------------------------------------

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
const GITHUB_NODES = ["Get Website Main SHA", "Create Article Branch", "Create Article File Only", "Open Review PR"];

const agentFiles = new Set();
const envRefs = new Set();

function triggersOf(wf) {
  return (wf.nodes || [])
    .filter((n) => /Trigger$/.test(n.type.split(".").pop() || "") || n.type.includes("Trigger"))
    .map((n) => n.name);
}

function reachable(startNodes, connections) {
  const seen = new Set();
  const queue = [...startNodes];
  while (queue.length) {
    const n = queue.pop();
    if (seen.has(n)) continue;
    seen.add(n);
    const conns = connections[n];
    if (!conns) continue;
    for (const branch of conns.main || []) for (const cc of branch || []) queue.push(cc.node);
  }
  return seen;
}

for (const [f, wf] of workflows) {
  const tag = basename(f, ".json");
  const nodes = wf.nodes || [];
  const names = new Set(nodes.map((n) => n.name));
  const byName = Object.fromEntries(nodes.map((n) => [n.name, n]));

  // 2/3. Connections reference real nodes; node names unique; no duplicate edges
  const allNames = nodes.map((n) => n.name);
  check(new Set(allNames).size === allNames.length, `${f}: duplicate node names`);
  const seenEdges = new Set();
  for (const [src, conns] of Object.entries(wf.connections || {})) {
    check(names.has(src), `${f}: connection source "${src}" is not a node`);
    (conns.main || []).forEach((branch, outIdx) => {
      for (const cc of branch || []) {
        check(names.has(cc.node), `${f}: connection target "${cc.node}" (from ${src}) is not a node`);
        const key = `${src}|${outIdx}|${cc.node}`;
        check(!seenEdges.has(key), `${f}: duplicate connection edge ${src} -> ${cc.node}`);
        seenEdges.add(key);
      }
    });
  }

  // 4. Committed workflows stay inactive
  check(wf.active === false, `${f}: must be "active": false in the repository`);

  // 7. Timezone
  check(wf.settings?.timezone === "America/New_York", `${f}: timezone must be America/New_York`);

  // 5/6. No hardcoded Supabase project URL; Supabase via env; no Studio citation table
  const blob = JSON.stringify(wf);
  check(!blob.includes("ftchgfwahjeqbyilsmjn"), `${f}: hardcoded Supabase project URL`);
  check(!blob.includes("/rest/v1/citations'") && !blob.includes("/rest/v1/citations?"),
    `${f}: must not query Studio table /rest/v1/citations (GrowthOS uses growth_citations)`);
  if (/rest\/v1\//.test(blob)) {
    check(blob.includes("$env.SUPABASE_URL"), `${f}: Supabase REST calls must use $env.SUPABASE_URL`);
    check(blob.includes("$env.SUPABASE_SERVICE_ROLE_KEY"), `${f}: Supabase calls must use $env.SUPABASE_SERVICE_ROLE_KEY`);
  }
  for (const m of blob.matchAll(/\$env\.([A-Z_][A-Z0-9_]*)/g)) envRefs.add(m[1]);

  // One-to-one workflow->agent model must stay dead
  check(!blob.includes("n8n_workflow_name=eq") || f === "99-error-handler.json"
    ? !blob.includes("agents?n8n_workflow_name") : true,
    `${f}: must resolve workflows through workflow_runtime_map, not agents columns`);
  check(!/agents\?n8n_workflow_name=/.test(blob), `${f}: legacy agents?n8n_workflow_name lookup present`);
  check(!/agents\?[^']*n8n_workflow_id/.test(blob), `${f}: legacy agents?n8n_workflow_id lookup present`);

  // Embedded n8n expressions must parse (HTTP bodies, URLs, Set values, IF conditions…)
  for (const node of nodes) {
    if (node.type === "n8n-nodes-base.code") continue; // jsCode checked separately below
    for (const [param, value] of Object.entries(node.parameters || {})) {
      if (typeof value !== "string" || !value.includes("{{")) continue;
      for (const { body, unterminated } of extractExpressions(value)) {
        if (unterminated) {
          errors.push(`${f} :: ${node.name}.${param}: unterminated {{ }} expression`);
          continue;
        }
        if (!expressionIsParsable(body)) {
          errors.push(`${f} :: ${node.name}.${param}: malformed expression: ${body.slice(0, 120)}`);
        }
      }
    }
  }

  // Literal-body bug class: JSON bodies must be expressions, not literal text
  for (const node of nodes) {
    const p = node.parameters || {};
    const isHttp = node.type === "n8n-nodes-base.httpRequest";
    if (isHttp && p.sendBody && p.rawContentType === "application/json") {
      check(typeof p.body === "string" && p.body.startsWith("={{"),
        `${f} :: ${node.name}: JSON body must be an n8n expression (={{ ... }}), not literal text`);
    }
    if (isHttp && p.specifyBody === "json" && p.jsonBody !== undefined) {
      check(String(p.jsonBody).startsWith("={{"),
        `${f} :: ${node.name}: jsonBody must be an n8n expression`);
    }
  }

  // `.first()` must not be used in per-item mutation nodes fed by Explode nodes
  const explodeFed = new Set();
  for (const node of nodes) {
    if (/^Explode/.test(node.name) && node.type === "n8n-nodes-base.code") {
      const conns = (wf.connections || {})[node.name];
      for (const branch of (conns?.main || [])) for (const cc of branch || []) explodeFed.add(cc.node);
    }
  }
  for (const node of nodes) {
    if (!explodeFed.has(node.name)) continue;
    const blob2 = JSON.stringify(node.parameters || {});
    for (const m of blob2.matchAll(/\$\('([^']+)'\)\.first\(\)/g)) {
      if (explodeFed.has(m[1])) {
        errors.push(`${f} :: ${node.name}: per-item .first() on multi-item node "${m[1]}" — cross-item contamination; use $json / .item`);
      }
    }
  }

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
    check(names.has("GrowthOS Paused?"), `${f}: fail-closed pause gate missing`);
  }

  // Every non-trigger node must be reachable from some trigger (no orphaned chains)
  {
    const triggerNames = triggersOf(wf);
    const reachedAll = reachable(triggerNames, wf.connections || {});
    for (const node of nodes) {
      const isTrigger = triggerNames.includes(node.name);
      check(isTrigger || reachedAll.has(node.name),
        `${f}: node "${node.name}" is unreachable from any trigger (broken chain)`);
    }
  }

  // 04 publisher: dry-run true branch must never reach GitHub
  if (f === "04-content-github-publisher.json") {
    const dryTrue = ((wf.connections || {})["Dry Run?"]?.main || [])[0]?.map((e) => e.node) || [];
    check(dryTrue.includes("Compose Dry-Run Outcome"),
      "04: Dry Run? TRUE branch must route to Compose Dry-Run Outcome");
    const reached = reachable(dryTrue, wf.connections || {});
    for (const g of GITHUB_NODES) {
      check(!reached.has(g), `04: Dry Run? TRUE branch can reach GitHub node "${g}" — dry-run is not safe`);
    }
    const dryFalse = ((wf.connections || {})["Dry Run?"]?.main || [])[1]?.map((e) => e.node) || [];
    check(dryFalse.includes("Get Website Main SHA"),
      "04: Dry Run? FALSE branch must route to the real publishing path");
  }
}

// 00/99 runtime-map model
check(readFileSync(join(n8nDir, "00-growthos-orchestrator.json"), "utf8").includes("workflow_runtime_map"),
  "00: must source dispatch from workflow_runtime_map");
check(readFileSync(join(n8nDir, "99-error-handler.json"), "utf8").includes("workflow_runtime_map"),
  "99: must resolve workflows through workflow_runtime_map");

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

// Migration sanity: no Studio-table targets, no uuid workflow ids
const migPath = join(root, "supabase", "migrations", "20260913_production_hardening.sql");
if (existsSync(migPath)) {
  const mig = readFileSync(migPath, "utf8");
  check(!/(?<![a-z_])citations_directory_unique/.test(mig), "migration: legacy citations_directory_unique on Studio table present");
  check(mig.includes("growth_citations"), "migration: growth_citations reconciliation missing");
  check(!mig.includes("legacy_citations rename to citations"), "migration: would overwrite Studio table");
  check(/rename to growth_citations/.test(mig), "migration: legacy_citations -> growth_citations rename missing");
  check(!mig.includes("n8n_workflow_id uuid"), "migration: workflow IDs must be text, not uuid");
  check(mig.includes("workflow_runtime_map"), "migration: workflow_runtime_map table missing");
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
