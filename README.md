# Super Lig Atlas

A data-driven frontend for Turkish Super Lig matches, backed by an embedded SQLite database and deployed as a static site to GitHub Pages at `super-lig.arda.tr`.

The project has two halves:

- A Python scraper that collects match reports and event timelines from Transfermarkt into `data/super_lig.db`
- An independent Python scraper that collects Super Lig match and incident data from SofaScore into `data/sofascore_super_lig.db`
- A canonical adapter build that turns either source DB into `data/site.db`
- A ReScript + React + Vite frontend that ships the canonical database directly to the browser and queries it with `sql.js`

## Features

- Season overview cards across the available archive
- Latest-season standings and top scorers
- Team archive pages with aggregate records, recent form, and season tabs
- Team-specific `kollandığı maçlar` / `propped up games` drill-down pages
- Match detail pages with richer event timelines
- Built-in TR / EN language toggle
- Static deployment with no backend runtime

## Tech Stack

- **Scraper**: Python, `requests`, `beautifulsoup4`, `lxml`, SQLite
- **Transfermarkt DB**: SQLite (`data/super_lig.db`)
- **SofaScore DB**: SQLite (`data/sofascore_super_lig.db`)
- **Canonical Site DB**: SQLite (`data/site.db`)
- **Frontend**: ReScript, React 18, Vite 5
- **In-browser SQL**: `sql.js`
- **Hosting**: GitHub Pages
- **Domain**: `super-lig.arda.tr`

## Repository Layout

```text
.
├── data/
│   ├── super_lig.db            # Raw Transfermarkt archive
│   ├── sofascore_super_lig.db  # Raw SofaScore archive
│   └── site.db                 # Canonical frontend DB built from one source adapter
├── frontend/
│   ├── public/                 # Copied DB + sql-wasm.wasm before builds
│   ├── scripts/
│   │   └── sync-public-assets.mjs
│   ├── src/
│   │   ├── App.res
│   │   ├── Dashboard.res
│   │   ├── SeasonView.res
│   │   ├── TeamView.res
│   │   ├── ProppedUpView.res
│   │   ├── MatchView.res
│   │   ├── Route.res
│   │   ├── TeamQueries.res
│   │   ├── SqlHelper.js
│   │   └── ...
│   ├── test/
│   ├── package.json
│   ├── rescript.json
│   └── vite.config.js
├── .github/workflows/deploy.yml
├── db.py                       # SQLite schema bootstrap
├── scraper.py                  # Transfermarkt scraper
├── sofascore_db.py             # SofaScore-only SQLite schema bootstrap
├── sofascore_scraper.py        # SofaScore scraper
├── site_db.py                  # Canonical frontend DB schema
├── site_builder.py             # Source adapter builder (SofaScore / Transfermarkt)
├── AGENTS.md                   # Agent handoff notes for automated contributors
└── CLAUDE.md                   # Claude/Codex project instructions
```

## Data Model

The canonical frontend database (`data/site.db`) contains two main tables:

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
- `minute_label`
- `minute_base`
- `minute_extra`
- `team` (`"Home"` or `"Away"`)
- `event_type` (`Goal`, `Penalty Goal`, `Missed Penalty`, `Yellow Card`, `Second Yellow Card`, `Red Card`, `Substitution`)
- `event_order`
- `event_subtype`
- `event_detail`
- `player_1`
- `player_2`
- `home_score_before`
- `away_score_before`
- `home_score_after`
- `away_score_after`

`team` is stored as `"Home"` / `"Away"` and mapped back to club names in frontend SQL queries. The richer event fields make it possible to render stoppage-time labels, missed penalties, own goals, VAR decisions, second-yellow reds, and team-level derived views like `kollandığı maçlar`. Indexes cover `match_id`, `event_type`, `matches.season`, and both team columns.

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

### 3. Initialize the raw source schemas

```bash
python db.py
```

This creates `data/super_lig.db` if it does not already exist.

Initialize the SofaScore raw schema:

```bash
python sofascore_db.py
```

Build the canonical frontend DB from SofaScore:

```bash
python site_builder.py --source sofascore
```

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

Initialize the raw Transfermarkt schema:

```bash
python db.py
```

Initialize the raw SofaScore schema:

```bash
python sofascore_db.py
```

Run the scraper for a year range (defaults: 2010–2025):

```bash
python scraper.py --start 2010 --end 2025
```

Force a re-scrape of already-seen matches:

```bash
python scraper.py --start 2010 --end 2025 --refresh
```

Run the independent SofaScore scraper into `data/sofascore_super_lig.db`:

```bash
python sofascore_scraper.py --start 2024 --end 2026
```

Force a SofaScore refresh:

```bash
python sofascore_scraper.py --start 2024 --end 2026 --refresh
```

Run a small SofaScore smoke test:

```bash
python sofascore_scraper.py --start 2025 --end 2025 --limit-matches 3
```

Build the canonical frontend DB:

```bash
python site_builder.py --source sofascore
```

Switch the canonical DB back to Transfermarkt if needed:

```bash
python site_builder.py --source transfermarkt
```

Update the live site data after new matches land:

```bash
python sofascore_scraper.py --start 2025 --end 2025 --refresh
python site_builder.py --source sofascore
cd frontend
npm run build
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

Choose a different canonical source for a local frontend build:

```bash
SITE_DB_SOURCE=transfermarkt npm run build
```

## Sync Flow

The frontend never reads the raw source DBs directly.

The normal flow is:

1. Update the raw source DB you care about
2. Rebuild `data/site.db` from that source
3. Let the frontend copy `data/site.db` into `frontend/public/super_lig.db`

For the current SofaScore-first setup, that usually means:

```bash
python sofascore_scraper.py --start 2025 --end 2025 --refresh
python site_builder.py --source sofascore
cd frontend
npm run build
```

The frontend asset sync script behaves like this:

1. If the selected raw source DB exists, it rebuilds `data/site.db`
2. If the raw source DB is missing but `data/site.db` already exists, it reuses the committed canonical DB
3. If neither is available, the build fails

This fallback is intentional so GitHub Pages builds can succeed from a clean checkout without requiring the raw SofaScore archive to be re-scraped during CI.

## Scraper Workflow

The Transfermarkt scraper pipeline is:

1. Discover match report URLs per season and matchday
2. Fetch each report page from Transfermarkt
3. Parse fixture metadata:
   - teams
   - score
   - raw date text
4. Skip unplayed fixtures whose score is still shown as `-:-`
5. Parse timeline events:
   - goals
   - cards
   - substitutions
   - missed penalties
   - event subtype / detail text
   - live score snapshots before / after each event
6. Save the fixture and its events into SQLite

The independent SofaScore scraper works similarly, but keeps its output in a separate DB so it can be compared against Transfermarkt without affecting the frontend:

1. Discover available Super Lig seasons from SofaScore
2. Page through each season's fixture list
3. Normalize match metadata into `matches`
4. Fetch each match's incident feed
5. Normalize incidents, including VAR-style decisions, into `incidents`
6. Save the match bundle into `data/sofascore_super_lig.db`

The canonical site builder then adapts one source DB into the stable frontend contract:

1. Read either `data/sofascore_super_lig.db` or `data/super_lig.db`
2. Normalize source-specific rows into canonical `matches` / `events`
3. Preserve existing frontend SQL expectations
4. Write the result to `data/site.db`
5. Copy `data/site.db` into `frontend/public/super_lig.db` during frontend builds

Important notes:

- CLI entrypoint: `python scraper.py --start <year> --end <year>` (inclusive range, defaults 2010–2025)
- `--refresh` forces already-scraped matches to be parsed again
- `get_scraped_match_ids()` skips fixtures already scraped with a valid score
- Re-scraping a match deletes and re-inserts its events, so timelines cannot duplicate
- Unplayed placeholder fixtures are removed from the DB at scraper startup and are never persisted
- `python sofascore_scraper.py --start <year> --end <year>` is intentionally independent from the Transfermarkt scraper and does not touch `data/super_lig.db`
- The SofaScore DB preserves each source payload as `raw_json` for later comparison or cross-mapping work
- `python site_builder.py --source <source>` is the only step that changes the frontend-facing DB
- Frontend builds default to `SITE_DB_SOURCE=sofascore`
- If the selected raw source DB is missing, frontend builds reuse the committed `data/site.db`

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
- `TeamView.res`: team archive, latest-season match history, and season tabs
- `ProppedUpView.res`: team-specific `kollandığı maçlar` drill-down
- `MatchView.res`: single match timeline page
- `TeamQueries.res`: shared SQL used by team pages
- `Copy.res`: TR / EN labels and UI copy
- `Database.res`: ReScript bindings to `SqlHelper.js`
- `SqlHelper.js`: browser SQLite loader/query helper

### Routing

The app uses hash-based routing for GitHub Pages compatibility:

- `#/`
- `#/season/<year>`
- `#/team/<name>`
- `#/team/<name>/propped-up`
- `#/match/<id>`

Hash routing is intentional because GitHub Pages does not provide SPA rewrite rules for arbitrary nested paths.

## Testing

The frontend currently has lightweight Node-based tests for:

- route parsing and route generation
- locale parsing and toggling
- timeline copy helpers
- team SQL queries for season tabs and `kollandığı maçlar`
- `SqlHelper.js` import behavior

Run them with:

```bash
cd frontend
npm test
```

The scraper has Python regression tests for schema setup and parsing rules:

```bash
python -m unittest tests.test_scraper
```

## Deployment

Deployment is handled by `.github/workflows/deploy.yml`.

### Trigger

- push to `main`
- manual workflow dispatch

### Pipeline

1. Checkout repository
2. Configure GitHub Pages
3. Set up Node 20
4. Install `frontend/` dependencies
5. Run `npm run verify:deploy`
6. Upload `frontend/dist` as the GitHub Pages artifact
7. Deploy that artifact with the official GitHub Pages actions

The workflow uses `actions/configure-pages`, `actions/upload-pages-artifact`, and
`actions/deploy-pages`. It does not publish via a `gh-pages` branch.

### Production build behavior

`npm run build` automatically:

1. Copies the DB and WASM into `frontend/public/`
2. Compiles ReScript
3. Builds the Vite app
4. Copies the root [CNAME](CNAME) file into `frontend/dist/`

That means deployment should not rely on manually copying `data/super_lig.db`.

## Known Quirks and Caveats

- The frontend ships a real SQLite file to the browser, so bundle size is dominated by the database asset.
- Match `date` values are raw strings from the scraped source and are not normalized yet.
- `sql.js` currently emits Vite warnings about `node:fs` and `node:crypto` during build. The build still succeeds.
- `frontend/src/*.res.js` files are generated output and are gitignored.
- The scraper is source-structure-sensitive and can break if Transfermarkt changes HTML classes or timeline markup.
- Transfermarkt sometimes renames clubs across seasons, so a team's history in `TeamView` can fragment across name variants.
- Team history is intentionally season-scoped in the UI now; the latest season is selected by default and older seasons live behind tabs.

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
python scraper.py --start 2010 --end 2025 --refresh
cd frontend
npm run build
```

## Next Improvements

Some good next steps for the project:

- normalize match dates into machine-friendly values
- add filters for seasons, clubs, and event types
- add browser-level regression tests for key flows
- unify historical club-name variants when a single team changes naming across seasons
