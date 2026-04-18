import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bs4 import BeautifulSoup

import db
import scraper


SAMPLE_MATCH_HTML = """
<div id="sb-tore">
  <li class="sb-aktion-heim">
    <div class="sb-aktion">
      <div class="sb-aktion-uhr">
        <span class="sb-sprite-uhr-klein" style="background-position: -36px -36px;"></span>
      </div>
      <div class="sb-aktion-spielstand"><b>1:0</b></div>
      <div class="sb-aktion-aktion">
        <a class="wichtig" title="Edin Dzeko">Edin Dzeko</a>, Normal oyun, 1. Sezon golü
        <br />
        Asist:
        <a class="wichtig" title="Dusan Tadic">Dusan Tadic</a>, Orta
      </div>
    </div>
  </li>
  <li class="sb-aktion-heim">
    <div class="sb-aktion">
      <div class="sb-aktion-uhr">
        <span class="sb-sprite-uhr-klein" style="background-position: -324px -252px;"></span>
      </div>
      <div class="sb-aktion-spielstand"><b>2:0</b></div>
      <div class="sb-aktion-aktion">
        <a class="wichtig" title="Talisca">Talisca</a>, Penaltı, 16. Sezon golü
        <br />
        Asist:
        <a class="wichtig" title="Talisca">Talisca</a>, Penaltı: Faul yapılan oyuncu
      </div>
    </div>
  </li>
</div>
<div id="sb-karten">
  <li class="sb-aktion-gast">
    <div class="sb-aktion">
      <div class="sb-aktion-uhr">
        <span class="sb-sprite-uhr-klein" style="background-position: -144px -252px;"></span>
      </div>
      <div class="sb-aktion-spielstand"><span class="sb-sprite sb-gelbrot"></span></div>
      <div class="sb-aktion-aktion">
        <a class="wichtig" title="Samet Akaydin">Samet Akaydin</a>
        <br />
        2. Sarı kart  , Faul
      </div>
    </div>
  </li>
</div>
<div id="sb-verschossene">
  <li class="sb-aktion-gast">
    <div class="sb-aktion">
      <div class="sb-aktion-uhr">
        <span class="sb-sprite-uhr-klein" style="background-position: -324px -288px;">+4</span>
      </div>
      <div class="sb-aktion-spielstand"></div>
      <div class="sb-aktion-aktion">
        <div class="sb-aktion-spielerbild" style="margin-right: 10px;"></div>
        <span class="sb-aktion-wechsel-ein">
          Faul penaltısı,
          <a class="wichtig" title="Talisca">Talisca</a>
        </span>
        <span class="sb-aktion-wechsel-aus">
          <a class="wichtig" title="Mateusz Lis">Mateusz Lis</a>, Kurtarış
        </span>
      </div>
    </div>
  </li>
</div>
"""

SAMPLE_UNPLAYED_MATCH_HTML = """
<div class="sb-spieldaten">
  <p class="sb-datum"><a>19 Nis 2026</a></p>
</div>
<div class="sb-team sb-heim">
  <a class="sb-vereinslink">Fenerbahçe SK</a>
</div>
<div class="sb-team sb-gast">
  <a class="sb-vereinslink">Galatasaray</a>
</div>
<div class="sb-ergebnis">
  <span class="sb-endstand">-:-</span>
</div>
"""


class InitDbTests(unittest.TestCase):
    def test_init_db_adds_rich_event_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_dir = db.DB_DIR
            original_path = db.DB_PATH

            try:
                db.DB_DIR = Path(tmp_dir)
                db.DB_PATH = db.DB_DIR / "test.db"
                db.init_db()

                with db.get_connection() as conn:
                    columns = {
                        row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()
                    }

                self.assertTrue(
                    {
                        "minute_label",
                        "minute_base",
                        "minute_extra",
                        "event_order",
                        "event_subtype",
                        "event_detail",
                        "home_score_before",
                        "away_score_before",
                        "home_score_after",
                        "away_score_after",
                    }.issubset(columns)
                )
            finally:
                db.DB_DIR = original_dir
                db.DB_PATH = original_path

    def test_delete_unplayed_matches_removes_placeholder_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_dir = db.DB_DIR
            original_path = db.DB_PATH

            try:
                db.DB_DIR = Path(tmp_dir)
                db.DB_PATH = db.DB_DIR / "test.db"
                db.init_db()

                with db.get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO matches
                        (id, season, matchday, date, home_team, away_team, home_score, away_score, url)
                        VALUES
                        ('played', '2025', 1, '', 'A', 'B', 2, 1, ''),
                        ('future', '2025', 2, '', 'C', 'D', -1, -1, '')
                        """
                    )
                    conn.execute(
                        """
                        INSERT INTO events
                        (match_id, minute, minute_label, minute_base, minute_extra, team, event_type, event_order,
                         event_subtype, event_detail, player_1, player_2, home_score_before, away_score_before,
                         home_score_after, away_score_after)
                        VALUES
                        ('future', 0, '', NULL, 0, 'Home', 'Goal', 1, '', '', '', '', 0, 0, 0, 0)
                        """
                    )
                    conn.commit()

                    removed = db.delete_unplayed_matches(conn)
                    remaining = conn.execute("SELECT id FROM matches ORDER BY id").fetchall()
                    remaining_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

                self.assertEqual(removed, 1)
                self.assertEqual(remaining, [("played",)])
                self.assertEqual(remaining_events, 0)
            finally:
                db.DB_DIR = original_dir
                db.DB_PATH = original_path


class ParseMatchEventsTests(unittest.TestCase):
    def test_parse_match_events_extracts_rich_fields_and_score_state(self) -> None:
        soup = BeautifulSoup(SAMPLE_MATCH_HTML, "lxml")

        events = scraper.parse_match_events(soup, "demo-match")

        self.assertEqual(
            [event["event_type"] for event in events],
            ["Goal", "Second Yellow Card", "Penalty Goal", "Missed Penalty"],
        )
        self.assertEqual([event["event_order"] for event in events], [1, 2, 3, 4])

        opening_goal = events[0]
        self.assertEqual(opening_goal["minute"], 12)
        self.assertEqual(opening_goal["minute_label"], "12")
        self.assertEqual(opening_goal["player_1"], "Edin Dzeko")
        self.assertEqual(opening_goal["player_2"], "Dusan Tadic")
        self.assertEqual(opening_goal["event_subtype"], "Normal oyun")
        self.assertEqual(opening_goal["event_detail"], "Asist: Dusan Tadic, Orta")
        self.assertEqual(opening_goal["home_score_before"], 0)
        self.assertEqual(opening_goal["away_score_before"], 0)
        self.assertEqual(opening_goal["home_score_after"], 1)
        self.assertEqual(opening_goal["away_score_after"], 0)

        second_yellow = events[1]
        self.assertEqual(second_yellow["minute"], 75)
        self.assertEqual(second_yellow["team"], "Away")
        self.assertEqual(second_yellow["player_1"], "Samet Akaydin")
        self.assertEqual(second_yellow["event_detail"], "Faul")
        self.assertEqual(second_yellow["home_score_before"], 1)
        self.assertEqual(second_yellow["away_score_before"], 0)
        self.assertEqual(second_yellow["home_score_after"], 1)
        self.assertEqual(second_yellow["away_score_after"], 0)

        penalty_goal = events[2]
        self.assertEqual(penalty_goal["minute"], 80)
        self.assertEqual(penalty_goal["event_subtype"], "Penaltı")
        self.assertEqual(penalty_goal["player_1"], "Talisca")
        self.assertEqual(penalty_goal["player_2"], "Talisca")
        self.assertEqual(penalty_goal["home_score_before"], 1)
        self.assertEqual(penalty_goal["away_score_before"], 0)
        self.assertEqual(penalty_goal["home_score_after"], 2)
        self.assertEqual(penalty_goal["away_score_after"], 0)

        missed_penalty = events[3]
        self.assertEqual(missed_penalty["minute"], 94)
        self.assertEqual(missed_penalty["minute_base"], 90)
        self.assertEqual(missed_penalty["minute_extra"], 4)
        self.assertEqual(missed_penalty["minute_label"], "90+4")
        self.assertEqual(missed_penalty["team"], "Away")
        self.assertEqual(missed_penalty["player_1"], "Talisca")
        self.assertEqual(missed_penalty["player_2"], "Mateusz Lis")
        self.assertEqual(missed_penalty["event_subtype"], "Faul penaltısı")
        self.assertEqual(missed_penalty["event_detail"], "Kurtarış")
        self.assertEqual(missed_penalty["home_score_before"], 2)
        self.assertEqual(missed_penalty["away_score_before"], 0)
        self.assertEqual(missed_penalty["home_score_after"], 2)
        self.assertEqual(missed_penalty["away_score_after"], 0)


class ParseMatchReportTests(unittest.TestCase):
    def test_parse_match_report_skips_unplayed_matches(self) -> None:
        soup = BeautifulSoup(SAMPLE_UNPLAYED_MATCH_HTML, "lxml")

        with mock.patch("scraper.fetch_html", return_value=soup):
            details = scraper.parse_match_report(
                {
                    "match_id": "future-match",
                    "season": "2026",
                    "matchday": 32,
                    "url": "https://example.test/spielbericht/future-match",
                }
            )

        self.assertIsNone(details)


if __name__ == "__main__":
    unittest.main()
