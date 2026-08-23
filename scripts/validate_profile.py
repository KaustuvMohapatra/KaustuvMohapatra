"""Validate Player Profile OS config, generated assets, README, and workflows."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROJECT_REQUIRED_FIELDS = {
    "id",
    "name",
    "tagline",
    "description",
    "role",
    "status",
    "category",
    "engine",
    "stack",
    "github",
    "featured",
}
REQUIRED_README_SECTIONS = {
    "PLAYER PROFILE // SAVE IDENTITY",
    "MISSION LOG // BUILD PHILOSOPHY",
    "PLAYER SAVE // LIVE TELEMETRY",
    "WORLD SELECT // FEATURED BUILDS",
    "CURRENT QUEST // NOW LOADING",
    "DEV DNA // CURRENT BUILD",
    "TECH TREE // LOADOUT",
    "SHIP LOG // RECENT PATCHES",
    "ACHIEVEMENTS UNLOCKED // VERIFIED",
    "CONTRIBUTION SYSTEM // SNAKE RUN",
    "GAME OVER? // CONTINUE",
}


class ValidationError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValidationError(f"Expected a mapping in {path}")
    return data


def _valid_url(value: str, *, allow_mailto: bool = False) -> bool:
    parsed = urlparse(value)
    if parsed.scheme == "mailto":
        return allow_mailto and "@" in parsed.path
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_projects(projects: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    featured_count = 0
    for index, project in enumerate(projects):
        missing = PROJECT_REQUIRED_FIELDS - project.keys()
        if missing:
            raise ValidationError(f"Project #{index + 1} missing fields: {sorted(missing)}")
        project_id = project["id"]
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_id):
            raise ValidationError(f"Invalid project id: {project_id!r}")
        if project_id in ids:
            raise ValidationError(f"Duplicate project id: {project_id}")
        ids.add(project_id)
        if not _valid_url(project["github"]):
            raise ValidationError(f"Invalid GitHub URL for {project_id}")
        demo = project.get("demo")
        if demo and not _valid_url(demo):
            raise ValidationError(f"Invalid demo URL for {project_id}")
        if not isinstance(project["stack"], list) or not project["stack"]:
            raise ValidationError(f"Project {project_id} needs a non-empty stack")
        featured_count += int(bool(project["featured"]))
    if not 3 <= featured_count <= 5:
        raise ValidationError("World Select must contain 3–5 featured projects")


def validate_profile(profile: dict[str, Any]) -> None:
    for section in (
        "player",
        "mission_log",
        "current_quests",
        "side_quests",
        "dev_dna",
        "tech_tree",
        "achievements",
        "links",
    ):
        if section not in profile:
            raise ValidationError(f"Missing profile section: {section}")
    for item in profile["dev_dna"]:
        value = item.get("value")
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValidationError(f"Dev DNA value must be 0–100: {item}")
    for name, url in profile["links"].items():
        if not _valid_url(url, allow_mailto=name == "email"):
            raise ValidationError(f"Invalid profile link: {name}")
    for achievement in profile["achievements"]:
        if not _valid_url(achievement.get("url", "")):
            raise ValidationError(f"Invalid achievement URL: {achievement.get('label')}")


def validate_svg_directory(directory: Path) -> None:
    expected = {"hero.svg", "player-save.svg", "world-select.svg", "dev-dna.svg", "ship-log.svg"}
    missing = [name for name in sorted(expected) if not (directory / name).is_file()]
    if missing:
        raise ValidationError(f"Missing generated SVGs in {directory}: {missing}")
    for path in directory.glob("*.svg"):
        if path.stat().st_size == 0:
            raise ValidationError(f"Generated SVG is empty: {path}")
        root = ET.parse(path).getroot()
        if not root.tag.endswith("svg"):
            raise ValidationError(f"Generated XML root is not SVG: {path}")
        if path.name in expected and root.find("{http://www.w3.org/2000/svg}title") is None:
            raise ValidationError(f"Generated SVG lacks an accessible title: {path}")


def local_asset_references(readme: str) -> set[str]:
    refs = set(re.findall(r'(?:src|srcset)="([^"\s]+)', readme))
    refs.update(re.findall(r"!\[[^\]]*\]\(([^)\s]+)", readme))
    return {
        ref.split("?", 1)[0].split("#", 1)[0]
        for ref in refs
        if ref.startswith("./") or ref.startswith("assets/")
    }


def validate_readme(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    missing_sections = sorted(section for section in REQUIRED_README_SECTIONS if section not in text)
    if missing_sections:
        raise ValidationError(f"README missing sections: {missing_sections}")
    for marker in ("PLAYER_PROFILE", "WORLD_LINKS", "CURRENT_QUESTS", "TECH_TREE", "ACHIEVEMENTS"):
        if text.count(f"<!-- PLAYER_OS:{marker}:START -->") != 1 or text.count(
            f"<!-- PLAYER_OS:{marker}:END -->"
        ) != 1:
            raise ValidationError(f"README marker pair is invalid: {marker}")
    for reference in sorted(local_asset_references(text)):
        resolved = (ROOT / reference.removeprefix("./")).resolve()
        if ROOT.resolve() not in resolved.parents and resolved != ROOT.resolve():
            raise ValidationError(f"README local asset escapes repository: {reference}")
        if not resolved.is_file():
            raise ValidationError(f"README local asset does not exist: {reference}")
    if re.search(r"<img\b(?![^>]*\balt=)[^>]*>", text, flags=re.IGNORECASE | re.DOTALL):
        raise ValidationError("Every README <img> must have alt text")


def validate_workflows(directory: Path) -> None:
    workflow_paths = sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml"))
    if not workflow_paths:
        raise ValidationError("No GitHub workflows found")
    use_pattern = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s*#\s*(\S+))?", re.MULTILINE)
    for path in workflow_paths:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValidationError(f"Workflow is not a mapping: {path}")
        if not isinstance(data.get("permissions"), dict):
            raise ValidationError(f"Workflow needs explicit permissions: {path}")
        for action, friendly in use_pattern.findall(text):
            if action.startswith("./") or action.startswith("docker://"):
                continue
            if "@" not in action:
                raise ValidationError(f"Action reference lacks a version: {path}: {action}")
            _, revision = action.rsplit("@", 1)
            if not re.fullmatch(r"[0-9a-f]{40}", revision):
                raise ValidationError(f"Action is not pinned to a full SHA: {path}: {action}")
            if not friendly:
                raise ValidationError(f"Pinned action needs a friendly release comment: {path}: {action}")
        for cron in re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", text):
            if len(cron.split()) != 5:
                raise ValidationError(f"Cron must have five fields: {path}: {cron}")


def validate_all(generated_dir: Path) -> None:
    profile = load_yaml(ROOT / "profile" / "profile.yml")
    projects = load_yaml(ROOT / "profile" / "projects.yml").get("projects")
    if not isinstance(projects, list):
        raise ValidationError("profile/projects.yml must contain a projects list")
    validate_profile(profile)
    validate_projects(projects)
    validate_svg_directory(generated_dir)
    validate_readme(ROOT / "README.md")
    validate_workflows(ROOT / ".github" / "workflows")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-dir", type=Path, default=ROOT / "assets" / "generated")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_all(args.generated_dir)
    except (ValidationError, ET.ParseError, yaml.YAMLError) as exc:
        print(f"Profile validation failed: {exc}", file=sys.stderr)
        return 1
    print("Player Profile OS validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
