// Builds a personalised Stremio addon from the daily data the GitHub Action publishes.

const DATA_BASE = (process.env.DATA_BASE ||
  "https://raw.githubusercontent.com/jotaunospa/usa-free-tv/main").replace(/\/$/, "");
const PAGE_SIZE = 100;
const MIN_ROW = 5;
const INDEX_TTL = 10 * 60 * 1000;

// Ready-made setups that need no saved code ("p-en" is also the default).
const PRESETS = {
  "p-en": { lang: "en", region: "intl", favs: [], hide: [] },
  "p-all": { lang: "all", region: "intl", favs: [], hide: [] },
  "p-us": { lang: "en", region: "us", favs: [], hide: [] },
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
  const data = { updated: raw.updated, themes: raw.themes, channels, byId: new Map(channels.map((c) => [c.id, c])) };
  cached = { at: Date.now(), data };
  return data;
}

function cleanPrefs(p, index) {
  const valid = new Set(index ? index.channels.map((c) => c.id) : []);
  const themeIds = new Set(index ? index.themes.map((t) => t[0]) : []);
  const favs = Array.isArray(p?.favs) ? [...new Set(p.favs.filter((x) => typeof x === "string"))] : [];
  return {
    lang: p?.lang === "all" ? "all" : "en",
    region: p?.region === "us" ? "us" : "intl",
    favs: (index ? favs.filter((id) => valid.has(id)) : favs).slice(0, 500),
    hide: Array.isArray(p?.hide) ? p.hide.filter((t) => !index || themeIds.has(t)).slice(0, 50) : [],
  };
}

function preview(c) {
  return { id: c.id, type: "tv", name: c.name, poster: c.poster, posterShape: "square", genres: c.genres };
}

// Channels this person sees, in display order.
function pool(index, prefs) {
  let list = index.channels.filter((c) => prefs.lang === "all" || c.lang === "en");
  if (prefs.region === "us") {
    // Everything plays from the US, so "no VPN" is no longer a reason to rank first.
    list = [...list].sort((a, b) => b.providers.length - a.providers.length || a.name.localeCompare(b.name));
  }
  return list;
}

function rows(index, prefs) {
  const list = pool(index, prefs);
  const hidden = new Set(prefs.hide);
  if (prefs.region === "us") hidden.add("novpn");
  const out = [{ id: "fav", name: "⭐ My Favorites", items: favItems(index, prefs) }];
  if (prefs.lang === "all") {
    out.push({ id: "otherlang", name: "En Español y otros idiomas", items: list.filter((c) => c.lang !== "en") });
  }
  for (const [tid, tname] of index.themes) {
    if (hidden.has(tid)) continue;
    const items = list.filter((c) => c.themes.includes(tid));
    if (items.length >= MIN_ROW) out.push({ id: tid, name: tname, items });
  }
  return out;
}

function favItems(index, prefs) {
  return prefs.favs.map((id) => index.byId.get(id)).filter(Boolean)
    .filter((c) => prefs.lang === "all" || c.lang === "en");
}

function manifest(index, prefs, code, origin) {
  const list = pool(index, prefs);
  const genres = [...new Set(list.flatMap((c) => c.genres))].sort();
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
    version: "2.0.0",
    name: "USA Free TV",
    description: `${list.length} free, legal live channels with your favorites first. ` +
      "Change your favorites any time from the configure page.",
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
    if (extra.genre) items = items.filter((c) => c.genres.includes(extra.genre));
  } else {
    const row = rows(index, prefs).find((r) => r.id === id);
    items = row ? row.items : [];
  }
  const skip = Math.max(0, parseInt(extra.skip || "0", 10) || 0);
  return { metas: items.slice(skip, skip + PAGE_SIZE).map(preview) };
}

module.exports = { DATA_BASE, PRESETS, DEFAULT_PREFS, loadIndex, cleanPrefs, manifest, catalog, rows };
