import sys
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "pixelart"))
import art  # noqa: E402
from validate_portfolio import validate, ART  # noqa: E402


def same(a, b):
    return ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox() is None


class PortfolioTests(unittest.TestCase):
    def test_readme_and_assets_validate(self):
        self.assertGreaterEqual(validate(), 26)

    @unittest.skipUnless(art.fonts_available(), "display fonts not installed (CI runs on Linux)")
    def test_exports_match_the_art_source(self):
        """Committed exports must be rebuilt whenever tools/pixelart/art.py changes."""
        for sub, a in art.catalogue():
            name = f"{a.name}-still.png" if a.frames > 1 else f"{a.name}.png"
            with Image.open(ART / sub / name) as exported:
                self.assertTrue(same(exported, a.composite(0)), f"{sub}/{name} is stale: run tools/pixelart/build.py")

    def test_animations_loop_seamlessly(self):
        for path in sorted(ART.glob("*/*.gif")):
            with Image.open(path) as gif:
                frames = [f.convert("RGB") for f in ImageSequence.Iterator(gif)]
            self.assertGreater(len(frames), 1, path.name)
            # it animates (held frames are fine) but never flashes: < 6% of pixels change per frame
            moved = 0
            for i in range(len(frames)):
                diff = ImageChops.difference(frames[i], frames[(i + 1) % len(frames)]).convert("L")
                # Aseprite's GIF colour lookup rounds to 5 bits per channel, so ignore shifts of <= 8 levels
                changed = sum(diff.histogram()[9:]) / (diff.width * diff.height)
                moved += changed > 0
                self.assertLess(changed, 0.06, f"{path.name}: frame {i} changes {changed:.1%} of pixels")
            self.assertGreater(moved, 1, f"{path.name} barely animates")

    def test_stills_are_the_first_frame(self):
        for path in sorted(ART.glob("*/*.gif")):
            with Image.open(path) as gif, Image.open(path.with_name(path.stem + "-still.png")) as still:
                diff = ImageChops.difference(gif.convert("RGB"), still.convert("RGB")).convert("L")
                # the GIF shares one 255-colour palette, so a few antialiased text pixels may shift slightly
                self.assertLess(sum(diff.histogram()[25:]), 0.001 * diff.width * diff.height, path.name)


if __name__ == "__main__":
    unittest.main()
