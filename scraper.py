import argparse
import logging
import random
import re
import sqlite3
import time
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from db import delete_unplayed_matches, get_connection, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

BASE_URL = "https://www.transfermarkt.com.tr"


def fetch_html(url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
    request_url = url.replace("://www.transfermarkt.com/", "://www.transfermarkt.com.tr/")
    for _ in range(max_retries):
        try:
            time.sleep(random.uniform(2.0, 4.0))  # Polite scraping delay
            response = requests.get(request_url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, "lxml")
            if response.status_code == 404:
                return None
            logging.warning(f"Failed to fetch {request_url} (Status: {response.status_code})")
        except requests.RequestException as e:
            logging.error(f"Error fetching {request_url}: {e}")
        time.sleep(5)
    return None


def parse_minute_from_sprite(style_str: str) -> Optional[int]:
    try:
        match = re.search(r"background-position:\s*(-?\d+)px\s*(-?\d+)px", style_str)
        if match:
            x = abs(int(match.group(1))) // 36
            y = abs(int(match.group(2))) // 36
            return (y * 10) + x + 1
    except Exception:
        pass
    return None


GOAL_EVENT_TYPES = {"Goal", "Penalty Goal"}


def normalize_space(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


def parse_minute_data(sprite_span: Optional[Tag]) -> Tuple[Optional[int], str, Optional[int], int]:
    if not sprite_span:
        return None, "", None, 0

    base_minute = parse_minute_from_sprite(sprite_span.get("style", ""))
    minute_text = normalize_space(sprite_span.get_text(" ", strip=True))
    extra_minute = 0

    if minute_text.startswith("+") and minute_text[1:].isdigit():
        extra_minute = int(minute_text[1:])
    elif base_minute is None and minute_text.isdigit():
        base_minute = int(minute_text)

    total_minute = (
        base_minute + extra_minute if base_minute is not None else None
    )
    minute_label = ""
    if base_minute is not None:
        minute_label = (
            f"{base_minute}+{extra_minute}" if extra_minute > 0 else str(base_minute)
        )
    elif minute_text:
        minute_label = minute_text

    return total_minute, minute_label, base_minute, extra_minute


def parse_score_text(raw_score: str) -> Optional[Tuple[int, int]]:
    match = re.search(r"(\d+)\s*:\s*(\d+)", raw_score)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def extract_player_names(container: Tag) -> List[str]:
    return [normalize_space(link.get_text(" ", strip=True)) for link in container.select("a.wichtig")]


def first_non_empty(parts: List[str]) -> str:
    for part in parts:
        cleaned = normalize_space(part).strip(" ,")
        if cleaned:
            return cleaned
    return ""


def remaining_csv_parts(text: str) -> List[str]:
    return [part for part in (normalize_space(chunk).strip(" ,") for chunk in text.split(",")) if part]


def parse_goal_details(action: Tag, player_1: str, player_2: str) -> Tuple[str, str]:
    action_text = normalize_space(action.get_text(" ", strip=True))
    first_segment, _, assist_segment = action_text.partition("Asist:")
    main_text = normalize_space(first_segment.replace(player_1, "", 1))
    subtype = first_non_empty(remaining_csv_parts(main_text))

    detail = ""
    if player_2:
        assist_rest = normalize_space(assist_segment.replace(player_2, "", 1)).strip(" ,")
        detail = "Asist: " + player_2
        if assist_rest:
            detail += ", " + assist_rest

    return subtype, detail


def parse_card_details(action: Tag, player_1: str) -> Tuple[str, str]:
    action_text = normalize_space(action.get_text(" ", strip=True))
    remainder = normalize_space(action_text.replace(player_1, "", 1))
    parts = remaining_csv_parts(remainder)
    subtype = parts[0] if parts else ""
    detail = ", ".join(parts[1:]) if len(parts) > 1 else ""
    return subtype, detail


def parse_substitution_details(action: Tag) -> Tuple[str, str, str]:
    in_span = action.select_one(".sb-aktion-wechsel-ein")
    out_span = action.select_one(".sb-aktion-wechsel-aus")
    player_in = ""
    player_out = ""
    reason = ""

    if in_span:
        player_in = first_non_empty(extract_player_names(in_span))
    if out_span:
        player_out = first_non_empty(extract_player_names(out_span))
        reason = normalize_space(out_span.get_text(" ", strip=True).replace(player_out, "", 1)).strip(" ,")

    return player_in, player_out, reason


def parse_missed_penalty_details(action: Tag) -> Tuple[str, str, str, str]:
    in_span = action.select_one(".sb-aktion-wechsel-ein")
    out_span = action.select_one(".sb-aktion-wechsel-aus")
    taker = ""
    goalkeeper = ""
    subtype = ""
    detail = ""

    if in_span:
        taker = first_non_empty(extract_player_names(in_span))
        subtype = normalize_space(in_span.get_text(" ", strip=True).replace(taker, "", 1)).strip(" ,")
    if out_span:
        goalkeeper = first_non_empty(extract_player_names(out_span))
        detail = normalize_space(out_span.get_text(" ", strip=True).replace(goalkeeper, "", 1)).strip(" ,")

    return taker, goalkeeper, subtype, detail


def normalize_event_type(container_id: str, raw_event_type: str, subtype: str) -> str:
    lowered_type = raw_event_type.lower()
    lowered_subtype = subtype.lower()

    if container_id == "sb-verschossene" or "11m" in lowered_type or "verschossen" in lowered_type:
        return "Missed Penalty"
    if "wechsel" in lowered_type or "ein" in lowered_type:
        return "Substitution"
    if "gelbrot" in lowered_type:
        return "Second Yellow Card"
    if "gelb" in lowered_type:
        return "Yellow Card"
    if "rot" in lowered_type:
        return "Red Card"
    if "elfmeter" in lowered_type or "penalt" in lowered_subtype:
        return "Penalty Goal"
    if container_id == "sb-tore" or "tor" in lowered_type:
        return "Goal"

    return raw_event_type


def score_state_from_event(current_home: int, current_away: int, event: Dict) -> Tuple[int, int, int, int]:
    if event["event_type"] not in GOAL_EVENT_TYPES:
        return current_home, current_away, current_home, current_away

    parsed_after = event.get("_score_after")
    if parsed_after:
        home_after, away_after = parsed_after
        if event["team"] == "Home":
            home_before, away_before = max(home_after - 1, 0), away_after
        else:
            home_before, away_before = home_after, max(away_after - 1, 0)
        return home_before, away_before, home_after, away_after

    if event["team"] == "Home":
        return current_home, current_away, current_home + 1, current_away
    if event["team"] == "Away":
        return current_home, current_away, current_home, current_away + 1
    return current_home, current_away, current_home, current_away


def annotate_event_scores(events: List[Dict]) -> List[Dict]:
    sorted_events = sorted(
        events,
        key=lambda event: (
            event["minute"] if event["minute"] is not None else 999,
            1 if event["event_type"] in GOAL_EVENT_TYPES else 0,
            event.get("_section_rank", 0),
            event.get("_row_index", 0),
        ),
    )

    current_home = 0
    current_away = 0
    annotated_events: List[Dict] = []

    for order, event in enumerate(sorted_events, start=1):
        home_before, away_before, home_after, away_after = score_state_from_event(
            current_home,
            current_away,
            event,
        )

        current_home = home_after
        current_away = away_after

        clean_event = {
            key: value
            for key, value in event.items()
            if not key.startswith("_")
        }
        clean_event["event_order"] = order
        clean_event["home_score_before"] = home_before
        clean_event["away_score_before"] = away_before
        clean_event["home_score_after"] = home_after
        clean_event["away_score_after"] = away_after
        annotated_events.append(clean_event)

    return annotated_events


def get_season_match_urls(season_start_year: int) -> List[Dict]:
    """
    Given a season start year (e.g., 2010), return a list of match report URLs.
    """
    matches = []
    for matchday in range(1, 43):
        url = (
            f"{BASE_URL}/super-lig/spieltagtabelle/wettbewerb/TR1"
            f"/saison_id/{season_start_year}/spieltag/{matchday}"
        )
        logging.info(f"Fetching Matchday {matchday} for season {season_start_year}...")
        soup = fetch_html(url)
        if not soup:
            break

        report_links = soup.select('a[href*="spielbericht"], a[class*="liveLink"]')
        seen_urls = set()
        found_any = False

        for link in report_links:
            href = link.get("href")
            if href and "spielbericht" in href:
                full_url = f"{BASE_URL}{href}"
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                match_id = href.split("/")[-1]
                matches.append(
                    {
                        "match_id": match_id,
                        "url": full_url,
                        "season": str(season_start_year),
                        "matchday": matchday,
                    }
                )
                found_any = True

        if not found_any:
            logging.info(
                f"No more matches found on matchday {matchday}. Proceeding to next season."
            )
            break

    return matches


def parse_match_events(soup: BeautifulSoup, match_id: str) -> List[Dict]:
    """Parse timeline events of a match with rich details and score state."""
    events: List[Dict] = []

    section_order = {
        "sb-karten": 0,
        "sb-wechsel": 1,
        "sb-tore": 2,
        "sb-verschossene": 3,
    }

    for container_id in ["sb-tore", "sb-wechsel", "sb-karten", "sb-verschossene"]:
        container = soup.select_one(f"#{container_id}")
        if not container:
            continue

        event_rows = container.select("li.sb-aktion-heim, li.sb-aktion-gast")
        for row_index, row in enumerate(event_rows):
            try:
                is_home = "sb-aktion-heim" in row.get("class", [])
                team_indicator = "Home" if is_home else "Away"

                sprite_span = row.select_one(".sb-aktion-uhr span")
                minute, minute_label, minute_base, minute_extra = parse_minute_data(
                    sprite_span
                )

                action = row.select_one(".sb-aktion-aktion")
                if not action:
                    continue

                icon = row.select_one(
                    ".sb-aktion-spielstand span.sb-sprite, "
                    ".sb-aktion-aktion span.sb-sprite"
                )
                icon_classes = icon.get("class", []) if icon else []
                tm_event_type = (
                    icon_classes[1].replace("sb-", "")
                    if len(icon_classes) > 1
                    else container_id.replace("sb-", "")
                )

                player_1 = ""
                player_2 = ""
                event_subtype = ""
                event_detail = ""

                if container_id == "sb-wechsel":
                    player_1, player_2, event_detail = parse_substitution_details(action)
                    event_subtype = event_detail
                elif container_id == "sb-verschossene":
                    player_1, player_2, event_subtype, event_detail = parse_missed_penalty_details(action)
                else:
                    players = extract_player_names(action)
                    player_1 = players[0] if len(players) > 0 else ""
                    player_2 = players[1] if len(players) > 1 else ""
                    if container_id == "sb-tore":
                        event_subtype, event_detail = parse_goal_details(action, player_1, player_2)
                    elif container_id == "sb-karten":
                        event_subtype, event_detail = parse_card_details(action, player_1)

                event_type = normalize_event_type(container_id, tm_event_type, event_subtype)
                score_after = None
                if event_type in GOAL_EVENT_TYPES:
                    score_tag = row.select_one(".sb-aktion-spielstand b")
                    score_after = parse_score_text(score_tag.get_text(" ", strip=True)) if score_tag else None

                events.append(
                    {
                        "match_id": match_id,
                        "minute": minute,
                        "minute_label": minute_label,
                        "minute_base": minute_base,
                        "minute_extra": minute_extra,
                        "team": team_indicator,
                        "event_type": event_type,
                        "player_1": player_1,
                        "player_2": player_2,
                        "event_subtype": event_subtype,
                        "event_detail": event_detail,
                        "_score_after": score_after,
                        "_section_rank": section_order.get(container_id, 0),
                        "_row_index": row_index,
                    }
                )
            except Exception as e:
                logging.error(f"Failed to parse event row in {match_id}: {e}")

    return annotate_event_scores(events)


def parse_match_report(match_data: Dict) -> Optional[Dict]:
    """Parse the match report to extract scores, dates, and events."""
    logging.info(f"Parsing match '{match_data['match_id']}'...")
    soup = fetch_html(match_data["url"])
    if not soup:
        return None

    try:
        date_tag = soup.select_one(".sb-spieldaten p.sb-datum a")
        if not date_tag:
            date_tag = soup.select_one(".sb-spieldaten a")
        match_date = date_tag.text.strip() if date_tag else ""

        home_team_tag = soup.select_one(".sb-team.sb-heim .sb-vereinslink")
        away_team_tag = soup.select_one(".sb-team.sb-gast .sb-vereinslink")
        home_team = home_team_tag.text.strip() if home_team_tag else "Unknown Home"
        away_team = away_team_tag.text.strip() if away_team_tag else "Unknown Away"

        score_tag = soup.select_one(".sb-ergebnis .sb-endstand")
        home_score = away_score = -1
        if score_tag:
            raw_score = normalize_space(score_tag.get_text(" ", strip=True))
            parsed_score = parse_score_text(raw_score)
            if parsed_score is None:
                logging.info(
                    "Skipping unplayed match '%s' with score placeholder '%s'.",
                    match_data["match_id"],
                    raw_score,
                )
                return None
            home_score, away_score = parsed_score

        events = parse_match_events(soup, match_data["match_id"])

        return {
            "match": {
                "id": match_data["match_id"],
                "season": match_data["season"],
                "matchday": match_data["matchday"],
                "date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "url": match_data["url"],
            },
            "events": events,
        }
    except Exception as e:
        logging.error(f"Error parsing match {match_data['match_id']}: {e}")
        return None


def save_to_db(conn: sqlite3.Connection, match_details: Dict) -> None:
    m = match_details["match"]
    try:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO matches
                (id, season, matchday, date, home_team, away_team, home_score, away_score, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    m["id"],
                    m["season"],
                    m["matchday"],
                    m["date"],
                    m["home_team"],
                    m["away_team"],
                    m["home_score"],
                    m["away_score"],
                    m["url"],
                ),
            )
            conn.execute("DELETE FROM events WHERE match_id = ?", (m["id"],))
            conn.executemany(
                """
                INSERT INTO events (
                    match_id, minute, minute_label, minute_base, minute_extra, team, event_type,
                    event_order, event_subtype, event_detail, player_1, player_2,
                    home_score_before, away_score_before, home_score_after, away_score_after
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        e["match_id"],
                        e["minute"],
                        e["minute_label"],
                        e["minute_base"],
                        e["minute_extra"],
                        e["team"],
                        e["event_type"],
                        e["event_order"],
                        e["event_subtype"],
                        e["event_detail"],
                        e["player_1"],
                        e["player_2"],
                        e["home_score_before"],
                        e["away_score_before"],
                        e["home_score_after"],
                        e["away_score_after"],
                    )
                    for e in match_details["events"]
                ],
            )
    except sqlite3.Error as e:
        logging.error(f"DB Error on match {m['id']}: {e}")


def backfill_existing_event_metadata(conn: sqlite3.Connection) -> None:
    event_columns = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    if not {"event_order", "home_score_before", "away_score_before"}.issubset(event_columns):
        return

    match_ids = [
        row[0]
        for row in conn.execute(
            """
            SELECT DISTINCT match_id
            FROM events
            WHERE event_order IS NULL
               OR minute_label IS NULL
               OR home_score_before IS NULL
               OR away_score_before IS NULL
               OR home_score_after IS NULL
               OR away_score_after IS NULL
               OR event_subtype IS NULL
               OR event_detail IS NULL
            """
        ).fetchall()
    ]
    if not match_ids:
        return

    logging.info("Backfilling event metadata for %s existing matches...", len(match_ids))

    with conn:
        for (match_id,) in [(match_id,) for match_id in match_ids]:
            rows = conn.execute(
                """
                SELECT id, minute, team, event_type, player_1, player_2,
                       minute_label, minute_base, minute_extra, event_subtype, event_detail
                FROM events
                WHERE match_id = ?
                ORDER BY minute ASC, id ASC
                """,
                (match_id,),
            ).fetchall()

            events = []
            for row_index, row in enumerate(rows):
                (
                    event_id,
                    minute,
                    team,
                    event_type,
                    player_1,
                    player_2,
                    minute_label,
                    minute_base,
                    minute_extra,
                    event_subtype,
                    event_detail,
                ) = row
                normalized_type = event_type
                normalized_subtype = event_subtype or ""

                if (
                    event_type == "Goal"
                    and player_1
                    and player_1 == player_2
                    and not normalized_subtype
                ):
                    normalized_type = "Penalty Goal"
                    normalized_subtype = "Penaltı"

                base_minute = minute_base if minute_base is not None else minute
                extra_minute = minute_extra if minute_extra is not None else 0
                label = minute_label or (str(base_minute) if base_minute is not None else "")

                events.append(
                    {
                        "id": event_id,
                        "match_id": match_id,
                        "minute": minute,
                        "minute_label": label,
                        "minute_base": base_minute,
                        "minute_extra": extra_minute,
                        "team": team,
                        "event_type": normalized_type,
                        "player_1": player_1 or "",
                        "player_2": player_2 or "",
                        "event_subtype": normalized_subtype,
                        "event_detail": event_detail or "",
                        "_section_rank": 0,
                        "_row_index": row_index,
                    }
                )

            for event in annotate_event_scores(events):
                conn.execute(
                    """
                    UPDATE events
                    SET minute_label = ?,
                        minute_base = ?,
                        minute_extra = ?,
                        event_type = ?,
                        event_order = ?,
                        event_subtype = ?,
                        event_detail = ?,
                        home_score_before = ?,
                        away_score_before = ?,
                        home_score_after = ?,
                        away_score_after = ?
                    WHERE id = ?
                    """,
                    (
                        event["minute_label"],
                        event["minute_base"],
                        event["minute_extra"],
                        event["event_type"],
                        event["event_order"],
                        event["event_subtype"],
                        event["event_detail"],
                        event["home_score_before"],
                        event["away_score_before"],
                        event["home_score_after"],
                        event["away_score_after"],
                        event["id"],
                    ),
                )


def get_scraped_match_ids(conn: sqlite3.Connection) -> set:
    try:
        cursor = conn.execute("SELECT id FROM matches WHERE home_score >= 0")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return set()


def run_scraper(start_year: int, end_year: int, refresh: bool = False) -> None:
    init_db()

    with get_connection() as conn:
        removed_unplayed = delete_unplayed_matches(conn)
        if removed_unplayed > 0:
            logging.info("Removed %s unplayed matches from the database.", removed_unplayed)
        backfill_existing_event_metadata(conn)
        scraped_ids = get_scraped_match_ids(conn)
        logging.info(
            f"Found {len(scraped_ids)} already completely scraped matches. "
            "They will be skipped."
        )

        for year in range(start_year, end_year + 1):
            logging.info(f"--- Starting Season {year} ---")
            matches = get_season_match_urls(year)
            logging.info(
                f"Found {len(matches)} matches for season {year}. Proceeding to parse..."
            )

            for match_data in matches:
                if not refresh and match_data["match_id"] in scraped_ids:
                    logging.debug(
                        f"Skipping match {match_data['match_id']} (already scraped)."
                    )
                    continue

                details = parse_match_report(match_data)
                if details:
                    save_to_db(conn, details)
                    if details["match"]["home_score"] >= 0:
                        scraped_ids.add(details["match"]["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Turkish Super Lig data from Transfermarkt.")
    parser.add_argument("--start", type=int, default=2010, help="Season start year (inclusive).")
    parser.add_argument("--end", type=int, default=2025, help="Season end year (inclusive).")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-scrape matches even if they already exist in the database.",
    )
    args = parser.parse_args()

    if args.end < args.start:
        parser.error("--end must be >= --start")

    run_scraper(args.start, args.end, refresh=args.refresh)


if __name__ == "__main__":
    main()
