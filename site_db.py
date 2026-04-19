import sqlite3
from pathlib import Path
from typing import Iterable

DB_DIR = Path("data")
DB_PATH = DB_DIR / "site.db"

MATCH_COLUMNS = (
    "id",
    "season",
    "matchday",
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "url",
)

EVENT_COLUMNS = (
    "match_id",
    "minute",
    "minute_label",
    "minute_base",
    "minute_extra",
    "team",
    "event_type",
    "event_order",
    "event_subtype",
    "event_detail",
    "player_1",
    "player_2",
    "home_score_before",
    "away_score_before",
    "home_score_after",
    "away_score_after",
)

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS matches (
        id TEXT PRIMARY KEY,
        season TEXT,
        matchday INTEGER,
        date TEXT,
        home_team TEXT,
        away_team TEXT,
        home_score INTEGER,
        away_score INTEGER,
        url TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT NOT NULL,
        minute INTEGER,
        minute_label TEXT,
        minute_base INTEGER,
        minute_extra INTEGER,
        team TEXT,
        event_type TEXT,
        event_order INTEGER,
        event_subtype TEXT,
        event_detail TEXT,
        player_1 TEXT,
        player_2 TEXT,
        home_score_before INTEGER,
        away_score_before INTEGER,
        home_score_after INTEGER,
        away_score_after INTEGER,
        FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS build_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_matches_season ON matches (season)",
    "CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches (home_team)",
    "CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches (away_team)",
    "CREATE INDEX IF NOT EXISTS idx_events_match_id ON events (match_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type)",
)


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str = DB_PATH, *, recreate: bool = False) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if recreate and db_path.exists():
        db_path.unlink()

    with get_connection(db_path) as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()


def _ordered_values(row: dict, columns: Iterable[str]) -> list:
    return [row.get(column) for column in columns]


def save_match_bundle(
    conn: sqlite3.Connection, match_row: dict, event_rows: list[dict]
) -> None:
    match_placeholders = ", ".join("?" for _ in MATCH_COLUMNS)
    event_placeholders = ", ".join("?" for _ in EVENT_COLUMNS)

    conn.execute(
        f"INSERT OR REPLACE INTO matches ({', '.join(MATCH_COLUMNS)}) VALUES ({match_placeholders})",
        _ordered_values(match_row, MATCH_COLUMNS),
    )
    conn.execute("DELETE FROM events WHERE match_id = ?", (match_row["id"],))

    if event_rows:
        conn.executemany(
            f"INSERT INTO events ({', '.join(EVENT_COLUMNS)}) VALUES ({event_placeholders})",
            [_ordered_values(row, EVENT_COLUMNS) for row in event_rows],
        )


def replace_metadata(conn: sqlite3.Connection, metadata: dict[str, str]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO build_meta (key, value) VALUES (?, ?)",
        sorted(metadata.items()),
    )


if __name__ == "__main__":
    init_db(recreate=True)
    print(f"Database initialized at {DB_PATH}")
