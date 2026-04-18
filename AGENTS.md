# AGENTS.md

Handoff notes for automated contributors.

## Project summary

- Python scraper builds [data/super_lig.db](data/super_lig.db)
- ReScript frontend in [frontend/](frontend/) reads that DB directly in the browser via `sql.js`
- GitHub Pages workflow in [.github/workflows/deploy.yml](.github/workflows/deploy.yml) deploys to `super-lig.arda.tr`

There is no production backend.

## Product surface

- Dashboard / season archive
- Season detail
- Team archive
- Match timeline
- TR / EN language toggle
- Hash-based routing (Pages-compatible)

## Hard constraints

### Frontend stays in ReScript

- Change UI behavior in `.res` files
- `frontend/src/*.res.js` is generated and gitignored — never hand-edit

### Hash routing is intentional

Use `#/`, `#/season/...`, `#/team/...`, `#/match/...`. Do not switch to history
routing unless the deployment target changes.

### DB is embedded into the static site

Frontend builds depend on:

- [data/super_lig.db](data/super_lig.db)
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
- [data/super_lig.db](data/super_lig.db)

Frontend shell:

- [frontend/src/App.res](frontend/src/App.res)
- [frontend/src/Route.res](frontend/src/Route.res)
- [frontend/src/Locale.res](frontend/src/Locale.res)
- [frontend/src/Copy.res](frontend/src/Copy.res)

Frontend pages:

- [frontend/src/Dashboard.res](frontend/src/Dashboard.res)
- [frontend/src/SeasonView.res](frontend/src/SeasonView.res)
- [frontend/src/TeamView.res](frontend/src/TeamView.res)
- [frontend/src/MatchView.res](frontend/src/MatchView.res)

Helpers:

- [frontend/src/Database.res](frontend/src/Database.res)
- [frontend/src/SqlHelper.js](frontend/src/SqlHelper.js)
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
python scraper.py --start 2010 --end 2025
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

`matches.date` is raw display text, not ISO.

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
