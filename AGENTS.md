# AGENTS.md

This file is for automated contributors and handoff-friendly project context.

## Project Summary

This repository contains:

- A Python scraper that builds `data/super_lig.db`
- A ReScript frontend in `frontend/` that reads that DB directly in the browser
- A GitHub Pages deployment pipeline targeting `super-lig.arda.tr`

There is no production backend. The browser queries SQLite through `sql.js`.

## Current Product Shape

The frontend currently supports:

- dashboard / season archive view
- season detail pages
- team archive pages
- match timeline pages
- TR / EN language toggle
- hash-based routing for Pages compatibility

## Most Important Constraints

### 1. Frontend should stay ReScript

The user explicitly wants the frontend in ReScript.

- Add or change UI behavior in `.res` files
- Do not treat generated `.res.js` files as source-of-truth
- `frontend/src/*.res.js` is generated and gitignored

### 2. Routing is hash-based on purpose

Use:

- `#/`
- `#/season/...`
- `#/team/...`
- `#/match/...`

Do not switch to history routing unless deployment infrastructure changes too.

### 3. The DB is embedded into the static site

Frontend builds depend on:

- `data/super_lig.db`
- `frontend/scripts/sync-public-assets.mjs`
- `frontend/public/super_lig.db`
- `frontend/public/sql-wasm.wasm`

If you change the DB path or asset pipeline, update the sync script and build docs.

### 4. sql.js import behavior is fragile

The frontend intentionally imports:

- `sql.js/dist/sql-wasm.js`

Do not casually change this back to bare `sql.js`; that previously caused a Vite/browser export mismatch.

## Key Files

### Data layer

- `db.py`: schema bootstrap
- `scraper.py`: match discovery + parsing + persistence
- `data/super_lig.db`: embedded dataset

### Frontend app shell

- `frontend/src/App.res`
- `frontend/src/Route.res`
- `frontend/src/Locale.res`
- `frontend/src/Copy.res`

### Frontend pages

- `frontend/src/Dashboard.res`
- `frontend/src/SeasonView.res`
- `frontend/src/TeamView.res`
- `frontend/src/MatchView.res`

### Frontend helpers

- `frontend/src/Database.res`
- `frontend/src/SqlHelper.js`
- `frontend/src/FixtureCard.res`
- `frontend/src/MatchTimeline.res`
- `frontend/src/Browser.res`
- `frontend/src/BrowserApi.js`

### Deployment

- `.github/workflows/deploy.yml`
- `frontend/scripts/sync-public-assets.mjs`

## Commands Agents Should Know

### Python

```bash
source venv/bin/activate
python db.py
python scraper.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run res:build
npm test
npm run verify:deploy
```

## Validation Checklist

Before closing work on the frontend, run:

```bash
cd frontend
npm run verify:deploy
```

That covers:

- ReScript compile
- Node tests
- asset sync
- production Vite build

## Non-Obvious Implementation Notes

### Match dates

`matches.date` is currently scraped as raw display text, not normalized ISO dates.

### Event descriptions

`events.description` is currently empty in practice. Timeline copy is mostly derived from:

- `event_type`
- `player_1`
- `player_2`
- home/away side mapping

### Team values in events

`events.team` stores `"Home"` or `"Away"`, not club names. Frontend SQL resolves this by joining against `matches`.

### Scraper entrypoint

`scraper.py` currently runs:

```python
run_scraper(2025, 2026)
```

in `__main__`. That is not the full historical range. Treat it as current code behavior, not necessarily intended archival behavior.

### Build warnings

Vite currently warns about `node:fs` / `node:crypto` being externalized from `sql-wasm.js`. Production builds still complete successfully.

## Suggested Agent Workflow

If the task is frontend-only:

1. Read `frontend/src/App.res` and the relevant view module
2. Make changes in `.res` source files only
3. Run `cd frontend && npm run verify:deploy`

If the task touches data:

1. Read `db.py` and `scraper.py`
2. Check whether schema changes affect frontend SQL queries
3. Rebuild data if necessary
4. Run frontend verification after any DB shape change

## Safe Assumptions

- GitHub Pages is still the deployment target
- Hash routing is acceptable and preferred here
- TR / EN UI support should be preserved
- Browser-side SQLite is a deliberate product choice

## Watchouts

- Do not hand-edit generated ReScript JS output
- Do not remove the DB sync step from the build
- Do not assume direct nested URLs will work outside hash routing
- Do not rewrite scraper behavior without checking how frontend queries depend on the schema

