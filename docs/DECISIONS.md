# Decision Log — KaustuvMohapatra (GitHub profile README)

Durable decisions only. Newest at the bottom. If a decision is reversed, add a new
entry and mark the old one superseded — never delete history.

Do not record: routine implementation choices, one-off fixes, or anything the code
already makes obvious.

## D1 — Every section is a Hogwarts object, typography included
- **Date.** 2026-11-17
- **Decision.** The README is built from themed images (letter, Daily Prophet, library cards, O.W.L.s, Marauder's Map, owl post, plaque buttons), with lettering set in period display faces inside the art. Plain Markdown text appears only in `<details>` fallbacks and the footer.
- **Reason.** The owner rejected v1 (pixel art around ordinary Markdown headings and "Volume" book pages) as generic.
- **Alternatives rejected.** Themed images around plain Markdown text (v1); a 5×7 bitmap font for all lettering (unreadable at size, looked generic).
- **Consequences.** Content changes need an art rebuild. Accessibility depends on full-content alt text, `<details>` versions and reduced-motion stills; the validator enforces non-empty alt text.
- **Supersedes.** v1 "Candlelit Great Hall" design (commit `aead32d`).

## D2 — Display fonts are rasterised locally and never committed
- **Date.** 2026-11-17
- **Decision.** `art.py` renders text with installed Windows/Office fonts (Old English, Castellar, Goudy Old Style, Monotype Corsiva, Lucida Calligraphy, Bodoni). Only rendered images are committed. The export-match test skips when the fonts are absent, so Linux CI does not run it.
- **Reason.** Font licences don't allow redistribution; the look needs these faces.
- **Alternatives rejected.** Committing font files; open fonts downloaded at build time (adds a dependency and changes the look).
- **Consequences.** Rebuilding art requires a Windows machine with these fonts (or `PROFILE_FONT_DIR`) plus Aseprite. Stale exports are only caught locally.
- **Supersedes.** v1's original 5×7 bitmap font.

## D3 — Content and publishing rules for the profile
- **Date.** 2026-11-17
- **Decision.** Only confirmed facts. TypeMaker and RIFT stay out (validator forbids them). RELOAD and Medieval Hauler are shown as "still brewing" with no links until the owner provides them. The owner's reference photo is used only to draw the portrait and is never committed (validator rejects jpg/jpeg/heic/webp). Publishing is a fast-forward push to `main` after the owner approves a rendered preview; never force-push.
- **Reason.** Owner's brief: no invented facts, private projects stay private, approval before publishing.
- **Alternatives rejected.** PR workflow (owner chose a direct push to `main` after approval).
- **Consequences.** New projects need an owner-confirmed description and link before they're added.
- **Supersedes.** None.

## D4 — The hero uses the owner's own portrait image
- **Date.** 2026-11-17
- **Decision.** The hero frame shows the pixel portrait the owner supplied, committed as `tools/pixelart/portrait-source.png` (418 px PNG) and resampled to the frame's native size by `portrait_image()` in `art.py`. The code-drawn portrait was deleted.
- **Reason.** The owner judged the drawn likeness poor and asked for his image instead.
- **Alternatives rejected.** Keeping or redrawing the code-drawn portrait.
- **Consequences.** The portrait doesn't animate. The image contains a Slytherin-style crest, which the owner accepted; the footer disclaimer still states that the profile is unofficial. To change the likeness, replace the PNG and rebuild.
- **Supersedes.** The drawn-portrait part of D1. D3's "photo never committed" rule still applies to real photographs.
