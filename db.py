import sqlite3
from pathlib import Path

DB_DIR = Path("data")
DB_PATH = DB_DIR / "super_lig.db"

EVENT_COLUMN_DEFINITIONS = {
    "minute_label": "TEXT",
    "minute_base": "INTEGER",
    "minute_extra": "INTEGER",
    "event_order": "INTEGER",
    "event_subtype": "TEXT",
    "event_detail": "TEXT",
    "home_score_before": "INTEGER",
    "away_score_before": "INTEGER",
    "home_score_after": "INTEGER",
    "away_score_after": "INTEGER",
}

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
    "CREATE INDEX IF NOT EXISTS idx_matches_season ON matches (season)",
    "CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches (home_team)",
    "CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches (away_team)",
    "CREATE INDEX IF NOT EXISTS idx_events_match_id ON events (match_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type)",
)


def _drop_description_column(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    if "description" in cols:
        conn.execute("ALTER TABLE events DROP COLUMN description")


def _ensure_event_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    for column, column_type in EVENT_COLUMN_DEFINITIONS.items():
        if column not in cols:
            conn.execute(f"ALTER TABLE events ADD COLUMN {column} {column_type}")


def init_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        for stmt in SCHEMA_STATEMENTS:
            conn.execute(stmt)
        _drop_description_column(conn)
        _ensure_event_columns(conn)
        conn.commit()


def delete_unplayed_matches(conn: sqlite3.Connection) -> int:
    cursor = conn.execute(
        "DELETE FROM matches WHERE home_score < 0 OR away_score < 0"
    )
    return cursor.rowcount


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
