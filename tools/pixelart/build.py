"""Build the profile's pixel art.

    python tools/pixelart/build.py                 # Aseprite: .aseprite sources + 3x exports
    python tools/pixelart/build.py --preview DIR   # Pillow-only 3x previews (no Aseprite needed)

Aseprite path: $ASEPRITE, else E:/Aseprite/aseprite.exe, else `aseprite` on PATH.
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


def save_gif(frames, path, duration, scale):
    """Pillow fallback GIF (used only by --preview)."""
    big = [f.resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    big[0].save(path, save_all=True, append_images=big[1:], duration=duration, loop=0, disposal=2, optimize=False)


def preview(dest):
    dest.mkdir(parents=True, exist_ok=True)
    for sub, a in art.catalogue():
        frames = [a.composite(f) for f in range(a.frames)]
        frames[0].resize((a.w * a.scale, a.h * a.scale), Image.NEAREST).save(dest / f'{a.name}.png')
        if a.frames > 1:
            save_gif(frames, dest / f'{a.name}.gif', a.duration_ms, a.scale)
    print('previews written to', dest)


def build():
    ase = find_aseprite()
    lua = Path(__file__).with_name('assemble.lua')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for sub, a in art.catalogue():
            stage = tmp / a.name; stage.mkdir()
            for li, name in enumerate(a.order):
                for f, im in enumerate(a.layers[name]):
                    im.save(stage / f'{li:02d}-{f:02d}.png')
            src = OUT / 'source' / f'{a.name}.aseprite'
            src.parent.mkdir(parents=True, exist_ok=True)
            (OUT / sub).mkdir(parents=True, exist_ok=True)
            # Lua reads a tiny key=value file because this Aseprite build has no JSON module
            (stage / 'manifest.txt').write_text(
                f"w={a.w}\nh={a.h}\nframes={a.frames}\nduration={a.duration_ms / 1000}\n" +
                ''.join(f"layer={n}\n" for n in a.order))
            subprocess.run([ase, '-b', '--script-param', f'dir={stage.as_posix()}',
                            '--script-param', f'out={src.as_posix()}', '--script', str(lua)], check=True)
            base = OUT / sub / a.name
            if a.frames > 1:
                subprocess.run([ase, '-b', str(src), '--scale', str(a.scale), '--save-as', f'{base}.gif'], check=True)
                # static first frame: reduced-motion / documentation still
                subprocess.run([ase, '-b', str(src), '--frame-range', '0,0', '--scale', str(a.scale),
                                '--save-as', f'{base}-still.png'], check=True)
            else:
                subprocess.run([ase, '-b', str(src), '--scale', str(a.scale), '--save-as', f'{base}.png'], check=True)
            print(f'built {sub}/{a.name} ({len(a.order)} layers, {a.frames} frames)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', type=Path)
    args = ap.parse_args()
    preview(args.preview) if args.preview else build()
