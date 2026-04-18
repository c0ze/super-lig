import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import sqlite3
from typing import List, Dict, Optional
from db import init_db, get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_URL = "https://www.transfermarkt.com"

def fetch_html(url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(2.0, 4.0)) # Polite scraping delay
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'lxml')
            else:
                logging.warning(f"Failed to fetch {url} (Status: {response.status_code})")
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
        time.sleep(5)
    return None

def get_season_match_urls(season_start_year: int) -> List[Dict]:
    """
    Given a season start year (e.g., 2010), return a list of match report URLs.
    """
    matches = []
    # Transfermarkt pagination structure for matchdays
    # Example: https://www.transfermarkt.com/super-lig/spieltagtabelle/wettbewerb/TR1/saison_id/2010/spieltag/1
    # Super Lig historically has had 34 to 40+ matchdays depending on the season format.
    # We will loop through matchdays until we get a 404 or a page with no matches.
    for matchday in range(1, 43):
        url = f"{BASE_URL}/super-lig/spieltagtabelle/wettbewerb/TR1/saison_id/{season_start_year}/spieltag/{matchday}"
        logging.info(f"Fetching Matchday {matchday} for season {season_start_year}...")
        soup = fetch_html(url)
        if not soup:
            break
            
        # Find match anchors within the match results table
        # Typical Transfermarkt structure: `<a title="Match report" href="/galatasaray-a-s-sivasspor/spielbericht/1057482" class="liveLink">...</a>`
        report_links = soup.select('a[title="Match report"], a[class*="liveLink"]')
        found_any = False
        
        seen_urls = set()
        for link in report_links:
            href = link.get('href')
            if href and 'spielbericht' in href:
                full_url = f"{BASE_URL}{href}"
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    match_id = href.split('/')[-1]
                    matches.append({
                        'match_id': match_id,
                        'url': full_url,
                        'season': str(season_start_year),
                        'matchday': matchday
                    })
                    found_any = True
                    
        if not found_any:
            # Reached a matchday that doesn't exist for this season
            logging.info(f"No more matches found on matchday {matchday}. Proceeding to next season.")
            break
            
    return matches

import re



def parse_minute_from_sprite(style_str: str) -> Optional[int]:
    try:
        match = re.search(r'background-position:\s*(-?\d+)px\s*(-?\d+)px', style_str)
        if match:
            x = abs(int(match.group(1))) // 36
            y = abs(int(match.group(2))) // 36
            return (y * 10) + x + 1
    except:
        pass
    return None

def parse_match_events(soup: BeautifulSoup, match_id: str) -> List[Dict]:
    """
    Parse timeline events of a match (goals, cards, subs)
    """
    events = []
    
    for container_id in ['sb-tore', 'sb-wechsel', 'sb-karten']:
        container = soup.select_one(f'#{container_id}')
        if not container:
            continue
            
        event_rows = container.select('li.sb-aktion-heim, li.sb-aktion-gast')
        for row in event_rows:
            try:
                is_home = 'sb-aktion-heim' in row.get('class', [])
                team_indicator = 'Home' if is_home else 'Away'
                
                # Minute
                sprite_span = row.select_one('.sb-aktion-uhr span')
                minute = parse_minute_from_sprite(sprite_span.get('style', '')) if sprite_span else None
                
                # Event type icon
                icon = row.select_one('.sb-aktion-spielstand span.sb-sprite, .sb-aktion-aktion span.sb-sprite')
                tm_event_type = icon.get('class', [''])[1].replace('sb-', '') if icon and len(icon.get('class', [])) > 1 else container_id.replace('sb-', '')
                
                # Match to friendly name
                if 'wechsel' in tm_event_type or 'ein' in tm_event_type:
                    event_type = 'Substitution'
                elif 'gelbrot' in tm_event_type:
                    event_type = 'Second Yellow Card'
                elif 'gelb' in tm_event_type:
                    event_type = 'Yellow Card'
                elif 'rot' in tm_event_type:
                    event_type = 'Red Card'
                elif 'elfmeter' in tm_event_type:
                    event_type = 'Penalty Goal'
                elif 'verschossen' in tm_event_type:
                    event_type = 'Missed Penalty'
                elif 'tor' in tm_event_type:
                    event_type = 'Goal'
                else:
                    event_type = tm_event_type
                
                # Find players involved
                players = [a.text.strip() for a in row.select('a.wichtig')]
                player_1 = players[0] if len(players) > 0 else ""
                player_2 = players[1] if len(players) > 1 else ""
                
                events.append({
                    'match_id': match_id,
                    'minute': minute,
                    'team': team_indicator,
                    'event_type': event_type,
                    'player_1': player_1,
                    'player_2': player_2,
                    'description': ""
                })
            except Exception as e:
                logging.error(f"Failed to parse event row in {match_id}: {e}")
            
    return events

def parse_match_report(match_data: Dict) -> Optional[Dict]:
    """
    Parse the match report to extract scores, dates, and events.
    """
    logging.info(f"Parsing match '{match_data['match_id']}'...")
    soup = fetch_html(match_data['url'])
    if not soup:
        return None
        
    try:
        # Extract Date
        date_tag = soup.select_one('.sb-spieldaten p.sb-datum a')
        if not date_tag:
            date_tag = soup.select_one('.sb-spieldaten a')
        match_date = date_tag.text.strip() if date_tag else ""
        
        # Extract teams
        home_team_tag = soup.select_one('.sb-team.sb-heim .sb-vereinslink')
        away_team_tag = soup.select_one('.sb-team.sb-gast .sb-vereinslink')
        home_team = home_team_tag.text.strip() if home_team_tag else "Unknown Home"
        away_team = away_team_tag.text.strip() if away_team_tag else "Unknown Away"
        
        # Extract score
        score_tag = soup.select_one('.sb-ergebnis .sb-endstand')
        if score_tag:
            score_text = score_tag.contents[0].strip().split(':')
            if len(score_text) == 2:
                home_score = int(score_text[0])
                away_score = int(score_text[1])
            else:
                home_score = away_score = -1
        else:
            home_score = away_score = -1
            
        events = parse_match_events(soup, match_data['match_id'])
        
        return {
            'match': {
                'id': match_data['match_id'],
                'season': match_data['season'],
                'matchday': match_data['matchday'],
                'date': match_date,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'url': match_data['url']
            },
            'events': events
        }
    except Exception as e:
        logging.error(f"Error parsing match {match_data['match_id']}: {e}")
        return None

def save_to_db(match_details: Dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    m = match_details['match']
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO matches 
            (id, season, matchday, date, home_team, away_team, home_score, away_score, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (m['id'], m['season'], m['matchday'], m['date'], 
              m['home_team'], m['away_team'], m['home_score'], m['away_score'], m['url']))
              
        for e in match_details['events']:
            cursor.execute("""
                INSERT INTO events (match_id, minute, team, event_type, player_1, player_2, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (e['match_id'], e['minute'], e['team'], e['event_type'], 
                  e['player_1'], e['player_2'], e['description']))
                  
        conn.commit()
    except Exception as e:
        logging.error(f"DB Error on match {m['id']}: {e}")
    finally:
        conn.close()

def get_scraped_match_ids() -> set:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM matches WHERE home_score >= 0")
        scraped = {row[0] for row in cursor.fetchall()}
        conn.close()
        return scraped
    except sqlite3.OperationalError:
        # Table might not exist yet
        return set()

def run_scraper(start_year: int, end_year: int):
    init_db()
    scraped_ids = get_scraped_match_ids()
    logging.info(f"Found {len(scraped_ids)} already completely scraped matches. They will be skipped.")
    
    for year in range(start_year, end_year + 1):
        logging.info(f"--- Starting Season {year} ---")
        matches = get_season_match_urls(year)
        logging.info(f"Found {len(matches)} matches for season {year}. Proceeding to parse...")
        
        for match_data in matches:
            if match_data['match_id'] in scraped_ids:
                logging.debug(f"Skipping match {match_data['match_id']} (already scraped).")
                continue
                
            details = parse_match_report(match_data)
            if details:
                save_to_db(details)
                if details['match']['home_score'] >= 0:
                    scraped_ids.add(details['match']['id'])
                
if __name__ == "__main__":
    # Scrape seasons 2010 to 2026 (current)
    run_scraper(2025, 2026)
