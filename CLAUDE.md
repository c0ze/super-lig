# CLAUDE.md

Project-specific instructions for Claude Code / Codex-style agents.

## What This Repo Is

This is a static Super Lig data app with:

- Python scraping and SQLite persistence at the repo root
- A ReScript frontend in `frontend/`
- GitHub Pages deployment with a custom domain

The frontend reads `data/super_lig.db` in the browser via `sql.js`.

## First Files To Read

If you are starting a task, inspect these first:

- `README.md`
- `AGENTS.md`
- `frontend/src/App.res`
- `frontend/src/Route.res`
- `frontend/package.json`
- `scraper.py`
- `db.py`

## Working Rules

### Frontend

- Treat ReScript source as authoritative
- Edit `.res` files, not generated `.res.js`
- Preserve hash routing
- Preserve TR / EN support unless explicitly asked otherwise

### Data / Scraper

- `matches` and `events` are the contract the frontend depends on
- If you change schema or event semantics, audit frontend SQL queries too
- Be careful with Transfermarkt-specific selectors in `scraper.py`

### Deployment

- GitHub Pages deploys from `frontend/dist`
- The DB and WASM are copied into `frontend/public` by `frontend/scripts/sync-public-assets.mjs`
- `npm run verify:deploy` is the expected final validation path

## Commands

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
npm test
npm run verify:deploy
```

## Important Notes

- Keep the explicit `sql.js/dist/sql-wasm.js` import in `frontend/src/SqlHelper.js`
- Match routes live at `#/match/<id>`
- Team routes live at `#/team/<name>`
- Season routes live at `#/season/<year>`
- `frontend/src/*.res.js` is generated and should not be hand-maintained

## If You Change Frontend Behavior

Run:

```bash
cd frontend
npm run verify:deploy
```

Do not claim the work is done without at least compiling ReScript and producing a production build.

## If You Change Data Shape

Check:

- `frontend/src/Dashboard.res`
- `frontend/src/SeasonView.res`
- `frontend/src/TeamView.res`
- `frontend/src/MatchView.res`

These pages all issue direct SQL queries against the embedded schema.

## Known Sharp Edges

- `sql.js` produces Vite warnings during build, but builds still succeed
- `matches.date` is raw scraped text, not normalized date data
- `events.description` is usually empty
- The scraper main block is currently configured for `run_scraper(2025, 2026)`

