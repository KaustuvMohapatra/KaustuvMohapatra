from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_profile import calculate_xp, load_yaml  # noqa: E402
from validate_profile import (  # noqa: E402
    ValidationError,
    local_asset_references,
    validate_projects,
    validate_readme,
)


class ProfileGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_yaml(ROOT / "profile" / "profile.yml")
        cls.projects = load_yaml(ROOT / "profile" / "projects.yml")["projects"]
        cls.fixture = json.loads((ROOT / "tests" / "fixtures" / "github.json").read_text(encoding="utf-8"))

    def test_configuration_parses(self) -> None:
        self.assertEqual(self.profile["player"]["handle"], "zeusmonsterx")
        self.assertGreaterEqual(len(self.projects), 3)
        validate_projects(self.projects)

    def test_required_project_fields_and_url_syntax(self) -> None:
        for project in self.projects:
            self.assertTrue(project["github"].startswith("https://github.com/"))
            if project.get("demo"):
                self.assertTrue(project["demo"].startswith("https://"))

    def test_duplicate_project_ids_fail_validation(self) -> None:
        duplicated = deepcopy(self.projects)
        duplicated.append(deepcopy(duplicated[0]))
        with self.assertRaises(ValidationError):
            validate_projects(duplicated)

    def test_xp_calculation_is_deterministic(self) -> None:
        first = calculate_xp(self.fixture)
        second = calculate_xp(deepcopy(self.fixture))
        self.assertEqual(first, second)
        self.assertEqual(first, (3540, 4))

    def test_generator_runs_offline_and_writes_valid_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            output = Path(temp_name) / "generated"
            rendered_readme = Path(temp_name) / "README.md"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "generate_profile.py"),
                    "--fixture",
                    str(ROOT / "tests" / "fixtures" / "github.json"),
                    "--output-dir",
                    str(output),
                    "--readme-output",
                    str(rendered_readme),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            generated = sorted(output.glob("*.svg"))
            self.assertEqual(len(generated), 5)
            for path in generated:
                self.assertGreater(path.stat().st_size, 100)
                self.assertTrue(ET.parse(path).getroot().tag.endswith("svg"))
            self.assertIn("WORLD 01 // ARENA SURVIVOR", rendered_readme.read_text(encoding="utf-8"))

    def test_readme_required_sections_exist(self) -> None:
        validate_readme(ROOT / "README.md")

    def test_readme_local_asset_references_resolve(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        references = local_asset_references(text)
        self.assertGreaterEqual(len(references), 7)
        for reference in references:
            self.assertTrue((ROOT / reference.removeprefix("./")).is_file(), reference)


if __name__ == "__main__":
    unittest.main()

