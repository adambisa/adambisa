"""Builds assets/stats.svg and assets/langs.svg from the GitHub GraphQL API.

Runs daily in .github/workflows/cards.yml with the Actions token. Locally:
    GH_TOKEN=$(gh auth token --user adambisa) python3 scripts/cards.py
Only public, non-fork repos owned by LOGIN count, so local and CI runs agree.
"""

import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = "adambisa"
ASSETS = Path(__file__).resolve().parent.parent / "assets"

INK = "#0d0d0d"
PAPER = "#ecebe6"
MUTED = "#8a8984"
SHADES = [PAPER, "#9d9c97", "#5c5b58", "#3a3a38"]
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
CARD_W, CARD_H = 420, 200
# hack-kosice-bsh vendors a C SDK (6.5 MB) that would read as the main language.
SKIP_REPOS = {"hack-kosice-bsh"}
# Markup and infra config, not languages anyone reads a profile for.
SKIP_LANGUAGES = {"HTML", "CSS", "SCSS", "Dockerfile", "Shell", "HCL"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
    contributionsCollection { totalCommitContributions }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
  }
}
"""


def fetch(token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]


def card(title: str, inner: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-label="{escape(title)}">
  <title>{escape(title)}</title>
  <rect x="1.5" y="1.5" width="{CARD_W - 3}" height="{CARD_H - 3}" fill="{INK}" stroke="{PAPER}" stroke-width="3"/>
  <text x="24" y="40" fill="{PAPER}" font-family="{SANS}" font-size="17" font-weight="800">{escape(title)}</text>
  {inner}
</svg>
"""


def stats_card(user: dict) -> str:
    repos = user["repositories"]["nodes"]
    rows = [
        ("Total stars", sum(r["stargazerCount"] for r in repos)),
        ("Commits (past year)", user["contributionsCollection"]["totalCommitContributions"]),
        ("Pull requests", user["pullRequests"]["totalCount"]),
        ("Issues", user["issues"]["totalCount"]),
        ("Contributed to", user["repositoriesContributedTo"]["totalCount"]),
    ]
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 74 + i * 25
        lines.append(
            f'<text x="24" y="{y}" fill="{PAPER}" font-family="{SANS}" font-size="13" font-weight="600">{label}</text>'
            f'<text x="{CARD_W - 24}" y="{y}" fill="{PAPER}" font-family="{SANS}" font-size="13" font-weight="800" text-anchor="end">{value}</text>'
        )
    name = user["name"] or LOGIN
    return card(f"{name}'s GitHub Stats", "\n  ".join(lines))


def top_languages(user: dict, limit: int = 4) -> list[tuple[str, float]]:
    """Score is sqrt(bytes) * sqrt(repos using it), so one repo with a vendored SDK can't swamp the rest."""
    sizes: dict[str, int] = {}
    counts: dict[str, int] = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"] in SKIP_REPOS:
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
            counts[name] = counts.get(name, 0) + 1
    scores = {name: (sizes[name] * counts[name]) ** 0.5 for name in sizes if name not in SKIP_LANGUAGES}
    total = sum(scores.values()) or 1
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = [(name, size / total) for name, size in ranked[:limit]]
    rest = 1 - sum(share for _, share in top)
    if len(ranked) > limit and rest > 0:
        top[-1] = ("Other", top[-1][1] + rest)
    return top


def langs_card(user: dict) -> str:
    langs = top_languages(user)
    bar_x, bar_w, gap = 24, CARD_W - 48, 3
    usable = bar_w - gap * (len(langs) - 1)
    parts, x = [], bar_x
    for i, (_, share) in enumerate(langs):
        w = usable * share
        parts.append(f'<rect x="{x:.1f}" y="62" width="{w:.1f}" height="10" fill="{SHADES[i]}"/>')
        x += w + gap
    for i, (name, share) in enumerate(langs):
        col, row = i % 2, i // 2
        lx, ly = 24 + col * 190, 106 + row * 28
        parts.append(
            f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" fill="{SHADES[i]}"/>'
            f'<text x="{lx + 18}" y="{ly}" fill="{PAPER}" font-family="{SANS}" font-size="13" font-weight="600">'
            f'{escape(name)} <tspan fill="{MUTED}">{share * 100:.0f}%</tspan></text>'
        )
    return card("Most Used Languages", "\n  ".join(parts))


if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("set GH_TOKEN")
    user = fetch(token)
    (ASSETS / "stats.svg").write_text(stats_card(user))
    (ASSETS / "langs.svg").write_text(langs_card(user))
    print("wrote stats.svg, langs.svg")
