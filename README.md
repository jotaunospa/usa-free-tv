# USA Free TV

A static Stremio addon with free, legal US live channels. Each channel appears
once; when several services carry it, every source is offered as a backup stream.

Hosted entirely on GitHub raw URLs — no server. A GitHub Action rebuilds the
channel list every day.

## Install

```
stremio://raw.githubusercontent.com/jotaunospa/usa-free-tv/main/manifest.json
```

Or paste `https://raw.githubusercontent.com/jotaunospa/usa-free-tv/main/manifest.json`
into Stremio → Addons → search box.

## Themed rows

The addon adds rows to the Stremio home screen: Popular Free Channels, Series 24/7,
News 24/7, Sports, Movies, True Crime, Comedy, Kids & Family, Anime & Gaming,
Game Shows, History, Science & Nature (documentaries plus the official FAST channels
of History, Discovery, Smithsonian, BBC Earth...), Food & Home,
Westerns & Classic TV, Music and Local News. "All Channels" in Discover has a genre filter.

## English only

Spanish-language and dubbed channels are left out ("CSI en español", "Pluto TV Cine",
Telemundo, ViX, Roku's Spanish dubs of Z Nation or Andromeda...). A channel is dropped
when its provider category, its name, its iptv-org language or the wording of its
description and schedule show it is not in English. Every build writes the dropped
channels to `data/non_english.json` so the filter can be audited.

Themes come from each service's own categories and from the EPG: a channel whose
schedule repeats the show it is named after joins **Series 24/7**, and every channel
description lists the shows it airs most. Rows with fewer than 5 channels are hidden.
Edit `THEMES` in `generator/build.py` to add or change rows.

## Sources

| Source | What it adds |
|---|---|
| Pluto TV | Official FAST channels, via [i.mjh.nz](https://i.mjh.nz) channel data |
| Samsung TV Plus | Official FAST channels, via i.mjh.nz |
| Tubi | Official Tubi live channels, via the daily [tubi-scraper](https://github.com/BuddyChewChew/tubi-scraper) playlist (Tubi CDN URLs only) |
| The Roku Channel | Official FAST channels, via i.mjh.nz channel data |
| Plex | Official FAST channels (US lineup), via i.mjh.nz channel data |
| [iptv-org](https://github.com/iptv-org/iptv) | Publicly available US streams (local stations, public access, indie networks) |
| [Free-TV](https://github.com/Free-TV/IPTV) | Curated free US channels |

Community playlists (iptv-org, Free-TV) are filtered before publishing:

- Pay-TV networks and bare over-the-air network feeds (HBO, ESPN, "NBC West"...) are dropped.
- Streams on bare IP addresses, non-standard ports or known reseller hosts are dropped.
- Each remaining stream is probed daily; dead ones are removed.

FAST streams are geo-restricted by their services and generally play only from a US connection.

## Configurable version (favorites)

`service/` is a small Vercel app that turns the same daily data into a personal addon:

- A configure page where anyone picks where they watch from, the language (English only,
  or English plus Spanish and other languages), which rows to show, and their favorite
  channels. No account: saving returns a 10-character code and an install link.
- A **⭐ My Favorites** row first on the home screen. Favorites edited later show up on
  the TV by themselves; changing language, region or rows needs a reinstall, and the page
  says so.
- Search inside Stremio (channel names carry their shows, so "South Park" works).

It reads `data/index.json` and the meta/stream files from this repo, so the GitHub Action
stays the only thing that builds channel data. Setups are stored in Upstash Redis.

| Route | What it serves |
|---|---|
| `/` or `/{code}/configure` | Configure page |
| `/{code}/manifest.json` | Personal addon |
| `/manifest.json`, `/p-en/…`, `/p-all/…`, `/p-us/…` | Ready-made setups, no code needed |
| `/api/prefs` | Read (GET `?code=`) and save (POST) a setup |

### Deploy (free)

1. On [vercel.com](https://vercel.com), sign up with GitHub (Hobby plan).
2. **Add New → Project**, import this repo. Set **Root Directory** to `service`,
   Framework Preset **Other**, no build command. Deploy.
3. In the project, **Storage → Create Database → Upstash for Redis** (free plan), and
   connect it to the project. It adds the `KV_REST_API_URL` / `KV_REST_API_TOKEN`
   variables. Redeploy once so the function picks them up.
4. Open `https://<your-project>.vercel.app`.

Optional: set `DATA_BASE` if the data lives somewhere other than
`https://raw.githubusercontent.com/jotaunospa/usa-free-tv/main`. In Settings → Build and
Deployment, enable "Skip deployments when there are no changes to the root directory" so
the daily data commits don't redeploy the service.

### Run locally

```
python -m http.server 8001          # from the repo root, serves the data
cd service && DATA_BASE=http://localhost:8001 node dev-server.js
```

Without Redis credentials, setups are kept in memory.

## Build locally

```
python generator/build.py --base-url https://raw.githubusercontent.com/jotaunospa/usa-free-tv/main
python generator/build.py --check   # also probe community streams
```

Standard library only (Python 3.10+). Output: `manifest.json`, `catalog/`, `meta/`,
`stream/`, `stats.json`.

## Routes

| Stremio resource | Path |
|---|---|
| Manifest | `/manifest.json` |
| Catalog | `/catalog/tv/all.json`, `/catalog/tv/all/skip={n}.json` |
| Catalog by genre | `/catalog/tv/all/genre={Genre}.json`, `...&skip={n}.json` |
| Meta | `/meta/tv/{id}.json` |
| Stream | `/stream/tv/{id}.json` |

Inspired by [yowmamasita/usa-tv-next](https://github.com/yowmamasita/usa-tv-next).
