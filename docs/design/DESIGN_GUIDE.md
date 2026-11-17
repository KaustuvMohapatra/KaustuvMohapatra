# Design guide: a letter from Hogwarts

An unofficial fan tribute: every section is a Hogwarts object. No official crests, logos, film stills or third-party sprites are used, and all artwork is original (see [RESEARCH.md](RESEARCH.md)).

## Page structure
| Section | Object | What it carries |
|---|---|---|
| Hero | Moonlit castle over the lake, gilded moving portrait | Name, roles, House Slytherin, Kaustuv's likeness in Slytherin robes |
| Buttons | Emerald-and-gold plaques with a play rune and a passing glint | Portfolio, Play games, GitHub, LinkedIn, Owl post (email) |
| The Acceptance Letter | Hogwarts letter on parchment, green wax seal | About: studies, craft, known for, office held, interests |
| The Restricted Section | *Daily Prophet* front pages with moving sepia photos, plus library catalogue cards | Featured projects and the archive |
| Ordinary Wizarding Levels | O.W.L. subject cards | Skills: Transfiguration = gameplay, Divination = AI, Charms = web, Arithmancy = backend, Potions = creative tools |
| The Marauder's Map | Animated map with walking footprints | Journey and experience |
| Owl Post | Owl leaving the owlery | Contact, then the buttons again |

Every image has full-content alt text, and the projects and map have a `<details>` plain-text version, so nothing is image-only.

## Palette (`tools/pixelart/art.py` → `P`)
| Role | Colours |
|---|---|
| Night and castle | navy night ramp, charcoal stone, warm lit windows |
| Slytherin | emerald `em` ramp, silver `sv` |
| Gilding | `g` gold ramp (`GOLD_RAMP` for metal lettering) |
| Paper | parchment `parch`, newsprint `news`, sepia photo ramp `sep` |
| Ink | `ink`, `ink2`, accent red `red`, wax |

## Pixel grid and typography
- Scenery, portrait, props and frames are pixel art drawn at native size and exported at **2×** (each art pixel is a 2×2 block). Native sizes: hero 416×196, banners 416×50, letter 416×222, Prophet pages 202×222, catalogue cards 134×64, subject cards 134×100, map 416×214, owl post 416×104, buttons 82×24.
- Lettering is set at full export resolution in period display faces, so it stays readable: Old English (titles, mastheads), Castellar (engraved caps), Goudy Old Style (body), Monotype Corsiva (script), Lucida Calligraphy (map labels) and Bodoni (headlines). These are Windows/Office fonts, used only to rasterise. They are never committed.
- The README shows images at natural width; GitHub scales them down on narrow screens.

## Animation
- Hero: 12 frames × 130 ms. Window lights flicker, stars twinkle, fireflies drift, the portrait blinks.
- Buttons: 8 × 120 ms glint sweep and pulsing play rune. Prophet photos: 8 × 160 ms. Map: 12 × 150 ms footprints. Owl: 8 × 150 ms.
- Rules (enforced by tests): no frame changes more than 6% of pixels, so nothing flashes. Hero ≤ 1.5 MB, other GIFs ≤ 400 KB, all art ≤ 4 MB. Each GIF has a `-still.png` that is served to `prefers-reduced-motion` visitors through `<picture>`.

## Building the art
```sh
python tools/pixelart/build.py                  # needs Aseprite (ASEPRITE env var or E:/Aseprite/aseprite.exe) and the fonts above
python tools/pixelart/build.py --preview out/   # Pillow-only previews, no Aseprite
```
`build.py` renders each asset's named layers and frames from `art.py`. Animated assets are mapped onto one shared 255-colour palette so the GIF holds every colour. It then runs `assemble.lua` in Aseprite to save a layered, animated `.aseprite` file to `assets/pixel-art/source/`, and exports the PNG and GIF files with Aseprite's CLI. Set `PROFILE_FONT_DIR` if the fonts live outside `C:/Windows/Fonts`.

## Adding or replacing a featured project
1. Write a sepia photo function (`_photo_<key>(cv, x, y, f)`, 120×64 native) in `art.py`.
2. Add a dict to `PROJECTS` (`brewing=True` stamps it "Still brewing").
3. Run `build.py`, then add the card (wrapped in `<picture>` with its still) and a `### Name` block in the plain-text `<details>` of the README.
4. Add the name to `REQUIRED_TEXT` in `scripts/validate_portfolio.py`.

## Validation
```sh
python scripts/validate_portfolio.py            # offline: README structure, images, alt text, budgets, sources
python scripts/validate_portfolio.py --links    # also checks external links
python -m unittest discover -s tests -p 'test_portfolio.py' -v
```
Where the fonts are installed, the tests also fail if a committed export no longer matches what `art.py` draws. CI runs on Linux without them and skips that one check.
