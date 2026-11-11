#!/usr/bin/env python3
"""Build the Team 238 event page from The Blue Alliance API.

The script polls The Blue Alliance every EVENT_POLL_SECONDS (default 300),
renders ``docs/event-template.md`` with the current event data, and writes
``docs/event.md``. Zensical's dev server watches ``docs/`` and rebuilds the
page automatically.

The Blue Alliance supports ETags, so every response is cached in
``.cache/tba.json``. Subsequent polls send ``If-None-Match`` and reuse the
cached JSON when the API returns ``304 Not Modified`` instead of downloading
the body again.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import urllib3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
TEMPLATE_PATH = DOCS_DIR / "event-template.md"
OUTPUT_PATH = DOCS_DIR / "event.md"
CACHE_PATH = ROOT / ".cache" / "tba.json"

TBA_BASE_URL = "https://www.thebluealliance.com/api/v3"
TEAM_KEY = "frc238"

load_dotenv(ROOT / ".env")

API_KEY = os.environ.get("TBA_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "TBA_API_KEY is not set. Copy .env.example to .env and add your "
        "The Blue Alliance API key."
    )

POLL_SECONDS = int(os.environ.get("EVENT_POLL_SECONDS", "300"))
QUEUE_LEAD_MINUTES = int(os.environ.get("QUEUE_LEAD_MINUTES", "15"))

COMP_LEVEL_NAMES = {
    "qm": "Qualification",
    "ef": "Eighth Final",
    "qf": "Quarterfinal",
    "sf": "Semifinal",
    "f": "Final",
}


class TBAError(RuntimeError):
    """Raised when The Blue Alliance request or response is unusable."""


class TBACache:
    """Small ETag-aware cache for The Blue Alliance API."""

    def __init__(self, api_key: str, cache_path: Path, timeout: float = 20.0):
        self.api_key = api_key
        self.cache_path = cache_path
        self.timeout = timeout
        self.http = urllib3.PoolManager(
            retries=urllib3.util.Retry(
                total=2,
                backoff_factor=0.5,
                status_forcelist=(500, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
            )
        )
        self.entries: dict[str, dict[str, Any]] = self._load()
        self.dirty = False
        self.downloaded = 0
        self.revalidated = 0
        self.from_cache = 0

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.cache_path.exists():
            return {}
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return raw if isinstance(raw, dict) else {}

    def save(self) -> None:
        if not self.dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.cache_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(self.entries, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(self.cache_path)
        self.dirty = False

    def get(self, path: str, *, allow_404: bool = False) -> Any:
        url = f"{TBA_BASE_URL}{path}"
        entry = self.entries.get(url)
        now = time.time()

        if entry and now < entry.get("expires_at", 0):
            self.from_cache += 1
            return entry["data"]

        headers = {
            "X-TBA-Auth-Key": self.api_key,
            "User-Agent": "frc238-pit-display/0.1 (+https://frc238.org)",
            "Accept": "application/json",
        }
        if entry and entry.get("etag"):
            headers["If-None-Match"] = entry["etag"]

        response = self.http.request("GET", url, headers=headers, timeout=self.timeout)

        if response.status == 304:
            if entry is None:
                headers.pop("If-None-Match", None)
                response = self.http.request(
                    "GET", url, headers=headers, timeout=self.timeout
                )
            else:
                entry["fetched_at"] = now
                entry["expires_at"] = now + entry.get("max_age", 0)
                if response.headers.get("ETag"):
                    entry["etag"] = response.headers["ETag"]
                self.dirty = True
                self.revalidated += 1
                return entry["data"]

        if response.status == 404 and allow_404:
            return None

        if response.status != 200:
            body = response.data[:300].decode("utf-8", "replace")
            raise TBAError(f"GET {path} failed with HTTP {response.status}: {body}")

        try:
            data = json.loads(response.data.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise TBAError(f"GET {path} returned invalid JSON: {exc}") from exc

        cache_control = response.headers.get("Cache-Control", "")
        match = re.search(r"max-age=(\d+)", cache_control)
        max_age = int(match.group(1)) if match else 0

        self.entries[url] = {
            "etag": response.headers.get("ETag"),
            "data": data,
            "fetched_at": now,
            "expires_at": now + max_age,
            "max_age": max_age,
        }
        self.dirty = True
        self.downloaded += 1
        return data


def parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def format_date_range(start: dt.date, end: dt.date) -> str:
    if start == end:
        return f"{start.strftime('%B')} {start.day}, {start.year}"
    if start.year == end.year and start.month == end.month:
        return f"{start.strftime('%B')} {start.day}–{end.day}, {end.year}"
    if start.year == end.year:
        return (
            f"{start.strftime('%B')} {start.day} – "
            f"{end.strftime('%B')} {end.day}, {end.year}"
        )
    return (
        f"{start.strftime('%B')} {start.day}, {start.year} – "
        f"{end.strftime('%B')} {end.day}, {end.year}"
    )


def format_timestamp(timestamp: int | None, tz: ZoneInfo) -> str | None:
    if not timestamp:
        return None
    local = dt.datetime.fromtimestamp(int(timestamp), tz)
    hour = local.strftime("%I").lstrip("0") or "0"
    return f"{local.strftime('%a')} {hour}:{local.strftime('%M %p')}"


def format_updated(tz: ZoneInfo) -> str:
    local = dt.datetime.now(tz)
    hour = local.strftime("%I").lstrip("0") or "0"
    return f"{local.strftime('%b')} {local.day}, {hour}:{local.strftime('%M %p %Z')}"


def team_number(team_key: str) -> str:
    return team_key.removeprefix("frc")


def match_label(match: dict[str, Any]) -> str:
    level = match.get("comp_level", "")
    name = COMP_LEVEL_NAMES.get(level, level.upper() or "Match")
    number = match.get("match_number")
    if level == "qm":
        return f"{name} {number}"
    return f"{name} {match.get('set_number')}-{number}"


def match_sort_time(match: dict[str, Any]) -> int:
    return (
        match.get("time")
        or match.get("predicted_time")
        or match.get("actual_time")
        or 0
    )


def match_alliance(match: dict[str, Any]) -> str | None:
    alliances = match.get("alliances") or {}
    for color in ("red", "blue"):
        if TEAM_KEY in ((alliances.get(color) or {}).get("team_keys") or []):
            return color
    return None


def is_played(match: dict[str, Any]) -> bool:
    return bool(match.get("actual_time")) or match.get("winning_alliance") in {
        "red",
        "blue",
    }


def match_result(match: dict[str, Any]) -> str | None:
    if not is_played(match):
        return None
    winner = match.get("winning_alliance")
    ours = match_alliance(match)
    if winner not in {"red", "blue"} or ours is None:
        return None

    alliances = match.get("alliances") or {}
    ours_score = (alliances.get(ours) or {}).get("score")
    other = "blue" if ours == "red" else "red"
    other_score = (alliances.get(other) or {}).get("score")

    if ours_score is not None and other_score is not None and ours_score == other_score:
        result = "Tie"
    elif winner == ours:
        result = "Win"
    else:
        result = "Loss"

    if ours_score is not None and other_score is not None:
        return f"{result} {ours_score}–{other_score}"
    return result


def alliance_badge(color: str | None) -> str:
    if color in {"red", "blue"}:
        return (
            f'<span class="pit-alliance pit-alliance--{color}">'
            f"{color.capitalize()}</span>"
        )
    return "Unknown"


def facts_section(aria_label: str, items: list[tuple[str, str]]) -> str:
    lines = [
        (
            f'<section class="pit-facts pit-facts--compact" '
            f'aria-label="{aria_label}" markdown="1">'
        )
    ]
    for label, value in items:
        lines.append(f"- **{label}**")
        lines.append(f"  {value}")
    lines.append("</section>")
    return "\n".join(lines)


def select_event(events: list[dict[str, Any]], today: dt.date) -> dict[str, Any] | None:
    if not events:
        return None
    ongoing = [
        event
        for event in events
        if parse_date(event["start_date"]) <= today <= parse_date(event["end_date"])
    ]
    if ongoing:
        return max(ongoing, key=lambda event: parse_date(event["start_date"]))
    upcoming = [event for event in events if parse_date(event["start_date"]) > today]
    if upcoming:
        return min(upcoming, key=lambda event: parse_date(event["start_date"]))
    return max(events, key=lambda event: parse_date(event["end_date"]))


def resolve_event_key(cache: TBACache, today: dt.date) -> str:
    override = os.environ.get("TBA_EVENT_KEY", "").strip()
    if override:
        return override

    year = int(os.environ.get("TBA_YEAR", str(today.year)))
    events = cache.get(f"/team/{TEAM_KEY}/events/{year}")
    event = select_event(events, today)
    if event is None:
        raise TBAError(f"No events found for {TEAM_KEY} in {year}")
    return event["key"]


def event_status(event: dict[str, Any], today: dt.date) -> str:
    start = parse_date(event["start_date"])
    end = parse_date(event["end_date"])
    if today < start:
        return "Upcoming"
    if today > end:
        return "Completed"
    return "In progress"


def find_next_match(
    status: dict[str, Any] | None,
    matches: list[dict[str, Any]],
    now: float,
) -> dict[str, Any] | None:
    if status:
        key = status.get("next_match_key")
        if key:
            for match in matches:
                if match.get("key") == key:
                    return match

    upcoming = [
        match
        for match in matches
        if not is_played(match) and (match.get("time") or 0) >= now - 60
    ]
    if upcoming:
        return min(upcoming, key=match_sort_time)

    unplayed = [match for match in matches if not is_played(match)]
    return min(unplayed, key=match_sort_time) if unplayed else None


def find_last_match(
    status: dict[str, Any] | None,
    matches: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if status:
        key = status.get("last_match_key")
        if key:
            for match in matches:
                if match.get("key") == key:
                    return match

    played = [match for match in matches if is_played(match)]
    return max(played, key=match_sort_time) if played else None


def render_next_match(
    match: dict[str, Any] | None,
    tz: ZoneInfo,
) -> str:
    if match is None:
        return "No upcoming matches are scheduled.\n{ .pit-muted }"

    color = match_alliance(match)
    alliances = match.get("alliances") or {}
    ours = (alliances.get(color) or {}) if color else {}
    other_color = "blue" if color == "red" else "red"
    others = alliances.get(other_color) or {}

    partners = [team_number(key) for key in ours.get("team_keys") or [] if key != TEAM_KEY]
    opponents = [team_number(key) for key in others.get("team_keys") or []]

    start = match.get("predicted_time") or match.get("time")
    queue = (start - QUEUE_LEAD_MINUTES * 60) if start else None

    facts = facts_section(
        "Next match",
        [
            ("Match", match_label(match)),
            ("Alliance", alliance_badge(color)),
            ("Partners", ", ".join(partners) or "—"),
            ("Opponents", ", ".join(opponents) or "—"),
            ("Scheduled", format_timestamp(match.get("time"), tz) or "TBD"),
            ("Estimated queue", format_timestamp(queue, tz) or "TBD"),
        ],
    )
    note = (
        f"Queue time is estimated {QUEUE_LEAD_MINUTES} minutes before the match."
        "\n{ .pit-muted }"
    )
    return f"{facts}\n\n{note}"


def render_overall_stats(
    status: dict[str, Any] | None,
    last_match: dict[str, Any] | None,
    tz: ZoneInfo,
) -> str:
    if not status:
        return "Event results will appear once the event begins.\n{ .pit-muted }"

    qual = status.get("qual") or {}
    ranking = qual.get("ranking") or {}

    items: list[tuple[str, str]] = []
    if ranking.get("matches_played") is not None:
        items.append(("Matches played", str(ranking["matches_played"])))
    if ranking.get("qual_average") is not None:
        items.append(("Qual average", f"{ranking['qual_average']:.2f}"))

    playoff = status.get("playoff") or {}
    playoff_record = playoff.get("record") or {}
    if playoff_record:
        items.append(
            (
                "Playoff record",
                (
                    f"{playoff_record.get('wins', 0)}-"
                    f"{playoff_record.get('losses', 0)}-"
                    f"{playoff_record.get('ties', 0)}"
                ),
            )
        )

    if last_match:
        result = match_result(last_match)
        when = format_timestamp(
            last_match.get("actual_time") or last_match.get("time"), tz
        )
        value = match_label(last_match)
        if result:
            value = f"{value} — {result}"
        if when:
            value = f"{value} ({when})"
        items.append(("Last match", value))

    parts = [facts_section("Overall stats", items)] if items else []
    if status.get("overall_status_str"):
        parts.append(status["overall_status_str"])
    return "\n\n".join(parts) or (
        "Event results will appear once the event begins.\n{ .pit-muted }"
    )


def render_alliance(status: dict[str, Any] | None) -> str:
    if not status:
        return "Alliance selection has not happened yet.\n{ .pit-muted }"

    alliance = status.get("alliance") or {}
    if not alliance:
        return "No playoff alliance yet.\n{ .pit-muted }"

    number = alliance.get("number")
    name = alliance.get("name") or (
        f"Alliance {number}" if number is not None else "Alliance"
    )
    pick = alliance.get("pick")
    if pick == 0:
        role = "Captain"
    elif pick:
        role = f"Pick {pick}"
    else:
        role = "—"

    items: list[tuple[str, str]] = [("Alliance", name), ("Role", role)]

    backup = alliance.get("backup") or {}
    if backup.get("in") or backup.get("out"):
        backup_text = []
        if backup.get("in"):
            backup_text.append(f"in: {team_number(backup['in'])}")
        if backup.get("out"):
            backup_text.append(f"out: {team_number(backup['out'])}")
        items.append(("Backup", ", ".join(backup_text)))

    parts = [facts_section("Playoff alliance", items)]
    if status.get("playoff_status_str"):
        parts.append(status["playoff_status_str"])
    return "\n\n".join(parts)


def render_upcoming_matches(
    matches: list[dict[str, Any]],
    next_match: dict[str, Any] | None,
    tz: ZoneInfo,
    limit: int = 5,
) -> str:
    next_key = next_match.get("key") if next_match else None
    upcoming = [
        match
        for match in matches
        if not is_played(match) and match.get("key") != next_key
    ]
    upcoming.sort(key=match_sort_time)
    upcoming = upcoming[:limit]

    if not upcoming:
        if next_match is None:
            return "No upcoming matches are scheduled.\n{ .pit-muted }"
        return "No other matches are scheduled.\n{ .pit-muted }"

    lines = []
    for match in upcoming:
        color = match_alliance(match)
        when = format_timestamp(match.get("predicted_time") or match.get("time"), tz)
        detail = f"{match_label(match)} — {alliance_badge(color)} alliance"
        if when:
            detail = f"{detail} — {when}"
        lines.append(f"- {detail}")
    return "\n".join(lines)


def build_context(
    event: dict[str, Any] | None,
    status: dict[str, Any] | None,
    matches: list[dict[str, Any]],
    tz: ZoneInfo,
    today: dt.date,
) -> dict[str, str]:
    now = time.time()
    next_match = find_next_match(status, matches, now)
    last_match = find_last_match(status, matches)

    if event is None:
        return {
            "EVENT_NAME": "Event information",
            "EVENT_LEDE": (
                "Event information is being updated. Check back for the "
                "competition schedule, venue details, and ways to cheer on "
                "Team 238."
            ),
            "EVENT_STATUS": "Coming soon",
            "EVENT_DATE": "Coming soon",
            "EVENT_LOCATION": "Coming soon",
            "TEAM_RANK": "—",
            "TEAM_RECORD": "—",
            "TEAM_ALLIANCE": "—",
            "NEXT_MATCH": "No event is scheduled right now.\n{ .pit-muted }",
            "OVERALL_STATS": (
                "Event results will appear once the event begins.\n{ .pit-muted }"
            ),
            "ALLIANCE": (
                "Alliance selection has not happened yet.\n{ .pit-muted }"
            ),
            "UPCOMING_MATCHES": (
                "No upcoming matches are scheduled.\n{ .pit-muted }"
            ),
            "UPDATED_AT": format_updated(tz),
        }

    location = ", ".join(
        part
        for part in (
            event.get("location_name"),
            event.get("city"),
            event.get("state_prov"),
        )
        if part
    )
    event_date = format_date_range(
        parse_date(event["start_date"]), parse_date(event["end_date"])
    )

    qual = (status or {}).get("qual") or {}
    ranking = qual.get("ranking") or {}
    rank = ranking.get("rank")
    num_teams = qual.get("num_teams")
    if rank is not None and num_teams:
        team_rank = f"{rank} / {num_teams}"
    elif rank is not None:
        team_rank = str(rank)
    else:
        team_rank = "—"

    record = ranking.get("record") or {}
    team_record = (
        f"{record.get('wins', 0)}-{record.get('losses', 0)}-{record.get('ties', 0)}"
        if record
        else "—"
    )

    alliance = (status or {}).get("alliance") or {}
    alliance_number = alliance.get("number")
    if alliance_number is not None:
        pick = alliance.get("pick")
        role = "Captain" if pick == 0 else (f"Pick {pick}" if pick else "")
        team_alliance = f"Alliance {alliance_number}"
        if role:
            team_alliance = f"{team_alliance} — {role}"
    else:
        team_alliance = "—"

    event_type = event.get("event_type_string") or "Event"
    lede = f"{event_type} at {location}." if location else f"{event_type}."

    return {
        "EVENT_NAME": event.get("name") or event.get("short_name") or "Event",
        "EVENT_LEDE": lede,
        "EVENT_STATUS": event_status(event, today),
        "EVENT_DATE": event_date,
        "EVENT_LOCATION": location or "—",
        "TEAM_RANK": team_rank,
        "TEAM_RECORD": team_record,
        "TEAM_ALLIANCE": team_alliance,
        "NEXT_MATCH": render_next_match(next_match, tz),
        "OVERALL_STATS": render_overall_stats(status, last_match, tz),
        "ALLIANCE": render_alliance(status),
        "UPCOMING_MATCHES": render_upcoming_matches(matches, next_match, tz),
        "UPDATED_AT": format_updated(tz),
    }


TOKEN_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def render_template(template: str, context: dict[str, str]) -> str:
    missing = sorted(set(TOKEN_PATTERN.findall(template)) - context.keys())
    if missing:
        raise TBAError(
            "Template is missing values for: " + ", ".join(missing)
        )
    return TOKEN_PATTERN.sub(lambda match: context[match.group(1)], template)


def write_page(content: str) -> None:
    temp_path = OUTPUT_PATH.with_suffix(".md.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(OUTPUT_PATH)


def fetch_and_render(cache: TBACache) -> tuple[str, str]:
    today = dt.date.today()
    event_key = resolve_event_key(cache, today)

    event = cache.get(f"/event/{event_key}")
    status = cache.get(
        f"/team/{TEAM_KEY}/event/{event_key}/status", allow_404=True
    )
    matches = cache.get(
        f"/team/{TEAM_KEY}/event/{event_key}/matches", allow_404=True
    ) or []

    tz = ZoneInfo(event.get("timezone") or "America/New_York")
    context = build_context(event, status, matches, tz, today)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return event_key, render_template(template, context)


def main() -> None:
    once = "--once" in sys.argv[1:]
    cache = TBACache(API_KEY, CACHE_PATH)

    if once:
        print("Building Team 238 event page once.")
    else:
        print(
            f"Building Team 238 event page every {POLL_SECONDS} seconds. "
            "Press Ctrl+C to stop."
        )

    while True:
        try:
            event_key, content = fetch_and_render(cache)
            write_page(content)
            print(
                f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{event_key}: wrote {OUTPUT_PATH.relative_to(ROOT)} "
                f"(downloaded={cache.downloaded}, "
                f"revalidated={cache.revalidated}, "
                f"cached={cache.from_cache})"
            )
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # noqa: BLE001
            print(
                f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"ERROR: {exc}",
                file=sys.stderr,
            )
        finally:
            cache.save()

        if once:
            break

        try:
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            break

    print("Done." if once else "Stopped event page builder.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped event page builder.")
