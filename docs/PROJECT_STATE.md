# Project State — KaustuvMohapatra (GitHub profile README)

> Authoritative current state. Keep it short; replace stale lines rather than appending.

**Current objective.**
A Hogwarts/Slytherin-themed pixel-art GitHub profile (unofficial fan tribute) that still reads as a real portfolio.

**Current sprint / milestone.**
v2 "Hogwarts objects" redesign: shipped and live.

**Active branch.** `main`
**Last verified commit.** `ae1574e` — verified 2026-11-17 (CI green, live profile checked: 32 images, none broken)

## Completed
- v2 layout: gilded-portrait hero, animated plaque buttons, Acceptance Letter (about), Daily Prophet project pages + library cards (Restricted Section), O.W.L. subject cards (skills), animated Marauder's Map (journey), Owl Post (contact).
- Full-content alt text on every image, `-still.png` reduced-motion fallbacks, `<details>` plain-text versions of projects and journey.
- Aseprite pipeline: `tools/pixelart/build.py` → layered `.aseprite` sources in `assets/pixel-art/source/` + PNG/GIF exports.
- Validator, tests, design docs and preview images updated for v2.
- Hero portrait replaced with the owner's own pixel portrait (D4).

## In progress
- Nothing.

## Known failures
- None. Note: GIF frames differ from the art source by ≤ 8 levels on a few pixels (Aseprite's 5-bit GIF colour lookup); tests tolerate this deliberately.

## Test / build / deployment status
| Gate | Command | Status | Last run |
|---|---|---|---|
| Tests | `python scripts/validate_portfolio.py --links` and `python -m unittest discover -s tests -p 'test_portfolio.py'` | Pass (4 tests; export-match test skips without the fonts) | 2026-11-17 |
| Build | `python tools/pixelart/build.py` (needs Aseprite + Windows display fonts) | Pass, 26 assets | 2026-11-17 |
| Deploy | push to `main` (GitHub renders the README); CI `.github/workflows/profile-ci.yml` | Live, CI success (run 44094043731) | 2026-11-17 |

## Immediate next steps
1. When RELOAD or Medieval Hauler get public links, drop `brewing=True` and add `url` in `PROJECTS` (`tools/pixelart/art.py`), rebuild, and link the card in `README.md`.

_Last updated: 2026-11-17_
