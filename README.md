# Pit Display

The Team 238 pit display is a static website built with
[Zensical](https://github.com/zensical/zensical). It is designed to run on a
screen at our pit and show team, robot, outreach, sponsor, and event information.

## Primary documentation

**See [`docs/about.md`](docs/about.md) for the primary development
documentation.** It covers the site structure, page patterns, CSS classes, HTML
shells, troubleshooting, and maintenance workflow.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python and dependency management
- A web browser for previewing the site

## Run the site locally

```bash
uv sync
uv run zensical serve --open
```

`uv sync` installs the Python environment and dependencies. The preview reloads
when files change. Stop it with `Ctrl+C`.

## Build the site

```bash
uv run zensical build
```

The generated site is written to `site/`. Do not edit files in `site/`; they are
rebuilt from `docs/`.

## Develop

All page content lives in `docs/`. Edit the Markdown files there, then preview
the result at the kiosk resolutions: **1440×810** and **1920×1080**.

- Page source: `docs/*.md`
- Styles: `docs/stylesheets/extra.css`
- Sponsor ticker/grid behavior: `docs/javascripts/sponsors.js`
- Sponsor data: `docs/assets/sponsors/sponsors.json`
- Site configuration: `zensical.toml`

For detailed guidance, examples, and style references, read
[`docs/about.md`](docs/about.md).

## Build the event page

`scripts/Build-Event-Page.py` reads event data from
[The Blue Alliance](https://www.thebluealliance.com/) and updates the event
page. It requires an API key.

1. Copy `.env.example` to `.env`.
2. Add your The Blue Alliance API key:

   ```bash
   TBA_API_KEY=your_key_here
   ```

3. Run the script:

   ```bash
   uv run scripts/Build-Event-Page.py
   ```

The `.env` file is ignored by git and must never be committed.

## Project structure

| Path | Purpose |
| --- | --- |
| `docs/` | Markdown page source and site assets. |
| `scripts/` | Helper scripts such as the event page builder. |
| `zensical.toml` | Site name, navigation, theme, and Markdown settings. |
| `pyproject.toml` | uv project and Python dependencies. |
| `site/` | Generated output. Rebuilt by Zensical. |
