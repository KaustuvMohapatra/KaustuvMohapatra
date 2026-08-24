# Player Profile OS setup

This profile now owns its important visuals and telemetry instead of depending on a wall of third-party cards.

## First run

```bash
python -m pip install -r requirements.txt
python scripts/generate_profile.py
python -m unittest discover -s tests -v
python scripts/validate_profile.py
```

No repository secret is required. Live telemetry refreshes hourly after merge. Run **Update Player Save** manually for an immediate refresh, and run **Generate Contribution Snake** once if you do not want to wait for its daily schedule.

Maintenance instructions, the XP formula, configuration fields, and workflow behavior are documented in [CONTRIBUTING.md](./CONTRIBUTING.md).
