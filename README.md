# USA Free TV

A static Stremio addon with free, legal US live channels. Each channel appears
once; when several services carry it, every source is offered as a backup stream.

Hosted entirely on GitHub raw URLs — no server. A GitHub Action rebuilds the
channel list every day.

## Install / Instalar

**Manifest URL** (copy and paste / copiar y pegar):

```
https://raw.githubusercontent.com/jotaunospa/usa-free-tv/main/manifest.json
```

**Stremio desktop, TV or mobile app**

1. Open Stremio → **Addons** (puzzle icon).
2. Paste the manifest URL above into the search box at the top.
3. Click **Install**.

**Stremio Web** — open this link and click **Install**:

```
https://web.stremio.com/#/addons?addon=https%3A%2F%2Fraw.githubusercontent.com%2Fjotaunospa%2Fusa-free-tv%2Fmain%2Fmanifest.json
```

**One-click link** (opens the installed Stremio app directly):

```
stremio://raw.githubusercontent.com/jotaunospa/usa-free-tv/main/manifest.json
```

After installing, the themed rows appear on the Stremio **Board** (home) and every
channel is also under **Discover → TV → USA Free TV**.

> FAST services (Pluto TV, Samsung TV Plus, Tubi, Roku, Plex) are geo-restricted to
> the US. Outside the US, streams may need a US connection to play.

## Themed rows

The addon adds rows to the Stremio home screen: Popular Free Channels, Series 24/7,
News 24/7, Sports, Movies, True Crime, Comedy, Kids & Family, Anime & Gaming,
Game Shows, History, Science & Nature (documentaries plus the official FAST channels
of History, Discovery, Smithsonian, BBC Earth...), Food & Home,
Westerns & Classic TV, Music, En Español and Local News. "All Channels" in Discover has a genre filter.

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
| The Roku Channel | Official FAST channels, via i.mjh.nz playlists |
| Plex | Official FAST channels, via i.mjh.nz playlists |
| [iptv-org](https://github.com/iptv-org/iptv) | Publicly available US streams (local stations, public access, indie networks) |
| [Free-TV](https://github.com/Free-TV/IPTV) | Curated free US channels |

Community playlists (iptv-org, Free-TV) are filtered before publishing:

- Pay-TV networks and bare over-the-air network feeds (HBO, ESPN, "NBC West"...) are dropped.
- Streams on bare IP addresses, non-standard ports or known reseller hosts are dropped.
- Each remaining stream is probed daily; dead ones are removed.

FAST streams are geo-restricted by their services and generally play only from a US connection.

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
