# Event Page Implementation Walkthrough

This guide explains how to build the Team 238 event page from scratch, step by
step. It is written for a high school student who knows a little Python and is
comfortable using a terminal. By the end, you will have the same event page
implementation that is on the `event-page-example` branch.

You do not need to copy an existing implementation. You will create each file
yourself and add the code in small pieces.

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
- [Step 3: Plan the page](#step-3-plan-the-page)
- [Step 4: Install the dependencies](#step-4-install-the-dependencies)
- [Step 5: Exclude the template from the build](#step-5-exclude-the-template-from-the-build)
- [Step 6: Create the page template](#step-6-create-the-page-template)
- [Step 7: Create the Python script](#step-7-create-the-python-script)
- [Step 8: Add the styles](#step-8-add-the-styles)
- [Step 9: Run it](#step-9-run-it)
- [Step 10: Check your work](#step-10-check-your-work)
- [Step 11: Make it your own](#step-11-make-it-your-own)
- [Troubleshooting](#troubleshooting)
- [Glossary](#glossary)

## Before you start

You need:

- Python 3.14 or newer.
- [uv](https://docs.astral.sh/uv/) for Python and dependency management.
- A text editor.
- A terminal. On Windows, use PowerShell (Windows 10/11) or Windows Terminal.
- A The Blue Alliance API key.

Start from the `main` branch of the project. It contains the site, the starter
files, and the placeholder event page. You will replace the placeholder event
page files as you work through this guide.

### Windows setup

The Python code is cross-platform, but some terminal commands are different on
Windows. This guide shows the macOS/Linux command first and the Windows
PowerShell equivalent next to it. Use PowerShell for the Windows commands, not
the old Command Prompt.

If you do not have `uv` yet, install it from PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart PowerShell after the installer finishes so the `uv` command is on your
`PATH`.

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

Copy the example file.

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
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

Every request needs your key in the `X-TBA-Auth-Key` header. The Python script
loads `.env` by itself, but the `curl` commands below need the key in your
shell. Load it first.

macOS/Linux (bash or zsh):

```bash
set -a
source .env
set +a
```

Windows PowerShell:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*?)\s*=\s*(.*)$') {
        Set-Item -Path "Env:$($matches[1])" -Value $matches[2]
    }
}
$TBA_API_KEY = $env:TBA_API_KEY
```

The PowerShell version also sets `$TBA_API_KEY`, so the `curl` commands below
work without changing the variable name.

Now try a few requests. These commands pipe the JSON through `jq`, which
pretty-prints it so it is much easier to read. If you do not have `jq`, install
it first (`brew install jq` on macOS, `winget install jqlang.jq` on Windows, or
`sudo apt install jq` on Ubuntu/Debian) or remove the `| jq .` part.

List Team 238's events for 2026:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/team/frc238/events/2026" \
  | jq .
```

Get one event:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/event/2026nhrr" \
  | jq .
```

Get the team's status at that event:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/team/frc238/event/2026nhrr/status" \
  | jq .
```

Get the team's matches at that event:

```bash
curl -s \
  -H "X-TBA-Auth-Key: $TBA_API_KEY" \
  "https://www.thebluealliance.com/api/v3/team/frc238/event/2026nhrr/matches" \
  | jq .
```

On Windows PowerShell, use `curl.exe` instead of `curl`. Windows PowerShell
aliases `curl` to `Invoke-WebRequest`, which uses different options. Use a
backtick for line continuation instead of a backslash:

```powershell
curl.exe -s `
  -H "X-TBA-Auth-Key: $TBA_API_KEY" `
  "https://www.thebluealliance.com/api/v3/event/2026nhrr" `
  | jq .
```

The other requests use the same pattern. `curl.exe` is included with Windows 10
and Windows 11.

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

## Step 3: Plan the page

Before writing code, decide what the page should show. This page is designed for
a pit display, so it should answer the questions people ask at an event:

- What event are we at?
- When and where is it?
- What is our rank and record?
- What is our next match?
- Who are our partners and opponents?
- When should we queue?
- What is our playoff alliance?
- What other matches are coming up?
- When was the page last updated?

The page will have five main data sections:

1. Event facts: date, location, rank, record, and playoff alliance.
2. Next match: match name, alliance, partners, opponents, scheduled time, and
   estimated queue time.
3. Overall stats: matches played, qualification average, playoff record, and the
   last match result.
4. Playoff alliance: alliance number, role, and backup information.
5. Upcoming matches: the next few matches after the next one.

A team can attend many events. The script should show the most useful one:

1. An event happening today, if there is one.
2. Otherwise, the next upcoming event.
3. Otherwise, the most recent past event.

You can also force a specific event with an environment variable:

```text
TBA_EVENT_KEY=2026nhrr
```

You will implement that logic later in the script.

## Step 4: Install the dependencies

The project uses `uv` to manage three things:

- `pyproject.toml`: the packages you want.
- `uv.lock`: the exact versions uv resolved.
- `.venv/`: the installed virtual environment.

The starter project uses `tba-api-v3client`. You will replace it with
`urllib3` so you can control ETag headers and caching yourself. `tzdata` gives
Python's `ZoneInfo` the IANA time zone data it needs on Windows.

Run these commands from the project root:

```bash
uv remove tba-api-v3client
uv add "urllib3>=2.0" tzdata
uv sync
```

What each command does:

| Command | What it does |
| --- | --- |
| `uv remove tba-api-v3client` | Removes the old TBA client from `pyproject.toml` and updates `uv.lock`. |
| `uv add "urllib3>=2.0" tzdata` | Adds the two new packages to `pyproject.toml`, resolves compatible versions, and updates `uv.lock`. |
| `uv sync` | Creates or updates `.venv/` and installs exactly the versions recorded in `uv.lock`. |

If `uv remove` leaves a `[tool.uv.sources]` block for `tba-api-v3client` in
`pyproject.toml`, delete that block. It is no longer needed. The final file
should look like this:

```toml
[project]
name = "pit-display"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "python-dotenv",
    "tzdata",
    "urllib3>=2.0",
]

[dependency-groups]
dev = [
    "zensical>=0.0.73",
]
```

Other useful `uv` commands:

- `uv lock` updates `uv.lock` without installing anything.
- `uv run <command>` runs a command inside the project environment. It installs
  missing dependencies first if needed.
- `uv tree` shows the dependency tree so you can see which package requires
  which other package.

The same commands work in Windows PowerShell.

## Step 5: Exclude the template from the build

The template you will create in the next step contains `{{TOKENS}}`, so it
should not be built as a real page. Open `zensical.toml` and add this near the
top, after `copyright`:

```toml
exclude_docs = """
event-template.md
"""
```

Zensical will now skip `docs/event-template.md` when it builds the site. The
generated `docs/event.md` is still built normally.

## Step 6: Create the page template

Create or replace `docs/event-template.md` with this content:

```markdown
---
title: Event
hide:
  - navigation
  - toc
  - path
---

<div class="pit-page" markdown="1">

<header class="pit-topbar" markdown="span">
[← Go back to main page!](./){: .pit-back }
[![FIRST Robotics Team 238](assets/logo-yellow.png){ .pit-brand__logo }](./){: .pit-brand }
**MMHS FRC 238 Operations**{: .pit-location .pit-location--end }
</header>

<main class="pit-content" markdown="1">

Event information
{ .pit-kicker }

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
- **Alliance**
  {{TEAM_ALLIANCE}}
</section>

<div class="pit-columns" markdown="1">

<section class="pit-panel" markdown="1">
## Next match

{{NEXT_MATCH}}
</section>

<section class="pit-panel" markdown="1">
## Overall stats

{{OVERALL_STATS}}
</section>

</div>

<div class="pit-columns" markdown="1">

<section class="pit-panel" markdown="1">
## Playoff alliance

{{ALLIANCE}}
</section>

<section class="pit-panel" markdown="1">
## Upcoming matches

{{UPCOMING_MATCHES}}
</section>

</div>

</main>

<footer class="pit-footer" markdown="1">
*FIRST*<sup>&reg;</sup> Robotics Team 238

MMHS FRC 238 Operations

Updated {{UPDATED_AT}}
</footer>

</div>
```

Here is what the important parts do:

- The front matter hides the normal site navigation, table of contents, and
  breadcrumb path.
- `<div class="pit-page" markdown="1">` is the page shell. The `markdown="1"`
  attribute tells Zensical to process Markdown inside the HTML element.
- `markdown="span"` is used for wrappers that contain only inline content.
- `{{EVENT_NAME}}`, `{{EVENT_DATE}}`, and the other tokens are placeholders. The
  Python script replaces them with real values.
- The CSS classes such as `.pit-panel`, `.pit-facts`, and `.pit-status` already
  exist in `docs/stylesheets/extra.css`.

The script writes `docs/event.md`. Do not edit that file by hand because the
script overwrites it on every update. Edit `docs/event-template.md` instead.

The template uses these tokens:

| Token | What it becomes |
| --- | --- |
| `EVENT_NAME` | Event name. |
| `EVENT_LEDE` | One-sentence event description. |
| `EVENT_STATUS` | Upcoming, In progress, or Completed. |
| `EVENT_DATE` | Formatted event date range. |
| `EVENT_LOCATION` | Venue and city/state. |
| `TEAM_RANK` | Team rank out of the number of teams. |
| `TEAM_RECORD` | Win-loss-tie record. |
| `TEAM_ALLIANCE` | Playoff alliance and role. |
| `NEXT_MATCH` | Next match details and estimated queue time. |
| `OVERALL_STATS` | Qualification and playoff statistics. |
| `ALLIANCE` | Playoff alliance details. |
| `UPCOMING_MATCHES` | The next few matches after the next one. |
| `UPDATED_AT` | When the page was generated. |

## Step 7: Create the Python script

Create or replace `scripts/Build-Event-Page.py`. The script is long, so build
it in the order shown below. The code blocks are cumulative: add each block to
the bottom of the same file. Do not run the script until you have added all the
blocks; a partial script will not work.

### 7a. Imports and configuration

Start with the imports, file paths, API settings, and shared constants:

```python
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
```

`Path(__file__).resolve().parent.parent` finds the project root even if you run
the script from a different folder. Use `pathlib.Path` for every file path. It
automatically uses `\` on Windows and `/` on macOS/Linux.

`load_dotenv` reads `.env`. The script stops immediately if the API key is
missing, which is better than failing later with a confusing `401` error.

`EVENT_POLL_SECONDS` controls how often the page updates. `QUEUE_LEAD_MINUTES`
controls how early the estimated queue time is.

### 7b. Build the ETag cache

The TBA API supports **ETags**. An ETag is a short fingerprint of a response.
If the data has not changed, TBA returns `304 Not Modified` and no body. That
saves bandwidth and API usage.

The flow is:

1. First request: save the JSON and the `ETag` header.
2. Next request: send `If-None-Match: <saved ETag>`.
3. If nothing changed: TBA returns `304`, and you reuse the saved JSON.
4. If something changed: TBA returns `200` with new JSON and a new ETag.

Add the cache class:

```python
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
```

`urllib3.PoolManager` reuses connections and retries temporary server errors.
`_load` reads the cache from disk, and `save` writes it back with a temporary
file and `replace`. The temporary file prevents another program from reading a
half-written cache.

The `get` method does the real work:

- If the cached entry has not expired, return it without making a request.
- If there is an ETag, send it in the `If-None-Match` header.
- If TBA returns `304`, reuse the cached JSON and count a revalidation.
- If TBA returns `404` and `allow_404` is true, return `None` instead of
  crashing. This is useful before an event starts, when status and rankings do
  not exist yet.
- If TBA returns `200`, save the new JSON, ETag, and `max-age` value.
- Any other status raises `TBAError` with a helpful message.

### 7c. Add date, time, and team helpers

These helpers turn raw TBA values into readable text:

```python
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
```

`parse_date` reads TBA's `YYYY-MM-DD` strings. `format_timestamp` converts Unix
timestamps to the event's local timezone. The `lstrip("0")` removes the leading
zero from hours such as `09`, so the page shows `9:30 AM` instead of `09:30 AM`.

`match_label` turns a key such as `2026nhrr_qm10` into `Qualification 10`.
`match_sort_time` chooses the best available time for sorting: scheduled time
first, then predicted time, then actual time.

`match_alliance` checks both alliances for `frc238`. `is_played` treats a match
as played if it has an actual start time or a winning alliance.

### 7d. Add match result and HTML helpers

Next, add the result formatting and small HTML helpers:

```python
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
```

`match_result` returns text such as `Win 87–64` or `Loss 52–71`. If scores are
missing, it still returns `Win`, `Loss`, or `Tie`.

`alliance_badge` returns a colored HTML badge. The colors come from the CSS you
will add in Step 8.

`facts_section` builds a small grid of labeled facts. It returns Markdown inside
an HTML `<section>`, which is why the section uses `markdown="1"`.

### 7e. Add event selection

Now add the logic that chooses which event to show:

```python
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
```

`select_event` follows the three rules from Step 3. If multiple events are
ongoing, it picks the one that started most recently. If none are ongoing, it
picks the next upcoming event. If there are no upcoming events, it picks the
most recent past event.

`resolve_event_key` lets `TBA_EVENT_KEY` override the automatic choice. It also
lets `TBA_YEAR` change which year's events are downloaded.

`event_status` returns the text shown near the top of the page.

### 7f. Find the next and last matches

Add these two functions:

```python
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
```

The status endpoint usually provides `next_match_key` and `last_match_key`,
which are the most reliable choices. If those are missing, the functions fall
back to the match list.

`find_next_match` ignores matches that are already played. It also allows a
60-second grace period, so a match does not disappear from the page the moment
its scheduled time passes.

### 7g. Render the next match

Add the function that builds the next-match section:

```python
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
```

This function finds Team 238's alliance, lists the partners and opponents, and
formats the scheduled time. It also calculates an estimated queue time by
subtracting `QUEUE_LEAD_MINUTES` from the predicted or scheduled match time.

TBA does not provide an official queue time, so the page always labels this as
an estimate.

### 7h. Render overall stats

Add the overall statistics section:

```python
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
```

This section only shows values that exist. Before an event starts, TBA may not
have rankings or playoff data, so the page shows a friendly placeholder instead
of an error.

`overall_status_str` is TBA's own summary text, such as a description of the
team's current standing.

### 7i. Render the playoff alliance

Add the playoff alliance section:

```python
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
```

The `pick` field is `0` for the alliance captain and a positive number for a
picked team. If the team was a backup robot, the section also shows which team
went in and which team went out.

### 7j. Render upcoming matches

Add the list of other upcoming matches:

```python
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
```

This function skips the next match because it already has its own panel. It
shows up to five matches by default, sorted by the best available time.

### 7k. Build the template context

Now connect the data to the template tokens:

```python
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
```

The returned dictionary keys must match the tokens in
`docs/event-template.md`. If you add a token to the template, you must also add
the same key here.

The `event is None` branch is a fallback. It lets the page show a friendly
message instead of crashing if TBA does not return the event.

### 7l. Render the template and write the page

Add the template replacement and file-writing code:

```python
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
```

`TOKEN_PATTERN` matches tokens such as `{{EVENT_NAME}}`. The
`render_template` function checks for missing values before replacing anything.
That way you get a clear error instead of a page full of `{{TOKENS}}`.

`write_page` writes to a temporary file and then replaces `docs/event.md`. This
is an atomic write, so the page is never half-updated. It works on Windows too.
If another program has `event.md` locked open, the replace can fail with a
`PermissionError`; close that program and try again.

`fetch_and_render` downloads the event, status, and matches, then builds the
context and renders the template. The `allow_404=True` arguments matter because
status and rankings may not exist before an event starts.

### 7m. Add the main loop

Finish the script with the main loop:

```python
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
```

The `--once` flag is for testing. It runs one update and exits. Without it, the
script runs forever and sleeps for `POLL_SECONDS` between updates.

The `try` block catches errors inside the loop. If the network blips or TBA
returns an error, the script prints the error and keeps running. The old
`docs/event.md` stays in place until a good update arrives.

The `finally` block saves the cache even if rendering fails. That way, a
successful download is not lost.

## Step 8: Add the styles

Open `docs/stylesheets/extra.css` and add these rules near the other
`.pit-facts` and `.pit-panel` rules:

```css
.md-typeset .pit-facts--compact ul {
  grid-template-columns: repeat(auto-fit, minmax(7rem, 1fr));
  gap: 0.5rem;
}

.md-typeset .pit-facts--compact li {
  padding: 0.5rem 0.65rem;
  font-size: clamp(0.85rem, 1.3vw, 1rem);
}

.md-typeset .pit-alliance {
  font-weight: bold;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.md-typeset .pit-alliance--red {
  color: #ff6b6b;
}

.md-typeset .pit-alliance--blue {
  color: #6bb6ff;
}
```

The `pit-facts--compact` rules make the small fact grids fit inside the panels.
The `pit-alliance` rules color the red and blue alliance badges produced by
`alliance_badge`.

If you add a new CSS class in the script or template, add the matching rule to
this file. Prefix the rule with `.md-typeset` so it wins over the theme styles.

## Step 9: Run it

Build the page one time:

```bash
uv run scripts/Build-Event-Page.py --once
```

The same command works in Windows PowerShell. Forward slashes work there too,
or you can write `uv run scripts\Build-Event-Page.py --once`.

You should see output like:

```text
[2026-03-14 09:15:00] 2026nhrr: wrote docs/event.md (downloaded=4, revalidated=0, cached=0)
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

## Step 10: Check your work

Use this checklist:

- [ ] `.env` contains a valid `TBA_API_KEY`.
- [ ] `.env` is ignored by git.
- [ ] `pyproject.toml` lists `python-dotenv`, `tzdata`, and `urllib3>=2.0`.
- [ ] `zensical.toml` excludes `event-template.md`.
- [ ] The script finds the correct event.
- [ ] `docs/event.md` contains real event data, not `{{TOKENS}}`.
- [ ] The next match shows the correct alliance color.
- [ ] The queue time is labeled as estimated.
- [ ] Rank and record match The Blue Alliance website.
- [ ] The page fits the pit display at 1440×810.
- [ ] `uv run zensical build` finishes without errors.
- [ ] The template is excluded from the built site.

## Step 11: Make it your own

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
`context` dictionary in `build_context`.

### `ModuleNotFoundError` for `urllib3` or `dotenv`

Run `uv sync` to install the dependencies. Then run the script again with
`uv run`.

### `ZoneInfoNotFoundError`

The `tzdata` package is missing. Make sure it is listed in `pyproject.toml` and
run `uv sync`. This is especially important on Windows.

### The page does not update

- Make sure the script is still running.
- Check the terminal for errors.
- Confirm `docs/event.md` is being rewritten.
- Make sure `zensical serve` is running.

### The cache looks stale

Delete `.cache/tba.json` and run the script again.

macOS/Linux:

```bash
rm .cache/tba.json
uv run scripts/Build-Event-Page.py --once
```

Windows PowerShell:

```powershell
Remove-Item .cache\tba.json
uv run scripts\Build-Event-Page.py --once
```

### Times look wrong

TBA times are Unix timestamps in UTC. The script converts them to the event's
timezone with `ZoneInfo`. Check the event's `timezone` field. On Windows, the
`tzdata` dependency is what provides the IANA time zone data, so keep it in
`pyproject.toml`.

### The template appears as a page

Make sure `zensical.toml` excludes it:

```toml
exclude_docs = """
event-template.md
"""
```

Restart `zensical serve` after changing `zensical.toml`.

### `PermissionError` when writing the page on Windows

Another program may have `docs/event.md` open. Close the editor or preview that
is using the file, then run the script again.

### `jq` is not recognized

Install `jq` (`brew install jq` on macOS, `winget install jqlang.jq` on Windows,
or `sudo apt install jq` on Ubuntu/Debian). If you do not want to install it,
remove the `| jq .` part of the `curl` commands.

### `curl` does not accept `-H` on Windows PowerShell

PowerShell may be using its `Invoke-WebRequest` alias. Use `curl.exe` instead,
as shown in Step 2.

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
