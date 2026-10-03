#!/usr/bin/env python3
"""
Generate self-hosted GitHub stat cards for the profile README.

Fetches live data from the GitHub API and renders SVG cards into cards/.
Runs locally (uses `gh auth token` or GITHUB_TOKEN) and in GitHub Actions
(GITHUB_TOKEN provided automatically).

No external dependencies — stdlib only.
"""

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"
USER = "rubayet2027"

# ---------------------------------------------------------------- theme ----
BG = "#20232a"          # card background (github-readme-stats "react" theme)
BORDER = "#61dafb"      # accent border
TITLE = "#61dafb"       # card titles
NUMBER = "#61dafb"      # big numbers
LABEL = "#98c1b9"       # muted labels
TEXT = "#c9d1d9"        # body text
MUTED = "#8b949e"       # faint text
FONT = "'Segoe UI', -apple-system, Helvetica, Arial, sans-serif"

# repos shown as pin cards (kept in sync with the README's Featured Projects)
PIN_REPOS = ["Creatix", "EduXolve", "hackathon", "SkillSwap"]

LANG_COLORS = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "CSS": "#663399",
    "Python": "#3572a5",
    "HTML": "#e34c26",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Makefile": "#427819",
    "Dockerfile": "#384d54",
    "Shell": "#89e051",
    "Go": "#00add8",
    "Rust": "#dea584",
}
FALLBACK_COLOR = "#61dafb"


def token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return None


def api(path, method="GET", payload=None):
    req = urllib.request.Request(
        API + path,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + (token() or ""),
            "User-Agent": "profile-card-generator",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        data=json.dumps(payload).encode() if payload is not None else None,
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def graphql(query):
    return api("/graphql", "POST", {"query": query})["data"]


# ------------------------------------------------------------------ data ---
def collect():
    print("Fetching user data ...")
    user = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner&sort=updated")

    g = graphql(
        """
        query {
          user(login: "%s") {
            contributionsCollection {
              totalCommitContributions
              totalPullRequestContributions
              contributionCalendar { totalContributions }
            }
          }
        }
        """ % USER
    )["user"]["contributionsCollection"]

    stars = sum(r["stargazers_count"] for r in repos)

    print("Fetching per-repo languages ...")
    lang_bytes = {}
    for r in repos:
        try:
            langs = api(f"/repos/{USER}/{r['name']}/languages")
        except Exception as e:
            print(f"  ! languages for {r['name']}: {e}", file=sys.stderr)
            continue
        for name, size in langs.items():
            lang_bytes[name] = lang_bytes.get(name, 0) + size

    print("Fetching pinned repos ...")
    pins = []
    for name in PIN_REPOS:
        pins.append(api(f"/repos/{USER}/{name}"))

    return {
        "user": user,
        "repos": repos,
        "stars": stars,
        "commits": g["totalCommitContributions"] or 0,
        "prs": g["totalPullRequestContributions"] or 0,
        "contributions": (g.get("contributionCalendar") or {}).get(
            "totalContributions", 0
        ),
        "languages": lang_bytes,
        "pins": pins,
    }


# --------------------------------------------------------------- render ----
def card_svg(w, h, inner):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img">'
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{BG}" '
        f'stroke="{BORDER}" stroke-width="2"/>'
        f"{inner}</svg>"
    )


def title(y, text, w):
    return (
        f'<text x="{w // 2}" y="{y}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="15" font-weight="600" fill="{TITLE}">{text}</text>'
    )


ICONS = {
    # 16x16 octicon paths
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 "
    ".416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 "
    "1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l"
    "4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 "
    "0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 "
    "1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 "
    "2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 "
    ".25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 "
    "15.7a.25.25 0 0 1-.4-.2Z",
    "commit": "M17.5 9.75a.75.75 0 0 1-.75.75h-3.19l.66 3.19a.75.75 0 0 "
    "1-.553.894l-3.5.75a.75.75 0 0 1-.905-.555l-.661-3.19h-3.19a.75.75 0 0 1 "
    "0-1.5h3.19l-.66-3.19a.75.75 0 0 1 .553-.894l3.5-.75a.75.75 0 0 1 .905.555l"
    ".66 3.19h3.19a.75.75 0 0 1 .75.75Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 "
    "0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 "
    "10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 "
    "0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 "
    "0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 "
    "0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 "
    "0-1.5 0Z",
}


def icon(name, x, y, size=16, color=NUMBER):
    path = ICONS[name]
    s = size / 16
    return (
        f'<g transform="translate({x},{y}) scale({s})" fill="{color}">'
        f'<path d="{path}"/></g>'
    )


def icon_gist(x, y, size=16, color=NUMBER):
    s = size / 16
    return (
        f'<g transform="translate({x},{y}) scale({s})" fill="none" '
        f'stroke="{color}" stroke-width="1.4">'
        f'<path d="M3 1.2h7.2l3.8 3.8v9.8H3z" stroke-linejoin="round"/>'
        f'<path d="M10.2 1.2v3.8h3.8" stroke-linejoin="round"/>'
        f"</g>"
    )


def icon_contrib(x, y, size=16, color=NUMBER):
    s = size / 16
    return (
        f'<g transform="translate({x},{y}) scale({s})" fill="{color}">'
        f'<rect x="1" y="9" width="3.4" height="6" rx="0.8"/>'
        f'<rect x="6.3" y="5.5" width="3.4" height="9.5" rx="0.8"/>'
        f'<rect x="11.6" y="1" width="3.4" height="14" rx="0.8"/>'
        f"</g>"
    )


def render_stats(d):
    w, h = 500, 192
    cells = [
        (lambda x, y: icon("star", x, y, 20), "Stars", d["stars"]),
        (lambda x, y: icon("repo", x, y, 20), "Repos", len(d["repos"])),
        (lambda x, y: icon("commit", x, y, 20), "Commits", d["commits"]),
        (lambda x, y: icon_gist(x, y, 20), "Gists", d["user"]["public_gists"]),
        (lambda x, y: icon("pr", x, y, 20), "Pull Requests", d["prs"]),
        (lambda x, y: icon_contrib(x, y, 20), "Contributions", d["contributions"]),
    ]
    cw, ch = w / 3, (h - 64) / 2
    parts = [title(32, "Al Rubayet Turjo · GitHub Stats", w)]
    for i, (draw, label, value) in enumerate(cells):
        r, c = divmod(i, 3)
        x0 = c * cw
        y0 = 64 + r * ch
        mid = y0 + ch / 2
        ix = x0 + 34
        parts.append(
            f'<g>'
            f"{draw(ix, mid - 26)}"
            f'<text x="{ix + 28}" y="{mid - 8}" font-family="{FONT}" '
            f'font-size="26" font-weight="700" fill="{NUMBER}">{value}</text>'
            f'<text x="{x0 + cw / 2}" y="{mid + 18}" '
            f'text-anchor="middle" font-family="{FONT}" font-size="11" '
            f'fill="{LABEL}">{label}</text>'
            f"</g>"
        )
    return card_svg(w, h, "".join(parts))


def render_top_langs(d):
    w, h = 500, 226
    langs = sorted(d["languages"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in langs) or 1
    parts = [title(34, "Top Languages", w)]
    y = 66
    for name, size in langs:
        pct = size / total * 100
        bar_w = max(28, pct / 100 * 300)
        color = LANG_COLORS.get(name, FALLBACK_COLOR)
        parts.append(
            f'<g font-family="{FONT}">'
            f'<text x="40" y="{y + 9}" font-size="12.5" fill="{TEXT}">{name}</text>'
            f'<rect x="150" y="{y}" width="300" height="12" rx="6" fill="#161b22"/>'
            f'<rect x="150" y="{y}" width="{bar_w:.0f}" height="12" rx="6" '
            f'fill="{color}"/>'
            f'<text x="460" y="{y + 10}" font-size="11.5" fill="{LABEL}">'
            f'{pct:.1f}%</text>'
            f"</g>"
        )
        y += 27
    return card_svg(w, h, "".join(parts))


def render_pin(repo):
    w, h = 500, 132
    name = repo["name"]
    url = repo["html_url"]
    lang = repo.get("language")
    stars = repo["stargazers_count"]
    forks = repo["forks_count"]
    parts = [
        f'<text x="24" y="40" font-family="{FONT}" font-size="17" '
        f'font-weight="700" fill="{TITLE}">{name}.git</text>'
        f'<text x="{w - 24}" y="40" text-anchor="end" font-family="{FONT}" '
        f'font-size="11.5" fill="{MUTED}">Public Repository</text>'
    ]
    if repo.get("description"):
        desc = repo["description"][:64]
        parts.append(
            f'<text x="24" y="70" font-family="{FONT}" font-size="12" '
            f'fill="{TEXT}">{desc}</text>'
        )
    fy = 104
    if lang:
        color = LANG_COLORS.get(lang, FALLBACK_COLOR)
        parts.append(
            f'<circle cx="30" cy="{fy - 4}" r="5" fill="{color}"/>'
            f'<text x="42" y="{fy}" font-family="{FONT}" font-size="12" '
            f'fill="{TEXT}">{lang}</text>'
        )
    parts.append(
        f'<g transform="translate(380,{fy - 12}) scale(1)">{_icon_str("star")}</g>'
        f'<text x="402" y="{fy}" font-family="{FONT}" font-size="12" '
        f'fill="{LABEL}">{stars}</text>'
        f'<g transform="translate(432,{fy - 12})">{_icon_str("fork")}</g>'
        f'<text x="454" y="{fy}" font-family="{FONT}" font-size="12" '
        f'fill="{LABEL}">{forks}</text>'
    )
    return card_svg(w, h, "".join(parts))


GIT_BRANCH = (
    "M9.5 3.25a2.25 2.25 0 1 1 3 2.122V6A2.5 2.5 0 0 1 10 8.5H6a1 1 0 0 0-1 1"
    "v1.128a2.251 2.251 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.5 0v1.836A2.493 "
    "2.493 0 0 1 6 7h4a1 1 0 0 0 1-1v-.628A2.25 2.25 0 0 1 9.5 3.25Zm-6 0a.75"
    ".75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Zm8.25-.75a.75.75 0 1 0 0 1.5.75.75 0 "
    "0 0 0-1.5ZM4.25 12a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Z"
)


def _icon_str(name, color=NUMBER):
    if name == "star":
        return f'<g fill="{color}"><path d="{ICONS["star"]}"/></g>'
    return f'<g fill="{color}"><path d="{GIT_BRANCH}"/></g>'


# ---------------------------------------------------------------- main -----
def main():
    d = collect()
    os.makedirs("cards/pins", exist_ok=True)

    with open("cards/stats.svg", "w") as f:
        f.write(render_stats(d))
    with open("cards/top-langs.svg", "w") as f:
        f.write(render_top_langs(d))
    for repo in d["pins"]:
        slug = repo["name"].lower().replace("/", "-")
        with open(f"cards/pins/{slug}.svg", "w") as f:
            f.write(render_pin(repo))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    for fname in [
        "cards/stats.svg",
        "cards/top-langs.svg",
    ] + [f"cards/pins/{r['name'].lower()}.svg" for r in d["pins"]]:
        with open(fname, "a") as f:
            f.write(f"\n<!-- generated {now} -->\n")

    print(
        f"Done. {len(d['repos'])} repos, {d['stars']} stars, "
        f"{d['commits']} commits (1y), {d['contributions']} contributions (1y)."
    )


if __name__ == "__main__":
    main()
