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
        self.assertGreaterEqual(validate(), 17)

    def test_exports_match_the_art_source(self):
        """Committed exports must be rebuilt whenever tools/pixelart/art.py changes."""
        for sub, a in art.catalogue():
            name = f"{a.name}-still.png" if a.frames > 1 else f"{a.name}.png"
            exported = Image.open(ART / sub / name)
            expected = a.composite(0).resize((a.w * a.scale, a.h * a.scale), Image.NEAREST)
            self.assertTrue(same(exported, expected), f"{sub}/{name} is stale: run tools/pixelart/build.py")

    def test_animations_loop_seamlessly(self):
        for sub, a in art.catalogue():
            if a.frames < 2:
                continue
            gif = Image.open(ART / sub / f"{a.name}.gif")
            self.assertEqual(gif.n_frames, a.frames)
            first = [f.convert("RGB") for f in ImageSequence.Iterator(gif)]
            # consecutive frames differ (it animates) but never flash: < 6% of pixels change per frame
            for i in range(len(first)):
                diff = ImageChops.difference(first[i], first[(i + 1) % len(first)]).convert("L")
                changed = sum(1 for v in diff.getdata() if v) / (diff.width * diff.height)
                self.assertGreater(changed, 0, f"{a.name}: frame {i} identical to next")
                self.assertLess(changed, 0.06, f"{a.name}: frame {i} changes {changed:.1%} of pixels")

    def test_pixel_art_uses_a_limited_palette(self):
        for sub, a in art.catalogue():
            colours = set()
            for f in range(a.frames):
                colours |= {c for _, c in a.composite(f).getcolors(1 << 16) if c[3]}
            self.assertLessEqual(len(colours), 64, f"{a.name} uses {len(colours)} colours")

    def test_font_glyphs_are_5x7(self):
        for ch, glyph in art.FONT.items():
            self.assertEqual(len(glyph), 35, ch)


if __name__ == "__main__":
    unittest.main()
