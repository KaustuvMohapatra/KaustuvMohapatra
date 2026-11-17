"""Build the profile's artwork.

    python tools/pixelart/build.py                 # Aseprite: layered .aseprite sources + PNG/GIF exports
    python tools/pixelart/build.py --preview DIR   # Pillow-only previews (no Aseprite needed)

Aseprite path: $ASEPRITE, else E:/Aseprite/aseprite.exe, else `aseprite` on PATH.
Fonts: the display faces in art.FONT_FILES (Windows/Office fonts); set PROFILE_FONT_DIR if elsewhere.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import art  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets' / 'pixel-art'


def find_aseprite():
    for c in (os.environ.get('ASEPRITE'), 'E:/Aseprite/aseprite.exe', shutil.which('aseprite')):
        if c and Path(c).exists():
            return c
    sys.exit('Aseprite not found: set ASEPRITE=/path/to/aseprite (or use --preview)')


def limit_palette(a):
    """GIFs hold 256 colours. Typography adds antialiased edge colours, so map every layer of an animated
    asset onto one shared 255-colour palette (no dithering). Layers keep binary alpha, so the composite of
    the mapped layers uses only palette colours and Aseprite's GIF export is lossless."""
    strip = Image.new('RGB', (a.w, a.h * a.frames))
    for f in range(a.frames): strip.paste(a.composite(f).convert('RGB'), (0, f * a.h))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    for name in a.order:
        for i, layer in enumerate(a.layers[name]):
            out = layer.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE).convert('RGBA')
            out.putalpha(layer.getchannel('A'))
            a.layers[name][i] = out


def preview(dest):
    dest.mkdir(parents=True, exist_ok=True)
    for sub, a in art.catalogue():
        frames = [a.composite(f) for f in range(a.frames)]
        frames[0].save(dest / f'{a.name}.png')
        if a.frames > 1:
            frames[0].save(dest / f'{a.name}.gif', save_all=True, append_images=frames[1:],
                           duration=a.duration_ms, loop=0, disposal=2)
    print('previews written to', dest)


def build():
    if not art.fonts_available():
        sys.exit(f'Display fonts missing from {art.FONT_DIR}: {sorted(art.FONT_FILES.values())}')
    ase = find_aseprite()
    lua = Path(__file__).with_name('assemble.lua')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for sub, a in art.catalogue():
            if a.frames > 1:
                limit_palette(a)
            stage = tmp / a.name; stage.mkdir()
            for li, name in enumerate(a.order):
                for f, im in enumerate(a.layers[name]):
                    im.save(stage / f'{li:02d}-{f:02d}.png')
            # Lua reads a tiny key=value file because this Aseprite build has no JSON module
            (stage / 'manifest.txt').write_text(
                f"w={a.w}\nh={a.h}\nframes={a.frames}\nduration={a.duration_ms / 1000}\n" +
                ''.join(f"layer={n}\n" for n in a.order))
            src = OUT / 'source' / f'{a.name}.aseprite'
            src.parent.mkdir(parents=True, exist_ok=True)
            (OUT / sub).mkdir(parents=True, exist_ok=True)
            subprocess.run([ase, '-b', '--script-param', f'dir={stage.as_posix()}',
                            '--script-param', f'out={src.as_posix()}', '--script', str(lua)], check=True)
            base = OUT / sub / a.name
            if a.frames > 1:
                subprocess.run([ase, '-b', str(src), '--save-as', f'{base}.gif'], check=True)
                # static first frame, served to prefers-reduced-motion visitors
                subprocess.run([ase, '-b', str(src), '--frame-range', '0,0', '--save-as', f'{base}-still.png'], check=True)
            else:
                subprocess.run([ase, '-b', str(src), '--save-as', f'{base}.png'], check=True)
            print(f'built {sub}/{a.name} ({len(a.order)} layers, {a.frames} frames)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', type=Path)
    args = ap.parse_args()
    preview(args.preview) if args.preview else build()
