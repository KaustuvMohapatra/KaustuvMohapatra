# Research & provenance — wizarding pixel-art profile

Status: Concept A approved 2026-11-17; production art lives in `assets/pixel-art/`.

## Brief, as answered
Hogwarts student dossier (1A) as a direct but clearly unofficial fan theme (2A), set in the Great Hall with floating candles (3E), polished modern pixel art (4D). The hero shows a pixel wizard version of Kaustuv casting a spell in a doorway (5D, 7A). Palette: burgundy, gold and charcoal (6B), house Slytherin. Projects shown as spellbook pages (8B), moderate animation (9C), 40/60 portfolio to immersion (10C), ornate headers and dividers (11B). Motifs: enchanted maps and footprints, a golden winged orb, magical creatures (12E/F/G).

## What was researched and what it changed
| Topic | Source | Influence |
|---|---|---|
| Theme-aware images | [GitHub Docs: basic formatting](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax), [GitHub blog: light/dark images](https://github.blog/developer-skills/github/how-to-make-your-images-in-markdown-on-github-adjust-for-dark-mode-and-light-mode/) | `<picture>` + `prefers-color-scheme` and relative image paths are supported. No GIF size limit is documented, so the budget is our own: hero GIF < 1.5 MB, others < 300 KB. |
| Candle and chandelier construction | [itch.io candlestick tutorial](https://itch.io/t/2620307/pixel-tutorial-candlesticks-candelabras-and-chandeliers) | Candles are 1–2 px wide wax plus a 1–2 px flame, and depth is shown by size. Glow uses ordered dither, not alpha. |
| Castle hall palettes | [Summer Engine torch-lit hall listing](https://www.summerengine.com/asset-store/the-torchlit-castle-hub-1291354b) (read as a description, not copied) | Confirmed navy, charcoal and amber as a mood with no anti-aliasing. |
| Palette discipline | [Pixnote colour guide](https://pixnote.net/en/learn/color-palette), [androidarts pixel tutorial](https://www.androidarts.com/pixtut/pixelart.htm), local `pixel-art` skill (hue-shifted ramps, one dither style per piece) | Hue-shifted ramps: cool shadows and warm highlights. One Bayer 4×4 dither style throughout. |

## Originality rules
- All artwork is drawn pixel by pixel from code or in Aseprite. No traced or imported film stills, game sprites, logos, crests or fan art.
- No official Hogwarts or Slytherin crest. House identity uses colour plus an original serpent-wave or serpent-"S" mark.
- Text in the art uses an original 5×7 bitmap font (`tools/pixelart/art.py`), so no third-party font is embedded.
- The README footer will state that this is an unofficial fan tribute with no affiliation to Warner Bros. or J.K. Rowling.

## Tools
- Concept boards (`docs/design/concepts/`): Python and Pillow at a native 288×112 canvas, upscaled ×3 nearest-neighbour.
- Production: `tools/pixelart/art.py` draws the named layers and frames, Aseprite 1.2.21-dev assembles them into `.aseprite` sources (`assemble.lua`), and Aseprite's CLI exports the PNG and GIF files.
