# Player Profile OS setup

This profile now owns its important visuals and telemetry instead of depending on a wall of third-party cards.

## First run

```bash
python -m pip install -r requirements.txt
python scripts/generate_profile.py
python -m unittest discover -s tests -v
python scripts/validate_profile.py
```

No repository secret is required. After the feature branch is merged, run **Generate Contribution Snake** once from the Actions tab if you want an immediate refresh instead of waiting for the daily schedule.

Maintenance instructions, the XP formula, configuration fields, and workflow behavior are documented in [CONTRIBUTING.md](./CONTRIBUTING.md).
