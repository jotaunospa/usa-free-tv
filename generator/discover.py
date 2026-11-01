#!/usr/bin/env python3
"""Discovery only: list the channels other free services carry, WITHOUT touching the
published catalog. Writes data/discovery.json so the new channels can be reviewed
(and pay-TV ones excluded) before any of them is added to the addon.

Run from the GitHub Action (US servers). Each source is independent; one failing
does not stop the others.
"""
import json
import re
import sys
import uuid
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402  (main-guarded, safe to import)

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def get_json(url, headers=None, timeout=45):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def vizio():
    j = get_json("https://watchfreeplus-epg-prod.smartcasttv.com/api/channels", {"User-Agent": "okhttp/4.12.0"})
    for c in j.get("channels") or []:
        name = (c.get("channelName") or "").strip()
        if not name or str(c.get("channelId", "")).upper().startswith("FEATURED"):
            continue
        yield {"id": str(c.get("channelId")), "name": name, "category": c.get("category"),
               "gated": bool(c.get("tokenUrl"))}


def lg():
    h = {"Origin": "https://lgchannels.com", "Referer": "https://lgchannels.com/", "x-device-country": "US",
         "x-device-language": "en", "x-device-type": "WEB"}
    j = get_json("https://api.lgchannels.com/api/v1.0/schedulelist", h)
    seen = set()
    for cat in j.get("categories", []):
        for c in cat.get("channels", []):
            cid, name = str(c.get("channelId") or ""), (c.get("channelName") or "").strip()
            if cid and name and cid not in seen:
                seen.add(cid)
                yield {"id": cid, "name": name, "category": cat.get("categoryName") or c.get("channelGenreName")}


def xumo():
    u = ("https://valencia-app-mds.xumo.com/v2/proxy/channels/list/10006.json?sort=hybrid&geoId=2f08a9b3"
         f"&deviceId={uuid.uuid4()}&ifaId={uuid.uuid4()}")
    j = get_json(u)
    ch = j.get("channel")
    items = (ch.get("item") if isinstance(ch, dict) else None) or j.get("items") or []
    for it in items:
        if not isinstance(it, dict):
            continue
        guid = (it.get("guid") or {}).get("value") if isinstance(it.get("guid"), dict) else None
        name = (it.get("title") or "").strip()
        live = str((it.get("properties") or {}).get("is_live", "")).lower() == "true"
        if guid and name and live:
            g = it.get("genre")
            cat = (g[0].get("value") if isinstance(g, list) and g and isinstance(g[0], dict) else None)
            yield {"id": str(guid), "name": name, "category": cat}


def stirr():
    j = get_json("https://stirr.com/api/videos/list/?categories=all_categories&content_type=4&no_limit=true")
    seen, stack = set(), [j]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if "videoid" in o and "title" in o:
                vid = str(o["videoid"])
                if vid not in seen:
                    seen.add(vid)
                    yield {"id": vid, "name": str(o["title"]).strip(), "category": None}
                continue
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)


SOURCES = {"vizio": vizio, "lg": lg, "xumo": xumo, "stirr": stirr}


def main():
    idx = json.loads((ROOT / "data" / "index.json").read_text())
    f = idx["fields"]
    known = {build.norm(row[f.index("name")]) for row in idx["channels"]}
    out, status = [], {}
    for src, fn in SOURCES.items():
        try:
            rows = list(fn())
            status[src] = {"ok": True, "channels": len(rows)}
        except Exception as e:  # noqa: BLE001
            status[src] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
            print(f"[{src}] FAILED: {e}", file=sys.stderr)
            continue
        for r in rows:
            r["src"] = src
            r["pay"] = build.is_pay_tv(r["name"])
            r["known"] = build.norm(r["name"]) in known
            out.append(r)
        print(f"[{src}] {len(rows)} channels")
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "discovery.json").write_text(
        json.dumps({"sources": status, "channels": out}, ensure_ascii=False, separators=(",", ":")))
    new = [r for r in out if not r["known"] and not r["pay"]]
    print(f"total {len(out)} | new & free-looking {len(new)} | pay-TV {sum(r['pay'] for r in out)}")


if __name__ == "__main__":
    main()
