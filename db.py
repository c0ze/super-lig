import sqlite3
from pathlib import Path

DB_DIR = Path("data")
DB_PATH = DB_DIR / "super_lig.db"

def init_db():
    if not DB_DIR.exists():
        DB_DIR.mkdir(parents=True)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create matches table
    cursor.execute("""
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
    """)
    
    # Create events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        minute INTEGER,
        team TEXT,
        event_type TEXT,
        player_1 TEXT,
        player_2 TEXT,
        description TEXT,
        FOREIGN KEY (match_id) REFERENCES matches (id)
    )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
