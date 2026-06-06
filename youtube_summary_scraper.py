import argparse
import json
import logging
import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

import requests

import site_db
import sofascore_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

@dataclass(frozen=True)
class YoutubeChannel:
    url: str
    source: str
    title: str


DEFAULT_CHANNELS = (
    YoutubeChannel(
        url="https://www.youtube.com/@beinsportsarsiv",
        source="youtube:beinsportsarsiv",
        title="beIN SPORTS Arşiv",
    ),
    YoutubeChannel(
        url="https://www.youtube.com/@beINSPORTST%C3%BCrkiye",
        source="youtube:beinsportsturkiye",
        title="beIN SPORTS Türkiye",
    ),
)
DEFAULT_CHANNEL_URL = DEFAULT_CHANNELS[0].url
DEFAULT_CHANNEL_TITLE = DEFAULT_CHANNELS[0].title
YOUTUBEI_URL = "https://www.youtube.com/youtubei/v1/browse"
SOURCE = DEFAULT_CHANNELS[0].source
DEFAULT_TIMEOUT = 20


@dataclass(frozen=True)
class ParsedSummaryTitle:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    season_start_year: int
    matchday: int | None


@dataclass(frozen=True)
class YoutubeVideo:
    video_id: str
    title: str
    url: str
    embed_url: str
    thumbnail_url: str
    channel_title: str
    published_text: str
    raw: dict[str, Any]


def normalize_text(text: str) -> str:
    text = text.casefold().replace("ı", "i")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    aliases = {
        "osmanlispor": "ankaraspor",
    }
    words = [
        aliases.get(word, word)
        for word in text.split()
        if word
        not in {
            "jk",
            "sk",
            "fk",
            "as",
            "a",
            "s",
            "k",
            "kulubu",
            "sincan",
            "belediyesi",
            "caykur",
            "fatih",
        }
    ]
    return " ".join(words)


def source_from_channel_url(channel_url: str, fallback_index: int = 1) -> str:
    handle_match = re.search(r"/@([^/?#]+)", channel_url)
    if not handle_match:
        return f"youtube:custom{fallback_index}"

    handle = unquote(handle_match.group(1))
    source_key = normalize_text(handle).replace(" ", "")
    return f"youtube:{source_key or f'custom{fallback_index}'}"


def channel_title_from_url(channel_url: str, fallback_index: int = 1) -> str:
    handle_match = re.search(r"/@([^/?#]+)", channel_url)
    if not handle_match:
        return f"YouTube Channel {fallback_index}"
    return unquote(handle_match.group(1))


def channels_from_urls(channel_urls: list[str] | None) -> tuple[YoutubeChannel, ...]:
    if not channel_urls:
        return DEFAULT_CHANNELS

    return tuple(
        YoutubeChannel(
            url=channel_url,
            source=source_from_channel_url(channel_url, index),
            title=channel_title_from_url(channel_url, index),
        )
        for index, channel_url in enumerate(channel_urls, start=1)
    )


def channel_videos_url(channel_url: str) -> str:
    base_url = channel_url.rstrip("/")
    return base_url if base_url.endswith("/videos") else f"{base_url}/videos"


def parse_season_start_year(text: str) -> int:
    match = re.search(r"\b(?P<start>\d{4})\s*/\s*(?P<end>\d{2}|\d{4})\b", text)
    if not match:
        raise ValueError(f"No season range found in title: {text}")
    return int(match.group("start"))


def is_supported_league_summary_title(title: str) -> bool:
    normalized_title = title.casefold()
    excluded_league_patterns = (
        r"\b1\.\s*lig\b",
        r"\bpremier league\b",
        r"\bligue 1\b",
        r"\bbundesliga\b",
        r"\bserie a\b",
        r"\bla liga\b",
    )
    if any(re.search(pattern, normalized_title, re.IGNORECASE) for pattern in excluded_league_patterns):
        return False
    english_marker = any(
        marker in normalized_title
        for marker in ("highlight", "match summary")
    )
    if english_marker:
        return "süper lig" in normalized_title or "super lig" in normalized_title
    return True


def parse_summary_title(title: str) -> ParsedSummaryTitle | None:
    normalized_title = title.casefold()
    if not any(
        marker in normalized_title
        for marker in ("özet", "highlight", "summary")
    ):
        return None
    if not is_supported_league_summary_title(title):
        return None

    match_title = title
    score_start = re.search(r"\(\d+\s*[-:–]\s*\d+\)", title)
    if score_start is not None and "|" in title[: score_start.start()]:
        match_title = title[: score_start.start()].rsplit("|", 1)[-1] + title[score_start.start() :]

    score_match = re.match(
        r"^\s*(?P<home>.+?)\s*\((?P<home_score>\d+)\s*[-:–]\s*(?P<away_score>\d+)\)\s*(?P<away>.+?)\s*(?:\||[-–—])",
        match_title,
        flags=re.IGNORECASE,
    )
    if not score_match:
        score_match = re.match(
            r"^\s*(?P<home>.+?)\s+(?P<home_score>\d+)\s*[-:–]\s*(?P<away_score>\d+)\s+(?P<away>.+?)\s*(?:\||[-–—])",
            match_title,
            flags=re.IGNORECASE,
        )
    if not score_match:
        return None

    try:
        season_start_year = parse_season_start_year(title)
    except ValueError:
        return None

    matchday_match = re.search(
        r"\b(?P<matchday>\d+)\.\s*Hafta\b|\bWeek\s+(?P<week>\d+)\b",
        title,
        re.IGNORECASE,
    )
    matchday = None
    if matchday_match:
        value = matchday_match.group("matchday") or matchday_match.group("week")
        matchday = int(value) if value else None

    return ParsedSummaryTitle(
        home_team=score_match.group("home").strip(),
        away_team=score_match.group("away").strip(),
        home_score=int(score_match.group("home_score")),
        away_score=int(score_match.group("away_score")),
        season_start_year=season_start_year,
        matchday=matchday,
    )


def extract_json_object(text: str, marker: str) -> dict[str, Any]:
    marker_index = text.find(marker)
    if marker_index == -1:
        raise ValueError(f"Could not find {marker}")

    start = text.find("{", marker_index)
    if start == -1:
        raise ValueError(f"Could not find JSON object after {marker}")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : index + 1])

    raise ValueError(f"Unterminated JSON object after {marker}")


def extract_initial_data(html: str) -> dict[str, Any]:
    for marker in ("var ytInitialData =", "window[\"ytInitialData\"] ="):
        try:
            return extract_json_object(html, marker)
        except ValueError:
            pass
    raise ValueError("Could not find ytInitialData")


def extract_ytcfg(html: str) -> dict[str, Any]:
    return extract_json_object(html, "ytcfg.set({")


def text_from_runs(value: dict[str, Any] | None) -> str:
    if not value:
        return ""
    if isinstance(value.get("simpleText"), str):
        return value["simpleText"]
    runs = value.get("runs") or []
    return "".join(run.get("text", "") for run in runs)


def walk_json(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def thumbnail_url(renderer: dict[str, Any]) -> str:
    thumbnails = (renderer.get("thumbnail") or {}).get("thumbnails") or []
    if not thumbnails:
        return ""
    return thumbnails[-1].get("url", "")


def video_from_renderer(renderer: dict[str, Any]) -> YoutubeVideo | None:
    video_id = renderer.get("videoId")
    title = text_from_runs(renderer.get("title"))
    if not video_id or not title:
        return None

    owner = renderer.get("ownerText") or renderer.get("shortBylineText")
    return YoutubeVideo(
        video_id=video_id,
        title=title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        embed_url=f"https://www.youtube-nocookie.com/embed/{video_id}",
        thumbnail_url=thumbnail_url(renderer),
        channel_title=text_from_runs(owner),
        published_text=text_from_runs(renderer.get("publishedTimeText")),
        raw=renderer,
    )


def thumbnail_from_sources(value: dict[str, Any]) -> str:
    sources = (
        (((value.get("contentImage") or {}).get("thumbnailViewModel") or {}).get("image") or {})
        .get("sources")
        or []
    )
    if not sources:
        return ""
    return sources[-1].get("url", "")


def metadata_text(value: dict[str, Any], index: int) -> str:
    rows = (
        (((value.get("metadata") or {}).get("lockupMetadataViewModel") or {}).get("metadata") or {})
        .get("contentMetadataViewModel", {})
        .get("metadataRows")
        or []
    )
    parts = rows[index].get("metadataParts") if index < len(rows) else None
    if not parts:
        return ""
    return " ".join(
        ((part.get("text") or {}).get("content") or "")
        for part in parts
    ).strip()


def video_from_lockup(value: dict[str, Any], channel_title: str) -> YoutubeVideo | None:
    video_id = value.get("contentId")
    title = (
        ((((value.get("metadata") or {}).get("lockupMetadataViewModel") or {}).get("title") or {})
        .get("content"))
        or ""
    )
    if not video_id or not title:
        return None

    return YoutubeVideo(
        video_id=video_id,
        title=title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        embed_url=f"https://www.youtube-nocookie.com/embed/{video_id}",
        thumbnail_url=thumbnail_from_sources(value),
        channel_title=channel_title,
        published_text=metadata_text(value, 1),
        raw=value,
    )


def extract_videos(data: dict[str, Any], *, channel_title: str = DEFAULT_CHANNEL_TITLE) -> list[YoutubeVideo]:
    videos = []
    seen_ids = set()
    for node in walk_json(data):
        if not isinstance(node, dict):
            continue
        renderer = node.get("videoRenderer")
        lockup = node.get("lockupViewModel")
        video = video_from_renderer(renderer) if renderer else None
        if video is None and lockup:
            video = video_from_lockup(lockup, channel_title)
        if video is None or video.video_id in seen_ids:
            continue
        seen_ids.add(video.video_id)
        videos.append(video)
    return videos


def extract_continuation_token(data: dict[str, Any]) -> str | None:
    for node in walk_json(data):
        if not isinstance(node, dict):
            continue
        command = node.get("continuationCommand")
        if command and command.get("token"):
            return command["token"]
    return None


def fetch_json(
    session: requests.Session,
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if method == "POST":
        response = session.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
    else:
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    if "text/html" in response.headers.get("content-type", ""):
        return {
            "initial_data": extract_initial_data(response.text),
            "ytcfg": extract_ytcfg(response.text),
        }
    return response.json()


def scan_channel_videos(
    channel_url: str = DEFAULT_CHANNEL_URL,
    *,
    channel_title: str = DEFAULT_CHANNEL_TITLE,
    max_pages: int | None = None,
    request_sleep: float = 0.2,
) -> list[YoutubeVideo]:
    session = requests.Session()
    session.headers.update(
        {
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            ),
        }
    )

    first_page = fetch_json(session, channel_videos_url(channel_url))
    initial_data = first_page["initial_data"]
    ytcfg = first_page["ytcfg"]
    videos = extract_videos(initial_data, channel_title=channel_title)
    seen_ids = {video.video_id for video in videos}
    token = extract_continuation_token(initial_data)

    page = 1
    while token and (max_pages is None or page < max_pages):
        page += 1
        if request_sleep > 0:
            time.sleep(request_sleep)
        payload = {
            "context": {
                "client": {
                    "clientName": ytcfg.get("INNERTUBE_CLIENT_NAME", "WEB"),
                    "clientVersion": ytcfg.get("INNERTUBE_CLIENT_VERSION"),
                }
            },
            "continuation": token,
        }
        data = fetch_json(
            session,
            f"{YOUTUBEI_URL}?key={ytcfg['INNERTUBE_API_KEY']}",
            method="POST",
            payload=payload,
        )
        for video in extract_videos(data, channel_title=channel_title):
            if video.video_id not in seen_ids:
                videos.append(video)
                seen_ids.add(video.video_id)
        token = extract_continuation_token(data)

    return videos


def match_parsed_sofascore_title(
    conn: sqlite3.Connection, parsed: ParsedSummaryTitle
) -> int | None:
    params: list[Any] = [
        parsed.season_start_year,
        parsed.home_score,
        parsed.away_score,
    ]
    where = [
        "season_start_year = ?",
        "home_score = ?",
        "away_score = ?",
        "status_description = 'Ended'",
    ]
    if parsed.matchday is not None:
        where.append("round = ?")
        params.append(parsed.matchday)

    rows = conn.execute(
        f"""
        SELECT id, home_team_name, away_team_name
        FROM matches
        WHERE {' AND '.join(where)}
        """,
        params,
    ).fetchall()

    home_key = normalize_text(parsed.home_team)
    away_key = normalize_text(parsed.away_team)
    matches = [
        row[0]
        for row in rows
        if normalize_text(row[1] or "") == home_key
        and normalize_text(row[2] or "") == away_key
    ]
    return matches[0] if len(matches) == 1 else None


def match_parsed_site_title(
    conn: sqlite3.Connection, parsed: ParsedSummaryTitle
) -> str | None:
    params: list[Any] = [
        str(parsed.season_start_year),
        parsed.home_score,
        parsed.away_score,
    ]
    where = [
        "season = ?",
        "home_score = ?",
        "away_score = ?",
    ]
    if parsed.matchday is not None:
        where.append("matchday = ?")
        params.append(parsed.matchday)

    rows = conn.execute(
        f"""
        SELECT id, home_team, away_team
        FROM matches
        WHERE {' AND '.join(where)}
        """,
        params,
    ).fetchall()

    home_key = normalize_text(parsed.home_team)
    away_key = normalize_text(parsed.away_team)
    matches = [
        row[0]
        for row in rows
        if normalize_text(row[1] or "") == home_key
        and normalize_text(row[2] or "") == away_key
    ]
    return matches[0] if len(matches) == 1 else None


def match_parsed_title(
    conn: sqlite3.Connection, parsed: ParsedSummaryTitle, *, target: str = "sofascore"
) -> int | str | None:
    if target == "site":
        return match_parsed_site_title(conn, parsed)
    return match_parsed_sofascore_title(conn, parsed)


def raw_video_row(
    match_id: int | str,
    video: YoutubeVideo,
    matched_at: str,
    source: str = SOURCE,
) -> dict[str, Any]:
    return {
        "match_id": match_id,
        "source": source,
        "video_id": video.video_id,
        "title": video.title,
        "url": video.url,
        "embed_url": video.embed_url,
        "thumbnail_url": video.thumbnail_url,
        "channel_title": video.channel_title,
        "published_text": video.published_text,
        "matched_at": matched_at,
        "raw_json": json.dumps(video.raw, ensure_ascii=False, sort_keys=True),
    }


def site_video_row(
    match_id: int | str,
    video: YoutubeVideo,
    source: str = SOURCE,
) -> dict[str, Any]:
    return {
        "match_id": str(match_id),
        "source": source,
        "video_id": video.video_id,
        "title": video.title,
        "url": video.url,
        "embed_url": video.embed_url,
        "thumbnail_url": video.thumbnail_url,
        "channel_title": video.channel_title,
        "published_text": video.published_text,
    }


def resolve_target(target: str) -> str:
    if target != "auto":
        return target
    if Path(sofascore_db.DB_PATH).exists():
        with sqlite3.connect(sofascore_db.DB_PATH) as conn:
            if db_match_count(conn) > 0:
                return "sofascore"
    return "site"


def db_match_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM matches").fetchone()
    return int(row[0] if row else 0)


def enrich_match_videos(
    *,
    channels: tuple[YoutubeChannel, ...] | None = None,
    channel_url: str | None = None,
    max_pages: int | None = None,
    request_sleep: float = 0.2,
    dry_run: bool = False,
    target: str = "auto",
) -> dict[str, int]:
    resolved_target = resolve_target(target)
    selected_channels = channels
    if selected_channels is None:
        selected_channels = (
            (
                YoutubeChannel(
                    channel_url,
                    source_from_channel_url(channel_url),
                    channel_title_from_url(channel_url),
                ),
            )
            if channel_url
            else DEFAULT_CHANNELS
        )
    matched_at = datetime.now(UTC).isoformat()
    video_count = 0
    parsed_count = 0
    matched_count = 0

    db_path = site_db.DB_PATH if resolved_target == "site" else sofascore_db.DB_PATH
    if not Path(db_path).exists():
        raise RuntimeError(
            f"{resolved_target} DB does not exist at {db_path}. "
            "Refresh or restore the match DB before running YouTube enrichment."
        )
    if resolved_target == "site":
        site_db.init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        match_count = db_match_count(conn)
        if match_count == 0:
            raise RuntimeError(
                f"{resolved_target} DB at {db_path} has no matches. "
                "Run YouTube enrichment against data/site.db with --target site, "
                "or restore/populate the SofaScore DB first."
            )

        for channel in selected_channels:
            videos = scan_channel_videos(
                channel.url,
                channel_title=channel.title,
                max_pages=max_pages,
                request_sleep=request_sleep,
            )
            video_count += len(videos)
            channel_parsed_count = 0
            channel_matched_count = 0

            for video in videos:
                parsed = parse_summary_title(video.title)
                if parsed is None:
                    continue
                parsed_count += 1
                channel_parsed_count += 1
                match_id = match_parsed_title(conn, parsed, target=resolved_target)
                if match_id is None:
                    continue
                matched_count += 1
                channel_matched_count += 1
                if not dry_run:
                    if resolved_target == "site":
                        site_db.save_match_videos(
                            conn,
                            [site_video_row(match_id, video, channel.source)],
                        )
                    else:
                        sofascore_db.save_match_video(
                            conn,
                            raw_video_row(match_id, video, matched_at, channel.source),
                        )

            logging.info(
                "Scanned %s videos from %s into %s DB (parsed=%s, matched=%s)",
                len(videos),
                channel.url,
                resolved_target,
                channel_parsed_count,
                channel_matched_count,
            )
        conn.commit()

    logging.info(
        "Scanned %s videos from %s channels into %s DB (parsed=%s, matched=%s)",
        video_count,
        len(selected_channels),
        resolved_target,
        parsed_count,
        matched_count,
    )
    return {"videos": video_count, "parsed": parsed_count, "matched": matched_count}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Match beIN SPORTS YouTube match summaries to SofaScore matches."
    )
    parser.add_argument(
        "--channel-url",
        action="append",
        dest="channel_urls",
        help="YouTube channel URL to scan. Repeat to scan multiple channels. Defaults to both beIN channels.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page cap. Omit to scan the full channel.",
    )
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument(
        "--target",
        choices=["auto", "sofascore", "site"],
        default="auto",
        help="DB to enrich. auto uses SofaScore DB when present, otherwise canonical site.db.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    enrich_match_videos(
        channels=channels_from_urls(args.channel_urls),
        max_pages=args.max_pages,
        request_sleep=args.sleep,
        dry_run=args.dry_run,
        target=args.target,
    )


if __name__ == "__main__":
    main()
