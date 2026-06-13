# Media Tracker

[Leer en Español](README.es.md)

**Media Tracker** is my personal log of movies, series and games — a generated
Hugo site built from my Obsidian vault.

> **Looking to build your own?**
> This repo is my private content, not a template.
> Use [**mediatracker-starter**](https://github.com/christt105/mediatracker-starter)
> to spin up a fresh site in one click, or check the
> [**hugo-mediatracker-theme**](https://github.com/christt105/hugo-mediatracker-theme)
> docs for all configuration options.

## How it works

Content lives in Obsidian. Entries are created with my
[hugo-mediatracker-plugin](https://github.com/christt105/hugo-mediatracker-plugin),
which pulls metadata and artwork from TMDB, TheTVDB, IGDB, Steam and SteamGridDB.
A migration script (`scripts/migration.py`) then converts those Obsidian notes
into Hugo page bundles under `content/`. The `content/` directory is therefore
**generated** — manual edits will be overwritten on the next run.

```
Obsidian vault  ←── notes created by hugo-mediatracker-plugin
      │
      ▼
scripts/migration.py
      │
      ▼
content/  ←── generated, do not edit by hand
      │
      ▼
hugo build → GitHub Actions → GitHub Pages
```

## Stack

| Tool | Role |
|------|------|
| [Hugo](https://gohugo.io/) | Static site generator |
| [hugo-mediatracker-theme](https://github.com/christt105/hugo-mediatracker-theme) | Theme (Hugo Module) |
| [Obsidian](https://obsidian.md/) | Note editing / source of truth |
| [hugo-mediatracker-plugin](https://github.com/christt105/hugo-mediatracker-plugin) | Creates entries in Obsidian (TMDB / TheTVDB / IGDB / Steam / SteamGridDB) |
| GitHub Actions | Build & deploy to Pages |

## Running locally

```bash
hugo server
```

Requires Hugo extended + Go (for modules). The theme is fetched automatically
via `go.mod`.

## RSS feeds

| Feed | URL |
|------|-----|
| All content | `/index.xml` |
| Finished items | `/finished.xml` |
