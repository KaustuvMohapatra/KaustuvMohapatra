# Design guide: the Candlelit Great Hall

A Hogwarts-style student dossier, told as a feast-night spellbook. It's an unofficial fan tribute: no official crests, logos, film stills or third-party sprites are used. Every image is original pixel art (see [RESEARCH.md](RESEARCH.md)).

## Page structure
Hero (animated) → Chapter I: The Wizard's Dossier → Chapter II: Featured Creations (spellbook pages) → Chapter III: The Spellbook of Skills → Chapter IV: The Adventure Log → Finale: Send an Owl.
Everything a visitor needs (name, roles, project names, stacks, links, contact) is real Markdown text. Images only add atmosphere, and they all have alt text.

## Palette (`tools/pixelart/art.py` → `P`)
| Role | Colours |
|---|---|
| Charcoal / outline | `#0d0a0e` `#1a1419` `#2a2027` |
| Warm stone | `#1e1619` → `#86644f` (5-step ramp, hue-shifted warm in highlights) |
| Burgundy (ribbons, banners, wax) | `#3a0f18` `#6b1a28` `#93303a` · wax `#5a141e` `#8c2430` `#c4503e` |
| Antique gold | `#7a4f18` `#b07a24` `#e0aa3e` `#fbe2a0` |
| Enchanted ceiling | `#0b0c1a` → `#262c52` |
| Candlelight | wax `#efe0c0` `#bfa982`, flame `#fff7d0` `#ffbf3c` `#e07a28` |
| Parchment / ink | `#a88a58` → `#f3e6c4`, ink `#3a2414` `#7d5a38` |
| Slytherin (on Kaustuv only) | `#124430` `#1e6b45` `#b8c0c4` |

Slytherin colours appear only on the character (scarf) and his dossier. The scene uses burgundy and gold.

## Pixel grid
- Everything is drawn at 1× and exported with nearest-neighbour scaling. Hero, plates, pages and the owl export at **3×**; the dossier and skill icons at **2×**.
- The README shows each image at exactly its exported width (or `width="100%"` for full-width art) so pixels stay square. The validator enforces this.
- Native sizes: hero 288×112, chapter plates 288×22, project pages 140×52, dossier 124×140, icons 16×16, owl 160×52.
- One dither style: ordered Bayer 4×4. Light falls off with ordered dither, never alpha blending. 1 px dark outlines (`#0d0a0e`).
- Lettering uses an original 5×7 bitmap font (`FONT` in `art.py`), so no font files are embedded.

## Animation
- Hero: 16 frames × 110 ms, seamless loop. Candle flames flicker (each with its own phase), the ceiling stars twinkle, the spell trail flows, the winged orb hovers in a figure-eight, and a glint sweeps the gold title.
- Owl: 8 frames × 140 ms, with a wing-flap cycle and twinkling stars.
- Rules (enforced by tests): no frame changes more than 6% of pixels, so nothing flashes. Hero ≤ 1.5 MB, other GIFs ≤ 300 KB. Each GIF has a `-still.png` that is served to `prefers-reduced-motion` visitors through `<picture>`.

## Building the art
```sh
python tools/pixelart/build.py                  # needs Aseprite (ASEPRITE env var or E:/Aseprite/aseprite.exe)
python tools/pixelart/build.py --preview out/   # Pillow-only previews, no Aseprite
```
`build.py` renders each asset's named layers and frames from `art.py`. It then runs `assemble.lua` in Aseprite to save a layered, animated `.aseprite` file to `assets/pixel-art/source/`, and finally exports the PNG and GIF files with Aseprite's CLI. To make manual edits, change the `.aseprite` file and export with Aseprite. Note that a later `build.py` run regenerates it from code.

## Adding or replacing a featured project
1. Draw a 54×32 vignette function in `art.py` and register it in `VIGNETTES`.
2. Add `(key, TITLE, VOLUME, stamp-or-None)` to `PROJECT_PAGES`. The stamp `BREWING` marks work in progress.
3. Run `build.py`, then add the page image and a `### Name` block (one-line pitch, stack, description, links) to the README.
4. Add the name to `REQUIRED_TEXT` in `scripts/validate_portfolio.py`.

## Validation
```sh
python scripts/validate_portfolio.py            # offline: README structure, images, alt text, budgets, sources
python scripts/validate_portfolio.py --links    # also checks external links
python -m unittest discover -s tests -p 'test_portfolio.py' -v
```
The tests also fail if any committed export no longer matches what `art.py` draws, so rebuild after you change the art.
