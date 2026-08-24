"""Normalize, filter, rank, and label public profile activity."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


NOISE_PREFIXES = (
    "bump ",
    "build(deps)",
    "chore(deps)",
    "deps:",
    "format ",
    "format:",
    "chore: format",
    "prettier:",
    "style:",
    "chore(profile): update",
)
BOT_MARKERS = ("[bot]", "dependabot", "renovate", "github-actions")
ACTIVITY_WEIGHTS = {"COMMIT": 1, "PUSH": 2, "MERGE": 3, "RELEASE": 5}


def parse_timestamp(value: str) -> datetime:
    """Parse a GitHub timestamp and always return an aware UTC datetime."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class ActivityItem:
    kind: str
    repository: str
    timestamp: str
    summary: str
    url: str = ""
    branch: str = ""
    commits: int = 1

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ActivityItem":
        return cls(
            kind=str(value.get("kind") or "ACTIVITY").upper(),
            repository=str(value.get("repository") or ""),
            timestamp=utc_timestamp(parse_timestamp(str(value.get("timestamp")))),
            summary=str(value.get("summary") or ""),
            url=str(value.get("url") or ""),
            branch=str(value.get("branch") or ""),
            commits=max(1, int(value.get("commits") or 1)),
        )


def is_bot(value: str) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in BOT_MARKERS)


def is_noise(summary: str) -> bool:
    lowered = summary.strip().casefold()
    return not lowered or lowered.startswith(NOISE_PREFIXES)


def meaningful_activity(
    items: Iterable[ActivityItem], *, username: str
) -> list[ActivityItem]:
    """Remove profile automation, bots, dependency bumps, and formatting noise."""

    filtered = [
        item
        for item in items
        if item.repository.casefold() != username.casefold()
        and not is_bot(item.summary)
        and not is_noise(item.summary)
    ]
    return sorted(
        filtered,
        key=lambda item: (
            -parse_timestamp(item.timestamp).timestamp(),
            item.repository.casefold(),
            item.kind,
            item.summary.casefold(),
        ),
    )


def current_state(timestamp: str, *, now: datetime) -> str:
    """Derive recency state solely from the last public activity timestamp."""

    age = now.astimezone(timezone.utc) - parse_timestamp(timestamp)
    if age < timedelta(hours=24):
        return "SHIPPING"
    if age < timedelta(days=3):
        return "BUILDING"
    if age < timedelta(days=7):
        return "ACTIVE"
    return "IDLE"


def relative_age(timestamp: str, *, now: datetime) -> str:
    age = max(timedelta(0), now.astimezone(timezone.utc) - parse_timestamp(timestamp))
    seconds = int(age.total_seconds())
    if seconds < 3600:
        return f"{max(1, seconds // 60)}M AGO"
    if seconds < 86400:
        return f"{seconds // 3600}H AGO"
    return f"{seconds // 86400}D AGO"


def select_now_playing(
    items: Iterable[ActivityItem],
    repositories: Iterable[dict[str, Any]],
    *,
    username: str,
) -> dict[str, Any] | None:
    """Choose the newest meaningful repo signal, falling back to pushed_at."""

    activity = meaningful_activity(items, username=username)
    activity_candidate: dict[str, Any] | None = None
    if activity:
        item = activity[0]
        activity_candidate = {
            "repository": item.repository,
            "timestamp": item.timestamp,
            "summary": item.summary,
            "branch": item.branch,
            "url": item.url,
        }

    candidates = [
        repo
        for repo in repositories
        if repo.get("name")
        and repo["name"].casefold() != username.casefold()
        and repo.get("pushed_at")
        and not repo.get("archived")
        and not repo.get("fork")
    ]
    if not candidates:
        return activity_candidate
    selected_repo = sorted(
        candidates,
        key=lambda repo: (-parse_timestamp(repo["pushed_at"]).timestamp(), repo["name"].casefold()),
    )[0]
    repository_candidate = {
        "repository": selected_repo["name"],
        "timestamp": utc_timestamp(parse_timestamp(selected_repo["pushed_at"])),
        "summary": "Latest public repository push",
        "branch": "",
        "url": selected_repo.get("html_url") or "",
    }
    if not activity_candidate:
        return repository_candidate
    return max(
        (activity_candidate, repository_candidate),
        key=lambda candidate: (
            parse_timestamp(candidate["timestamp"]).timestamp(),
            candidate["repository"].casefold(),
        ),
    )


def score_repositories(
    items: Iterable[ActivityItem],
    repositories: Iterable[dict[str, Any]],
    *,
    now: datetime,
    days: int = 30,
) -> list[dict[str, Any]]:
    """Rank repositories by recent work signals, never by popularity."""

    cutoff = now.astimezone(timezone.utc) - timedelta(days=days)
    scores: dict[str, int] = {}
    latest: dict[str, str] = {}
    pushed_repositories: set[str] = set()
    for item in items:
        when = parse_timestamp(item.timestamp)
        if when < cutoff:
            continue
        weight = ACTIVITY_WEIGHTS.get(item.kind, 0)
        if not weight:
            continue
        scores[item.repository] = scores.get(item.repository, 0) + weight * (
            item.commits if item.kind == "COMMIT" else 1
        )
        latest[item.repository] = max(latest.get(item.repository, ""), item.timestamp)
        if item.kind == "PUSH":
            pushed_repositories.add(item.repository)

    # A pushed_at signal counts once even when public Events has expired.
    for repo in repositories:
        name = str(repo.get("name") or "")
        pushed_at = repo.get("pushed_at")
        if name and name not in pushed_repositories and pushed_at and parse_timestamp(pushed_at) >= cutoff:
            scores[name] = scores.get(name, 0) + ACTIVITY_WEIGHTS["PUSH"]
            latest[name] = max(latest.get(name, ""), utc_timestamp(parse_timestamp(pushed_at)))

    return sorted(
        (
            {"repository": name, "score": score, "timestamp": latest[name]}
            for name, score in scores.items()
            if score > 0
        ),
        key=lambda row: (-row["score"], -parse_timestamp(row["timestamp"]).timestamp(), row["repository"].casefold()),
    )


def release_status(release: dict[str, Any] | None, *, now: datetime) -> str:
    if not release:
        return "NO RELEASE"
    published = parse_timestamp(str(release["published_at"]))
    return "NEW DROP" if now.astimezone(timezone.utc) - published <= timedelta(days=7) else "LATEST DROP"


def published_state(
    project: dict[str, Any],
    *,
    has_release: bool,
) -> str:
    """Return one controlled public state from verified config and release data."""

    published = project.get("published") or {}
    if published.get("type") not in (None, "", "none") and published.get("url"):
        return "PLAYABLE"
    if has_release:
        return "RELEASED"
    lifecycle = str(project.get("lifecycle") or "prototype").replace("-", " ").upper()
    if lifecycle in {"ACTIVE DEVELOPMENT", "PROTOTYPE", "ARCHIVED"}:
        return lifecycle
    return "PROTOTYPE"
