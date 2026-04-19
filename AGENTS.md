# AGENTS.md

Handoff notes for automated contributors.

## Project summary

- Python scrapers build raw source DBs:
  - [data/super_lig.db](data/super_lig.db) from Transfermarkt
  - [data/sofascore_super_lig.db](data/sofascore_super_lig.db) from SofaScore
- [site_builder.py](site_builder.py) adapts one source into the canonical frontend DB at [data/site.db](data/site.db)
- ReScript frontend in [frontend/](frontend/) reads the canonical DB directly in the browser via `sql.js`
- GitHub Pages workflow in [.github/workflows/deploy.yml](.github/workflows/deploy.yml) deploys to `super-lig.arda.tr`
- The root [CNAME](CNAME) file is the source of truth for the custom domain
- GitHub Pages is deployed via the official Pages artifact actions, not via a `gh-pages` branch

There is no production backend.

## Product surface

- Dashboard / season archive
- Season detail
- Team archive with season tabs
- Team squad tables and assist leaders
- Player archive with season tabs
- Team `kollandığı maçlar` / `propped up games` drill-down
- Team `VAR swing wins` drill-down
- Match timeline
- TR / EN language toggle
- Hash-based routing (Pages-compatible)

## Hard constraints

### Frontend stays in ReScript

- Change UI behavior in `.res` files
- `frontend/src/*.res.js` is generated and gitignored — never hand-edit

### Hash routing is intentional

Use `#/`, `#/season/...`, `#/team/...`, `#/team/.../propped-up`,
`#/team/.../var-swing-wins`, `#/player/...`, `#/match/...`. Do not switch to history
routing unless the deployment target changes.

### DB is embedded into the static site

Frontend builds depend on:

- [data/site.db](data/site.db)
- [site_builder.py](site_builder.py)
- [frontend/scripts/sync-public-assets.mjs](frontend/scripts/sync-public-assets.mjs)
- `frontend/public/super_lig.db` (copied on build)
- `frontend/public/sql-wasm.wasm` (copied on build)

Update the sync script and docs if you move any of these.

### sql.js import is fragile

[frontend/src/SqlHelper.js](frontend/src/SqlHelper.js) imports
`sql.js/dist/sql-wasm.js` explicitly. A bare `sql.js` import previously caused
a Vite/browser export mismatch — do not "simplify" it. Asset paths resolve via
`import.meta.env.BASE_URL` so sub-path deployments work.

## Key files

Data layer:

- [db.py](db.py) — schema + indexes + FK pragma
- [scraper.py](scraper.py) — discovery, parsing, persistence
- [sofascore_db.py](sofascore_db.py) — raw SofaScore schema
- [sofascore_scraper.py](sofascore_scraper.py) — SofaScore discovery, parsing, persistence
- [site_db.py](site_db.py) — canonical frontend DB schema
- [site_builder.py](site_builder.py) — source adapter builder
- [update_site.py](update_site.py) — one-command SofaScore refresh + canonical rebuild
- [data/super_lig.db](data/super_lig.db)
- [data/sofascore_super_lig.db](data/sofascore_super_lig.db)
- [data/site.db](data/site.db)

Frontend shell:

- [frontend/src/App.res](frontend/src/App.res)
- [frontend/src/Route.res](frontend/src/Route.res)
- [frontend/src/Locale.res](frontend/src/Locale.res)
- [frontend/src/Copy.res](frontend/src/Copy.res)

Frontend pages:

- [frontend/src/Dashboard.res](frontend/src/Dashboard.res)
- [frontend/src/SeasonView.res](frontend/src/SeasonView.res)
- [frontend/src/TeamView.res](frontend/src/TeamView.res)
- [frontend/src/PlayerView.res](frontend/src/PlayerView.res)
- [frontend/src/ProppedUpView.res](frontend/src/ProppedUpView.res)
- [frontend/src/VarSwingView.res](frontend/src/VarSwingView.res)
- [frontend/src/MatchView.res](frontend/src/MatchView.res)

Helpers:

- [frontend/src/Database.res](frontend/src/Database.res)
- [frontend/src/SqlHelper.js](frontend/src/SqlHelper.js)
- [frontend/src/TeamQueries.res](frontend/src/TeamQueries.res)
- [frontend/src/PlayerQueries.res](frontend/src/PlayerQueries.res)
- [frontend/src/FixtureCard.res](frontend/src/FixtureCard.res)
- [frontend/src/MatchTimeline.res](frontend/src/MatchTimeline.res)
- [frontend/src/Browser.res](frontend/src/Browser.res) / [BrowserApi.js](frontend/src/BrowserApi.js)

Deployment:

- [.github/workflows/deploy.yml](.github/workflows/deploy.yml)
- [frontend/scripts/sync-public-assets.mjs](frontend/scripts/sync-public-assets.mjs)

## Commands

Python:

```bash
source venv/bin/activate
python db.py
python sofascore_db.py
python scraper.py --start 2010 --end 2025
python scraper.py --start 2010 --end 2025 --refresh
python sofascore_scraper.py --start 2010 --end 2026
python site_builder.py --source sofascore
python update_site.py
```

Frontend (from [frontend/](frontend/)):

```bash
npm install
npm run dev
npm run res:build
npm test
npm run verify:deploy
```

## Validation checklist

Before closing frontend work:

```bash
cd frontend
npm run verify:deploy
```

Covers ReScript compile, Node tests, asset sync, production Vite build.

## Non-obvious implementation notes

### Match dates

In raw Transfermarkt data, `matches.date` is raw display text, not ISO.
In canonical `site.db`, adapter-built rows may use UTC timestamps rendered as text.

### Team values in events

`events.team` is `"Home"` / `"Away"`, not a club name. SQL joins back to
`matches` to resolve it.

### Penalty goals

The scraper maps the Transfermarkt `elfmeter` sprite to
`event_type = 'Penalty Goal'`, but historical rows in the DB are almost all
stored as `event_type = 'Goal'` with `player_1 == player_2`. The frontend treats
either shape as a penalty (see `MatchTimeline.isPenaltyGoal`). Keep both paths
until the archive is re-scraped end-to-end.

### Scraper entrypoint

`scraper.py` takes `--start` / `--end` arguments (defaults: 2010–2025). The
entrypoint is not hardcoded to a single season.

### Re-scrape safety

`save_to_db` deletes old events for a match before inserting the new timeline,
so re-running the scraper does not duplicate event rows.

### Unplayed fixtures

Transfermarkt exposes future matches as `-:-`. `parse_match_report` skips those
fixtures entirely, and `run_scraper` removes any already-stored placeholder
rows at startup. Do not reintroduce unplayed matches into `matches`.

### Event schema is richer now

`events` includes:

- stoppage-time fields: `minute_label`, `minute_base`, `minute_extra`
- ordering/detail fields: `event_order`, `event_subtype`, `event_detail`
- live score snapshots: `home_score_before`, `away_score_before`,
  `home_score_after`, `away_score_after`

Frontend timelines and team-derived metrics depend on these columns.

### Canonical DB source switching

- The frontend should consume the canonical `data/site.db`, not the raw source DBs
- `site_builder.py` currently supports `--source sofascore` and `--source transfermarkt`
- `frontend/scripts/sync-public-assets.mjs` builds `data/site.db` automatically before copying it into `frontend/public/super_lig.db`
- If the selected raw source DB exists, the sync script rebuilds `data/site.db`
- If the raw source DB is missing but `data/site.db` already exists, the sync script reuses the committed canonical DB
- If neither the raw source DB nor `data/site.db` exists, the frontend build fails
- The default frontend build source is SofaScore unless `SITE_DB_SOURCE` is overridden

### Latest-data policy

- The live site currently pivots off SofaScore, not Transfermarkt
- To pull the latest games, refresh `data/sofascore_super_lig.db` and then rebuild `data/site.db`
- Recommended update flow:
  - `python update_site.py --frontend-build`
- `python update_site.py` infers the active season and refreshes only that season by default
- Use `python update_site.py --season 2025` when you want to pin a specific season
- Transfermarkt syncing is optional now and mainly useful for comparison or fallback work

### Event-derived player surfaces

- Team squad tables and player archive views are derived from timeline events in `data/site.db`
- Quiet full-match appearances can be missing because there is no lineup/appearance feed in the canonical schema yet
- `VAR denied goals` are supported in player-facing views
- `VAR denied assists` are intentionally not exposed because the current SofaScore incident feed does not provide an assister on overturned-goal events

### Build warnings

Vite externalizes `node:fs` / `node:crypto` from `sql-wasm.js`. Warning only —
production builds still succeed.

## Safe assumptions

- GitHub Pages is still the deployment target
- Hash routing is preferred
- TR / EN UI support is preserved
- Browser-side SQLite is a deliberate product choice

## Watchouts

- Do not hand-edit generated ReScript JS
- Do not remove the DB sync step from the build
- Do not assume direct nested URLs work outside hash routing
- Do not change scraper output shape without updating the frontend SQL queries
- Do not make `TeamView` show all seasons at once unless product requirements change again
