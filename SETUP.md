# Pixel-art GitHub profile

This repository powers [Kaustuv's public profile](https://github.com/KaustuvMohapatra).

## Structure
- `README.md`: the profile. Plain Markdown and GitHub-supported HTML only, with no scripts or CSS.
- `assets/pixel-art/`: exported art (`hero/`, `buttons/`, `sections/`, `about/`, `projects/`, `skills/`, `journey/`, `contact/`) and the editable Aseprite files (`source/`).
- `tools/pixelart/`: `art.py` draws every asset, `build.py` builds the sources and exports through Aseprite, and `assemble.lua` is the Aseprite script. Rebuilding needs Aseprite and the display fonts listed in the design guide.
- `scripts/validate_portfolio.py` and `tests/test_portfolio.py`: preflight checks.
- `.github/workflows/profile-ci.yml`: read-only validation on pull requests and pushes to `main`. It has no schedule and makes no API calls.
- `docs/design/`: the design guide, the research and provenance notes, and the concept boards.

## Validate locally
```sh
pip install -r requirements.txt
python scripts/validate_portfolio.py
python -m unittest discover -s tests -p 'test_portfolio.py' -v
```

## Nothing overwrites the README
The old "Player Profile OS" generator, its telemetry scripts and their scheduled workflows were removed in the pixel-art redesign; they remain in Git history. No workflow writes to this repository. The README changes only when someone edits it.

See [docs/design/DESIGN_GUIDE.md](docs/design/DESIGN_GUIDE.md) for the palette, grid, animation rules and how to add a project.
