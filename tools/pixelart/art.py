"""Hogwarts / Slytherin profile art (v2).

Pixel art is drawn at native resolution and shown at 2x (every native pixel is a 2x2 block);
typography is set at full resolution with real display faces (blackletter, engraved capitals,
old-style serif, chancery script) on top of the pixel art, like an HD-2D game UI.

Every asset is an `Asset`: named layers x frames of RGBA images at final size. `build.py`
assembles them into layered .aseprite sources and exports PNG/GIF with Aseprite.
"""
import math
import os
import random
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

S = 2  # pixel scale: native pixel -> 2x2 screen pixels
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
CLEAR = (0, 0, 0, 0)


def hx(s, a=255):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (a,)


# ---------------------------------------------------------------- fonts (installed system faces; never committed)
FONT_DIR = Path(os.environ.get('PROFILE_FONT_DIR', 'C:/Windows/Fonts'))
FONT_FILES = {'black': 'OLDENGL.TTF', 'caps': 'CASTELAR.TTF', 'serif': 'GOUDOS.TTF', 'serifb': 'GOUDOSB.TTF',
              'serifi': 'GOUDOSI.TTF', 'script': 'MTCORSVA.TTF', 'hand': 'LCALLIG.TTF', 'bodoni': 'BOD_B.TTF'}


def fonts_available():
    return all((FONT_DIR / f).is_file() for f in FONT_FILES.values())


_font_cache = {}


def font(key, size):
    k = (key, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(str(FONT_DIR / FONT_FILES[key]), size)
    return _font_cache[k]


# ---------------------------------------------------------------- palette
P = dict(
    k0=hx('#08070a'), k1=hx('#121016'), k2=hx('#1e1a22'),
    night=[hx(c) for c in ('#05070f', '#0a0e1e', '#10172e', '#18213f', '#222e52')],
    star=hx('#dfe6e8'), moon=[hx('#9ea6a0'), hx('#cfd6cc'), hx('#eef1e4')],
    castle=[hx('#06070d'), hx('#0d1020'), hx('#161b30'), hx('#222a46')],
    hills=[hx('#0b1020'), hx('#111830')],
    water=[hx('#04060c'), hx('#080d1a'), hx('#0e1628'), hx('#18223c')],
    win=[hx('#7a4a14'), hx('#d89a34'), hx('#ffd27a'), hx('#fff3c8')],
    g=[hx('#4a2e0c'), hx('#7a4f18'), hx('#b07a24'), hx('#e0aa3e'), hx('#fbe2a0')],
    sv=[hx('#3c4448'), hx('#6c787c'), hx('#a8b4b6'), hx('#dfe6e4')],
    em=[hx('#04140e'), hx('#0b2a1e'), hx('#124430'), hx('#1c6b45'), hx('#33975e'), hx('#6fcf8e')],
    parch=[hx('#8a6a3e'), hx('#b8955e'), hx('#d6bb84'), hx('#e8d4a2'), hx('#f4e6c2')],
    news=[hx('#a8987a'), hx('#cbbd9c'), hx('#dfd3b6'), hx('#ece2c8')],
    ink=hx('#2b1a0e'), ink2=hx('#5a3c22'), red=hx('#8c2430'),
    sep=[hx(c) for c in ('#24180e', '#3e2c1c', '#5e4630', '#82674a', '#a88c66', '#cdb488', '#ece0bc')],
    wax=[hx('#062a18'), hx('#0e4428'), hx('#1c6b45'), hx('#3d9a66')],
    skin=[hx('#4a2a18'), hx('#6a3e26'), hx('#8a5434'), hx('#a46c46'), hx('#bc8458'), hx('#d09c70')],
    hair=[hx('#0a0707'), hx('#171111'), hx('#261d1c'), hx('#3c2f2c')],
    beard=[hx('#0e0a0a'), hx('#1b1413'), hx('#2b2120')],
    wood=[hx('#1a0f08'), hx('#2e1a0e'), hx('#4a2c16'), hx('#6e4424')],
)
GOLD_RAMP = [hx('#fff2c0'), hx('#f4cf6a'), hx('#d79a2c'), hx('#a8681a'), hx('#e8b44a')]


# ---------------------------------------------------------------- canvas: native-pixel drawing + HD typography
class Canvas:
    def __init__(self, nw, nh, bg=CLEAR, s=S):
        self.nw, self.nh, self.s = nw, nh, s
        self.w, self.h = nw * s, nh * s
        self.im = Image.new('RGBA', (self.w, self.h), bg)
        self.px = self.im.load()

    # native-pixel primitives
    def p(self, x, y, c):
        if c is None: return
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.nw and 0 <= y < self.nh:
            s = self.s; X, Y = x * s, y * s
            for dy in range(s):
                for dx in range(s):
                    self.px[X + dx, Y + dy] = c

    def g(self, x, y):
        x, y = int(round(x)), int(round(y))
        return self.px[x * self.s, y * self.s] if 0 <= x < self.nw and 0 <= y < self.nh else CLEAR

    def rect(self, x0, y0, x1, y1, c):
        if c is None: return
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(self.nw - 1, x1), min(self.nh - 1, y1)
        if x1 >= x0 and y1 >= y0:
            self.im.paste(c, (x0 * self.s, y0 * self.s, (x1 + 1) * self.s, (y1 + 1) * self.s))

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1):
            self.p(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, c)

    @staticmethod
    def dither(x, y, t):
        return t * 16 > BAYER[int(y) % 4][int(x) % 4]

    def sprite(self, ox, oy, rows, pal, flip=False):
        for y, row in enumerate(rows):
            row = row[::-1] if flip else row
            for x, ch in enumerate(row):
                if ch != '.': self.p(ox + x, oy + y, pal[ch])

    def paste(self, other, nx, ny):
        self.im.alpha_composite(other.im, (int(nx) * self.s, int(ny) * self.s))

    def outline(self, color):
        src = self.im.copy(); sp = src.load(); s = self.s
        for y in range(self.nh):
            for x in range(self.nw):
                if sp[x * s, y * s][3] == 0 and any(
                        0 <= x + dx < self.nw and 0 <= y + dy < self.nh and sp[(x + dx) * s, (y + dy) * s][3]
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.p(x, y, color)

    # full-resolution typography
    def text(self, x, y, txt, f, fill, anchor='ls', shadow=None, spacing=0):
        txt = txt.replace('·', '•')  # Goudy/Castellar have a bullet but no middle dot
        if spacing:
            return self.spaced(x, y, txt, f, fill, anchor, shadow, spacing)
        d = ImageDraw.Draw(self.im)
        if shadow: d.text((x + 2, y + 2), txt, font=f, fill=shadow, anchor=anchor)
        d.text((x, y), txt, font=f, fill=fill, anchor=anchor)

    def spaced(self, x, y, txt, f, fill, anchor, shadow, spacing):
        txt = txt.replace('·', '•')
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths) + spacing * (len(txt) - 1)
        cx = x - (total / 2 if anchor[0] == 'm' else total if anchor[0] == 'r' else 0)
        d = ImageDraw.Draw(self.im)
        for ch, wdt in zip(txt, widths):
            if shadow: d.text((cx + 1.5, y + 1.5), ch, font=f, fill=shadow, anchor='l' + anchor[1])
            d.text((cx, y), ch, font=f, fill=fill, anchor='l' + anchor[1])
            cx += wdt + spacing
        return total

    def metal_text(self, x, y, txt, f, ramp=GOLD_RAMP, anchor='ls', outline=None, shadow=True, stroke=2):
        """Gilded lettering: dark outline + drop shadow, then a vertical metallic gradient fill."""
        outline = outline or P['k0']
        d = ImageDraw.Draw(self.im)
        if shadow:
            d.text((x + 3, y + 3), txt, font=f, fill=hx('#000000', 200), anchor=anchor, stroke_width=stroke,
                   stroke_fill=hx('#000000', 200))
        d.text((x, y), txt, font=f, fill=outline, anchor=anchor, stroke_width=stroke, stroke_fill=outline)
        mask = Image.new('L', self.im.size, 0)
        ImageDraw.Draw(mask).text((x, y), txt, font=f, fill=255, anchor=anchor)
        bb = mask.getbbox()
        if not bb: return None
        grad = Image.new('RGBA', self.im.size, CLEAR)
        gd = ImageDraw.Draw(grad)
        top, bot = bb[1], bb[3]
        stops = [0.0, 0.32, 0.58, 0.82, 1.0]
        for yy in range(top, bot + 1):
            t = (yy - top) / max(1, bot - top)
            c = ramp[-1]
            for i in range(len(stops) - 1):
                if stops[i] <= t <= stops[i + 1]:
                    u = (t - stops[i]) / (stops[i + 1] - stops[i])
                    c = tuple(int(ramp[i][k] + (ramp[i + 1][k] - ramp[i][k]) * u) for k in range(3)) + (255,)
                    break
            gd.line([(bb[0], yy), (bb[2], yy)], fill=c)
        self.im.paste(grad, (0, 0), mask)
        return bb

    def paragraph(self, x, y, txt, f, fill, width, leading, align='left'):
        lines, cur = [], ''
        for word in txt.split():
            trial = (cur + ' ' + word).strip()
            if f.getlength(trial.replace('·', '•')) <= width: cur = trial
            else: lines.append(cur); cur = word
        if cur: lines.append(cur)
        for i, ln in enumerate(lines):
            if align == 'center': self.text(x + width / 2, y + i * leading, ln, f, fill, anchor='ms')
            else: self.text(x, y + i * leading, ln, f, fill)
        return len(lines)


def glow(cv, cx, cy, r, warm, strength=0.55):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1 and cv.dither(x, y, (1 - d) * strength):
                c = cv.g(x, y)
                if c[3] and sum(c[:3]) < sum(warm[:3]): cv.p(x, y, warm)


def ramp_fill(cv, x0, y0, x1, y1, ramp, horizontal=False):
    n = len(ramp) - 1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = ((x - x0) / max(1, x1 - x0)) if horizontal else ((y - y0) / max(1, y1 - y0))
            v = t * n; i = int(v)
            cv.p(x, y, ramp[min(n, i + (1 if cv.dither(x, y, v - i) else 0))])


# ---------------------------------------------------------------- layered asset container
@dataclass
class Asset:
    name: str
    w: int
    h: int
    frames: int = 1
    duration_ms: int = 100
    layers: dict = field(default_factory=dict)
    order: list = field(default_factory=list)
    alt: str = ''

    def composite(self, f=0):
        out = Image.new('RGBA', (self.w, self.h), CLEAR)
        for n in self.order: out.alpha_composite(self.layers[n][f])
        return out


class Recorder:
    """Each named step's changed pixels become one Aseprite layer. Alpha stays binary, so the layer
    stack composites back to exactly the drawn image."""

    def __init__(self, cv):
        self.cv, self.layers, self.order, self._snap = cv, {}, [], None

    def step(self, name):
        rec = self

        class _Ctx:
            def __enter__(s): rec._snap = rec.cv.im.copy()

            def __exit__(s, *a):
                after = rec.cv.im
                if not rec.order:
                    layer = after.copy()
                else:
                    diff = ImageChops.difference(after, rec._snap).convert('L').point(lambda v: 255 if v else 0)
                    layer = Image.new('RGBA', after.size, CLEAR); layer.paste(after, (0, 0), diff)
                rec.layers[name] = layer; rec.order.append(name)
        return _Ctx()


def layered(name, nw, nh, frames, duration, draw, alt=''):
    a = Asset(name, nw * S, nh * S, frames, duration, alt=alt)
    for f in range(frames):
        rec = Recorder(Canvas(nw, nh))
        draw(rec, f)
        for n in rec.order: a.layers.setdefault(n, []).append(rec.layers[n])
        a.order = rec.order
    return a


# ---------------------------------------------------------------- small pixel sprites (16x16)
IC = {'K': P['k0'], 'g': P['g'][2], 'G': P['g'][3], 'Y': P['g'][4], 'p': P['parch'][3], 'P': P['parch'][4],
      'q': P['parch'][1], 'i': P['ink'], 'e': P['em'][3], 'E': P['em'][4], 's': P['sv'][2], 'S': P['sv'][3],
      'w': P['wood'][2], 'W': hx('#b8925a'), 'b': hx('#22305e'), 'B': hx('#5a7ab8'), 'c': hx('#9ad0f0'),
      'f': hx('#ffbf3c'), 'F': hx('#fff7d0'), 'm': hx('#463238'), 'M': hx('#86644f'), 'h': hx('#efe6d2'),
      'n': hx('#8a6a4a'), 'N': hx('#b08c5c'), 'V': hx('#8f78c0'), 'x': P['k2']}
ICONS = {
    'scroll': ["................", "..KKKKKKKKKKKK..", ".KqpPPPPPPPPPpK.", ".KqKKKKKKKKKKqK.", "..KpPPPPPPPPpK..",
               "..KpiiiiiiiPpK..", "..KpPPPPPPPPpK..", "..KpiiiiiPPPpK..", "..KpPPPPPPPPpK..", "..KpiiiiiiPPpK..",
               "..KpPPPPPPeeepK.", "..KpiiiPPeEEeK..", ".KqKKKKKKeeKKqK.", ".KqpPPPPPPPPPpK.", "..KKKKKKKKKKKK..",
               "................"],
    'book': ["................", "................", ".KKKKKK..KKKKKK.", "KpPPPPPKKPPPPPpK", "KpiiiiPKKPiiiipK",
             "KpPPPPPKKPPPPPpK", "KpiiiPPKKPiiiPpK", "KpPPPPPKKPPPPPpK", "KpiiiiPKKPiiiipK", "KpPPPPPKKPPPPPpK",
             "KpiiPPPKKPPiiPpK", "KqpPPPPKKPPPPpqK", "KKKqqqqKKqqqqKKK", ".KeeKKKKKKKKKKK.", "..KE............",
             "................"],
    'orb': ["................", "................", "h.............h.", "hh...........hh.", ".hhh..KKK...hhh.",
            "..hhhKGYGK.hhh..", "...hKGYYGGKh....", "....KGGYGgK.....", "....KgGGggK.....", ".....KgggK......",
            "......KKK.......", "................", "................", "................", "................",
            "................"],
    'quill': ["...........hhK..", "..........hhhK..", ".........hhhK...", "........hhhK....", ".......hhhK.....",
              "......hhhK......", ".....hhhK.......", "....hhhK........", "....KhK.........", "...KKK..........",
              "..KiK...........", ".KKKKKK.........", ".KbbbbK.........", ".KbBbbK.........", ".KKKKKK.........",
              "................"],
    'owl': ["....K......K....", "...KnK....KnK...", "...KnnKKKKnnK...", "..KnnnnnnnnnnK..", "..KnKKnnnnKKnK..",
            ".KnKYGKnnKYGKnK.", ".KnKGKKnnKGKKnK.", ".KnnKKnWWnKKnnK.", ".KNnnnnWWnnnnNK.", ".KNNnNnnnnNnNNK.",
            ".KNnNnNnnNnNnNK.", "..KNNnNnnNnNNK..", "..KNnNnNNnNnNK..", "...KNNNNNNNNK...", "....KWK..KWK....",
            "................"],
    'gamepad': ["................", "................", "................", "...KKKK..KKKK...", "..KmmmmKKmmmmK..",
                ".KmMmmmmmmmGmmK.", ".KmMMMmmmmGYGmK.", ".KmmMmmmmmmGmmK.", ".KmmmmmKKmmmmmK.", ".KmmmmK..KmmmmK.",
                "..KmmK....KmmK..", "...KK......KK...", "................", "................", "................",
                "................"],
    'crystal': ["................", ".....KKKKKK.....", "...KKbbbbcbKK...", "..KbbBbbbccbbK..", "..KbBVBbbbcbbK..",
                ".KbbBVVBbbbbbbK.", ".KbbbBBbbbBbbbK.", ".KbbbbbbbBVBbbK.", "..KbbbbbbbBbbK..", "..KKbbbbbbbbKK..",
                "...KKKbbbbKKK...", "....KgGGGGgK....", "...KgggGGgggK...", "..KKKKKKKKKKKK..", "................",
                "................"],
    'wand': ["............Y...", "...........YGY..", "..Y.........Y...", ".YGY.....Y......", "..Y.....KWK.....",
             "........KWK.....", ".......KWK......", "......KWK...Y...", ".....KwK...YGY..", "....KwK.....Y...",
             "...KwK..........", "..KwgK..........", ".KwgK...........", "KwwK............", "KKK.............",
             "................"],
    'abacus': ["................", ".KKKKKKKKKKKKKK.", ".KwwwwwwwwwwwwK.", ".Kw..........wK.", ".KwssssGGG...wK.",
               ".Kw..........wK.", ".KwssGGGG....wK.", ".Kw..........wK.", ".KwsssssGG...wK.", ".Kw..........wK.",
               ".KwsGGGGGG...wK.", ".Kw..........wK.", ".KwwwwwwwwwwwwK.", ".KKKKKKKKKKKKKK.", "................",
               "................"],
    'cauldron': ["................", "....E...E.......", "...E..E...E.....", ".....E..E..E....", "...KKKKKKKKKK...",
                 "..KxEEeEEeEExK..", ".KKKKKKKKKKKKKK.", ".KxxmxxxxxxxmxK.", ".KxmxxxxxxxxxxK.", ".KxxxxxxxxxxxxK.",
                 "..KxxxxxxxxxxK..", "...KKKKKKKKKK...", "...KfK.KfK.KfK..", "..KFfK.KFfKKFfK.", "................",
                 "................"],
}
SERPENT = [  # original serpent emblem, 14x16 (not the official house crest)
    "......SSS.....", ".....SsssS....", "....SsKssK....", "....SssssS.r..", ".....SssS.r...", "......SsSr....",
    ".......SsS....", "..SSS...SsS...", ".SsssS...SsS..", "SsS.SsS...SsS.", "SsS..SsSSSssS.", ".SsS..SsssssS.",
    "..SsS..SSSSS..", "...SsS........", "....SsSSS.....", ".....SSSS.....",
]


def icon(cv, nx, ny, name):
    cv.sprite(nx, ny, ICONS[name], IC)


def serpent(cv, nx, ny, flip=False):
    cv.sprite(nx, ny, SERPENT, {'S': P['sv'][1], 's': P['sv'][3], 'K': P['k0'], 'r': P['red']}, flip=flip)


# ---------------------------------------------------------------- Kaustuv: pixel portrait (from his reference photo)
def portrait(f=0):
    """64x80 native. Voluminous black curls, round thin-rimmed glasses, full short beard, broad smile,
    medium-brown skin; Slytherin uniform: black robe with green lining, grey jumper with green/silver
    trim, white shirt, green-and-silver striped tie."""
    cv = Canvas(64, 80)
    SK, HR, BD = P['skin'], P['hair'], P['beard']
    cx = 32
    for y in range(58, 80):  # robe
        hw = 20 + (y - 58) * 0.62
        for x in range(int(cx - hw), int(cx + hw) + 1):
            u = x - cx
            cv.p(x, y, hx('#121216') if u > hw - 3 else hx('#1a1a20') if u < -hw + 5 else hx('#25252d'))
    for y in range(60, 80):  # lapels with green lining
        k = (y - 60) * 0.55
        for side in (-1, 1):
            xl = cx + side * (9 + k)
            cv.p(xl, y, P['em'][3]); cv.p(xl + side, y, P['em'][2])
    for y in range(60, 80):  # grey jumper
        half = 8 + (y - 60) * 0.55
        for x in range(int(cx - half) + 1, int(cx + half)):
            cv.p(x, y, hx('#545a62') if x < cx + 3 else hx('#444a52'))
    for y in range(59, 74):  # V-neck with green/silver trim, shirt inside
        half = max(0, 8 - (y - 59) * 0.62)
        for x in range(int(cx - half), int(cx + half) + 1):
            cv.p(x, y, hx('#ecebe6') if x < cx + 2 else hx('#c4c8cc'))
        cv.p(cx - half - 1, y, P['em'][3]); cv.p(cx + half + 1, y, P['em'][3])
        cv.p(cx - half - 2, y, P['sv'][2]); cv.p(cx + half + 2, y, P['sv'][2])
    for y in range(57, 61):  # collar points
        for x in range(cx - 7 + (y - 57), cx - 1): cv.p(x, y, hx('#f4f2ec'))
        for x in range(cx + 2, cx + 8 - (y - 57)): cv.p(x, y, hx('#d4d8da'))
    cv.rect(cx - 2, 58, cx + 2, 60, P['em'][2]); cv.p(cx - 1, 58, P['em'][3]); cv.p(cx, 59, P['sv'][2])  # knot
    for y in range(61, 74):  # tie, diagonal Slytherin stripes
        half = 1 + (y - 61) * 0.18
        for x in range(int(cx - half - 0.5), int(cx + half + 0.5) + 1):
            cv.p(x, y, P['sv'][2] if (x + y) % 5 == 0 else (P['em'][3] if x < cx + 1 else P['em'][2]))
    for y in range(48, 60):  # neck
        for x in range(cx - 7, cx + 8):
            cv.p(x, y, SK[1] if x > cx + 3 or y < 52 else SK[2])
    for (ex, s) in ((18, -1), (46, 1)):  # ears
        for y in range(34, 43):
            cv.p(ex, y, SK[2] if s < 0 else SK[1]); cv.p(ex - s, y, SK[3] if s < 0 else SK[2])
        cv.p(ex, 37, SK[0]); cv.p(ex, 38, SK[0])
    for y in range(20, 54):  # face, light from upper left
        for x in range(18, 47):
            dx, dy = (x - cx) / 13.0, (y - 36) / 16.5
            if dy > 0: dx *= 1 + dy * 0.35
            if dx * dx + dy * dy <= 1:
                shade = 3
                if x > cx + 6 or (x > cx + 3 and y > 44): shade = 2
                if x > cx + 10: shade = 1
                if x < cx - 4 and y < 40: shade = 4
                if x < cx - 6 and 28 < y < 36: shade = 5 if cv.dither(x, y, 0.5) else 4
                cv.p(x, y, SK[shade])
    rnd = random.Random(3)
    for y in range(38, 58):  # full short beard, stubble edge dithered into the cheeks
        for x in range(16, 49):
            if cv.g(x, y)[3] == 0 and not (y >= 52 and abs(x - cx) < 9 - (y - 52)): continue
            dx = abs(x - cx)
            start = 41 if dx > 8 else 43 if dx > 5 else 45
            if y < start or (y > 53 and dx > 9 - (y - 53) * 2) or dx > 13: continue
            if y == start and cv.dither(x, y, 0.5): continue
            cv.p(x, y, BD[2] if rnd.random() < 0.18 else BD[1] if rnd.random() < 0.8 else BD[0])
    for x in range(cx - 7, cx + 8):  # mustache
        cv.p(x, 45, BD[1]); cv.p(x, 46, BD[0] if abs(x - cx) > 1 else BD[1])
    for x in range(cx - 6, cx + 7): cv.p(x, 47, hx('#3a1a14'))  # broad smile
    for x in range(cx - 5, cx + 6): cv.p(x, 48, hx('#f4f0e6') if abs(x - cx) < 5 else hx('#cfc8b8'))
    for x in range(cx - 4, cx + 5): cv.p(x, 49, hx('#e2dccc') if abs(x - cx) < 4 else hx('#5a2a20'))
    for x in range(cx - 3, cx + 4): cv.p(x, 50, hx('#4a1e18'))
    for x in range(cx - 2, cx + 3): cv.p(x, 51, hx('#7a3c30'))
    cv.p(cx - 7, 46, hx('#3a1a14')); cv.p(cx + 7, 46, hx('#3a1a14'))
    for y in range(36, 43): cv.p(cx, y, SK[4] if y < 41 else SK[3])  # nose
    for y in range(38, 43): cv.p(cx + 2, y, SK[2])
    cv.p(cx - 2, 43, SK[1]); cv.p(cx + 2, 43, SK[0]); cv.p(cx - 1, 43, SK[2]); cv.p(cx + 1, 43, SK[2]); cv.p(cx, 42, SK[4])
    for i in range(9):  # thick eyebrows
        y = 30 if 1 <= i <= 7 else 31
        for bx in (cx - 11 + i, cx + 3 + i):
            cv.p(bx, y, HR[1]); cv.p(bx, y + 1, HR[2] if i % 2 else HR[1])
    blink = f in (9, 10)
    for ex in (cx - 7, cx + 7):  # smiling eyes
        if blink:
            for d in range(-2, 3): cv.p(ex + d, 36, hx('#1a0e0a'))
        else:
            for d in (-1, 0, 1): cv.p(ex + d, 34, hx('#1a0e0a'))
            cv.p(ex - 2, 35, hx('#1a0e0a')); cv.p(ex + 2, 35, hx('#1a0e0a'))
            cv.p(ex - 1, 35, hx('#140a08')); cv.p(ex, 35, hx('#0a0606')); cv.p(ex + 1, 35, hx('#140a08'))
            cv.p(ex - 1, 34, hx('#f0e8d8'))
        for d in (-1, 0, 1): cv.p(ex + d, 38, SK[4] if ex < cx else SK[3])
    for ex in (cx - 7, cx + 7):  # round thin-rimmed glasses
        for y in range(28, 44):
            for x in range(ex - 7, ex + 8):
                if 5.0 <= math.hypot(x - ex, (y - 36) * 1.05) < 6.0:
                    cv.p(x, y, hx('#8c7a62') if y < 33 else hx('#2a201c'))
        cv.p(ex - 3, 32, hx('#e8f0f2')); cv.p(ex - 2, 32, hx('#c8dce4')); cv.p(ex - 4, 33, hx('#c8dce4'))
    for x in (cx - 1, cx, cx + 1): cv.p(x, 35, hx('#2a201c'))
    cv.line(cx - 13, 35, 18, 34, hx('#2a201c')); cv.line(cx + 13, 35, 46, 34, hx('#2a201c'))
    rnd = random.Random(11)
    curls = []
    for i in range(17):  # dome of curls
        a = math.pi * (1.02 + i / 16 * 0.96)
        curls.append((cx + 16 * math.cos(a), 25 + 17 * math.sin(a), 4.0 + rnd.random() * 1.1))
    for i in range(12):  # inner volume
        a = math.pi * (1.1 + i / 11 * 0.8)
        curls.append((cx + 10 * math.cos(a), 20 + 10 * math.sin(a), 4.5))
    curls += [(cx - 14, 28, 3.2), (cx + 15, 28, 3.2), (cx - 14, 32, 2.2), (cx + 15, 32, 2.2)]
    curls += [(cx - 8, 22.5, 3.2), (cx - 2, 22, 3.4), (cx + 4, 22.5, 3.2), (cx + 9, 23.5, 3.0), (cx - 12, 25, 3)]
    for (ux, uy, r) in curls:
        for y in range(int(uy - r - 1), int(uy + r + 2)):
            for x in range(int(ux - r - 1), int(ux + r + 2)):
                d = math.hypot(x - ux, y - uy)
                if d <= r:
                    ang = math.atan2(y - uy, x - ux)
                    c = HR[1]
                    if d > r - 1.2 and -2.6 < ang < -0.9: c = HR[3]
                    elif d > r - 1.0 and 0.4 < ang < 2.2: c = HR[0]
                    elif d < r * 0.45 and (x + y) % 3 == 0: c = HR[2]
                    cv.p(x, y, c)
    cv.outline(hx('#050304'))
    return cv


# ---------------------------------------------------------------- shared scenery
def night_sky(cv, y0, y1, f, seed=5, stars=90):
    ramp_fill(cv, 0, y0, cv.nw - 1, y1, P['night'])
    rnd = random.Random(seed)
    for i in range(stars):
        x, y = rnd.randrange(cv.nw), rnd.randrange(y0, max(y0 + 1, y1 - 10))
        k = (i + f) % 6
        if k == 0: continue
        cv.p(x, y, P['star'] if i % 3 else P['moon'][1])
        if i % 17 == 0 and k in (2, 3):
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.p(x + d[0], y + d[1], P['night'][4])


def moon(cv, mx, my, r):
    glow(cv, mx, my, r + 9, P['night'][4], 0.7)
    for y in range(my - r, my + r + 1):
        for x in range(mx - r, mx + r + 1):
            d = math.hypot(x - mx, y - my)
            if d <= r:
                c = P['moon'][2] if (x - mx) + (y - my) < r * 0.4 else P['moon'][1]
                if d > r - 1.2 and x > mx: c = P['moon'][0]
                cv.p(x, y, c)
    for (dx, dy, rr) in ((-3, -2, 2), (3, 3, 1.5), (-1, 5, 1.2), (4, -4, 1)):
        for y in range(int(my + dy - rr), int(my + dy + rr) + 1):
            for x in range(int(mx + dx - rr), int(mx + dx + rr) + 1):
                if math.hypot(x - mx - dx, y - my - dy) <= rr: cv.p(x, y, P['moon'][0])


TOWERS = [  # x, width, top, roof height: an original gothic school-castle silhouette
    (88, 7, 104, 12), (100, 9, 92, 16), (114, 6, 108, 9), (128, 12, 78, 22), (146, 8, 96, 14), (158, 16, 66, 26),
    (180, 9, 86, 16), (195, 22, 100, 0), (222, 7, 82, 18), (234, 11, 94, 14), (250, 6, 106, 10), (262, 13, 88, 18),
    (282, 8, 100, 12), (296, 7, 110, 9),
]


def castle(cv, f, horizon=136):
    C = P['castle']
    for x in range(cv.nw):  # far hills
        top = horizon - 14 + round(5 * math.sin(x / 23) + 3 * math.sin(x / 9 + 1))
        for y in range(top, horizon + 1): cv.p(x, y, P['hills'][1] if y < top + 2 else P['hills'][0])
    for x in range(70, 318):  # cliff
        top = horizon - 10 + round(3 * math.sin(x / 7) + 2 * math.sin(x / 3.3))
        if x < 84: top += (84 - x)
        if x > 304: top += (x - 304)
        for y in range(top, horizon + 1): cv.p(x, y, C[0] if (x + y) % 7 else C[1])
    for x in range(86, 302):  # curtain wall with crenellations
        top = 114 if (x // 3) % 2 else 112
        for y in range(top, horizon - 6): cv.p(x, y, C[1])
    rnd = random.Random(9)
    windows = []
    for (tx, tw, top, rh) in TOWERS:
        for y in range(top, horizon - 4):
            for x in range(tx, tx + tw): cv.p(x, y, C[2] if x == tx else C[1])
        if rh:
            for j in range(rh):
                half = (tw / 2 + 1) * (j / rh)
                for x in range(int(tx + tw / 2 - half), int(tx + tw / 2 + half) + 1):
                    cv.p(x, top - rh + j, C[2] if x < tx + tw / 2 - half + 1 else C[1])
        else:  # great hall, pitched roof
            for j in range(8): cv.line(tx + j, top - j, tx + tw - j, top - j, C[1])
        for k in range(max(1, tw // 4)):
            for row in range(top + 4, horizon - 10, 7):
                if rnd.random() < 0.55:
                    windows.append((tx + 1 + k * 4 + rnd.randrange(max(1, min(3, tw - 2))), row))
        if rh >= 16:  # Slytherin pennants on the tallest spires
            px_, py_ = int(tx + tw / 2), top - rh - 5
            cv.line(px_, py_, px_, top - rh, C[2])
            for i in range(5): cv.p(px_ + 1 + i, py_ + (i + (f // 2) % 2) % 2, P['em'][3] if i < 4 else P['sv'][2])
    for i, (x, y) in enumerate(windows):
        lvl = 1 if (i * 7 + f) % 11 == 0 else 2 if (i + f // 3) % 5 else 3
        cv.p(x, y, P['win'][lvl]); cv.p(x, y + 1, P['win'][max(1, lvl - 1)])
    return windows


def lake(cv, y0, windows, f):
    W_ = P['water']
    ramp_fill(cv, 0, y0, cv.nw - 1, cv.nh - 1, W_)
    for y in range(y0 + 2, cv.nh, 3):
        off = (f * 2 + y * 5) % 24
        for x in range(-off, cv.nw, 24): cv.line(x, y, x + 7, y, W_[3] if y < y0 + 25 else W_[2])
    for i, (wx, wy) in enumerate(windows):  # a few broken gold reflections
        if i % 4: continue
        ry = y0 + 3 + (y0 - wy) // 4
        for k in range(0, 5, 2):
            if (k + f + i) % 3: cv.p(wx + ((k // 2 + f) % 2), ry + k, P['win'][1])


def gilded_frame(cv, x0, y0, x1, y1):
    G_ = P['g']
    rings = (P['k0'], G_[1], G_[3], G_[4], G_[2], G_[1], G_[2], P['k0'])
    for i, c in enumerate(rings):
        lit = c; shade = G_[1] if i in (2, 3) else c  # light from top-left
        for x in range(x0 + i, x1 - i + 1): cv.p(x, y0 + i, lit); cv.p(x, y1 - i, shade)
        for y in range(y0 + i, y1 - i + 1): cv.p(x0 + i, y, lit); cv.p(x1 - i, y, shade)
    for i in range(x0 + 4, x1 - 3, 6): cv.p(i, y0 + 3, G_[4]); cv.p(i + 1, y1 - 3, G_[1])  # beading
    for (cx_, cy_) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):  # corner rosettes
        for y in range(cy_ - 3, cy_ + 4):
            for x in range(cx_ - 3, cx_ + 4):
                d = abs(x - cx_) + abs(y - cy_)
                if d <= 3: cv.p(x, y, (G_[4], G_[3], G_[2], P['k0'])[d])


def parchment(cv, x0, y0, x1, y1, seed=1, ramp=None, edge=True):
    pr = ramp or P['parch']
    rnd = random.Random(seed)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n = math.sin(x * 0.11 + y * 0.07 + seed) + math.sin(x * 0.035 - y * 0.13) + 0.6 * math.sin((x + y) * 0.2)
            c = pr[3]
            if n > 1.5: c = pr[2] if cv.dither(x, y, 0.6) else pr[3]
            if n > 2.1: c = pr[2]
            if n < -1.7: c = pr[4] if cv.dither(x, y, 0.5) else pr[3]
            cv.p(x, y, c)
    if edge:  # aged, deckled edge
        for x in range(x0, x1 + 1):
            for y in range(rnd.randint(0, 2)): cv.p(x, y0 + y, pr[0])
            for y in range(rnd.randint(0, 2)): cv.p(x, y1 - y, pr[0])
            cv.p(x, y0 + 2, pr[1]); cv.p(x, y1 - 2, pr[1])
        for y in range(y0, y1 + 1):
            for x in range(rnd.randint(0, 2)): cv.p(x0 + x, y, pr[0])
            for x in range(rnd.randint(0, 2)): cv.p(x1 - x, y, pr[0])
            cv.p(x0 + 2, y, pr[1]); cv.p(x1 - 2, y, pr[1])


def wax_seal(cv, cx, cy, r=9):
    W_ = P['wax']
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = math.hypot(x - cx, y - cy) + 0.7 * math.sin(math.atan2(y - cy, x - cx) * 7)
            if d <= r:
                c = W_[3] if d < r - 3 and (x - cx) + (y - cy) < -4 else W_[2] if d < r - 1.5 else W_[1]
                if r - 4.2 < d < r - 3.2: c = W_[1]
                cv.p(x, y, c)
    for i in range(12):  # embossed serpent "S"
        cv.p(cx + round(2.6 * math.sin(i / 1.8)), cy - 6 + i, W_[0])
    cv.p(cx + 1, cy - 6, W_[3]); cv.p(cx + 2, cy - 7, W_[0])


# ---------------------------------------------------------------- HERO
HERO_ALT = ("Animated pixel-art banner: a gothic castle across a moonlit lake at night with flickering windows. "
            "Gilded lettering reads Kaustuv Mohapatra, Game Developer, AI/ML Engineer, Creative Technologist, "
            "of the noble House of Slytherin. On the right, a gilded moving portrait of Kaustuv: curly black hair, "
            "round glasses, a short beard and a broad smile, in a Slytherin robe and green-and-silver tie.")


def hero():
    nw, nh = 416, 196

    def draw(rec, f):
        cv = rec.cv
        with rec.step('sky'):
            night_sky(cv, 0, 140, f)
        with rec.step('moon'):
            moon(cv, 286, 22, 9)
        with rec.step('castle'):
            wins = castle(cv, f)
        with rec.step('lake'):
            lake(cv, 137, wins, f)
        with rec.step('fireflies'):
            for i in range(9):
                x = 30 + i * 31 + round(3 * math.sin((f + i * 2) * math.pi / 6))
                y = 150 + (i * 7) % 30 + round(2 * math.cos((f + i) * math.pi / 6))
                cv.p(x, y, P['em'][5] if (i + f) % 3 else P['g'][4])
        fx0, fy0, fx1, fy1 = 316, 14, 402, 124
        with rec.step('portrait-backdrop'):
            ramp_fill(cv, fx0 + 7, fy0 + 7, fx1 - 7, fy1 - 7, [P['em'][2], P['em'][1], P['em'][0]])
            for y in range(fy0 + 7, fy1 - 6):  # common-room arch behind the sitter
                for x in range(fx0 + 7, fx1 - 6):
                    u = abs(x - (fx0 + fx1) / 2) / 30
                    if u < 1 and fy0 + 12 + 26 * (1 - math.sqrt(1 - u * u)) < y < fy0 + 70 and (x + y) % 2 == 0:
                        cv.p(x, y, P['em'][3])
            glow(cv, fx0 + 16, fy0 + 26, 8, P['g'][1], 0.5)
            cv.p(fx0 + 16, fy0 + 26, P['g'][4]); cv.p(fx0 + 16, fy0 + 25, P['win'][3])
        with rec.step('portrait'):
            cv.paste(portrait(f), 327, fy1 - 7 - 79)
        with rec.step('frame-gilt'):
            gilded_frame(cv, fx0, fy0, fx1, fy1)
            serpent(cv, 352, 4)
            cv.rect(331, 127, 387, 139, P['g'][2]); cv.rect(332, 128, 386, 138, P['g'][3])
            cv.line(331, 127, 387, 127, P['g'][4]); cv.line(331, 139, 387, 139, P['k0']); cv.line(332, 138, 386, 138, P['g'][1])
        with rec.step('lettering'):
            cv.metal_text(40, 116, 'Kaustuv Mohapatra', font('black', 70))
            cv.text(44, 158, 'GAME DEVELOPER  ·  AI/ML ENGINEER  ·  CREATIVE TECHNOLOGIST', font('caps', 13),
                    P['sv'][3], shadow=hx('#000000', 220), spacing=1.2)
            cv.text(44, 202, 'of the noble House of Slytherin', font('script', 30), P['em'][5], shadow=hx('#000000', 220))
            cv.text(718, 271, 'SLYTHERIN', font('caps', 13), hx('#2a1a08'), anchor='ms', spacing=2)
    return layered('hero', nw, nh, 12, 130, draw, HERO_ALT)


# ---------------------------------------------------------------- game-menu buttons
BUTTONS = [  # (slug, label, icon, url)
    ('portfolio', 'PORTFOLIO', 'scroll', 'https://kaustuvmohapatra.github.io/ResumeSite/'),
    ('play', 'PLAY GAMES', 'orb', 'https://kaustuvm.itch.io/'),
    ('github', 'GITHUB', 'book', 'https://github.com/KaustuvMohapatra?tab=repositories'),
    ('linkedin', 'LINKEDIN', 'quill', 'https://www.linkedin.com/in/kaustuv-mohapatra-b0538428b/'),
    ('owl', 'OWL POST', 'owl', 'mailto:kaustuv4@outlook.com'),
]


def button(slug, label, icon_name):
    nw, nh = 82, 24

    def draw(rec, f):
        cv = rec.cv
        with rec.step('plate'):
            ramp_fill(cv, 1, 1, nw - 2, nh - 2, [P['em'][2], P['em'][1], P['em'][1], P['em'][0]])
            for x in range(nw):
                cv.p(x, 0, P['k0']); cv.p(x, nh - 1, P['k0'])
                cv.p(x, 1, P['g'][4] if 2 < x < nw - 3 else P['g'][3]); cv.p(x, nh - 2, P['g'][1])
                cv.p(x, 2, P['g'][2]); cv.p(x, nh - 3, P['g'][2])
            for y in range(nh):
                cv.p(0, y, P['k0']); cv.p(nw - 1, y, P['k0'])
                cv.p(1, y, P['g'][3]); cv.p(nw - 2, y, P['g'][1]); cv.p(2, y, P['g'][2]); cv.p(nw - 3, y, P['g'][2])
            for (x, y) in ((1, 1), (nw - 2, 1), (1, nh - 2), (nw - 2, nh - 2)): cv.p(x, y, P['k0'])
            cv.line(3, 3, nw - 4, 3, P['em'][3])
            cv.rect(4, 4, 21, nh - 5, P['em'][0]); cv.line(22, 4, 22, nh - 5, P['g'][1])  # icon well
        with rec.step('icon'):
            icon(cv, 5, 4, icon_name)
            if f in (2, 3):
                for (x, y) in ((18, 5), (17, 6), (19, 6), (18, 7)): cv.p(x, y, P['g'][4])
        with rec.step('glint'):  # light sweeping across the plate
            gx = -20 + f * 15
            for d in range(4, nh - 3):
                for w in range(3):
                    x = gx + d // 2 + w
                    if 23 < x < nw - 3 and cv.g(x, d)[:3] in (P['em'][1][:3], P['em'][2][:3], P['em'][0][:3]):
                        cv.p(x, d, P['em'][3])
        with rec.step('label'):
            size = 15
            while font('caps', size).getlength(label) + 1.2 * len(label) > 90 and size > 10: size -= 1
            cv.spaced(95, 25, label, font('caps', size), P['g'][4], 'mm', hx('#000000', 230), 1.2)
            col = P['g'][4] if (f % 4) < 2 else P['g'][2]  # pulsing "play" rune
            cv.sprite(nw - 9, 9, ["#..", "##.", "###", "##.", "#.."], {'#': col})
    return layered(f'button-{slug}', nw, nh, 8, 120, draw, f'{label.title()} button')


# ---------------------------------------------------------------- section banners
SECTIONS = [
    ('letter', 'The Acceptance Letter', 'ABOUT  ME'),
    ('restricted', 'The Restricted Section', 'FEATURED  PROJECTS'),
    ('owls', 'Ordinary Wizarding Levels', 'SKILLS  &  TECHNOLOGIES'),
    ('map', "The Marauder's Map", 'JOURNEY  &  EXPERIENCE'),
    ('owlpost', 'Owl Post', 'GET  IN  TOUCH'),
]


def banner(slug, title, sub):
    nw, nh = 416, 50

    def draw(rec, f):
        cv = rec.cv
        y0, y1 = 8, 40
        with rec.step('ribbon'):
            for s_, x in ((-1, 22), (1, 393)):  # swallowtail ends folding back behind the ribbon
                for d in range(1, 20):
                    for y in range(y0 + 6, y1 + 7):
                        if d > 11 and abs(y - (y0 + y1 + 12) / 2) < d - 11: continue
                        cv.p(x + s_ * d, y, P['k0'] if d == 19 or y in (y0 + 6, y1 + 6) else P['em'][0])
            for x in range(20, 396):
                for y in range(y0, y1 + 1):
                    c = P['em'][2] if y < y0 + 3 else P['em'][1] if y < y1 - 3 else P['em'][0]
                    if (x * 3 + y) % 11 == 0 and y0 + 3 < y < y1 - 3: c = P['em'][2]  # velvet nap
                    cv.p(x, y, c)
            for x in range(18, 398):
                cv.p(x, y0 - 1, P['k0']); cv.p(x, y1 + 1, P['k0'])
                cv.p(x, y0, P['sv'][3] if x % 2 else P['sv'][2]); cv.p(x, y1, P['sv'][1])
                if 40 < x < 376: cv.p(x, y0 + 2, P['g'][2]); cv.p(x, y1 - 2, P['g'][1])
        with rec.step('serpents'):
            serpent(cv, 26, 16); serpent(cv, 376, 16, flip=True)
            for x0 in (48, 368):
                for d in range(3):
                    for (dx, dy) in ((0, -d), (0, d), (-d, 0), (d, 0)): cv.p(x0 + dx, 24 + dy, P['g'][3])
                cv.p(x0, 24, P['g'][4])
        with rec.step('lettering'):
            cv.metal_text(416, 55, title, font('black', 38), anchor='ms')
            cv.text(416, 73, sub, font('caps', 11), P['sv'][3], anchor='ms', shadow=hx('#000000', 220), spacing=2.5)
    return layered(f'section-{slug}', nw, nh, 1, 100, draw, f'{title}: {" ".join(sub.split()).title()}')


# ---------------------------------------------------------------- acceptance letter (About)
LETTER = {
    'greeting': 'Dear Mr. Mohapatra,',
    'opening': ('We are pleased to confirm that you have been sorted into Slytherin House, for ambition, '
                'resourcefulness and a habit of building things that feel alive.'),
    'entries': [
        ('STUDIES', 'B.Tech, Computer Science & Engineering · VIT Vellore'),
        ('CRAFT', 'Game development, applied AI and interactive software'),
        ('KNOWN FOR', 'Autonomous simulations, playable games and creative AI tools'),
        ('OFFICE HELD', 'Senior Core Technical Department Head, TAG Club, VIT'),
        ('INTERESTS', 'Gameplay, AI agents, emergent simulation, creative tools'),
    ],
    'closing': 'Wherever technical depth meets experiences that feel good to use, you will find him at work.',
    'sign': 'Yours sincerely, the Sorting Hat',
}


def letter():
    nw, nh = 416, 222

    def draw(rec, f):
        cv = rec.cv
        with rec.step('desk'):
            for y in range(nh):
                for x in range(nw):
                    c = P['wood'][1] if (y // 9) % 2 else P['wood'][2]
                    if (x * 7 + (y // 9) * 31) % 53 == 0 or y % 9 == 0: c = P['wood'][0]
                    cv.p(x, y, c)
            for (cx_, cy_) in ((14, 18), (402, 18)):  # candles in the corners
                glow(cv, cx_, cy_, 16, P['wood'][3], 0.6)
                cv.rect(cx_ - 2, cy_, cx_ + 2, cy_ + 14, hx('#efe0c0')); cv.line(cx_ + 2, cy_, cx_ + 2, cy_ + 14, hx('#bfa982'))
                cv.p(cx_, cy_ - 1, P['win'][2]); cv.p(cx_, cy_ - 2, P['win'][3]); cv.p(cx_, cy_ - 3, P['win'][2])
        with rec.step('envelope'):
            cv.rect(28, 12, 392, 218, hx('#c8b07a')); cv.line(28, 12, 392, 12, hx('#e0cc98'))
            cv.line(28, 12, 210, 70, hx('#a88f5a')); cv.line(392, 12, 210, 70, hx('#a88f5a'))
        with rec.step('parchment'):
            parchment(cv, 36, 6, 384, 214, seed=4)
            for x in range(52, 368):
                cv.p(x, 32, P['ink2']); cv.p(x, 34, P['g'][2] if x % 3 else None)
        with rec.step('seal'):
            for i in range(12):  # ribbon tails under the seal
                for w in range(3):
                    cv.p(344 - i // 2 + w, 194 + i, P['wax'][2] if w else P['wax'][1])
                    cv.p(362 + i // 2 + w, 194 + i, P['wax'][2] if w < 2 else P['wax'][1])
            wax_seal(cv, 354, 186, 13)
        with rec.step('lettering'):
            ink = P['ink']
            cv.text(416, 52, 'HOGWARTS SCHOOL of WITCHCRAFT and WIZARDRY', font('caps', 19), ink, anchor='ms', spacing=1.2)
            cv.text(416, 104, LETTER['greeting'], font('script', 32), ink, anchor='ms')
            y = 136
            n = cv.paragraph(112, y, LETTER['opening'], font('serifi', 18), ink, 608, 23, align='center')
            y += n * 23 + 16
            for label, value in LETTER['entries']:
                cv.text(240, y, label, font('caps', 13), P['red'], anchor='rs', spacing=1)
                cv.text(256, y, value, font('serif', 17), ink)
                y += 26
            n = cv.paragraph(112, y + 10, LETTER['closing'], font('serifi', 17), P['ink2'], 608, 22, align='center')
            cv.text(416, y + 10 + n * 22 + 34, LETTER['sign'], font('script', 28), ink, anchor='ms')
    alt = ('Acceptance letter on parchment, sealed with green wax. ' + LETTER['greeting'] + ' ' + LETTER['opening'] + ' '
           + ' '.join(f'{k.title()}: {v}.' for k, v in LETTER['entries']) + ' ' + LETTER['closing'] + ' ' + LETTER['sign'] + '.')
    return layered('letter', nw, nh, 1, 100, draw, alt)


# ---------------------------------------------------------------- Daily Prophet pages with moving photographs
SEP = P['sep']


def _photo_echosim(cv, x0, y0, f):
    for y in range(64):
        for x in range(120):
            cv.p(x0 + x, y0 + y, SEP[1] if y < 40 else SEP[2] if cv.dither(x, y, 0.5) else SEP[3])
    for (sx, sy) in ((12, 6), (40, 10), (70, 4), (96, 9), (110, 15)):
        cv.p(x0 + sx, y0 + sy, SEP[6] if (sx + f) % 3 else SEP[4])
    for i, hx0 in enumerate((6, 44, 82)):
        cv.rect(x0 + hx0, y0 + 22, x0 + hx0 + 28, y0 + 42, SEP[3]); cv.line(x0 + hx0 + 28, y0 + 22, x0 + hx0 + 28, y0 + 42, SEP[2])
        for d in range(10): cv.line(x0 + hx0 - 2 + d, y0 + 22 - d, x0 + hx0 + 30 - d, y0 + 22 - d, SEP[0] if d < 9 else SEP[1])
        cv.rect(x0 + hx0 + 5, y0 + 27, x0 + hx0 + 9, y0 + 31, SEP[6] if (f + i) % 4 else SEP[2])
        cv.rect(x0 + hx0 + 17, y0 + 32, x0 + hx0 + 22, y0 + 42, SEP[1])
    walk = [0, 1, 2, 3, 4, 3, 2, 1][f]
    for i, (bx, dir_) in enumerate(((20, 1), (58, -1), (96, 1))):  # residents strolling, thinking
        x = x0 + bx + dir_ * walk * 2
        y = y0 + 52
        cv.rect(x, y - 6, x + 2, y, SEP[0]); cv.rect(x, y - 9, x + 2, y - 7, SEP[5])
        cv.p(x + (f % 2), y + 1, SEP[0]); cv.p(x + 2 - (f % 2), y + 1, SEP[0])
        if (f + i * 3) % 8 < 5:
            cv.rect(x + 4, y - 20, x + 13, y - 13, SEP[6]); cv.p(x + 4, y - 11, SEP[6]); cv.p(x + 3, y - 9, SEP[6])
            sym = [["#.#", ".#.", "#.#"], [".#.", "###", ".#."], ["##.", "###", ".##"]][i]
            cv.sprite(x + 7, y - 19, sym, {'#': SEP[1]})
    for x in range(26, 96, 2): cv.p(x0 + x, y0 + 46, SEP[5] if (x // 2 + f) % 4 == 0 else SEP[4])


def _photo_arena(cv, x0, y0, f):
    cx, cy = x0 + 60, y0 + 32
    for y in range(64):
        for x in range(120):
            d = math.hypot((x0 + x - cx) / 1.8, y0 + y - cy)
            cv.p(x0 + x, y0 + y, SEP[4] if d < 26 and cv.dither(x, y, 0.6) else SEP[3] if d < 26 else SEP[2] if d < 28 else SEP[1])
    for k in range(12):
        a = k * math.pi / 6 + f * 0.08
        r = 25 - (f % 8) * 0.6
        ex, ey = cx + r * 1.8 * math.cos(a), cy + r * math.sin(a)
        cv.rect(ex - 1, ey - 1, ex + 1, ey + 1, SEP[0]); cv.p(ex, ey - 1, SEP[5])
    for k in range(3):  # orbiting blades
        a = f * math.pi / 4 + k * 2 * math.pi / 3
        bx, by = cx + 12 * math.cos(a), cy + 7 * math.sin(a)
        cv.p(bx, by, SEP[6]); cv.p(bx + 1, by, SEP[6]); cv.p(bx, by - 1, SEP[5])
    for (gx, gy) in ((-20, 6), (18, -9), (8, 12), (-28, -6), (30, 4)):
        cv.p(cx + gx, cy + gy, SEP[6] if (gx + f) % 2 else SEP[5])
    cv.rect(cx - 2, cy - 4, cx + 2, cy + 3, SEP[0]); cv.rect(cx - 1, cy - 6, cx + 1, cy - 4, SEP[5])
    cv.rect(x0 + 4, y0 + 4, x0 + 40, y0 + 6, SEP[0]); cv.rect(x0 + 5, y0 + 5, x0 + 5 + (f + 1) * 4, y0 + 5, SEP[6])


def _photo_reload(cv, x0, y0, f):
    for y in range(64):
        for x in range(120):
            cv.p(x0 + x, y0 + y, SEP[5] if y < 14 else SEP[4] if y < 30 else SEP[3] if y < 44 else SEP[4] if cv.dither(x, y, 0.4) else SEP[3])
    for x in range(120):  # compound wall
        top = 30 + (3 if (x // 10) % 3 == 0 else 0)
        for y in range(top, 44): cv.p(x0 + x, y0 + y, SEP[2] if y > top else SEP[3])
    cv.rect(x0 + 10, y0 + 34, x0 + 34, y0 + 56, SEP[2])
    cv.line(x0 + 10, y0 + 34, x0 + 34, y0 + 56, SEP[1]); cv.line(x0 + 34, y0 + 34, x0 + 10, y0 + 56, SEP[1])
    cv.rect(x0 + 10, y0 + 34, x0 + 34, y0 + 34, SEP[4])
    gx, gy = x0 + 70, y0 + 40  # first-person pistol: drop mag, seat a new one, rack, fire
    rack = 3 if f == 6 else 0
    cv.rect(gx - 4 + rack, gy, gx + 34, gy + 6, SEP[0]); cv.line(gx - 4 + rack, gy, gx + 34, gy, SEP[3])
    cv.rect(gx + 20, gy + 6, gx + 30, gy + 22, SEP[1])
    mag_y = {2: 6, 3: 14, 4: 10}.get(f, 0)
    cv.rect(gx + 22, gy + 16 + mag_y, gx + 28, gy + 26 + mag_y, SEP[2]); cv.p(gx + 25, gy + 16 + mag_y, SEP[6])
    cv.rect(gx + 26, gy + 20, gx + 40, gy + 28, SEP[4])  # hand
    if f == 7:
        for (dx, dy) in ((-6, 3), (-8, 2), (-9, 4), (-7, 5), (-10, 3)): cv.p(gx + dx, gy + dy, SEP[6])
    cx, cy = x0 + 50, y0 + 26
    for d in (3, 4):
        for (dx, dy) in ((d, 0), (-d, 0), (0, d), (0, -d)): cv.p(cx + dx, cy + dy, SEP[6])


def _photo_hauler(cv, x0, y0, f):
    for y in range(64):
        for x in range(120): cv.p(x0 + x, y0 + y, SEP[5] if y < 20 else SEP[4])
    for (cx_, cy_) in ((20, 8), (78, 12)):
        ccx = (cx_ - f * 2) % 120
        for d in range(10):
            cv.p(x0 + (ccx + d) % 120, y0 + cy_, SEP[6]); cv.p(x0 + (ccx + 2 + d // 2) % 120, y0 + cy_ - 1, SEP[6])
    cv.rect(x0 + 96, y0 + 5, x0 + 102, y0 + 11, SEP[6])
    for x in range(120):
        top = 40 + round(6 * math.sin((x + f * 4) / 11.0))
        for y in range(top, 64): cv.p(x0 + x, y0 + y, SEP[2] if y < top + 2 else SEP[1])
        if (x + f * 4) % 13 == 0: cv.p(x0 + x, y0 + top - 1, SEP[3])
    hx0 = 64
    base = 40 + round(6 * math.sin((hx0 + 8 + f * 4) / 11.0))
    horse = ["......KK..", ".....KKKK.", "KKKKKKKK..", "KKKKKKKK..", ".KKKKKKK..", ".K.K..K.K.",
             (".K..K.K..K" if f % 2 else "K.K..K.K..")]
    cv.sprite(x0 + hx0, y0 + base - 8, horse, {'K': SEP[0]})
    cart = x0 + hx0 - 26
    cbase = 40 + round(6 * math.sin((hx0 - 18 + f * 4) / 11.0))
    cv.line(cart + 22, y0 + cbase - 6, x0 + hx0 + 1, y0 + base - 5, SEP[0])
    cv.rect(cart, y0 + cbase - 8, cart + 22, y0 + cbase - 3, SEP[0])
    bob = 1 if f % 4 == 1 else 0
    for (kx, kw, kh, lift) in ((2, 6, 6, bob), (9, 6, 5, bob), (5, 5, 4, 6)):
        top = cbase - 8 - kh - lift
        cv.rect(cart + kx, y0 + top, cart + kx + kw, y0 + top + kh, SEP[3]); cv.p(cart + kx, y0 + top, SEP[0])
    for wx in (cart + 4, cart + 18):
        cv.rect(wx - 2, y0 + cbase - 3, wx + 2, y0 + cbase + 1, SEP[0]); cv.p(wx, y0 + cbase - 1, SEP[4])


PROJECTS = [
    dict(key='echosim', name='ECHOSIM', kicker='AUTONOMOUS SOCIAL SIMULATION', vol='VOL. I',
         sub='Residents who remember, plan and befriend one another',
         body=('An engine-independent simulation where needs, utility scoring, GOAP planning, perception and memory '
               'drive every resident. It runs headless; browser clients only read it.'),
         tech='TYPESCRIPT · BABYLON.JS · PHASER', action='READ THE SOURCE ON GITHUB',
         url='https://github.com/KaustuvMohapatra/EchosSim', photo=_photo_echosim),
    dict(key='arena-survivor', name='ARENA SURVIVOR', kicker='UNITY SURVIVAL ARENA', vol='VOL. II',
         sub='Waves, automatic weapons and level-ups',
         body=('A survival arena built around enemy waves, automatic weapons, XP progression and shader work, '
               'with a WebGL build you can play in the browser.'),
         tech='UNITY · C# · SHADERLAB · WEBGL', action='PLAY IN BROWSER',
         url='https://kaustuvm.itch.io/arena-survivor', photo=_photo_arena),
    dict(key='reload', name='RELOAD', kicker='FIRST-PERSON ARCADE SHOOTER', vol='VOL. III',
         sub='The shooter where you reload by hand',
         body=('Drop the magazine, seat the next and rack the slide yourself while enemies close in. Campaign, Time '
               'Attack, Endless and daily modes, for desktop and phone.'),
         tech='TYPESCRIPT · BABYLON.JS · VITE', brewing=True, photo=_photo_reload),
    dict(key='medieval-hauler', name='MEDIEVAL HAULER', kicker='PHYSICS DRIVING GAME', vol='VOL. IV',
         sub='Keep the cargo on the cart',
         body=('A horse pulls a loaded cart over rolling hills, and the cargo is only as safe as your throttle. '
               'Twelve roads, star ratings and saved progress, for browser and Android.'),
         tech='PHASER 4 · TYPESCRIPT · MATTER.JS · CAPACITOR', brewing=True, photo=_photo_hauler),
]


def prophet(p):
    nw, nh = 202, 222

    def draw(rec, f):
        cv = rec.cv
        with rec.step('newsprint'):
            parchment(cv, 0, 0, nw - 1, nh - 1, seed=len(p['key']),
                      ramp=[P['news'][0], P['news'][0], P['news'][1], P['news'][2], P['news'][3]])
            for y in (24, 26, 34, 186):
                for x in range(8, nw - 8): cv.p(x, y, P['ink'] if y != 26 else P['ink2'])
        with rec.step('photo'):
            px0, py0 = 41, 76
            cv.rect(px0 - 4, py0 - 4, px0 + 123, py0 + 67, hx('#f2ead6')); cv.rect(px0 - 1, py0 - 1, px0 + 120, py0 + 64, P['ink'])
            p['photo'](cv, px0, py0, f)
        with rec.step('type'):
            ink = P['ink']
            cv.text(202, 40, 'The Daily Prophet', font('black', 34), ink, anchor='ms')
            cv.text(20, 62, 'SPECIAL EDITION', font('caps', 10), P['ink2'], spacing=1)
            cv.text(384, 62, p['vol'], font('caps', 10), P['ink2'], anchor='rs', spacing=1)
            hs = 34
            while font('bodoni', hs).getlength(p['name']) > 370: hs -= 1
            cv.text(202, 100, p['name'], font('bodoni', hs), ink, anchor='ms')
            cv.text(202, 122, p['kicker'], font('caps', 10), P['red'], anchor='ms', spacing=1.5)
            cv.text(202, 143, p['sub'], font('serifi', 16), P['ink2'], anchor='ms')
            cv.paragraph(20, 302, p['body'], font('serif', 15), ink, 364, 19)
            cv.text(202, 362, p['tech'], font('caps', 11), P['ink2'], anchor='ms', spacing=1)
        with rec.step('action'):
            if p.get('brewing'):
                c = P['red'] if f % 8 < 6 else hx('#b04450')
                cv.rect(36, 192, 165, 214, P['news'][3])
                for x in range(36, 166): cv.p(x, 192, c); cv.p(x, 193, c); cv.p(x, 214, c)
                for y in range(192, 215): cv.p(36, y, c); cv.p(37, y, c); cv.p(165, y, c)
                cv.text(202, 406, 'STILL BREWING', font('caps', 15), c, anchor='ms', spacing=2)
                cv.text(202, 422, 'REPOSITORY NOT YET PUBLIC', font('caps', 9), P['ink2'], anchor='ms', spacing=1)
            else:
                w = font('caps', 13).getlength(p['action']) + 1.2 * len(p['action'])
                tx = 202 - w / 2 + 10
                cv.sprite(int(tx / 2) - 8, 200, ["#..", "##.", "###", "##.", "#.."], {'#': P['red'] if f % 4 < 2 else P['ink']})
                cv.text(tx, 412, p['action'], font('caps', 13), P['red'], spacing=1.2)
    alt = (f"Daily Prophet front page, {p['vol']}: {p['name'].title()}, {p['kicker'].lower()}. {p['sub']}. {p['body']} "
           f"Built with {p['tech'].title()}." + (' Still brewing: repository not yet public.' if p.get('brewing') else ''))
    return layered(f"prophet-{p['key']}", nw, nh, 8, 160, draw, alt)


# ---------------------------------------------------------------- library catalogue cards (archive)
ARCHIVE = [
    ('ai-game-asset-maker', 'AI Game Asset Maker', 'Prompt to generated asset to a playable Pygame loop.',
     'PYTHON · FASTAPI · ELECTRON', 'https://github.com/KaustuvMohapatra/AI-Game-Asset-Maker'),
    ('medlingo', 'MedLingo', 'Gamified medical revision with spaced repetition. Live app.',
     'REACT · SUPABASE · PYTHON', 'https://medlingo-pied.vercel.app/'),
    ('alexai', 'AlexAI', 'A conversational AI assistant.', 'CONVERSATIONAL AI', 'https://github.com/KaustuvMohapatra/AlexAI'),
]


def catalogue_card(key, title, desc, tech):
    nw, nh = 134, 64

    def draw(rec, f):
        cv = rec.cv
        with rec.step('card'):
            cv.rect(0, 0, nw - 1, nh - 1, P['k0']); cv.rect(1, 1, nw - 2, nh - 2, hx('#f1e9d4'))
            for y in range(20, nh - 3, 8):
                for x in range(4, nw - 4): cv.p(x, y, hx('#c8d4dc'))
            for x in range(4, nw - 4): cv.p(x, 12, P['red'])
            cv.rect(nw // 2 - 3, nh - 8, nw // 2 + 3, nh - 4, hx('#d8ccb0')); cv.p(nw // 2, nh - 6, P['k0'])
        with rec.step('type'):
            cv.text(12, 18, 'HOGWARTS LIBRARY  ·  CATALOGUE', font('caps', 8), P['red'], spacing=1)
            cv.text(12, 46, title, font('serifb', 19), P['ink'])
            cv.paragraph(12, 66, desc, font('serifi', 13), P['ink2'], 240, 16)
            cv.text(12, 110, tech, font('caps', 9), P['ink'], spacing=1)
    return layered(f'catalogue-{key}', nw, nh, 1, 100, draw, f'Library catalogue card: {title}. {desc} {tech.title()}.')


# ---------------------------------------------------------------- O.W.L. subject cards (skills)
SUBJECTS = [
    ('transfiguration', 'Transfiguration', 'GAMEPLAY ENGINEERING', 'gamepad',
     'Unity · C# · Godot · Phaser · Babylon.js · Three.js · ShaderLab · WebGL · Matter.js'),
    ('divination', 'Divination', 'ARTIFICIAL INTELLIGENCE', 'crystal',
     'Python · PyTorch · TensorFlow · OpenCV · scikit-learn · NumPy · Pandas · Generative AI · GOAP & utility AI'),
    ('charms', 'Charms', 'WEB & INTERACTIVE', 'wand',
     'React · TypeScript · JavaScript · Next.js · Vite · Tailwind CSS · Capacitor'),
    ('arithmancy', 'Arithmancy', 'BACKEND & SYSTEMS', 'abacus',
     'FastAPI · Flask · Node.js · Celery · PostgreSQL · Supabase · Docker · REST · SQL'),
    ('potions', 'Potions', 'CREATIVE TOOLS', 'cauldron',
     'Aseprite · Blender · Krita · Figma · Git · GitHub · CI/CD · Automated testing'),
]


def subject_card(key, subject, discipline, icon_name, tech):
    nw, nh = 134, 100

    def draw(rec, f):
        cv = rec.cv
        with rec.step('parchment'):
            parchment(cv, 0, 0, nw - 1, nh - 1, seed=len(key) * 3)
            for x in range(6, nw - 6): cv.p(x, 5, P['ink2']); cv.p(x, nh - 6, P['ink2'])
            for y in range(5, nh - 5): cv.p(5, y, P['ink2']); cv.p(nw - 6, y, P['ink2'])
            for (x, y) in ((5, 5), (nw - 6, 5), (5, nh - 6), (nw - 6, nh - 6)):
                for d in (-1, 1): cv.p(x + d, y + d, P['g'][2]); cv.p(x - d, y + d, P['g'][2])
            cv.rect(10, 10, 29, 29, P['em'][1]); cv.rect(11, 11, 28, 28, P['em'][0])
            for x in range(10, 30): cv.p(x, 10, P['g'][3]); cv.p(x, 29, P['g'][1])
            for y in range(10, 30): cv.p(10, y, P['g'][3]); cv.p(29, y, P['g'][1])
            for x in range(10, nw - 10):
                if x % 3: cv.p(x, 36, P['g'][2])
        with rec.step('icon'):
            icon(cv, 12, 12, icon_name)
        with rec.step('type'):
            cv.text(72, 44, subject, font('black', 27), P['ink'])
            cv.text(72, 60, discipline, font('caps', 10), P['red'], spacing=1)
            cv.paragraph(22, 98, tech, font('serif', 15), P['ink'], 224, 20)
    return layered(f'subject-{key}', nw, nh, 1, 100, draw, f'O.W.L. subject card: {subject}, {discipline.title()}: {tech}.')


# ---------------------------------------------------------------- the Marauder's Map (journey)
MAP_STOPS = [  # native x, y of the room centre, label, line
    (64, 70, 'VIT Vellore', 'B.Tech, Computer Science & Engineering'),
    (168, 138, 'TAG Club Tower', 'Senior Core Technical Department Head'),
    (286, 70, 'The Arena', 'Arena Survivor: WebGL build on itch.io'),
    (348, 152, 'The Simulation Wing', 'EchoSim: headless social-simulation engine'),
]
DUNGEON = (66, 172, 'The Slytherin Dungeons', 'Brewing: RELOAD, Medieval Hauler · Project Bloom in design')


def _map_path():
    pts = [(s[0], s[1]) for s in MAP_STOPS] + [(DUNGEON[0], DUNGEON[1])]
    path = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        for (sx, sy, tx, ty) in ((ax, ay, bx, ay), (bx, ay, bx, by)):  # corridor-style elbows
            n = int(max(abs(tx - sx), abs(ty - sy)))
            for i in range(n): path.append((sx + (tx - sx) * i / max(1, n), sy + (ty - sy) * i / max(1, n)))
    return path


def marauders_map():
    nw, nh = 416, 214
    path = _map_path()
    stops = MAP_STOPS + [DUNGEON]

    def draw(rec, f):
        cv = rec.cv
        ink = P['ink2']
        with rec.step('parchment'):
            parchment(cv, 0, 0, nw - 1, nh - 1, seed=8)
            for k in (138, 277):  # fold creases
                for y in range(4, nh - 4, 2): cv.p(k, y, P['parch'][2])
        with rec.step('ink-architecture'):
            for (x, y, _, _) in stops:  # rooms (double ink walls)
                for i in range(-47, 48):
                    cv.p(x + i, y - 12, ink); cv.p(x + i, y + 12, ink)
                    if -45 < i < 45: cv.p(x + i, y - 10, P['parch'][1]); cv.p(x + i, y + 10, P['parch'][1])
                for j in range(-12, 13): cv.p(x - 47, y + j, ink); cv.p(x + 47, y + j, ink)
                cv.rect(x - 3, y + 12, x + 3, y + 12, P['parch'][3])  # doorway
            for x in range(8, 408):
                if x % 3: cv.p(x, 30, ink); cv.p(x, 202, ink)
            cx_, cy_ = 392, 100  # compass rose
            for d in range(-9, 10): cv.p(cx_ + d, cy_, ink); cv.p(cx_, cy_ + d, ink)
            for d in range(-4, 5): cv.p(cx_ + d, cy_ + d, P['parch'][1]); cv.p(cx_ + d, cy_ - d, P['parch'][1])
            cv.p(cx_, cy_ - 10, P['red']); cv.p(cx_, cy_ - 11, P['red'])
        with rec.step('path'):
            for i, (x, y) in enumerate(path):
                if i % 4 == 0: cv.p(x, y, P['parch'][1])
        with rec.step('footprints'):
            n = len(path)
            for k in range(3):  # three walkers, each leaving a short trail of footprints
                head = int((f / 12 + k / 3) * n) % n
                for t in range(4):
                    j = (head - t * 6) % n
                    x, y = path[j]
                    if any(abs(x - rx) < 49 and abs(y - ry) < 14 for (rx, ry, _, _) in stops): continue  # not over room labels
                    x2, y2 = path[(j + 1) % n]
                    ang = math.atan2(y2 - y, x2 - x)
                    side = 1 if t % 2 else -1
                    ox, oy = -math.sin(ang) * 2 * side, math.cos(ang) * 2 * side
                    c = P['ink'] if t < 2 else P['ink2']
                    cv.rect(x + ox - 1, y + oy - 1, x + ox + 1, y + oy + 1, c)  # sole
                    cv.p(x + ox + math.cos(ang) * 3, y + oy + math.sin(ang) * 3, c)  # toes
        with rec.step('labels'):
            cv.text(416, 42, 'I solemnly swear that I am up to no good.', font('script', 28), P['ink'], anchor='ms')
            for (x, y, label, line) in stops:
                X, Y = x * 2, y * 2
                cv.text(X, Y + 6, label, font('hand', 13), P['ink'], anchor='ms')
                lw = font('serifi', 14).getlength(line)
                fx_ = min(max(X, lw / 2 + 14), 832 - lw / 2 - 14)
                cv.text(fx_, Y + 44, line, font('serifi', 14), P['red'], anchor='ms')
    alt = ("Animated Marauder's Map with footprints walking between rooms. I solemnly swear that I am up to no good. "
           + ' '.join(f'{lab}: {ln}.' for _, _, lab, ln in stops))
    return layered('marauders-map', nw, nh, 12, 150, draw, alt)


# ---------------------------------------------------------------- Owl Post (contact)
OWL = {
    0: [".....K......K.........", "....KnK....KnK........", "hh..KnnKKKKnnK.....hh.", ".hhhKnnnnnnnnnKhhhhh..",
        "..hhKnYYnnYYnnKhhh....", "...KnnYKnnKYnnK.......", "...KnnnnWWnnnnK.......", "...KNnnnnnnnnNK.......",
        "....KNnNnNnNnK........", "....KNNnNNnNNK........", ".....KNNNNNNK.........", "......KYYKYY.........."],
    1: ["......................", ".....K......K.........", "....KnK....KnK........", "hhhhKnnKKKKnnKhhhhh...",
        ".hhhKnYYnnYYnnKhhhh...", "...KnnYKnnKYnnK.......", "...KnnnnWWnnnnK.......", "...KNnnnnnnnnNK.......",
        "....KNnNnNnNnK........", "....KNNnNNnNNK........", ".....KNNNNNNK.........", "......KYYKYY.........."],
    2: ["......................", ".....K......K.........", "....KnK....KnK........", "....KnnKKKKnnK........",
        "...KnnYYnnYYnnK.......", "..hKnnYKnnKYnnKh......", ".hhKnnnnWWnnnnKhh.....", "hhhKNnnnnnnnnNKhhh....",
        "hh..KNnNnNnNnK..hh....", "....KNNnNNnNNK........", ".....KNNNNNNK.........", "......KYYKYY.........."],
}


def owl_post():
    nw, nh = 416, 104

    def draw(rec, f):
        cv = rec.cv
        with rec.step('sky'):
            night_sky(cv, 0, nh - 1, f, seed=12, stars=60)
            moon(cv, 386, 26, 12)
        with rec.step('owlery'):
            C = P['castle']
            cv.rect(14, 30, 58, nh - 1, C[1]); cv.rect(14, 30, 15, nh - 1, C[2])
            for j in range(22): cv.line(14 + j, 30 - j, 58 - j, 30 - j, C[1])
            for (wx, wy) in ((28, 46), (42, 64), (24, 80)):
                cv.rect(wx, wy, wx + 3, wy + 5, P['win'][2 if (f + wx) % 5 else 1]); cv.p(wx + 1, wy - 1, P['win'][1])
            for x in range(nw):
                top = nh - 8 + round(2 * math.sin(x / 13))
                for y in range(top, nh): cv.p(x, y, C[0])
        with rec.step('owl'):
            ox = 80 + f * 3
            oy = 30 + [0, 1, 2, 1][f % 4]
            cv.sprite(ox, oy, OWL[[0, 1, 2, 1][f % 4]], {'h': hx('#efe6d2'), 'K': P['k0'], 'n': hx('#8a6a4a'),
                                                       'N': hx('#b08c5c'), 'Y': P['g'][3], 'W': P['g'][2]})
            cv.rect(ox + 6, oy + 13, ox + 13, oy + 17, hx('#f2e6c4'))
            cv.line(ox + 6, oy + 13, ox + 9, oy + 15, P['ink2']); cv.line(ox + 13, oy + 13, ox + 10, oy + 15, P['ink2'])
            cv.p(ox + 10, oy + 16, P['wax'][2])
            for i in range(5):
                cv.p(ox - 3 - i * 5 - (f % 2) * 2, oy + 8 + [0, 2, 1, 3, 1][(i + f) % 5], P['g'][4] if i % 2 == 0 else P['g'][2])
        with rec.step('lettering'):
            cv.text(540, 70, 'Working on a game, an AI tool', font('script', 30), P['parch'][4], anchor='ms', shadow=hx('#000000', 230))
            cv.text(540, 104, 'or an ambitious interactive world?', font('script', 30), P['parch'][4], anchor='ms', shadow=hx('#000000', 230))
            cv.metal_text(540, 160, 'Send an owl.', font('black', 40), anchor='ms')
    return layered('owl-post', nw, nh, 8, 150, draw,
                   'Animated: an owl carrying a sealed letter flies from a castle owlery under the moon. '
                   'Working on a game, an AI tool or an ambitious interactive world? Send an owl.')


# ---------------------------------------------------------------- catalogue
def catalogue():
    """(output subdir, Asset) for every image the README uses."""
    out = [('hero', hero()), ('about', letter()), ('journey', marauders_map()), ('contact', owl_post())]
    out += [('buttons', button(s, label, ic)) for s, label, ic, _ in BUTTONS]
    out += [('sections', banner(*s)) for s in SECTIONS]
    out += [('projects', prophet(p)) for p in PROJECTS]
    out += [('projects', catalogue_card(k, t, d, tech)) for k, t, d, tech, _ in ARCHIVE]
    out += [('skills', subject_card(*s)) for s in SUBJECTS]
    return out
