// Read and save a setup.
//   GET  /api/prefs?code=abc123     -> { code, prefs }
//   POST /api/prefs {code?, prefs}  -> { code, prefs }   (no code: a new one is created)
// No accounts: the code in the install link is the only key. Codes are long and
// random, so they can't be guessed.

const crypto = require("crypto");
const store = require("../lib/store");
const cat = require("../lib/catalog");

const CODE = /^[a-z0-9]{10}$/;
const ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"; // no 0/o, 1/l/i

function newCode() {
  const bytes = crypto.randomBytes(10);
  return [...bytes].map((b) => ALPHABET[b % ALPHABET.length]).join("");
}

function send(res, status, body) {
  res.statusCode = status;
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(body));
}

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  let size = 0;
  for await (const c of req) {
    size += c.length;
    if (size > 64 * 1024) throw new Error("too large");
    chunks.push(c);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
}

module.exports = async (req, res) => {
  try {
    const url = new URL(req.url, "http://x");
    if (req.method === "GET") {
      const code = (url.searchParams.get("code") || "").toLowerCase();
      if (!CODE.test(code)) return send(res, 400, { err: "Invalid code." });
      const prefs = await store.getPrefs(code);
      if (!prefs) return send(res, 404, { err: "This setup code does not exist." });
      return send(res, 200, { code, prefs });
    }
    if (req.method !== "POST") return send(res, 405, { err: "Use GET or POST." });

    const body = await readBody(req);
    const index = await cat.loadIndex();
    const prefs = { ...cat.cleanPrefs(body.prefs, index), saved: new Date().toISOString() };
    let code = (body.code || "").toLowerCase();
    if (code) {
      if (!CODE.test(code) || !(await store.exists(code))) return send(res, 404, { err: "This setup code does not exist." });
    } else {
      do { code = newCode(); } while (await store.exists(code));
    }
    await store.setPrefs(code, prefs);
    return send(res, 200, { code, prefs, persistent: store.persistent });
  } catch (e) {
    console.error(e);
    return send(res, 500, { err: "Could not save right now. Try again in a minute." });
  }
};
