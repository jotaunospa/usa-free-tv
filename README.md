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

The addon adds rows to the Stremio home screen: History & Discovery (official FAST
channels from History, Discovery, Smithsonian, BBC Earth...), Popular Free Channels, Series 24/7,
News 24/7, Sports, Movies, True Crime, Comedy, Kids & Family, Anime & Gaming,
Game Shows, Nature/History/Science, Food & Home, Westerns & Classic TV, Music,
En Español and Local News. "All Channels" in Discover has a genre filter.

Themes come from each service's own categories and from the EPG: a channel whose
schedule repeats the show it is named after joins **Series 24/7**, and every channel
description lists the shows it airs most. Rows with fewer than 5 channels are hidden.
Edit `THEMES` in `generator/build.py` to add or change rows.

## Sources

| Source | What it adds |
|---|---|
| Pluto TV | Official FAST channels, via [i.mjh.nz](https://i.mjh.nz) channel data |
| Samsung TV Plus | Official FAST channels, via i.mjh.nz |
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
