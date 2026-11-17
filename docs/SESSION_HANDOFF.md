# Session Handoff — KaustuvMohapatra (GitHub profile README)

> Replaced in full each session. Not a conversation log.

**Session ended.** 2026-11-17
**Branch.** `main` @ `ae1574e`

## What changed this session
- Shipped v1 (`aead32d`), which the owner rejected as generic. Replaced it with the v2 Hogwarts-objects redesign (`ae1574e`): new art module, Aseprite build driver, README, validator, tests, docs and previews.
- Portrait redrawn from the owner's reference photo (curly hair, round glasses, short beard) in Slytherin uniform. The photo was not committed.

## Files changed
```
README.md  SETUP.md  docs/design/{DESIGN_GUIDE,RESEARCH}.md  docs/design/previews/*.png
scripts/validate_portfolio.py  tests/test_portfolio.py  tools/pixelart/{art,build}.py
assets/pixel-art/{hero,buttons,sections,about,projects,skills,journey,contact,source}/
```

## Commands and tests run
```
python tools/pixelart/build.py
python scripts/validate_portfolio.py --links
python -m unittest discover -s tests -p 'test_portfolio.py' -v
PROFILE_FONT_DIR=/nonexistent python -m unittest ...   # simulates CI: 1 skip, rest pass
gh api -X POST markdown -f mode=markdown ...           # preview render (mode=markdown, not gfm)
git push origin main                                   # fast-forward aead32d..ae1574e
```

## What passed
- Build (26 assets), validator with link check, 4 unit tests, CI run 44094043731.
- Live profile: v2 hero and all 32 images load, no broken images.

## What remains
- Nothing for v2. Optional: add links for RELOAD / Medieval Hauler once they're public.

## Risks / unresolved questions
- Images keep their filenames across rebuilds, so GitHub's image cache can show the old version for about 5 minutes after a push.
- Preview renders must use `mode=markdown`: `gfm` mode turns newlines into `<br>` and stacks inline images.
- `.preview/` (gitignored) holds local screenshots and preview HTML. It is safe to delete.

## Exact next action
To update a project: edit `PROJECTS` in `tools/pixelart/art.py`, run `python tools/pixelart/build.py`, then run the validator and tests before pushing.
