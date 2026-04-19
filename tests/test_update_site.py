from datetime import UTC, datetime
from pathlib import Path
from unittest import mock
import unittest

import update_site


class UpdateSiteTests(unittest.TestCase):
    def test_infer_active_season_start_year_uses_previous_year_before_july(self) -> None:
        season_start = update_site.infer_active_season_start_year(
            datetime(2026, 4, 19, tzinfo=UTC)
        )

        self.assertEqual(season_start, 2025)

    def test_infer_active_season_start_year_uses_current_year_from_july(self) -> None:
        season_start = update_site.infer_active_season_start_year(
            datetime(2026, 7, 1, tzinfo=UTC)
        )

        self.assertEqual(season_start, 2026)

    @mock.patch("update_site.site_builder.build_site_db")
    @mock.patch("update_site.sofascore_scraper.run_scraper")
    def test_run_update_refreshes_requested_season_and_rebuilds_site_db(
        self,
        run_scraper: mock.Mock,
        build_site_db: mock.Mock,
    ) -> None:
        build_site_db.return_value = {"matches": 12, "events": 144}

        stats = update_site.run_update(season_start_year=2025)

        self.assertEqual(stats, {"matches": 12, "events": 144})
        run_scraper.assert_called_once_with(
            start_year=2025,
            end_year=2025,
            refresh=True,
            limit_matches=None,
            request_sleep=0.2,
        )
        build_site_db.assert_called_once_with(
            source="sofascore",
            target_db_path=update_site.site_db.DB_PATH,
            sofascore_db_path=update_site.sofascore_db.DB_PATH,
        )

    @mock.patch("update_site.subprocess.run")
    @mock.patch("update_site.site_builder.build_site_db")
    @mock.patch("update_site.sofascore_scraper.run_scraper")
    def test_run_update_can_trigger_frontend_build(
        self,
        run_scraper: mock.Mock,
        build_site_db: mock.Mock,
        subprocess_run: mock.Mock,
    ) -> None:
        update_site.run_update(
            season_start_year=2025,
            refresh=False,
            limit_matches=3,
            request_sleep=0.0,
            build_frontend=True,
        )

        run_scraper.assert_called_once_with(
            start_year=2025,
            end_year=2025,
            refresh=False,
            limit_matches=3,
            request_sleep=0.0,
        )
        build_site_db.assert_called_once()
        subprocess_run.assert_called_once_with(
            ["npm", "run", "build"],
            cwd=Path("/home/arda/projects/utils/tff/frontend"),
            check=True,
        )
