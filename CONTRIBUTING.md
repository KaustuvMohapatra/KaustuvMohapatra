# Maintaining Player Profile OS

The public `README.md` is presentation-focused. Profile content and positioning live in `profile/`; generated SVGs live in `assets/generated/`.

## Add or reorder a featured world

Edit `profile/projects.yml`. Every project needs a unique kebab-case `id`, honest project metadata, a valid GitHub URL, and a demo URL only when a public build exists. Keep 3–5 projects marked `featured: true`; list order is World Select order.

Regenerate after editing:

```bash
python -m pip install -r requirements.txt
python scripts/generate_profile.py
```

## Change Current Quest or Dev DNA

Edit `current_quests`, `side_quests`, or `dev_dna` in `profile/profile.yml`, then run the generator. Dev DNA is a deliberate positioning map, not an inferred or official GitHub statistic.

## Generated files

Do not hand-edit these files:

- `assets/generated/hero.svg`
- `assets/generated/player-save.svg`
- `assets/generated/world-select.svg`
- `assets/generated/dev-dna.svg`
- `assets/generated/ship-log.svg`
- `assets/generated/github-snake.svg`
- `assets/generated/github-snake-dark.svg`

The Python generator also replaces the guarded `PLAYER_OS` blocks in `README.md`. The contribution snake is generated separately by its workflow.

## Player XP

Player XP is explicitly playful and uses this formula from `scripts/generate_profile.py`:

```text
public source repositories × 100
+ public commits in the last 30 days × 5
+ published GitHub releases × 150
+ stars received × 20
```

Level is `floor(XP / 1000) + 1`. The UI labels this as a profile metric, not a GitHub score.

## Automation map

- **Profile CI** validates pull requests, pushes to `main`, and manual runs. It generates from a deterministic fixture and never writes to the repository.
- **Update Player Save** runs daily, manually, and after profile/generator changes on `main`. It uses the built-in GitHub Actions token, commits only changed generated output, and fails before replacing good assets if the API cannot be read.
- **Generate Contribution Snake** runs daily or manually and commits only changed light/dark snake SVGs.
- Dependabot checks GitHub Action references monthly.

No repository secret is required. The workflows use the built-in `GITHUB_TOKEN` with explicit least-privilege permissions. GitHub Metrics and WakaTime are not configured; add either only when it provides distinct value and can fail independently of the core profile.

## Local validation

```bash
python scripts/generate_profile.py --fixture tests/fixtures/github.json --output-dir .profile-ci/generated --no-readme
python -m unittest discover -s tests -v
python scripts/validate_profile.py --generated-dir .profile-ci/generated
git diff --check
```

For a live refresh, omit `--fixture`. If GitHub cannot be reached, generation exits without replacing the last known-good SVGs.
