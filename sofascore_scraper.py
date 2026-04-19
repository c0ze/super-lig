import argparse
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

import requests

from sofascore_db import (
    DB_PATH,
    get_connection,
    get_existing_match_ids,
    init_db,
    save_match_bundle,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_API_URL = "https://api.sofascore.com/api/v1"
BASE_WEB_URL = "https://www.sofascore.com"
SPORT_SLUG = "football"
UNIQUE_TOURNAMENT_ID = 52
DEFAULT_TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def seasons_url() -> str:
    return f"{BASE_API_URL}/unique-tournament/{UNIQUE_TOURNAMENT_ID}/seasons"


def season_events_url(season_id: int, page: int) -> str:
    return (
        f"{BASE_API_URL}/unique-tournament/{UNIQUE_TOURNAMENT_ID}/season/"
        f"{season_id}/events/last/{page}"
    )


def match_incidents_url(match_id: int) -> str:
    return f"{BASE_API_URL}/event/{match_id}/incidents"


def parse_season_start_year(season_year: str) -> int:
    normalized = season_year.strip()
    if not normalized:
        raise ValueError("season year is empty")

    start_segment = normalized.split("/", 1)[0].strip()
    if len(start_segment) == 4 and start_segment.isdigit():
        return int(start_segment)
    if len(start_segment) == 2 and start_segment.isdigit():
        start_year = int(start_segment)
        century = 1900 if start_year >= 90 else 2000
        return century + start_year
    raise ValueError(f"Unsupported season year format: {season_year}")


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_json(
    session: requests.Session,
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 3,
    sleep_seconds: float = 0.5,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt == max_retries:
                break
            logging.warning("Retrying %s after error: %s", url, exc)
            time.sleep(sleep_seconds * attempt)
    raise RuntimeError(f"Failed to fetch JSON from {url}") from last_error


def get_target_seasons(
    session: requests.Session, start_year: int, end_year: int
) -> list[dict[str, Any]]:
    payload = fetch_json(session, seasons_url())
    seasons = []
    for season in payload.get("seasons", []):
        season_year = season.get("year") or season.get("name") or ""
        try:
            season_start_year = parse_season_start_year(season_year)
        except ValueError:
            continue
        if start_year <= season_start_year <= end_year:
            seasons.append({**season, "season_start_year": season_start_year})
    return sorted(seasons, key=lambda season: season["season_start_year"])


def fetch_season_events(session: requests.Session, season_id: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    page = 0

    while True:
        payload = fetch_json(session, season_events_url(season_id, page))
        page_events = payload.get("events", [])
        if not page_events:
            break

        for event in page_events:
            event_id = event.get("id")
            if event_id is None or event_id in seen_ids:
                continue
            seen_ids.add(event_id)
            events.append(event)

        if payload.get("hasNextPage") is False:
            break
        page += 1

    return events


def fetch_match_incidents(
    session: requests.Session, match_id: int
) -> list[dict[str, Any]]:
    payload = fetch_json(session, match_incidents_url(match_id))
    return payload.get("incidents", [])


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _bool_to_int(value: Any) -> int | None:
    if value is None:
        return None
    return 1 if bool(value) else 0


def _get_name(person: dict[str, Any] | None, fallback: str | None = None) -> str | None:
    if person and person.get("name"):
        return person["name"]
    return fallback


def normalize_match(event: dict[str, Any]) -> dict[str, Any]:
    season = event.get("season") or {}
    tournament = event.get("tournament") or {}
    unique_tournament = tournament.get("uniqueTournament") or {}
    home_team = event.get("homeTeam") or {}
    away_team = event.get("awayTeam") or {}
    status = event.get("status") or {}
    round_info = event.get("roundInfo") or {}
    home_score = event.get("homeScore") or {}
    away_score = event.get("awayScore") or {}

    season_year = season.get("year") or season.get("name") or ""
    season_start_year = parse_season_start_year(season_year)

    return {
        "id": event.get("id"),
        "season_id": season.get("id"),
        "season_name": season.get("name"),
        "season_year": season_year,
        "season_start_year": season_start_year,
        "round": round_info.get("round"),
        "start_timestamp": event.get("startTimestamp"),
        "status_code": status.get("code"),
        "status_description": status.get("description"),
        "status_type": status.get("type"),
        "winner_code": event.get("winnerCode"),
        "home_team_id": home_team.get("id"),
        "home_team_name": home_team.get("name"),
        "away_team_id": away_team.get("id"),
        "away_team_name": away_team.get("name"),
        "home_score": home_score.get("current"),
        "away_score": away_score.get("current"),
        "tournament_id": tournament.get("id"),
        "tournament_name": tournament.get("name"),
        "unique_tournament_id": unique_tournament.get("id"),
        "unique_tournament_name": unique_tournament.get("name"),
        "category_name": (tournament.get("category") or {}).get("name"),
        "custom_id": event.get("customId"),
        "slug": event.get("slug"),
        "url": (
            f"{BASE_WEB_URL}/{SPORT_SLUG}/match/{event.get('slug')}/"
            f"{event.get('customId')}#id:{event.get('id')}"
        ),
        "raw_json": _to_json(event),
    }


def normalize_incident(
    match_id: int, incident_order: int, incident: dict[str, Any]
) -> dict[str, Any]:
    player = incident.get("player") or {}
    player_in = incident.get("playerIn") or {}
    player_out = incident.get("playerOut") or {}
    assist_1 = incident.get("assist1") or {}

    return {
        "match_id": match_id,
        "incident_id": incident.get("id"),
        "incident_order": incident_order,
        "incident_type": incident.get("incidentType"),
        "incident_class": incident.get("incidentClass"),
        "time": incident.get("time"),
        "added_time": incident.get("addedTime"),
        "reversed_period_time": incident.get("reversedPeriodTime"),
        "is_home": _bool_to_int(incident.get("isHome")),
        "confirmed": _bool_to_int(incident.get("confirmed")),
        "rescinded": _bool_to_int(incident.get("rescinded")),
        "player_id": player.get("id"),
        "player_name": _get_name(player, incident.get("playerName")),
        "player_in_id": player_in.get("id"),
        "player_in_name": _get_name(player_in),
        "player_out_id": player_out.get("id"),
        "player_out_name": _get_name(player_out),
        "assist_1_id": assist_1.get("id"),
        "assist_1_name": _get_name(assist_1),
        "home_score": incident.get("homeScore"),
        "away_score": incident.get("awayScore"),
        "reason": incident.get("reason"),
        "text": incident.get("text"),
        "raw_json": _to_json(incident),
    }


def scrape_season(
    session: requests.Session,
    season: dict[str, Any],
    *,
    refresh: bool = False,
    limit_matches: int | None = None,
    request_sleep: float = 0.2,
) -> tuple[int, int]:
    season_id = season["id"]
    season_start_year = season["season_start_year"]
    logging.info(
        "Fetching SofaScore season %s (id=%s)", season.get("year"), season_id
    )
    season_events = fetch_season_events(session, season_id)
    if limit_matches is not None:
        season_events = season_events[:limit_matches]

    saved = 0
    skipped = 0

    with get_connection() as conn:
        existing_match_ids = set()
        if not refresh:
            existing_match_ids = get_existing_match_ids(
                conn, season_start_year=season_start_year
            )

        for event in season_events:
            match_id = event.get("id")
            if match_id is None:
                skipped += 1
                continue
            if not refresh and match_id in existing_match_ids:
                skipped += 1
                continue

            match_row = normalize_match(event)
            incidents = fetch_match_incidents(session, match_id)
            incident_rows = [
                normalize_incident(match_id, order, incident)
                for order, incident in enumerate(incidents, start=1)
            ]
            save_match_bundle(conn, match_row, incident_rows)
            conn.commit()
            saved += 1

            if request_sleep > 0:
                time.sleep(request_sleep)

    return saved, skipped


def run_scraper(
    *,
    start_year: int,
    end_year: int,
    refresh: bool = False,
    limit_matches: int | None = None,
    request_sleep: float = 0.2,
) -> None:
    init_db()
    session = create_session()
    seasons = get_target_seasons(session, start_year, end_year)
    if not seasons:
        logging.warning("No SofaScore seasons found between %s and %s", start_year, end_year)
        return

    total_saved = 0
    total_skipped = 0
    for season in seasons:
        saved, skipped = scrape_season(
            session,
            season,
            refresh=refresh,
            limit_matches=limit_matches,
            request_sleep=request_sleep,
        )
        total_saved += saved
        total_skipped += skipped

    logging.info(
        "Finished SofaScore scrape into %s (saved=%s, skipped=%s)",
        DB_PATH,
        total_saved,
        total_skipped,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    current_year = datetime.now(UTC).year
    parser = argparse.ArgumentParser(
        description="Scrape Turkish Super Lig matches and incidents from SofaScore."
    )
    parser.add_argument("--start", type=int, default=2010, help="Season start year")
    parser.add_argument(
        "--end",
        type=int,
        default=current_year,
        help="Season start year upper bound",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch matches already stored in the SofaScore database",
    )
    parser.add_argument(
        "--limit-matches",
        type=int,
        default=None,
        help="Optional cap per season, useful for smoke tests",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Delay in seconds between incident requests",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    run_scraper(
        start_year=args.start,
        end_year=args.end,
        refresh=args.refresh,
        limit_matches=args.limit_matches,
        request_sleep=args.sleep,
    )


if __name__ == "__main__":
    main()
