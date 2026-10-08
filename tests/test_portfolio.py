import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_portfolio import validate, ASSETS

class PortfolioTests(unittest.TestCase):
    def test_public_readme(self):
        validate()

    def test_all_svg_xml(self):
        for name in ASSETS:
            svg = ET.parse(ROOT / name).getroot()
            self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertIsNotNone(svg.find("{http://www.w3.org/2000/svg}title"))

    def test_portrait_is_derived_not_photo(self):
        svg = (ROOT / "assets/portrait/ascii-portrait.svg").read_text()
        self.assertIn("ASCII portrait of Kaustuv", svg)
        self.assertGreater(svg.count("xml:space=\"preserve\""), 60)
        self.assertNotIn("<image", svg)
        self.assertFalse((ROOT / "assets/portrait/portrait-source.jpg").exists())

    def test_readme_has_relevant_links(self):
        r = (ROOT / "README.md").read_text()
        for link in ["https://github.com/KaustuvMohapatra/EchosSim",
                     "https://kaustuvm.itch.io/arena-survivor",
                     "https://github.com/KaustuvMohapatra/AI-Game-Asset-Maker",
                     "https://skillicons.dev/icons"]:
            self.assertIn(link, r)

if __name__ == "__main__":
    unittest.main()
