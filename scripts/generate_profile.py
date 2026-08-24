"""Generate the repository-owned Player Profile OS assets and README blocks."""

from __future__ import annotations

import argparse
import html
import json
import os
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlparse

import yaml

from github_data import fetch_profile_data
from activity import (
    ActivityItem,
    current_state,
    meaningful_activity,
    parse_timestamp,
    published_state,
    relative_age,
    release_status,
    score_repositories,
    select_now_playing,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "assets" / "generated"

PALETTE = {
    "background": "#0D0221",
    "cyan": "#00F0FF",
    "magenta": "#FF2E97",
    "purple": "#7B2FF7",
    "green": "#39FF14",
    "gold": "#FFB800",
    "text": "#C9D1D9",
    "white": "#FFFFFF",
}

# Playful profile metric; these are deliberately visible and documented.
XP_WEIGHTS = {
    "public_repositories": 100,
    "commits_30d": 5,
    "releases": 150,
    "stars_received": 20,
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return data


def calculate_xp(data: dict[str, Any]) -> tuple[int, int]:
    xp = sum(int(data.get(key, 0)) * weight for key, weight in XP_WEIGHTS.items())
    level = xp // 1000 + 1
    return xp, level


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _svg_shell(
    *,
    title: str,
    description: str,
    body: str,
    width: int,
    height: int,
    accent: str,
) -> str:
    body = body.strip()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="svg-title svg-desc">
  <title id="svg-title">{_escape(title)}</title>
  <desc id="svg-desc">{_escape(description)}</desc>
  <defs>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="#7B2FF7" stroke-opacity="0.10" stroke-width="1"/>
    </pattern>
    <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#FFFFFF" opacity="0.025"/>
    </pattern>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .display {{ font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif; font-weight: 800; letter-spacing: 2px; }}
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
      .label {{ fill: #C9D1D9; font-size: 15px; letter-spacing: 1.4px; }}
      .value {{ fill: #FFFFFF; font-size: 22px; font-weight: 700; }}
      .muted {{ fill: #C9D1D9; font-size: 14px; }}
      .pulse-dot {{ animation: hudPulse 2.4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
      .radar-sweep {{ animation: radarSweep 5s linear infinite; }}
      .cursor {{ animation: cursorBlink 1.15s steps(1, end) infinite; }}
      @keyframes hudPulse {{ 0%, 100% {{ opacity: .45; transform: scale(.82); }} 50% {{ opacity: 1; transform: scale(1); }} }}
      @keyframes radarSweep {{ 0% {{ transform: translateX(-720px); opacity: 0; }} 12%, 88% {{ opacity: .65; }} 100% {{ transform: translateX(720px); opacity: 0; }} }}
      @keyframes cursorBlink {{ 0%, 48% {{ opacity: 1; }} 49%, 100% {{ opacity: 0; }} }}
      @media (prefers-reduced-motion: reduce) {{
        .pulse-dot, .radar-sweep, .cursor {{ animation: none !important; }}
      }}
    </style>
  </defs>
  <rect width="{width}" height="{height}" rx="20" fill="#0D0221"/>
  <rect x="1.5" y="1.5" width="{width - 3}" height="{height - 3}" rx="18.5" fill="none" stroke="{accent}" stroke-width="3"/>
  <rect x="12" y="12" width="{width - 24}" height="{height - 24}" rx="12" fill="url(#grid)"/>
  <rect width="{width}" height="{height}" rx="20" fill="url(#scanlines)"/>
  {body}
</svg>
'''


def render_hero_svg(profile: dict[str, Any]) -> str:
    player = profile["player"]
    focus = player["focus"]
    roles = ["GAME DEVELOPER", "AI / ML ENGINEER", "INTERACTIVE SYSTEMS"]
    role_nodes = []
    for index, role in enumerate(roles):
        x = 62 + index * 286
        role_nodes.append(
            f'<text x="{x}" y="270" class="mono" fill="#FFFFFF" font-size="18" font-weight="700">{_escape(role)}</text>'
        )
        if index < len(roles) - 1:
            role_nodes.append(
                f'<line x1="{x + 250}" y1="244" x2="{x + 250}" y2="282" stroke="#7B2FF7" stroke-width="2"/>'
            )

    body = f'''
  <path d="M32 48 H250" stroke="#00F0FF" stroke-width="3" filter="url(#glow)"/>
  <text x="62" y="78" class="mono" fill="#00F0FF" font-size="17" font-weight="700">INSERT COIN // PLAYER PROFILE OS</text>
  <text x="58" y="157" class="display" fill="#FFFFFF" font-size="53">{_escape(player['name'].upper())}</text>
  <text x="62" y="207" class="mono" fill="#FF2E97" font-size="22" font-weight="700">PLAYER 1 READY // {_escape(player['handle'])}</text>
  {''.join(role_nodes)}
  <text x="62" y="331" class="mono" fill="#C9D1D9" font-size="16">“{_escape(player['motto'])}”</text>
  <text x="898" y="78" text-anchor="end" class="mono" fill="#39FF14" font-size="14">STATUS: {_escape(player['status'])}</text>
  <circle cx="916" cy="73" r="5" fill="#39FF14" filter="url(#glow)"/>
  <text x="898" y="331" text-anchor="end" class="mono" fill="#7B2FF7" font-size="12">FOCUS: {_escape(' / '.join(focus[:3]).upper())}</text>
'''
    return _svg_shell(
        title=f"{player['name']} — Player 1 Ready",
        description="Arcade-style title screen identifying Kaustuv as a game developer, AI engineer, and interactive systems developer.",
        body=body,
        width=960,
        height=380,
        accent=PALETTE["purple"],
    )


def render_player_save_svg(data: dict[str, Any], profile: dict[str, Any]) -> str:
    player = profile["player"]
    xp, level = calculate_xp(data)
    progress = xp % 1000
    bar_width = int(520 * progress / 1000)
    saved = datetime.fromisoformat(data["generated_at"]).strftime("%d %b %Y").upper()
    metrics = [
        ("PUBLIC SOURCE REPOS", data["public_repositories"]),
        ("PUBLIC COMMITS / 30D", data["commits_30d"]),
        ("ACTIVE WORLDS / 180D", data["active_repositories_180d"]),
        ("RELEASES PUBLISHED", data["releases"]),
        ("TOP SIGNAL", str(data["top_language"]).upper()),
        ("STARS RECEIVED", data["stars_received"]),
    ]
    nodes = []
    for index, (label, value) in enumerate(metrics):
        column = index % 2
        row = index // 2
        x = 62 + column * 438
        y = 246 + row * 67
        nodes.append(f'<text x="{x}" y="{y}" class="label mono">{_escape(label)}</text>')
        nodes.append(
            f'<text x="{x + 360}" y="{y}" text-anchor="end" class="value mono">{_escape(value)}</text>'
        )

    body = f'''
  <text x="62" y="74" class="display" fill="#00F0FF" font-size="30">PLAYER SAVE // SLOT 01</text>
  <text x="898" y="72" text-anchor="end" class="mono" fill="#39FF14" font-size="15">SAVE DATA VERIFIED</text>
  <line x1="62" y1="94" x2="898" y2="94" stroke="#7B2FF7" stroke-width="2"/>
  <text x="62" y="143" class="display" fill="#FFFFFF" font-size="31">{_escape(player['name'].upper())}</text>
  <text x="62" y="181" class="mono" fill="#C9D1D9" font-size="17">CLASS  {_escape(player['class'].upper())}</text>
  <text x="898" y="143" text-anchor="end" class="display" fill="#FFB800" font-size="31">LVL {level:02d}</text>
  <text x="898" y="181" text-anchor="end" class="mono" fill="#39FF14" font-size="17">STATUS  {_escape(player['status'])}</text>
  {''.join(nodes)}
  <text x="62" y="456" class="label mono">PLAYER XP // PLAYFUL PROFILE METRIC</text>
  <text x="898" y="456" text-anchor="end" class="value mono">{xp:,} XP</text>
  <rect x="62" y="474" width="520" height="15" rx="7.5" fill="#241344" stroke="#7B2FF7"/>
  <rect x="62" y="474" width="{bar_width}" height="15" rx="7.5" fill="#FF2E97"/>
  <text x="322" y="518" text-anchor="middle" class="mono" fill="#C9D1D9" font-size="12">{progress} / 1000 TO NEXT LEVEL</text>
  <text x="898" y="487" text-anchor="end" class="mono" fill="#C9D1D9" font-size="13">LAST SAVE  {saved}</text>
'''
    return _svg_shell(
        title="Player Save — live public GitHub telemetry",
        description="A custom save slot showing public source repositories, recent public commits, active repositories, releases, language signal, stars, and transparent profile XP.",
        body=body,
        width=960,
        height=545,
        accent=PALETTE["cyan"],
    )


def render_dev_dna_svg(profile: dict[str, Any]) -> str:
    rows = profile["dev_dna"]
    height = 150 + len(rows) * 58
    nodes = []
    colors = ["#00F0FF", "#FF2E97", "#7B2FF7", "#39FF14", "#FFB800", "#00F0FF"]
    for index, item in enumerate(rows):
        y = 142 + index * 58
        width = int(540 * int(item["value"]) / 100)
        color = colors[index % len(colors)]
        nodes.extend(
            [
                f'<text x="62" y="{y}" class="label mono">{_escape(item["label"].upper())}</text>',
                f'<rect x="310" y="{y - 17}" width="540" height="18" rx="4" fill="#241344" stroke="#463068"/>',
                f'<rect x="310" y="{y - 17}" width="{width}" height="18" rx="4" fill="{color}"/>',
                f'<text x="898" y="{y}" text-anchor="end" class="value mono">{int(item["value"]):02d}</text>',
            ]
        )
    body = f'''
  <text x="62" y="70" class="display" fill="#FF2E97" font-size="30">DEV DNA // CURRENT BUILD</text>
  <text x="898" y="68" text-anchor="end" class="mono" fill="#C9D1D9" font-size="13">POSITIONING MAP // EDITABLE CONFIG</text>
  <line x1="62" y1="91" x2="898" y2="91" stroke="#7B2FF7" stroke-width="2"/>
  {''.join(nodes)}
  <text x="62" y="{height - 26}" class="mono" fill="#C9D1D9" font-size="12">Deliberately defined in profile/profile.yml — not an official GitHub measurement.</text>
'''
    return _svg_shell(
        title="Dev DNA — current engineering positioning",
        description="An editable positioning map covering gameplay systems, AI, interactive web, tools, full stack work, and multiplayer.",
        body=body,
        width=960,
        height=height,
        accent=PALETTE["magenta"],
    )


def render_ship_log_svg(data: dict[str, Any]) -> str:
    entries = data.get("ship_log") or []
    visible = entries[:5]
    if not visible:
        visible = [
            {
                "date": "—",
                "kind": "IDLE",
                "summary": "No public activity was returned in the current GitHub Events window.",
            }
        ]
    height = 132 + len(visible) * 58
    nodes = []
    kind_colors = {
        "PUSH": "#00F0FF",
        "COMMIT": "#00F0FF",
        "RELEASE": "#39FF14",
        "MERGE": "#FF2E97",
        "WORLD": "#FFB800",
        "IDLE": "#FFB800",
    }
    for index, item in enumerate(visible):
        y = 128 + index * 58
        color = kind_colors.get(item.get("kind"), "#7B2FF7")
        nodes.extend(
            [
                f'<rect x="62" y="{y - 25}" width="118" height="34" rx="5" fill="#241344" stroke="{color}"/>',
                f'<text x="121" y="{y - 2}" text-anchor="middle" class="mono" fill="{color}" font-size="13" font-weight="700">{_escape(item.get("date", "")[:10])}</text>',
                f'<text x="206" y="{y - 2}" class="mono" fill="#FFFFFF" font-size="16">[{_escape(item.get("kind", "LOG"))}]  {_escape(_truncate(item.get("summary", ""), 72))}</text>',
            ]
        )
    body = f'''
  <text x="62" y="70" class="display" fill="#39FF14" font-size="30">SHIP LOG // RECENT PATCHES</text>
  <text x="898" y="68" text-anchor="end" class="mono" fill="#C9D1D9" font-size="13">PUBLIC GITHUB ACTIVITY // LATEST SIGNALS</text>
  <line x1="62" y1="91" x2="898" y2="91" stroke="#7B2FF7" stroke-width="2"/>
  {''.join(nodes)}
'''
    return _svg_shell(
        title="Ship Log — recent public GitHub activity",
        description="Five factual recent public commits, pushes, releases, or merged pull requests from GitHub.",
        body=body,
        width=960,
        height=height,
        accent=PALETTE["green"],
    )


def _activity_items(data: dict[str, Any]) -> list[ActivityItem]:
    items: list[ActivityItem] = []
    for value in data.get("activity") or []:
        try:
            items.append(ActivityItem.from_mapping(value))
        except (TypeError, ValueError, KeyError):
            continue
    return meaningful_activity(items, username=str(data.get("username") or ""))


def _sync_label(data: dict[str, Any]) -> str:
    return parse_timestamp(data["generated_at"]).strftime("%Y-%m-%d %H:%M UTC")


def render_now_playing_svg(data: dict[str, Any], projects: list[dict[str, Any]]) -> str:
    now = parse_timestamp(data["generated_at"])
    items = _activity_items(data)
    repositories = data.get("repositories") or []
    selected = select_now_playing(
        items,
        repositories,
        username=str(data.get("username") or ""),
    )
    if selected:
        repository = selected["repository"]
        project = next(
            (
                project
                for project in projects
                if Path(urlparse(str(project.get("github") or "")).path).name.casefold()
                == repository.casefold()
            ),
            None,
        )
        repo = next((repo for repo in repositories if repo.get("name") == repository), {})
        tech = (project or {}).get("engine") or repo.get("language") or "PUBLIC REPOSITORY"
        state = current_state(selected["timestamp"], now=now)
        state_color = "#39FF14" if state in {"SHIPPING", "BUILDING", "ACTIVE"} else "#FFB800"
        age = relative_age(selected["timestamp"], now=now)
        branch = selected.get("branch")
        branch_node = (
            f'<text x="72" y="250" class="mono" fill="#C9D1D9" font-size="14">BRANCH  {_escape(_truncate(branch, 44))}</text>'
            if branch
            else ""
        )
        body = f'''
  <text x="62" y="68" class="display" fill="#00F0FF" font-size="30">NOW PLAYING</text>
  <text x="898" y="66" text-anchor="end" class="mono" fill="#C9D1D9" font-size="12">LAST SYNC // {_sync_label(data)}</text>
  <line x1="62" y1="90" x2="898" y2="90" stroke="#7B2FF7" stroke-width="2"/>
  <circle class="pulse-dot" cx="77" cy="137" r="7" fill="{state_color}" filter="url(#glow)"/>
  <text x="98" y="143" class="mono" fill="{state_color}" font-size="16" font-weight="700">{_escape(state)} // {age}</text>
  <text x="70" y="196" class="display" fill="#FFFFFF" font-size="38">{_escape(_truncate(repository.upper(), 34))}</text>
  <text x="898" y="195" text-anchor="end" class="mono" fill="#FFB800" font-size="15">LOADOUT // {_escape(str(tech).upper())}</text>
{branch_node}
  <rect x="62" y="280" width="836" height="62" rx="8" fill="#14072D" stroke="#463068"/>
  <text x="82" y="307" class="mono" fill="#7B2FF7" font-size="12">LATEST MEANINGFUL SIGNAL</text>
  <text x="82" y="330" class="mono" fill="#FFFFFF" font-size="15">{_escape(_truncate(selected['summary'], 84))}</text>
  <text class="cursor mono" x="888" y="330" text-anchor="end" fill="#00F0FF" font-size="18">▮</text>
'''
    else:
        body = f'''
  <text x="62" y="68" class="display" fill="#00F0FF" font-size="30">NOW PLAYING</text>
  <text x="898" y="66" text-anchor="end" class="mono" fill="#C9D1D9" font-size="12">LAST SYNC // {_sync_label(data)}</text>
  <line x1="62" y1="90" x2="898" y2="90" stroke="#7B2FF7" stroke-width="2"/>
  <text x="480" y="204" text-anchor="middle" class="display" fill="#FFB800" font-size="30">NO PUBLIC WORLD SIGNAL</text>
  <text x="480" y="246" text-anchor="middle" class="mono" fill="#C9D1D9" font-size="15">THE HUD WILL RESUME WHEN A MEANINGFUL PUBLIC PUSH APPEARS.</text>
'''
    return _svg_shell(
        title="Now Playing — latest meaningful public repository",
        description="The most recently active meaningful public repository, with a timestamp-derived activity state and latest factual signal.",
        body=body,
        width=960,
        height=380,
        accent=PALETTE["cyan"],
    )


def render_activity_radar_svg(data: dict[str, Any]) -> str:
    now = parse_timestamp(data["generated_at"])
    cutoff = now - timedelta(days=14)
    visible = [item for item in _activity_items(data) if parse_timestamp(item.timestamp) >= cutoff]
    colors = {"COMMIT": "#00F0FF", "PUSH": "#7B2FF7", "MERGE": "#FF2E97", "RELEASE": "#39FF14"}
    nodes: list[str] = []
    for index, item in enumerate(visible[:18]):
        age = (now - parse_timestamp(item.timestamp)).total_seconds()
        x = 850 - int(min(14 * 86400, max(0, age)) / (14 * 86400) * 740)
        y = 154 + (index % 3) * 44
        color = colors.get(item.kind, "#FFB800")
        nodes.append(f'<line x1="{x}" y1="126" x2="{x}" y2="{y}" stroke="{color}" stroke-opacity=".35"/>')
        nodes.append(f'<circle class="pulse-dot" cx="{x}" cy="{y}" r="6" fill="{color}"/>')
    signal = (
        f'{len(visible)} PUBLIC PULSE{"S" if len(visible) != 1 else ""} // 14D'
        if visible
        else "NO PUBLIC PULSES DETECTED // 14D"
    )
    body = f'''
  <text x="62" y="68" class="display" fill="#FF2E97" font-size="30">ACTIVITY RADAR // 14D</text>
  <text x="898" y="66" text-anchor="end" class="mono" fill="#C9D1D9" font-size="12">LAST SYNC // {_sync_label(data)}</text>
  <line x1="62" y1="90" x2="898" y2="90" stroke="#7B2FF7" stroke-width="2"/>
  <rect x="100" y="116" width="760" height="160" rx="8" fill="#100529" stroke="#463068"/>
  <line x1="110" y1="250" x2="850" y2="250" stroke="#7B2FF7" stroke-width="2"/>
  <line class="radar-sweep" x1="480" y1="122" x2="480" y2="270" stroke="#00F0FF" stroke-width="3" filter="url(#glow)"/>
{''.join(nodes)}
  <text x="110" y="302" class="mono" fill="#C9D1D9" font-size="12">14 DAYS AGO</text>
  <text x="850" y="302" text-anchor="end" class="mono" fill="#C9D1D9" font-size="12">SYNC</text>
  <text x="480" y="340" text-anchor="middle" class="mono" fill="#FFB800" font-size="14" font-weight="700">{signal}</text>
'''
    return _svg_shell(
        title="Activity Radar — fourteen days of public development signals",
        description="A fourteen-day timeline of public commits, pushes, merged pull requests, and releases. Motion is decorative and respects reduced-motion preferences.",
        body=body,
        width=960,
        height=372,
        accent=PALETTE["magenta"],
    )


def render_live_feed_svg(data: dict[str, Any], projects: list[dict[str, Any]]) -> str:
    now = parse_timestamp(data["generated_at"])
    items = _activity_items(data)
    pushes = [item for item in items if item.kind in {"COMMIT", "PUSH"}][:5]
    repos = (data.get("repositories") or [])[:6]
    scored = score_repositories(items, data.get("repositories") or [], now=now)
    releases_by_repo = {str(item.get("repository") or "").casefold() for item in data.get("release_feed") or []}
    nodes: list[str] = []
    left_y = 142
    if pushes:
        for index, item in enumerate(pushes):
            y = left_y + index * 58
            nodes.extend([
                f'<text x="62" y="{y}" class="mono" fill="#00F0FF" font-size="12">{_escape(item.timestamp[:10])}</text>',
                f'<text x="164" y="{y}" class="mono" fill="#FFFFFF" font-size="14" font-weight="700">{_escape(_truncate(item.repository, 24))}</text>',
                f'<text x="164" y="{y + 20}" class="mono" fill="#C9D1D9" font-size="12">{_escape(_truncate(item.summary, 42))}</text>',
            ])
    else:
        nodes.append('<text x="62" y="162" class="mono" fill="#FFB800" font-size="14">NO MEANINGFUL PUBLIC PUSHES IN THE CURRENT WINDOW.</text>')

    if repos:
        for index, repo in enumerate(repos[:5]):
            y = left_y + index * 58
            state = current_state(repo["pushed_at"], now=now)
            state_color = "#39FF14" if state in {"SHIPPING", "BUILDING", "ACTIVE"} else "#FFB800"
            nodes.extend([
                f'<text x="525" y="{y}" class="mono" fill="#FFFFFF" font-size="14" font-weight="700">{_escape(_truncate(repo["name"], 25))}</text>',
                f'<text x="525" y="{y + 20}" class="mono" fill="#C9D1D9" font-size="12">{_escape(str(repo.get("language") or "N/A").upper())} // {relative_age(repo["pushed_at"], now=now)}</text>',
                f'<text x="898" y="{y}" text-anchor="end" class="mono" fill="{state_color}" font-size="12">{state}</text>',
            ])
    else:
        nodes.append('<text x="525" y="162" class="mono" fill="#FFB800" font-size="14">NO PUBLIC WORLDS AVAILABLE.</text>')

    if scored:
        hot = scored[0]
        hot_text = f'{hot["repository"]} // ACTIVITY SCORE {hot["score"]}'
    else:
        hot_text = "NO HOT WORLD // SIGNAL BELOW THRESHOLD"
    status_parts = []
    for project in projects[:4]:
        repo_name = Path(urlparse(str(project.get("github") or "")).path).name.casefold()
        state = published_state(project, has_release=repo_name in releases_by_repo)
        status_parts.append(f'{project["name"]}: {state}')
    status_text = "  •  ".join(status_parts)
    body = f'''
  <text x="62" y="68" class="display" fill="#39FF14" font-size="30">LIVE FEED // PLAYER ACTIVITY</text>
  <text x="898" y="66" text-anchor="end" class="mono" fill="#C9D1D9" font-size="12">LAST SYNC // {_sync_label(data)}</text>
  <line x1="62" y1="90" x2="898" y2="90" stroke="#7B2FF7" stroke-width="2"/>
  <text x="62" y="116" class="mono" fill="#FF2E97" font-size="13" font-weight="700">RECENT PUSHES</text>
  <text x="525" y="116" class="mono" fill="#FF2E97" font-size="13" font-weight="700">RECENTLY PLAYED WORLDS</text>
  <line x1="480" y1="110" x2="480" y2="430" stroke="#463068"/>
  {''.join(nodes)}
  <rect x="62" y="452" width="836" height="70" rx="8" fill="#14072D" stroke="#FFB800"/>
  <text x="82" y="480" class="mono" fill="#FFB800" font-size="12">HOT WORLD // 30D // COMMITS×1 + PUSH×2 + MERGE×3 + RELEASE×5</text>
  <text x="82" y="506" class="mono" fill="#FFFFFF" font-size="16" font-weight="700">{_escape(_truncate(hot_text, 78))}</text>
  <text x="62" y="568" class="mono" fill="#00F0FF" font-size="13" font-weight="700">SYSTEM STATUS // VERIFIED CONFIG + PUBLIC RELEASES</text>
  <text x="62" y="600" class="mono" fill="#C9D1D9" font-size="12">{_escape(_truncate(status_text, 118))}</text>
'''
    return _svg_shell(
        title="Live Feed — recent pushes, recently played worlds, and system status",
        description="A compact public activity feed with recent development signals, repository recency, activity scoring, and verified project publication states.",
        body=body,
        width=960,
        height=640,
        accent=PALETTE["green"],
    )


def render_release_radar_svg(data: dict[str, Any], projects: list[dict[str, Any]]) -> str:
    now = parse_timestamp(data["generated_at"])
    releases = data.get("release_feed") or []
    latest = releases[0] if releases else None
    label = release_status(latest, now=now)
    if latest:
        release_name = _truncate(str(latest.get("name") or latest.get("tag") or "Release"), 54)
        detail = f'{latest.get("repository")} // {release_name}'
        date = parse_timestamp(latest["published_at"]).strftime("%Y-%m-%d %H:%M UTC")
        footer = f'PUBLISHED // {date}'
    else:
        playable = sum(1 for project in projects if published_state(project, has_release=False) == "PLAYABLE")
        detail = "NO PUBLIC GITHUB RELEASE DETECTED"
        footer = f"VERIFIED PLAYABLE BUILDS // {playable}"
    body = f'''
  <text x="62" y="68" class="display" fill="#FFB800" font-size="30">RELEASE RADAR</text>
  <text x="898" y="66" text-anchor="end" class="mono" fill="#C9D1D9" font-size="12">LAST SYNC // {_sync_label(data)}</text>
  <line x1="62" y1="90" x2="898" y2="90" stroke="#7B2FF7" stroke-width="2"/>
  <rect x="62" y="120" width="178" height="48" rx="6" fill="#241344" stroke="#39FF14"/>
  <text x="151" y="151" text-anchor="middle" class="mono" fill="#39FF14" font-size="14" font-weight="700">{label}</text>
  <text x="62" y="226" class="display" fill="#FFFFFF" font-size="31">{_escape(detail.upper())}</text>
  <text x="62" y="272" class="mono" fill="#C9D1D9" font-size="14">{_escape(footer)}</text>
'''
    return _svg_shell(
        title="Release Radar — latest public GitHub release",
        description="The newest factual public GitHub release, or an explicit no-release state paired with the count of verified playable builds.",
        body=body,
        width=960,
        height=310,
        accent=PALETTE["gold"],
    )


def render_world_select_svg(
    projects: Iterable[dict[str, Any]], release_repositories: set[str] | None = None
) -> str:
    featured = [project for project in projects if project.get("featured")]
    release_repositories = release_repositories or set()
    card_height = 244
    height = 116 + len(featured) * card_height
    colors = ["#FF2E97", "#00F0FF", "#7B2FF7", "#39FF14"]
    nodes = []
    for index, project in enumerate(featured):
        y = 100 + index * card_height
        accent = colors[index % len(colors)]
        stack = " / ".join(project["stack"])
        repo_name = Path(urlparse(str(project.get("github") or "")).path).name.casefold()
        state = published_state(project, has_release=repo_name in release_repositories)
        state_color = "#39FF14" if state in {"PLAYABLE", "RELEASED"} else "#FFB800"
        lines = textwrap.wrap(project["description"], width=86)[:2]
        nodes.extend(
            [
                f'<rect x="38" y="{y}" width="884" height="220" rx="12" fill="#14072D" stroke="{accent}" stroke-width="2"/>',
                f'<rect x="38" y="{y}" width="14" height="220" rx="7" fill="{accent}"/>',
                f'<text x="74" y="{y + 44}" class="mono" fill="{accent}" font-size="15" font-weight="700">WORLD {index + 1:02d} // {_escape(project["category"].upper())}</text>',
                f'<text x="74" y="{y + 82}" class="display" fill="#FFFFFF" font-size="28">{_escape(project["name"].upper())}</text>',
                f'<text x="74" y="{y + 112}" class="mono" fill="#FFB800" font-size="14">{_escape(project["tagline"])}</text>',
            ]
        )
        for line_index, line in enumerate(lines):
            nodes.append(
                f'<text x="74" y="{y + 143 + line_index * 22}" class="mono" fill="#C9D1D9" font-size="14">{_escape(line)}</text>'
            )
        nodes.extend(
            [
                f'<text x="74" y="{y + 198}" class="mono" fill="#FFFFFF" font-size="13">ROLE  {_escape(project["role"].upper())}</text>',
                f'<text x="475" y="{y + 198}" class="mono" fill="#C9D1D9" font-size="13">LOADOUT  {_escape(_truncate(stack.upper(), 50))}</text>',
                f'<circle cx="{760}" cy="{y + 39}" r="5" fill="{state_color}"/>',
                f'<text x="895" y="{y + 44}" text-anchor="end" class="mono" fill="{state_color}" font-size="13" font-weight="700">{_escape(state)}</text>',
            ]
        )
    body = f'''
  <text x="48" y="65" class="display" fill="#FFB800" font-size="31">WORLD SELECT // FEATURED BUILDS</text>
  <text x="912" y="64" text-anchor="end" class="mono" fill="#C9D1D9" font-size="13">CHOOSE A WORLD // SOURCE BELOW</text>
  {''.join(nodes)}
'''
    return _svg_shell(
        title="World Select — featured projects",
        description="Four vertically stacked project worlds covering gameplay systems, generative AI tooling, interactive web, and gamified learning.",
        body=body,
        width=960,
        height=height,
        accent=PALETTE["gold"],
    )


def _replace_marker(text: str, name: str, content: str) -> str:
    start = f"<!-- PLAYER_OS:{name}:START -->"
    end = f"<!-- PLAYER_OS:{name}:END -->"
    if start not in text or end not in text:
        raise ValueError(f"README marker pair missing: {name}")
    before, remainder = text.split(start, 1)
    _, after = remainder.split(end, 1)
    return f"{before}{start}\n{content.rstrip()}\n{end}{after}"


def _profile_markdown(profile: dict[str, Any]) -> str:
    player = profile["player"]
    focus = "\n".join(f"  - {item}" for item in player["focus"])
    return f'''```yaml
PLAYER:    {player['name']}
HANDLE:    {player['handle']}
CLASS:     {player['class']}
BUILD:     {player['build']}
FOCUS:
{focus}
STATUS:    {player['status']}
```'''


def _quests_markdown(profile: dict[str, Any]) -> str:
    active = "\n".join(f"- {item}" for item in profile["current_quests"])
    side = "\n".join(f"- {item}" for item in profile["side_quests"])
    return f'''**ACTIVE QUESTS**

{active}

<details>
<summary>SIDE QUESTS // OPTIONAL OBJECTIVES</summary>

{side}

</details>'''


def _world_links_markdown(projects: list[dict[str, Any]]) -> str:
    lines = []
    for index, project in enumerate(project for project in projects if project.get("featured")):
        links = [f"[SOURCE]({project['github']})"]
        if project.get("demo"):
            links.append(f"[ENTER WORLD]({project['demo']})")
        lines.append(
            f"**WORLD {index + 1:02d} // {project['name'].upper()}** — {project['tagline']}<br />\n"
            + " · ".join(links)
        )
    return "\n\n".join(lines)


def _tech_tree_markdown(profile: dict[str, Any]) -> str:
    lines = []
    for category, tools in profile["tech_tree"].items():
        formatted = " · ".join(f"`{tool}`" for tool in tools)
        lines.append(f"**{category.upper()}**<br />\n{formatted}")
    return "\n\n".join(lines)


def _achievements_markdown(profile: dict[str, Any]) -> str:
    return "\n".join(
        f"- **[{item['label']}]({item['url']})** — {item['detail']}"
        for item in profile["achievements"]
    )


def update_readme(template: str, profile: dict[str, Any], projects: list[dict[str, Any]]) -> str:
    text = _replace_marker(template, "PLAYER_PROFILE", _profile_markdown(profile))
    text = _replace_marker(text, "WORLD_LINKS", _world_links_markdown(projects))
    text = _replace_marker(text, "CURRENT_QUESTS", _quests_markdown(profile))
    text = _replace_marker(text, "TECH_TREE", _tech_tree_markdown(profile))
    text = _replace_marker(text, "ACHIEVEMENTS", _achievements_markdown(profile))
    return text


def _write_assets_atomically(output_dir: Path, assets: dict[str, str]) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="player-profile-", dir=output_dir.parent) as temp_name:
        staging = Path(temp_name)
        for name, content in assets.items():
            path = staging / name
            path.write_text(content, encoding="utf-8", newline="\n")
            if path.stat().st_size == 0:
                raise ValueError(f"Refusing to install empty generated asset: {name}")
            ET.parse(path)

        output_dir.mkdir(parents=True, exist_ok=True)
        for name in assets:
            os.replace(staging / name, output_dir / name)


def generate(
    *,
    profile_path: Path,
    projects_path: Path,
    output_dir: Path,
    data: dict[str, Any],
    readme_path: Path | None,
    readme_output: Path | None,
) -> list[Path]:
    profile = load_yaml(profile_path)
    projects_config = load_yaml(projects_path)
    projects = projects_config.get("projects")
    if not isinstance(projects, list):
        raise ValueError("profile/projects.yml must contain a projects list")

    release_repositories = {
        str(item.get("repository") or "").casefold() for item in data.get("release_feed") or []
    }
    assets = {
        "hero.svg": render_hero_svg(profile),
        "player-save.svg": render_player_save_svg(data, profile),
        "world-select.svg": render_world_select_svg(projects, release_repositories),
        "now-playing.svg": render_now_playing_svg(data, projects),
        "activity-radar.svg": render_activity_radar_svg(data),
        "live-feed.svg": render_live_feed_svg(data, projects),
        "release-radar.svg": render_release_radar_svg(data, projects),
        "dev-dna.svg": render_dev_dna_svg(profile),
        "ship-log.svg": render_ship_log_svg(data),
    }
    _write_assets_atomically(output_dir, assets)

    written = [output_dir / name for name in assets]
    if readme_path is not None:
        destination = readme_output or readme_path
        rendered = update_readme(readme_path.read_text(encoding="utf-8"), profile, projects)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8", newline="\n")
        written.append(destination)
    return written


def generate_live(
    *,
    username: str,
    token: str | None,
    profile_path: Path,
    projects_path: Path,
    output_dir: Path,
    readme_path: Path | None,
    readme_output: Path | None,
    fetcher: Callable[..., dict[str, Any]] = fetch_profile_data,
) -> list[Path]:
    """Fetch first, then render atomically so API failure preserves good output."""

    configured_projects = load_yaml(projects_path).get("projects") or []
    preferred_repositories = {
        Path(urlparse(project["github"]).path).name
        for project in configured_projects
        if project.get("featured") and project.get("github")
    }
    data = fetcher(
        username,
        token,
        preferred_repositories=preferred_repositories,
    )
    return generate(
        profile_path=profile_path,
        projects_path=projects_path,
        output_dir=output_dir,
        data=data,
        readme_path=readme_path,
        readme_output=readme_output,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=ROOT / "profile" / "profile.yml")
    parser.add_argument("--projects", type=Path, default=ROOT / "profile" / "projects.yml")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fixture", type=Path, help="Use deterministic JSON data instead of the network")
    parser.add_argument("--username", default="KaustuvMohapatra")
    parser.add_argument("--readme", type=Path, default=ROOT / "README.md")
    parser.add_argument("--readme-output", type=Path)
    parser.add_argument("--no-readme", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fixture:
        data = json.loads(args.fixture.read_text(encoding="utf-8"))
        written = generate(
            profile_path=args.profile,
            projects_path=args.projects,
            output_dir=args.output_dir,
            data=data,
            readme_path=None if args.no_readme else args.readme,
            readme_output=args.readme_output,
        )
    else:
        written = generate_live(
            username=args.username,
            token=os.environ.get("GITHUB_TOKEN"),
            profile_path=args.profile,
            projects_path=args.projects,
            output_dir=args.output_dir,
            readme_path=None if args.no_readme else args.readme,
            readme_output=args.readme_output,
        )
    print(f"Generated {len(written)} Player Profile OS files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
