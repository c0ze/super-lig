import argparse
import logging
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import db as transfermarkt_db
import site_db
import sofascore_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

GOAL_EVENT_TYPES = {"Goal", "Penalty Goal", "Own Goal"}
SUPPORTED_SOURCES = {"sofascore", "transfermarkt"}
SKIPPED_SOFASCORE_STATUSES = {"Postponed", "Canceled"}


def format_match_date(start_timestamp: int | None) -> str:
    if start_timestamp is None:
        return ""
    return datetime.fromtimestamp(start_timestamp, UTC).strftime("%Y-%m-%d %H:%M UTC")


def total_minute(minute_base: int | None, minute_extra: int) -> int | None:
    if minute_base is None:
        return None
    return minute_base + minute_extra


def minute_fields(time_value: int | None, added_time: int | None) -> tuple[int | None, str, int | None, int]:
    minute_base = time_value
    minute_extra = added_time or 0
    minute = total_minute(minute_base, minute_extra)
    if minute_base is None:
        return None, "", None, 0
    minute_label = (
        f"{minute_base}+{minute_extra}" if minute_extra > 0 else str(minute_base)
    )
    return minute, minute_label, minute_base, minute_extra


def title_case(text: str | None) -> str:
    if not text:
        return ""
    normalized = " ".join(text.replace("_", " ").split())
    if not normalized:
        return ""
    return normalized[0].upper() + normalized[1:]


def should_include_sofascore_match(match_row: sqlite3.Row) -> bool:
    if match_row["home_score"] is None or match_row["away_score"] is None:
        return False
    return match_row["status_description"] not in SKIPPED_SOFASCORE_STATUSES


def transfermarkt_event_type(row: sqlite3.Row) -> str:
    event_type = row["event_type"]
    subtype = (row["event_subtype"] or "").strip().lower()
    if event_type == "Goal" and subtype == "kendi kalesine gol":
        return "Own Goal"
    return event_type


def normalize_transfermarkt_match(match_row: sqlite3.Row) -> dict:
    return {
        "id": str(match_row["id"]),
        "season": match_row["season"],
        "matchday": match_row["matchday"],
        "date": match_row["date"] or "",
        "home_team": match_row["home_team"],
        "away_team": match_row["away_team"],
        "home_score": match_row["home_score"],
        "away_score": match_row["away_score"],
        "url": match_row["url"] or "",
    }


def normalize_transfermarkt_event(event_row: sqlite3.Row) -> dict:
    return {
        "match_id": str(event_row["match_id"]),
        "minute": event_row["minute"],
        "minute_label": event_row["minute_label"] or "",
        "minute_base": event_row["minute_base"],
        "minute_extra": event_row["minute_extra"] or 0,
        "team": event_row["team"] or "",
        "event_type": transfermarkt_event_type(event_row),
        "event_order": event_row["event_order"],
        "event_subtype": event_row["event_subtype"] or "",
        "event_detail": event_row["event_detail"] or "",
        "player_1": event_row["player_1"] or "",
        "player_2": event_row["player_2"] or "",
        "home_score_before": event_row["home_score_before"],
        "away_score_before": event_row["away_score_before"],
        "home_score_after": event_row["home_score_after"],
        "away_score_after": event_row["away_score_after"],
    }


def normalize_sofascore_match(match_row: sqlite3.Row) -> dict:
    return {
        "id": str(match_row["id"]),
        "season": str(match_row["season_start_year"]),
        "matchday": match_row["round"],
        "date": format_match_date(match_row["start_timestamp"]),
        "home_team": match_row["home_team_name"],
        "away_team": match_row["away_team_name"],
        "home_score": match_row["home_score"],
        "away_score": match_row["away_score"],
        "url": match_row["url"] or "",
    }


def canonical_team(is_home: int | None) -> str:
    return "Home" if bool(is_home) else "Away"


def var_decision_detail(confirmed: int | None, rescinded: int | None) -> str:
    if rescinded:
        return "rescinded"
    if confirmed == 1:
        return "confirmed"
    if confirmed == 0:
        return "overturned"
    return ""


def normalize_sofascore_incident(incident_row: sqlite3.Row) -> dict | None:
    incident_type = incident_row["incident_type"]
    incident_class = incident_row["incident_class"] or ""
    minute, minute_label, minute_base, minute_extra = minute_fields(
        incident_row["time"], incident_row["added_time"]
    )

    if incident_type == "goal":
        own_goal = incident_class == "ownGoal"
        event_type = (
            "Penalty Goal"
            if incident_class == "penalty"
            else "Own Goal"
            if own_goal
            else "Goal"
        )
        return {
            "_source_order": incident_row["incident_order"],
            "_score_after": (
                incident_row["home_score"],
                incident_row["away_score"],
            ),
            "minute": minute,
            "minute_label": minute_label,
            "minute_base": minute_base,
            "minute_extra": minute_extra,
            "team": canonical_team(incident_row["is_home"]),
            "event_type": event_type,
            "event_subtype": "own_goal" if own_goal else "",
            "event_detail": "",
            "player_1": incident_row["player_name"] or "",
            "player_2": incident_row["assist_1_name"] or "",
        }

    if incident_type == "inGamePenalty" and incident_class == "missed":
        return {
            "_source_order": incident_row["incident_order"],
            "minute": minute,
            "minute_label": minute_label,
            "minute_base": minute_base,
            "minute_extra": minute_extra,
            "team": canonical_team(incident_row["is_home"]),
            "event_type": "Missed Penalty",
            "event_subtype": "missed",
            "event_detail": title_case(incident_row["reason"]),
            "player_1": incident_row["player_name"] or "",
            "player_2": "",
        }

    if incident_type == "card":
        event_type = {
            "yellow": "Yellow Card",
            "yellowRed": "Second Yellow Card",
            "red": "Red Card",
        }.get(incident_class)
        if not event_type:
            return None
        return {
            "_source_order": incident_row["incident_order"],
            "minute": minute,
            "minute_label": minute_label,
            "minute_base": minute_base,
            "minute_extra": minute_extra,
            "team": canonical_team(incident_row["is_home"]),
            "event_type": event_type,
            "event_subtype": incident_class,
            "event_detail": title_case(incident_row["reason"]),
            "player_1": incident_row["player_name"] or "",
            "player_2": "",
        }

    if incident_type == "substitution":
        return {
            "_source_order": incident_row["incident_order"],
            "minute": minute,
            "minute_label": minute_label,
            "minute_base": minute_base,
            "minute_extra": minute_extra,
            "team": canonical_team(incident_row["is_home"]),
            "event_type": "Substitution",
            "event_subtype": incident_class or "",
            "event_detail": "Injury" if incident_class == "injury" else "",
            "player_1": incident_row["player_in_name"] or "",
            "player_2": incident_row["player_out_name"] or "",
        }

    if incident_type == "varDecision":
        return {
            "_source_order": incident_row["incident_order"],
            "minute": minute,
            "minute_label": minute_label,
            "minute_base": minute_base,
            "minute_extra": minute_extra,
            "team": canonical_team(incident_row["is_home"]),
            "event_type": "VAR Decision",
            "event_subtype": incident_class,
            "event_detail": var_decision_detail(
                incident_row["confirmed"], incident_row["rescinded"]
            ),
            "player_1": incident_row["player_name"] or "",
            "player_2": "",
        }

    return None


def sofascore_event_sort_key(event: dict) -> tuple:
    minute = event["minute"] if event["minute"] is not None else 999
    goal_priority = 0 if event["event_type"] in GOAL_EVENT_TYPES else 1
    return (minute, goal_priority, -event["_source_order"])


def annotate_event_scores(events: list[dict], match_id: str) -> list[dict]:
    sorted_events = sorted(events, key=sofascore_event_sort_key)
    current_home = 0
    current_away = 0
    annotated_events = []

    for event_order, event in enumerate(sorted_events, start=1):
        home_before = current_home
        away_before = current_away
        home_after = current_home
        away_after = current_away

        if event["event_type"] in GOAL_EVENT_TYPES:
            score_after = event.get("_score_after")
            if score_after is not None:
                home_after, away_after = score_after
                if event["team"] == "Home":
                    home_before = max(home_after - 1, 0)
                    away_before = away_after
                else:
                    home_before = home_after
                    away_before = max(away_after - 1, 0)
            elif event["team"] == "Home":
                home_after = current_home + 1
            else:
                away_after = current_away + 1

            current_home = home_after
            current_away = away_after

        clean_event = {
            "match_id": match_id,
            "minute": event["minute"],
            "minute_label": event["minute_label"],
            "minute_base": event["minute_base"],
            "minute_extra": event["minute_extra"],
            "team": event["team"],
            "event_type": event["event_type"],
            "event_order": event_order,
            "event_subtype": event["event_subtype"],
            "event_detail": event["event_detail"],
            "player_1": event["player_1"],
            "player_2": event["player_2"],
            "home_score_before": home_before,
            "away_score_before": away_before,
            "home_score_after": home_after,
            "away_score_after": away_after,
        }
        annotated_events.append(clean_event)

    return annotated_events


def build_from_transfermarkt(
    target_conn: sqlite3.Connection, source_db_path: Path | str
) -> dict[str, int]:
    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row

    matches = source_conn.execute(
        """
        SELECT id, season, matchday, date, home_team, away_team, home_score, away_score, url
        FROM matches
        ORDER BY CAST(season AS INTEGER) ASC, matchday ASC, id ASC
        """
    ).fetchall()
    raw_events = source_conn.execute(
        """
        SELECT match_id, minute, minute_label, minute_base, minute_extra, team, event_type,
               event_order, event_subtype, event_detail, player_1, player_2,
               home_score_before, away_score_before, home_score_after, away_score_after, id
        FROM events
        ORDER BY match_id ASC, COALESCE(event_order, id) ASC, id ASC
        """
    ).fetchall()
    source_conn.close()

    events_by_match: dict[str, list[dict]] = defaultdict(list)
    for event_row in raw_events:
        normalized = normalize_transfermarkt_event(event_row)
        events_by_match[normalized["match_id"]].append(normalized)

    match_count = 0
    event_count = 0
    for match_row in matches:
        canonical_match = normalize_transfermarkt_match(match_row)
        event_rows = events_by_match.get(canonical_match["id"], [])
        site_db.save_match_bundle(target_conn, canonical_match, event_rows)
        match_count += 1
        event_count += len(event_rows)

    return {"matches": match_count, "events": event_count}


def build_from_sofascore(
    target_conn: sqlite3.Connection, source_db_path: Path | str
) -> dict[str, int]:
    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row

    matches = [
        row
        for row in source_conn.execute(
            """
            SELECT id, season_start_year, season_year, round, start_timestamp, status_code,
                   status_description, status_type, home_team_name, away_team_name,
                   home_score, away_score, url
            FROM matches
            ORDER BY season_start_year ASC, round ASC, start_timestamp ASC, id ASC
            """
        ).fetchall()
        if should_include_sofascore_match(row)
    ]

    incidents_by_match: dict[int, list[dict]] = defaultdict(list)
    for incident_row in source_conn.execute(
        """
        SELECT match_id, incident_order, incident_type, incident_class, time, added_time,
               reversed_period_time, is_home, confirmed, rescinded, player_name,
               player_in_name, player_out_name, assist_1_name, home_score, away_score,
               reason, text
        FROM incidents
        ORDER BY match_id ASC, incident_order ASC, id ASC
        """
    ):
        normalized = normalize_sofascore_incident(incident_row)
        if normalized is None:
            continue
        incidents_by_match[incident_row["match_id"]].append(normalized)

    source_conn.close()

    match_count = 0
    event_count = 0
    for match_row in matches:
        canonical_match = normalize_sofascore_match(match_row)
        event_rows = annotate_event_scores(
            incidents_by_match.get(match_row["id"], []),
            canonical_match["id"],
        )
        site_db.save_match_bundle(target_conn, canonical_match, event_rows)
        match_count += 1
        event_count += len(event_rows)

    return {"matches": match_count, "events": event_count}


def build_site_db(
    *,
    source: str,
    target_db_path: Path | str = site_db.DB_PATH,
    sofascore_db_path: Path | str = sofascore_db.DB_PATH,
    transfermarkt_db_path: Path | str = transfermarkt_db.DB_PATH,
) -> dict[str, int]:
    normalized_source = source.lower()
    if normalized_source not in SUPPORTED_SOURCES:
        raise ValueError(
            f"Unsupported source '{source}'. Expected one of: {', '.join(sorted(SUPPORTED_SOURCES))}"
        )

    target_db_path = Path(target_db_path)
    site_db.init_db(target_db_path, recreate=True)

    with site_db.get_connection(target_db_path) as target_conn:
        if normalized_source == "sofascore":
            stats = build_from_sofascore(target_conn, sofascore_db_path)
        else:
            stats = build_from_transfermarkt(target_conn, transfermarkt_db_path)

        site_db.replace_metadata(
            target_conn,
            {
                "built_at": datetime.now(UTC).isoformat(),
                "source": normalized_source,
            },
        )
        target_conn.commit()

    logging.info(
        "Built canonical site DB at %s from %s (%s matches, %s events)",
        target_db_path,
        normalized_source,
        stats["matches"],
        stats["events"],
    )
    return stats


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the canonical site DB used by the frontend."
    )
    parser.add_argument(
        "--source",
        choices=sorted(SUPPORTED_SOURCES),
        default="sofascore",
        help="Source database adapter to use",
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
    parser.add_argument(
        "--transfermarkt-db",
        default=str(transfermarkt_db.DB_PATH),
        help="Path to the Transfermarkt source DB",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    build_site_db(
        source=args.source,
        target_db_path=args.target,
        sofascore_db_path=args.sofascore_db,
        transfermarkt_db_path=args.transfermarkt_db,
    )


if __name__ == "__main__":
    main()
