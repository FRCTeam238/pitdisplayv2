---
title: About This Site
hide:
  - navigation
  - toc
  - path
---

<div class="pit-page pit-page--about" markdown="1">

<header class="pit-topbar" markdown="span">
[← Go back to main page!](./){: .pit-back }
[![FIRST Robotics Team 238](assets/logo-yellow.png){ .pit-brand__logo }](./){: .pit-brand }
**MMHS FRC 238 Operations**{: .pit-location .pit-location--end }
</header>

<main class="pit-content pit-content--about" markdown="1">

Behind the scenes
{ .pit-kicker }

# About This Site { .pit-title }

How this pit display works, and how to keep it current.
{ .pit-lede }

<div class="pit-columns" markdown="1">

<section class="pit-panel" markdown="1">
## For judges

This display is a student-built static website. It shows our team, robot,
outreach, sponsors, and event information on a screen at our pit. The site uses
plain Markdown, HTML, CSS, and a small amount of JavaScript, built with
[Zensical](https://github.com/zensical/zensical). No database or server-side application is
required.
</section>

<section class="pit-panel" markdown="1">
## For students

Everything needed to update the display lives in `docs/`. This page is the
maintenance guide: page structure, common Markdown patterns, CSS classes, and
the HTML shells used by every screen. If you can edit a Markdown file, you can
maintain this site.
</section>

</div>

<section class="pit-panel" markdown="1">
## On this page

- [How this site works](#how-this-site-works)
- [Update and maintain](#update-and-maintain)
- [Page patterns](#page-patterns)
- [Style reference](#style-reference)
- [Troubleshooting](#troubleshooting)
- [Keeping content current](#keeping-content-current)
</section>

<section class="pit-panel" markdown="1">
## How this site works

The pit display is a **static site**. Zensical reads the Markdown files in
`docs/`, applies the shared layout and styles, and writes a complete website to
`site/`. A static site is reliable at a competition because it needs no database,
login, or server-side application. It can be hosted on GitHub Pages, a school
server, or any static web host.

### Tech stack

- **Python 3.14** and **uv** manage the build environment and commands.
- **Zensical 0.0.73** builds the site and provides the Material for MkDocs theme.
- **Markdown** holds the page content.
- **HTML** is used only for layout wrappers and the page shell.
- **CSS** in `docs/stylesheets/extra.css` provides all Team 238 branding.
- **Vanilla JavaScript** in `docs/javascripts/sponsors.js` renders the sponsor
  ticker and sponsor grid.
- **JSON** in `docs/assets/sponsors/sponsors.json` lists sponsor names, logos,
  and links.
- **PNG** files in `docs/assets/` hold the team logo and favicon.

The site is designed for a pit display at **1440×810** and **1920×1080**, and it
still works down to **1024×768**. The six pit screens are sized to fit one
screen. This guide is intentionally longer and scrolls. The theme's header,
sidebar, search, and footer chrome are hidden so the display looks like an app
rather than a documentation site.

### Project map

| Path | Purpose |
| --- | --- |
| `docs/*.md` | Page source. This is where content is edited. |
| `docs/event-template.md` | Template used to generate the event page. |
| `docs/stylesheets/extra.css` | All custom colors, layout, and component styles. |
| `docs/javascripts/sponsors.js` | Sponsor ticker and sponsor grid renderer. |
| `docs/assets/` | Team logo, favicon, and sponsor logos. |
| `scripts/Build-Event-Page.py` | Fetches TBA data and writes `docs/event.md`. |
| `.cache/tba.json` | ETag cache for The Blue Alliance API. |
| `zensical.toml` | Site name, URL, navigation, theme, and Markdown extensions. |
| `pyproject.toml` | uv project and Zensical dependency. |
| `site/` | Generated output. Do not edit; it is rebuilt. |

### Commands

```bash
uv sync
uv run zensical serve --open
uv run zensical build
uv run scripts/Build-Event-Page.py
```

- `uv sync` installs the Python environment and dependencies.
- `uv run zensical serve --open` starts a live preview in the browser.
- `uv run zensical build` writes the final site to `site/`.
- `uv run scripts/Build-Event-Page.py` updates the event page every five
  minutes. Add `--once` to update it a single time and exit.

Install uv from [docs.astral.sh/uv](https://docs.astral.sh/uv/) if it is not
already available. The preview reloads when a file changes. Stop it with
`Ctrl+C`.
</section>

<section class="pit-panel" markdown="1">
## Update and maintain

### Quick start

1. If the project uses version control, pull the latest changes first.
2. Run `uv sync` once after cloning or when dependencies change.
3. Run `uv run zensical serve --open`.
4. Edit files in `docs/`.
5. Check the preview at **1440×810** and **1920×1080**.
6. Run `uv run zensical build` before publishing.
7. Deploy the generated `site/` folder, or push if a deployment workflow does it.

### Edit an existing page

Open the matching file in `docs/` and change the text inside the panels. Keep
the `markdown="1"` attributes on the outer wrappers, or the Markdown inside them
will not be processed.

| Page | File |
| --- | --- |
| Home | `docs/index.md` |
| Robot | `docs/robot.md` |
| Team | `docs/team.md` |
| Outreach | `docs/outreach.md` |
| Sponsors | `docs/sponsors.md` |
| Event | `docs/event.md` (generated from `docs/event-template.md`) |
| This guide | `docs/about.md` |

### Update the home page

The home page has four editable areas:

- the hero kicker, title, and lede;
- the five folder links in `.pit-folders`;
- the sponsor ticker and “Learn about our sponsors!” button;
- the footer, including the small **About this site** link.

Keep the folder descriptions short. The home screen is sized for five folders;
if a sixth folder is added, update the `.pit-folders ul` grid in
`docs/stylesheets/extra.css` and retest at **1440×810**.

### Update the event page

`docs/event.md` is generated; do not edit it by hand. Edit
`docs/event-template.md` instead, then run:

```bash
uv run scripts/Build-Event-Page.py --once
```

The script selects the team's current event automatically: an in-progress
event, then the next upcoming event, then the most recent past event. Set
`TBA_EVENT_KEY` in `.env` to force a specific event. While the script runs, it
updates the page every five minutes.

The Blue Alliance responses are cached in `.cache/tba.json` and revalidated
with ETags. Delete that file to force a full refresh. Queue times are estimated
from the scheduled match time and `QUEUE_LEAD_MINUTES`.

### Add a new screen

1. Copy an inner page such as `docs/robot.md` to `docs/newscreen.md`.
2. Change the `title` in the front matter.
3. Change the kicker, page title, lede, and panel content.
4. Add a folder link in `docs/index.md`:

```markdown
- [**New screen** *Short description.*](newscreen/)
```

5. Add the page to `nav` in `zensical.toml`:

```toml
{ "New screen" = "newscreen.md" },
```

6. Run `uv run zensical build` and check the preview.

### Update sponsors

Edit `docs/assets/sponsors/sponsors.json`:

```json
{
  "sponsors": [
    {
      "name": "Example Sponsor",
      "logo": "example-sponsor.png",
      "url": "https://example.com"
    }
  ]
}
```

- Put logo files in `docs/assets/sponsors/`.
- `logo` is resolved relative to `sponsors.json`, not the page.
- `url` is optional. Without it, the sponsor is shown but not clickable.
- If `logo` is missing, the sponsor name is shown as text.
- Use the exact filename, including capitalization.

The home page uses `assets/sponsors/sponsors.json`. The sponsors page uses
`../assets/sponsors/sponsors.json` because that page is one folder deeper.

### Update branding

- Colors are defined once at the top of `docs/stylesheets/extra.css`:
  `--team-black`, `--team-yellow`, `--team-white`, and `--team-neon`.
- The typeface is Verdana, set on `body` in `extra.css`.
- Google Fonts are disabled in `zensical.toml` with `font = false` so the
  display works offline.
- Replace `docs/assets/logo-yellow.png` to change the main logo.
- Replace `docs/assets/favicon.png` to change the browser icon.
- The site URL and page order are in `zensical.toml`.
</section>

<section class="pit-panel" markdown="1">
## Page patterns

Use **Markdown first**. Add HTML only when a layout wrapper is required. Every
block wrapper that contains Markdown needs `markdown="1"`; inline-only wrappers,
such as the topbar, use `markdown="span"`.

### Common Markdown

| Want | Write |
| --- | --- |
| Heading | `## Section heading` |
| Bold | `**important**` |
| Italic | `*FIRST*` |
| Link | `[text](robot/)` |
| Image | `![alt text](assets/logo-yellow.png)` |
| Bullet list | `- item` |
| Inline class | `[Button](sponsors/){: .pit-button }` |
| Block class | `Label` then `{ .pit-kicker }` on the next line |
| Code block | Three backticks before and after the code |
| Em dash | `—` or `&mdash;` |

`attr_list` and `md_in_html` are enabled in `zensical.toml`. They provide the
`{: .class }` syntax and make Markdown work inside HTML wrappers.

### Inner page shell

```text
---
title: Page Name
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

Section label
{ .pit-kicker }

# Page Title { .pit-title }

One-sentence summary.
{ .pit-lede }

<section class="pit-panel" markdown="1">
## Section heading

Your Markdown content goes here.
</section>

</main>

<footer class="pit-footer" markdown="1">
*FIRST*<sup>&reg;</sup> Robotics Team 238

MMHS FRC 238 Operations
</footer>

</div>
```

### Quick facts

Facts use a normal Markdown list. The bold label and value are separated by a
line break:

```markdown
<section class="pit-facts" aria-label="Quick facts" markdown="1">
- **Label**
  Value
- **Another label**
  Another value
</section>
```

### Columns and panels

```markdown
<div class="pit-columns" markdown="1">

<section class="pit-panel" markdown="1">
## First panel

Panel content.
</section>

<section class="pit-panel" markdown="1">
## Second panel

Panel content.
</section>

</div>
```

### Home folder links

```markdown
<nav class="pit-folders" aria-label="Pit display sections" markdown="1">
- [**Robot** *Learn about our robot!*](robot/)
- [**Team** *Learn about our team!*](team/)
- [**Outreach** *Learn about our outreach!*](outreach/)
- [**Sponsors** *Learn about our sponsors!*](sponsors/)
- [**Event** *Event information!*](event/)
</nav>
```

### Sponsor ticker and grid

Home page ticker:

```html
<div class="pit-sponsor-strip">
  <div class="pit-ticker" data-sponsor-ticker="true" data-sponsors-src="assets/sponsors/sponsors.json">
    <div class="pit-ticker__track"></div>
  </div>
  [Learn about our sponsors!](sponsors/){: .pit-button }
</div>
```

Sponsors page grid:

```html
<div class="pit-sponsor-grid" data-sponsor-grid="true" data-sponsors-src="../assets/sponsors/sponsors.json" markdown="1">
Sponsor logos are being updated.
{ .pit-muted }
</div>
```

The `data-sponsor-ticker` and `data-sponsor-grid` hooks are required. Keep the
inner `.pit-ticker__track` element; JavaScript fills it. The fallback text is
replaced when sponsor data loads.

### Status and hashtags

```markdown
In progress
{ .pit-status }
```

```markdown
**#frc238**{: .pit-hashtags } &nbsp; **#crusaders**{: .pit-hashtags }
```

### Footer and About link

The home page footer includes the small guide link:

```html
<footer class="pit-footer" markdown="1">
*FIRST*<sup>&reg;</sup> Robotics Team 238

MMHS FRC 238 Operations

[About this site](./about/){: .pit-about-link }
</footer>
```

The other pages use the same footer without the About link.
</section>

<section class="pit-panel" markdown="1">
## Style reference

### Colors

| Color | Value | Use |
| --- | --- | --- |
| Team black | `#000000` | Page background |
| Team yellow | `#eeee00` | Titles, borders, buttons, links |
| Team white | `#ffffff` | Body text |
| Team neon | `#ccff00` | Hover and accent states |

Use the CSS variables instead of repeating hex values:

```css
var(--team-black);
var(--team-yellow);
var(--team-white);
var(--team-neon);
```

### Type and spacing

- Font: Verdana, Geneva, Tahoma, sans-serif.
- Base text size: 18px.
- Titles and ledes use `clamp()` so they scale with the screen.
- `.pit-content` is centered and limited to 1180px.
- `.pit-columns` uses `auto-fit` columns with a 15rem minimum.
- `.pit-facts` uses `auto-fit` columns with a 12rem minimum.
- Breakpoints: 900px, 700px, 520px, and a short-screen rule at 800px height.

### Common classes

| Class | What it does |
| --- | --- |
| `.pit-page` | Full-height page shell with branded background. |
| `.pit-page--home` | Home page layout variant. |
| `.pit-page--about` | Guide page layout, including the sticky topbar. |
| `.pit-topbar` | Three-column top bar: back link, logo, location. |
| `.pit-back` | Yellow outlined back button. |
| `.pit-brand` / `.pit-brand__logo` | Centered logo link and image sizing. |
| `.pit-location` / `.pit-location--end` | Small uppercase topbar labels. |
| `.pit-content` | Main content wrapper. |
| `.pit-content--about` | Narrower reading width for the guide. |
| `.pit-kicker` | Small yellow uppercase label above a title. |
| `.pit-title` | Large yellow page title. |
| `.pit-lede` | Muted intro paragraph. |
| `.pit-folders` | Home page folder grid. |
| `.pit-facts` | Responsive quick-facts grid. |
| `.pit-columns` | Responsive multi-column layout. |
| `.pit-panel` | Bordered content card with dark background. |
| `.pit-status` | Yellow pill-shaped status label. |
| `.pit-hashtags` | Yellow bold hashtag text. |
| `.pit-sponsor-strip` | Ticker plus button row. |
| `.pit-ticker` / `.pit-ticker__track` | Scrolling sponsor ticker. |
| `.pit-sponsor-grid` / `.pit-sponsor` | Sponsor logo wall. |
| `.pit-button` | Yellow outlined call-to-action button. |
| `.pit-muted` | Lower-emphasis text. |
| `.pit-footer` | Small footer line. |
| `.pit-about-link` | Subtle link to this guide. |

### CSS rules

- Prefix custom rules with `.md-typeset` so they beat the theme styles.
- Prefix custom rules inside media queries the same way.
- Put shared values in the `:root` variables at the top of `extra.css`.
- Keep new components inside `.pit-content` or `.pit-panel` so spacing stays
  consistent.
- Use `clamp()` for sizes that must scale between kiosk resolutions.

### HTML rules

- Add `markdown="1"` to any HTML wrapper that contains Markdown.
- Use `markdown="span"` only for wrappers with inline content, such as topbars.
- Keep raw HTML to layout wrappers, page shells, and JavaScript hooks.
- Use relative links: `./` for home, `robot/` for a sibling page, and
  `assets/...` for assets in the page source.
- Do not edit `site/`; it is regenerated by the build.
- Do not add inline `<script>` blocks. Put behavior in `sponsors.js` or a new
  file registered in `zensical.toml`.
- Do not change a class name unless the matching CSS is updated too.
</section>

<section class="pit-panel" markdown="1">
## Troubleshooting

### Markdown is showing as plain text

Add `markdown="1"` to the outer HTML wrapper. The build only processes Markdown
inside a wrapper when that attribute is present.

### A page is too tall for the display

Shorten the text, move details into a list, or split the content into two panels.
The important check is **1440×810**: the home page and all inner screens should
fit without scrolling.

### Sponsor logos are missing

Check that:

- `sponsors.json` is valid JSON;
- the logo path is relative to `sponsors.json`;
- the file exists in `docs/assets/sponsors/`;
- the filename capitalization matches exactly;
- the site was rebuilt after the change.

If `url` is omitted, the sponsor still appears but is not a link. If `logo` is
omitted, the name appears as text.

### A link goes to the wrong place

Use relative page links such as `robot/` and `./`. Avoid leading slashes. In raw
HTML, Zensical rewrites relative URLs based on the page location. Data attributes
are not rewritten.

### A style is not applying

Increase specificity with `.md-typeset` and confirm the class is on the element.
If the rule is inside a media query, it needs the `.md-typeset` prefix too.

### The font looks different

That is expected. `font = false` in `zensical.toml` disables Google Fonts, so the
site uses the local Verdana stack and works without internet access.

### A new page does not appear

Create the file under `docs/`, add a link, and add the page to `nav` in
`zensical.toml`. Then rebuild and check `site/`.
</section>

<section class="pit-panel" markdown="1">
## Keeping content current

### Before an event

- Confirm `.env` has a valid `TBA_API_KEY`.
- Run `uv run scripts/Build-Event-Page.py` and check the event page.
- Confirm robot facts, team facts, and sponsor names.
- Check that the sponsor JSON and logos are current.
- Test the site at **1440×810**.

### After an event

- Leave the event builder running so results and awards stay current.
- Replace outdated photos or sponsor logos.
- Check for broken links.

### Each build season

- Update the robot page with the new robot name and facts.
- Review the team page and outreach page.
- Ask sponsors for current logos and permission to display them.
- Update the copyright year in `zensical.toml` if needed.

### Before publishing

1. Run `uv run zensical build`.
2. Open the site and click every folder link.
3. Check the sponsor ticker and sponsor grid.
4. Test at **1440×810** and **1920×1080**.
5. Confirm the About link in the home footer still works.

This page is maintained alongside the site. If a pattern changes, update the
example here so the next student has an accurate reference.
</section>

</main>

<footer class="pit-footer" markdown="1">
*FIRST*<sup>&reg;</sup> Robotics Team 238

MMHS FRC 238 Operations
</footer>

</div>
