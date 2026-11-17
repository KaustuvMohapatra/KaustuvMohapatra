"""Original pixel art for the profile: drawn pixel-by-pixel at native resolution.

Every asset is a function returning an `Asset`: named layers x frames of RGBA images at 1x.
`build.py` writes those layers to disk and Aseprite assembles them into editable .aseprite
sources and exports the README images at 3x (nearest-neighbour).
"""
import math
import random
from dataclasses import dataclass, field
from PIL import Image, ImageChops

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
CLEAR = (0, 0, 0, 0)


def hx(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


# ---------------------------------------------------------------- palette (Concept A)
P = dict(
    k0=hx('#0d0a0e'), k1=hx('#1a1419'), k2=hx('#2a2027'),
    sky=[hx(c) for c in ('#0b0c1a', '#12162c', '#1b2140', '#262c52')],
    star=hx('#d9d3c0'), moon=hx('#f2e7c2'),
    stone=[hx(c) for c in ('#1e1619', '#30232a', '#463238', '#644743', '#86644f')],
    floor=[hx(c) for c in ('#251a1c', '#33242a', '#4a3436')],
    wood=[hx(c) for c in ('#1f120e', '#3c2216', '#5a361f', '#b8925a')],
    cloth=hx('#7a2232'), banners=[(hx('#4a1220'), hx('#7a2232')), (hx('#4a1220'), hx('#8c2a34'))],
    ribbon=[hx('#3a0f18'), hx('#6b1a28'), hx('#93303a')],
    g1=hx('#7a4f18'), g2=hx('#b07a24'), g3=hx('#e0aa3e'), g4=hx('#fbe2a0'), wing=hx('#efe6d2'),
    glass=[hx('#121a36'), hx('#22305e')], glow=hx('#5c3a22'), rim=hx('#7a4a26'),
    wax=[hx('#efe0c0'), hx('#bfa982')], flame=[hx('#fff7d0'), hx('#ffbf3c'), hx('#e07a28')],
    hair=[hx('#110c0c'), hx('#2a2024'), hx('#5a4038')],
    scarf=[hx('#1e6b45'), hx('#b8c0c4'), hx('#124430')],
    robe=[hx('#1a1620'), hx('#2a2433'), hx('#3a3246'), hx('#b0703a')],
    skin=[hx('#5a3420'), hx('#8a5434'), hx('#a8704a'), hx('#c48a5e')],
    parch=[hx('#a88a58'), hx('#cfb47c'), hx('#e6d2a2'), hx('#f3e6c4')],
    ink=hx('#3a2414'), ink2=hx('#7d5a38'), waxs=[hx('#5a141e'), hx('#8c2430'), hx('#c4503e')],
)

# ---------------------------------------------------------------- 5x7 bitmap font (original)
_rows = lambda *r: ''.join(r)
FONT = {
    'A': _rows('.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'),
    'B': _rows('####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'),
    'C': _rows('.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'),
    'D': _rows('####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'),
    'E': _rows('#####', '#....', '#....', '####.', '#....', '#....', '#####'),
    'F': _rows('#####', '#....', '#....', '####.', '#....', '#....', '#....'),
    'G': _rows('.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'),
    'H': _rows('#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'),
    'I': _rows('.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'),
    'J': _rows('..###', '...#.', '...#.', '...#.', '#..#.', '#..#.', '.##..'),
    'K': _rows('#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'),
    'L': _rows('#....', '#....', '#....', '#....', '#....', '#....', '#####'),
    'M': _rows('#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'),
    'N': _rows('#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'),
    'O': _rows('.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'),
    'P': _rows('####.', '#...#', '#...#', '####.', '#....', '#....', '#....'),
    'Q': _rows('.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'),
    'R': _rows('####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'),
    'S': _rows('.####', '#....', '#....', '.###.', '....#', '....#', '####.'),
    'T': _rows('#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'),
    'U': _rows('#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'),
    'V': _rows('#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'),
    'W': _rows('#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'),
    'X': _rows('#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'),
    'Y': _rows('#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'),
    'Z': _rows('#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'),
    ' ': '.' * 35, '.': '.' * 30 + '..#..', '·': '.' * 15 + '..#..' + '.' * 15,
    '-': '.' * 15 + '.###.' + '.' * 15, "'": '..#....#..' + '.' * 25,
}
for _k, _v in FONT.items():
    assert len(_v) == 35, _k


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg=CLEAR):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w, h), bg)
        self.px = self.im.load()

    def p(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def g(self, x, y):
        x, y = int(round(x)), int(round(y))
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else CLEAR

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.p(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1):
            self.p(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, c)

    @staticmethod
    def dither(x, y, t):
        return t * 16 > BAYER[int(y) % 4][int(x) % 4]

    def text(self, x, y, msg, color=None, scale=1, shade=None, outline=None):
        cells, cx = [], x
        for ch in msg.upper():
            gl = FONT.get(ch, FONT[' '])
            for r in range(7):
                for col in range(5):
                    if gl[r * 5 + col] == '#':
                        cells.append((cx + col * scale, y + r * scale, r))
            cx += 6 * scale
        if outline:
            for (qx, qy, _) in cells:
                for dx in range(-1, scale + 1):
                    for dy in range(-1, scale + 2):
                        self.p(qx + dx, qy + dy, outline)
        for (qx, qy, r) in cells:
            col = shade[min(len(shade) - 1, r * len(shade) // 7)] if shade else color
            for dx in range(scale):
                for dy in range(scale):
                    self.p(qx + dx, qy + dy, col)
        return cx - x

    @staticmethod
    def tw(msg, scale=1):
        return len(msg) * 6 * scale - scale

    def sprite(self, ox, oy, rows, pal, flip=False):
        for y, row in enumerate(rows):
            row = row[::-1] if flip else row
            for x, ch in enumerate(row):
                if ch != '.':
                    self.p(ox + x, oy + y, pal[ch])

    def outline(self, color, src=None):
        """1px outer outline around every opaque pixel (selective outlines are drawn by hand)."""
        src = src or self.im.copy()
        sp = src.load()
        for y in range(self.h):
            for x in range(self.w):
                if sp[x, y][3] == 0 and any(
                        0 <= x + dx < self.w and 0 <= y + dy < self.h and sp[x + dx, y + dy][3]
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.px[x, y] = color

    def paste(self, other, x, y):
        self.im.alpha_composite(other.im, (int(x), int(y)))


def poly_fill(cv, pts, colfn):
    ys = [q[1] for q in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(int(math.ceil(a)), int(b) + 1):
                cv.p(x, y, colfn(x, y))


def glow(cv, cx, cy, r, warm, strength=0.55):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1 and cv.dither(x, y, (1 - d) * strength):
                c = cv.g(x, y)
                if c[3] and sum(c[:3]) < sum(warm[:3]):
                    cv.p(x, y, warm)


def gothic_window(x0, x1, ytop, ybot, steps=20):
    w = x1 - x0; r = w * 0.85; cxL, cxR = x0 + r, x1 - r; mid = x0 + w / 2
    spring = ytop + w / 2
    pts = []
    aL = math.acos((mid - cxL) / r)
    for i in range(steps + 1):
        a = math.pi - i / steps * (math.pi - aL)
        pts.append((cxL + r * math.cos(a), spring - r * math.sin(a)))
    aR = math.acos((mid - cxR) / r)
    for i in range(steps + 1):
        a = aR * (1 - i / steps)
        pts.append((cxR + r * math.cos(a), spring - r * math.sin(a)))
    off = ytop - min(q[1] for q in pts)
    return [(x0, ybot)] + [(x, y + off) for x, y in pts] + [(x1, ybot)]


# ---------------------------------------------------------------- layered asset container
@dataclass
class Asset:
    name: str
    w: int
    h: int
    frames: int = 1
    duration_ms: int = 100
    scale: int = 3  # export scale; README shows each image at exactly this size
    layers: dict = field(default_factory=dict)  # name -> [Image per frame]
    order: list = field(default_factory=list)

    def composite(self, f=0):
        out = Image.new('RGBA', (self.w, self.h), CLEAR)
        for n in self.order:
            out.alpha_composite(self.layers[n][f])
        return out


class Recorder:
    """Draw a scene step by step; each step's changed pixels become a named layer."""

    def __init__(self, cv):
        self.cv, self.layers, self.order, self._snap = cv, {}, [], None

    def step(self, name):
        rec = self

        class _Ctx:
            def __enter__(s):
                rec._snap = rec.cv.im.copy()

            def __exit__(s, *a):
                after = rec.cv.im
                if not rec.order:
                    layer = after.copy()
                else:
                    diff = ImageChops.difference(after, rec._snap).convert('L').point(lambda v: 255 if v else 0)
                    layer = Image.new('RGBA', after.size, CLEAR)
                    layer.paste(after, (0, 0), diff)
                rec.layers[name] = layer
                rec.order.append(name)
        return _Ctx()


def layered(name, w, h, frames, duration, draw):
    """draw(rec, frame) must call rec.step() with the same names every frame."""
    a = Asset(name, w, h, frames, duration)
    for f in range(frames):
        rec = Recorder(Canvas(w, h))
        draw(rec, f)
        for n in rec.order:
            a.layers.setdefault(n, []).append(rec.layers[n])
        a.order = rec.order
    return a


def single(name, cv, frames=None, duration=100):
    a = Asset(name, cv.w, cv.h, 1 if frames is None else len(frames), duration)
    a.layers['art'] = [cv.im] if frames is None else [c.im for c in frames]
    a.order = ['art']
    return a


# ---------------------------------------------------------------- the wizard (Kaustuv): back view for the hero
def wizard_back(cv, cx, foot, f=0):
    """Medium wavy black hair, glasses, medium-brown skin, Slytherin scarf, wand raised to the right."""
    tmp = Canvas(cv.w, cv.h)
    R0, R1, R2, RIM = P['robe']
    yt = foot - 27  # robe top (shoulders)
    for j in range(28):  # robe body
        y = yt + j
        hw = 4 + min(j, 3) * 1 + j * 0.2 if j > 0 else 4
        for u in range(-int(hw), int(hw) + 1):
            if u <= -int(hw) + 1:
                c = R0
            elif u >= int(hw):
                c = RIM if j > 2 else R1
            elif u == 1 and j > 9:
                c = R2
            elif u in (-3, 4) and j > 14 and j % 7 != 0:
                c = R0
            else:
                c = R1
            tmp.p(cx + u, y, c)
    for u in range(-9, 10):  # hem shadow
        tmp.p(cx + u, foot, R0 if tmp.g(cx + u, foot)[3] else None)
    # left arm hanging (sleeve fold + hand)
    for j in range(3, 16):
        tmp.p(cx - 6 - (1 if j > 6 else 0), yt + j, R0)
    tmp.p(cx - 7, yt + 16, P['skin'][1]); tmp.p(cx - 7, yt + 17, P['skin'][0])
    # scarf: wrap at the neck + one tail down the back with diagonal stripes
    for u in range(-4, 5):
        tmp.p(cx + u, yt - 1, P['scarf'][1] if (u + 1) % 3 == 0 else P['scarf'][0])
        tmp.p(cx + u, yt, P['scarf'][2] if abs(u) == 4 else (P['scarf'][1] if u % 3 == 0 else P['scarf'][0]))
    for j in range(1, 11):
        for u in (-1, 0, 1):
            tmp.p(cx + u - (1 if j > 6 else 0), yt + j, P['scarf'][1] if (j + u) % 4 == 0 else P['scarf'][0])
    tmp.p(cx - 2, yt + 11, P['scarf'][1]); tmp.p(cx, yt + 11, P['scarf'][1])  # fringe
    # neck
    for u in (-1, 0, 1):
        tmp.p(cx + u, yt - 2, P['skin'][1])
    # head: wavy black hair seen from behind
    hcx, hcy = cx, yt - 8
    for y in range(hcy - 7, hcy + 6):
        for x in range(hcx - 7, hcx + 8):
            a = math.atan2(y - hcy, x - hcx)
            r = 5.6 + 0.9 * math.sin(a * 5 + 0.6) + (0.6 if y < hcy - 2 else 0)
            if math.hypot((x - hcx) * 1.0, (y - hcy) * 1.05) <= r:
                c = P['hair'][0]
                if (x + 2 * y) % 5 == 0 and y < hcy + 2: c = P['hair'][1]
                if y < hcy - 3 and (x - y) % 4 == 0: c = P['hair'][1]
                tmp.p(x, y, c)
    for (dx, dy) in ((-6, 4), (-5, 5), (6, 3), (5, 5), (0, 6), (-2, 6), (2, 6)):  # wavy locks at the nape
        tmp.p(hcx + dx, hcy + dy, P['hair'][0])
    tmp.p(hcx + 6, hcy + 1, P['skin'][1])                   # ear
    tmp.p(hcx + 6, hcy - 1, P['g2']); tmp.p(hcx + 7, hcy - 1, P['g2'])  # glasses temple
    for x in range(hcx - 3, hcx + 6):  # warm rim light from the hall on the top of the hair
        top = min((y for y in range(hcy - 8, hcy + 6) if tmp.g(x, y)[3]), default=None)
        if top is not None and (x % 2 == 0 or x > hcx + 2): tmp.p(x, top, P['hair'][2])
    # raised right arm, sleeve widening to a cuff, hand, wand
    sx, sy = cx + 5, yt + 2
    hx_, hy_ = cx + 12, yt - 9
    n = 14
    for i in range(n + 1):
        t = i / n
        x = sx + (hx_ - sx) * t; y = sy + (hy_ - sy) * t
        rad = 1.2 + 0.9 * t
        for oy in range(-2, 3):
            for ox in range(-2, 3):
                if ox * ox + oy * oy <= rad * rad:
                    tmp.p(x + ox, y + oy, RIM if ox >= 1 and oy <= 0 else R1)
    tmp.p(hx_ + 1, hy_ - 2, P['skin'][1]); tmp.p(hx_ + 2, hy_ - 2, P['skin'][2]); tmp.p(hx_ + 1, hy_ - 3, P['skin'][1])
    tip = (hx_ + 7, hy_ - 9)
    tmp.line(hx_ + 2, hy_ - 3, *tip, P['wood'][3])
    tmp.p(hx_ + 2, hy_ - 3, P['wood'][1])
    tmp.outline(P['k0'])
    cv.paste(tmp, 0, 0)
    return tip


# ---------------------------------------------------------------- golden winged orb + spell
def golden_orb(cv, x, y, f):
    up = f % 4 < 2
    wings = ["W.......W", ".WW...WW.", "........."] if up else [".........", ".WW...WW.", "W.......W"]
    cv.sprite(x - 4, y - 1, wings, {'W': P['wing']})
    cv.sprite(x - 1, y - 1, [".o.", "oGg", ".o."], {'o': P['g2'], 'G': P['g4'], 'g': P['g3']})


def spell_points(x0, y0, x1, y1, lift=24, n=70):
    cx, cy = (x0 + x1) / 2, min(y0, y1) - lift
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
             (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1) for t in [i / n for i in range(n + 1)]]


def spell(cv, pts, f, period=4):
    for i, (x, y) in enumerate(pts[:-5]):
        phase = (i - f) % period
        if phase == 0:
            cv.p(x, y, P['g4'])
        elif phase == 1 and i % 2 == 0:
            cv.p(x, y, P['g3'])
        elif i > len(pts) * 0.65 and phase == 2:
            cv.p(x, y, P['g2'])
        if i % 9 == (f * 2) % 9:
            cv.p(x + (2 if i % 2 else -2), y - 2, P['g4'])


# ---------------------------------------------------------------- HERO: the candlelit Great Hall
HW, HH = 288, 112


def _candles(seed, n, bx0, by0, bx1, by1):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        t = rnd.random() ** 1.6
        depth = 1 - t
        x = rnd.uniform(bx0 * (1 - depth) + 14, HW - 14 - (HW - bx1) * (1 - depth))
        y = rnd.uniform(by0 * (1 - depth) + 26, by0 + (by1 - by0) * 0.55 * (1 - depth) + depth * 40 + 6)
        out.append((x, y, depth, rnd.randrange(8)))
    return out


def hero_scene(rec, f):
    cv = rec.cv
    bx0, by0, bx1, by1 = 112, 22, 176, 70
    st, sky, fl = P['stone'], P['sky'], P['floor']
    rnd = random.Random(7)
    with rec.step('ceiling-sky'):
        poly_fill(cv, [(0, 0), (HW - 1, 0), (bx1, by0), (bx0, by0)],
                  lambda x, y: sky[min(3, int(y / by0 * 3 + (0.5 if cv.dither(x, y, (y / by0 * 3) % 1) else 0)))])
    with rec.step('stars'):
        for i in range(80):
            x, y = rnd.randrange(HW), rnd.randrange(by0)
            if (i + f) % 8 == 0: continue  # twinkle off
            cv.p(x, y, P['g4'] if (i * 3 + f) % 16 == 0 else P['star'] if i % 3 else P['sky'][3])
        for k, (sx, sy) in enumerate([(56, 9), (232, 11), (100, 5), (196, 15)]):
            big = (f // 2 + k * 2) % 8 < 4
            cv.p(sx, sy, P['g4'])
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if big else ():
                cv.p(sx + d[0], sy + d[1], P['star'])

    def wall(x, y, left):
        t = (x / bx0) if left else ((HW - 1 - x) / (HW - 1 - bx1))
        k = min(4, 1 + int(t * 2.4))
        course = max(3, int(8 * (1 - t) + 2))
        if y % course == 0 or (x + (y // course) * 5) % (course * 2 + 3) == 0: return st[k - 1]
        return st[k] if cv.dither(x, y, (t * 2.4) % 1) else st[max(1, k - 1)]

    with rec.step('walls'):
        poly_fill(cv, [(0, 0), (bx0, by0), (bx0, by1), (0, HH)], lambda x, y: wall(x, y, True))
        poly_fill(cv, [(HW - 1, 0), (bx1, by0), (bx1, by1), (HW - 1, HH)], lambda x, y: wall(x, y, False))
        poly_fill(cv, [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)],
                  lambda x, y: st[2] if (y % 5 == 0 or (x + (y // 5) * 4) % 9 == 0) else st[3] if cv.dither(x, y, 0.3) else st[2])
    with rec.step('columns-banners'):
        for i in range(1, 7):
            t = 1 - 1 / (1 + 0.42 * i)
            t2 = 1 - 1 / (1 + 0.42 * (i + 1))
            for side in (0, 1):
                X = (lambda tt: tt * bx0) if side == 0 else (lambda tt: HW - 1 - tt * (HW - 1 - bx1))
                x = X(t); top = t * by0; bot = HH - t * (HH - by1)
                wcol = max(1, int(5 * (1 - t))); s = 1 if side == 0 else -1
                for dx in range(wcol):
                    cv.line(x + s * dx, top, x + s * dx, bot, st[4] if dx == 0 else st[3])
                cv.line(x + s * wcol, top, x + s * wcol, bot, st[0])
                xm = X((t + t2) / 2)
                bw = max(2, int(9 * (1 - t))); bh = max(5, int(30 * (1 - t)))
                btop = t * by0 + 6 * (1 - t) + 6
                bc = P['banners'][(i + side) % 2]
                for yy in range(int(btop), int(btop + bh)):
                    for dx in range(-(bw // 2), bw // 2 + 1):
                        if yy <= btop + bh - 1 - (bw // 2 - abs(dx)) * 0.6:
                            cv.p(xm + dx, yy, bc[0] if abs(dx) == bw // 2 else bc[1])
                cv.line(xm - bw // 2 - 1, btop, xm + bw // 2 + 1, btop, P['g2'])
                if bw >= 5:  # original serpent-wave device in gold on the nearest banners
                    for yy in range(int(btop + 3), int(btop + bh * 0.6)):
                        cv.p(xm + round(math.sin((yy - btop) / 1.6)), yy, P['g2'])
    with rec.step('windows-high-table'):
        for (wx0, wx1, wt, wb) in [(133, 155, 26, 60), (119, 127, 34, 58), (161, 169, 34, 58)]:
            arch = gothic_window(wx0, wx1, wt, wb)
            poly_fill(cv, arch, lambda x, y: P['glass'][1] if cv.dither(x, y, 0.55 - (y - wt) / 70) else P['glass'][0])
            for k in range(len(arch) - 1):
                cv.line(*arch[k], *arch[k + 1], P['g1'])
            mx = (wx0 + wx1) // 2
            cv.line(mx, wt + 3, mx, wb, P['g1'])
            if wx1 - wx0 > 12:
                cv.line(wx0, wt + 18, wx1, wt + 18, P['g1'])
                for a, b in ((mx - 5, wt + 9), (mx + 5, wt + 9), (mx - 6, wt + 26), (mx + 4, wt + 24)):
                    cv.p(a, b, P['star'])
                cv.rect(mx - 3, wt + 7, mx - 2, wt + 8, P['moon']); cv.p(mx - 1, wt + 7, P['moon'])
        cv.rect(bx0 + 2, by1 - 6, bx1 - 2, by1 - 4, P['wood'][2])
        cv.rect(bx0 + 2, by1 - 3, bx1 - 2, by1, P['cloth'])
        cv.line(bx0 + 2, by1 - 3, bx1 - 2, by1 - 3, P['g2'])
        for x in range(bx0 + 5, bx1 - 3, 5): cv.p(x, by1 - 7, P['g3'])
    with rec.step('floor-tables'):
        poly_fill(cv, [(bx0, by1), (bx1, by1), (HW - 1, HH), (0, HH)],
                  lambda x, y: fl[1] if cv.dither(x, y, 0.25 + (y - by1) / 140) else fl[0])
        for row in range(1, 9):
            y = by1 + (HH - by1) * (1 - 1 / (1 + 0.18 * row * row))
            t = (y - by1) / (HH - by1)
            cv.line(bx0 - bx0 * t, y, bx1 + (HW - 1 - bx1) * t, y, fl[2])
        for (xb, xf) in [(122, 22), (136, 108), (152, 182), (166, 268)]:
            for y in range(by1 + 2, HH):
                t = (y - by1) / (HH - by1)
                c = xb + (xf - xb) * t; hw = 1 + 7 * t
                for x in range(int(c - hw - 1 - 2 * t), int(c + hw + 2 + 2 * t)): cv.p(x, y, P['wood'][0])
                for x in range(int(c - hw), int(c + hw) + 1):
                    cv.p(x, y, P['wood'][2] if abs(x - c) < hw - 1 else P['wood'][1])
                if y % max(2, int(7 * t + 1)) == 0:
                    cv.p(c - hw * 0.4, y, P['g3']); cv.p(c + hw * 0.4, y, P['wax'][1])
    candles = _candles(11, 110, bx0, by0, bx1, by1)
    with rec.step('candle-glow'):
        for (x, y, depth, ph) in candles:
            glow(cv, x, y - 1, 2 + depth * 5, P['glow'], 0.45)
    with rec.step('candles'):
        for (x, y, depth, ph) in candles:
            hgt = 1 + int(depth * 4); wd = 1 if depth < 0.55 else 2
            cv.rect(x, y, x + wd - 1, y + hgt, P['wax'][0])
            if wd == 2: cv.line(x + 1, y + 1, x + 1, y + hgt, P['wax'][1])
    with rec.step('flames'):
        for (x, y, depth, ph) in candles:
            k = (f + ph) % 8
            cv.p(x, y - 1, P['flame'][1] if k not in (3, 6) else P['flame'][2])
            if depth > 0.5 and k not in (2, 5): cv.p(x + (1 if k == 7 and depth > 0.8 else 0), y - 2, P['flame'][0])
    with rec.step('doorway'):
        jl, jr, top, spring = 10, HW - 11, -10, 58

        def inside(x, y):
            if x < jl or x > jr: return False
            u = abs((x - (jl + jr) / 2) / ((jr - jl) / 2))
            return y >= top + (spring - top) * (1 - math.sqrt(max(0.0, 1 - u)))
        for y in range(HH):
            for x in range(HW):
                if not inside(x, y):
                    e1 = any(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    e2 = any(inside(x + dx, y + dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)))
                    block = (y // 6 + (x // 9) % 2) % 2 and (x + y // 6 * 4) % 9
                    cv.p(x, y, P['rim'] if e1 else P['k2'] if e2 else P['k1'] if block else P['k0'])
    orb = (220 + round(3 * math.sin(2 * math.pi * f / 16)), 50 + round(2 * math.sin(4 * math.pi * f / 16)))
    with rec.step('wizard'):
        tip = wizard_back(cv, 40, 111, f)
    with rec.step('spell'):
        spell(cv, spell_points(tip[0], tip[1], orb[0] - 2, orb[1], lift=26), f)
        glow(cv, tip[0], tip[1], 4 + (f % 4 < 2), P['g1'], 0.7)
        cv.p(*tip, P['g4'])
    with rec.step('golden-orb'):
        glow(cv, orb[0], orb[1], 6, P['g1'], 0.5)
        golden_orb(cv, *orb, f)
    with rec.step('title-ribbon'):
        title = 'KAUSTUV MOHAPATRA'
        tw = Canvas.tw(title, 2); tx = (HW - tw) // 2; ty = 7
        rb = P['ribbon']
        for s, x in ((-1, tx - 10), (1, tx + tw + 9)):  # folded, forked tails
            for d in range(1, 8):
                for yy in range(ty + 1, ty + 19):
                    if not abs(yy - (ty + 10)) < d - 3:
                        cv.p(x + s * d, yy + 3, rb[0] if d > 1 else P['k0'])
        cv.rect(tx - 10, ty - 4, tx + tw + 9, ty + 16, rb[1])
        cv.line(tx - 10, ty - 4, tx + tw + 9, ty - 4, rb[2]); cv.line(tx - 10, ty + 16, tx + tw + 9, ty + 16, rb[0])
        cv.line(tx - 8, ty - 2, tx + tw + 7, ty - 2, P['g2']); cv.line(tx - 8, ty + 14, tx + tw + 7, ty + 14, P['g2'])
        cv.text(tx, ty, title, scale=2, shade=[P['g4'], P['g3'], P['g3'], P['g2'], P['g2'], P['g1'], P['g1']], outline=P['k0'])
        # glint sweeping across the gold letters (1 pixel diagonal, every 16 frames)
        gx = tx - 20 + f * (tw + 40) // 16
        for d in range(14):
            x, y = gx + d // 2, ty + 13 - d
            if cv.g(x, y)[:3] in (P['g3'][:3], P['g2'][:3]): cv.p(x, y, P['g4'])


def hero():
    return layered('hero', HW, HH, 16, 110, hero_scene)


# ---------------------------------------------------------------- 16x16 emblems and skill icons
ICON_PAL = {'K': P['k0'], 'g': P['g2'], 'G': P['g3'], 'Y': P['g4'], 'p': P['parch'][2], 'P': P['parch'][3],
            'q': P['parch'][1], 'r': P['ribbon'][1], 'R': P['ribbon'][2], 'i': P['ink'], 'e': P['scarf'][0],
            'E': hx('#33975e'), 's': P['scarf'][1], 'w': P['wood'][2], 'W': P['wood'][3], 'b': P['glass'][1],
            'B': hx('#5a7ab8'), 'c': hx('#9ad0f0'), 'o': hx('#6a4a2e'), 'f': P['flame'][1], 'F': P['flame'][0],
            'm': P['stone'][2], 'M': P['stone'][4], 'h': P['wing'], 'n': hx('#8a6a4a'), 'N': hx('#b08c5c'),
            'v': hx('#4f3d6a'), 'V': hx('#8f78c0'), 'x': P['k2']}
ICONS = {
    'scroll': ["................", "..KKKKKKKKKKKK..", ".KqpPPPPPPPPPpK.", ".KqKKKKKKKKKKqK.", "..KpPPPPPPPPpK..",
               "..KpiiiiiiiPpK..", "..KpPPPPPPPPpK..", "..KpiiiiiPPPpK..", "..KpPPPPPPPPpK..", "..KpiiiiiiPPpK..",
               "..KpPPPPPPrrpK..", "..KpiiiPPrRRrK..", ".KqKKKKKKrrKKqK.", ".KqpPPPPPPPPPpK.", "..KKKKKKKKKKKK..",
               "................"],
    'book': ["................", "................", ".KKKKKK..KKKKKK.", "KpPPPPPKKPPPPPpK", "KpiiiiPKKPiiiipK",
             "KpPPPPPKKPPPPPpK", "KpiiiPPKKPiiiPpK", "KpPPPPPKKPPPPPpK", "KpiiiiPKKPiiiipK", "KpPPPPPKKPPPPPpK",
             "KpiiPPPKKPPiiPpK", "KqpPPPPKKPPPPpqK", "KKKqqqqKKqqqqKKK", ".KrrKKKKKKKKKKK.", "..KR............",
             "................"],
    'wand': ["............Y...", "...........YGY..", "..Y.........Y...", ".YGY.....Y......", "..Y.....KWK.....",
             "........KWK.....", ".......KWK......", "......KWK...Y...", ".....KwK...YGY..", "....KwK.....Y...",
             "...KwK..........", "..KwgK..........", ".KwgK...........", "KwwK............", "KKK.............",
             "................"],
    'map': ["................", "KKKKKKKKKKKKKKKK", "KpPpqpPPqPPpPPpK", "KpPoPpPPqPPPPPpK", "KpoooPPpqPPoPPpK",
            "KpPoPPPPqPoooPpK", "KpPPPoPPqPPoPPpK", "KpPPoooPqPPPPPpK", "KpPPPoPPqPPPoPpK", "KpPPPPPPqPPoooPK",
            "KpPoPPPPqPPPoPpK", "KpoooPPPqPPPPPpK", "KpPoPPPPqPPPPPpK", "KqqqqqqqKqqqqqqK", "KKKKKKKKKKKKKKKK",
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
    'mirror': ["................", "....KKKKKKKK....", "...KGGGGGGGGK...", "..KGKKKKKKKKGK..", "..KGKbbbcbbKGK..",
               "..KGKbBbbcbKGK..", "..KGKbbBbbbKGK..", "..KGKbbbbBbKGK..", "..KGKVbbbbbKGK..", "..KGKbVbbbbKGK..",
               "..KGKKKKKKKKGK..", "...KGGGGGGGGK...", ".....KKggKK.....", "....KgggggggK...", "....KKKKKKKKK...",
               "................"],
    'cauldron': ["................", "....E...E.......", "...E..E...E.....", ".....E..E..E....", "...KKKKKKKKKK...",
                 "..KxEEeEEeEExK..", ".KKKKKKKKKKKKKK.", ".KxxmxxxxxxxmxK.", ".KxmxxxxxxxxxxK.", ".KxxxxxxxxxxxxK.",
                 "..KxxxxxxxxxxK..", "...KKKKKKKKKK...", "...KfK.KfK.KfK..", "..KFfK.KFfKKFfK.", "................",
                 "................"],
    'quill': ["...........hhK..", "..........hhhK..", ".........hhhK...", "........hhhK....", ".......hhhK.....",
              "......hhhK......", ".....hhhK.......", "....hhhK........", "....KhK.........", "...KKK..........",
              "..KiK...........", ".KKKKKK.........", ".KbbbbK.........", ".KbBbbK.........", ".KKKKKK.........",
              "................"],
}


def icon(name):
    cv = Canvas(16, 16)
    cv.sprite(0, 0, ICONS[name], ICON_PAL)
    return cv


# ---------------------------------------------------------------- chapter plates (transparent, gold filigree)
def chapter_plate(numeral, emblem):
    w, h = 288, 22
    cv = Canvas(w, h)
    mid = w // 2
    label = f'CHAPTER {numeral}' if numeral else 'FINALE'
    tw = Canvas.tw(label)
    # emblem in a gold-rimmed medallion
    for y in range(h):
        for x in range(mid - 11, mid + 12):
            d = math.hypot(x - mid + 0.5, y - 10.5)
            if d <= 10.5: cv.p(x, y, P['k1'] if d < 9.5 else P['g2'])
    cv.paste(icon(emblem), mid - 8, 3)
    # filigree arms with curls and diamonds
    for s in (-1, 1):
        x0 = mid + s * 13
        x_end = mid + s * 130
        for x in range(min(x0, x_end), max(x0, x_end) + 1):
            cv.p(x, 10, P['g2'] if x % 7 else P['g3'])
        for k, off in enumerate((24, 70)):
            dx = mid + s * (13 + off)
            cv.p(dx, 8, P['g3']); cv.p(dx - 1, 9, P['g3']); cv.p(dx + 1, 9, P['g3'])
            cv.p(dx, 12, P['g3']); cv.p(dx - 1, 11, P['g3']); cv.p(dx + 1, 11, P['g3']); cv.p(dx, 10, P['g4'])
        for i in range(10):  # curl at the end
            a = i / 10 * 2 * math.pi
            cv.p(x_end + s * (2 + round(2.5 * math.cos(a))), 10 + round(2.5 * math.sin(a)) - 1, P['g2'])
    # label text on the right arm, numeral plate style
    lx = mid + 30
    cv.rect(lx - 3, 6, lx + tw + 2, 14, P['k1'])
    cv.text(lx, 7, label, shade=[P['g4'], P['g3'], P['g3'], P['g2']])
    cv.outline(P['k0'])
    return cv


# ---------------------------------------------------------------- dossier card + front portrait (Chapter I)
PORTRAIT = [  # 32 x 34; glasses, light stubble, medium wavy black hair, medium-brown skin
    "..........h..hh..h..............",
    "........hhhhhhhhhhhh............",
    "......hhhHhhhhhHhhhhhh..........",
    ".....hhhhhHhhhhhHhhhhhhh........",
    "....hhhHhhhhhhhhhhhHhhhhh.......",
    "....hhhhhhhhhhhhhhhhhhhhhh......",
    "...hhhhhhhhhhhhhhhhhhhhhhh......",
    "...hhhhhkhhhhkkhhhhhkkhhhhh.....",
    "...hhhhkkkkhkkkkkkkkkkkhhhh.....",
    "...hhhkkkkkkkkkkkkkkkkkkhhh.....",
    "...hhkkhhhhkkkkkkhhhhkkkkhh.....",
    "...hhkGGGGGGGkkGGGGGGGkkkhh.....",
    "..hkkGcbeebbGGGGcbeebbGkkkkh....",
    "..hkkGbbeebbGkkGbbeebbGkkkkh....",
    "...kkGGGGGGGGkkGGGGGGGGkkkk.....",
    "...jkkkkkkkkkknkkkkkkkkkkkK.....",
    "...jkkkkkkkkknnkkkkkkkkkkkK.....",
    "....kkkkkkkkkknnkkkkkkkkkK......",
    "....Kkkzkkkkkkkkkkkkkkzkkk......",
    ".....kzkzkkmMMMMMmkkkzkzK.......",
    ".....Kkzkzkkkkkkkkkzkzkk........",
    "......KkzkzkzkzkzkzkzkK.........",
    ".......KKkkkkkkkkkkkKK..........",
    "..........KkkkkkkkK.............",
    "..........KkkkkkkkK.............",
    "......eesseessEeesseess.........",
    "....rReeeesseeEEeesseeeRr.......",
    "...rRRRReeesseeeesseeeRRRRr.....",
    "..rRRRRRRreeessseeeeRRRRRRRr....",
    "..rRRRRRRRreeeesseeRRRRRRRRRr...",
    ".rRRRRRRRRRreeesseRRRRRRRRRRRr..",
    ".rRRRRRRRRRRreessRRRRRRRRRRRRr..",
    "rRRRRRRRRRRRRreesRRRRRRRRRRRRRr.",
    "rRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRr",
]
PORTRAIT_PAL = {'h': P['hair'][0], 'H': P['hair'][2], 'k': P['skin'][1], 'j': P['skin'][2], 'K': P['skin'][0],
                'n': P['skin'][0], 'z': P['skin'][0], 'G': P['k0'], 'e': P['k0'], 'b': P['skin'][2],
                'c': hx('#dfe8ee'), 'm': P['skin'][0], 'M': hx('#6a3a2a'), 's': P['scarf'][1],
                'E': P['scarf'][2], 'r': P['robe'][0], 'R': P['robe'][1]}
PORTRAIT_PAL['e'] = P['scarf'][0]  # scarf green (eyes are drawn below, separately)


def portrait(cv, ox, oy):
    rows = [r.ljust(32, '.') for r in PORTRAIT]
    pal = dict(PORTRAIT_PAL)
    tmp = Canvas(cv.w, cv.h)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.': continue
            c = pal[ch]
            if y in (12, 13) and ch == 'e': c = P['k0']  # eyes inside the lenses
            tmp.p(ox + x, oy + y, c)
    tmp.outline(P['k0'])
    cv.paste(tmp, 0, 0)


def dossier():
    w, h = 124, 140

    def draw(rec, f):
        cv = rec.cv
        with rec.step('parchment'):
            cv.rect(0, 0, w - 1, h - 1, P['parch'][2])
            for y in range(h):
                for x in range(w):
                    n = math.sin(x * 0.09 + y * 0.05) + math.sin(x * 0.031 - y * 0.12)
                    if n > 1.3 and cv.dither(x, y, 0.5): cv.p(x, y, P['parch'][1])
                    if n < -1.5 and cv.dither(x, y, 0.4): cv.p(x, y, P['parch'][3])
            rnd = random.Random(4)
            for x in range(w):
                for y in range(rnd.randint(0, 1)): cv.p(x, y, P['parch'][0]); cv.p(x, h - 1 - y, P['parch'][0])
            for y in range(h):
                for x in range(rnd.randint(0, 1)): cv.p(x, y, P['parch'][0]); cv.p(w - 1 - x, y, P['parch'][0])
        with rec.step('frame-ornament'):
            for x in range(4, w - 4):
                cv.p(x, 4, P['ink2'] if x % 4 else P['g2']); cv.p(x, h - 5, P['ink2'] if x % 4 else P['g2'])
            for y in range(4, h - 4):
                cv.p(4, y, P['ink2'] if y % 4 else P['g2']); cv.p(w - 5, y, P['ink2'] if y % 4 else P['g2'])
            for (x, y) in ((4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5)):
                for d in (-1, 1): cv.p(x + d, y, P['g3']); cv.p(x, y + d, P['g3'])
            label = 'STUDENT DOSSIER'
            cv.text((w - Canvas.tw(label)) // 2, 9, label, P['ink'])
            cv.line(10, 18, w - 11, 18, P['waxs'][1])
        with rec.step('photo'):
            px, py = 38, 24
            cv.rect(px - 3, py - 3, px + 50, py + 56, hx('#efe6d0'))
            cv.line(px - 2, py + 57, px + 51, py + 57, P['parch'][0]); cv.line(px + 51, py - 2, px + 51, py + 57, P['parch'][0])
            # candlelit backdrop: the Great Hall's banners and a few candles behind the portrait
            for y in range(py, py + 54):
                for x in range(px, px + 48):
                    cv.p(x, y, P['stone'][2] if cv.dither(x, y, 0.35 + (y - py) / 160) else P['stone'][1])
            for bxp in (px + 3, px + 41):
                cv.rect(bxp, py, bxp + 3, py + 16, P['banners'][0][1]); cv.p(bxp + 1, py + 17, P['banners'][0][1]); cv.p(bxp + 2, py + 17, P['banners'][0][1])
            for (cx_, cy_) in ((px + 10, py + 22), (px + 38, py + 18), (px + 44, py + 30)):
                glow(cv, cx_, cy_, 3, P['glow'], 0.5)
                cv.p(cx_, cy_, P['wax'][0]); cv.p(cx_, cy_ + 1, P['wax'][0])
                cv.p(cx_, cy_ - 1, P['flame'][1] if (f + cx_) % 3 else P['flame'][2])
            portrait(cv, px + 8, py + 20)
            for y in range(py, py + 54):  # clip portrait to the photo window
                for x in range(px + 48, px + 52):
                    pass
        with rec.step('name-plate'):
            name = 'KAUSTUV MOHAPATRA'
            cv.rect(8, 87, w - 9, 97, P['ribbon'][1])
            cv.line(8, 87, w - 9, 87, P['ribbon'][2]); cv.line(8, 97, w - 9, 97, P['ribbon'][0])
            cv.text((w - Canvas.tw(name)) // 2, 89, name, shade=[P['g4'], P['g3'], P['g3'], P['g2']])
            fields = [('HOUSE', 'SLYTHERIN'), ('STUDIES', 'B.TECH CSE'), ('CRAFT', 'GAMES · AI')]
            for i, (k, v) in enumerate(fields):
                y = 102 + i * 10
                cv.text(12, y, k, P['ink2'])
                cv.text(58, y, v, P['ink'])
        with rec.step('seal'):
            cx_, cy_, r = 88, 76, 8  # pressed onto the photo's corner
            for y in range(cy_ - r, cy_ + r + 1):
                for x in range(cx_ - r, cx_ + r + 1):
                    d = math.hypot(x - cx_, y - cy_) + 0.6 * math.sin(math.atan2(y - cy_, x - cx_) * 7)
                    if d <= r:
                        cv.p(x, y, P['waxs'][2] if d < r - 2 and (x - cx_) + (y - cy_) < -3 else P['waxs'][1] if d < r - 1 else P['waxs'][0])
            for i in range(11):  # original serpent mark (not an official crest)
                cv.p(cx_ + round(2.2 * math.sin(i / 1.6)), cy_ - 5 + i, P['waxs'][0])
            cv.p(cx_ + 1, cy_ - 5, P['waxs'][2]); cv.p(cx_ + 2, cy_ - 6, P['waxs'][0])
    a = layered('dossier', w, h, 1, 100, draw)
    a.scale = 2  # shown at 248px beside text-sized content; 2x keeps pixels square
    return a


# ---------------------------------------------------------------- project spellbook pages
PW, PH = 140, 52


def _vignette_echosim(cv, x0, y0):
    cv.rect(x0, y0, x0 + 53, y0 + 31, hx('#1b2140'))
    for i, (sx, sy) in enumerate(((x0 + 6, y0 + 3), (x0 + 30, y0 + 5), (x0 + 47, y0 + 2), (x0 + 18, y0 + 8))):
        cv.p(sx, sy, P['star'])
    cv.rect(x0 + 44, y0 + 3, x0 + 46, y0 + 5, P['moon'])
    cv.rect(x0, y0 + 24, x0 + 53, y0 + 31, hx('#2f4a32'))
    for i, hxp in enumerate((x0 + 3, x0 + 21, x0 + 39)):
        cv.rect(hxp, y0 + 15, hxp + 10, y0 + 24, hx('#8a6a4a'))
        for d in range(6): cv.line(hxp - 1 + d, y0 + 15 - d, hxp + 11 - d, y0 + 15 - d, P['ribbon'][1])
        cv.p(hxp + 3, y0 + 18, P['g3']); cv.p(hxp + 4, y0 + 18, P['g3']); cv.rect(hxp + 7, y0 + 20, hxp + 8, y0 + 24, P['wood'][1])
        rx = hxp + 5
        cv.rect(rx, y0 + 26, rx, y0 + 28, P['robe'][2]); cv.p(rx, y0 + 25, P['skin'][1])
        bub = ["KKKKK", "KhhhK", "KhGhK", "KKKKK", "..K..", ".K..."][:5]
        cv.sprite(rx + 1, y0 + 3 + (i % 2) * 2, ["hhhhh", "hhhhh", "hhhhh", "..h..", ".h..."], {'h': P['wing']})
        cv.p(rx + 2 + (i % 2), y0 + 4 + (i % 2) * 2, [P['ribbon'][2], P['scarf'][0], P['g2']][i])
    cv.line(x0 + 10, y0 + 27, x0 + 44, y0 + 27, P['g2'])  # relationship thread


def _vignette_arena(cv, x0, y0):
    cv.rect(x0, y0, x0 + 53, y0 + 31, P['stone'][1])
    cx, cy = x0 + 27, y0 + 16
    for y in range(y0, y0 + 32):
        for x in range(x0, x0 + 54):
            d = math.hypot((x - cx) / 1.6, y - cy)
            if d < 14: cv.p(x, y, hx('#c9a46a') if cv.dither(x, y, 0.7) else hx('#a8844e'))
            elif d < 15.2: cv.p(x, y, P['stone'][3])
    for a in range(0, 360, 30):
        ex = cx + round(19 * math.cos(math.radians(a)) * 1.0); ey = cy + round(10 * math.sin(math.radians(a)))
        cv.rect(ex, ey, ex + 1, ey + 1, hx('#b03a3a')); cv.p(ex, ey, hx('#e06a5a'))
    for (gx, gy) in ((cx - 8, cy + 4), (cx + 9, cy - 5), (cx + 4, cy + 7), (cx - 10, cy - 6)):
        cv.p(gx, gy, hx('#5ad0e0')); cv.p(gx, gy - 1, hx('#b8f0f8'))
    for a in (20, 140, 260):
        cv.line(cx, cy, cx + 9 * math.cos(math.radians(a)), cy + 5 * math.sin(math.radians(a)), P['g4'])
    cv.rect(cx - 1, cy - 2, cx + 1, cy + 1, P['robe'][2]); cv.p(cx, cy - 3, P['skin'][1]); cv.p(cx, cy - 2, P['scarf'][0])
    cv.rect(x0 + 2, y0 + 2, x0 + 17, y0 + 3, P['k0']); cv.rect(x0 + 2, y0 + 2, x0 + 12, y0 + 3, hx('#5ad0e0'))  # XP bar


def _vignette_reload(cv, x0, y0):
    for y in range(y0, y0 + 20):
        c = [hx('#f0b060'), hx('#e08a48'), hx('#b05a3a')][min(2, (y - y0) // 7)]
        for x in range(x0, x0 + 54): cv.p(x, y, c)
    cv.rect(x0 + 40, y0 + 3, x0 + 44, y0 + 7, hx('#fff0c0'))
    for x in range(x0, x0 + 54):  # compound wall silhouette
        top = y0 + 14 + (2 if (x // 6) % 3 == 0 else 0)
        for y in range(top, y0 + 20): cv.p(x, y, hx('#7a4a32'))
    cv.rect(x0, y0 + 20, x0 + 53, y0 + 31, hx('#d0a060'))
    for x in range(x0, x0 + 54, 3): cv.p(x + (x % 2), y0 + 24 + x % 4, hx('#b88a4e'))
    cv.rect(x0 + 6, y0 + 15, x0 + 20, y0 + 27, hx('#8a5a2a')); cv.rect(x0 + 6, y0 + 15, x0 + 20, y0 + 15, hx('#b07a3a'))
    cv.line(x0 + 6, y0 + 15, x0 + 20, y0 + 27, hx('#6a4220')); cv.line(x0 + 20, y0 + 15, x0 + 6, y0 + 27, hx('#6a4220'))
    gx, gy = x0 + 33, y0 + 21  # pistol (first-person, bottom right) with the magazine dropping out
    cv.rect(gx, gy, gx + 14, gy + 3, P['k2']); cv.rect(gx + 8, gy + 3, gx + 12, gy + 10, P['k2'])
    cv.line(gx, gy, gx + 14, gy, hx('#6a6a72'))
    cv.rect(gx + 9, gy + 13, gx + 11, gy + 17, hx('#4a4a52')); cv.p(gx + 10, gy + 13, P['g3'])
    cv.p(gx + 12, gy + 11, P['g4']); cv.p(gx + 7, gy + 12, P['g4'])
    cv.rect(gx + 11, gy + 8, gx + 14, gy + 10, P['skin'][1])
    cx, cy = x0 + 26, y0 + 12
    for d in (2, 3): cv.p(cx + d, cy, P['wing']); cv.p(cx - d, cy, P['wing']); cv.p(cx, cy + d, P['wing']); cv.p(cx, cy - d, P['wing'])


def _vignette_hauler(cv, x0, y0):
    for y in range(y0, y0 + 32):
        c = [hx('#7ab8d8'), hx('#a8d0e0'), hx('#e8dcb0')][min(2, (y - y0) // 8)]
        for x in range(x0, x0 + 54): cv.p(x, y, c)
    cv.rect(x0 + 6, y0 + 4, x0 + 10, y0 + 8, hx('#fff0a0'))
    for x in range(x0, x0 + 54):
        top = y0 + 21 + round(4 * math.sin((x - x0) / 7.0))
        for y in range(top, y0 + 32): cv.p(x, y, hx('#5a8a3a') if y < top + 2 else hx('#3f6a2c'))
        if (x - x0) % 9 == 0: cv.p(x, top - 1, hx('#7aaa4a'))
    hx0 = x0 + 30; base = y0 + 20 + round(4 * math.sin((hx0 - x0) / 7.0))
    horse = ["....KK..", "...KnnK.", "KKKnnK..", "KnnnnK..", "KnnnnnK.", ".K.K.K.K"]
    cv.sprite(hx0, base - 6, horse, {'K': P['k0'], 'n': hx('#7a4a2a')})
    cx = hx0 - 16
    cv.line(cx + 12, base - 3, hx0 + 1, base - 3, P['wood'][1])
    cv.rect(cx, base - 6, cx + 12, base - 2, P['wood'][2]); cv.line(cx, base - 6, cx + 12, base - 6, P['wood'][3])
    for (kx, ky, kc) in ((cx + 1, base - 10, hx('#b07a3a')), (cx + 6, base - 9, hx('#8a5a2a')), (cx + 4, base - 13, P['ribbon'][2])):
        cv.rect(kx, ky, kx + 3, ky + 3, kc); cv.p(kx, ky, P['k0'])
    for wx in (cx + 2, cx + 10):
        cv.rect(wx - 1, base - 1, wx + 1, base + 1, P['k0']); cv.p(wx, base, P['wood'][3])


VIGNETTES = {'echosim': _vignette_echosim, 'arena-survivor': _vignette_arena, 'reload': _vignette_reload,
             'medieval-hauler': _vignette_hauler}


def project_page(key, title, volume, stamp=None):
    def draw(rec, f):
        cv = rec.cv
        with rec.step('book'):
            cv.rect(1, 2, PW - 2, PH - 2, P['ribbon'][0])  # leather cover edge
            cv.rect(4, 3, PW - 5, PH - 4, P['parch'][3]); cv.rect(4, 3, PW // 2 - 1, PH - 4, P['parch'][2])
            for y in range(3, PH - 3):  # page curvature shading toward the spine
                cv.p(PW // 2 - 2, y, P['parch'][1]); cv.p(PW // 2 + 1, y, P['parch'][2])
            cv.line(PW // 2, 3, PW // 2, PH - 4, P['parch'][0])
            for x in range(5, PW - 5, 2): cv.p(x, PH - 3, P['parch'][1])
            for (x, y) in ((1, 2), (PW - 2, 2), (1, PH - 2), (PW - 2, PH - 2)):  # gold corner guards
                for d in range(4):
                    cv.p(x + (d if x < 5 else -d), y, P['g3']); cv.p(x, y + (d if y < 5 else -d), P['g3'])
        with rec.step('illustration'):
            cv.rect(8, 7, 65, 42, P['ink'])
            vig = Canvas(54, 32)  # vignettes are clipped to their frame
            VIGNETTES[key](vig, 0, 0)
            cv.paste(vig, 10, 9)
            cv.line(9, 43, 65, 43, P['parch'][0])
        with rec.step('lettering'):
            tx = 76
            lines = title.split() if Canvas.tw(title) > PW - tx - 8 else [title]
            for i, ln in enumerate(lines):
                cv.text(tx, 8 + i * 9, ln, P['ink'])
            yl = 8 + len(lines) * 9
            cv.line(tx, yl, tx + max(Canvas.tw(l) for l in lines), yl, P['g2'])
            cv.text(tx, yl + 4, volume, P['ink2'])
            if not stamp:
                for i in range(3):
                    cv.line(tx, yl + 16 + i * 3, PW - 12 - i * 11, yl + 16 + i * 3, P['parch'][1])
        with rec.step('ribbon-bookmark'):
            cv.rect(PW - 14, 0, PW - 11, 14, P['ribbon'][2])
            cv.p(PW - 14, 15, P['ribbon'][2]); cv.p(PW - 11, 15, P['ribbon'][2])
        if stamp:
            with rec.step('stamp'):
                sw = Canvas.tw(stamp) + 6
                sx, sy = 64 - sw, 31  # stamped over the illustration's corner
                for x in range(sx, sx + sw):
                    cv.p(x, sy, P['waxs'][1]); cv.p(x, sy + 10, P['waxs'][1])
                for y in range(sy, sy + 11):
                    cv.p(sx, y, P['waxs'][1]); cv.p(sx + sw - 1, y, P['waxs'][1])
                cv.rect(sx + 1, sy + 1, sx + sw - 2, sy + 9, P['parch'][3])
                cv.text(sx + 3, sy + 2, stamp, P['waxs'][1])
    return layered(f'page-{key}', PW, PH, 1, 100, draw)


# ---------------------------------------------------------------- Send an owl (animated footer)
BODY = ["......KnnnWWnnnK......", "......KNnnnnnnNK......", ".......KNnNnNnK.......", ".......KNNnNNNK.......",
        "........KNNNNK........", ".........KYYK.........."]
OWL_UP = ["hh..................hh", ".hhh....K....K....hhh.", "..hhhh..KKKKKK..hhhh..", "...hhhhKnnnnnnKhhhh...",
          "....hhKnYYnnYYnKhh....", "......KnYKnnKYnK......"] + BODY
OWL_MID = ["......................", "........K....K........", "........KKKKKK........", "hhhhhhhKnnnnnnKhhhhhhh",
           ".hhhhhKnYYnnYYnKhhhhh.", "......KnYKnnKYnK......"] + BODY
OWL_DOWN = ["......................", "........K....K........", "........KKKKKK........", ".......KnnnnnnK.......",
            "....hhKnYYnnYYnKhh....", "..hhhhKnYKnnKYnKhhhh..", ".hhhh.KnnnWWnnnK.hhhh.", "hhh...KNnnnnnnNK...hhh",
            "hh.....KNnNnNnK.....hh", ".......KNNnNNNK.......", "........KNNNNK........", ".........KYYK........."]


def owl_scene(rec, f):
    cv = rec.cv
    w, h = 160, 52
    rnd = random.Random(5)
    with rec.step('night'):
        for y in range(h):
            for x in range(w):
                cv.p(x, y, P['sky'][min(3, int(y / h * 3 + (0.5 if cv.dither(x, y, (y / h * 3) % 1) else 0)))])
        cv.rect(126, 6, 132, 12, P['moon']); cv.rect(125, 7, 133, 11, P['moon']); cv.rect(129, 7, 132, 10, P['star'])
    with rec.step('stars'):
        for i in range(26):
            x, y = rnd.randrange(w), rnd.randrange(h - 12)
            if (i + f) % 5: cv.p(x, y, P['star'] if i % 4 else P['g4'])
    with rec.step('towers'):  # distant castle towers silhouette, a single lit window
        for (tx, tw_, th) in ((6, 8, 22), (18, 6, 15), (136, 7, 19), (148, 9, 26)):
            cv.rect(tx, h - th, tx + tw_ - 1, h - 1, P['k1'])
            for d in range(tw_ // 2 + 2): cv.line(tx - 1 + d, h - th - d, tx + tw_ - d, h - th - d, P['k1'])
        cv.p(10, h - 14, P['g3']); cv.p(151, h - 18, P['g3']); cv.p(151, h - 17, P['g3'])
    with rec.step('owl'):
        sprite = [OWL_UP, OWL_MID, OWL_DOWN, OWL_MID][f % 4]
        ox, oy = 69, 12 + [0, 1, 2, 1][f % 4] - (1 if f >= 4 else 0)
        cv.sprite(ox, oy, sprite, {'h': P['wing'], 'K': P['k0'], 'n': hx('#8a6a4a'), 'N': hx('#b08c5c'),
                                  'Y': P['g3'], 'W': P['g2'], 'p': P['parch'][3], 'P': P['waxs'][1]})
        cv.sprite(ox + 7, oy + 12, [".KKKKK.", "KpPPPpK", "KpPrPpK", ".KKKKK."],
                  {'K': P['k0'], 'p': P['parch'][2], 'P': P['parch'][3], 'r': P['waxs'][1]})  # letter
    with rec.step('sparkle'):
        for i in range(4):
            x = 64 - i * 7 - (f % 2) * 2; y = 22 + [0, 2, 1, 3][(i + f) % 4]
            cv.p(x, y, P['g4'] if i % 2 == 0 else P['g3'])


def owl():
    return layered('send-an-owl', 160, 52, 8, 140, owl_scene)


# ---------------------------------------------------------------- catalogue
PROJECT_PAGES = [
    ('echosim', 'ECHOSIM', 'VOLUME I', None),
    ('arena-survivor', 'ARENA SURVIVOR', 'VOLUME II', None),
    ('reload', 'RELOAD', 'VOLUME III', 'BREWING'),
    ('medieval-hauler', 'MEDIEVAL HAULER', 'VOLUME IV', 'BREWING'),
]
CHAPTERS = [('1', 'I', 'scroll'), ('2', 'II', 'book'), ('3', 'III', 'wand'), ('4', 'IV', 'map'), ('finale', None, 'owl')]
SKILLS = ['gamepad', 'crystal', 'mirror', 'cauldron', 'quill']


def catalogue():
    """(output subdir, Asset) for every asset in the README."""
    out = [('hero', hero()), ('chapters', dossier()), ('animations', owl())]
    for key, title, vol, stamp in PROJECT_PAGES:
        out.append(('projects', project_page(key, title, vol, stamp)))
    for slug, numeral, emblem in CHAPTERS:
        out.append(('chapters', single(f'chapter-{slug}', chapter_plate(numeral, emblem))))
    for s in SKILLS:
        ic = single(f'skill-{s}', icon(s))
        ic.scale = 2  # 32px beside a heading
        out.append(('icons', ic))
    return out
