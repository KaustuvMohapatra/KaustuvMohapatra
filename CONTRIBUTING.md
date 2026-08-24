# Maintaining Player Profile OS

The public `README.md` is presentation-focused. Profile content and positioning live in `profile/`; generated SVGs live in `assets/generated/`.

## Add or reorder a featured world

Edit `profile/projects.yml`. Every project needs a unique kebab-case `id`, honest project metadata, a valid GitHub URL, and a demo URL only when a public build exists. Keep 3–5 projects marked `featured: true`; list order is World Select order.

Publication is explicit and never guessed from a homepage field:

```yaml
published:
  type: web # one of: none, itch, web, download
  url: https://verified-public-build.example/
lifecycle: active-development # active-development, prototype, or archived
```

The visible state is restricted to `PLAYABLE`, `RELEASED`, `ACTIVE DEVELOPMENT`, `PROTOTYPE`, or `ARCHIVED`. `PLAYABLE` requires a configured publication URL; `RELEASED` requires a factual GitHub release.

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
- `assets/generated/now-playing.svg`
- `assets/generated/live-feed.svg`
- `assets/generated/activity-radar.svg`
- `assets/generated/release-radar.svg`
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
- **Update Player Save** runs hourly at minute 17, manually, after profile/generator changes on `main`, or when it receives a `profile-telemetry` repository dispatch. It uses the built-in GitHub Actions token, commits only changed generated output, cancels superseded telemetry runs, and fetches before atomically replacing good assets.
- **Generate Contribution Snake** runs daily or manually and commits only changed light/dark snake SVGs.
- Dependabot checks GitHub Action references monthly.

No repository secret is required. The workflows use the built-in `GITHUB_TOKEN` with explicit least-privilege permissions. GitHub Metrics and WakaTime are not configured; add either only when it provides distinct value and can fail independently of the core profile.

### Optional cross-repository refresh

GitHub cannot make a push in another repository directly trigger this profile repository with that repository's built-in token. The hourly poll is the default and needs no extra setup. For near-immediate refreshes, a source repository may call the profile repository's `repository_dispatch` endpoint with event type `profile-telemetry`. That optional source workflow needs a fine-grained token limited to this profile repository with **Contents: write** (the permission in [GitHub's repository dispatch documentation](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)), stored as a source-repository secret. No source repositories are modified by this profile.

## Live activity rules

`scripts/activity.py` is the normalized activity boundary. It excludes the profile repository, bots, dependency updates, formatting-only noise, forks, archives, and empty repositories before rendering.

Now Playing selects the newest meaningful public signal and falls back to a repository's factual `pushed_at` timestamp. Branch is shown only when GitHub exposes it in a public push event. Recency state is timestamp-only:

```text
< 24 hours  SHIPPING
< 3 days    BUILDING
< 7 days    ACTIVE
otherwise   IDLE
```

Hot World uses work signals from the last 30 days, never stars:

```text
activity score = commits × 1 + push signal × 2 + merged PR × 3 + release × 5
```

Release Radar labels a release `NEW DROP` for seven days after publication and `LATEST DROP` afterward. Every live SVG carries an absolute UTC last-sync timestamp; relative labels are computed from that same timestamp.

## Local validation

```bash
python scripts/generate_profile.py --fixture tests/fixtures/github.json --output-dir .profile-ci/generated --no-readme
python -m unittest discover -s tests -v
python scripts/validate_profile.py --generated-dir .profile-ci/generated
git diff --check
```

For a live refresh, omit `--fixture`. If GitHub cannot be reached, generation exits without replacing the last known-good SVGs.
