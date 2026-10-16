// Preferences storage: Upstash Redis over its REST API (what Vercel's Redis/KV
// integration provisions). Falls back to memory when no credentials are set, which
// is only meant for local testing.

const URL_ = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL || "";
const TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN || "";
const memory = new Map();
const PREFIX = "prefs:";

async function redis(command) {
  const r = await fetch(URL_, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(command),
  });
  if (!r.ok) throw new Error(`storage ${r.status}`);
  return (await r.json()).result;
}

async function getPrefs(code) {
  if (!URL_) return memory.get(code) || null;
  const raw = await redis(["GET", PREFIX + code]);
  return raw ? JSON.parse(raw) : null;
}

async function setPrefs(code, prefs) {
  if (!URL_) { memory.set(code, prefs); return; }
  await redis(["SET", PREFIX + code, JSON.stringify(prefs)]);
}

async function exists(code) {
  if (!URL_) return memory.has(code);
  return (await redis(["EXISTS", PREFIX + code])) === 1;
}

module.exports = { getPrefs, setPrefs, exists, persistent: Boolean(URL_) };
