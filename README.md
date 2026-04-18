# Super Lig Atlas

A data-driven frontend for Turkish Super Lig matches, backed by an embedded SQLite database and deployed as a static site to GitHub Pages at `super-lig.arda.tr`.

The project has two halves:

- A Python scraper that collects match reports and event timelines from Transfermarkt into `data/super_lig.db`
- A ReScript + React + Vite frontend that ships the database directly to the browser and queries it with `sql.js`

## Features

- Season overview cards across the available archive
- Latest-season standings and top scorers
- Team archive pages with aggregate records and recent form
- Match detail pages with event timelines
- Built-in TR / EN language toggle
- Static deployment with no backend runtime

## Tech Stack

- **Scraper**: Python, `requests`, `beautifulsoup4`, `lxml`, SQLite
- **Database**: SQLite (`data/super_lig.db`)
- **Frontend**: ReScript, React 18, Vite 5
- **In-browser SQL**: `sql.js`
- **Hosting**: GitHub Pages
- **Domain**: `super-lig.arda.tr`

## Repository Layout

```text
.
├── data/
│   └── super_lig.db            # Embedded SQLite database used by the frontend
├── frontend/
│   ├── public/                 # Copied DB + sql-wasm.wasm before builds
│   ├── scripts/
│   │   └── sync-public-assets.mjs
│   ├── src/
│   │   ├── App.res
│   │   ├── Dashboard.res
│   │   ├── SeasonView.res
│   │   ├── TeamView.res
│   │   ├── MatchView.res
│   │   ├── Route.res
│   │   ├── SqlHelper.js
│   │   └── ...
│   ├── test/
│   ├── package.json
│   ├── rescript.json
│   └── vite.config.js
├── .github/workflows/deploy.yml
├── db.py                       # SQLite schema bootstrap
├── scraper.py                  # Transfermarkt scraper
├── AGENTS.md                   # Agent handoff notes for automated contributors
└── CLAUDE.md                   # Claude/Codex project instructions
```

## Data Model

The SQLite database currently contains two main tables:

### `matches`

Stores one row per fixture.

Columns:

- `id`
- `season`
- `matchday`
- `date`
- `home_team`
- `away_team`
- `home_score`
- `away_score`
- `url`

### `events`

Stores a timeline of match events.

Columns:

- `id`
- `match_id` (FK → `matches.id`, `ON DELETE CASCADE`)
- `minute`
- `team` (`"Home"` or `"Away"`)
- `event_type` (`Goal`, `Penalty Goal`, `Missed Penalty`, `Yellow Card`, `Second Yellow Card`, `Red Card`, `Substitution`)
- `player_1`
- `player_2`

`team` is stored as `"Home"` / `"Away"` and mapped back to club names in frontend SQL queries. Indexes cover `match_id`, `event_type`, `matches.season`, and both team columns.

## Prerequisites

### For scraping

- Python 3.10+
- A virtual environment is recommended

### For frontend development

- Node.js 20+
- npm

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd tff
```

### 2. Set up the Python environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Initialize the database schema

```bash
python db.py
```

This creates `data/super_lig.db` if it does not already exist.

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

### 5. Start the frontend

```bash
npm run dev
```

Then open the Vite URL shown in the terminal.

## Common Commands

### Root / Python

Initialize the schema:

```bash
python db.py
```

Run the scraper for a year range (defaults: 2010–2025):

```bash
python scraper.py --start 2010 --end 2025
```

### Frontend

Install dependencies:

```bash
cd frontend
npm install
```

Start local development:

```bash
npm run dev
```

Compile ReScript only:

```bash
npm run res:build
```

Run ReScript in watch mode:

```bash
npm run res:watch
```

Run tests:

```bash
npm test
```

Build production assets:

```bash
npm run build
```

Run the full deployment verification path:

```bash
npm run verify:deploy
```

## Scraper Workflow

The scraper pipeline is:

1. Discover match report URLs per season and matchday
2. Fetch each report page from Transfermarkt
3. Parse fixture metadata:
   - teams
   - score
   - raw date text
4. Parse timeline events:
   - goals
   - cards
   - substitutions
5. Save the fixture and its events into SQLite

Important notes:

- CLI entrypoint: `python scraper.py --start <year> --end <year>` (inclusive range, defaults 2010–2025)
- `get_scraped_match_ids()` skips fixtures already scraped with a valid score
- Re-scraping a match deletes and re-inserts its events, so timelines cannot duplicate

## Frontend Architecture

The frontend is intentionally backend-free in production.

### How it works

1. `frontend/scripts/sync-public-assets.mjs` copies:
   - `data/super_lig.db`
   - `sql-wasm.wasm`
2. Vite serves those files from `frontend/public/`
3. `src/SqlHelper.js` loads the SQLite database into the browser with `sql.js`
4. ReScript components execute SQL queries directly in the client

### Important frontend modules

- `App.res`: app shell, DB bootstrapping, locale state, route rendering
- `Route.res`: hash-based routing
- `Dashboard.res`: home page and season archive overview
- `SeasonView.res`: season table, top scorers, fixture list
- `TeamView.res`: team archive and match history
- `MatchView.res`: single match timeline page
- `Copy.res`: TR / EN labels and UI copy
- `Database.res`: ReScript bindings to `SqlHelper.js`
- `SqlHelper.js`: browser SQLite loader/query helper

### Routing

The app uses hash-based routing for GitHub Pages compatibility:

- `#/`
- `#/season/<year>`
- `#/team/<name>`
- `#/match/<id>`

Hash routing is intentional because GitHub Pages does not provide SPA rewrite rules for arbitrary nested paths.

## Testing

The frontend currently has lightweight Node-based tests for:

- route parsing and route generation
- locale parsing and toggling
- timeline copy helpers
- `SqlHelper.js` import behavior

Run them with:

```bash
cd frontend
npm test
```

## Deployment

Deployment is handled by `.github/workflows/deploy.yml`.

### Trigger

- push to `main`
- manual workflow dispatch

### Pipeline

1. Checkout repository
2. Set up Node 20
3. Install `frontend/` dependencies
4. Run `npm run verify:deploy`
5. Publish `frontend/dist` to GitHub Pages
6. Set `CNAME` to `super-lig.arda.tr`

### Production build behavior

`npm run build` automatically:

1. Copies the DB and WASM into `frontend/public/`
2. Compiles ReScript
3. Builds the Vite app

That means deployment should not rely on manually copying `data/super_lig.db`.

## Known Quirks and Caveats

- The frontend ships a real SQLite file to the browser, so bundle size is dominated by the database asset.
- Match `date` values are raw strings from the scraped source and are not normalized yet.
- `sql.js` currently emits Vite warnings about `node:fs` and `node:crypto` during build. The build still succeeds.
- `frontend/src/*.res.js` files are generated output and are gitignored.
- The scraper is source-structure-sensitive and can break if Transfermarkt changes HTML classes or timeline markup.
- Transfermarkt sometimes renames clubs across seasons, so a team's history in `TeamView` can fragment across name variants.

## Recommended Workflow

For normal frontend work:

```bash
cd frontend
npm install
npm run verify:deploy
```

For data refreshes:

```bash
source venv/bin/activate
python scraper.py
cd frontend
npm run build
```

## Next Improvements

Some good next steps for the project:

- normalize match dates into machine-friendly values
- add filters for seasons, clubs, and event types
- improve timeline labeling for penalty goals and other special event types
- add browser-level regression tests for key flows
- document or script reproducible full-database refreshes

