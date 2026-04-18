import argparse
import logging
import random
import re
import sqlite3
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from db import get_connection, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = "https://www.transfermarkt.com"


def fetch_html(url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
    for _ in range(max_retries):
        try:
            time.sleep(random.uniform(2.0, 4.0))  # Polite scraping delay
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, "lxml")
            if response.status_code == 404:
                return None
            logging.warning(f"Failed to fetch {url} (Status: {response.status_code})")
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
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

        report_links = soup.select('a[title="Match report"], a[class*="liveLink"]')
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
    """Parse timeline events of a match (goals, cards, subs)."""
    events: List[Dict] = []

    for container_id in ["sb-tore", "sb-wechsel", "sb-karten"]:
        container = soup.select_one(f"#{container_id}")
        if not container:
            continue

        event_rows = container.select("li.sb-aktion-heim, li.sb-aktion-gast")
        for row in event_rows:
            try:
                is_home = "sb-aktion-heim" in row.get("class", [])
                team_indicator = "Home" if is_home else "Away"

                sprite_span = row.select_one(".sb-aktion-uhr span")
                minute = (
                    parse_minute_from_sprite(sprite_span.get("style", ""))
                    if sprite_span
                    else None
                )

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

                if "wechsel" in tm_event_type or "ein" in tm_event_type:
                    event_type = "Substitution"
                elif "gelbrot" in tm_event_type:
                    event_type = "Second Yellow Card"
                elif "gelb" in tm_event_type:
                    event_type = "Yellow Card"
                elif "rot" in tm_event_type:
                    event_type = "Red Card"
                elif "elfmeter" in tm_event_type:
                    event_type = "Penalty Goal"
                elif "verschossen" in tm_event_type:
                    event_type = "Missed Penalty"
                elif "tor" in tm_event_type:
                    event_type = "Goal"
                else:
                    event_type = tm_event_type

                players = [a.text.strip() for a in row.select("a.wichtig")]
                player_1 = players[0] if len(players) > 0 else ""
                player_2 = players[1] if len(players) > 1 else ""

                events.append(
                    {
                        "match_id": match_id,
                        "minute": minute,
                        "team": team_indicator,
                        "event_type": event_type,
                        "player_1": player_1,
                        "player_2": player_2,
                    }
                )
            except Exception as e:
                logging.error(f"Failed to parse event row in {match_id}: {e}")

    return events


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
            score_text = score_tag.contents[0].strip().split(":")
            if len(score_text) == 2:
                home_score = int(score_text[0])
                away_score = int(score_text[1])

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
                INSERT INTO events (match_id, minute, team, event_type, player_1, player_2)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        e["match_id"],
                        e["minute"],
                        e["team"],
                        e["event_type"],
                        e["player_1"],
                        e["player_2"],
                    )
                    for e in match_details["events"]
                ],
            )
    except sqlite3.Error as e:
        logging.error(f"DB Error on match {m['id']}: {e}")


def get_scraped_match_ids(conn: sqlite3.Connection) -> set:
    try:
        cursor = conn.execute("SELECT id FROM matches WHERE home_score >= 0")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return set()


def run_scraper(start_year: int, end_year: int) -> None:
    init_db()

    with get_connection() as conn:
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
                if match_data["match_id"] in scraped_ids:
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
    args = parser.parse_args()

    if args.end < args.start:
        parser.error("--end must be >= --start")

    run_scraper(args.start, args.end)


if __name__ == "__main__":
    main()
