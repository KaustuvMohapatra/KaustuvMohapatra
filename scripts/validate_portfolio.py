"""Preflight checks for the pixel-art profile README and its artwork (offline, stdlib + Pillow).

    python scripts/validate_portfolio.py           # offline checks (what CI runs)
    python scripts/validate_portfolio.py --links   # also check external links over the network
"""
from pathlib import Path
import re
import sys
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets" / "pixel-art"
EXPORT_DIRS = ["hero", "chapters", "projects", "icons", "animations"]
# byte budgets: GitHub documents no GIF limit, these are our own load-time budgets
GIF_BUDGET = {"hero.gif": 1_500_000}
DEFAULT_GIF_BUDGET = 300_000
TOTAL_BUDGET = 3_000_000

REQUIRED_TEXT = [
    "Game Developer · AI/ML Engineer · Creative Technologist",
    "## The Wizard's Dossier", "## Featured Creations", "## The Spellbook of Skills",
    "## The Adventure Log", "## Send an Owl",
    "### EchoSim", "### Arena Survivor", "### RELOAD", "### Medieval Hauler",
    "VIT Vellore", "unofficial fan tribute",
    "https://github.com/KaustuvMohapatra/EchosSim", "https://kaustuvm.itch.io/arena-survivor",
    "https://kaustuvmohapatra.github.io/ResumeSite/", "https://www.linkedin.com/in/kaustuv-mohapatra-b0538428b/",
    "mailto:kaustuv4@outlook.com",
]
# retired design, removed projects, and anything that must stay private
FORBIDDEN_TEXT = ["aurora", "ascii-portrait", "skillicons.dev", "assets/generated", "TypeMaker",
                  "typemaker-pro", "RIFT"]
UNSUPPORTED_HTML = ["<script", "<style", "<iframe", "<link", "onclick=", "onload="]


def exports():
    return sorted(p for d in EXPORT_DIRS for p in (ART / d).glob("*") if p.suffix in {".png", ".gif"})


def validate(check_links=False):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    errors = []

    for text in REQUIRED_TEXT:
        if text not in readme:
            errors.append("README missing: " + text)
    for text in FORBIDDEN_TEXT:
        if text in readme:
            errors.append("README contains retired/private content: " + text)
    for tag in UNSUPPORTED_HTML:
        if tag in readme.lower():
            errors.append("GitHub strips this HTML, do not rely on it: " + tag)

    refs = re.findall(r'(?:src|srcset)="(\./[^"]+)"', readme)
    for ref in refs:
        if not (ROOT / ref).is_file():
            errors.append("Broken local image: " + ref)

    for tag in re.findall(r"<img\b[^>]*>", readme, flags=re.S | re.I):
        alt = re.search(r'alt="([^"]*)"', tag)
        if alt is None:
            errors.append("Image lacks alt attribute: " + tag[:80])
        elif alt.group(1) == "" and "/icons/" not in tag:
            errors.append("Only heading icons may be decorative (alt=\"\"): " + tag[:80])
        # pixel art must be shown at its exported width (or full width) so pixels stay square
        src = re.search(r'src="(\./[^"]+)"', tag)
        width = re.search(r'width="(\d+)"', tag)
        if src and width and (ROOT / src.group(1)).is_file():
            with Image.open(ROOT / src.group(1)) as probe:
                natural = probe.width
            shown = int(width.group(1))
            if natural % shown:
                errors.append(f"{src.group(1)} shown at {shown}px, not an integer fraction of {natural}px")

    total = 0
    referenced = {Path(r).name for r in refs}
    for path in exports():
        rel = path.relative_to(ROOT).as_posix()
        total += path.stat().st_size
        try:
            with Image.open(path) as probe:
                probe.verify()
            with Image.open(path) as probe:
                probe.load()
                im = probe.copy()
                im.info = dict(probe.info, n_frames=getattr(probe, "n_frames", 1))
        except Exception as exc:  # noqa: BLE001 - any decode failure is a validation failure
            errors.append(f"Cannot decode {rel}: {exc}")
            continue
        if path.name not in referenced:
            errors.append("Exported asset not used by README: " + rel)
        stem = path.stem.removesuffix("-still")
        if not (ART / "source" / f"{stem}.aseprite").is_file():
            errors.append("No editable Aseprite source for " + rel)
        if path.suffix == ".gif":
            if im.info["n_frames"] < 2 or im.info.get("loop") != 0:
                errors.append("GIF must be animated and loop forever: " + rel)
            if path.stat().st_size > GIF_BUDGET.get(path.name, DEFAULT_GIF_BUDGET):
                errors.append(f"GIF over budget ({path.stat().st_size} bytes): {rel}")
        if im.width > 1000:
            errors.append(f"Image wider than needed ({im.width}px): {rel}")
    if total > TOTAL_BUDGET:
        errors.append(f"Artwork total {total} bytes exceeds {TOTAL_BUDGET}")

    for photo in ROOT.rglob("*"):
        if photo.suffix.lower() in {".jpg", ".jpeg", ".heic", ".webp"} and ".git" not in photo.parts:
            errors.append("Photographs must not be committed: " + photo.relative_to(ROOT).as_posix())

    if check_links:
        for url in sorted(set(re.findall(r'\((https://[^)\s]+)\)', readme))):
            if "linkedin.com" in url:
                continue  # LinkedIn rejects automated requests
            try:
                req = urllib.request.Request(url, method="GET", headers={"User-Agent": "profile-link-check"})
                urllib.request.urlopen(req, timeout=20)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Link failed: {url} ({exc})")

    if errors:
        raise ValueError("\n  ".join(["Portfolio validation failed:"] + errors))
    return len(exports())


if __name__ == "__main__":
    try:
        n = validate(check_links="--links" in sys.argv)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print(f"Portfolio validation passed: README and {n} pixel-art exports verified.")
