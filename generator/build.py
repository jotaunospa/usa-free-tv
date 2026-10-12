"""Build the USA Free TV Stremio addon as static JSON files.

Sources are free, ad-supported (FAST) services and curated public playlists.
Each channel appears once; when several services carry the same channel, its
streams are merged as alternatives under a single entry.

Usage:
    python generator/build.py                 # build into the repo root
    python generator/build.py --check         # also probe community streams
    python generator/build.py --base-url URL  # override published base URL

Standard library only, so it runs in GitHub Actions without installing anything.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import hashlib
import ipaddress
import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
PAGE_SIZE = 100
ID_PREFIX = "usfree-"

MJH_RAW = "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master"
MJH_SITE = "https://i.mjh.nz"
JMP = "https://jmp2.uk"

# Playlists published by i.mjh.nz. Used to resolve stream URLs by channel id.
# All optional: whichever ones respond are indexed.
MJH_PLAYLISTS = [
    f"{MJH_SITE}/all/raw-tv.m3u8",
    f"{MJH_SITE}/PlutoTV/us.m3u8",
    f"{MJH_SITE}/SamsungTVPlus/us.m3u8",
    f"{MJH_SITE}/Plex/us.m3u8",
    f"{MJH_SITE}/Roku/all.m3u8",
]

# Tubi's free live channels, published daily by a community scraper. Stream URLs
# point at Tubi's own CDN (live-manifest.production-public.tubi.io).
TUBI = "https://raw.githubusercontent.com/BuddyChewChew/tubi-scraper/main/tubi_playlist.m3u"
TUBI_HOST = "live-manifest.production-public.tubi.io"

IPTV_ORG_US = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u"
IPTV_ORG_CHANNELS = "https://iptv-org.github.io/api/channels.json"
FREE_TV = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"

# Lower number = listed first and preferred for name/logo/description.
PROVIDERS = {
    "pluto": ("Pluto TV", 1),
    "samsung": ("Samsung TV Plus", 2),
    "tubi": ("Tubi", 3),
    "roku": ("The Roku Channel", 4),
    "plex": ("Plex", 5),
    "freetv": ("Free-TV", 6),
    "iptvorg": ("iptv-org", 7),
}

# Services that only stream to US IP addresses. Tubi's live channels and most
# community streams play from abroad (tested from Chile); these need a US connection.
US_ONLY = {"pluto", "samsung", "roku", "plex"}

# Order in which a channel's streams are offered: sources that play without a VPN first.
STREAM_ORDER = ["tubi", "iptvorg", "freetv", "pluto", "samsung", "roku", "plex"]

# Pay-TV networks. Community playlists sometimes carry unlicensed restreams of
# these; they are dropped from community sources. FAST services are official
# and are not filtered by this list.
PAY_TV = [
    "a and e", "aande", "amc", "animal planet", "bet", "bravo", "cartoon network",
    "cinemax", "cmt", "cnbc", "cnn", "comedy central", "cooking channel",
    "discovery", "disney", "e entertainment", "espn", "food network", "fox news",
    "fox business", "fox sports", "fs1", "fs2", "freeform", "fx", "fxx", "fxm",
    "golf channel", "hallmark", "hbo", "hgtv", "history", "ifc", "investigation discovery",
    "lifetime", "magnolia", "mgm", "mlb network", "msnbc", "mtv", "nat geo",
    "national geographic", "nba tv", "nfl network", "nfl redzone", "nhl network",
    "nick", "nickelodeon", "own", "oxygen", "paramount network", "science channel",
    "showtime", "smithsonian", "starz", "sundance", "syfy", "tbs", "tcm", "tlc",
    "tnt", "travel channel", "trutv", "tv land", "universal kids", "usa network",
    "vh1", "we tv", "weather channel", "tennis channel", "big ten network",
    "sec network", "acc network", "cbs sports network", "nbc sports", "bein",
]

# Over-the-air networks only appear legitimately on FAST services under their
# own streaming brands (ABC News Live, NBC News NOW...). A community stream named
# just "NBC" or "Fox West" is a retransmission, so it is dropped.
BROADCAST = {"abc", "cbs", "nbc", "fox", "cw", "the cw", "pbs", "ion", "telemundo",
             "univision", "unimas", "galavision", "tudn", "my network", "mynetworktv"}

# Hosts in community playlists that resell or retransmit channels they do not
# own (subscription apps, regional OTT resellers, camera-monitoring relays).
BLOCKED_HOSTS = ("univisionnow.com", "aynaott.com", "smartplaytv.in", "cammonitorplus.net",
                 "edgenextcdn.net")

GENRES = [
    "News", "Local", "Sports", "Movies", "Entertainment", "Comedy", "Drama",
    "Reality", "Classics", "Sci-Fi", "Kids", "Documentaries",
    "Lifestyle", "Music", "Latino", "Faith", "Shopping",
]

# First matching rule wins. Matched against the lowercased provider group.
GENRE_RULES = [
    ("Latino", ["espanol", "español", "latino", "hispanic"]),
    ("Local", ["local news", "local"]),
    ("News", ["news", "opinion", "weather", "talk"]),
    ("Sports", ["sport", "racing", "ball", "boxing", "wrestling", "martial", "soccer",
                "hockey", "golf", "poker", "billiards", "bowling", "surf", "ski", "snowboard",
                "bmx", "bicycle", "motorcycle", "rugby", "olympic", "volleyball", "swimming",
                "fishing", "outdoors", "skateboard", "football"]),
    ("Kids", ["kids", "children", "animated", "family"]),
    ("Sci-Fi", ["sci-fi", "science fiction", "anime", "gaming", "horror", "fantasy",
                        "paranormal"]),
    ("Documentaries", ["nature", "history", "science", "documentary", "docudrama", "animals",
                       "educational", "environment"]),
    ("Movies", ["movie", "action", "thriller", "adventure", "romance", "suspense", "halloween"]),
    ("Comedy", ["comedy", "sitcom", "standup"]),
    ("Drama", ["drama", "crime", "mystery", "law", "soap", "medical"]),
    ("Reality", ["reality", "game show", "competition", "daytime", "auction"]),
    ("Classics", ["classic", "western"]),
    ("Music", ["music", "ambiance"]),
    ("Lifestyle", ["home", "food", "eats", "cooking", "travel", "lifestyle", "fashion", "auto",
                   "health", "how-to", "house", "garden", "art", "pop culture"]),
    ("Faith", ["faith", "religious"]),
    ("Shopping", ["shopping"]),
]

NAME_GENRE_HINTS = [
    ("News", re.compile(r"\b(news|noticias|weather)\b")),
    ("Shopping", re.compile(r"\b(qvc|hsn|shop|jewelry)\b")),
    ("Faith", re.compile(r"\b(church|gospel|bible|faith|christian|catholic|god|abn|ewtn|tbn|daystar)\b")),
    ("Music", re.compile(r"\b(music|radio|hits|jukebox)\b")),
    ("Sports", re.compile(r"\b(sports?|racing|golf|tennis|fight|wrestling)\b")),
    ("Kids", re.compile(r"\b(kids|cartoon|toons?)\b")),
    ("Local", re.compile(r"^[kw][a-z]{2,3}\b")),
]


# Themed catalogs shown as rows on the Stremio home screen, in this order.
# A channel joins a theme when any rule matches: one of its genres, a word in a
# provider's own category, or a regex on its name.
THEMES = [
    # id, row name, genres, provider-category words, name regex
    ("novpn", "Watch Without VPN", [], [], None),         # has a stream that plays outside the US
    ("popular", "Popular Free Channels", [], [], None),   # carried by 2+ services
    ("series", "Series 24/7", [], [], None),              # EPG shows one series all day
    ("news", "News 24/7", ["News"], [], None),
    ("sports", "Sports", ["Sports"], [], None),
    ("movies", "Movies", ["Movies"], [], None),
    ("truecrime", "True Crime", [], ["true crime", "crime"],
     r"\b(crime|cops|forensic|murder|detective|csi|investigat|court|judge|fbi|homicide)"),
    ("comedy", "Comedy", ["Comedy"], [], None),
    ("kids", "Kids & Family", ["Kids"], [], None),
    ("anime", "Anime & Gaming", [], ["anime", "gaming"],
     r"\b(anime|gaming|esports|crunchyroll|yu gi oh|pokemon|naruto|gundam)"),
    ("gameshows", "Game Shows", [], ["game show", "daytime", "games & competition"],
     r"\b(game show|price is right|family feud|deal or no deal|jeopardy|wheel of fortune|buzzr|match game|lets make a deal)"),
    # Documentaries plus the official FAST channels of History, Discovery, Smithsonian,
    # BBC Earth and similar, matched on the channel name or the series it shows 24/7.
    ("factual", "History, Science & Nature", ["Documentaries"], [],
     r"\b(history|discovery|smithsonian|bbc earth|pbs nature|love nature|magellantv|pluto tv science"
     r"|ancient aliens|modern marvels|pawn stars|american pickers|forged in fire|swamp people"
     r"|ice road truckers|curse of oak island|the universe|universe mysteries|mythbusters|how its made"
     r"|gold rush|deadliest catch|naked and afraid|mysteries xplored|xtreme outdoor)\b"),
    ("food", "Food & Home", [], ["food", "cooking", "home", "good eats"],
     r"\b(cook|kitchen|food|chef|bbq|bake|baking|recipe|tasty|home improvement)"),
    ("classics", "Westerns & Classic TV", ["Classics"], [], None),
    ("music", "Music", ["Music"], [], None),
    ("latino", "En Español", ["Latino"], [], None),
    ("local", "Local News", ["Local"], [], None),
]

# Genres whose EPG repeats one title for reasons other than being a series marathon.
NOT_SERIES = {"News", "Local", "Sports", "Music", "Shopping", "Faith", "Movies"}


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #

def fetch(url: str, timeout: int = 60) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        return data
    except Exception as e:  # noqa: BLE001 - every source is optional
        print(f"  ! {url}: {e}", file=sys.stderr)
        return None


def fetch_json(url: str):
    data = fetch(url)
    return json.loads(data) if data else None


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #

@dataclass
class Stream:
    provider: str
    url: str
    label: str = ""


@dataclass
class Entry:
    provider: str
    name: str
    url: str
    logo: str = ""
    background: str = ""
    description: str = ""
    groups: list[str] = field(default_factory=list)
    programs: list[str] = field(default_factory=list)  # EPG titles, in airing order

    @property
    def needs_us(self) -> bool:
        return self.provider in US_ONLY or "geo-blocked" in self.name.lower()


@dataclass
class Channel:
    key: str
    entries: list[Entry] = field(default_factory=list)

    @property
    def primary(self) -> Entry:
        return min(self.entries, key=lambda e: PROVIDERS[e.provider][1])

    def best(self, attr: str) -> str:
        for e in sorted(self.entries, key=lambda e: PROVIDERS[e.provider][1]):
            if getattr(e, attr):
                return getattr(e, attr)
        return ""


# --------------------------------------------------------------------------- #
# Normalisation and genre mapping
# --------------------------------------------------------------------------- #

TRAILING_NOISE = {"hd", "fhd", "uhd", "4k", "east", "us", "usa", "tv", "channel", "network", "live"}


def clean_display(name: str) -> str:
    name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", name)  # (720p), [Geo-blocked]
    name = re.sub(r"[ⒼⓈⓎⓉ]", "", name)
    return re.sub(r"\s+", " ", name).strip(" -|")


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", clean_display(name)).encode("ascii", "ignore").decode().lower()
    s = s.replace("'", "").replace("&", " and ").replace("+", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s).split()
    while len(s) > 1 and s[-1] in TRAILING_NOISE:
        s.pop()
    return " ".join(s)


def merge_key(name: str) -> str:
    """Spacing-insensitive identity: 'Toon Goggles' == 'ToonGoggles', 'QVC 2' == 'QVC2'."""
    return norm(name).replace(" ", "")


def slug(key: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", key).strip("-")[:60] or "channel"
    return f"{ID_PREFIX}{base}"


def genre_for(groups: list[str], name: str) -> list[str]:
    found: list[str] = []
    for g in groups:
        gl = g.lower()
        for genre, words in GENRE_RULES:
            if any(w in gl for w in words):
                if genre not in found:
                    found.append(genre)
                break
    if not found:
        n = norm(name)
        for genre, rx in NAME_GENRE_HINTS:
            if rx.search(n):
                found.append(genre)
                break
    return found[:2] or ["Entertainment"]


def lineup(ch: "Channel") -> tuple[str | None, list[str]]:
    """Return (series shown 24/7 or None, most frequent shows) from EPG titles."""
    titles = max((e.programs for e in ch.entries), key=len, default=[])
    if not titles:
        return None, []
    counts: dict[str, int] = {}
    for t in titles:
        t = t.strip()
        counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts, key=lambda t: -counts[t])
    top = ranked[0]
    chan = norm(ch.primary.name)
    # The EPG only covers about a day, so a weekend marathon looks like a series
    # channel. Require the channel to be named after the show it repeats.
    stop = {"the", "a", "of", "and", "tv", "la", "el", "los", "las", "de", "pluto", "24", "7", "channel"}
    shared = (set(norm(top).split()) & set(chan.split())) - stop
    series = top if len(titles) >= 4 and counts[top] / len(titles) >= 0.75 and shared else None
    shows = [t for t in ranked if norm(t) != chan][:5]
    return series, shows


def themes_for(groups: list[str], name: str, genres: list[str], providers: int,
               series: str | None, open_stream: bool) -> list[str]:
    gl = " | ".join(groups).lower()
    n = norm(name)
    out = []
    for tid, _, tgenres, words, rx in THEMES:
        if tid == "novpn":
            hit = open_stream
        elif tid == "popular":
            hit = providers >= 2
        elif tid == "series":
            hit = series is not None and not (set(genres) & NOT_SERIES)
        else:
            hit = (any(g in genres for g in tgenres)
                   or any(w in gl for w in words)
                   or bool(rx and re.search(rx, n))
                   or bool(rx and series and re.search(rx, norm(series))))
        if hit:
            out.append(tid)
    return out


def is_pay_tv(name: str) -> bool:
    n = norm(name)
    if any(n == p or n.startswith(p + " ") for p in PAY_TV):
        return True
    words = n.split()
    while len(words) > 1 and words[-1] in {"west", "east", "hd", "pacific", "central"}:
        words.pop()
    return " ".join(words) in BROADCAST


def url_is_clean(url: str) -> bool:
    """Community streams must use a hostname on a default port."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    if u.scheme not in ("http", "https") or not u.hostname:
        return False
    if any(u.hostname == h or u.hostname.endswith("." + h) for h in BLOCKED_HOSTS):
        return False
    try:
        ipaddress.ip_address(u.hostname)
        return False
    except ValueError:
        pass
    return u.port in (None, 80, 443)


# --------------------------------------------------------------------------- #
# M3U parsing
# --------------------------------------------------------------------------- #

ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def parse_m3u(text: str) -> list[dict]:
    out, cur = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF"):
            head, _, title = line.partition(",")
            cur = dict(ATTR.findall(head))
            cur["title"] = title.strip()
        elif line and not line.startswith("#") and cur is not None:
            cur["url"] = line.split("|")[0].strip()
            out.append(cur)
            cur = None
    return out


def mjh_url_index() -> dict[str, str]:
    """Map provider channel ids to the stream URLs i.mjh.nz publishes."""
    index: dict[str, str] = {}
    for url in MJH_PLAYLISTS:
        data = fetch(url)
        if not data:
            continue
        items = parse_m3u(data.decode("utf-8", "replace"))
        for it in items:
            for key in (it.get("tvg-id", ""), it.get("channel-id", "")):
                if key:
                    index.setdefault(key, it["url"])
                    index.setdefault(key.split(".")[-1], it["url"])
            m = re.search(r"jmp2\.uk/[a-z]+-([^/?.]+)", it["url"])
            if m:
                index.setdefault(m.group(1), it["url"])
        print(f"  i.mjh.nz {url.rsplit('/', 2)[-2]}: {len(items)} entries")
    return index


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #

def titles(c: dict) -> list[str]:
    return [p[1] for p in c.get("programs", []) if len(p) > 1 and p[1]]


def src_pluto(index: dict[str, str]) -> list[Entry]:
    d = fetch_json(f"{MJH_RAW}/PlutoTV/.channels.json.gz")
    if not d:
        return []
    out = []
    for cid, c in d["regions"]["us"]["channels"].items():
        out.append(Entry("pluto", c["name"], index.get(cid, f"{JMP}/plu-{cid}.m3u8"),
                         c.get("logo", ""), c.get("art", ""), c.get("description", ""),
                         [c.get("group", "")], titles(c)))
    return out


def src_samsung(index: dict[str, str]) -> list[Entry]:
    d = fetch_json(f"{MJH_RAW}/SamsungTVPlus/.channels.json.gz")
    if not d:
        return []
    pattern = d.get("slug", "stvp-{id}")
    out = []
    for cid, c in d["regions"]["us"]["channels"].items():
        out.append(Entry("samsung", c["name"], index.get(cid, f"{JMP}/{pattern.format(id=cid)}"),
                         c.get("logo", ""), "", c.get("description", ""), [c.get("group", "")],
                         titles(c)))
    return out


def src_tubi(index: dict[str, str]) -> list[Entry]:
    data = fetch(TUBI)
    if not data:
        return []
    out = []
    for it in parse_m3u(data.decode("utf-8", "replace")):
        if urllib.parse.urlsplit(it["url"]).hostname != TUBI_HOST:
            continue  # only Tubi's own streams
        out.append(Entry("tubi", it["title"], it["url"], it.get("tvg-logo", ""), "", "",
                         [it.get("group-title", "")]))
    return out


def src_roku(index: dict[str, str]) -> list[Entry]:
    d = fetch_json(f"{MJH_RAW}/Roku/.channels.json.gz")
    if not d:
        return []
    out = []
    for cid, c in d["channels"].items():
        if cid in index:  # stream URL only known via the published playlist
            out.append(Entry("roku", c["name"], index[cid], c.get("logo", ""), c.get("fanart", ""),
                             c.get("description", ""), c.get("groups", []), titles(c)))
    return out


def src_plex(index: dict[str, str]) -> list[Entry]:
    d = fetch_json(f"{MJH_RAW}/Plex/.channels.json.gz")
    if not d:
        return []
    out = []
    for cid, c in d["channels"].items():
        if "us" in c.get("regions", []) and cid in index:
            out.append(Entry("plex", c["name"], index[cid], c.get("logo", ""), "", "", [], titles(c)))
    return out


def src_community(check: bool) -> list[Entry]:
    cats: dict[str, list[str]] = {}
    api = fetch_json(IPTV_ORG_CHANNELS)
    if api:
        for c in api:
            if c.get("is_nsfw"):
                cats[c["id"]] = ["__nsfw__"]
            else:
                cats[c["id"]] = c.get("categories", [])

    raw: list[Entry] = []
    data = fetch(IPTV_ORG_US)
    if data:
        for it in parse_m3u(data.decode("utf-8", "replace")):
            tid = it.get("tvg-id", "").split("@")[0]
            raw.append(Entry("iptvorg", it["title"], it["url"], it.get("tvg-logo", ""), "", "",
                             cats.get(tid, [])))
    data = fetch(FREE_TV)
    if data:
        for it in parse_m3u(data.decode("utf-8", "replace")):
            if it.get("group-title") == "USA" or it.get("tvg-country") == "US":
                raw.append(Entry("freetv", it.get("tvg-name") or it["title"], it["url"],
                                 it.get("tvg-logo", ""), "", "", []))

    kept, dropped = [], {"nsfw": 0, "pay_tv": 0, "url": 0, "dead": 0}
    for e in raw:
        if "__nsfw__" in e.groups:
            dropped["nsfw"] += 1
        elif is_pay_tv(e.name):
            dropped["pay_tv"] += 1
        elif not url_is_clean(e.url):
            dropped["url"] += 1
        else:
            kept.append(e)

    if check and kept:
        alive = probe_all([e.url for e in kept])
        dropped["dead"] = sum(1 for e in kept if e.url not in alive)
        kept = [e for e in kept if e.url in alive]

    print(f"  community: {len(raw)} raw -> {len(kept)} kept, dropped {dropped}")
    return kept


def probe(url: str) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status == 200 and b"#EXTM3U" in r.read(4096)
    except Exception:  # noqa: BLE001
        return False


def probe_all(urls: list[str]) -> set[str]:
    urls = list(dict.fromkeys(urls))
    with cf.ThreadPoolExecutor(max_workers=24) as pool:
        return {u for u, ok in zip(urls, pool.map(probe, urls)) if ok}


# --------------------------------------------------------------------------- #
# Merge and write
# --------------------------------------------------------------------------- #

def merge(entries: list[Entry]) -> list[Channel]:
    channels: dict[str, Channel] = {}
    for e in entries:
        k = merge_key(e.name)
        if not k:
            continue
        ch = channels.setdefault(k, Channel(k))
        if all(x.url != e.url for x in ch.entries):
            ch.entries.append(e)
    return list(channels.values())


def resolve_ids(channels: list[Channel]) -> dict[str, Channel]:
    out: dict[str, Channel] = {}
    for ch in channels:
        cid = slug(ch.key)
        if cid in out:  # slug collision after truncation
            cid = f"{cid}-{hashlib.sha1(ch.key.encode()).hexdigest()[:6]}"
        out[cid] = ch
    return out


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def build(base_url: str, check: bool) -> None:
    print("Indexing i.mjh.nz playlists")
    index = mjh_url_index()
    print("Loading sources")
    entries: list[Entry] = []
    for fn in (src_pluto, src_samsung, src_tubi, src_roku, src_plex):
        got = fn(index)
        print(f"  {fn.__name__[4:]}: {len(got)}")
        entries += got
    entries += src_community(check)

    channels = resolve_ids(merge(entries))
    if len(channels) < 200:
        sys.exit(f"Only {len(channels)} channels built; refusing to overwrite the addon.")

    metas = []
    for cid, ch in channels.items():
        p = ch.primary
        groups = [g for e in ch.entries for g in e.groups if g]
        genres = genre_for(groups, p.name)
        providers = sorted({e.provider for e in ch.entries}, key=lambda x: PROVIDERS[x][1])
        avail = "Available on: " + ", ".join(PROVIDERS[x][0] for x in providers)
        desc = ch.best("description")
        series, shows = lineup(ch)
        open_stream = any(not e.needs_us for e in ch.entries)
        themes = themes_for(groups, p.name, genres, len(providers), series, open_stream)
        extra_lines = []
        if series and "series" in themes:
            extra_lines.append(f"24/7: {series}")
        elif shows:
            extra_lines.append("Shows: " + ", ".join(shows))
        extra_lines.append(avail)
        tail = "\n".join(extra_lines)
        logo = ch.best("logo") or f"{base_url}/public/logo.png"
        meta = {
            "id": cid,
            "type": "tv",
            "name": clean_display(p.name),
            "poster": logo,
            "posterShape": "square",
            "logo": logo,
            "genres": genres,
            "description": f"{desc}\n\n{tail}" if desc else tail,
        }
        bg = ch.best("background")
        if bg:
            meta["background"] = bg
        streams = [
            {
                "name": PROVIDERS[e.provider][0],
                "description": (f"{clean_display(e.name)}\n"
                                + ("🇺🇸 US only, needs a US VPN" if e.needs_us else "✅ No VPN needed")),
                "url": e.url,
                "behaviorHints": {"notWebReady": True},
            }
            for e in sorted(ch.entries, key=lambda e: (e.needs_us, STREAM_ORDER.index(e.provider)))
        ]
        metas.append((meta, streams, len(providers), themes))

    # In every row: channels that play without a VPN first, then the most widely
    # carried, then alphabetical.
    metas.sort(key=lambda m: ("novpn" not in m[3], -m[2], m[0]["name"].lower()))

    out = ROOT
    for d in ("catalog", "meta", "stream"):
        shutil.rmtree(out / d, ignore_errors=True)

    for meta, streams, *_ in metas:
        write_json(out / "meta" / "tv" / f"{meta['id']}.json", {"meta": meta})
        write_json(out / "stream" / "tv" / f"{meta['id']}.json", {"streams": streams})

    previews = [{k: m[k] for k in ("id", "type", "name", "poster", "posterShape", "genres")}
                for m, *_ in metas]
    theme_of = {m["id"]: t for m, _, _, t in metas}
    used_genres = [g for g in GENRES if any(g in m["genres"] for m in previews)]

    def write_pages(catalog: str, items: list[dict], genre: str | None = None) -> None:
        for skip in range(0, max(len(items), 1), PAGE_SIZE):
            page = {"metas": items[skip:skip + PAGE_SIZE]}
            extras = []
            if genre:
                extras.append(f"genre={genre}")
            if skip:
                extras.append(f"skip={skip}")
            name = f"{catalog}.json" if not extras else f"{catalog}/" + "&".join(extras) + ".json"
            write_json(out / "catalog" / "tv" / name, page)

    write_pages("all", previews)
    for g in used_genres:
        write_pages("all", [m for m in previews if g in m["genres"]], g)

    theme_catalogs = []
    theme_counts = {}
    for tid, tname, *_ in THEMES:
        items = [m for m in previews if tid in theme_of[m["id"]]]
        if len(items) < 5:  # too thin to deserve a row
            continue
        write_pages(tid, items)
        theme_counts[tname] = len(items)
        theme_catalogs.append({"type": "tv", "id": tid, "name": tname,
                               "extra": [{"name": "skip", "isRequired": False}]})

    manifest = {
        "id": "community.usa-free-tv",
        "version": "1.0.0",
        "name": "USA Free TV",
        "description": (f"{len(metas)} free, legal US live channels from Pluto TV, Samsung TV Plus, "
                        "Tubi, The Roku Channel, Plex and curated public streams. One entry per channel, "
                        "with every available source as a backup stream."),
        "logo": f"{base_url}/public/logo.png",
        "resources": ["catalog", "meta", "stream"],
        "types": ["tv"],
        "idPrefixes": [ID_PREFIX],
        "catalogs": theme_catalogs + [{
            "type": "tv",
            "id": "all",
            "name": "All Channels",
            "extra": [
                {"name": "genre", "isRequired": False, "options": used_genres},
                {"name": "skip", "isRequired": False},
            ],
        }],
        "behaviorHints": {"configurable": False},
    }
    old = ROOT / "manifest.json"
    if old.exists():
        prev = json.loads(old.read_text())
        same = {k: v for k, v in prev.items() if k != "version"} == {k: v for k, v in manifest.items() if k != "version"}
        manifest["version"] = prev["version"] if same else bump(prev.get("version", "1.0.0"))
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    by_provider = {p: sum(1 for _, s, *_ in metas if any(x["name"] == PROVIDERS[p][0] for x in s)) for p in PROVIDERS}
    stats = {
        "channels": len(metas),
        "streams": sum(len(s) for _, s, *_ in metas),
        "multi_source_channels": sum(1 for _, _, n, _ in metas if n > 1),
        "channels_by_provider": by_provider,
        "channels_by_genre": {g: sum(1 for m in previews if g in m["genres"]) for g in used_genres},
        "channels_by_theme": theme_counts,
    }
    (ROOT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


def bump(v: str) -> str:
    major, minor, patch = (int(x) for x in v.split("."))
    return f"{major}.{minor}.{patch + 1}"


def default_base_url() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "OWNER/usa-free-tv")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=default_base_url())
    ap.add_argument("--check", action="store_true", help="probe community streams and drop dead ones")
    args = ap.parse_args()
    build(args.base_url.rstrip("/"), args.check)
