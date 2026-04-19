import tempfile
import unittest
from pathlib import Path

import requests

import sofascore_db
import sofascore_scraper


def make_event(
    event_id: int,
    *,
    season_id: int = 77805,
    season_year: str = "25/26",
    round_number: int = 30,
    start_timestamp: int = 1776531600,
    home_name: str = "Gençlerbirliği",
    home_id: int = 7802,
    away_name: str = "Galatasaray",
    away_id: int = 3061,
    home_score: int = 1,
    away_score: int = 2,
    custom_id: str = "llbscgd",
    slug: str = "genclerbirligi-galatasaray",
) -> dict:
    return {
        "id": event_id,
        "season": {
            "id": season_id,
            "name": f"Super Lig {season_year}",
            "year": season_year,
        },
        "roundInfo": {"round": round_number},
        "startTimestamp": start_timestamp,
        "status": {
            "code": 100,
            "description": "Ended",
            "type": "finished",
        },
        "winnerCode": 2,
        "homeTeam": {"id": home_id, "name": home_name},
        "awayTeam": {"id": away_id, "name": away_name},
        "homeScore": {"current": home_score},
        "awayScore": {"current": away_score},
        "tournament": {
            "name": "Trendyol Süper Lig",
            "slug": "trendyol-super-lig",
            "uniqueTournament": {
                "id": 52,
                "name": "Trendyol Süper Lig",
                "slug": "trendyol-super-lig",
            },
            "category": {"name": "Turkey"},
        },
        "customId": custom_id,
        "slug": slug,
    }


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append(url)
        payload = self.responses.get(url)
        if payload is None:
            return FakeResponse({"error": "not found"}, status_code=404)
        return FakeResponse(payload)


class SofaScoreDbTests(unittest.TestCase):
    def test_init_db_creates_isolated_matches_and_incidents_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_dir = sofascore_db.DB_DIR
            original_path = sofascore_db.DB_PATH

            try:
                sofascore_db.DB_DIR = Path(tmp_dir)
                sofascore_db.DB_PATH = sofascore_db.DB_DIR / "sofascore_test.db"
                sofascore_db.init_db()

                with sofascore_db.get_connection() as conn:
                    tables = {
                        row[0]
                        for row in conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        ).fetchall()
                    }
                    match_columns = {
                        row[1] for row in conn.execute("PRAGMA table_info(matches)").fetchall()
                    }
                    incident_columns = {
                        row[1]
                        for row in conn.execute("PRAGMA table_info(incidents)").fetchall()
                    }

                self.assertIn("matches", tables)
                self.assertIn("incidents", tables)
                self.assertTrue(
                    {
                        "season_id",
                        "season_year",
                        "season_start_year",
                        "home_team_id",
                        "away_team_id",
                        "url",
                        "raw_json",
                    }.issubset(match_columns)
                )
                self.assertTrue(
                    {
                        "match_id",
                        "incident_id",
                        "incident_order",
                        "incident_type",
                        "incident_class",
                        "confirmed",
                        "rescinded",
                        "raw_json",
                    }.issubset(incident_columns)
                )
            finally:
                sofascore_db.DB_DIR = original_dir
                sofascore_db.DB_PATH = original_path


class SofaScoreScraperTests(unittest.TestCase):
    def test_parse_season_start_year_uses_two_digit_suffixes(self) -> None:
        self.assertEqual(sofascore_scraper.parse_season_start_year("25/26"), 2025)
        self.assertEqual(sofascore_scraper.parse_season_start_year("10/11"), 2010)
        self.assertEqual(sofascore_scraper.parse_season_start_year("99/00"), 1999)

    def test_get_target_seasons_filters_requested_start_years(self) -> None:
        session = FakeSession(
            {
                sofascore_scraper.seasons_url(): {
                    "seasons": [
                        {"id": 77805, "name": "Super Lig 25/26", "year": "25/26"},
                        {"id": 63814, "name": "Super Lig 24/25", "year": "24/25"},
                        {"id": 53190, "name": "Super Lig 23/24", "year": "23/24"},
                    ]
                }
            }
        )

        seasons = sofascore_scraper.get_target_seasons(session, 2024, 2025)

        self.assertEqual([season["id"] for season in seasons], [63814, 77805])

    def test_fetch_season_events_paginates_until_empty_and_deduplicates(self) -> None:
        session = FakeSession(
            {
                sofascore_scraper.season_events_url(77805, 0): {
                    "events": [make_event(1), make_event(2)]
                },
                sofascore_scraper.season_events_url(77805, 1): {
                    "events": [make_event(2), make_event(3)]
                },
                sofascore_scraper.season_events_url(77805, 2): {"events": []},
            }
        )

        events = sofascore_scraper.fetch_season_events(session, 77805)

        self.assertEqual([event["id"] for event in events], [1, 2, 3])
        self.assertEqual(
            session.calls,
            [
                sofascore_scraper.season_events_url(77805, 0),
                sofascore_scraper.season_events_url(77805, 1),
                sofascore_scraper.season_events_url(77805, 2),
            ],
        )

    def test_normalize_match_extracts_compare_ready_fields(self) -> None:
        match = sofascore_scraper.normalize_match(make_event(14109887))

        self.assertEqual(match["id"], 14109887)
        self.assertEqual(match["season_id"], 77805)
        self.assertEqual(match["season_year"], "25/26")
        self.assertEqual(match["season_start_year"], 2025)
        self.assertEqual(match["round"], 30)
        self.assertEqual(match["home_team_name"], "Gençlerbirliği")
        self.assertEqual(match["away_team_name"], "Galatasaray")
        self.assertEqual(
            match["url"],
            "https://www.sofascore.com/football/match/genclerbirligi-galatasaray/llbscgd#id:14109887",
        )
        self.assertIn('"id": 14109887', match["raw_json"])

    def test_normalize_incident_preserves_var_decision_flags(self) -> None:
        incident = {
            "id": 98164,
            "incidentType": "varDecision",
            "incidentClass": "goalAwarded",
            "confirmed": False,
            "rescinded": False,
            "time": 64,
            "isHome": False,
            "player": {"id": 293519, "name": "Leroy Sane"},
        }

        row = sofascore_scraper.normalize_incident(14109887, 7, incident)

        self.assertEqual(row["match_id"], 14109887)
        self.assertEqual(row["incident_id"], 98164)
        self.assertEqual(row["incident_order"], 7)
        self.assertEqual(row["incident_type"], "varDecision")
        self.assertEqual(row["incident_class"], "goalAwarded")
        self.assertEqual(row["confirmed"], 0)
        self.assertEqual(row["rescinded"], 0)
        self.assertEqual(row["player_id"], 293519)
        self.assertEqual(row["player_name"], "Leroy Sane")

    def test_save_match_bundle_replaces_incidents_for_existing_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_dir = sofascore_db.DB_DIR
            original_path = sofascore_db.DB_PATH

            try:
                sofascore_db.DB_DIR = Path(tmp_dir)
                sofascore_db.DB_PATH = sofascore_db.DB_DIR / "sofascore_test.db"
                sofascore_db.init_db()

                match_row = sofascore_scraper.normalize_match(make_event(14109887))
                old_incident = sofascore_scraper.normalize_incident(
                    14109887,
                    1,
                    {
                        "id": 1,
                        "incidentType": "card",
                        "incidentClass": "yellow",
                        "time": 48,
                        "isHome": False,
                        "player": {"id": 10, "name": "Roland Sallai"},
                    },
                )
                new_incident = sofascore_scraper.normalize_incident(
                    14109887,
                    1,
                    {
                        "id": 2,
                        "incidentType": "varDecision",
                        "incidentClass": "goalAwarded",
                        "time": 64,
                        "isHome": False,
                        "confirmed": False,
                        "player": {"id": 293519, "name": "Leroy Sane"},
                    },
                )

                with sofascore_db.get_connection() as conn:
                    sofascore_db.save_match_bundle(conn, match_row, [old_incident])
                    sofascore_db.save_match_bundle(conn, match_row, [new_incident])

                    incidents = conn.execute(
                        """
                        SELECT incident_id, incident_type, player_name
                        FROM incidents
                        WHERE match_id = ?
                        ORDER BY incident_order
                        """,
                        (14109887,),
                    ).fetchall()

                self.assertEqual(incidents, [(2, "varDecision", "Leroy Sane")])
            finally:
                sofascore_db.DB_DIR = original_dir
                sofascore_db.DB_PATH = original_path


if __name__ == "__main__":
    unittest.main()
