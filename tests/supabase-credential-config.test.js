// Offline guard for the n8n Cloud secure-config conversion (2026-11-13).
// $env is self-hosted-only in n8n (docs.n8n.io/build/code-in-n8n/use-built-in-shortcuts/n8n-metadata),
// so workflows targeting n8n Cloud must not read config/secrets from $env.
// The supported secure path: Supabase REST nodes authenticate through the
// workspace's existing "Supabase account" credential (predefined supabaseApi),
// and non-secret config (project URL, site URL, GA4 property id) lives in
// plain workflow fields - never the service key.
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
// Files converted so far; extend this list as the batch proceeds.
const CONVERTED = ["n8n/00-growthos-orchestrator.json", "n8n/01-seo-intelligence.json"];

function* allStrings(v) {
  if (typeof v === "string") yield v;
  else if (Array.isArray(v)) for (const x of v) yield* allStrings(x);
  else if (v && typeof v === "object") for (const k of Object.keys(v)) yield* allStrings(v[k]);
}

for (const rel of CONVERTED) {
  const wf = JSON.parse(fs.readFileSync(path.join(ROOT, rel), "utf8"));
  const strings = [...allStrings(wf)];

  // 1. No self-hosted-only $env reads remain for the config/secrets we converted.
  for (const banned of ["$env.SUPABASE_URL", "$env.SUPABASE_SERVICE_ROLE_KEY", "$env.GSC_SITE_URL", "$env.GA4_PROPERTY_ID"]) {
    assert.ok(!strings.some((s) => s.includes(banned)), `${rel} still references ${banned}`);
  }

  // 2. No service-key-shaped material anywhere in the workflow file.
  assert.ok(!strings.some((s) => /Bearer\s+\$env/.test(s)), `${rel} builds a Bearer header from $env`);
  assert.ok(!strings.some((s) => s.includes("ftchgfwahjeqbyilsmjn")), `${rel} hardcodes the real project ref (use the placeholder)`);

  // 3. Every Supabase REST node uses the credential, not manual auth headers.
  for (const node of wf.nodes) {
    const url = node.parameters && node.parameters.url;
    if (typeof url === "string" && url.includes("/rest/v1/")) {
      assert.strictEqual(node.parameters.authentication, "predefinedCredentialType", `${rel}:${node.name} must use predefined credential auth`);
      assert.strictEqual(node.parameters.nodeCredentialType, "supabaseApi", `${rel}:${node.name} must use supabaseApi`);
      assert.ok(node.credentials && node.credentials.supabaseApi, `${rel}:${node.name} must bind the Supabase credential`);
      const headers = (node.parameters.headerParameters && node.parameters.headerParameters.parameters) || [];
      assert.ok(!headers.some((h) => ["apikey", "Authorization"].includes(h.name)), `${rel}:${node.name} still sets auth headers manually`);
    }
  }
}

// 4. 01 carries its config in the Run Config node as plain non-secret fields.
const wf01 = JSON.parse(fs.readFileSync(path.join(ROOT, "n8n/01-seo-intelligence.json"), "utf8"));
const runConfig = wf01.nodes.find((n) => n.name === "Run Config");
const fields = Object.fromEntries(runConfig.parameters.assignments.assignments.map((a) => [a.name, a.value]));
assert.strictEqual(fields.supabase_url, "https://YOUR-PROJECT-REF.supabase.co", "supabase_url placeholder must be filled by the operator");
assert.strictEqual(fields.site_url, "https://mopshy.com/", "site_url is a literal, not $env");
assert.ok("ga4_property_id" in fields, "ga4_property_id field exists (empty = GA4 branch skipped)");

// 5. GA4 nodes read the property id from Run Config, not $env.
const ga4If = wf01.nodes.find((n) => n.name === "GA4 Configured?");
assert.ok(JSON.stringify(ga4If.parameters).includes("ga4_property_id"), "GA4 Configured? reads config field");

console.log("supabase-credential-config: all assertions passed");
