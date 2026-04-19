import sqlite3
import tempfile
import unittest
from pathlib import Path

import site_builder


def create_sofascore_source_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE matches (
                id INTEGER PRIMARY KEY,
                season_start_year INTEGER,
                season_year TEXT,
                round INTEGER,
                start_timestamp INTEGER,
                status_code INTEGER,
                status_description TEXT,
                status_type TEXT,
                home_team_name TEXT,
                away_team_name TEXT,
                home_score INTEGER,
                away_score INTEGER,
                url TEXT
            );

            CREATE TABLE incidents (
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
                raw_json TEXT
            );
            """
        )

        conn.execute(
            """
            INSERT INTO matches
            (id, season_start_year, season_year, round, start_timestamp, status_code, status_description,
             status_type, home_team_name, away_team_name, home_score, away_score, url)
            VALUES
            (14109887, 2025, '25/26', 30, 1776531600, 100, 'Ended', 'finished',
             'Gençlerbirliği', 'Galatasaray', 1, 2,
             'https://www.sofascore.com/football/match/genclerbirligi-galatasaray/llbscgd#id:14109887'),
            (20000001, 2025, '25/26', 31, 1777136400, 60, 'Postponed', 'postponed',
             'Fenerbahçe', 'Beşiktaş JK', NULL, NULL,
             'https://www.sofascore.com/football/match/besiktas-fenerbahce/example#id:20000001'),
            (1454658, 2010, '10/11', 5, 1285441200, 100, 'Ended', 'finished',
             'Beşiktaş JK', 'Fenerbahçe', 0, 1,
             'https://www.sofascore.com/football/match/fenerbahce-besiktas/example#id:1454658')
            """
        )

        conn.executemany(
            """
            INSERT INTO incidents
            (match_id, incident_id, incident_order, incident_type, incident_class, time, added_time,
             reversed_period_time, is_home, confirmed, rescinded, player_id, player_name, player_in_id,
             player_in_name, player_out_id, player_out_name, assist_1_id, assist_1_name, home_score,
             away_score, reason, text, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    14109887,
                    344932896,
                    6,
                    "goal",
                    "regular",
                    2,
                    None,
                    44,
                    0,
                    None,
                    None,
                    233114,
                    "Mauro Icardi",
                    None,
                    None,
                    None,
                    None,
                    857738,
                    "Yunus Akgün",
                    0,
                    1,
                    None,
                    None,
                    "{}",
                ),
                (
                    14109887,
                    344944310,
                    5,
                    "goal",
                    "regular",
                    35,
                    None,
                    11,
                    0,
                    None,
                    None,
                    857738,
                    "Yunus Akgün",
                    None,
                    None,
                    None,
                    None,
                    913593,
                    "Gabriel Sara",
                    0,
                    2,
                    None,
                    None,
                    "{}",
                ),
                (
                    14109887,
                    98164,
                    4,
                    "varDecision",
                    "goalAwarded",
                    64,
                    None,
                    27,
                    0,
                    0,
                    None,
                    293519,
                    "Leroy Sane",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    '{"confirmed": false}',
                ),
                (
                    14109887,
                    126065418,
                    2,
                    "substitution",
                    "regular",
                    78,
                    None,
                    13,
                    0,
                    None,
                    None,
                    None,
                    None,
                    1001,
                    "Noa Lang",
                    233114,
                    "Mauro Icardi",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "{}",
                ),
                (
                    14109887,
                    344950000,
                    3,
                    "goal",
                    "regular",
                    66,
                    None,
                    22,
                    1,
                    None,
                    None,
                    139228,
                    "M'Baye Niang",
                    None,
                    None,
                    None,
                    None,
                    1172372,
                    "Adama Malouda Traoré",
                    1,
                    2,
                    None,
                    None,
                    "{}",
                ),
                (
                    14109887,
                    125073833,
                    1,
                    "card",
                    "yellow",
                    81,
                    None,
                    10,
                    1,
                    None,
                    0,
                    355582,
                    "Zan Zuzek",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "Foul",
                    None,
                    "{}",
                ),
                (
                    1454658,
                    900001,
                    3,
                    "goal",
                    "ownGoal",
                    5,
                    None,
                    40,
                    0,
                    None,
                    None,
                    300001,
                    "Necip Uysal",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    0,
                    1,
                    None,
                    None,
                    "{}",
                ),
                (
                    1454658,
                    900002,
                    2,
                    "inGamePenalty",
                    "missed",
                    23,
                    None,
                    22,
                    1,
                    None,
                    None,
                    300002,
                    "Ricardo Quaresma",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "Saved",
                    None,
                    "{}",
                ),
                (
                    1454658,
                    900003,
                    1,
                    "card",
                    "yellowRed",
                    71,
                    None,
                    19,
                    1,
                    None,
                    0,
                    300003,
                    "Guti",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "Professional foul",
                    None,
                    "{}",
                ),
            ],
        )
        conn.commit()


def create_transfermarkt_source_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE matches (
                id TEXT PRIMARY KEY,
                season TEXT,
                matchday INTEGER,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_score INTEGER,
                away_score INTEGER,
                url TEXT
            );

            CREATE TABLE events (
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
                away_score_after INTEGER
            );
            """
        )
        conn.execute(
            """
            INSERT INTO matches
            (id, season, matchday, date, home_team, away_team, home_score, away_score, url)
            VALUES
            ('tm-1', '2025', 1, '19 Nis 2026', 'Fenerbahçe SK', 'Galatasaray', 2, 1, 'https://example.test/tm-1')
            """
        )
        conn.execute(
            """
            INSERT INTO events
            (match_id, minute, minute_label, minute_base, minute_extra, team, event_type, event_order,
             event_subtype, event_detail, player_1, player_2, home_score_before, away_score_before,
             home_score_after, away_score_after)
            VALUES
            ('tm-1', 12, '12', 12, 0, 'Home', 'Goal', 1, 'Normal oyun', 'Asist: Tadic', 'Dzeko', 'Tadic', 0, 0, 1, 0)
            """
        )
        conn.commit()


class SiteBuilderTests(unittest.TestCase):
    def test_build_site_db_from_sofascore_normalizes_matches_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            sofascore_path = tmp_path / "sofascore.db"
            site_path = tmp_path / "site.db"
            create_sofascore_source_db(sofascore_path)

            result = site_builder.build_site_db(
                source="sofascore",
                target_db_path=site_path,
                sofascore_db_path=sofascore_path,
            )

            self.assertEqual(result["matches"], 2)
            self.assertEqual(result["events"], 9)

            with sqlite3.connect(site_path) as conn:
                matches = conn.execute(
                    """
                    SELECT id, season, matchday, date, home_team, away_team, home_score, away_score, url
                    FROM matches
                    ORDER BY CAST(season AS INTEGER), id
                    """
                ).fetchall()
                events = conn.execute(
                    """
                    SELECT match_id, minute, minute_label, minute_base, minute_extra, team, event_type,
                           event_order, event_subtype, event_detail, player_1, player_2,
                           home_score_before, away_score_before, home_score_after, away_score_after
                    FROM events
                    ORDER BY match_id, event_order
                    """
                ).fetchall()

            self.assertEqual(
                matches,
                [
                    (
                        "1454658",
                        "2010",
                        5,
                        "2010-09-25 19:00 UTC",
                        "Beşiktaş JK",
                        "Fenerbahçe",
                        0,
                        1,
                        "https://www.sofascore.com/football/match/fenerbahce-besiktas/example#id:1454658",
                    ),
                    (
                        "14109887",
                        "2025",
                        30,
                        "2026-04-18 17:00 UTC",
                        "Gençlerbirliği",
                        "Galatasaray",
                        1,
                        2,
                        "https://www.sofascore.com/football/match/genclerbirligi-galatasaray/llbscgd#id:14109887",
                    ),
                ],
            )
            self.assertEqual(
                events,
                [
                    ("14109887", 2, "2", 2, 0, "Away", "Goal", 1, "", "", "Mauro Icardi", "Yunus Akgün", 0, 0, 0, 1),
                    ("14109887", 35, "35", 35, 0, "Away", "Goal", 2, "", "", "Yunus Akgün", "Gabriel Sara", 0, 1, 0, 2),
                    ("14109887", 64, "64", 64, 0, "Away", "VAR Decision", 3, "goalAwarded", "overturned", "Leroy Sane", "", 0, 2, 0, 2),
                    ("14109887", 66, "66", 66, 0, "Home", "Goal", 4, "", "", "M'Baye Niang", "Adama Malouda Traoré", 0, 2, 1, 2),
                    ("14109887", 78, "78", 78, 0, "Away", "Substitution", 5, "regular", "", "Noa Lang", "Mauro Icardi", 1, 2, 1, 2),
                    ("14109887", 81, "81", 81, 0, "Home", "Yellow Card", 6, "yellow", "Foul", "Zan Zuzek", "", 1, 2, 1, 2),
                    ("1454658", 5, "5", 5, 0, "Away", "Own Goal", 1, "own_goal", "", "Necip Uysal", "", 0, 0, 0, 1),
                    ("1454658", 23, "23", 23, 0, "Home", "Missed Penalty", 2, "missed", "Saved", "Ricardo Quaresma", "", 0, 1, 0, 1),
                    ("1454658", 71, "71", 71, 0, "Home", "Second Yellow Card", 3, "yellowRed", "Professional foul", "Guti", "", 0, 1, 0, 1),
                ],
            )

    def test_build_site_db_from_transfermarkt_copies_existing_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            transfermarkt_path = tmp_path / "transfermarkt.db"
            site_path = tmp_path / "site.db"
            create_transfermarkt_source_db(transfermarkt_path)

            result = site_builder.build_site_db(
                source="transfermarkt",
                target_db_path=site_path,
                transfermarkt_db_path=transfermarkt_path,
            )

            self.assertEqual(result["matches"], 1)
            self.assertEqual(result["events"], 1)

            with sqlite3.connect(site_path) as conn:
                match = conn.execute(
                    "SELECT id, season, matchday, date, home_team, away_team, home_score, away_score, url FROM matches"
                ).fetchone()
                event = conn.execute(
                    """
                    SELECT match_id, minute, minute_label, team, event_type, event_subtype, event_detail,
                           player_1, player_2, home_score_before, away_score_before, home_score_after, away_score_after
                    FROM events
                    """
                ).fetchone()

            self.assertEqual(
                match,
                ("tm-1", "2025", 1, "19 Nis 2026", "Fenerbahçe SK", "Galatasaray", 2, 1, "https://example.test/tm-1"),
            )
            self.assertEqual(
                event,
                ("tm-1", 12, "12", "Home", "Goal", "Normal oyun", "Asist: Tadic", "Dzeko", "Tadic", 0, 0, 1, 0),
            )


if __name__ == "__main__":
    unittest.main()
