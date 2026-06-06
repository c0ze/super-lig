import sqlite3
import tempfile
import unittest
from pathlib import Path

import sofascore_db
import site_db
import youtube_summary_scraper


class YoutubeSummaryScraperTests(unittest.TestCase):
    def test_parse_summary_title_extracts_match_identity(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Trabzonspor (3-4) Beşiktaş | MAÇ ÖZETİ | 27. Hafta - 2016/2017"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Trabzonspor")
        self.assertEqual(parsed.away_team, "Beşiktaş")
        self.assertEqual(parsed.home_score, 3)
        self.assertEqual(parsed.away_score, 4)
        self.assertEqual(parsed.matchday, 27)
        self.assertEqual(parsed.season_start_year, 2016)

    def test_parse_summary_title_accepts_plain_score_format(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Trabzonspor 3 - 4 Beşiktaş | Maç Özeti | 2016/17"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Trabzonspor")
        self.assertEqual(parsed.away_team, "Beşiktaş")
        self.assertEqual(parsed.home_score, 3)
        self.assertEqual(parsed.away_score, 4)
        self.assertIsNone(parsed.matchday)
        self.assertEqual(parsed.season_start_year, 2016)

    def test_parse_summary_title_ignores_editorial_prefix(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "🔥 UNUTULMAZ DERBİ! | Fenerbahçe (2-2) Galatasaray | MAÇ ÖZETİ | 31. Hafta - 2011/2012"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Fenerbahçe")
        self.assertEqual(parsed.away_team, "Galatasaray")
        self.assertEqual(parsed.home_score, 2)
        self.assertEqual(parsed.away_score, 2)

    def test_parse_summary_title_accepts_main_channel_highlight_titles(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Trabzonspor (2-1) Galatasaray - Match Highlights | Trendyol Süper Lig - 2025/26"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Trabzonspor")
        self.assertEqual(parsed.away_team, "Galatasaray")
        self.assertEqual(parsed.home_score, 2)
        self.assertEqual(parsed.away_score, 1)
        self.assertIsNone(parsed.matchday)
        self.assertEqual(parsed.season_start_year, 2025)

    def test_parse_summary_title_accepts_highlights_summary_marker(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Gaziantep FK (1-1) Alanyaspor - Highlights/Summary | Trendyol Süper Lig - 2025/26"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Gaziantep FK")
        self.assertEqual(parsed.away_team, "Alanyaspor")
        self.assertEqual(parsed.home_score, 1)
        self.assertEqual(parsed.away_score, 1)
        self.assertEqual(parsed.season_start_year, 2025)

    def test_parse_summary_title_accepts_bare_highlights_marker(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Gençlerbirliği (1-2) Galatasaray - Highlights | Trendyol Süper Lig - 2025/26"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Gençlerbirliği")
        self.assertEqual(parsed.away_team, "Galatasaray")
        self.assertEqual(parsed.home_score, 1)
        self.assertEqual(parsed.away_score, 2)
        self.assertEqual(parsed.season_start_year, 2025)

    def test_parse_summary_title_accepts_highlights_ozet_marker(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Galatasaray (4-0) Kayserispor - Highlights/Özet | Trendyol Süper Lig - 2025/26"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Galatasaray")
        self.assertEqual(parsed.away_team, "Kayserispor")
        self.assertEqual(parsed.home_score, 4)
        self.assertEqual(parsed.away_score, 0)

    def test_parse_summary_title_accepts_highlights_and_goals_marker(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Beşiktaş (4-2) Antalyaspor - Highlights & All Goals | Trendyol Süper Lig - 2025/26 Season"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Beşiktaş")
        self.assertEqual(parsed.away_team, "Antalyaspor")
        self.assertEqual(parsed.home_score, 4)
        self.assertEqual(parsed.away_score, 2)

    def test_parse_summary_title_handles_en_dash_separators(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Konyaspor (2–0) Galatasaray – Highlights/Summary | Trendyol Süper Lig – 2025/26"
        )

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.home_team, "Konyaspor")
        self.assertEqual(parsed.away_team, "Galatasaray")
        self.assertEqual(parsed.home_score, 2)
        self.assertEqual(parsed.away_score, 0)
        self.assertEqual(parsed.season_start_year, 2025)

    def test_parse_summary_title_rejects_first_league_summaries(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "İstanbulspor (8-1) Adana Demirspor | Week 38 Match Summary | Trendyol 1. Lig - 2025/26"
        )

        self.assertIsNone(parsed)

    def test_parse_summary_title_rejects_foreign_league_summaries(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Newcastle United (4-3) Leeds United | 21. Hafta MAÇ ÖZETİ | Premier League - 2025/26"
        )

        self.assertIsNone(parsed)

    def test_parse_summary_title_rejects_foreign_competition_highlights(self) -> None:
        parsed = youtube_summary_scraper.parse_summary_title(
            "Galatasaray (3-1) Tottenham - Highlights | UEFA Champions League - 2025/26"
        )

        self.assertIsNone(parsed)

    def test_source_from_channel_url_decodes_turkish_handle(self) -> None:
        source = youtube_summary_scraper.source_from_channel_url(
            "https://www.youtube.com/@beINSPORTST%C3%BCrkiye/videos"
        )

        self.assertEqual(source, "youtube:beinsportsturkiye")

    def test_channel_videos_url_accepts_channel_or_videos_url(self) -> None:
        self.assertEqual(
            youtube_summary_scraper.channel_videos_url(
                "https://www.youtube.com/@beINSPORTST%C3%BCrkiye"
            ),
            "https://www.youtube.com/@beINSPORTST%C3%BCrkiye/videos",
        )
        self.assertEqual(
            youtube_summary_scraper.channel_videos_url(
                "https://www.youtube.com/@beINSPORTST%C3%BCrkiye/videos"
            ),
            "https://www.youtube.com/@beINSPORTST%C3%BCrkiye/videos",
        )

    def test_match_parsed_title_matches_sofascore_club_suffixes(self) -> None:
        with sqlite3.connect(":memory:") as conn:
            conn.execute(
                """
                CREATE TABLE matches (
                    id INTEGER PRIMARY KEY,
                    season_start_year INTEGER,
                    round INTEGER,
                    status_description TEXT,
                    home_team_name TEXT,
                    away_team_name TEXT,
                    home_score INTEGER,
                    away_score INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO matches
                (id, season_start_year, round, status_description, home_team_name,
                 away_team_name, home_score, away_score)
                VALUES
                (7133727, 2016, 27, 'Ended', 'Trabzonspor', 'Beşiktaş JK', 3, 4)
                """
            )

            parsed = youtube_summary_scraper.parse_summary_title(
                "Trabzonspor (3-4) Beşiktaş | MAÇ ÖZETİ | 27. Hafta - 2016/2017"
            )
            match_id = youtube_summary_scraper.match_parsed_title(conn, parsed)

        self.assertEqual(match_id, 7133727)

    def test_match_parsed_title_matches_known_team_aliases(self) -> None:
        with sqlite3.connect(":memory:") as conn:
            conn.execute(
                """
                CREATE TABLE matches (
                    id INTEGER PRIMARY KEY,
                    season_start_year INTEGER,
                    round INTEGER,
                    status_description TEXT,
                    home_team_name TEXT,
                    away_team_name TEXT,
                    home_score INTEGER,
                    away_score INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO matches
                (id, season_start_year, round, status_description, home_team_name,
                 away_team_name, home_score, away_score)
                VALUES
                (7133738, 2016, 28, 'Ended', 'Alanyaspor', 'Sincan Belediyesi Ankaraspor', 0, 1)
                """
            )

            parsed = youtube_summary_scraper.parse_summary_title(
                "Alanyaspor (0-1) Osmanlıspor | MAÇ ÖZETİ | 28. Hafta - 2016/2017"
            )
            match_id = youtube_summary_scraper.match_parsed_title(conn, parsed)

        self.assertEqual(match_id, 7133738)

    def test_match_parsed_title_can_match_canonical_site_db(self) -> None:
        with sqlite3.connect(":memory:") as conn:
            conn.execute(
                """
                CREATE TABLE matches (
                    id TEXT PRIMARY KEY,
                    season TEXT,
                    matchday INTEGER,
                    home_team TEXT,
                    away_team TEXT,
                    home_score INTEGER,
                    away_score INTEGER
                )
                """
            )
            conn.execute(
                """
                INSERT INTO matches
                (id, season, matchday, home_team, away_team, home_score, away_score)
                VALUES
                ('7133727', '2016', 27, 'Trabzonspor', 'Beşiktaş JK', 3, 4)
                """
            )

            parsed = youtube_summary_scraper.parse_summary_title(
                "Trabzonspor (3-4) Beşiktaş | MAÇ ÖZETİ | 27. Hafta - 2016/2017"
            )
            match_id = youtube_summary_scraper.match_parsed_title(
                conn,
                parsed,
                target="site",
            )

        self.assertEqual(match_id, "7133727")

    def test_save_match_video_replaces_existing_video_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_dir = sofascore_db.DB_DIR
            original_path = sofascore_db.DB_PATH

            try:
                sofascore_db.DB_DIR = Path(tmp_dir)
                sofascore_db.DB_PATH = sofascore_db.DB_DIR / "sofascore_test.db"
                sofascore_db.init_db()

                with sofascore_db.get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO matches
                        (id, season_id, raw_json)
                        VALUES (7133727, 1, '{}')
                        """
                    )
                    base_row = {
                        "match_id": 7133727,
                        "source": youtube_summary_scraper.SOURCE,
                        "video_id": "wcZvWylJ3k0",
                        "title": "old title",
                        "url": "https://www.youtube.com/watch?v=wcZvWylJ3k0",
                        "embed_url": "https://www.youtube-nocookie.com/embed/wcZvWylJ3k0",
                        "thumbnail_url": "",
                        "channel_title": "beIN SPORTS Arşiv",
                        "published_text": "",
                        "matched_at": "2026-05-15T00:00:00+00:00",
                        "raw_json": "{}",
                    }
                    sofascore_db.save_match_video(conn, base_row)
                    sofascore_db.save_match_video(conn, {**base_row, "title": "new title"})

                    rows = conn.execute(
                        "SELECT video_id, title FROM match_videos"
                    ).fetchall()

                self.assertEqual(rows, [("wcZvWylJ3k0", "new title")])
            finally:
                sofascore_db.DB_DIR = original_dir
                sofascore_db.DB_PATH = original_path

    def test_enrich_match_videos_rejects_empty_target_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = site_db.DB_PATH

            try:
                site_db.DB_PATH = Path(tmp_dir) / "site.db"
                site_db.init_db(site_db.DB_PATH)

                with self.assertRaisesRegex(RuntimeError, "has no matches"):
                    youtube_summary_scraper.enrich_match_videos(
                        target="site",
                        dry_run=True,
                    )
            finally:
                site_db.DB_PATH = original_path


if __name__ == "__main__":
    unittest.main()
