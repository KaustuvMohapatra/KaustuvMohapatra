from __future__ import annotations

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from activity import (  # noqa: E402
    ActivityItem,
    current_state,
    meaningful_activity,
    parse_timestamp,
    published_state,
    release_status,
    score_repositories,
    select_now_playing,
)
from generate_profile import (  # noqa: E402
    _write_assets_atomically,
    generate_live,
    load_yaml,
    render_now_playing_svg,
)
from github_data import GitHubAPIError  # noqa: E402


class ActivityModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads((ROOT / "tests" / "fixtures" / "github.json").read_text(encoding="utf-8"))
        cls.projects = load_yaml(ROOT / "profile" / "projects.yml")["projects"]
        cls.now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    def test_profile_repo_and_bots_are_filtered(self) -> None:
        items = [
            ActivityItem("COMMIT", "KaustuvMohapatra", "2026-08-23T10:00:00Z", "Add profile panel"),
            ActivityItem("COMMIT", "world", "2026-08-23T09:00:00Z", "dependabot[bot] bump package"),
            ActivityItem("COMMIT", "world", "2026-08-23T08:00:00Z", "Build boss encounter"),
        ]
        result = meaningful_activity(items, username="KaustuvMohapatra")
        self.assertEqual([item.summary for item in result], ["Build boss encounter"])

    def test_now_playing_selects_newest_meaningful_repository(self) -> None:
        items = [
            ActivityItem("COMMIT", "older", "2026-08-20T08:00:00Z", "Add arena"),
            ActivityItem("COMMIT", "newer", "2026-08-21T08:00:00Z", "Tune movement"),
        ]
        result = select_now_playing(items, [], username="KaustuvMohapatra")
        self.assertIsNotNone(result)
        self.assertEqual(result["repository"], "newer")

    def test_newer_repository_push_outranks_older_commit(self) -> None:
        items = [ActivityItem("COMMIT", "older", "2026-08-20T08:00:00Z", "Add arena")]
        repos = [
            {
                "name": "newer",
                "pushed_at": "2026-08-22T08:00:00Z",
                "html_url": "https://github.com/owner/newer",
                "archived": False,
                "fork": False,
            }
        ]
        result = select_now_playing(items, repos, username="owner")
        self.assertEqual(result["repository"], "newer")
        self.assertEqual(result["summary"], "Latest public repository push")

    def test_release_labels_cover_new_latest_and_none(self) -> None:
        new = {"published_at": "2026-08-18T12:00:00Z"}
        old = {"published_at": "2026-07-01T12:00:00Z"}
        self.assertEqual(release_status(new, now=self.now), "NEW DROP")
        self.assertEqual(release_status(old, now=self.now), "LATEST DROP")
        self.assertEqual(release_status(None, now=self.now), "NO RELEASE")

    def test_zero_activity_has_no_hot_repository(self) -> None:
        self.assertEqual(score_repositories([], [], now=self.now), [])

    def test_activity_sorting_is_deterministic(self) -> None:
        items = [
            ActivityItem("COMMIT", "Zulu", "2026-08-20T08:00:00Z", "Fix Z"),
            ActivityItem("COMMIT", "alpha", "2026-08-20T08:00:00Z", "Fix A"),
        ]
        first = meaningful_activity(items, username="owner")
        second = meaningful_activity(reversed(items), username="owner")
        self.assertEqual(first, second)
        self.assertEqual(first[0].repository, "alpha")

    def test_timestamp_is_converted_to_utc(self) -> None:
        parsed = parse_timestamp("2026-08-23T17:30:00+05:30")
        self.assertEqual(parsed.isoformat(), "2026-08-23T12:00:00+00:00")

    def test_current_state_uses_documented_timestamp_thresholds(self) -> None:
        self.assertEqual(current_state("2026-08-23T00:01:00Z", now=self.now), "SHIPPING")
        self.assertEqual(current_state("2026-08-21T00:01:00Z", now=self.now), "BUILDING")
        self.assertEqual(current_state("2026-08-18T00:01:00Z", now=self.now), "ACTIVE")
        self.assertEqual(current_state("2026-08-01T00:01:00Z", now=self.now), "IDLE")

    def test_publication_state_uses_verified_config(self) -> None:
        self.assertEqual(published_state(self.projects[0], has_release=False), "PLAYABLE")
        self.assertEqual(published_state(self.projects[1], has_release=True), "RELEASED")
        self.assertEqual(published_state(self.projects[1], has_release=False), "ACTIVE DEVELOPMENT")

    def test_svg_escapes_long_unicode_and_markup(self) -> None:
        data = deepcopy(self.fixture)
        data["activity"].insert(
            0,
            {
                "kind": "COMMIT",
                "repository": "<Boss>&世界" * 8,
                "timestamp": "2026-08-23T11:59:00Z",
                "summary": "Fix <script>alert('x')</script> & preserve naïve 日本語" * 5,
                "url": "",
                "branch": "feat/<unsafe>&世界",
                "commits": 1,
            },
        )
        svg = render_now_playing_svg(data, self.projects)
        ET.fromstring(svg)
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;", svg)
        self.assertIn("世界", svg)

    def test_malformed_activity_is_ignored_without_breaking_svg(self) -> None:
        data = deepcopy(self.fixture)
        data["activity"] = [{"kind": "COMMIT", "repository": "bad", "timestamp": "not-a-date", "summary": "Bad"}]
        ET.fromstring(render_now_playing_svg(data, self.projects))

    def test_invalid_svg_never_overwrites_last_known_good_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name) / "generated"
            output.mkdir()
            target = output / "now-playing.svg"
            target.write_text("<svg xmlns='http://www.w3.org/2000/svg'><title>good</title></svg>", encoding="utf-8")
            with self.assertRaises(ET.ParseError):
                _write_assets_atomically(output, {"now-playing.svg": "<svg><broken></svg>"})
            self.assertIn("good", target.read_text(encoding="utf-8"))

    def test_api_failure_does_not_overwrite_assets(self) -> None:
        def failing_fetcher(*args: object, **kwargs: object) -> dict[str, object]:
            raise GitHubAPIError("fixture outage")

        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name) / "generated"
            output.mkdir()
            target = output / "now-playing.svg"
            target.write_text("last-known-good", encoding="utf-8")
            with self.assertRaises(GitHubAPIError):
                generate_live(
                    username="KaustuvMohapatra",
                    token=None,
                    profile_path=ROOT / "profile" / "profile.yml",
                    projects_path=ROOT / "profile" / "projects.yml",
                    output_dir=output,
                    readme_path=None,
                    readme_output=None,
                    fetcher=failing_fetcher,
                )
            self.assertEqual(target.read_text(encoding="utf-8"), "last-known-good")


if __name__ == "__main__":
    unittest.main()
