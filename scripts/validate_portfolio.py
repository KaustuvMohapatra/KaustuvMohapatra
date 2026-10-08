"""Check the curated public profile and its self-hosted artwork."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    "assets/hero/aurora-dark.svg", "assets/hero/aurora-light.svg",
    "assets/portrait/ascii-portrait.svg",
    "assets/projects/echosim.svg",
    "assets/projects/arena-survivor.svg",
    "assets/projects/ai-game-asset-maker.svg",
]
OBSOLETE = ["PLAYER XP", "WORLD SELECT", "LIVE TELEMETRY", "DEV DNA",
            "EXPERIMENTAL LAB", "CURRENT ACTIVITY", "SHIP LOG", "NOW PLAYING"]

def validate():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for text in ["Hello, I'm Kaustuv", "Selected work", "Technologies & creative tools",
                 "Beyond the code", "EchoSim", "Arena Survivor", "AI Game Asset Maker"]:
        if text not in readme:
            raise ValueError("Missing profile content: " + text)
    for text in OBSOLETE:
        if text in readme.upper():
            raise ValueError("Old profile UI remains: " + text)
    for relative in ASSETS:
        svg = ROOT / relative
        if not svg.is_file() or svg.stat().st_size < 400:
            raise ValueError("Missing/empty asset: " + relative)
        tree = ET.parse(svg)
        if tree.getroot().tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError("Invalid SVG: " + relative)
        if tree.getroot().find("{http://www.w3.org/2000/svg}title") is None:
            raise ValueError("SVG lacks accessible title: " + relative)
        if relative not in readme:
            raise ValueError("Unreferenced asset: " + relative)
    for ref in re.findall(r'(?:src|srcset)="([^"]+)"', readme):
        if ref.startswith("./") and not (ROOT / ref).is_file():
            raise ValueError("Broken local README asset: " + ref)
    for tag in re.findall(r"<img\\b[^>]*>", readme, flags=re.S | re.I):
        if "alt=" not in tag:
            raise ValueError("Image lacks alt text")
    if (ROOT / "assets/portrait/portrait-source.jpg").exists():
        raise ValueError("Original personal photograph must not be committed")
    print("Portfolio profile validation passed; 6 SVG assets and README verified.")

if __name__ == "__main__":
    try:
        validate()
    except (ValueError, ET.ParseError) as exc:
        print("Portfolio profile validation failed:", exc, file=sys.stderr)
        sys.exit(1)
