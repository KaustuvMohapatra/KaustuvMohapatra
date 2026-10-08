# Creative Portfolio — GitHub Profile

This repository powers [Kaustuv's public profile](https://github.com/KaustuvMohapatra).

## Structure

- `README.md`: curated, accessible public profile.
- `assets/hero/`: animated light/dark editorial aurora banners.
- `assets/portrait/`: text-only ASCII SVG derived from a user-supplied photo. **Do not commit the original photo.**
- `assets/projects/`: conceptual original project illustrations; not actual screenshots.
- `scripts/validate_portfolio.py`: preflight checks.
- `tests/test_portfolio.py`: validation tests.
- `.github/workflows/profile-ci.yml`: read-only profile validation.

## Editing

Edit the README and the SVG files directly. Validate with:

```sh
python scripts/validate_portfolio.py
python -m unittest discover -s tests -p 'test_portfolio.py' -v
```

Older telemetry generator, YAML configuration, and pre-redesign tests remain as legacy development history, but are not scheduled to run or required to render the profile. The new curated README is intentionally not overwritten by GitHub telemetry.

## Design provenance

Inspired by techniques documented in [Awesome GitHub Profile](https://github.com/beydemirfurkan/awesome-github-profile) and the [animated ASCII portrait](https://github.com/AVIVASHISHTA29/AVIVASHISHTA29) design. Technology icon references: [Skill Icons](https://github.com/tandpfun/skill-icons) and [Devicon](https://devicon.dev/). Illustration SVGs here are original compositions.

For the next visual pass, replace illustrative project diagrams with real, approved screenshots captured from game builds.
