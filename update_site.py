import argparse
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import site_builder
import site_db
import sofascore_db
import sofascore_scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def infer_active_season_start_year(reference_time: datetime | None = None) -> int:
    current_time = reference_time or datetime.now(UTC)
    return current_time.year if current_time.month >= 7 else current_time.year - 1


def run_update(
    *,
    season_start_year: int,
    refresh: bool = True,
    limit_matches: int | None = None,
    request_sleep: float = 0.2,
    build_frontend: bool = False,
    target_db_path: Path | str = site_db.DB_PATH,
    sofascore_db_path: Path | str = sofascore_db.DB_PATH,
) -> dict[str, int]:
    logging.info("Refreshing SofaScore season %s", season_start_year)
    sofascore_scraper.run_scraper(
        start_year=season_start_year,
        end_year=season_start_year,
        refresh=refresh,
        limit_matches=limit_matches,
        request_sleep=request_sleep,
    )

    stats = site_builder.build_site_db(
        source="sofascore",
        target_db_path=target_db_path,
        sofascore_db_path=sofascore_db_path,
    )

    if build_frontend:
        logging.info("Building frontend assets")
        subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR, check=True)

    return stats


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh the latest SofaScore season and rebuild the canonical site DB."
    )
    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help="Season start year to update. Defaults to the inferred active season.",
    )
    parser.add_argument(
        "--refresh",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Re-fetch matches already stored in the SofaScore DB",
    )
    parser.add_argument(
        "--limit-matches",
        type=int,
        default=None,
        help="Optional cap for smoke tests",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Delay in seconds between incident requests",
    )
    parser.add_argument(
        "--frontend-build",
        action="store_true",
        help="Also run `npm run build` in the frontend directory",
    )
    parser.add_argument(
        "--target",
        default=str(site_db.DB_PATH),
        help="Path to the canonical output DB",
    )
    parser.add_argument(
        "--sofascore-db",
        default=str(sofascore_db.DB_PATH),
        help="Path to the SofaScore source DB",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    season_start_year = args.season or infer_active_season_start_year()

    stats = run_update(
        season_start_year=season_start_year,
        refresh=args.refresh,
        limit_matches=args.limit_matches,
        request_sleep=args.sleep,
        build_frontend=args.frontend_build,
        target_db_path=args.target,
        sofascore_db_path=args.sofascore_db,
    )

    logging.info(
        "Update complete for season %s (%s matches, %s events)",
        season_start_year,
        stats["matches"],
        stats["events"],
    )


if __name__ == "__main__":
    main()
