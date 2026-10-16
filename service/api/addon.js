// Stremio addon routes for a saved setup:
//   /{code}/manifest.json
//   /{code}/catalog/tv/{id}.json   /{code}/catalog/tv/{id}/{extra}.json
//   /{code}/meta/tv/{id}.json      /{code}/stream/tv/{id}.json
// Without a code, the default setup (English only) is served. Also proxies
// /data/index.json for the configuration page.

const store = require("../lib/store");
const cat = require("../lib/catalog");

const CODE = /^[a-z0-9-]{3,24}$/;
const ITEM = /^usfree-[a-z0-9-]{1,80}$/;
const RESOURCES = new Set(["manifest.json", "catalog", "meta", "stream", "data"]);

function send(res, status, body, maxAge = 300) {
  res.statusCode = status;
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "*");
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", status === 200 ? `public, max-age=${maxAge}, s-maxage=${maxAge}` : "no-store");
  res.end(typeof body === "string" ? body : JSON.stringify(body));
}

// Vercel hands the function either the original path or the rewritten one
// (/api/addon?p=...). Everything after "p=" is the path, "&" included, since
// Stremio puts extras like "genre=News&skip=100" in the path itself.
function requestPath(req) {
  const url = req.url || "/";
  const i = url.indexOf("p=");
  const raw = url.startsWith("/api/") && i !== -1 ? url.slice(i + 2) : url.split("?")[0];
  try { return decodeURIComponent(raw).replace(/^\/+/, ""); } catch { return raw.replace(/^\/+/, ""); }
}

function parseExtra(s) {
  const out = {};
  for (const part of (s || "").split("&")) {
    const [k, ...v] = part.split("=");
    if (k) out[k] = v.join("=");
  }
  return out;
}

async function prefsFor(code, index) {
  if (!code) return cat.cleanPrefs(cat.DEFAULT_PREFS, index);
  if (cat.PRESETS[code]) return cat.cleanPrefs(cat.PRESETS[code], index);
  const saved = await store.getPrefs(code);
  return saved ? cat.cleanPrefs(saved, index) : null;
}

async function proxy(res, path) {
  const r = await fetch(`${cat.DATA_BASE}/${path}`);
  if (!r.ok) return send(res, r.status === 404 ? 404 : 502, { err: "not found" });
  send(res, 200, await r.text(), 3600);
}

module.exports = async (req, res) => {
  if (req.method === "OPTIONS") return send(res, 204, "");
  const parts = requestPath(req).split("/").filter(Boolean);
  let code = null;
  if (parts.length && !RESOURCES.has(parts[0])) {
    code = parts.shift().toLowerCase();
    if (!CODE.test(code)) return send(res, 404, { err: "unknown setup" });
  }
  const [resource, type, id, extra] = parts;

  try {
    if (resource === "data" && type === "index.json") return proxy(res, "data/index.json");
    if (resource === "meta" || resource === "stream") {
      const item = (id || "").replace(/\.json$/, "");
      if (type !== "tv" || !ITEM.test(item)) return send(res, 404, { err: "not found" });
      return proxy(res, `${resource}/tv/${item}.json`);
    }

    const index = await cat.loadIndex();
    const prefs = await prefsFor(code, index);
    if (!prefs) return send(res, 404, { err: "This setup code does not exist. Create one on the configure page." });

    if (resource === "manifest.json") return send(res, 200, cat.manifest(index, prefs, code), 60);
    if (resource === "catalog" && type === "tv" && id) {
      const catId = id.replace(/\.json$/, "");
      const ex = parseExtra((extra || "").replace(/\.json$/, ""));
      // Favorites change from the configure page, so that row is never cached for long.
      return send(res, 200, cat.catalog(index, prefs, catId, ex), catId === "fav" ? 30 : 600);
    }
    return send(res, 404, { err: "not found" });
  } catch (e) {
    console.error(e);
    return send(res, 502, { err: "Channel data is temporarily unavailable." });
  }
};

module.exports.requestPath = requestPath;
