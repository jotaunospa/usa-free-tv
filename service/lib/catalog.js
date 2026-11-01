// Builds a personalised Stremio addon from the daily data the GitHub Action publishes.

const DATA_BASE = (process.env.DATA_BASE ||
  "https://raw.githubusercontent.com/jotaunospa/usa-free-tv/main").replace(/\/$/, "");
const PAGE_SIZE = 100;
const MIN_ROW = 5;
const ROW_MAX = 25;       // channels per category row on the home screen (the full list lives in Discover)
const PICKS_PER_CAT = 5;  // "Para ti" starts with the best 5 of each category
const NO_PICKS = new Set(["local", "otros"]);
const INDEX_TTL = 10 * 60 * 1000;

// Ready-made setups that need no saved code ("p-en" is also the default).
const PRESETS = {
  "p-en": { lang: "en", region: "intl", favs: [], drop: [], hide: [] },
  "p-all": { lang: "all", region: "intl", favs: [], drop: [], hide: [] },
  "p-us": { lang: "en", region: "us", favs: [], drop: [], hide: [] },
};

const DEFAULT_PREFS = PRESETS["p-en"];

let cached = null;
async function loadIndex() {
  if (cached && Date.now() - cached.at < INDEX_TTL) return cached.data;
  const r = await fetch(`${DATA_BASE}/data/index.json`);
  if (!r.ok) {
    if (cached) return cached.data; // keep serving the last good copy
    throw new Error(`index ${r.status}`);
  }
  const raw = await r.json();
  const f = raw.fields;
  const channels = raw.channels.map((row) => Object.fromEntries(f.map((k, i) => [k, row[i]])));
  const data = { updated: raw.updated, themes: raw.themes, cats: raw.cats || [], aliases: raw.aliases || {}, channels, byId: new Map(channels.map((c) => [c.id, c])) };
  cached = { at: Date.now(), data };
  return data;
}

function cleanPrefs(p, index) {
  const valid = new Set(index ? index.channels.map((c) => c.id) : []);
  const rowIds = new Set(index ? [...index.themes.map((t) => t[0]), ...index.cats.map((c) => c[0])] : []);
  // Channels folded into another (duplicates) keep answering to their old id.
  const al = (id) => (index && index.aliases && index.aliases[id]) || id;
  const favs = Array.isArray(p?.favs) ? [...new Set(p.favs.filter((x) => typeof x === "string").map(al))] : [];
  return {
    lang: p?.lang === "all" ? "all" : "en",
    region: p?.region === "us" ? "us" : "intl",
    favs: (index ? favs.filter((id) => valid.has(id)) : favs).slice(0, 500),
    // Automatic "Para ti" picks this person removed. Only their own changes are stored,
    // so the daily improvements to the automatic list keep reaching them.
    drop: Array.isArray(p?.drop) ? [...new Set(p.drop.filter((x) => typeof x === "string").map(al).filter((x) => !index || valid.has(x)))].slice(0, 500) : [],
    hide: Array.isArray(p?.hide) ? p.hide.filter((t) => !index || rowIds.has(t)).slice(0, 50) : [],
  };
}

function preview(c) {
  return { id: c.id, type: "tv", name: c.name, poster: c.poster, posterShape: "square", genres: c.genres };
}

// Channels this person sees, in display order.
function pool(index, prefs) {
  // The generator already sorts best score first (no-VPN, widely carried and well-known
  // channels rank higher), so that order is kept.
  return index.channels.filter((c) => prefs.lang === "all" || c.lang === "en");
}

const hasCats = (index) => index.cats.length > 0 && index.channels.some((c) => c.cat);

function rows(index, prefs) {
  const list = pool(index, prefs);
  const hidden = new Set(prefs.hide);
  // Rows were once themes ("Watch Without VPN" and friends); that row is gone for good.
  hidden.add("novpn");
  const out = [{ id: "fav", name: "⭐ Para ti", items: favItems(index, prefs) }];
  if (prefs.lang === "all") {
    out.push({ id: "otherlang", name: "En Español y otros idiomas", items: list.filter((c) => c.lang !== "en") });
  }
  if (hasCats(index)) {
    for (const [cid, cname] of index.cats) {
      if (hidden.has(cid)) continue;
      const items = list.filter((c) => c.cat === cid);
      if (items.length >= MIN_ROW) out.push({ id: cid, name: cname, items: items.slice(0, ROW_MAX) });
    }
    return out;
  }
  for (const [tid, tname] of index.themes) { // data from before categories existed
    if (hidden.has(tid)) continue;
    const items = list.filter((c) => c.themes.includes(tid));
    if (items.length >= MIN_ROW) out.push({ id: tid, name: tname, items });
  }
  return out;
}

// Automatic part of "Para ti": the best few channels of every category.
function autoPicks(index, prefs) {
  if (!hasCats(index)) return [];
  const list = pool(index, prefs);
  const out = [];
  for (const [cid] of index.cats) {
    if (NO_PICKS.has(cid)) continue;
    out.push(...list.filter((c) => c.cat === cid).slice(0, PICKS_PER_CAT));
  }
  return out;
}

// "Para ti" = the channels the person added, in their order, then the automatic picks
// they have not removed.
function favItems(index, prefs) {
  const mine = prefs.favs.map((id) => index.byId.get(id)).filter(Boolean)
    .filter((c) => prefs.lang === "all" || c.lang === "en");
  const seen = new Set(mine.map((c) => c.id));
  const dropped = new Set(prefs.drop);
  return [...mine, ...autoPicks(index, prefs).filter((c) => !seen.has(c.id) && !dropped.has(c.id))];
}

function manifest(index, prefs, code, origin) {
  const list = pool(index, prefs);
  const cats = hasCats(index) ? index.cats : [];
  const genres = cats.length ? cats.map(([, n]) => n) : [...new Set(list.flatMap((c) => c.genres))].sort();
  const catalogs = rows(index, prefs).map((r) => ({
    type: "tv", id: r.id, name: r.name, extra: [{ name: "skip", isRequired: false }],
  }));
  catalogs.push({
    type: "tv", id: "all", name: "All Channels",
    extra: [{ name: "genre", isRequired: false, options: genres }, { name: "skip", isRequired: false }],
  });
  catalogs.push({ type: "tv", id: "search", name: "USA Free TV", extra: [{ name: "search", isRequired: true }] });
  return {
    id: "community.usa-free-tv.config",
    version: "3.0.0",
    name: "USA Free TV",
    description: `${list.length} free, legal live channels, sorted by category with the best first. ` +
      "Edit your \"Para ti\" row any time from the configure page.",
    logo: `${DATA_BASE}/public/logo.png`,
    resources: ["catalog", "meta", "stream"],
    types: ["tv"],
    idPrefixes: ["usfree-"],
    catalogs,
    behaviorHints: { configurable: true, configurationRequired: false },
  };
}

// Search matches the channel name, which carries the shows it airs.
function fold(s) {
  return s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function catalog(index, prefs, id, extra) {
  let items;
  if (id === "search") {
    const q = fold(extra.search || "").trim();
    items = q ? pool(index, prefs).filter((c) => fold(c.name).includes(q)) : [];
  } else if (id === "all") {
    items = pool(index, prefs);
    if (extra.genre) {
      const hit = hasCats(index) && index.cats.find(([, n]) => n === extra.genre);
      items = hit ? items.filter((c) => c.cat === hit[0]) : items.filter((c) => c.genres.includes(extra.genre));
    }
  } else {
    const row = rows(index, prefs).find((r) => r.id === id);
    items = row ? row.items : [];
  }
  const skip = Math.max(0, parseInt(extra.skip || "0", 10) || 0);
  return { metas: items.slice(skip, skip + PAGE_SIZE).map(preview) };
}

module.exports = { DATA_BASE, PRESETS, DEFAULT_PREFS, loadIndex, cleanPrefs, manifest, catalog, rows };
