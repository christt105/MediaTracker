# Media Tracker — Improvement Plan

> Status: proposal / draft. Written 2026-06-05.
> Goal: make the project reusable by others, generalize media types, unify
> styling, add search, fix social previews, and improve i18n + RSS.

---

## 1. Current state (analysis)

**Architecture**
- Single Hugo site. Theme `hugo-blog-awesome` is pulled as a **Hugo Module**
  (`go.mod`, `v1.21.0`). Customization is done entirely through **layout
  overrides** in this repo's `layouts/`, so the theme itself is stock.
- A local clone exists at `../hugo-blog-awesome`, **but it is not wired into the
  build** (no `replace` directive in `go.mod`). The build uses the published
  module. The clone is effectively a reference copy. → Worth clarifying/removing
  to avoid confusion.
- `go.mod` module path is the placeholder `github.com/USER/REPO`, and `baseURL`
  is hardcoded to `christt105.github.io/MediaTracker`. Both block reuse.
- Content flows Obsidian → `scripts/migration.py` → `content/` (treated as
  generated/immutable) → GitHub Actions builds & deploys to Pages.

**Content model** (page bundles, one `index.md` + cover/banner resources each):
- `type`: `movie | tv | season | videogame`
- `status`: Spanish literals `Acabado | Pausado | Abandonado | En Curso | Sin Empezar`
- `rating`: `1`–`7` (mapped to label/color/icon in `data/ratings.yml`)
- dates: `date` (completed), `release_date`; `rewatches: []`
- `image`, `banner_image`, `genres`, `tags`, `platforms`, `developer`,
  `tmdb_id`, `steam_appid`, `igdb_id`
- relations: `temporadas`/`seasons`, `series`/`serie`
- Counts today: movies 70, tv 57, seasons 31, games 80.

**Confirmed pain points**
1. **Type hardcoding.** The set `("season" "movie" "tv" "videogame")` is repeated
   in `index.html`, `index.json`, `_default/list.html`; `mainSections` and the
   menu are hardcoded; `media-card.html` and `single.html` hardcode per-type
   icons and season/series behavior; `scripts/migration.py` hardcodes the section
   map. **Adding "books" means editing ~8 files.**
2. **Template duplication.** `index.html` and `_default/list.html` share ~90% of
   their logic (in-progress / paused+abandoned / rewatch expansion / sort /
   year-grouping) as two divergent copies (home uses a JS toggle, list uses
   `<details>`). This is the "different pages for main vs type lists" problem and
   the source of style drift.
3. **Status coupling.** Spanish status strings appear as literals in 4 layout
   files (20 occurrences). Logic compares against `"Acabado"` etc., which is
   fragile for both i18n and adding new states.
4. **No search.** There is no search UI. (`index.json` already exists and is a
   ready-made search index.)
5. **Broken social previews.** Theme `meta/standard.html` emits
   `og:image = .Params.image | absURL`, but `image` is a *page-bundle-relative*
   resource filename (e.g. `tmdb_xxx.jpg`), so `absURL` produces a URL relative to
   the site root that **does not exist**. No `twitter:card=summary_large_image`.
   No per-entry OG override. → Cards show no cover.
6. **Thin entry preview.** The `overview` field is stored in frontmatter but
   **never rendered** on the single page or in meta. Lots of data (genres,
   platforms shown; overview, developer commented out) is underused.
7. **i18n is partial.** Single language (`es`). `i18n/es.yaml` covers a few type
   labels only. Status terms are baked into content/logic.
8. **RSS quality.** Custom feeds emit an invalid `<status>` element; no
   `media:content`/thumbnail namespace; only home + "acabados" feeds; per-type
   feeds rely on default behavior.

---

## 2. Target architecture: split into three repos

Adopt the standard **Hugo Modules** composition pattern.

```
hugo-mediatracker-theme   (NEW)  → reusable theme/module
mediatracker-starter      (NEW)  → "Use this template" minimal site
MediaTracker              (THIS) → personal content + Obsidian pipeline
```

### 2.1 `hugo-mediatracker-theme` (the reusable part)
Move into a standalone module repo:
- `layouts/` (all current overrides, generalized — see §3)
- `assets/sass/` (`_custom.scss`, `year-nav-styles.scss`)
- `i18n/`, `archetypes/`, `data/ratings.yml`, default `data/media_types.yml`
- partials: `media-card`, `year-nav*`, `random-hero-banner`, custom head, etc.
- `theme.toml`, `go.mod` with a **real module path**.
- It **imports `hugo-blog-awesome`** as its own module dependency (composition),
  so upstream theme updates still flow in.

Consumers add one block:
```toml
[module]
  [[module.imports]]
    path = "github.com/christt105/hugo-mediatracker-theme"
```

### 2.2 `mediatracker-starter` (the on-ramp)
- GitHub "template repository" (one-click "Use this template").
- Imports the theme module, ships ~3 example entries per type, a clean
  `hugo.toml`, and a short README ("add a markdown file, run `hugo server`").
- This is what you point people to instead of the complex personal repo.

### 2.3 `MediaTracker` (this repo, slimmed)
- Keeps: `content/`, `hugo.toml` (personal config + menu), `scripts/migration.py`,
  the deploy workflow, personal `data` overrides.
- Drops the vendored layouts/assets (now provided by the theme module).
- Local theme dev: use a `go.mod` `replace` (or `hugo mod` workspace) pointing at
  `../hugo-mediatracker-theme` so you can edit the theme and preview instantly.

> Migration is low-risk because customization is already isolated in `layouts/`
> and `assets/`. The move is mostly relocating files + setting module paths.

---

## 3. Generalize media types (kill the hardcoding)

Introduce a single source of truth: **`data/media_types.yml`**.

```yaml
movie:
  section: movies
  label: { es: Película, en: Movie }
  icon: "fas fa-film"
  weight: 20
tv:
  section: tv
  label: { es: Serie, en: Series }
  icon: "fas fa-tv"
  children: season          # tv owns seasons
  weight: 30
season:
  section: seasons
  label: { es: Temporada, en: Season }
  icon: "fas fa-tv"
  parent: tv
  hidden_in_lists: true     # seasons roll up under their series
videogame:
  section: games
  label: { es: Videojuego, en: Video game }
  icon: "fas fa-gamepad"
  fields: [platforms, developer]
  weight: 40
book:                       # adding a type = adding a block here
  section: books
  label: { es: Libro, en: Book }
  icon: "fas fa-book"
  fields: [author, pages]
  weight: 25
```

Then:
- Templates derive the type set from `site.Data.media_types` (no literal slices).
- `media-card.html` looks up the icon/label from the type entry; remove the `if eq
  type ...` ladder.
- `single.html` renders type-specific fields from `fields:` generically (label +
  value), and parent/child relations from `parent`/`children` instead of the
  hardcoded `serie`/`temporadas` blocks.
- The menu can be generated from the type entries (`weight`, `label`).
- `scripts/migration.py` reads the same mapping (or a small shared JSON) so
  section_map isn't a second copy.

**Result:** adding *Books* = one data block + content. No template edits.

### Normalize status to canonical keys
Change status to canonical keys and translate for display:

```
finished | in_progress | paused | dropped | not_started
```

Map current Spanish literals during migration. Display labels come from `i18n`.
This removes the 20 hardcoded literals and makes both i18n and new states clean.
(Keep a back-compat mapping so existing content keeps working during transition.)

---

## 4. Unify the listing (one template + filters + search)

**Collapse `index.html` + `list.html` into one shared partial.**
- Create `partials/media-collection.html` that takes a page slice and renders the
  in-progress / completed-by-year / paused+abandoned sections (the logic that is
  currently duplicated). Home and any section page both call it.
- Pick **one** "hidden section" UX (recommend `<details>`, no JS) and delete the
  divergent copy.

**Replace per-type pages with filters on the main page.**
- The home page becomes the single browse surface with a **filter bar**: type,
  status, rating, genre, platform, year — plus a **search box**.
- Filtering/search is client-side over the existing **`index.json`** (extend it
  with `genres`, `platforms`, `rating`, `year`, `url`). Use **Fuse.js** (tiny,
  works directly off `index.json`) for fuzzy search; chips for facet filters.
- Keep `/movies`, `/tv`, ... as deep links that just pre-apply a filter
  (`/?type=movie`) so existing URLs/menu still work, or 301 them.
- Alternative for scale/robustness: **Pagefind** (post-build static index, no
  hand-maintained JSON, search highlighting). Heavier to wire (extra CI step).
  Recommend Fuse.js first since `index.json` already exists.

**Result:** one styled surface, no drift, search + filters, fewer templates.

---

## 5. Fix social previews + richer entry pages

Add a theme **`custom-head.html`** (or `head` override) that, on single pages,
emits correct tags using the *resized resource Permalink* (absolute):

```go-html-template
{{ with .Resources.GetMatch .Params.image }}
  {{ $og := .Resize "600x webp" }}
  <meta property="og:image" content="{{ $og.Permalink }}">
  <meta name="twitter:image" content="{{ $og.Permalink }}">
{{ end }}
<meta name="twitter:card" content="summary_large_image">
<meta property="og:type" content="article">
<meta property="og:title" content="{{ .Title }}">
<meta property="og:description"
      content="{{ .Params.overview | default .Params.description | truncate 200 }}">
```

Also enrich the **single page body** (currently it only renders `.Content`):
- Render `overview` (it's captured but never shown).
- Show rating label, status label, genres, release date, type-specific fields.
- Optional structured data (`schema.org/Movie`/`VideoGame`/`Book`) for rich
  results.

This fixes "no cover when shared" and "show more data of the entry" together.

---

## 6. Multilingual

Separate two concerns:
- **UI i18n (do first, cheap):** move all visible strings (menu, "En Curso",
  "Completado", status labels, type labels, "No recuerdo cuándo", etc.) into
  `i18n/{es,en}.yaml`. Configure `[languages]` with `es` default + `en`. The
  status/type normalization in §3 is the enabler.
- **Content i18n (optional, expensive):** entries are generated in Spanish from
  Obsidian. Per-entry translation is a lot of work; recommend UI-multilingual now
  and leave content single-language (ES) with `hreflang` correct. If wanted
  later, the migration script could populate `overview`/title translations from
  TMDB/IGDB localized data.

---

## 7. RSS improvements

- Remove the invalid `<status>` element (not part of RSS spec). If you want it,
  use a namespaced custom element or put it in the description.
- Add `xmlns:media` and emit `<media:content>` / `<media:thumbnail>` for covers
  so feed readers show artwork reliably (enclosure stays for podcatcher-style
  readers).
- Auto-generate **per-type feeds** (and the "finished" feed) from the type data
  instead of the bespoke `RSS_ACABADO` output format — one parameterized RSS
  template keyed by a filter.
- Consider a feed that includes the full review (`overview` + `.Content`) for
  finished items, separate from a lightweight "activity" feed.
- Factor the shared channel boilerplate (duplicated between `index.rss.xml` and
  `index.acabado.xml`) into one partial.

---

## 8. Suggested sequencing

**Phase 0 — Quick wins (no restructure, high value)**
- [ ] Fix OG/Twitter image + `summary_large_image` (§5). *(broken today)*
- [ ] Render `overview` on single pages (§5).
- [ ] De-duplicate `index.html`/`list.html` into one shared partial (§4).
- [ ] Remove invalid `<status>` from RSS; add `media:thumbnail` (§7).

**Phase 1 — Generalize**
- [ ] `data/media_types.yml` + drive templates/menu/migration from it (§3).
- [ ] Normalize `status` to canonical keys with a compat map (§3).
- [ ] Add **Books** end-to-end as the proof that types are now data-driven.

**Phase 2 — Search & filters**
- [ ] Extend `index.json`; add Fuse.js search + facet filter bar on home (§4).
- [ ] Turn `/movies` etc. into pre-filtered deep links (§4).

**Phase 3 — Split repos**
- [ ] Extract `hugo-mediatracker-theme` module (real path), import upstream theme.
- [ ] Create `mediatracker-starter` template repo.
- [ ] Slim this repo to content + pipeline; use `replace`/workspace for theme dev.

**Phase 4 — i18n polish**
- [ ] Move all UI strings to `i18n/{es,en}.yaml`; enable `en` language (§6).

---

## 9. Extra improvement ideas (beyond the original list)

- **Stats / dashboard page:** counts per year, ratings distribution, hours
  played (Steam), genre breakdown — fun and cheap from existing frontmatter.
- **"Currently / recently" OG default image** for the home and section pages
  (site `ogimage`) so non-entry shares also look good.
- **Genre & platform taxonomy pages** (Hugo taxonomies) — better than ad-hoc
  filtering for SEO and browsing; the filter UI can sit on top.
- **Validate frontmatter in CI** (a small script) so a bad migration fails the
  build instead of silently shipping broken cards.
- **Pin the theme module version** and add `hugo mod get -u` to a scheduled
  workflow with a PR, so updates are reviewable.
- **Clean `category: '[[...]]'`** wikilinks in migration (today only
  `serie/temporadas/related` are cleaned; `category` still ships `[[Películas]]`).
- **Image performance:** you already resize to webp — add `loading="lazy"`
  everywhere (cards have it; check banners) and generate low-res LQIP/blur
  placeholders for the grid.
- **Accessibility pass:** alt text is the title (good); ensure rating badges and
  platform icons have `aria-label`s, and color isn't the only signal for status.
- **Sitemap & robots** sanity for the new multi-section structure.
- **`go.mod` real module path + configurable `baseURL`** via `HUGO_BASEURL`/CI so
  forks deploy without editing tracked files.
```
