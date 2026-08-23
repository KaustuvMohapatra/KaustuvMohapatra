"""Small GitHub REST client for the profile asset generator.

Only public, evidence-backed signals are collected. API failures are raised so the
caller can retain the last known-good generated assets.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any


API_ROOT = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """Raised when a GitHub API request cannot be completed safely."""


class GitHubClient:
    def __init__(self, token: str | None = None, retries: int = 2) -> None:
        self.token = token
        self.retries = retries

    def get(self, path: str) -> Any:
        url = path if path.startswith("https://") else f"{API_ROOT}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "player-profile-os",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        for attempt in range(self.retries + 1):
            request = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=25) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                if attempt < self.retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                status = getattr(exc, "code", "network")
                raise GitHubAPIError(f"GitHub API request failed ({status}): {url}") from exc
        raise AssertionError("unreachable")

    def get_pages(self, path: str, *, max_pages: int = 10) -> list[dict[str, Any]]:
        separator = "&" if "?" in path else "?"
        items: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            batch = self.get(f"{path}{separator}per_page=100&page={page}")
            if not isinstance(batch, list):
                raise GitHubAPIError(f"Expected a list response from {path}")
            items.extend(batch)
            if len(batch) < 100:
                break
        return items


def _parse_github_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _event_to_log(event: dict[str, Any]) -> dict[str, str] | None:
    event_type = event.get("type")
    payload = event.get("payload") or {}
    repository = (event.get("repo") or {}).get("name", "").split("/")[-1]
    created_at = event.get("created_at")
    if not repository or not created_at:
        return None

    if event_type == "ReleaseEvent" and payload.get("action") == "published":
        release = payload.get("release") or {}
        version = release.get("name") or release.get("tag_name") or "a release"
        kind = "RELEASE"
        summary = f"Published {version} in {repository}"
    elif event_type == "PullRequestEvent" and payload.get("action") == "closed":
        pull = payload.get("pull_request") or {}
        if not pull.get("merged_at"):
            return None
        number = payload.get("number") or pull.get("number")
        kind = "MERGE"
        summary = f"Merged PR #{number} in {repository}"
    elif event_type == "PushEvent":
        commit_count = payload.get("size")
        if commit_count is None:
            commit_count = len(payload.get("commits") or [])
        if not commit_count:
            return None
        noun = "commit" if commit_count == 1 else "commits"
        kind = "PUSH"
        summary = f"Pushed {commit_count} {noun} to {repository}"
    else:
        return None

    return {
        "date": created_at[:10],
        "kind": kind,
        "repository": repository,
        "summary": summary,
    }


def _build_ship_log(events: list[dict[str, Any]], username: str) -> list[dict[str, str]]:
    preferred: list[dict[str, str]] = []
    profile_repo_events: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for event in events:
        item = _event_to_log(event)
        if not item:
            continue
        key = (item["kind"], item["repository"])
        if key in seen:
            continue
        seen.add(key)
        target = profile_repo_events if item["repository"] == username else preferred
        target.append(item)

    return (preferred + profile_repo_events)[:5]


def _commit_search_log(items: list[dict[str, Any]], username: str) -> list[dict[str, str]]:
    """Convert indexed public commits into factual fallback patch notes."""

    preferred: list[dict[str, str]] = []
    repeat_repository_items: list[dict[str, str]] = []
    profile_repo_items: list[dict[str, str]] = []
    seen_repositories: set[str] = set()
    seen_commits: set[tuple[str, str, str]] = set()
    noisy_prefixes = ("bump ", "build(deps)", "chore(deps)")
    for item in items:
        repository = (item.get("repository") or {}).get("name")
        is_private = bool((item.get("repository") or {}).get("private"))
        commit = item.get("commit") or {}
        message = str(commit.get("message") or "").splitlines()[0].strip()
        created_at = (commit.get("committer") or {}).get("date")
        author_login = (item.get("author") or {}).get("login", "")
        if (
            not repository
            or is_private
            or not message
            or not created_at
            or author_login.endswith("[bot]")
            or message.lower().startswith(noisy_prefixes)
        ):
            continue
        commit_key = (repository, created_at, message)
        if commit_key in seen_commits:
            continue
        seen_commits.add(commit_key)
        entry = {
            "date": created_at[:10],
            "kind": "COMMIT",
            "repository": repository,
            "summary": f"{repository}: {message}",
        }
        if repository == username:
            target = profile_repo_items
        elif repository in seen_repositories:
            target = repeat_repository_items
        else:
            target = preferred
            seen_repositories.add(repository)
        target.append(entry)
    return preferred + repeat_repository_items + profile_repo_items


def _repository_activity_log(
    repos: list[dict[str, Any]], username: str, cutoff: datetime
) -> list[dict[str, str]]:
    """Build factual fallbacks from public repository push timestamps."""

    entries: list[dict[str, str]] = []
    for repo in repos:
        pushed_at = repo.get("pushed_at")
        if not pushed_at or _parse_github_time(pushed_at) < cutoff:
            continue
        name = repo["name"]
        entries.append(
            {
                "date": pushed_at[:10],
                "kind": "WORLD",
                "repository": name,
                "summary": f"Public repository activity in {name}",
            }
        )
    entries.sort(key=lambda item: item["date"], reverse=True)
    return [item for item in entries if item["repository"] != username] + [
        item for item in entries if item["repository"] == username
    ]


def fetch_profile_data(
    username: str,
    token: str | None = None,
    *,
    now: datetime | None = None,
    preferred_repositories: set[str] | None = None,
) -> dict[str, Any]:
    """Fetch the public telemetry rendered by the Player Save and Ship Log."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    client = GitHubClient(token)

    quoted_user = urllib.parse.quote(username, safe="")
    repos = client.get_pages(
        f"/users/{quoted_user}/repos?type=owner&sort=pushed&direction=desc"
    )
    source_repos = [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and int(repo.get("size", 0)) > 0
    ]

    commit_cutoff = now - timedelta(days=30)
    activity_cutoff = now - timedelta(days=90)
    active_cutoff = now - timedelta(days=180)
    active_repositories = sum(
        1
        for repo in source_repos
        if repo.get("pushed_at") and _parse_github_time(repo["pushed_at"]) >= active_cutoff
    )

    release_count = 0
    commits_30d = 0
    recent_public_commits: list[dict[str, Any]] = []
    for repo in source_repos:
        name = urllib.parse.quote(repo["name"], safe="")
        releases = client.get(f"/repos/{quoted_user}/{name}/releases?per_page=100")
        if not isinstance(releases, list):
            raise GitHubAPIError(f"Expected releases list for {repo['name']}")
        release_count += len(releases)

        commit_params = urllib.parse.urlencode(
            {
                "author": username,
                "since": activity_cutoff.isoformat(timespec="seconds"),
            }
        )
        commits = client.get_pages(
            f"/repos/{quoted_user}/{name}/commits?{commit_params}", max_pages=10
        )
        for commit in commits:
            committed_at = ((commit.get("commit") or {}).get("committer") or {}).get("date")
            if not committed_at:
                continue
            if _parse_github_time(committed_at) >= commit_cutoff:
                commits_30d += 1
            normalized = dict(commit)
            normalized["repository"] = {
                "name": repo["name"],
                "private": False,
            }
            recent_public_commits.append(normalized)

    language_counts = Counter(
        repo["language"] for repo in source_repos if repo.get("language")
    )
    top_language = language_counts.most_common(1)[0][0] if language_counts else "N/A"
    events = client.get(f"/users/{quoted_user}/events/public?per_page=100")
    if not isinstance(events, list):
        raise GitHubAPIError("Expected a public events list")

    ship_by_repository: dict[str, dict[str, str]] = {}
    for entry in _build_ship_log(events, username):
        ship_by_repository.setdefault(entry["repository"], entry)
    recent_public_commits.sort(
        key=lambda item: ((item.get("commit") or {}).get("committer") or {}).get("date", ""),
        reverse=True,
    )
    profile_fallbacks: list[dict[str, str]] = []
    for entry in _commit_search_log(recent_public_commits, username):
        if entry["repository"] == username:
            profile_fallbacks.append(entry)
        else:
            ship_by_repository.setdefault(entry["repository"], entry)
    for entry in _repository_activity_log(source_repos, username, now - timedelta(days=365)):
        if entry["repository"] == username:
            profile_fallbacks.append(entry)
        else:
            ship_by_repository.setdefault(entry["repository"], entry)
    if len(ship_by_repository) < 5 and profile_fallbacks:
        ship_by_repository.setdefault(username, profile_fallbacks[0])
    preferred_repositories = preferred_repositories or set()
    ordered_entries = sorted(
        ship_by_repository.values(), key=lambda entry: entry["date"], reverse=True
    )
    selected_entries = [
        entry for entry in ordered_entries if entry["repository"] in preferred_repositories
    ] + [entry for entry in ordered_entries if entry["repository"] not in preferred_repositories]
    ship_log = sorted(selected_entries[:5], key=lambda entry: entry["date"], reverse=True)

    return {
        "username": username,
        "public_repositories": len(source_repos),
        "commits_30d": commits_30d,
        "active_repositories_180d": active_repositories,
        "releases": release_count,
        "stars_received": sum(int(repo.get("stargazers_count", 0)) for repo in source_repos),
        "top_language": top_language,
        "generated_at": now.isoformat(timespec="seconds"),
        "ship_log": ship_log,
    }
