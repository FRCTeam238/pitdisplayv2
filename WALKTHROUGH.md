# Event Page Implementation Walkthrough

This guide explains how the Team 238 event page works and how to build it
yourself, step by step. It is written for a high school student who knows a
little Python and is comfortable using a terminal.

The finished version lives in `scripts/Build-Event-Page.py`. Use this guide to
understand it, rebuild it, or adapt it for another team or another page.

## What you are building

The event page is generated automatically from The Blue Alliance (TBA) API.

```text
The Blue Alliance API
        |
        |  JSON data: event, status, matches
        v
scripts/Build-Event-Page.py
        |
        |  reads docs/event-template.md
        |  replaces {{TOKENS}} with real data
        v
docs/event.md
        |
        |  Zensical watches docs/
        v
HTML page on the pit display
```

The script runs in a loop. Every five minutes it asks TBA for fresh data,
rebuilds `docs/event.md`, and Zensical rebuilds the HTML page.

## Contents

- [Before you start](#before-you-start)
- [Step 1: Get an API key and store it safely](#step-1-get-an-api-key-and-store-it-safely)
- [Step 2: Explore the API before writing code](#step-2-explore-the-api-before-writing-code)
- [Step 3: Choose which event to show](#step-3-choose-which-event-to-show)
- [Step 4: Design the template](#step-4-design-the-template)
- [Step 5: Write the Python script](#step-5-write-the-python-script)
- [Step 6: Run it](#step-6-run-it)
- [Step 7: Check your work](#step-7-check-your-work)
- [Step 8: Make it your own](#step-8-make-it-your-own)
- [Troubleshooting](#troubleshooting)
- [Glossary](#glossary)
- [Where to look in the real code](#where-to-look-in-the-real-code)

## Before you start

You need:

- Python 3.14 or newer.
- [uv](https://docs.astral.sh/uv/) for Python and dependency management.
- A text editor.
- A terminal.
- A The Blue Alliance API key.

You should also know these basic ideas:

- **API**: a way for one program to ask another program for data.
- **JSON**: a text format for structured data. It looks like Python
  dictionaries and lists.
- **HTTP status code**: a number that says whether a web request worked.
  `200` means OK, `304` means "not changed", `404` means "not found".
- **Markdown**: the text format used by Zensical to write pages.
- **Environment variable**: a setting stored outside your code, often used for
  secrets such as API keys.

## Step 1: Get an API key and store it safely

Create a TBA account and request an API key from your account page:

<https://www.thebluealliance.com/account>

Never put the key directly in your Python file. Instead, store it in a `.env`
file at the project root.

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and add your key:

```text
TBA_API_KEY=your_real_key_here
```

The project `.gitignore` already ignores `.env`, so it will not be committed.
Check this before you commit anything:

```bash
git check-ignore .env
```

If that prints `.env`, you are safe.

## Step 2: Explore the API before writing code

It is much easier to write a script after you have seen the real data. The TBA
API uses this base URL:

```text
https://www.thebluealliance.com/api/v3
```

Every request needs your key in the `X-TBA-Auth-Key` header. Load the key into
your shell first:

```bash
set -a
source .env
set +a
```

Now try a few requests.

List Team 238's events for 2026:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/team/frc238/events/2026"
```

Get one event:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/event/2026nhrr"
```

Get the team's status at that event:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/team/frc238/event/2026nhrr/status"
```

Get the team's matches at that event:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/team/frc238/event/2026nhrr/matches"
```

Read the JSON carefully. Useful fields include:

| Field | Meaning |
| --- | --- |
| `key` | Event or match key, such as `2026nhrr` or `2026nhrr_qm10`. |
| `name` | Event name. |
| `start_date`, `end_date` | Event dates in `YYYY-MM-DD` format. |
| `timezone` | IANA timezone name, such as `America/New_York`. |
| `city`, `state_prov`, `location_name` | Event location. |
| `alliances.red.team_keys` | Teams on the red alliance. |
| `alliances.blue.team_keys` | Teams on the blue alliance. |
| `time` | Scheduled match start time as a Unix timestamp. |
| `predicted_time` | TBA's predicted match time. |
| `actual_time` | When the match actually started. |
| `winning_alliance` | `red`, `blue`, or `null`. |
| `qual.ranking.rank` | Team's qualification rank. |
| `qual.num_teams` | Number of teams at the event. |
| `alliance.number` | Playoff alliance number. |
| `next_match_key` | Key of the team's next match. |

The team's status and matches endpoints are the most important ones for this
page.

## Step 3: Choose which event to show

A team can attend many events. The script should show the most useful one:

1. An event happening today, if there is one.
2. Otherwise, the next upcoming event.
3. Otherwise, the most recent past event.

You can also force a specific event with an environment variable:

```text
TBA_EVENT_KEY=2026nhrr
```

The selection logic looks like this:

```python
def select_event(events, today):
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
```

This uses the team events endpoint for the current year. If you want a
different year, set `TBA_YEAR`. The function that ties it together is:

```python
def resolve_event_key(cache, today):
    override = os.environ.get("TBA_EVENT_KEY", "").strip()
    if override:
        return override

    year = int(os.environ.get("TBA_YEAR", str(today.year)))
    events = cache.get(f"/team/{TEAM_KEY}/events/{year}")
    event = select_event(events, today)
    if event is None:
        raise RuntimeError(f"No events found for {TEAM_KEY} in {year}")
    return event["key"]
```

## Step 4: Design the template

The page is a Markdown file with placeholders called **tokens**. A token looks
like this:

```text
{{EVENT_NAME}}
```

The script replaces each token with real text. The template lives in
`docs/event-template.md`.

Here is a simplified version:

```markdown
# {{EVENT_NAME}} { .pit-title }

{{EVENT_LEDE}}
{ .pit-lede }

{{EVENT_STATUS}}
{ .pit-status }

<section class="pit-facts" aria-label="Event details" markdown="1">
- **Date**
  {{EVENT_DATE}}
- **Location**
  {{EVENT_LOCATION}}
- **Rank**
  {{TEAM_RANK}}
- **Record**
  {{TEAM_RECORD}}
</section>

<section class="pit-panel" markdown="1">
## Next match

{{NEXT_MATCH}}
</section>
```

Important Markdown rules for this project:

- Add `markdown="1"` to any HTML wrapper that contains Markdown.
- Use `markdown="span"` for wrappers that only contain inline content.
- Use the existing CSS classes such as `.pit-panel`, `.pit-facts`, and
  `.pit-status`.
- Keep the front matter and page shell at the top and bottom of the template.

The real template also has panels for overall stats, the playoff alliance, and
upcoming matches.

## Step 5: Write the Python script

Create a file named `scripts/Build-Event-Page.py`. Build it in small pieces.

### 5a. Configuration

Start with imports, paths, and settings:

```python
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
    raise RuntimeError("TBA_API_KEY is not set. Copy .env.example to .env.")

POLL_SECONDS = int(os.environ.get("EVENT_POLL_SECONDS", "300"))
QUEUE_LEAD_MINUTES = int(os.environ.get("QUEUE_LEAD_MINUTES", "15"))
```

`Path(__file__).resolve().parent.parent` finds the project root even if you run
the script from a different folder. `load_dotenv` reads `.env`.

### 5b. Build an ETag cache

The TBA API supports **ETags**. An ETag is a short fingerprint of a response.
If the data has not changed, TBA returns `304 Not Modified` and no body. That
saves bandwidth and API usage.

The flow is:

1. First request: save the JSON and the `ETag` header.
2. Next request: send `If-None-Match: <saved ETag>`.
3. If nothing changed: TBA returns `304`, and you reuse the saved JSON.
4. If something changed: TBA returns `200` with new JSON and a new ETag.

A small cache class:

```python
class TBACache:
    def __init__(self, api_key, cache_path):
        self.api_key = api_key
        self.cache_path = cache_path
        self.http = urllib3.PoolManager()
        self.entries = self._load()
        self.dirty = False

    def _load(self):
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self):
        if not self.dirty:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.cache_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.entries, indent=2), encoding="utf-8")
        temp.replace(self.cache_path)
        self.dirty = False
```

The `get` method makes the request:

```python
    def get(self, path, allow_404=False):
        url = f"{TBA_BASE_URL}{path}"
        entry = self.entries.get(url)
        now = time.time()

        if entry and now < entry.get("expires_at", 0):
            return entry["data"]

        headers = {
            "X-TBA-Auth-Key": self.api_key,
            "User-Agent": "frc238-pit-display/0.1",
            "Accept": "application/json",
        }
        if entry and entry.get("etag"):
            headers["If-None-Match"] = entry["etag"]

        response = self.http.request("GET", url, headers=headers, timeout=20)

        if response.status == 304 and entry:
            entry["expires_at"] = now + entry.get("max_age", 0)
            self.dirty = True
            return entry["data"]

        if response.status == 404 and allow_404:
            return None

        if response.status != 200:
            raise RuntimeError(f"GET {path} failed with HTTP {response.status}")

        data = json.loads(response.data.decode("utf-8"))
        max_age = 0
        match = re.search(r"max-age=(\d+)", response.headers.get("Cache-Control", ""))
        if match:
            max_age = int(match.group(1))

        self.entries[url] = {
            "etag": response.headers.get("ETag"),
            "data": data,
            "expires_at": now + max_age,
            "max_age": max_age,
        }
        self.dirty = True
        return data
```

The real script also counts downloads, revalidations, and cache hits so you can
see what happened in the log.

Saving with a temporary file and `replace` is important. It prevents Zensical
from reading a half-written cache file.

### 5c. Fetch the data

The main fetch function does four things:

```python
def fetch_and_render(cache):
    today = dt.date.today()
    event_key = resolve_event_key(cache, today)

    event = cache.get(f"/event/{event_key}")
    status = cache.get(f"/team/{TEAM_KEY}/event/{event_key}/status", allow_404=True)
    matches = cache.get(f"/team/{TEAM_KEY}/event/{event_key}/matches", allow_404=True) or []

    tz = ZoneInfo(event.get("timezone") or "America/New_York")
    context = build_context(event, status, matches, tz, today)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return event_key, render_template(template, context)
```

`allow_404=True` matters because status and rankings may not exist before an
event starts. A `404` should not crash the loop.

### 5d. Turn raw data into readable text

You will need small helper functions. Here are the most useful ideas.

**Team numbers.** TBA uses keys such as `frc238`. To display `238`:

```python
def team_number(team_key):
    return team_key.removeprefix("frc")
```

**Dates.** Event dates come as `YYYY-MM-DD` strings:

```python
def parse_date(value):
    return dt.date.fromisoformat(value)


def format_date_range(start, end):
    if start == end:
        return f"{start.strftime('%B')} {start.day}, {start.year}"
    if start.year == end.year and start.month == end.month:
        return f"{start.strftime('%B')} {start.day}–{end.day}, {end.year}"
    return (
        f"{start.strftime('%B')} {start.day} – "
        f"{end.strftime('%B')} {end.day}, {end.year}"
    )


def event_status(event, today):
    start = parse_date(event["start_date"])
    end = parse_date(event["end_date"])
    if today < start:
        return "Upcoming"
    if today > end:
        return "Completed"
    return "In progress"
```

**Times.** TBA times are Unix timestamps. Convert them to the event's timezone:

```python
def format_timestamp(timestamp, tz):
    if not timestamp:
        return None
    local = dt.datetime.fromtimestamp(int(timestamp), tz)
    hour = local.strftime("%I").lstrip("0") or "0"
    return f"{local.strftime('%a')} {hour}:{local.strftime('%M %p')}"


def format_updated(tz):
    local = dt.datetime.now(tz)
    hour = local.strftime("%I").lstrip("0") or "0"
    return f"{local.strftime('%b')} {local.day}, {hour}:{local.strftime('%M %p %Z')}"
```

**Match labels.** A match key such as `2026nhrr_qm10` means qualification match
10. Playoff matches use set and match numbers:

```python
COMP_LEVEL_NAMES = {
    "qm": "Qualification",
    "ef": "Eighth Final",
    "qf": "Quarterfinal",
    "sf": "Semifinal",
    "f": "Final",
}

def match_label(match):
    level = match.get("comp_level", "")
    name = COMP_LEVEL_NAMES.get(level, level.upper() or "Match")
    if level == "qm":
        return f"{name} {match.get('match_number')}"
    return f"{name} {match.get('set_number')}-{match.get('match_number')}"
```

**Alliance color.** Check which alliance contains `frc238`:

```python
def match_alliance(match):
    alliances = match.get("alliances") or {}
    for color in ("red", "blue"):
        if TEAM_KEY in (alliances.get(color, {}).get("team_keys") or []):
            return color
    return None


def is_played(match):
    return bool(match.get("actual_time")) or match.get("winning_alliance") in {
        "red",
        "blue",
    }


def match_sort_time(match):
    return (
        match.get("time")
        or match.get("predicted_time")
        or match.get("actual_time")
        or 0
    )
```

**Queue time.** TBA does not provide an official queue time. The page estimates
it as the match start time minus a configurable number of minutes:

```python
start = match.get("predicted_time") or match.get("time")
queue_time = start - QUEUE_LEAD_MINUTES * 60
```

Always label this as an estimate so nobody thinks it is official.

**Next match.** Prefer the status endpoint's `next_match_key`. If it is missing,
find the earliest unplayed match:

```python
def find_next_match(status, matches, now):
    if status and status.get("next_match_key"):
        for match in matches:
            if match.get("key") == status["next_match_key"]:
                return match

    upcoming = [
        match
        for match in matches
        if not is_played(match) and (match.get("time") or 0) >= now - 60
    ]
    return min(upcoming, key=match_sort_time) if upcoming else None
```

### 5e. Render the template

Keep the template simple: find every token, look it up in a dictionary, and
replace it. If a token is missing, raise an error instead of silently writing a
broken page.

```python
TOKEN_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

def render_template(template, context):
    missing = sorted(set(TOKEN_PATTERN.findall(template)) - context.keys())
    if missing:
        raise RuntimeError("Template is missing values for: " + ", ".join(missing))

    return TOKEN_PATTERN.sub(lambda match: context[match.group(1)], template)
```

The `context` dictionary is built from the event, status, and matches. For
example:

```python
context = {
    "EVENT_NAME": event.get("name") or "Event",
    "EVENT_STATUS": event_status(event, today),
    "EVENT_DATE": format_date_range(start, end),
    "EVENT_LOCATION": location,
    "TEAM_RANK": team_rank,
    "TEAM_RECORD": team_record,
    "TEAM_ALLIANCE": team_alliance,
    "NEXT_MATCH": render_next_match(next_match, tz),
    "OVERALL_STATS": render_overall_stats(status, last_match, tz),
    "ALLIANCE": render_alliance(status),
    "UPCOMING_MATCHES": render_upcoming_matches(matches, next_match, tz),
    "UPDATED_AT": format_updated(tz),
}
```

Some values are plain text. Others, such as `NEXT_MATCH`, are complete Markdown
blocks built by helper functions. That keeps the template readable.

### 5f. Write the page and loop

Write the finished Markdown to `docs/event.md` using a temporary file:

```python
def write_page(content):
    temp_path = OUTPUT_PATH.with_suffix(".md.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(OUTPUT_PATH)
```

Then run the whole thing in a loop:

```python
def main():
    cache = TBACache(API_KEY, CACHE_PATH)

    while True:
        try:
            event_key, content = fetch_and_render(cache)
            write_page(content)
            print(f"{event_key}: wrote {OUTPUT_PATH}")
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
        finally:
            cache.save()

        time.sleep(POLL_SECONDS)
```

Catching the error inside the loop keeps the page builder alive if the network
blips. The old `event.md` stays in place until a good update arrives.

Add a `--once` flag for testing:

```python
once = "--once" in sys.argv[1:]
```

If `once` is true, break out of the loop after the first attempt.

## Step 6: Run it

Build the page one time:

```bash
uv run scripts/Build-Event-Page.py --once
```

You should see output like:

```text
2026nhrr: wrote docs/event.md (downloaded=4, revalidated=0, cached=0)
```

The numbers mean:

- `downloaded`: new responses downloaded from TBA.
- `revalidated`: cached responses that TBA confirmed with `304`.
- `cached`: responses used without making a request because `max-age` had not
  expired.

Run it again immediately. You should see `cached=4` and `downloaded=0`. After
the cache expires, you should see `revalidated=4`.

Now run the site:

```bash
uv run zensical serve --open
```

Open the event page in the browser. Zensical watches `docs/`, so when the
script rewrites `docs/event.md`, the page reloads.

For a production build:

```bash
uv run zensical build
```

The output goes to `site/`.

## Step 7: Check your work

Use this checklist:

- [ ] `.env` contains a valid `TBA_API_KEY`.
- [ ] `.env` is ignored by git.
- [ ] The script finds the correct event.
- [ ] `docs/event.md` contains real event data, not `{{TOKENS}}`.
- [ ] The next match shows the correct alliance color.
- [ ] The queue time is labeled as estimated.
- [ ] Rank and record match The Blue Alliance website.
- [ ] The page fits the pit display at 1440×810.
- [ ] `uv run zensical build` finishes without errors.
- [ ] The template is excluded from the built site.

## Step 8: Make it your own

Ideas for extending the page:

- Add the event website link.
- Add a webcast link from `event["webcasts"]`.
- Show the team's average match score.
- Show the next three matches with partners and opponents.
- Add a countdown to the next match.
- Add a second page for the team's other events.
- Change `TEAM_KEY` to another team and adapt the page.

If you add a new token, add it to both the template and the `context`
dictionary. The script will tell you if you forget one.

If you add a new CSS class, add the matching rule to
`docs/stylesheets/extra.css` and prefix it with `.md-typeset` so it wins over
the theme styles.

## Troubleshooting

### `TBA_API_KEY is not set`

Create `.env` from `.env.example` and add your key. Make sure the file is named
`.env`, not `.env.txt`.

### HTTP 401 or 403

Your key is missing, wrong, or not being sent. Check that `.env` contains
`TBA_API_KEY=...` and that the key is active on your TBA account.

### `No events found for frc238 in 2026`

The team has no events for that year, or the year is wrong. Set `TBA_YEAR` or
force an event with `TBA_EVENT_KEY`.

### `Template is missing values for: ...`

You added a token to `docs/event-template.md` but did not add it to the
`context` dictionary in the script.

### The page does not update

- Make sure the script is still running.
- Check the terminal for errors.
- Confirm `docs/event.md` is being rewritten.
- Make sure `zensical serve` is running.

### The cache looks stale

Delete `.cache/tba.json` and run the script again:

```bash
rm .cache/tba.json
uv run scripts/Build-Event-Page.py --once
```

### Times look wrong

TBA times are Unix timestamps in UTC. The script converts them to the event's
timezone with `ZoneInfo`. Check the event's `timezone` field.

### The template appears as a page

Make sure `zensical.toml` excludes it:

```toml
exclude_docs = """
event-template.md
"""
```

## Glossary

| Term | Meaning |
| --- | --- |
| API | A way for programs to request data from another service. |
| JSON | A text format for dictionaries, lists, strings, and numbers. |
| Endpoint | A specific API URL, such as `/event/2026nhrr`. |
| ETag | A fingerprint of a response, used to check whether it changed. |
| `If-None-Match` | The request header that sends an ETag back to the server. |
| `304 Not Modified` | The server's answer when the cached copy is still valid. |
| `Cache-Control` | The server's instructions for how long a response may be reused. |
| Environment variable | A setting stored outside the code, often for secrets. |
| Token | A placeholder such as `{{EVENT_NAME}}` that the script replaces. |
| Static site | A site made of prebuilt files, with no database or server app. |
| Zensical | The tool that turns the Markdown in `docs/` into the HTML site. |

## Where to look in the real code

| Topic | Location |
| --- | --- |
| Settings and API key | Top of `scripts/Build-Event-Page.py` |
| ETag cache | `TBACache` class |
| Event selection | `select_event` and `resolve_event_key` |
| Match helpers | `match_label`, `match_alliance`, `find_next_match` |
| Page sections | `render_next_match`, `render_overall_stats`, `render_alliance` |
| Template replacement | `render_template` |
| Main loop | `main` |
| Page layout | `docs/event-template.md` |
| Page styles | `docs/stylesheets/extra.css` |

Work through the steps in order, run `--once` after each meaningful change, and
compare your output with the real page. That is how the original implementation
was built.
