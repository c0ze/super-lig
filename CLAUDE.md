# CLAUDE.md

Project-specific instructions for Claude Code / Codex-style agents.

See [AGENTS.md](AGENTS.md) for the full handoff notes — constraints, key files,
non-obvious implementation details, and the validation checklist. Everything
below is a quick-reference; prefer `AGENTS.md` when they conflict.

## Shape

- Python scraper + SQLite DB at the repo root
- ReScript/React/Vite frontend in [frontend/](frontend/) that reads the DB in-browser via `sql.js`
- GitHub Pages deployment at `super-lig.arda.tr`

## Hard rules

- Edit `.res` files, not generated `.res.js`
- Preserve hash routing and TR/EN toggle
- Keep the `sql.js/dist/sql-wasm.js` import in [frontend/src/SqlHelper.js](frontend/src/SqlHelper.js)
- `matches` and `events` are the contract with the frontend — audit `.res` SQL
  after any schema change

## Commands

Python:

```bash
source venv/bin/activate
python db.py
python scraper.py --start 2010 --end 2025
```

Frontend (run from [frontend/](frontend/)):

```bash
npm install
npm run dev
npm test
npm run verify:deploy
```

## Validation

Do not claim frontend work is done without running `npm run verify:deploy` in
[frontend/](frontend/). It covers ReScript compile, tests, asset sync, and a
production Vite build.

## Known sharp edges

- `matches.date` is raw scraped text, not normalized dates
- Transfermarkt renames some clubs across seasons, so `TeamView` history can
  fragment
- Vite warns about `node:fs` / `node:crypto` from `sql-wasm.js` — build still
  succeeds
