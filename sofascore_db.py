import sqlite3
from pathlib import Path
from typing import Iterable

DB_DIR = Path("data")
DB_PATH = DB_DIR / "sofascore_super_lig.db"

MATCH_COLUMNS = (
    "id",
    "season_id",
    "season_name",
    "season_year",
    "season_start_year",
    "round",
    "start_timestamp",
    "status_code",
    "status_description",
    "status_type",
    "winner_code",
    "home_team_id",
    "home_team_name",
    "away_team_id",
    "away_team_name",
    "home_score",
    "away_score",
    "tournament_id",
    "tournament_name",
    "unique_tournament_id",
    "unique_tournament_name",
    "category_name",
    "custom_id",
    "slug",
    "url",
    "raw_json",
)

INCIDENT_COLUMNS = (
    "match_id",
    "incident_id",
    "incident_order",
    "incident_type",
    "incident_class",
    "time",
    "added_time",
    "reversed_period_time",
    "is_home",
    "confirmed",
    "rescinded",
    "player_id",
    "player_name",
    "player_in_id",
    "player_in_name",
    "player_out_id",
    "player_out_name",
    "assist_1_id",
    "assist_1_name",
    "home_score",
    "away_score",
    "reason",
    "text",
    "raw_json",
)

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        season_id INTEGER NOT NULL,
        season_name TEXT,
        season_year TEXT,
        season_start_year INTEGER,
        round INTEGER,
        start_timestamp INTEGER,
        status_code INTEGER,
        status_description TEXT,
        status_type TEXT,
        winner_code INTEGER,
        home_team_id INTEGER,
        home_team_name TEXT,
        away_team_id INTEGER,
        away_team_name TEXT,
        home_score INTEGER,
        away_score INTEGER,
        tournament_id INTEGER,
        tournament_name TEXT,
        unique_tournament_id INTEGER,
        unique_tournament_name TEXT,
        category_name TEXT,
        custom_id TEXT,
        slug TEXT,
        url TEXT,
        raw_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER NOT NULL,
        incident_id INTEGER,
        incident_order INTEGER NOT NULL,
        incident_type TEXT,
        incident_class TEXT,
        time INTEGER,
        added_time INTEGER,
        reversed_period_time INTEGER,
        is_home INTEGER,
        confirmed INTEGER,
        rescinded INTEGER,
        player_id INTEGER,
        player_name TEXT,
        player_in_id INTEGER,
        player_in_name TEXT,
        player_out_id INTEGER,
        player_out_name TEXT,
        assist_1_id INTEGER,
        assist_1_name TEXT,
        home_score INTEGER,
        away_score INTEGER,
        reason TEXT,
        text TEXT,
        raw_json TEXT NOT NULL,
        FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_matches_season_start_year ON matches (season_start_year)",
    "CREATE INDEX IF NOT EXISTS idx_matches_season_id ON matches (season_id)",
    "CREATE INDEX IF NOT EXISTS idx_matches_home_team_id ON matches (home_team_id)",
    "CREATE INDEX IF NOT EXISTS idx_matches_away_team_id ON matches (away_team_id)",
    "CREATE INDEX IF NOT EXISTS idx_incidents_match_id ON incidents (match_id)",
    "CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents (incident_type)",
    "CREATE INDEX IF NOT EXISTS idx_incidents_class ON incidents (incident_class)",
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()


def get_existing_match_ids(
    conn: sqlite3.Connection, *, season_start_year: int | None = None
) -> set[int]:
    if season_start_year is None:
        rows = conn.execute("SELECT id FROM matches").fetchall()
    else:
        rows = conn.execute(
            "SELECT id FROM matches WHERE season_start_year = ?",
            (season_start_year,),
        ).fetchall()
    return {row[0] for row in rows}


def _ordered_values(row: dict, columns: Iterable[str]) -> list:
    return [row.get(column) for column in columns]


def save_match_bundle(
    conn: sqlite3.Connection, match_row: dict, incident_rows: list[dict]
) -> None:
    match_placeholders = ", ".join("?" for _ in MATCH_COLUMNS)
    match_columns_sql = ", ".join(MATCH_COLUMNS)
    conn.execute(
        f"INSERT OR REPLACE INTO matches ({match_columns_sql}) VALUES ({match_placeholders})",
        _ordered_values(match_row, MATCH_COLUMNS),
    )

    conn.execute("DELETE FROM incidents WHERE match_id = ?", (match_row["id"],))

    if incident_rows:
        incident_placeholders = ", ".join("?" for _ in INCIDENT_COLUMNS)
        incident_columns_sql = ", ".join(INCIDENT_COLUMNS)
        conn.executemany(
            f"INSERT INTO incidents ({incident_columns_sql}) VALUES ({incident_placeholders})",
            [_ordered_values(row, INCIDENT_COLUMNS) for row in incident_rows],
        )


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
