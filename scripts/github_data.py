"""Bounded GitHub REST client for evidence-backed public profile telemetry."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from activity import ActivityItem, is_bot, is_noise, meaningful_activity, parse_timestamp


API_ROOT = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """Raised when GitHub data cannot be read safely."""


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


def _repo_snapshot(repo: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(repo.get("name") or ""),
        "pushed_at": repo.get("pushed_at"),
        "language": repo.get("language"),
        "html_url": repo.get("html_url"),
        "default_branch": repo.get("default_branch"),
        "archived": bool(repo.get("archived")),
        "fork": bool(repo.get("fork")),
    }


def _event_activity(event: dict[str, Any], username: str) -> ActivityItem | None:
    actor = str((event.get("actor") or {}).get("login") or "")
    if is_bot(actor):
        return None
    repository = str((event.get("repo") or {}).get("name") or "").split("/")[-1]
    timestamp = event.get("created_at")
    if not repository or repository.casefold() == username.casefold() or not timestamp:
        return None
    payload = event.get("payload") or {}
    event_type = event.get("type")
    url = f"https://github.com/{username}/{urllib.parse.quote(repository, safe='')}"

    if event_type == "PushEvent":
        count = int(payload.get("size") or len(payload.get("commits") or []))
        if count < 1:
            return None
        branch = str(payload.get("ref") or "").removeprefix("refs/heads/")
        summary = f"Pushed {count} {'commit' if count == 1 else 'commits'}"
        return ActivityItem("PUSH", repository, timestamp, summary, url, branch, count)
    if event_type == "PullRequestEvent" and payload.get("action") == "closed":
        pull = payload.get("pull_request") or {}
        if not pull.get("merged_at"):
            return None
        number = payload.get("number") or pull.get("number")
        return ActivityItem("MERGE", repository, timestamp, f"Merged PR #{number}", str(pull.get("html_url") or url))
    return None


def _commit_activity(commit: dict[str, Any], repository: str) -> ActivityItem | None:
    detail = commit.get("commit") or {}
    message = str(detail.get("message") or "").splitlines()[0].strip()
    timestamp = (detail.get("committer") or {}).get("date") or (detail.get("author") or {}).get("date")
    author = str((commit.get("author") or {}).get("login") or "")
    committer = str((commit.get("committer") or {}).get("login") or "")
    if not message or not timestamp or is_noise(message) or is_bot(author) or is_bot(committer):
        return None
    return ActivityItem("COMMIT", repository, timestamp, message, str(commit.get("html_url") or ""))


def fetch_profile_data(
    username: str,
    token: str | None = None,
    *,
    now: datetime | None = None,
    preferred_repositories: set[str] | None = None,
) -> dict[str, Any]:
    """Fetch bounded public telemetry; any failure aborts before asset writes."""

    del preferred_repositories  # Retained for CLI compatibility; ordering is now data-only.
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    client = GitHubClient(token)
    quoted_user = urllib.parse.quote(username, safe="")
    repos = client.get_pages(f"/users/{quoted_user}/repos?type=owner&sort=pushed&direction=desc")
    source_repos = [
        repo
        for repo in repos
        if str(repo.get("name") or "").casefold() != username.casefold()
        and not repo.get("fork")
        and not repo.get("archived")
        and int(repo.get("size", 0)) > 0
    ]

    activity_cutoff = now - timedelta(days=365)
    commits_30d = 0
    releases: list[dict[str, Any]] = []
    activity: list[ActivityItem] = []
    for repo in source_repos:
        repo_name = str(repo["name"])
        quoted_repo = urllib.parse.quote(repo_name, safe="")
        repo_releases = client.get(f"/repos/{quoted_user}/{quoted_repo}/releases?per_page=20")
        if not isinstance(repo_releases, list):
            raise GitHubAPIError(f"Expected releases list for {repo_name}")
        for release in repo_releases:
            published_at = release.get("published_at")
            if not published_at or release.get("draft"):
                continue
            item = {
                "repository": repo_name,
                "name": str(release.get("name") or release.get("tag_name") or "Release"),
                "tag": str(release.get("tag_name") or ""),
                "published_at": published_at,
                "url": str(release.get("html_url") or ""),
            }
            releases.append(item)
            activity.append(ActivityItem("RELEASE", repo_name, published_at, f"Published {item['name']}", item["url"]))

        params = urllib.parse.urlencode({"author": username, "since": activity_cutoff.isoformat(timespec="seconds")})
        repo_commits = client.get_pages(f"/repos/{quoted_user}/{quoted_repo}/commits?{params}", max_pages=2)
        for commit in repo_commits:
            item = _commit_activity(commit, repo_name)
            if not item:
                continue
            activity.append(item)
            if parse_timestamp(item.timestamp) >= now - timedelta(days=30):
                commits_30d += 1

    events = client.get(f"/users/{quoted_user}/events/public?per_page=100")
    if not isinstance(events, list):
        raise GitHubAPIError("Expected a public events list")
    for event in events:
        item = _event_activity(event, username)
        if item:
            activity.append(item)

    normalized = meaningful_activity(activity, username=username)
    releases.sort(key=lambda item: (-parse_timestamp(item["published_at"]).timestamp(), item["repository"].casefold()))
    repository_snapshots = [_repo_snapshot(repo) for repo in source_repos]
    repository_snapshots.sort(
        key=lambda repo: (
            -parse_timestamp(repo["pushed_at"]).timestamp() if repo.get("pushed_at") else 0,
            repo["name"].casefold(),
        )
    )
    ship_log = [
        {
            "date": item.timestamp[:10],
            "kind": item.kind,
            "repository": item.repository,
            "summary": f"{item.repository}: {item.summary}",
        }
        for item in normalized[:5]
    ]
    active_cutoff = now - timedelta(days=180)
    language_counts = Counter(repo["language"] for repo in source_repos if repo.get("language"))
    return {
        "username": username,
        "public_repositories": len(source_repos),
        "commits_30d": commits_30d,
        "active_repositories_180d": sum(
            1 for repo in source_repos if repo.get("pushed_at") and parse_timestamp(repo["pushed_at"]) >= active_cutoff
        ),
        "releases": len(releases),
        "stars_received": sum(int(repo.get("stargazers_count", 0)) for repo in source_repos),
        "top_language": language_counts.most_common(1)[0][0] if language_counts else "N/A",
        "generated_at": now.isoformat(timespec="seconds"),
        "repositories": repository_snapshots,
        "activity": [item.as_dict() for item in normalized],
        "release_feed": releases,
        "ship_log": ship_log,
    }
