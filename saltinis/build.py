#!/usr/bin/env python3
"""Builds /home/claude/italija.tingek/index.html (v2: times, legs, live mode, maps, photos, daylight)."""
import datetime
import html
import math
import random
import pathlib
import urllib.parse

OUT = pathlib.Path(__file__).resolve().parent.parent  # repozitorijos šaknis (skriptas guli saltinis/)
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(s, quote=True)


def mq(q):
    return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote_plus(q)


def hm(s):
    h, m = s.split(':')
    return int(h) * 60 + int(m)


def fm(m):
    m = int(round(m)) % 1440
    return f'{m // 60:02d}:{m % 60:02d}'


def dur_txt(m):
    m = int(round(m))
    if m < 60:
        return f'~{m} min'
    h, r = divmod(m, 60)
    return f'~{h} val.' if r == 0 else f'~{h} val. {r} min'


def nb(n):
    return f'{int(n):,}'.replace(',', ' ')


def km_txt(x):
    if x >= 10 or abs(x - round(x)) < 0.05:
        return f'~{round(x)} km'
    return '~' + f'{x:.1f}'.replace('.', ',') + ' km'


# --- sun (NOAA / Almanac algorithm, accuracy about +-2 min)
def sun_times(date, lat, lon, tz, zenith):
    n = date.timetuple().tm_yday
    res = []
    for rising in (True, False):
        lng_hour = lon / 15.0
        t = n + (((6 if rising else 18) - lng_hour) / 24.0)
        M = 0.9856 * t - 3.289
        L = (M + 1.916 * math.sin(math.radians(M)) + 0.020 * math.sin(math.radians(2 * M)) + 282.634) % 360
        RA = math.degrees(math.atan(0.91764 * math.tan(math.radians(L)))) % 360
        RA += math.floor(L / 90) * 90 - math.floor(RA / 90) * 90
        RA /= 15.0
        sin_dec = 0.39782 * math.sin(math.radians(L))
        cos_dec = math.cos(math.asin(sin_dec))
        cos_h = (math.cos(math.radians(zenith)) - sin_dec * math.sin(math.radians(lat))) / (cos_dec * math.cos(math.radians(lat)))
        H = math.degrees(math.acos(cos_h))
        H = (360 - H if rising else H) / 15.0
        T = H + RA - 0.06571 * t - 6.622
        ut = (T - lng_hour) % 24
        res.append(round(((ut + tz) % 24) * 60))
    return res


# --- icons (one SVG sprite, referenced with <use>)
SPRITE = {}


def _sym(name, inner, stroke=True):
    g = ('<g fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
         + inner + '</g>') if stroke else inner
    SPRITE[name] = f'<symbol id="i-{name}" viewBox="0 0 24 24">{g}</symbol>'


def _use(name, cls='ico', size=18):
    return (f'<svg class="{cls}" width="{size}" height="{size}" aria-hidden="true" focusable="false">'
            f'<use href="#i-{name}"/></svg>')


_sym('car', '<path d="M3.5 15v-3.2l1.8-4.4A1.6 1.6 0 0 1 6.8 6.4h10.4a1.6 1.6 0 0 1 1.5 1l1.8 4.4V15"/>'
            '<path d="M2.8 15h18.4v2.6H2.8z"/><circle cx="7" cy="18.4" r="1.5" fill="currentColor" stroke="none"/>'
            '<circle cx="17" cy="18.4" r="1.5" fill="currentColor" stroke="none"/><path d="M4.8 11.4h14.4"/>')
_sym('walk', '<circle cx="13.2" cy="4.6" r="1.7" fill="currentColor" stroke="none"/>'
             '<path d="M12.2 8.6l-2.6 3.8 2.6 2.2-.9 5.4M12.2 8.6l3 3.3 2.5.4M11.9 14.6l3.2 2.5.9 3.3M9.6 12.4L7.4 14"/>')
_sym('cable', '<path d="M2 6.5l20-3.2M12 4.9v4.1"/><rect x="7.5" y="9" width="9" height="6.5" rx="1.4"/><path d="M7.5 12.2h9"/>')
_sym('sun', '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4'
            'M5.3 5.3l1.7 1.7M17 17l1.7 1.7M5.3 18.7L7 17M17 7l1.7-1.7"/>')
_sym('route', '<circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="6" r="2.2"/><path d="M8.2 18h6.3a3 3 0 0 0 0-6H9.5a3 3 0 0 1 0-6h6.3"/>')
_sym('pin', '<path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z" stroke-width="2"/>'
            '<circle cx="12" cy="10" r="2.5" fill="currentColor" stroke="none"/>')
_sym('chev', '<path d="M6 9l6 6 6-6" stroke-width="2.6"/>')
_sym('plane', '<path d="M21 15.5v-1.7l-8-5V4a1.5 1.5 0 0 0-3 0v4.8l-8 5v1.7l8-2.4V18l-2 1.5V21l3.5-1 3.5 1v-1.5L13 18v-4.9l8 2.4z" '
              'fill="currentColor" stroke="none"/>', stroke=False)
_CLOUD = 'M6.5 {y}a4 4 0 0 1-.4-7.98 5.6 5.6 0 0 1 10.8-1.3A4.6 4.6 0 0 1 17.4 {y}z'
_sym('wx-sun', '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4'
                'M5.3 5.3l1.7 1.7M17 17l1.7 1.7M5.3 18.7L7 17M17 7l1.7-1.7"/>')
_sym('wx-cloud', f'<path d="{_CLOUD.format(y=18.5)}"/>')
_sym('wx-part', '<circle cx="8" cy="8" r="2.9"/><path d="M8 2.2v1.3M2.2 8h1.3M3.9 3.9l.9.9M12.1 3.9l-.9.9"/>'
                '<path d="M9.4 20a3.3 3.3 0 0 1-.3-6.6 4.6 4.6 0 0 1 8.8-.9 3.8 3.8 0 0 1 .5 7.5z"/>')
_sym('wx-rain', f'<path d="{_CLOUD.format(y=14.5)}"/><path d="M8 17.4l-1 2.6M12.2 17.4l-1 2.6M16.4 17.4l-1 2.6"/>')
_sym('wx-snow', f'<path d="{_CLOUD.format(y=14.5)}"/><path d="M8 18h.01M12 18h.01M16 18h.01M10 21.2h.01M14 21.2h.01" stroke-width="2.8"/>')
_sym('wx-storm', f'<path d="{_CLOUD.format(y=14.5)}"/><path d="M12.8 14.8l-2.4 3.2h3.2l-2.2 3.6"/>')
_sym('wx-fog', '<path d="M4 8h16M6 12h14M4 16h11M8 20h10"/>')
_sym('wx-drop', '<path d="M12 3.3s6 6.3 6 10.4a6 6 0 0 1-12 0C6 9.6 12 3.3 12 3.3z"/>')
_sym('wx-wind', '<path d="M3 9h10.2a2.7 2.7 0 1 0-2.6-3.3M3 13h14.6a2.7 2.7 0 1 1-2.6 3.3M3 17h6.5"/>')
SPRITE_SVG = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
              + ''.join(SPRITE.values()) + '</defs></svg>')

I_CAR = _use('car')
I_WALK = _use('walk')
I_CABLE = _use('cable')
I_SUN = _use('sun')
I_WX = _use('wx-part')
I_DROP = _use('wx-drop', 'ico', 16)
I_WIND = _use('wx-wind', 'ico', 16)
I_PIN = _use('pin', 'ico', 16)
I_ROUTE = _use('route', 'ico', 16)
CHEV = '<svg class="chev" aria-hidden="true" focusable="false"><use href="#i-chev"/></svg>'
CHV = '<svg class="chv" aria-hidden="true" focusable="false"><use href="#i-chev"/></svg>'
PLANE = '<svg class="plane" width="24" height="24" aria-hidden="true" focusable="false"><use href="#i-plane"/></svg>'
LEG_ICON = {'car': I_CAR, 'walk': I_WALK, 'cable': I_CABLE}
LEG_WORD = {'car': 'Važiuojate', 'walk': 'Einate', 'cable': 'Keltuvas ir ėjimas'}


def mlink(q, name):
    return (f'<a class="mlink" href="{esc(mq(q))}" target="_blank" rel="noopener" '
            f'aria-label="{esc(name)} – atidaryti žemėlapyje">{I_PIN}<span>Žemėlapyje</span></a>')


# ------------------------------------------------------------------ geometry (schematic lake map)
def smooth(pts, closed=True, k=1 / 6):
    n = len(pts)
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in (range(n) if closed else range(n - 1)):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p0 = pts[(i - 1) % n] if (closed or i > 0) else p1
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + (" Z" if closed else "")


LAKE = [
    (271, 77.5), (250, 108), (239.5, 138), (219, 179), (164, 239), (127.5, 283.5),
    (82, 311), (94, 356), (89, 372), (87, 400), (91, 426), (112, 432), (157, 438),
    (180, 450), (206, 394), (199, 359), (187, 336), (182, 310), (197, 233),
    (232, 208), (250, 181), (263, 138), (276, 113), (287, 92), (280, 80),
]
LAKE_D = smooth(LAKE)
SIR = [(127, 437), (128.5, 418), (129.5, 402), (131.5, 391), (133.5, 402), (134.5, 418), (136, 437)]
SIR_OPEN = smooth(SIR, closed=False)
SIR_FILL = SIR_OPEN + " L140 444 L123 444 Z"

# coast roads (outside the shoreline)
def _offset_line(idx, dist):
    cx, cy = 165, 270
    out = []
    for j, i in enumerate(idx):
        p = LAKE[i]
        a = LAKE[idx[max(j - 1, 0)]]
        b = LAKE[idx[min(j + 1, len(idx) - 1)]]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / ln, tx / ln
        if nx * (p[0] - cx) + ny * (p[1] - cy) < 0:
            nx, ny = -nx, -ny
        out.append((p[0] + nx * dist, p[1] + ny * dist))
    return out


ROAD_W = smooth(_offset_line([9, 8, 7, 6, 5, 4, 3, 2, 1, 0], 7), closed=False)
ROAD_E = smooth(_offset_line([14, 15, 16, 17, 18, 19, 20, 21, 22, 23], 7), closed=False)

TOWNS = [
    ('Desenzano', 89, 426, 'l'), ('Salò', 82, 311, 'l'), ('Maderno', 127.5, 283.5, 'l'),
    ('Gargnano', 164, 239, 'l'), ('Limone', 239.5, 138, 'l'), ('Torbole', 287, 92, 'r'),
    ('Torri d. B.', 182, 310, 'r'), ('Garda', 187, 336, 'r'), ('Bardolino', 199, 359, 'r'),
    ('Lazise', 206, 394, 'r'), ('Peschiera', 180, 450, 'r'),
]

ZC = {'south': '#E4895E', 'mid': '#BBC76C', 'north': '#80BCDA'}

# named places on the map: id -> (name, (x, y), label (dx, dy, anchor), overview label or None)
# overview label: (dx, dy, anchor, show_name)
LOC = {
    'moniga': ('Moniga', (89, 372), (-14, 2, 'end'), (-14, 17, 'end', False)),
    'sirmione': ('Sirmione', (132, 410), (15, 12, 'start'), (16, 3, 'start', False)),
    'tip': ('Passeggiata', (131, 395), (15, -8, 'start'), None),
    'salo': ('Salò', (82, 311), (-14, 2, 'end'), (-14, 14, 'end', False)),
    'forra': ('Strada della Forra', (219, 181), (-14, 12, 'end'), (-12, 19, 'end', True)),
    'terr': ('Terrazza del Brivido', (204, 164), (-14, -3, 'end'), None),
    'limone': ('Limone', (239.5, 138), (-14, 2, 'end'), (-14, 3, 'end', False)),
    'cicl': ('Via Reamol', (246, 129), (14, -4, 'start'), None),
    'riva': ('Riva del Garda', (270, 82), (-14, 4, 'end'), (-16, 15, 'end', False)),
    'station': ('Keltuvas', (259, 190), (14, 12, 'start'), None),
    'ridge': ('Monte Baldo viršus', (281, 169), (14, 3, 'start'), (14, 3, 'start', False)),
    'malc': ('Malcesine', (251, 180), (-14, 3, 'end'), (-12, 18, 'end', False)),
    'varone': ('Cascata Varone', (265, 58), (14, 2, 'start'), (14, 3, 'start', True)),
    'canale': ('Canale di Tenno', (247, 49), (-14, 4, 'end'), (-14, 3, 'end', True)),
    'lago': ('Lago di Tenno', (252, 37), (14, -2, 'start'), (14, -3, 'start', True)),
    'borghetto': ('Borghetto sul Mincio', (198, 478), (-14, -12, 'end'), None),
    'punta': ('Punta San Vigilio', (181, 327), (-14, -4, 'end'), (-14, -6, 'end', False)),
    'ponale': ('Ponale takas', (262, 93), (-14, 14, 'end'), None),
}

# routes: (style, points) – schematic; styles drive / off / walk / cable
ROUTES = {
    1: [('off', [(-30, 400), (18, 394), (55, 384), (89, 372)])],
    2: [('drive', [(89, 372), (110, 392), (135, 420), (160, 448), (182, 470), (198, 478)]),
        ('drive', [(198, 478), (180, 452), (160, 430), (140, 418), (132, 410)]),
        ('walk', [(132, 410), (132, 402), (131, 395)]),
        ('drive', [(131, 395), (150, 380), (165, 352), (176, 333), (181, 327)]),
        ('drive', [(181, 327), (150, 345), (120, 360), (100, 366), (89, 372)])],
    3: [('drive', [(89, 372), (80, 350), (77, 330), (83, 310), (104, 294), (124, 280), (144, 257), (162, 236), (186, 208),
                   (206, 188), (219, 181), (212, 172), (204, 164), (212, 153), (226, 146), (237, 141), (239.5, 138),
                   (247, 119), (257, 99), (270, 82)]),
        ('walk', [(239.5, 138), (243, 133), (246, 129)])],
    4: [('drive', [(270, 82), (281, 86), (288, 97), (285, 113), (277, 129), (268, 147), (262, 168), (259, 190)]),
        ('drive', [(259, 190), (268, 147), (277, 129), (285, 113), (288, 97), (275, 88), (262, 93)]),
        ('cable', [(259, 190), (270, 180), (281, 169)]),
        ('walk', [(259, 190), (255, 185), (251, 180)])],
    5: [('drive', [(270, 82), (269, 72), (266, 63), (265, 58), (257, 55), (247, 49), (246, 43), (252, 37)]),
        ('off', [(252, 37), (276, 27), (310, 34), (334, 68), (340, 130)])],
}
EXTRA_TXT = {  # day -> [(x, y, anchor, text)] off-map hints
    1: [(10, 412, 'start', '← Malpensa (A4)')],
    5: [(332, 22, 'end', 'į Malpensą ↓')],
}
VIEWS = {  # day -> viewBox for mini-map
    1: (10, 335, 150, 105), 2: (28, 318, 190, 172), 3: (28, 62, 294, 336),
    4: (205, 62, 128, 150), 5: (188, 12, 157, 105),
}


# ------------------------------------------------------------------ map effects: waves, mountains, boats, sky
def smooth_pts(pts, closed=True, k=1 / 6, steps=10):
    # the same curve as smooth(), sampled into a dense polyline (for geometry tests)
    n = len(pts)
    out = []
    for i in (range(n) if closed else range(n - 1)):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p0 = pts[(i - 1) % n] if (closed or i > 0) else p1
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        for j in range(steps):
            t = j / steps
            u = 1 - t
            out.append((u ** 3 * p1[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p2[0],
                        u ** 3 * p1[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p2[1]))
    if not closed:
        out.append(pts[-1])
    return out


def _pip(x, y, poly):
    ins = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            ins = not ins
        j = i
    return ins


def _sd(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _pd(px, py, pts, closed=True):
    n = len(pts)
    return min(_sd(px, py, pts[i], pts[(i + 1) % n]) for i in (range(n) if closed else range(n - 1)))


LAKE_P = smooth_pts(LAKE)


def _in_lake(x, y, margin=0.0):
    return _pip(x, y, LAKE_P) and (margin <= 0 or _pd(x, y, LAKE_P) >= margin)


def waves_svg(k, view, uid):
    # short wave strokes inside the lake; density constant on screen (spacing scales with k)
    x0, y0, w, h = view
    rng = random.Random(round(k * 997) + 5)
    sp = 17 * k
    pts = []
    tries = 0
    while tries < 9000 and len(pts) < (80 if uid == 'ov' else 46):
        tries += 1
        x = rng.uniform(x0, x0 + w)
        y = rng.uniform(y0 + 4 * k, y0 + h)
        if not _in_lake(x, y, 8 * k):
            continue
        if 120 < x < 144 and y > 386:      # Sirmione peninsula
            continue
        if 92 < x < 192 and 336 < y < 360:   # "Lago di Garda" label
            continue
        if any((x - a) ** 2 + (y - b) ** 2 < sp * sp for a, b in pts):
            continue
        pts.append((x, y))
    u = 3 * k
    glyph = (f'<defs><path id="wv{uid}" d="M{-2 * u:.2f} 0q{u / 2:.2f} {-0.85 * u:.2f} {u:.2f} 0'
             f't{u:.2f} 0t{u:.2f} 0t{u:.2f} 0"/></defs>')
    # 4 groups animate (not every wave): far cheaper to render, still looks scattered
    groups = ''
    for g in range(4):
        groups += f'<g class="wg wg{g}">' + ''.join(f'<use href="#wv{uid}" x="{x:.1f}" y="{y:.1f}"/>'
                                                      for i, (x, y) in enumerate(pts) if i % 4 == g) + '</g>'
    return glyph + groups


# sailing boats on the overview map: CSS keyframes (user units); every waypoint is checked to be on the water
BOATS = {
    'b1': [(108, 322), (140, 331), (170, 321), (164, 300), (138, 298)],
    'b2': [(259, 119), (246, 154), (230, 189), (203, 212), (184, 236)],
}


def boats_svg():
    for pts in BOATS.values():
        for x, y in pts:
            assert _in_lake(x, y - 4, 6) and _in_lake(x - 6, y, 2) and _in_lake(x + 6, y, 2), (x, y)
    g = ('<g class="bob"><path class="hull" d="M-5.2 0h10.4l-2.3 2.7h-5.8z"/>'
         '<path class="sail" d="M.5-10.8v9.9h5.6z"/><path class="sail s2" d="M-.5-8.6v7.7h-4.4z"/></g>')
    return ''.join(f'<g class="boat {b}" transform="translate({pts[0][0]} {pts[0][1]})">{g}</g>'
                   for b, pts in BOATS.items())


def boats_css():
    out = ''
    for b, pts in BOATS.items():
        n = len(pts) - 1
        frames = ''.join(f'{round(i * 100 / n)}%{{transform:translate({x}px,{y}px)}}' for i, (x, y) in enumerate(pts))
        out += f'@keyframes {b}{{{frames}}}\n.{b}{{transform:translate({pts[0][0]}px,{pts[0][1]}px)}}\n'
    return out


# --- mountains (overview only): pictorial Dolomite / Alpine peaks around the lake
PEAK_T = [  # normalised outlines: x -0.5..0.5, height 0..1 (up)
    [(-.5, 0), (-.3, .46), (-.22, .42), (-.05, 1), (.08, .74), (.15, .8), (.5, 0)],
    [(-.5, 0), (-.34, .36), (-.26, .62), (-.18, .58), (-.08, .92), (0, 1), (.1, .84), (.2, .6), (.28, .64), (.5, 0)],
    [(-.5, 0), (-.36, .5), (-.3, .82), (-.18, .86), (-.06, .97), (.06, .9), (.18, .95), (.3, .8), (.38, .48), (.5, 0)],
    [(-.5, 0), (-.18, .66), (-.1, .62), (0, 1), (.22, .6), (.5, 0)],
    [(-.5, 0), (-.28, .55), (-.2, .9), (-.12, .78), (-.02, 1), (.06, .7), (.16, .88), (.26, .55), (.5, 0)],
]


def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(a[i] + (b[i] - a[i]) * t):02X}' for i in range(3))


def _excl_boxes():
    k = 0.95
    B = []
    for name, x, y, side in TOWNS:
        w = len(name) * 5.7 * k + 4
        B.append((x - 6 * k - w, y - 9, x + 4, y + 7) if side == 'l' else (x - 4, y - 9, x + 6 * k + w, y + 7))
    for n, zone, x, y, label, dx, dy, anchor, aria in OV_PINS:
        B.append((x - 13, y - 13, x + 13, y + 13))
        w = len(label) * 7.4 + 4
        tx, ty = x + dx, y + dy
        B.append((tx - w, ty - 11, tx + 3, ty + 5) if anchor == 'end' else (tx - 3, ty - 11, tx + w, ty + 5))
    for d in DAYS:
        for v in d['visits']:
            name, (x, y), lab, ovlab = LOC[v['loc']]
            B.append((x - 8, y - 8, x + 8, y + 8))
            if ovlab is None:
                continue
            dx, dy, anc, show = ovlab
            fs = 10 * k
            times = ' · '.join(v['times'])
            w = max(len(name) if show else 0, len(times)) * 0.62 * fs + 5
            tx, ty = x + dx * k, y + dy * k
            y1 = ty + (1.22 * fs if show else 0) + 4
            B.append((tx - w, ty - fs - 3, tx + 3, y1) if anc == 'end' else (tx - 3, ty - fs - 3, tx + w, y1))
    for day, items in EXTRA_TXT.items():
        for x, y, anc, txt in items:
            w = len(txt) * 6.2 + 6
            B.append((x - w, y - 12, x + 4, y + 5) if anc == 'end' else (x - 4, y - 12, x + w, y + 5))
    B += [(258, 328, 338, 349),   # "Monte Baldo"
          (68, 351, 110, 393),    # base circle (Moniga)
          (240, 22, 266, 42)]     # Lago di Tenno
    return B


def _route_lines():
    return [smooth_pts(pts, closed=False, steps=6) for day in ROUTES.values() for style, pts in day]


# mountain ranges as spines (schematic, roughly where they are): points, max/min height, rows
RANGES = [
    ([(4, 50), (55, 42), (110, 36), (165, 30), (222, 18)], 44, 30, 2),        # Brenta Dolomites (north-west)
    ([(10, 104), (62, 98), (118, 94), (176, 96)], 32, 22, 2),                  # Alpi di Ledro / Tremosine
    ([(12, 158), (40, 190), (70, 220), (100, 248)], 27, 18, 1),               # Valvestino / Monte Pizzocolo
    ([(12, 250), (20, 288), (26, 322)], 19, 14, 1),                           # Valtenesi west edge
    ([(298, 124), (310, 172), (318, 216), (320, 262), (306, 314)], 31, 19, 2),  # Monte Baldo
    ([(306, 50), (330, 96)], 26, 20, 1),                                      # Monte Stivo (north-east)
    ([(270, 200), (279, 250), (281, 296)], 22, 15, 1),                       # Monte Baldo, lake side
]


def mountains_svg():
    rng = random.Random(20261029)
    boxes = _excl_boxes()
    lines = _route_lines()
    roads = [smooth_pts(_offset_line([9, 8, 7, 6, 5, 4, 3, 2, 1, 0], 7), closed=False, steps=6),
             smooth_pts(_offset_line([14, 15, 16, 17, 18, 19, 20, 21, 22, 23], 7), closed=False, steps=6)]

    def hit_box(x0, y0, x1, y1):
        return any(not (x1 < a or x0 > c or y1 < b or y0 > d) for a, b, c, d in boxes)

    def clear(pts, rmin):
        for x, y in pts:
            if _pip(x, y, LAKE_P) or _pd(x, y, LAKE_P) < 5:
                return False
            for ln in lines:
                if _pd(x, y, ln, closed=False) < rmin:
                    return False
            for ln in roads:
                if _pd(x, y, ln, closed=False) < 3:
                    return False
        return True

    def ok_peak(cx, cy, h, w):
        if cy - h < 1 or cx - w / 2 < -10 or cx + w / 2 > 350:
            return False
        pts = [(cx - w / 2, cy), (cx + w / 2, cy), (cx, cy - h), (cx - w / 4, cy - h / 2), (cx + w / 4, cy - h / 2),
               (cx, cy - h / 3), (cx - w / 3, cy - h * .2), (cx + w / 3, cy - h * .2), (cx, cy)]
        return clear(pts, 6.5) and not hit_box(cx - w / 2 + 2, cy - h, cx + w / 2 - 2, cy)

    peaks = []
    for spine, hmax, hmin, rows in RANGES:
        dense = smooth_pts(spine, closed=False, steps=12)
        seg = [math.hypot(dense[i + 1][0] - dense[i][0], dense[i + 1][1] - dense[i][1]) for i in range(len(dense) - 1)]
        total = sum(seg)
        for r in range(rows):
            pos = rng.uniform(0, 6) + r * 7
            while pos < total:
                # point + direction at arc length pos
                acc = 0
                for i, L in enumerate(seg):
                    if acc + L >= pos:
                        f = (pos - acc) / (L or 1)
                        x = dense[i][0] + (dense[i + 1][0] - dense[i][0]) * f
                        y = dense[i][1] + (dense[i + 1][1] - dense[i][1]) * f
                        tx, ty = (dense[i + 1][0] - dense[i][0]) / (L or 1), (dense[i + 1][1] - dense[i][1]) / (L or 1)
                        break
                    acc += L
                t = pos / total
                h = (hmin + (hmax - hmin) * math.sin(math.pi * t) ** .7) * rng.uniform(.84, 1.1) * (1 - .22 * r)
                off = rng.uniform(-4, 4) - 9 * r     # back row sits "behind" (higher on the map)
                cx, cy = x - ty * off * 0, y + off
                cx += rng.uniform(-2, 2)
                d = _pd(cx, cy, LAKE_P)
                h = min(h, 3 + d * .8, cy - 2)
                w = h * rng.uniform(1.3, 1.62)
                if h >= 9 and ok_peak(cx, cy, h, w):
                    peaks.append((cx, cy, h, w, r))
                pos += max(8.0, w * rng.uniform(.5, .66))

    hills = []
    y = 352.0
    while y < 486:
        x = rng.uniform(-8, 10)
        while x < 350:
            cx, cy = x + rng.uniform(-4, 4), y + rng.uniform(-3, 3)
            x += rng.uniform(22, 32)
            if rng.random() < .3 or _pip(cx, cy, LAKE_P) or _pd(cx, cy, LAKE_P) < 9:
                continue
            hh = rng.uniform(4, 7)
            hw = hh * rng.uniform(3.4, 4.6)
            pts = [(cx - hw / 2, cy), (cx, cy - hh), (cx + hw / 2, cy), (cx - hw / 4, cy - hh * .7), (cx + hw / 4, cy - hh * .7)]
            if clear(pts, 6) and not hit_box(cx - hw / 2, cy - hh, cx + hw / 2, cy):
                hills.append((cx, cy, hh, hw))
        y += rng.uniform(14, 19)

    P2 = lambda q: ' '.join(f'{a:.1f} {b:.1f}' for a, b in q)
    out = '<g class="hillsS" aria-hidden="true">'
    for cx, cy, hh, hw in sorted(hills, key=lambda p: p[1]):
        out += f'<path d="M{cx - hw / 2:.1f} {cy:.1f}Q{cx:.1f} {cy - 2 * hh:.1f} {cx + hw / 2:.1f} {cy:.1f}Z"/>'
    out += '</g><g class="mts" aria-hidden="true">'
    for cx, cy, h, w, r in sorted(peaks, key=lambda p: p[1]):
        t = rng.choice(PEAK_T)
        if rng.random() < .5:
            t = [(-x, y) for x, y in reversed(t)]
        pts = [(cx + x * w, cy - y * h) for x, y in t]
        top = max(range(len(t)), key=lambda i: t[i][1])
        depth = max(0.0, min(1.0, cy / 300)) * (1 - .35 * r)
        dark = _mix('#69735F', '#4B5442', depth)
        light = _mix('#AFAF9B', '#8D8D74', depth)
        snow = _mix('#F3EFE3', '#E7E1CD', depth)
        face = pts[:top + 1] + [(pts[top][0] + w * .05, cy)]
        out += f'<path fill="{dark}" d="M{P2(pts)}Z"/><path fill="{light}" d="M{P2(face)}Z"/>'
        if h > 20:
            hs = .64 + rng.uniform(-.04, .05)

            def cross(i, j):
                (x1, y1), (x2, y2) = t[i], t[j]
                f = (hs - y1) / ((y2 - y1) or 1e-9)
                return (x1 + (x2 - x1) * f, hs)
            i = top
            while i > 0 and t[i - 1][1] >= hs:
                i -= 1
            j = top
            while j < len(t) - 1 and t[j + 1][1] >= hs:
                j += 1
            if i == 0 or j == len(t) - 1:
                continue
            cl = cross(i - 1, i)
            cr = cross(j + 1, j)
            zig = [(cr[0] - (cr[0] - cl[0]) * f, hs - (.07 if q % 2 else -.02)) for q, f in enumerate((.25, .5, .75), 1)]
            sn = [cl] + t[i:j + 1] + [cr] + zig
            out += f'<path fill="{snow}" d="M{P2([(cx + x * w, cy - y * h) for x, y in sn])}Z"/>'
    return out + '</g>'


# --- sky panel above the overview map: the sun's arc for today (or the selected day)
SKY_W, SKY_H = 340, 140
SKY_CX, SKY_CY, SKY_RX, SKY_RY = 170, 98, 124, 74
SKY_ARC = f'M{SKY_CX - SKY_RX} {SKY_CY}A{SKY_RX} {SKY_RY} 0 0 1 {SKY_CX + SKY_RX} {SKY_CY}'


def _ridge(seed, y_side, y_mid, jag, n):
    rng = random.Random(seed)
    pts = []
    for i in range(n + 1):
        x = SKY_W * i / n
        t = abs(x - SKY_W / 2) / (SKY_W / 2)
        base = y_mid + (y_side - y_mid) * (t ** 1.3)
        spike = rng.uniform(.2, 1) * jag * (.45 + t) * (1.0 if i % 2 else .35)
        pts.append((x, base - spike))
    return 'M0 ' + str(SKY_H) + 'L' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + f'L{SKY_W} {SKY_H}Z'


def sky_html():
    d = DAYS[0]
    rng = random.Random(7)
    stars = ''
    for i in range(18):
        x = rng.uniform(10, 330)
        y = rng.uniform(26, 76)
        if 80 < x < 260 and 46 < y < 96:     # keep the centre text clear
            y = rng.uniform(25, 40)
        stars += f'<circle class="star s{i % 3}" cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(.7, 1.3):.2f}"/>'
    cloud = ('M0 0h27a6 6 0 0 0-1.6-11.8a8.6 8.6 0 0 0-16-2.6a6.2 6.2 0 0 0-8.6 6.6A4 4 0 0 0 0 0z')
    rays = ''.join(f'<line x1="0" y1="-10" x2="0" y2="-14.2" transform="rotate({a})"/>' for a in range(0, 360, 45))
    a = math.pi * .5
    sx = SKY_CX - SKY_RX * math.cos(a)
    sy = SKY_CY - SKY_RY * math.sin(a)
    big = dur_txt(d['set'] - d['rise']).lstrip('~')
    title = f'1 diena · spalio 29 d.'
    return f'''<div class="sky ph-day" id="sky">
<svg viewBox="0 0 {SKY_W} {SKY_H}" aria-hidden="true" focusable="false">
<defs><radialGradient id="sunglow"><stop offset="0" stop-color="#FFE3A0" stop-opacity=".75"/><stop offset=".45" stop-color="#FFD27A" stop-opacity=".28"/><stop offset="1" stop-color="#FFD27A" stop-opacity="0"/></radialGradient></defs>
<g class="stars">{stars}</g>
<path class="moon" d="M312 36a10.5 10.5 0 1 0 9.5 15.6a8.4 8.4 0 1 1-9.5-15.6z"/>
<g class="cl c1"><path d="{cloud}" transform="translate(0 40)"/></g><g class="cl c2"><path d="{cloud}" transform="translate(0 30) scale(.72)"/></g>
<path class="arc-t" d="{SKY_ARC}"/>
<path class="arc-d" id="sky-done" d="{SKY_ARC}" pathLength="100" stroke-dasharray="0 200"/>
<g id="sky-sun" class="sun" transform="translate({sx:.1f} {sy:.1f})"><circle class="glow" r="24" fill="url(#sunglow)"/><g class="rays">{rays}</g><circle class="core" r="7.2"/></g>
<path class="rg1" d="{_ridge(3, 80, 101, 10, 30)}"/>
<path class="rg2" d="{_ridge(9, 92, 109, 7, 22)}"/>
<text class="sk-t" id="sky-t" x="14" y="17">{title}</text>
<text class="sk-d" id="sky-dusk" x="326" y="17" text-anchor="end">Sutemos {fm(d['dusk'])}</text>
<text class="sk-big" id="sky-big" x="{SKY_CX}" y="72" text-anchor="middle">{big}</text>
<text class="sk-s" id="sky-small" x="{SKY_CX}" y="89" text-anchor="middle">šviesus paros metas</text>
<text class="sk-k" x="{SKY_CX - SKY_RX}" y="119" text-anchor="middle">Saulėtekis</text>
<text class="sk-v" id="sky-rise" x="{SKY_CX - SKY_RX}" y="135" text-anchor="middle">{fm(d['rise'])}</text>
<text class="sk-k" x="{SKY_CX + SKY_RX}" y="119" text-anchor="middle">Saulėlydis</text>
<text class="sk-v" id="sky-set" x="{SKY_CX + SKY_RX}" y="135" text-anchor="middle">{fm(d['set'])}</text>
</svg><p class="sr" id="sky-sr">{title}: saulėtekis {fm(d['rise'])}, saulėlydis {fm(d['set'])}, sutemos {fm(d['dusk'])}. Šviesus paros metas {big}.</p></div>'''



def basemap(uid, k, hide=(), view=(0, 0, 340, 480), fx=False):
    s = lambda v: f'{v * k:.2f}'
    contours = '' if fx else ''.join(
        f'<use href="#lk{uid}" transform="translate({dx} 0)" fill="none" stroke="#EFE4CC" '
        f'stroke-opacity=".10" stroke-width="{s(1)}"/>' for dx in (-60, -42, -24, 24, 42, 60))
    hills = '' if fx else (f'<g class="hills" fill="none" stroke="#EFE4CC" stroke-opacity=".07" stroke-width="{s(1)}">'
                           '<path d="M296 120C310 170 312 230 300 290M312 100C326 160 330 240 318 310M20 120C34 150 38 200 30 250"/></g>')
    mts = MOUNTAINS_SVG if fx else ''
    waves = f'<g class="waves" clip-path="url(#lc{uid})" stroke-width="{s(1.15)}">{waves_svg(k, view, uid)}</g>'
    boats = f'<g class="boats" aria-hidden="true">{BOATS_SVG}</g>' if fx else ''
    towns = ''
    for name, x, y, side in TOWNS:
        if name in hide:
            continue
        dx = -6 * k if side == 'l' else 6 * k
        anc = 'end' if side == 'l' else 'start'
        towns += (f'<circle cx="{x}" cy="{y}" r="{s(2.4)}" fill="#EFE4CC"/>'
                  f'<text class="town" x="{x + dx:.1f}" y="{y + 3.6 * k:.1f}" text-anchor="{anc}" '
                  f'style="font-size:{s(10.5)}px">{name}</text>')
    return f'''<defs><path id="lk{uid}" d="{LAKE_D}"/><clipPath id="lc{uid}"><use href="#lk{uid}"/></clipPath></defs>
<rect x="-300" y="-300" width="1000" height="1200" fill="#34401F"/>
{hills}{mts}
{contours}
<use href="#lk{uid}" fill="#1C5877"/>
<g clip-path="url(#lc{uid})" fill="none" stroke="#9CCBE0">
<use href="#lk{uid}" stroke-width="{s(9)}" stroke-opacity=".20"/>
<use href="#lk{uid}" stroke-width="{s(22)}" stroke-opacity=".11"/>
<use href="#lk{uid}" stroke-width="{s(40)}" stroke-opacity=".06"/>
</g>
{waves}{boats}
<path d="{SIR_FILL}" fill="#34401F"/>
<path d="{SIR_OPEN}" fill="none" stroke="#E9DFC5" stroke-width="{s(1.2)}" stroke-opacity=".75"/>
<use href="#lk{uid}" fill="none" stroke="#E9DFC5" stroke-width="{s(1.2)}" stroke-opacity=".75"/>
<path d="{ROAD_W}" fill="none" stroke="#EFE4CC" stroke-opacity=".32" stroke-width="{s(1.3)}" stroke-dasharray="{s(4)} {s(2.5)}"/>
<path d="{ROAD_E}" fill="none" stroke="#EFE4CC" stroke-opacity=".32" stroke-width="{s(1.3)}" stroke-dasharray="{s(4)} {s(2.5)}"/>
<ellipse cx="252" cy="31" rx="{s(7)}" ry="{s(4.5)}" fill="#1C5877" stroke="#E9DFC5" stroke-opacity=".5" stroke-width="{s(1)}"/>
<text class="lakename" x="142" y="352" text-anchor="middle" style="font-size:{s(15)}px">Lago di Garda</text>
<text class="landname" x="298" y="342" text-anchor="middle" style="font-size:{s(12)}px">Monte Baldo</text>
{towns}'''


FLOW_K = {}


def flow_cls(k):
    """one keyframes rule per map scale, so the dash pattern loops seamlessly."""
    key = f'{k:.3f}'
    FLOW_K.setdefault(key, f'fk{len(FLOW_K)}')
    return FLOW_K[key]


def flow_css():
    return ''.join(f'@keyframes {c}{{to{{stroke-dashoffset:-{12 * float(key):.3f}}}}}.dl.on .{c}{{animation:{c} 1.1s linear infinite}}\n'
                   for key, c in FLOW_K.items())


def route_svg(day, k):
    s = lambda v: f'{v * k:.2f}'
    out = ''
    for style, pts in ROUTES[day]:
        d = smooth(pts, closed=False)
        if style == 'drive':
            out += (f'<path class="rc" d="{d}" stroke-width="{s(5.6)}"/>'
                    f'<path class="rt" d="{d}" stroke-width="{s(3.2)}"/>'
                    f'<path class="rf {flow_cls(k)}" d="{d}" stroke-width="{s(1.3)}" stroke-dasharray="{s(2.4)} {s(9.6)}"/>')
        elif style == 'off':
            out += (f'<path class="rc" d="{d}" stroke-width="{s(4.6)}"/>'
                    f'<path class="rt" d="{d}" stroke-width="{s(2.6)}" stroke-dasharray="{s(5)} {s(4)}"/>')
        elif style == 'walk':
            out += f'<path class="rw" d="{d}" stroke-width="{s(2.4)}" stroke-dasharray="{s(0.1)} {s(3.6)}"/>'
        elif style == 'cable':
            out += f'<path class="rw" d="{d}" stroke-width="{s(1.6)}" stroke-dasharray="{s(6)} {s(3)}"/>'
    for x, y, anc, txt in EXTRA_TXT.get(day, []):
        out += (f'<text class="lab ex" x="{x}" y="{y}" text-anchor="{anc}" '
                f'style="font-size:{s(10.5)}px;stroke-width:{s(3)}px"><tspan>{txt}</tspan></text>')
    return out


def stops_svg(day_obj, k, overview):
    """numbered stops with arrival times; labels differ between overview and mini-map."""
    s = lambda v: f'{v * k:.2f}'
    n = day_obj['n']
    out = ''
    for num, v in enumerate(day_obj['visits'], 1):
        loc = v['loc']
        name, (x, y), lab, ovlab = LOC[loc]
        times = ' · '.join(v['times'])
        if overview:
            if ovlab is None:
                lab_svg = ''
            else:
                dx, dy, anc, show = ovlab
                lab_svg = _lab(x, y, dx, dy, anc, name if show else '', times, k, 10)
            r = 4.6
            numtxt = ''
        else:
            dx, dy, anc = lab
            lab_svg = _lab(x, y, dx, dy, anc, name, times, k, 11)
            r = 8.4
            numtxt = (f'<text class="num" x="{x}" y="{y}" style="font-size:{s(10.5)}px">{num}</text>')
        out += (f'<g class="lp" data-loc="d{n}-{loc}">'
                f'<circle class="ring" cx="{x}" cy="{y}" r="{s(r + 5)}" stroke-width="{s(2)}"/>'
                f'<circle class="dot" cx="{x}" cy="{y}" r="{s(r)}" stroke-width="{s(1.8)}"/>{numtxt}{lab_svg}</g>')
    return out


def _lab(x, y, dx, dy, anc, name, times, k, fs):
    f = fs * k
    px = x + dx * k
    py = y + dy * k
    t = (f'<text class="lab" x="{px:.1f}" y="{py:.1f}" text-anchor="{anc}" '
         f'style="font-size:{f:.2f}px;stroke-width:{3 * k:.2f}px">')
    if name:
        t += f'<tspan class="ln">{esc(name)}</tspan>'
        t += f'<tspan class="lt" x="{px:.1f}" dy="{1.22 * f:.2f}">{times}</tspan>'
    else:
        t += f'<tspan class="lt">{times}</tspan>'
    return t + '</text>'


# ------------------------------------------------------------------ itinerary data
def E(kind, title, desc=None, **kw):
    d = dict(kind=kind, title=title, desc=desc)
    d.update(kw)
    return d


def L(mode, minutes, note='', km=0.0, walk=0):
    return dict(mode=mode, min=minutes, note=note, km=km, walk=walk)


NOTE = lambda text: dict(kind='note', text=text)
NEWB = '<span class="nb">NEW</span>'  # pažymi naujai pridėtus punktus

PH = {  # wikipedia candidates (lang:Title|lang:Title ...) – loaded live in the browser
    'sirmione': 'en:Scaliger Castle (Sirmione)|it:Castello Scaligero (Sirmione)|en:Sirmione|it:Sirmione',
    'forra': 'en:Strada della Forra|it:Strada della Forra',
    'terr': 'it:Tremosine sul Garda|en:Tremosine sul Garda',
    'limone': 'en:Limone sul Garda|it:Limone sul Garda',
    'baldo': 'en:Monte Baldo|it:Monte Baldo',
    'malc': 'en:Malcesine|it:Malcesine',
    'varone': 'it:Cascate del Varone|en:Varone Falls|it:Cascata del Varone',
    'canale': 'it:Canale di Tenno|en:Canale di Tenno',
    'lago': 'it:Lago di Tenno|en:Lake Tenno|en:Lago di Tenno',
    'borghetto': 'it:Borghetto (Valeggio sul Mincio)|en:Borghetto sul Mincio|it:Borghetto sul Mincio',
    'punta': 'it:Punta San Vigilio|en:Punta San Vigilio',
    'ponale': 'it:Sentiero del Ponale|en:Ponale Trail',
}

DAYS = [
    dict(n=1, zone='south', iso='2026-10-29', date='Spalio 29 d., ketvirtadienis', title='Atvykimas',
         sun_at=(45.52, 10.54), must=None,
         events=[
             E('flight', 'Skrydis Vilnius ➔ Milanas Malpensa (MXP)',
               'Nusileidimas 20:05 Italijos laiku (Lietuvoje tuo metu 21:05); po to bagažas ir kelias į nuomos punktą.',
               at='17:25', dur=160, chip='18:25 → 20:05', kick='Skrydis (vietiniai laikai)', walk=10),
             E('car', 'Automobilių atsiėmimas', '„Centauro“ MXP oro uoste; 2 automobiliai.',
               q='Centauro Rent a Car Malpensa Airport', qn='Centauro MXP', at='20:30', dur=30, walk=10),
             E('dinner', 'Vėlyva vakarienė',
               'Sustokite A4 magistralėje (A) arba valgykite jau Monigoje (B); tada sustojimą praleiskite ir į Monigą atvyksite apie 23:15.',
               leg=L('car', 70, 'A4 magistralė', 83.8), dur=20, dq='Autogrill Brembo Sud A4 Osio Sopra', walk=5,
               opts=[('A', 'greitkelyje, A4 kryptimi į Triestą', 'Autogrill Brembo Sud', '24/7 sumuštiniai, pica, kava.', 'Autogrill Brembo Sud A4 Osio Sopra'),
                     ('B', 'Monigoje, pėsčiomis', 'Bar Centrale Moniga', 'Vietinis baras, panini, užkandžiai.', 'Bar Centrale Moniga del Garda')]),
             E('lodging', 'Registracija „Residence Corte Ferrari“',
               'Registracija iki 00:00. Jei vėluojate, iš anksto informuokite šeimininką. Rezidencijos sąlygos – skiltyje „Logistika“.',
               q='Residence Corte Ferrari Moniga del Garda', qn='Residence Corte Ferrari', loc='moniga',
               leg=L('car', 75, 'A4 magistralė', 91.9), dur=15, walk=5, kick='Apgyvendinimas'),
         ]),
    dict(n=2, zone='south', iso='2026-10-30', date='Spalio 30 d., penktadienis', title='Borghetto, Sirmione ir Punta San Vigilio',
         sun_at=(45.52, 10.54),
         must='Casoncelli bresciani (virtinukai su šalavijų sviestu) ir amatininkų ledai.',
         events=[
             E('coffee', 'Caffè San Martino', 'Monigoje. Švieži cornetti su pistacijomis ar kremu, kapučinas, sumuštiniai.',
               q='Caffè San Martino Moniga del Garda', qn='Caffè San Martino', at='08:45', dur=45, loc='moniga', walk=8,
               kick='Rytinė kavinė'),
             E('sight', 'Borghetto sul Mincio', 'Viduramžių kaimas ant Mincio upės: malūnai, akmeniniai namai, Visconteo tiltas ir upės kavinės. Tortellini di Valeggio – čia pat.',
               q='Borghetto sul Mincio', qn='Borghetto sul Mincio', loc='borghetto', ph=PH['borghetto'], new=True,
               leg=L('car', 45, 'per Peschierą', 40), dur=90, walk=30),
             E('meal', 'Pietūs Sirmione', 'Casoncelli bresciani ar amatininkų ledai (žr. „Būtina paragauti“).', dq='Castello Scaligero Sirmione',
               leg=L('car', 35, 'į Sirmione', 22), at='12:45', dur=60, walk=5),
             E('sight', 'Sirmione senamiestis ir pilis', 'Pro Castello Scaligero vartus, siauromis gatvelėmis; pilies bokšto apžvalgos aikštelė.',
               q='Castello Scaligero Sirmione', qn='Sirmione pilis', loc='sirmione', ph=PH['sirmione'], dur=90, walk=15),
             E('sight', 'Passeggiata Panoramica', 'Palei ežero skardžius ir alyvmedžius.',
               q='Passeggiata Panoramica Sirmione', qn='Passeggiata Panoramica', loc='tip', dur=30, walk=30),
             E('sight', 'Punta San Vigilio', 'Renesanso vila ant kyšulio ir akmenuota įlanka. Saulėlydis apie 17:08. Dalis prieigos eina per viešbučio teritoriją.',
               q='Punta San Vigilio', qn='Punta San Vigilio', loc='punta', ph=PH['punta'], at='16:20', new=True,
               leg=L('car', 35, 'per Lazise ir Gardą', 25), dur=70, walk=10),
             E('rest', 'Grįžimas į Moniga', 'Nakvynė „Residence Corte Ferrari“.', dq='Residence Corte Ferrari Moniga del Garda',
               loc='moniga', leg=L('car', 40, '', 30), dur=0, walk=5, kick='Apgyvendinimas'),
             E('dinner', 'Vakarienė Monigoje: 3 pasirinkimai pėsčiomis', None, at='19:00', loc='moniga',
               leg=L('walk', 5), dur=90, walk=8,
               opts=[('A', 'pėsčiomis', 'Pizzeria Ristorante Oasi', 'Didelė šeimyninė picerija, vaikų meniu. Geriau rezervuoti telefonu.', 'Pizzeria Ristorante Oasi Moniga del Garda'),
                     ('B', 'pėsčiomis', 'Ristorante La Pescatrice', 'Tradicinė ežero žuvies osterija, Via del Porto 18.', 'Ristorante La Pescatrice Moniga del Garda'),
                     ('C', 'pėsčiomis', 'Osteria MamaZita', 'Vietinė osterija su picomis. Penktadienį atidaryta 18:30–22:00.', 'Osteria MamaZita Moniga del Garda')]),
         ]),
    dict(n=3, zone='mid', iso='2026-10-31', date='Spalio 31 d., šeštadienis', title='Tarpeklis, Limone ir persikėlimas į šiaurę',
         sun_at=(45.77, 10.77),
         must='Polenta Cusa su kalnų sūriu arba makaronai su ežero upėtakiu ir citrina.',
         events=[
             E('lodging', 'Išsiregistravimas iš „Residence Corte Ferrari“', None, at='09:30', dur=15, loc='moniga',
               dq='Residence Corte Ferrari Moniga del Garda', walk=5, kick='Apgyvendinimas'),
             E('coffee', 'Bar Pasticceria Al Duomo', 'Salò krantinėje. Kava ir kepiniai prieš kelionę į šiaurę.',
               q='Bar Pasticceria Al Duomo Salò', qn='Bar Pasticceria Al Duomo', loc='salo', dur=40, walk=8,
               leg=L('car', 20, '', 13.2), kick='Rytinė kavinė'),
             E('sight', 'Strada della Forra (SP38)', 'Važiavimas uolų tarpekliu. Siauras kelias, žr. patarimą „Strada della Forra“ apačioje.',
               q='Strada della Forra Tremosine', qn='Strada della Forra', loc='forra', ph=PH['forra'],
               leg=L('car', 50, 'Gardesana Occidentale', 27), dur=10),
             E('sight', 'Terrazza del Brivido', 'Apžvalgos aikštelė virš ežero (Pieve di Tremosine).',
               q='Terrazza del Brivido Tremosine', qn='Terrazza del Brivido', loc='terr', ph=PH['terr'],
               leg=L('car', 15, 'kalnų serpantinas', 6), dur=45, walk=20),
             E('meal', 'Pietūs Tremosine', 'Polenta Cusa ar makaronai su upėtakiu (žr. „Būtina paragauti“).', dur=60, walk=5),
             E('sight', 'Limone sul Garda senamiestis', None, q='Limone sul Garda centro storico', qn='Limone sul Garda',
               loc='limone', ph=PH['limone'], leg=L('car', 25, 'kalnų keliu', 9), dur=60, walk=35),
             E('sight', 'Ciclopedonale del Garda (Via Reamol)', 'Pėsčiųjų takas virš vandens.',
               q='Ciclopedonale del Garda Limone', qn='Ciclopedonale del Garda', loc='cicl',
               leg=L('walk', 5), dur=45, walk=30),
             E('lodging', 'Persikėlimas į „Residence Segattini“', 'Registracija Riva del Gardoje ir poilsis iki vakarienės. Rezidencijos taisyklės ir paslaugos – skiltyje „Logistika“.',
               q='Residence Segattini Riva del Garda', qn='Residence Segattini', loc='riva',
               leg=L('car', 20, 'Gardesana Occidentale', 10.6), dur=0, walk=8, kick='Apgyvendinimas'),
             E('dinner', 'Vakarienė Riva del Gardoje: 2 pasirinkimai pėsčiomis', None, at='19:00', loc='riva',
               leg=L('walk', 5), dur=90, walk=8,
               opts=[('A', 'pėsčiomis', 'Ristorante La Berlera', 'Išskirtinis restoranas XIV a. uoloje tarp vynuogynų.', 'La Berlera Riva del Garda'),
                     ('B', 'pėsčiomis', 'Pizzeria Foci da Rita', 'Jauki vietinė picerija šalia Varone.', 'Pizzeria Foci da Rita Riva del Garda')]),
         ]),
    dict(n=4, zone='north', iso='2026-11-01', date='Lapkričio 1 d., sekmadienis', title='Monte Baldo kalnai ir Malcesine',
         sun_at=(45.886, 10.842),
         must='Carne Salada (vytinta ar kepta jautiena su pupelėmis) arba Strangolapreti.',
         events=[
             E('coffee', 'Pasticceria Cristallo', 'Riva del Gardoje. Traškūs raguoliai ir ciabatta sumuštiniai.',
               q='Pasticceria Cristallo Riva del Garda', qn='Pasticceria Cristallo', at='08:30', dur=40, loc='riva', walk=8,
               kick='Rytinė kavinė'),
             E('sight', 'Funivia Malcesine – Monte Baldo',
               'Keltuvas į 1760 m aukštį. Kabina sukasi 360°, o šiandien paskutinė sezono diena!',
               q='Funivia Malcesine Monte Baldo', qn='Monte Baldo keltuvas', loc='station', ph=PH['baldo'],
               leg=L('car', 35, 'Gardesana Orientale', 18.8), dur=30, walk=8),
             NOTE('Paskutinis kilimas aukštyn 15:45; paskutinis nusileidimas 17:00 (rudens grafikas, patikrinkite oficialioje svetainėje).'),
             E('sight', 'Pasivaikščiojimas kalno ketera', None, loc='ridge', dur=120, walk=60),
             E('sight', 'Malcesine senamiestis ir uostas',
               'Nusileidus: viduramžių senamiestis ir žvejų uostas; čia pat pietūs (Carne Salada).',
               q='Malcesine porto', qn='Malcesine uostas', loc='malc', ph=PH['malc'],
               leg=L('cable', 30, 'nusileidimas keltuvu ir pėsčiomis', 0, walk=15), dur=105, walk=60),
             E('sight', 'Ponale takas, pirma atkarpa', 'Senas kelias ir takas palei uolas virš ežero. Šeimai tinka pirma atkarpa nuo Rivos: pirmyn ir atgal apie 2 val.',
               q='Sentiero del Ponale Riva del Garda', qn='Ponale takas', loc='ponale', ph=PH['ponale'], new=True,
               at='15:45', leg=L('car', 35, 'Gardesana Orientale', 18.8), dur=75, walk=10),
             E('dinner', 'Vakarienė Riva del Garda senamiestyje: 2 pasirinkimai', None, at='19:00', loc='riva',
               leg=L('walk', 5), dur=90, walk=8,
               opts=[('A', 'senamiestyje', 'Osteria La Contrada', 'Autentiški senamiesčio skliautai.', 'Osteria La Contrada Riva del Garda'),
                     ('B', 'senamiestyje', "Ristorante Pizzeria Leon d'Oro", 'Istorinis centras.', "Leon d'Oro Riva del Garda")]),
         ]),
    dict(n=5, zone='north', iso='2026-11-02', date='Lapkričio 2 d., pirmadienis', title='Tarpeklio krioklys, Canale di Tenno ir skrydis',
         sun_at=(45.886, 10.842),
         must='Canederli (kalnų duonos kukuliai) ir obuolių štrudelis.',
         events=[
             E('lodging', 'Išsiregistravimas iš „Residence Segattini“', None, at='09:00', dur=15, loc='riva',
               dq='Residence Segattini Riva del Garda', walk=5, kick='Apgyvendinimas'),
             E('sight', 'Parco Grotta Cascata Varone', 'Krioklys uoloje. Lapkritį parkas dirba 10:00–17:00 (patikrinkite prieš vykdami).',
               q='Cascata Varone Riva del Garda', qn='Cascata Varone', loc='varone', ph=PH['varone'], at='10:00',
               leg=L('car', 10, '', 3.4), dur=90, walk=45),
             E('sight', 'Canale di Tenno', 'Akmeninis viduramžių kaimelis be automobilių eismo; čia pat pietūs (Canederli, obuolių štrudelis).',
               q='Canale di Tenno', qn='Canale di Tenno', loc='canale', ph=PH['canale'], at='12:00',
               leg=L('car', 25, 'siauri kalnų keliai', 15.1), dur=105, walk=40),
             E('sight', 'Lago di Tenno (pasirinktinai)', 'Smaragdinis ežeras.', q='Lago di Tenno', qn='Lago di Tenno', loc='lago', ph=PH['lago'],
               leg=L('car', 15, '', 5), dur=45, walk=20),
             NOTE('Iš Lago di Tenno išvykite apie 14:45, kad automobiliai būtų grąžinti iki 20:00.'),
             E('car', 'Automobilių grąžinimas MXP', 'Grąžinti reikia iki 20:00.', q='Centauro Rent a Car Malpensa Airport',
               qn='Centauro MXP', leg=L('car', 210, 'A22 ir A4 į Malpensą', 222.9), dur=30, walk=8),
             E('meal', 'Registracija, saugumo patikra, vakarienė oro uoste', None, at='20:00', dur=115, walk=17),
             E('flight', 'Skrydis MXP ➔ VNO (Wizz Air)', 'Nusileidimas 01:30 Vilniaus laiku (lapkričio 3 d.).',
               at='21:55', dur=155, chip='21:55 → 01:30', kick='Skrydis (vietiniai laikai)'),
         ]),
]



# papildomi aprašymai ir „Ką pamatyti“ punktai (raktas – punkto pavadinimas)
EXTRA = {
    'Skrydis Vilnius ➔ Milanas Malpensa (MXP)': ('Wizz Air skrydis iš Vilniaus. Nusileidus Malpensoje pasiimkite bagažą ir susitikite prie nuomos punktų. Susitarkite dėl bendro susitikimo taško prieš išsiskirstant.',
        ['Bendras susitikimo taškas oro uoste', 'Dokumentai ir vairuotojo pažymėjimas nuomai']),
    'Automobilių atsiėmimas': ('„Centauro“ nuomos punktas Malpensoje. Abu automobiliai, tas pats navigacijos taškas ir bendras pradžios laikas. Prieš išvykstant apžiūrėkite automobilius ir nufotografuokite esamus pažeidimus.',
        ['Patikrinkite kuro lygį ir mokėjimo būdą', 'A4 magistralė mokama – turėkite kortelę']),
    'Vėlyva vakarienė': ('Trumpas sustojimas A4 magistralėje. Sumuštiniai, picos ir kava – greitas valgis po ilgos dienos. Jei sustojimas praleidžiamas, Monigoje atvykstate apie 23:15.',
        ['Sumuštiniai ir picos greitai', 'Kava ir užkandžiai kelionei']),
    'Registracija „Residence Corte Ferrari“': ('Apartamentai Monigos centre, arti uosto ir senamiesčio. Registracija iki 00:00. Jei vėluojate, iš anksto parašykite šeimininkui.',
        ['Baseinas (patikrinkite, ar atidarytas spalį)', 'Vaizdas į vynuogynus ir ežerą iš balkono', 'Stovėjimas aikštelėje']),
    'Caffè San Martino': ('Rytinė kava Monigos aikštėje. Vieta patogi prieš išvykimą į Borghetto.',
        ['Cornetti su pistacijomis ar kremu', 'Kapučinas ir šviežias sumuštinis']),
    'Borghetto sul Mincio': ('Mažas viduramžių kaimas ant Mincio upės. Upė ir malūnai suteikia kaimui savitą atmosferą, o siauros gatvelės ir tiltai – puikus sustojimas prieš pietus. Vienas „Gražiausių Italijos kaimų“ (pagal atsiliepimus).',
        ['Visconteo tiltas ir upės vaizdai', 'Malūnai prie Mincio', 'Akmeniniai namai ir siauros gatvelės', 'Tortellini di Valeggio – kaimynystėje']),
    'Pietūs Sirmione': ('Pietūs Sirmione senamiestyje, prieš pilį. Jei norite stalo 8 žmonėms, rezervuokite iš anksto.',
        ['Casoncelli bresciani (virtinukai su šalavijų sviestu)', 'Amatininkų ledai po pietų']),
    'Sirmione senamiestis ir pilis': ('Scaligerių pilis (XIII–XIV a.) – vienas simboliškiausių Gardos ežero objektų. Senamiestis siaurose gatvelėse, bokšte – apžvalgos aikštelė.',
        ['Pilies griovas ir tiltas', 'Bokšto apžvalgos aikštelė – visas pussalis', 'Siauri laiptai, ne visiems tinka', 'Bilietas ~10 € suaugusiam; atidaryta 8:30–19:15, pirmadieniais uždaryta (Google)']),
    'Passeggiata Panoramica': ('Pasivaikščiojimas palei ežero skardžius Sirmione pakrantėje, tarp alyvmedžių. Trumpas, bet vaizdingas ėjimas prieš išvykstant į Punta San Vigilio.',
        ['Alyvmedžiai ir skardžiai', 'Vaizdai į Garda ežerą ir kalnus']),
    'Punta San Vigilio': ('Kyšulys rytinėje Gardos ežero pusėje su renesanso vila (XVI a.) ir akmenuotu įlankos krantu. Čia vienas gražiausių ežero saulėlydžių.',
        ['Renesanso vila (XVI a.) ant kyšulio', 'Akmenuotas įlankos krantas', 'Saulėlydis apie 17:08', 'Prieiga dalimi per viešbučio teritoriją – patikrinkite prieš einant']),
    'Grįžimas į Moniga': ('Grįžimas į Monigą. Poilsis apartamentuose prieš vakarienę.',
        ['Poilsis ir baseinas (jei atidarytas)', 'Trumpas vakaro pasivaikščiojimas Monigos aikštėje']),
    'Vakarienė Monigoje: 3 pasirinkimai pėsčiomis': ('Vakarienė Monigos centre, pėsčiomis nuo apartamentų. Trys pasirinkimai: Oasi – šeimyninė picerija su vaikų meniu, La Pescatrice – ežero žuvis, MamaZita – picos (penktadienį atidaryta 18:30–22:00).',
        ['Picos ir pasta, vaikų meniu (Oasi)', 'Ežero žuvis (La Pescatrice)', 'Vietinė osterija su picomis (MamaZita)']),
    'Išsiregistravimas iš „Residence Corte Ferrari“': ('Išsiregistravimas iš apartamentų ir kelias į šiaurę. Bagažą sudėkite prieš išvykstant.',
        ['Bagažas automobiliuose, vertingi daiktai su savimi', 'Vanduo ir užkandžiai kelionei']),
    'Bar Pasticceria Al Duomo': ('Kava ir kepiniai Salò krantinėje prieš kelionę per kalnus. Salò – miestas vakarų Gardos krante su Duomu ir krantine.',
        ['Salò Duomas ir krantinė', 'Pyragaičiai, ledai ir kava', 'Vaizdai į ežerą']),
    'Strada della Forra (SP38)': ('Kelias SP38, iškaltas uolų tarpeklyje virš Gardos ežero. Siauras ir vingiuotas: važiuokite ramiai, tuneliuose įjunkite šviesas. Žemesnėje dalyje vienkryptis, įkalnėje link Tremosine.',
        ['Uolų tarpeklis ir vaizdai į ežerą', 'Vienpusė atkarpa aukštyn nuo ežero', 'Atidaryta 24 val. (Google); kelias gali būti uždarytas dėl nuošliaužų']),
    'Terrazza del Brivido': ('Apžvalgos aikštelė Pieve di Tremosine kaime, virš ežero. Čia galima pasilsėti su kava ar pietumis ir pasigrožėti plačiu vaizdu.',
        ['Panoraminis vaizdas į ežerą', 'Pieve di Tremosine kaimas', 'Kavinė ir restoranas (9:00–21:00)']),
    'Pietūs Tremosine': ('Pietūs kalnų kaime prieš nusileidimą į Limone.',
        ['Polenta cusa su kalnų sūriu', 'Makaronai su ežero upėtakiu ir citrina']),
    'Limone sul Garda senamiestis': ('Limone – vienas žinomiausių citrinų miestų prie Gardos ežero. Senamiestyje siauros gatvelės, spalvingi namai ir citrinmedžių terasos.',
        ['Citrinmedžių terasos (limonaie)', 'Senamiesčio siauros gatvelės', 'Krantinė ir uostelis']),
    'Ciclopedonale del Garda (Via Reamol)': ('Pėsčiųjų ir dviratininkų takas, iškaltas uolose virš ežero. Gražiausi vaizdai maždaug per vidurį, prie Sophine. Takas nebaigtas – nesijungia su Riva, todėl pasivaikščiokite ir apsisukite.',
        ['Takas uolose virš ežero', 'Vaizdai į Gardos ežerą', 'Takas nebaigtas – nesijungia su Riva']),
    'Persikėlimas į „Residence Segattini“': ('Riva del Garda: apartamentai su baseinu, privačia aikštele ir nemokamais dviračiais. Registratūra 8:00–12:00 ir 15:00–22:00.',
        ['Baseinas 8:00–20:00', 'Nemokami dviračiai', 'Elektromobilių įkrova (0,70 €/kWh)']),
    'Vakarienė Riva del Gardoje: 2 pasirinkimai pėsčiomis': ('Vakarienė Rivos senamiestyje arba netoli Varone, pėsčiomis nuo apartamentų.',
        ['Senamiesčio aplinka', 'Vietinė virtuvė ir picos']),
    'Pasticceria Cristallo': ('Rytinė kava ir ledai Rivos krantinėje su ežero vaizdu. Puiki vieta pradėti sekmadienį prieš išvykstant į Malcesine.',
        ['Krantinė ir terasa', 'Raguoliai ir ciabatta sumuštiniai']),
    'Funivia Malcesine – Monte Baldo': ('Kabelinis keltuvas iš Malcesine į Monte Baldo viršūnę, 1 760 m. Kabina sukasi 360°, todėl visi mato ežerą. Lapkričio 1 d. – paskutinė sezono diena.',
        ['Kabina sukasi 360° – panoraminis vaizdas', 'Kavinė ir takai viršuje', 'Bilietai internetu su laiko langu (QR kodas)', 'Eilės iki valandos – rinkitės ankstyvą laiką']),
    'Pasivaikščiojimas kalno ketera': ('Pasivaikščiojimas Monte Baldo kalnagūriu su ežero ir Alpių panorama. Takai lengvi, tinka vaikams, tik apsirenkite šiltai – viršuje apie 3 °C.',
        ['Panoraminiai taškai ir Alpių vaizdai', 'Kavinė ir pasivaikščiojimo takai', 'Šilti drabužiai (viršuje apie 3 °C)']),
    'Malcesine senamiestis ir uostas': ('Malcesine – viduramžių miestelis su pilimi ir žvejų uostu. Čia pietūs ir trumpas pasivaikščiojimas prieš grįžtant į Rivą.',
        ['Malcesine pilis (Castello di Malcesine)', 'Žvejų uostas', 'Carne salada – vietinis patiekalas']),
    'Ponale takas, pirma atkarpa': ('Senas kelias ir takas palei uolas virš Gardos ežero, prasidedantis Rivos pakraštyje. Šeimai tinka pirma atkarpa: pirmyn ir atgal apie 2 val.',
        ['Uolų takas virš ežero', 'Vaizdai į Riva ir ežerą', 'Prieš eidami patikrinkite uždarymus (Garda Trentino)']),
    'Vakarienė Riva del Garda senamiestyje: 2 pasirinkimai': ('Vakarienė Rivos senamiestyje, pėsčiomis nuo apartamentų.',
        ['Senamiesčio skliautinės patalpos', 'Vietinė virtuvė']),
    'Išsiregistravimas iš „Residence Segattini“': ('Išsiregistravimas iš Rivos apartamentų. Apartamentai išvykimo dieną atlaisvinami iki 10:00.',
        ['Bagažas į automobilius prieš išvykstant']),
    'Parco Grotta Cascata Varone': ('Krioklys, krintantis į uolų olą Varone. Iš apatinės ir viršutinės dalies galima stebėti vandenį iš arti, takai eina per olos sodą.',
        ['Krioklys uolos oloje', 'Sodas ir takai aplink parką', 'Bilietas ~7 €; stovėjimas nemokamas', 'Darbo laikas: 9:00–17:00 (Google); site nurodo lapkričio 10:00–17:00']),
    'Canale di Tenno': ('Akmeninis viduramžių kaimelis Tenno kalnuose. Centre nėra automobilių eismo, akmeninės gatvelės ir arkos.',
        ['Akmeninės gatvelės ir arkos', 'Canederli ir obuolių štrudelis']),
    'Lago di Tenno (pasirinktinai)': ('Smaragdinis kalnų ežeras apie 20–30 min nuo Rivos. Aplink ežerą pasivaikščiojimo takas, vasarą galima maudytis.',
        ['Smaragdinis vanduo', 'Takas aplink ežerą', 'Mokamas stovėjimas (~2 €/val.), 5 min pėsčiomis laiptais']),
    'Automobilių grąžinimas MXP': ('Automobilių grąžinimas Malpensoje. Grąžinkite abu automobilius iki 20:00.',
        ['Grąžinimas tame pačiame punkte, kaip atsiėmimas', 'Patikrinkite kurą ir bagažinę']),
    'Registracija, saugumo patikra, vakarienė oro uoste': ('Malpensos oro uostas: registracija, saugumo patikra ir vakarienė prieš skrydį.',
        ['Vakarienė oro uoste', 'Dokumentai visiems keliautojams']),
    'Skrydis MXP ➔ VNO (Wizz Air)': ('Wizz Air skrydis iš Malpensos į Vilnių. Nusileidimas 01:30 lapkričio 3 d.',
        ['Rankinio bagažo ir bagažo taisyklės']),
}


# gėrimai kiekvienam punktui: alus visur, vynas vakarais (vyno zonos: Valtènesi – Moniga, Lugana – Sirmione, Trentino – Riva)
DRINK = {
    'Vėlyva vakarienė': 'Alus: greitai, prie A4 – trumpas „Birra“ prieš kelionę. Vakare vynas: Valtènesi, jei yra.',
    'Registracija „Residence Corte Ferrari“': 'Alus: vietinis amatininkų. Vakarui vynas: Valtènesi (raudonas arba rožinis; Moniga yra šios zonos).',
    'Caffè San Martino': 'Alus: vietinis amatininkų, vėliau per pietus. Ryte – kava.',
    'Borghetto sul Mincio': 'Alus: prie upės, vietinis amatininkų alus.',
    'Pietūs Sirmione': 'Alus: Lombardijos amatininkų alus prie pietų. Vynas: Lugana (baltas, Sirmione zonos vynas).',
    'Sirmione senamiestis ir pilis': 'Alus: po pilies, kavinėje ant senamiesčio aikštės.',
    'Passeggiata Panoramica': 'Alus: pakeliui, kavinėje ant kranto.',
    'Punta San Vigilio': 'Vynas: Lugana arba Bardolino prie saulėlydžio. Alus: vietinis amatininkų.',
    'Grįžimas į Moniga': 'Alus: šaltas po kelio. Vakarui vynas: Valtènesi.',
    'Vakarienė Monigoje: 3 pasirinkimai pėsčiomis': 'Vynas: Valtènesi (raudonas arba rožinis). Alus: vietinis amatininkų. Ežero žuvims – Lugana.',
    'Išsiregistravimas iš „Residence Corte Ferrari“': 'Alus: nėra – išvykstate. Vanduo kelionei.',
    'Bar Pasticceria Al Duomo': 'Alus: Salò krantinėje, vietinis amatininkų.',
    'Strada della Forra (SP38)': 'Alus: po tarpeklio Tremosine restorane, vietinis amatininkų.',
    'Terrazza del Brivido': 'Alus: belvederio terasoje su vaizdu. Vakare – Lugana ar Bardolino.',
    'Pietūs Tremosine': 'Alus: vietinis amatininkų prie upėtakio.',
    'Limone sul Garda senamiestis': 'Alus arba limončelo: vietinis citrininis likeris Limone krantinėje.',
    'Ciclopedonale del Garda (Via Reamol)': 'Alus: po pasivaikščiojimo Limone baruose.',
    'Persikėlimas į „Residence Segattini“': 'Alus: Riva krantinėje po registracijos. Vakare – vynas.',
    'Vakarienė Riva del Gardoje: 2 pasirinkimai pėsčiomis': 'Vynas: Trentino – Teroldego (raudonas) arba Nosiola (baltas). Alus: Trentino amatininkų.',
    'Pasticceria Cristallo': 'Alus: vietinis amatininkų, kavinėje krantinėje.',
    'Funivia Malcesine – Monte Baldo': 'Alus: viršuje kavinėje, vietinis amatininkų.',
    'Pasivaikščiojimas kalno ketera': 'Alus: po pasivaikščiojimo viršutinėje kavinėje.',
    'Malcesine senamiestis ir uostas': 'Alus: uosto kavinėje, vietinis amatininkų.',
    'Ponale takas, pirma atkarpa': 'Alus: po pasivaikščiojimo Riva, šaltas.',
    'Vakarienė Riva del Garda senamiestyje: 2 pasirinkimai': 'Vynas: Trentino Teroldego (raudonas) arba Nosiola (baltas). Alus: vietinis.',
    'Parco Grotta Cascata Varone': 'Alus: po parko, Varone vietinėje kavinėje.',
    'Canale di Tenno': 'Alus arba Teroldego vynas prie canederli pietų.',
    'Lago di Tenno (pasirinktinai)': 'Alus: prie ežero kavinėje (vasarą).',
    'Registracija, saugumo patikra, vakarienė oro uoste': 'Vakarui: vynas (Lugana) arba alus prieš skrydį.',
}


def finish_days():
    for d in DAYS:
        for e in d['events']:
            if e['kind'] != 'note' and e['title'] in EXTRA:
                e['desc'], e['see'] = EXTRA[e['title']]
            if e['kind'] != 'note' and e['title'] in DRINK:
                e['drink'] = DRINK[e['title']]
    for d in DAYS:
        base = (d['n'] - 1) * 1440
        evs = [e for e in d['events'] if e['kind'] != 'note']
        prev = None
        for e in evs:
            legm = e['leg']['min'] if e.get('leg') else 0
            if prev is None:
                a = base + hm(e['at'])
            else:
                earliest = prev['a'] + prev['dur'] + legm
                a = base + hm(e['at']) if e.get('at') else earliest
                assert a >= earliest, (d['n'], e['title'], fm(a), fm(earliest))
            e['a'] = a
            prev = e
        for i, e in enumerate(evs):
            if i + 1 < len(evs):
                nx = evs[i + 1]
                e['l'] = nx['a'] - (nx['leg']['min'] if nx.get('leg') else 0)
            else:
                e['l'] = e['a'] + e['dur']
            assert e['l'] >= e['a'], (d['n'], e['title'])
        d['evs'] = evs
        # visits on the map (consecutive events at the same place are one visit)
        visits = []
        last = None
        for e in evs:
            loc = e.get('loc')
            if not loc:
                continue
            if loc != last:
                found = next((v for v in visits if v['loc'] == loc), None)
                if found:
                    found['times'].append(fm(e['a']))
                else:
                    visits.append(dict(loc=loc, times=[fm(e['a'])]))
                last = loc
        d['visits'] = visits
        # totals
        dmin = 0
        dkm = 0.0
        wmin = 0
        for e in evs:
            lg = e.get('leg')
            if lg:
                if lg['mode'] == 'car':
                    dmin += lg['min']
                    dkm += lg['km']
                elif lg['mode'] == 'walk':
                    wmin += lg['min']
                else:
                    wmin += lg['walk']
            wmin += e.get('walk', 0)
        d['drive_min'], d['drive_km'], d['walk_min'] = dmin, dkm, wmin
        d['steps'] = int(round(wmin * 100 / 500.0)) * 500
        d['walk_km'] = d['steps'] * 0.72 / 1000
        # sun
        dt = datetime.date.fromisoformat(d['iso'])
        lat, lon = d['sun_at']
        d['rise'], d['set'] = sun_times(dt, lat, lon, 1, 90.833)
        d['dusk'] = sun_times(dt, lat, lon, 1, 96.0)[1]
        d['dawn'] = sun_times(dt, lat, lon, 1, 96.0)[0]
        for e in evs:
            lg = e.get('leg')
            e['km_e'] = lg['km'] if lg and lg['mode'] == 'car' else 0.0
            wk_leg = (lg['min'] if lg['mode'] == 'walk' else (lg['walk'] if lg['mode'] == 'cable' else 0)) if lg else 0
            e['wk_e'] = wk_leg + e.get('walk', 0)
        d['route_q'] = route_queries(evs)


def route_queries(evs):
    pts = []
    for e in evs:
        q = e.get('dq') or e.get('q')
        if not q:
            continue
        lg = e.get('leg')
        if not pts or (lg and lg['mode'] == 'car'):
            if not pts or pts[-1] != q:
                pts.append(q)
    return pts


def dir_url(pts):
    if len(pts) < 2:
        return None
    u = ('https://www.google.com/maps/dir/?api=1&origin=' + urllib.parse.quote_plus(pts[0]) +
         '&destination=' + urllib.parse.quote_plus(pts[-1]) + '&travelmode=driving')
    if len(pts) > 2:
        u += '&waypoints=' + '%7C'.join(urllib.parse.quote_plus(p) for p in pts[1:-1])
    return u


finish_days()


# ------------------------------------------------------------------ html builders
def day_map(d):
    k = VIEWS[d['n']][2] / 330.0
    x, y, w, h = VIEWS[d['n']]
    uid = f'd{d["n"]}'
    svg = (f'<svg class="lakemap dm" viewBox="{x} {y} {w} {h}" role="img" aria-label="{d["n"]} dienos žemėlapis su laikais" '
           f'style="--c:{ZC[d["zone"]]}">{basemap(uid, k, {LOC[v["loc"]][0] for v in d["visits"]}, VIEWS[d["n"]])}'
           f'<g class="dl on" data-day="{d["n"]}">{route_svg(d["n"], k)}{stops_svg(d, k, False)}</g></svg>')
    url = dir_url(d['route_q'])
    link = (f'<a class="mlink" href="{esc(url)}" target="_blank" rel="noopener">{I_ROUTE}<span>Maršrutas Google Maps</span></a>'
            if url else '')
    return (f'<div class="dmap"><h4>Dienos žemėlapis</h4><div class="dmbox">{svg}</div>'
            f'<p class="dmnote">Linija – važiavimas, taškai – pėsčiomis. Laikas prie taško – atvykimas.</p>{link}</div>')


def ev_html(d, i, e):
    n = d['n']
    first = i == 0
    leg = e.get('leg')
    leg_h = ''
    if leg and not first:
        note = f'<span class="lg-n">{esc(leg["note"])}</span>' if leg['note'] else ''
        km = f'<span class="lg-n">{km_txt(leg["km"])}</span>' if leg['mode'] == 'car' and leg['km'] else ''
        leg_h = (f'<div class="leg">{LEG_ICON[leg["mode"]]}<span class="sr">{LEG_WORD[leg["mode"]]}: </span>'
                 f'<span class="lg-t">{dur_txt(leg["min"])}</span>{km}{note}'
                 f'<span class="lg-live" hidden></span></div>')
    chip = e.get('chip') or (f'{fm(e["a"])}–{fm(e["l"])}' if e['l'] > e['a'] else fm(e['a']))
    kick = e.get('kick')
    if not kick:
        kick = {'dinner': 'Vakarienė', 'coffee': 'Rytinė kavinė', 'lodging': 'Apgyvendinimas', 'flight': 'Skrydis',
                'car': 'Automobiliai'}.get(e['kind'])
    kick_h = f'<span class="kick">{esc(kick)}</span>' if kick and e['kind'] in ('coffee', 'dinner', 'lodging', 'flight', 'car') else ''
    chips = (f'<span class="evc"><span class="t">{esc(chip)}</span>{kick_h}'
             f'<span class="bd bd-now" hidden>Dabar</span><span class="bd bd-next" hidden></span></span>')
    body = ''
    if e.get('desc'):
        body += f'<p>{esc(e["desc"])}</p>'
    if e.get('see'):
        body += ('<h5 class="seeh">Ką pamatyti</h5><ul class="see">'
                 + ''.join(f'<li>{esc(x)}</li>' for x in e['see']) + '</ul>')
    if e.get('drink'):
        body += f'<p class="drink">{esc(e["drink"])}</p>'
    if e.get('q'):
        body += mlink(e['q'], e.get('qn') or e['title'])
    if e.get('opts'):
        cards = ''
        for ab, tag, name, desc, q in e['opts']:
            cards += (f'<article class="opt"><div class="opt-top"><span class="ab"><span class="sr">Pasirinkimas </span>{ab}</span>'
                      f'<span class="tag">{esc(tag)}</span></div><h5 class="oname">{esc(name)}</h5>'
                      f'<p class="odesc">{esc(desc)}</p>{mlink(q, name)}</article>')
        body += f'<div class="opts">{cards}</div>'
    ph = ''
    if e.get('ph'):
        ph = (f'<span class="ph" data-wp="{esc(e["ph"])}"><img alt="" width="60" height="60" decoding="async"></span>')
        body += '<a class="cred" hidden target="_blank" rel="noopener">Nuotrauka: Wikipedia</a>'
    inner_sum = f'<span class="evs"><span class="evl">{chips}<span class="evt">{esc(e["title"])}</span>{NEWB if e.get("new") else ""}</span>{ph}{CHV if body else ""}</span>'
    if body:
        core = f'<details class="evd" open><summary>{inner_sum}</summary><div class="evb">{body}</div></details>'
    else:
        core = f'<div class="evd plain">{inner_sum}</div>'
    loc = f'd{n}-{e["loc"]}' if e.get('loc') else ''
    return (f'<li class="ev k-{e["kind"]}" id="e{n}-{i + 1}" data-a="{e["a"]}" data-l="{e["l"]}" data-d="{n}" '
            f'data-loc="{loc}" data-leg="{leg["min"] if leg and not first else 0}" '
            f'data-km="{e.get("km_e", 0)}" data-wk="{e.get("wk_e", 0)}" '
            f'data-mode="{leg["mode"] if leg and not first else ""}" data-title="{esc(e["title"])}">'
            f'<span class="mk" aria-hidden="true"></span>{leg_h}{core}</li>')


def sun_tile(d):
    dl = d['dusk'] - d['rise']
    return (f'<div class="st st-sun wide"><span class="st-k">{I_SUN}Saulė ir sutemos</span>'
            f'<div class="sun3"><span><i>Saulėtekis</i><b>{fm(d["rise"])}</b></span>'
            f'<span><i>Saulėlydis</i><b>{fm(d["set"])}</b></span>'
            f'<span><i>Sutemos</i><b>{fm(d["dusk"])}</b></span></div>'
            f'<div class="dl-bar" hidden><i></i></div>'
            f'<p class="dl-t">Šviesus laikas iki sutemų: {dur_txt(dl)[1:]}</p></div>')


# Prognozės momentinė kopija (2026-10-26): rodoma be JavaScript ir kol neužsikrauna šviežia iš Open-Meteo.
# diena: (raktas, vietovė, min, max, kritulių tikimybė %, valandos, pakilimas virš vietovės m, antros vietos pav.)
WX_SNAP_DATE = '2026-10-26'
WX_SNAP = {
    1: ('sir', 'Sirmione apylinkės', 11.3, 16.7, 5, [18, 20, 22], None, None, None),
    2: ('sir', 'Sirmione apylinkės', 11.1, 16.2, 0, [9, 12, 15, 18], None, None, None),
    3: ('lim', 'Limone sul Garda', 8.3, 13.9, 5, [9, 12, 15, 18], None, None, None),
    4: ('mal', 'Malcesine', 7.7, 13.3, 15, [9, 12, 15, 18], 'bal', 'Monte Baldo viršuje (~1 750 m)', 1660),
    5: ('ten', 'Riva del Garda', 5.3, 11.9, 15, [9, 12, 15, 18], None, 'Tenno (~570 m)', 500),
}


def wx_tile(d):
    key, loc, tmin, tmax, pp, hours, alt, altn, altdh = WX_SNAP[d['n']]
    attrs = (f'data-wx="{key}" data-n="{d["n"]}" data-date="{d["iso"]}" data-hours="{",".join(map(str, hours))}" '
             f'data-min="{tmin}" data-max="{tmax}" data-pp="{pp}" data-snap="{WX_SNAP_DATE}" data-snaploc="{esc(loc)}"')
    if altn:
        attrs += f' data-alt-n="{esc(altn)}" data-alt-dh="{altdh}"'
    if alt:
        attrs += f' data-alt="{alt}"'
    alt_html = ''
    if altn:
        est = tmax - altdh * 0.0065
        alt_html = (f'<p class="wx-alt">{esc(altn)}: apie {f"{est:.0f}"}&nbsp;°C dieną (įvertis pagal aukštį)</p>')
    return (f'<div class="st st-wx" {attrs}><span class="st-k">{I_WX}Orai: <span class="wx-loc">{esc(loc)}</span></span>'
            f'<div class="wx-main"><b class="wx-temp">{round(tmin)}–{round(tmax)}&nbsp;°C</b><span class="wx-cond"></span></div>'
            f'<p class="wx-meta"><span>{I_DROP}Lietaus tikimybė: {pp} %</span></p>'
            f'<div class="wx-hrs" hidden></div>{alt_html}<p class="wx-adv"></p>'
            f'<p class="wx-src">Prognozė, 2026 m. spalio 26 d.</p></div>')


def stats_html(d):
    abs0 = (d['n'] - 1) * 1440
    return (f'<div class="dstats" data-rise="{abs0 + d["rise"]}" data-set="{abs0 + d["set"]}" data-dusk="{abs0 + d["dusk"]}">'
            f'<div class="st"><span class="st-k">{I_CAR}Važiavimas</span><b>{dur_txt(d["drive_min"])[1:]}</b>'
            f'<small>{km_txt(d["drive_km"])} automobiliu</small></div>'
            f'<div class="st"><span class="st-k">{I_WALK}Ėjimas</span><b>{dur_txt(d["walk_min"])[1:]}</b>'
            f'<small>~{nb(d["steps"])} žingsnių (~{f"{d["walk_km"]:.1f}".replace(".", ",")} km)</small></div>'
            f'{sun_tile(d)}{wx_tile(d)}</div>')


def day_html(d):
    items = ''
    i = 0
    for e in d['events']:
        if e['kind'] == 'note':
            items += f'<li class="note"><span class="mk n" aria-hidden="true"></span><p>{esc(e["text"])}</p></li>'
        else:
            items += ev_html(d, i, e)
            i += 1
    must = (f'<div class="dsec dmust"><h4>Būtina paragauti</h4><p class="must">{esc(d["must"])}</p></div>'
            if d['must'] else '')
    return (f'<details class="day z-{d["zone"]}" id="d{d["n"]}" data-date="{d["iso"]}">'
            f'<summary><h3 class="dsum"><span class="dnum">{d["n"]}</span>'
            f'<span class="dhead"><span class="dtitle">{esc(d["title"])}</span>'
            f'<span class="ddate">{esc(d["date"])}<span class="badge" hidden>Šiandien</span></span></span>{CHEV}</h3></summary>'
            f'<div class="dbody">{stats_html(d)}<div class="dsec dtl"><h4>Programa</h4><ol class="tl">{items}</ol></div>'
            f'{must}{day_map(d)}</div></details>')


OV_PINS = [
    (1, 'south', 89, 372, 'Moniga', -16, 4, 'end', '1 diena: atvykimas, Moniga'),
    (2, 'south', 132, 410, 'Sirmione', 16, 4, 'start', '2 diena: Sirmione'),
    (3, 'mid', 210, 174, 'Tremosine', -15, 4, 'end', '3 diena: Tremosine ir Limone'),
    (4, 'north', 250, 181, 'Malcesine', 15, 4, 'start', '4 diena: Monte Baldo ir Malcesine'),
    (5, 'north', 243.5, 54, 'Tenno', -15, 4, 'end', '5 diena: Varone ir Canale di Tenno'),
]
MOUNTAINS_SVG = None
BOATS_SVG = None


def overview_svg():
    global MOUNTAINS_SVG, BOATS_SVG
    MOUNTAINS_SVG = mountains_svg()
    BOATS_SVG = boats_svg()
    k = 0.95
    layers = ''
    for d in DAYS:
        layers += (f'<g class="dl" data-day="{d["n"]}" style="--c:{ZC[d["zone"]]}">{route_svg(d["n"], k)}'
                   f'<g class="ovs">{stops_svg(d, k, True)}</g></g>')
    pins = ''
    PINS = OV_PINS
    for n, zone, x, y, label, dx, dy, anchor, aria in PINS:
        pins += (f'<a class="pin pin-{zone}" href="#d{n}" data-day="{n}" aria-label="{esc(aria)}">'
                 f'<title>{esc(aria)}</title><circle class="hit" cx="{x}" cy="{y}" r="22"/>'
                 f'<circle class="dot" cx="{x}" cy="{y}" r="10"/>'
                 f'<text x="{x}" y="{y}">{n}</text></a>')
    plabels = ''.join(
        f'<text class="plabel" x="{x + dx}" y="{y + dy}" text-anchor="{anchor}">{label}</text>'
        for n, zone, x, y, label, dx, dy, anchor, aria in PINS)
    return (f'<svg id="ovmap" class="lakemap" data-sel="0" viewBox="0 0 340 480" role="group" aria-labelledby="mapt">'
            f'<title id="mapt">Gardos ežero schema su penkių dienų maršrutais ir laikais</title>{basemap("ov", k, fx=True)}'
            f'<circle class="baseA" cx="89" cy="372" r="17"/><circle class="baseB" cx="271" cy="77" r="7"/>'
            f'{layers}{pins}{plabels}</svg>')


def day_buttons():
    out = '<button type="button" class="dbtn all" data-day="0" aria-pressed="true">Visos</button>'
    for d in DAYS:
        info = (f'Važiavimas {dur_txt(d["drive_min"])} ({km_txt(d["drive_km"])}) · '
                f'ėjimas ~{nb(d["steps"])} žingsnių · sutemos {fm(d["dusk"])}')
        out += (f'<button type="button" class="dbtn z-{d["zone"]}" data-day="{d["n"]}" aria-pressed="false" '
                f'data-title="{esc(str(d["n"]) + " diena · " + d["title"])}" data-sum="{esc(info)}" '
                f'aria-label="{d["n"]} diena">{d["n"]}</button>')
    return out


def flight(date, a, b, note=''):
    note_html = f'<small>{esc(note)}</small>' if note else ''
    return f'''<div class="flight"><p class="fdate">{esc(date)}</p>
<div class="fline"><div class="end"><b>{a[0]}</b><span>{a[2]}</span><i>{esc(a[1])}</i></div>
<div class="route" aria-hidden="true">{PLANE}</div>
<div class="end r"><b>{b[0]}</b><span>{b[2]}</span><i>{esc(b[1])}</i>{note_html}</div></div></div>'''


def stay(zone, label, name, town, dates, q, more='', sid=''):
    idattr = f' id="{sid}"' if sid else ''
    return (f'<article class="stay z-{zone}"{idattr}><p class="stay-label">{esc(label)}</p>'
            f'<h4 class="stay-name">{esc(name)}</h4><p class="stay-meta">{esc(town)}<br>{esc(dates)}</p>'
            f'{mlink(q, name)}{more}</article>')


# Rezidencijos laiškas (gautas iš „Residence Segattini“), išverstas į lietuvių kalbą.
# Parkingo vartų kodų čia SĄMONINGAI nėra: svetainė ir repozitorija vieši.
def _bin(color, text):
    return f'<span class="bin"><i style="background:{color}"></i>{text}</span>'


SEG_INFO = [
    ('Paslaugos', 'Tenisas, baseinas, privati stovėjimo aikštelė, dviračių saugykla, baras, stalo tenisas ir elektromobilių '
                  'įkrovimo stotelė.'),
    ('Atliekų rūšiavimas', 'Atliekas būtina rūšiuoti: konteineriai stovi prie rezidencijos įėjimo. '
                           + _bin('#E3B505', 'geltonas – plastikas') + _bin('#3F8F4A', 'žalias – stiklas')
                           + _bin('#2F6DB5', 'mėlynas – popierius') + _bin('#8A8F94', 'pilkas – sausos atliekos')
                           + _bin('#8B5A3C', 'rudas – šlapios (organinės) atliekos')),
    ('Duonos paslauga', 'Duoną galima užsisakyti kasdien iki 12:00: įrašykite ant lentos registratūroje. Ryte 8:15 duona '
                        'bus padėta prie jūsų apartamentų durų. Sekmadieniais paslauga neteikiama.'),
    ('Tenisas', 'Žaidimo laiką užsirašykite specialiame lape ant stalo prie įėjimo. Svečiams tenisas nemokamas. '
                'Reikalinga tinkama avalynė ir įranga; prireikus galima išsinuomoti raketes ir kamuoliukus.'),
    ('Baseinas', 'Atidarytas 8:00–20:00. Draudžiama „rezervuoti“ vietas prie baseino palikus rankšluosčius. Elkitės deramai ir '
                 'gerbkite kitus poilsiautojus. Prieš įeinant į baseiną privaloma nusiprausti po dušu; jaunesni nei 12 metų '
                 'vaikai turi būti su suaugusiuoju.'),
    ('Kavinė ir registratūra', 'Dirba 8:00–12:00 ir 15:00–22:00. Kavinėje galima žiūrėti televizorių ir ramiai praleisti '
                               'vakarą. Po uždarymo (22:00) bare ir prie baseino prašoma negerti savo atsinešamų gėrimų.'),
    ('Dviračiai', 'Svečiams dviračiai nuomojami nemokamai. Informacijos klauskite registratūroje.'),
    ('Apartamentai', 'Gerbkite kitus svečius; po 22:00 prašoma laikytis tylos. Jei užsakėte kelis apartamentus, griežtai '
                     'draudžiama kelti daiktus (indus, stiklines, stalus, kėdes ir pan.) iš vieno į kitą. Išvykimo dieną '
                     'apartamentai turi būti atlaisvinti iki 10:00.'),
    ('Švara ir užstatas', 'Apartamentai perduodami švarūs ir sutvarkyti, tikimasi, kad išvykdami paliksite juos tvarkingus, ypač '
                          'švarią virtuvę. Keraminę viryklę reguliariai valykite „Cif“ ir drėgna šluoste, per stipriai '
                          'nespausdami, kad nepažeistumėte paviršiaus. Dulkių siurblys yra prie įėjimo šalia kompiuterio: '
                          'panaudoję grąžinkite į vietą. Jei apartamentai paliekami netinkamos būklės, po darbuotojų patikros '
                          'papildomo valymo ar sugadinimų išlaidos bus išskaičiuotos iš užstato. Administracija neatsako už '
                          'apartamentuose ar bendrose erdvėse paliktų daiktų sugadinimą ar vagystę.'),
    ('Skalbimo mašina ir džiovyklė', 'Žetonų (po 5,00 €) klauskite registratūroje. Mašinos yra specialioje patalpoje '
                                     'registratūros pastato −1 aukšte.'),
    ('Papildomos paslaugos', 'Patalynės keitimas – 7,00 € asmeniui; rankšluosčių keitimas – 7,00 € (vienas vonios ir vienas '
                             'rankų rankšluostis); papildomas apartamentų valymas savaitės metu – 50,00 €.'),
    ('Ankstyvas išvykimas', 'Rezervacija yra įpareigojanti ir turi būti apmokėta visa, net jei išvykstate anksčiau.'),
    ('Stovėjimo aikštelė', 'Automatiškai atidaryta 7:00–23:00. Kai uždaryta, atidaroma tik specialiu kodu '
                           '(kodai nurodyti rezidencijos laiške; čia jų neskelbiame, nes puslapis viešas).'),
    ('Turgus', 'Pirmą ir trečią mėnesio trečiadienį – Arco centre, antrą ir ketvirtą trečiadienį – Riva del Gardoje. '
               'Jūsų viešnagės dienomis (šeštadienis–pirmadienis) turgaus nebus.'),
    ('Elektromobilių įkrova', 'Rezidencija turi „Wallbox“ įkrovimo stotelę elektromobiliams; ją galima rezervuoti '
                              'registratūroje. Kaina – 0,70 € už kWh.'),
    ('Kontaktai', 'Residence Segattini &amp; Residenza Le Due Torri, Via Venezia 61, 38066 Riva del Garda (TN)'
                  '<a class="ct" href="tel:+393356119074">Tel. +39 335 611 9074</a>'
                  '<a class="ct" href="mailto:segattini@residenzaleduetorri.it">segattini@residenzaleduetorri.it</a>'
                  '<a class="ct" href="https://www.residencesegattini.it" target="_blank" rel="noopener">www.residencesegattini.it</a>'),
]


# „Residence Corte Ferrari“ rezervacijos informacija (angliškai gauta iš rezervacijos), išversta į lietuvių kalbą.
CF_INFO = [
    ('Į kainą įskaičiuotos paslaugos', 'Baseinas (orientacinis laikotarpis – kovas–spalis); oro kondicionavimas vasarą ir '
                                       'šildymas žiemą; pasveikinimo rinkinys atvykus; patalynė ir rankšluosčiai (kas savaitę); '
                                       'galutinis valymas; kūdikio lovelė ir aukšta kėdutė (pagal pageidavimą). '
                                       'Valymo paslauga viešnagės metu teikiama tik gyvenant ilgiau nei 10 naktų.'),
    ('Pastaba: baseinas', 'Jūsų viešnagė (spalio 29–31 d.) yra orientacinio sezono pabaigoje, todėl baseinas gali būti jau '
                          'uždarytas. Verta pasitikslinti iš anksto.'),
    ('Stovėjimo aikštelė', 'Kiekvienam apartamentui skiriama vieta vienam automobiliui. Dideli automobiliai, kurie netelpa į '
                           'aikštelę, ir papildomi automobiliai statomi už rezidencijos teritorijos, viešoje aikštelėje. '
                           '<br><em>Pastaba: jūsų grupė važiuoja dviem automobiliais, todėl jei apgyvendinimas yra vienas '
                           'apartamentas, antrą automobilį reikės statyti viešoje aikštelėje.</em>'),
    ('Į kainą neįskaičiuota', 'Turistinis mokestis.'),
    ('Užstatas atvykus', 'Kredito kortelė kaip garantija arba 150 € grynaisiais.'),
    ('Ypatingi pageidavimai', 'Jei rezervuodami nurodėte konkrečių pageidavimų (pvz., aukštą, kampinį apartamentą, '
                              'apartamento numerį ir pan.), jie užfiksuoti ir bus stengiamasi juos įvykdyti, tačiau '
                              'garantuoti negalima.'),
    ('Booking.com klientų aptarnavimas', '<a class="ct" href="tel:+442033202624">+44 20 3320 2624</a>'
                                         '<a class="ct" href="tel:+390223331342">+39 02 2333 1342</a>'),
]


def stay_more(title, intro, items):
    dl = ''.join(f'<div><dt>{t}</dt><dd>{d}</dd></div>' for t, d in items)
    return (f'<details class="stay-more"><summary><span>{esc(title)}</span>{CHV}</summary>'
            f'<div class="sm-body"><p class="sm-intro">{intro}</p><dl class="sm-list">{dl}</dl></div></details>')


FLIGHTS = (flight('Spalio 29 d., ketvirtadienis', ('VNO', 'Vilnius', '18:25'), ('MXP', 'Milanas Malpensa', '20:05'),
                  'Italijos laiku')
           + flight('Lapkričio 2 d., pirmadienis', ('MXP', 'Milanas Malpensa', '21:55'), ('VNO', 'Vilnius', '01:30'),
                    'lapkričio 3 d.'))
STAYS = (stay('south', 'Pietūs', 'Residence Corte Ferrari', 'Moniga del Garda', 'Spalio 29–31 d. (2 naktys)',
              'Residence Corte Ferrari Moniga del Garda',
              more=stay_more('Svarbi informacija apie rezidenciją',
                             'Rezervacijos informacija, išversta į lietuvių kalbą. Mūsų pastabos pažymėtos žodžiu „Pastaba“.', CF_INFO), sid='stay-corte-ferrari')
         + stay('north', 'Šiaurė', 'Residence Segattini', 'Riva del Garda', 'Spalio 31 – lapkričio 2 d. (2 naktys)',
                'Residence Segattini Riva del Garda',
                more=stay_more('Svarbi informacija apie rezidenciją',
                               'Rezidencijos laiškas svečiams (viešnagė 2026-10-31 – 2026-11-02), išverstas į lietuvių kalbą. '
                               'Planuojamas atvykimas (16:20) ir išsiregistravimas (9:00) telpa į registratūros darbo laiką.',
                               SEG_INFO), sid='stay-segattini'))

d1, d5 = DAYS[0], DAYS[4]
sun_rng = f'{fm(min(d["set"] for d in DAYS))}–{fm(max(d["set"] for d in DAYS))}'
dusk_rng = f'{fm(min(d["dusk"] for d in DAYS))}–{fm(max(d["dusk"] for d in DAYS))}'

CSS = r'''
.sum-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}
.sum-card{border:1px solid rgba(0,0,0,.12);border-radius:12px;padding:14px}
.sk{display:block;font-size:13px;opacity:.7}
.sum-card b{display:block;font-size:24px;margin:2px 0}
.sum-t{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0 16px}
.sum-t th,.sum-t td{padding:6px 8px;border-bottom:1px solid rgba(0,0,0,.1);text-align:left}
.prog{border-top:1px solid rgba(0,0,0,.12);padding-top:12px}
.pbar{height:12px;border-radius:99px;background:rgba(0,0,0,.1);overflow:hidden;margin:10px 0 6px}
.pfill{height:100%;width:0;background:var(--terra);transition:width .6s}
.pline{font-weight:600;margin:6px 0}
.pdet{font-size:14px;opacity:.8;margin:0}
.seeh{font:600 12px/1.2 system-ui,sans-serif;text-transform:uppercase;letter-spacing:.06em;margin:12px 0 4px;opacity:.85}
.see{margin:0;padding-left:18px}
.see li{margin:3px 0}
.drink{font-size:13px;margin:10px 0 0;opacity:.85}
.nb{display:inline-block;margin-left:8px;background:#c4531f;color:#fff;font:600 11px/1 system-ui,sans-serif;letter-spacing:.06em;padding:3px 6px;border-radius:4px;vertical-align:2px}
@font-face{font-family:"Inter";font-style:normal;font-weight:400 800;font-display:swap;src:url(fonts/inter.woff) format("woff")}
@font-face{font-family:"Literata";font-style:normal;font-weight:500 700;font-display:swap;src:url(fonts/literata.woff) format("woff")}
@font-face{font-family:"Literata";font-style:italic;font-weight:500;font-display:swap;src:url(fonts/literata-italic.woff) format("woff")}
:root{
  --sand:#EFE4CC;--sand-d:#E6D8B8;--paper:#FBF6E9;--ink:#2B241B;--muted:#6B5F4F;
  --terra:#B4532A;--terra-d:#8C3B18;--terra-t:#F3D9C8;
  --lake:#123F5E;--lake-t:#CFE0E8;
  --olive:#5C6B2E;--olive-d:#44521E;--olive-t:#DDE3C4;
  --land:#34401F;--line:rgba(43,36,27,.18);--now:#B4532A;
  --display:"Literata",Georgia,"Times New Roman",serif;
  --text:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --gutter:clamp(16px,4.5vw,48px);--max:1080px;
  --gl:max(var(--gutter),env(safe-area-inset-left));--gr:max(var(--gutter),env(safe-area-inset-right));
}
a,button,summary{touch-action:manipulation}
button{font-family:inherit}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{scroll-behavior:smooth;scroll-padding-top:68px;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--sand);color:var(--ink);font:400 17px/1.55 var(--text)}
body.has-bar{padding-bottom:calc(86px + env(safe-area-inset-bottom))}
img,svg{max-width:100%}
a{color:inherit}
:focus-visible{outline:3px solid var(--terra);outline-offset:2px}
.nav :focus-visible,.hero :focus-visible{outline-color:var(--sand)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:8px;top:-60px;background:var(--paper);padding:10px 14px;border-radius:8px;z-index:50}
.skip:focus{top:8px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important;animation:none!important}}

/* nav */
.nav{position:sticky;top:0;z-index:20;background:var(--land);color:var(--sand);border-bottom:1px solid rgba(239,228,204,.18)}
.nav-in{max-width:var(--max);margin:0 auto;padding:0 var(--gr) 0 var(--gl);display:flex;align-items:center;gap:18px;min-height:52px;overflow-x:auto;scrollbar-width:none}
.nav-in::-webkit-scrollbar{display:none}
.nav-brand{font-family:var(--display);font-weight:600;font-size:19px;margin-right:auto;white-space:nowrap}
.nav a:not(.nav-brand){text-decoration:none;font-weight:600;font-size:15px;padding:15px 2px;white-space:nowrap}
@media (max-width:480px){.nav-in{gap:14px}.nav-brand{display:none}.nav a:not(.nav-brand){font-size:14.5px}.nav-in{justify-content:space-between}}
.nav a:not(.nav-brand):hover{text-decoration:underline;text-underline-offset:5px}
.nav #nav-today{background:var(--terra);color:#fff;border-radius:99px;padding:6px 12px;font-size:14px}

/* hero */
.hero{background:var(--land);color:var(--sand)}
.hero-in{max-width:var(--max);margin:0 auto;padding:clamp(26px,5vw,60px) var(--gr) clamp(34px,6vw,72px) var(--gl);display:grid;gap:26px;grid-template-columns:minmax(0,1fr);align-items:start}
.hero-head,.hero-facts{display:grid;gap:22px;justify-items:start;align-content:start;min-width:0}
@media (min-width:860px){
  .hero-in{grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr);grid-template-areas:"head map" "facts map";column-gap:48px;row-gap:26px;align-content:center}
  .hero-head{grid-area:head;align-self:end}
  .hero-facts{grid-area:facts;align-self:start}
  .mapbox{grid-area:map;align-self:center}
}
h1{margin:0;font-family:var(--display);font-weight:600;line-height:1.02;letter-spacing:-.012em}
.h1-main{display:block;font-size:clamp(40px,10.5vw,96px);overflow-wrap:break-word}
.h1-sub{display:block;margin-top:.3em;font-size:clamp(22px,4.2vw,36px);font-weight:400;color:#EDB791;letter-spacing:0}
.countdown{margin:0;padding:6px 14px;border:1.5px solid #D9784D;border-radius:99px;font-weight:600;font-size:15px;color:#F4CDB0}
.facts{margin:0;padding:0;list-style:none;width:100%;max-width:30rem;border-top:1px solid rgba(239,228,204,.3)}
.facts li{padding:10px 0;border-bottom:1px solid rgba(239,228,204,.3);font-size:18px}
.stats{margin:0;display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 22px}
.stats span{font-size:15px}
.stats b{font-family:var(--display);font-size:clamp(32px,6vw,50px);font-weight:600;line-height:1;margin-right:.2em;vertical-align:-.04em}
@media (min-width:480px){.stats span{font-size:16px}.stats{gap:6px 28px}}
@media (max-width:479px){.stats{display:grid;grid-template-columns:repeat(3,auto);justify-content:space-between;width:100%;gap:0}.stats span{font-size:14.5px;line-height:1.25}.stats b{display:block;margin:0 0 4px}}
.tagline{margin:0;font-family:var(--display);font-style:italic;font-size:clamp(19px,3vw,23px);color:#E6D3AE}
.mapbox{width:100%;max-width:430px;justify-self:center}
.lakemap{display:block;width:100%;height:auto;border-radius:22px 22px 70px 22px}
.lakemap.dm{border-radius:16px}
.lakename{font-family:var(--display);font-style:italic;font-weight:500;fill:#EFE4CC;fill-opacity:.62}
.landname{font-family:var(--display);font-style:italic;font-weight:500;fill:#EFE4CC;fill-opacity:.4}
.town{font-family:var(--text);font-weight:500;fill:#EFE4CC;fill-opacity:.78}
.lab{font-family:var(--text);font-weight:700;fill:#F6EEDA;paint-order:stroke;stroke:#1d2613;stroke-linejoin:round}
.lab .ln{font-weight:700}
.lab .lt{font-weight:600;fill:#F4D9A8;font-variant-numeric:tabular-nums}
.lab.ex{fill:#F4D9A8}
.baseA{fill:none;stroke:#E4895E;stroke-width:2;stroke-dasharray:3 3}
.baseB{fill:#EFE4CC;stroke:#80BCDA;stroke-width:3}
.rc{fill:none;stroke:#1d2613;stroke-opacity:.6;stroke-linecap:round;stroke-linejoin:round}
.rt{fill:none;stroke:var(--c);stroke-linecap:round;stroke-linejoin:round}
.rw{fill:none;stroke:#F6EEDA;stroke-linecap:round;stroke-opacity:.95}
.dl .rc,.dl .rt,.dl .rw{opacity:.32;transition:opacity .2s}
.dl.on .rc,.dl.on .rt,.dl.on .rw{opacity:1}
.dl.all .rc,.dl.all .rt,.dl.all .rw{opacity:.85}
.plabel{font:700 12px var(--text);fill:#F6EEDA;paint-order:stroke;stroke:#1d2613;stroke-width:3px;stroke-linejoin:round;pointer-events:none}
/* map fx: sky arc, mountains, waves, boats, route flow */
.mapbox .sky{position:relative;border-radius:22px 22px 0 0;overflow:hidden;--sk1:#17496E;--sk2:#3A7397;background:#34401F linear-gradient(180deg,var(--sk1) 0%,var(--sk2) 70%,#34401F 78%)}
.sky.ph-gold{--sk1:#1F2F57;--sk2:#A8573A}
.sky.ph-night{--sk1:#0A1424;--sk2:#1A2C46}
.sky svg{display:block;width:100%;height:auto}
#ovmap{border-radius:0 0 70px 22px}
.sky .stars{opacity:0;transition:opacity .8s}
.sky.ph-night .stars{opacity:1}
.sky.ph-gold .stars{opacity:.3}
.star{fill:#FFF8E6;animation:tw 3.6s ease-in-out infinite}
.star.s1{animation-duration:4.8s;animation-delay:-1.7s}
.star.s2{animation-duration:2.9s;animation-delay:-.8s}
@keyframes tw{50%{opacity:.2}}
.moon{fill:#F3EBD3;opacity:0;transition:opacity .8s}
.sky.ph-night .moon{opacity:.92}
.cl path{fill:#fff;opacity:.12}
.sky.ph-night .cl path{opacity:.05}
.cl{animation:cloud 110s linear infinite}
.c1{transform:translateX(40px);animation-delay:-25s}
.c2{transform:translateX(250px);animation-duration:150s;animation-delay:-95s}
@keyframes cloud{from{transform:translateX(-50px)}to{transform:translateX(375px)}}
.arc-t{fill:none;stroke:#FFF8E6;stroke-opacity:.5;stroke-width:1.4;stroke-dasharray:1.5 4.5;stroke-linecap:round}
.arc-d{fill:none;stroke:#FFD27A;stroke-width:2.8;stroke-linecap:round}
.sun .core{fill:#FFD66E;stroke:#FFF1C2;stroke-width:1.4}
.sky.ph-gold .sun .core{fill:#FFAB52}
.sun .rays{stroke:#FFD978;stroke-width:1.8;stroke-linecap:round;transform-box:fill-box;transform-origin:center;animation:spin 30s linear infinite}
.sun .glow{transform-box:fill-box;transform-origin:center;animation:glow 4.6s ease-in-out infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes glow{50%{transform:scale(1.2);opacity:.75}}
.sky.ph-night .sun{display:none}
.sky.ph-night .arc-d{stroke-opacity:.45}
.rg1{fill:#435045}
.rg2{fill:#34401F}
.sky text{font-family:var(--text);fill:#FFF8E6}
.sky .sk-t,.sky .sk-d{font-weight:700;font-size:12.5px}
.sky .sk-big{font-family:var(--display);font-weight:600;font-size:23px}
.sky .sk-s{font-weight:600;font-size:12.5px}
.sky .sk-k{font-weight:500;font-size:11.5px;fill:#D9CFB3}
.sky .sk-v{font-weight:700;font-size:15px;font-variant-numeric:tabular-nums}
.hillsS path{fill:#3D4A26}
.waves{fill:none;stroke:#BFE3F2;stroke-linecap:round}
.wg{opacity:.32;animation:wv 7s ease-in-out infinite}
.wg1{animation-duration:8.6s;animation-delay:-4s}
.wg2{animation-duration:6.2s;animation-delay:-2.6s}
.wg3{animation-duration:9.4s;animation-delay:-6s}
@keyframes wv{0%{opacity:0;transform:translateX(-3px)}40%{opacity:.6}65%{opacity:.5}100%{opacity:0;transform:translateX(4px)}}
.boat .hull{fill:#102536}
.boat .sail{fill:#F6EEDA}
.boat .s2{fill:#DCCDAB}
.b1{animation:b1 84s ease-in-out infinite alternate}
.b2{animation:b2 66s ease-in-out -22s infinite alternate}
.bob{transform-box:fill-box;transform-origin:50% 100%;animation:bob 3.4s ease-in-out infinite}
@keyframes bob{50%{transform:rotate(4deg) translateY(.5px)}}
.rf{fill:none;stroke:#1d2613;stroke-opacity:.55;stroke-linecap:round;display:none}
.dl.on .rf{display:inline}
.paused,.paused *{animation-play-state:paused!important}
@media (prefers-reduced-motion:reduce){.dl.on .rf{display:none}}
/*%%FXCSS%%*/
#ovmap:not([data-sel="0"]) .plabel{display:none}
#ovmap .ovs{display:none}
#ovmap .dl.on .ovs{display:inline}
.lp .dot{fill:var(--c);stroke:#F6EEDA}
.lp .num{font-family:var(--text);font-weight:800;fill:#1d1a12;text-anchor:middle;dominant-baseline:central;pointer-events:none}
.lp .ring{fill:none;stroke:#fff;opacity:0;transform-box:fill-box;transform-origin:center}
.lp.cur .ring,.lp.nxt .ring{opacity:1;animation:pulse 1.8s ease-out infinite}
.lp.cur .dot{stroke:#fff;stroke-width:3}
@keyframes pulse{0%{transform:scale(.7);opacity:1}100%{transform:scale(1.7);opacity:0}}
.pin{cursor:pointer;outline:none;-webkit-tap-highlight-color:transparent}
.pin .hit{fill:transparent;stroke:none}
.pin .dot{fill:var(--pc);stroke:#EFE4CC;stroke-width:2;transform-box:fill-box;transform-origin:center;transition:transform .15s}
.pin text{font:700 11.5px var(--text);fill:#1d1a12;text-anchor:middle;dominant-baseline:central;pointer-events:none}
.pin:hover .dot{transform:scale(1.22)}
.pin:focus-visible .dot{transform:scale(1.22)}
.pin:focus-visible .dot{stroke:#fff;stroke-width:3.5}
.pin.is-today .dot,.pin.sel .dot{stroke:#fff;stroke-width:3.5}
.pin.sel .dot{transform:scale(1.2)}
.pin-south{--pc:#E4895E}.pin-mid{--pc:#BBC76C}.pin-north{--pc:#80BCDA}
.legend{margin:14px 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:14.5px}
.legend li{display:flex;align-items:center;gap:8px}
.legend i{width:13px;height:13px;border-radius:50%;background:var(--pc);flex:none}
.legend .l1{--pc:#E4895E}.legend .l2{--pc:#BBC76C}.legend .l3{--pc:#80BCDA}
.mapnote{margin:8px 0 0;font-size:13.5px;color:#C9BFA2}
.dsel{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 0}
.dbtn{font:700 16px var(--text);min-width:44px;min-height:44px;padding:0 12px;border-radius:99px;border:2px solid var(--b,#EFE4CC);background:transparent;color:var(--sand);cursor:pointer}
.dbtn.z-south{--b:#E4895E}.dbtn.z-mid{--b:#BBC76C}.dbtn.z-north{--b:#80BCDA}
.dbtn[aria-pressed="true"]{background:var(--b,#EFE4CC);color:#1d1a12}
.dbtn.all{padding:0 13px;font-size:15px}
.dinfo{margin:12px 0 0;padding:12px 14px;border:1px solid rgba(239,228,204,.3);border-radius:14px;background:rgba(239,228,204,.07)}
.dinfo p{margin:0}
.di-t{font-family:var(--display);font-weight:600;font-size:20px;line-height:1.2}
.di-s{margin-top:4px!important;font-size:14.5px;color:#D9CFB3}
.dinfo .go{display:inline-block;margin-top:8px;font-weight:700;font-size:15px;color:#F4CDB0;text-underline-offset:3px;padding:6px 0}

/* sections */
.sec{padding:clamp(40px,7vw,84px) var(--gr) clamp(40px,7vw,84px) var(--gl)}
.sec-days{background:var(--sand-d)}
.wrap{max-width:var(--max);margin:0 auto}
h2{margin:0 0 clamp(18px,3vw,30px);font-family:var(--display);font-weight:600;font-size:clamp(31px,5.4vw,50px);line-height:1.08;letter-spacing:-.01em}
.head-row{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:10px 20px;margin-bottom:clamp(14px,2.4vw,22px)}
.head-row h2{margin:0}
.btn{font:600 15px var(--text);color:var(--ink);background:transparent;border:1.5px solid var(--ink);border-radius:99px;padding:9px 18px;min-height:42px;cursor:pointer}
.btn:hover{background:var(--ink);color:var(--sand)}
p>a:only-child{display:inline-block;padding:5px 0}  /* atskira nuoroda eilutėje: patogesnis paspaudimas */
.daynote{margin:0 0 18px;font-size:15px;color:#5A4F40;max-width:46rem}

/* shared bits */
.card{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:20px}
.mlink{display:inline-flex;align-items:center;gap:6px;align-self:flex-start;font-size:14.5px;font-weight:600;color:var(--zd,var(--terra-d));text-decoration:none;border:1.5px solid currentColor;border-radius:99px;padding:5px 12px 5px 10px;min-height:36px}
.mlink:hover{background:var(--zt,var(--terra-t))}
.z-south{--z:var(--terra);--zd:var(--terra-d);--zt:var(--terra-t)}
.z-mid{--z:var(--olive);--zd:var(--olive-d);--zt:var(--olive-t)}
.z-north{--z:var(--lake);--zd:var(--lake);--zt:var(--lake-t)}

/* logistics */
.logi{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
@media (min-width:800px){.logi{grid-template-columns:minmax(0,1.25fr) minmax(0,1fr)}.logi .stays{grid-column:1/-1}}
.logi h3{margin:0 0 14px;font-family:var(--display);font-weight:600;font-size:25px;line-height:1.15}
.flights{background:var(--lake);color:var(--sand);border-color:var(--lake);border-radius:16px 16px 16px 44px;padding:22px}
.flight+.flight{margin-top:18px;padding-top:18px;border-top:1px dashed rgba(239,228,204,.4)}
.fdate{margin:0 0 8px;font-size:15px;color:#BFD6E2}
.fline{display:grid;grid-template-columns:auto minmax(30px,1fr) auto;align-items:start;gap:10px}
.end b{display:block;font-family:var(--display);font-size:clamp(30px,6vw,38px);font-weight:600;line-height:1}
.end span{display:block;font-size:22px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:4px}
.end i{display:block;font-style:normal;font-size:14px;color:#BFD6E2}
.end small{display:block;font-size:13.5px;font-weight:600;color:#F0BE9B}
.end.r{text-align:right}
.route{position:relative;height:24px;border-top:2px dashed rgba(239,228,204,.45);margin-top:18px}
.route .plane{position:absolute;left:50%;top:-14px;transform:translateX(-50%) rotate(90deg);background:var(--lake);color:var(--sand);padding:2px 0}
.car p{margin:0 0 6px}
.car .big{font-family:var(--display);font-weight:600;font-size:23px;line-height:1.2}
.car dl{margin:12px 0 0;display:grid;grid-template-columns:auto 1fr;gap:6px 14px}
.car dt{color:var(--muted)}.car dd{margin:0;font-weight:600}
@media (max-width:480px){.car dl{grid-template-columns:1fr;gap:0}.car dd{margin-bottom:10px}}
.stays-in{display:grid;gap:14px;grid-template-columns:minmax(0,1fr);align-items:start}
@media (min-width:640px){.stays-in{grid-template-columns:1fr 1fr}}
.stay{display:flex;flex-direction:column;align-items:flex-start;gap:4px;border:1px solid var(--line);border-left:7px solid var(--z);border-radius:6px 14px 14px 6px;padding:14px 16px;background:#fff9}
.stay-label{margin:0;font-weight:700;color:var(--zd);font-size:15px}
.stay-name{margin:0;font-family:var(--display);font-weight:600;font-size:23px;line-height:1.15}
.stay-meta{margin:0 0 8px;color:var(--muted)}
.stay-more{align-self:stretch;margin-top:10px}
.stay-more>summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:10px;font-weight:700;font-size:15px;color:var(--zd);border:1.5px solid var(--zd);border-radius:12px;padding:9px 12px 9px 14px;min-height:44px;-webkit-tap-highlight-color:transparent}
.stay-more>summary::-webkit-details-marker{display:none}
.stay-more>summary:hover{background:var(--zt)}
.stay-more[open]>summary{background:var(--zt)}
.stay-more[open]>summary .chv{transform:rotate(180deg)}
.stay-more .chv{margin-top:0}
.sm-body{padding:12px 2px 2px}
.sm-intro{margin:0 0 12px;font-size:14.5px;color:var(--muted)}
.sm-list{margin:0;display:grid;gap:14px}
.sm-list dt{font-weight:700;color:var(--zd);font-size:15px}
.sm-list dd{margin:2px 0 0;font-size:15.5px;line-height:1.5}
.sm-list a{color:var(--zd);font-weight:600;overflow-wrap:break-word}
.sm-list a.ct{display:block;padding:8px 0;min-height:36px}
.bin{display:flex;align-items:center;gap:8px;margin-top:4px}
.bin i{flex:none;width:12px;height:12px;border-radius:50%;box-shadow:0 0 0 1.5px rgba(43,36,27,.35)}

/* days */
.days{display:grid;gap:14px}
.day{background:var(--paper);border:1px solid var(--line);border-left:8px solid var(--z);border-radius:6px 20px 20px 6px}
.day>summary{list-style:none;cursor:pointer;-webkit-tap-highlight-color:transparent;display:block}
.day>summary::-webkit-details-marker{display:none}
.dsum{margin:0;font:inherit;display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:14px;align-items:center;padding:13px 16px 13px 14px;min-height:72px}
.dnum{font-family:var(--display);font-weight:700;font-size:46px;line-height:1;color:var(--z);min-width:.75em;text-align:center}
.dtitle{display:block;font-family:var(--display);font-weight:600;font-size:clamp(19px,3.6vw,27px);line-height:1.15}
.ddate{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;margin-top:3px;font-size:14.5px;color:var(--muted)}
.badge{background:var(--z);color:#fff;border-radius:99px;padding:1px 10px;font-size:13px;font-weight:700}
.day.is-done .badge{background:var(--muted)}
.day.is-done .dtitle{opacity:.7}
.day.is-done .dnum{opacity:.85}
.chev{width:24px;height:24px;color:var(--zd);transition:transform .2s}
.day[open] .chev{transform:rotate(180deg)}
.dbody{display:grid;gap:20px;padding:6px 18px 22px 18px;grid-template-columns:minmax(0,1fr);grid-template-areas:"stats" "tl" "must" "map"}
@media (min-width:900px){
  .dbody{grid-template-columns:minmax(0,1fr) 360px;grid-template-areas:"stats stats" "tl map" "must map";padding:8px 24px 26px 76px;column-gap:30px}
  .dmap{position:sticky;top:72px;align-self:start}
}
.dstats{grid-area:stats}.dtl{grid-area:tl;min-width:0}.dmust{grid-area:must}.dmap{grid-area:map;min-width:0}
.dsec h4,.dmap h4{margin:0 0 9px;font-size:15.5px;font-weight:700;color:var(--zd)}
.must{margin:0;font-family:var(--display);font-weight:500;font-size:clamp(19px,3.2vw,22px);line-height:1.4;padding-left:14px;border-left:3px solid var(--z)}

/* day stats */
.dstats{display:grid;gap:10px;grid-template-columns:1fr 1fr}
.st{background:var(--zt);border-radius:14px;padding:10px 12px 11px;display:flex;flex-direction:column;gap:2px;min-width:0}
.st.wide{grid-column:1/-1}
.st-k{display:flex;align-items:center;gap:6px;font-size:13.5px;font-weight:700;color:var(--zd)}
.st b{font-family:var(--display);font-size:clamp(18px,4.8vw,22px);line-height:1.15;font-weight:600}
.st:not(.wide) small{margin-top:1px}
.st small{font-size:13.5px;color:var(--muted);line-height:1.3}
.sun3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:2px}
.sun3 i{display:block;font-style:normal;font-size:12.5px;color:var(--muted)}
.sun3 b{font-variant-numeric:tabular-nums}
.st-wx{grid-column:1/-1;gap:5px}
.wx-main{display:flex;align-items:center;gap:6px 10px;flex-wrap:wrap}
.wx-main .wico{width:34px;height:34px;color:var(--zd);flex:none}
.wx-temp{font-family:var(--display);font-size:clamp(22px,6vw,28px);line-height:1.1;font-weight:600}
.wx-cond{font-weight:700;font-size:15.5px}
.wx-meta{margin:0;display:flex;flex-wrap:wrap;gap:3px 14px;font-size:14.5px}
.wx-meta span{display:inline-flex;align-items:center;gap:5px}
.wx-meta .ico,.wx-alt .ico{color:var(--zd);flex:none}
.wx-hrs{display:grid;grid-template-columns:repeat(var(--n,4),minmax(0,1fr));gap:6px;margin-top:3px;max-width:560px}
.wx-h{background:rgba(255,255,255,.62);border-radius:10px;padding:6px 3px 5px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:1px;min-width:0}
.wx-h i{font-style:normal;font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.wx-h .ico{width:24px;height:24px;color:var(--zd)}
.wx-h b{font-family:var(--display);font-size:17px;line-height:1.2;font-weight:600}
.wx-h small{font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.wx-alt{margin:0;font-size:14.5px}
.wx-adv{margin:3px 0 0;font-weight:600;font-size:15px;line-height:1.4}
.wx-adv:empty{display:none}
.wx-src{margin:1px 0 0;font-size:12.5px;color:var(--muted)}
.dl-bar{height:8px;border-radius:99px;background:rgba(43,36,27,.14);overflow:hidden;margin-top:8px}
.dl-bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#E9B44C,#E4895E);border-radius:inherit;transition:width .6s}
.dl-t{margin:6px 0 0;font-weight:700;font-size:15.5px;line-height:1.35}
.st-sun.live{outline:2px solid var(--z)}
@media (min-width:700px){.dstats{grid-template-columns:1fr 1fr 1.7fr}.dstats .st.wide{grid-column:auto}}

/* timeline */
.tl{list-style:none;margin:0;padding:0;position:relative}
.tl::before{content:"";position:absolute;left:8px;top:14px;bottom:14px;width:2px;background:var(--zt)}
.ev,.note{position:relative;padding-left:30px;margin:0}
.ev{margin-bottom:2px}
.mk{position:absolute;left:3px;top:14px;width:11px;height:11px;background:var(--z);transform:rotate(45deg);box-shadow:0 0 0 3px var(--paper)}
.note .mk{background:var(--muted);width:9px;height:9px;left:4px;top:11px}
.note{padding-top:2px;padding-bottom:6px}
.note p{margin:0;font-size:14.5px;color:var(--ink);background:#fff9;border:1.5px dashed var(--z);border-radius:10px;padding:8px 12px}
.leg{display:flex;flex-wrap:wrap;align-items:center;gap:2px 8px;padding:7px 0 5px;font-size:14px;color:var(--muted);min-height:34px}
.leg .ico{flex:none;color:var(--zd)}
.lg-t{font-weight:700;color:var(--zd)}
.lg-n:not(:empty)::before{content:"· "}
.lg-live{font-weight:800;color:var(--now)}
.leg.on{color:var(--ink)}
.leg.on .lg-t{background:var(--now);color:#fff;border-radius:99px;padding:0 9px}
.evd>summary{list-style:none;cursor:pointer;display:block;padding:6px 0 5px;-webkit-tap-highlight-color:transparent}
.evd>summary::-webkit-details-marker{display:none}
.evd.plain{padding:6px 0 5px}
.evs{display:flex;gap:10px;align-items:flex-start}
.evl{display:block;flex:1;min-width:0}
.evc{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}
.t{display:inline-block;font-weight:700;font-size:14px;line-height:1.3;font-variant-numeric:tabular-nums;background:var(--zt);color:var(--zd);border-radius:8px;padding:3px 10px}
.kick{font-size:12.5px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;color:var(--zd)}
.bd{display:inline-block;border-radius:99px;padding:1px 10px;font-size:12.5px;font-weight:800;letter-spacing:.02em}
.bd-now{background:var(--now);color:#fff}
.bd-next{background:var(--ink);color:var(--paper)}
.evt{display:block;margin-top:4px;font-weight:700;font-size:17.5px;line-height:1.3;overflow-wrap:break-word}
.chv{flex:none;width:20px;height:20px;margin-top:2px;color:var(--zd);transition:transform .2s}
.evd[open]>summary .chv{transform:rotate(180deg)}
.evb{display:flex;flex-direction:column;align-items:flex-start;gap:9px;padding:2px 0 10px}
.evb p{margin:0}
.ph{display:block;flex:none;width:60px;height:60px;border-radius:12px;overflow:hidden;background:var(--zt);box-shadow:0 0 0 1.5px var(--zt)}
.ph.no{display:none}
.ph img{display:block;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity .3s}
.ph.ok img{opacity:1}
html:not(.js) .ph,html:not(.js) .dsel,html:not(.js) .dinfo,html:not(.js) #toggle-all{display:none}
.evd:not([open]) .ph{display:none}
.cred{font-size:12.5px;color:var(--muted);text-underline-offset:3px}
.opts{display:grid;gap:12px;grid-template-columns:minmax(0,1fr);width:100%}
@media (min-width:620px) and (max-width:899px){.opts{grid-template-columns:1fr 1fr}}
.opt{display:flex;flex-direction:column;align-items:flex-start;gap:6px;border:1.5px solid var(--z);border-radius:12px 12px 12px 26px;padding:14px 16px 16px;background:#fffdf6}
.opt-top{display:flex;align-items:center;gap:10px}
.ab{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--z);color:#fff;font-weight:800;font-size:15px}
.tag{font-size:14px;font-weight:600;color:var(--zd)}
.oname{margin:0;font-family:var(--display);font-weight:600;font-size:21px;line-height:1.18}
.odesc{margin:0 0 6px;color:var(--muted)}
/* live states */
.ev.is-past{opacity:.6}
.ev.is-past .mk{background:var(--muted)}
.ev.is-past .evt{font-weight:600}
.ev.is-cur{background:var(--zt);border-radius:14px;box-shadow:0 0 0 2px var(--z);margin:6px 0 8px;padding-right:12px}
.ev.is-cur .t{background:var(--paper)}
.ev.is-cur .mk{background:var(--now);width:13px;height:13px;left:2px;top:16px;box-shadow:0 0 0 3px var(--zt);animation:blink 1.6s ease-in-out infinite}
.ev.is-cur .leg{display:none}
.ev.is-next{box-shadow:inset 3px 0 0 var(--ink)}
@keyframes blink{50%{box-shadow:0 0 0 6px rgba(180,83,42,.25)}}
.dmbox{border-radius:16px;overflow:hidden;background:var(--land)}
.dmnote{margin:8px 0 10px;font-size:13.5px;color:var(--muted)}

/* live bar */
.livebar{position:fixed;left:0;right:0;bottom:0;z-index:40;background:var(--ink);color:var(--paper);border-top:3px solid var(--terra);padding:9px var(--gr) max(10px,env(safe-area-inset-bottom)) var(--gl);box-shadow:0 -8px 28px rgba(0,0,0,.28)}
.lb-in{max-width:var(--max);margin:0 auto;display:flex;flex-direction:column;gap:5px}
.lb-main{all:unset;box-sizing:border-box;flex:1;min-width:0;cursor:pointer;display:block;padding:2px 0}
.lb-main:focus-visible{outline:3px solid var(--sand);outline-offset:3px;border-radius:6px}
.lb-a{display:block;font-weight:800;font-size:16px;line-height:1.25;overflow-wrap:break-word}
.lb-b{display:block;font-size:14px;line-height:1.3;color:#E3D8BE;margin-top:2px}
.lb-r{display:flex;flex-wrap:wrap;gap:0 14px;font-size:13px;line-height:1.35;color:#E3D8BE;border-top:1px solid rgba(239,228,204,.2);padding-top:5px}
.lb-r b{color:#F4D9A8;font-variant-numeric:tabular-nums}
.lb-r a{color:#F4CDB0;margin-left:auto}
.lb-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#E4895E;margin-right:7px;animation:blink2 1.6s ease-in-out infinite}
@keyframes blink2{50%{opacity:.35}}

/* tips */
.tips{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
@media (min-width:800px){.tips{grid-template-columns:1fr 1fr}}
.tip{background:var(--paper);border:2.5px solid var(--terra);border-radius:20px 20px 20px 6px;padding:22px}
.tip h3{margin:0 0 10px;font-family:var(--display);font-weight:600;font-size:clamp(23px,4vw,28px);line-height:1.15}
.tip h3 span{margin-right:8px}
.tip p{margin:0 0 10px}
.tip p:last-child{margin-bottom:0}
.tip a{color:var(--terra-d);font-weight:600;text-underline-offset:3px}
@media (min-width:800px){.tip.wide{grid-column:1/-1}}

@media (pointer:coarse){.mlink{min-height:44px;padding:8px 14px 8px 12px}.btn{min-height:46px}}
footer{padding:26px var(--gr) max(40px,env(safe-area-inset-bottom)) var(--gl);background:var(--land);color:#D9CFB3;font-size:14.5px}
footer p{max-width:var(--max);margin:0 auto 10px}
footer a{color:#F4CDB0;text-underline-offset:3px}

@media print{
  .nav,.mapbox .mapnote,.btn,.mlink,.livebar,.dsel,.dinfo,.sky{display:none!important}
  #ovmap{border-radius:22px 22px 70px 22px}
  body{background:#fff;padding-bottom:0!important}.hero{background:#fff;color:#000}.sec-days{background:#fff}
  .ev.is-past{opacity:1}
}
'''

JS = r'''
(function(){
  'use strict';
  function $(s,r){return (r||document).querySelector(s);}
  function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));}
  function da(el,n){return el.getAttribute('data-'+n);}  // SVG elementams (dataset senesnėse naršyklėse nepalaikomas)
  var T0=Date.UTC(2026,9,29);
  var preview=null;
  (function(){
    var m=/[?&]t=(\d{4})-(\d{2})-(\d{2})(?:T|%20|\+| )(\d{2})(?::|%3A)(\d{2})/i.exec(location.search);
    if(m)preview=(Date.UTC(+m[1],+m[2]-1,+m[3],+m[4],+m[5])-T0)/60000;
  })();
  var loadedAt=Date.now();
  var fmt=null;
  try{fmt=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Rome',year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'numeric',hourCycle:'h23'});}catch(e){fmt=null;}
  function nowAbs(){
    if(preview!==null)return preview+(Date.now()-loadedAt)/60000;
    var d=new Date(),y,mo,da,h,mi;
    if(fmt){var p={};fmt.formatToParts(d).forEach(function(x){p[x.type]=x.value;});y=+p.year;mo=+p.month;da=+p.day;h=(+p.hour)%24;mi=+p.minute;}
    else{y=d.getFullYear();mo=d.getMonth()+1;da=d.getDate();h=d.getHours();mi=d.getMinutes();}
    return (Date.UTC(y,mo-1,da,h,mi)-T0)/60000;
  }
  function hhmm(a){var m=((Math.round(a)%1440)+1440)%1440,h=Math.floor(m/60),mi=m%60;return (h<10?'0':'')+h+':'+(mi<10?'0':'')+mi;}
  function dur(m){m=Math.max(0,Math.round(m));if(m<1)return 'mažiau nei min.';if(m<60)return m+' min';var h=Math.floor(m/60),r=m%60;return h+' val.'+(r?' '+r+' min':'');}
  function dienos(n){var a=n%10,b=n%100;if(a===1&&b!==11)return n+' diena';if(a===0||(b>=11&&b<=19))return n+' dienų';return n+' dienos';}

  var days=$$('details.day').map(function(el,i){return {el:el,i:i,badge:$('.badge',el),first:1e9,last:-1e9,stats:$('.dstats',el)};});
  var evs=$$('li.ev[data-a]').map(function(el){
    var d=el.dataset;
    return {el:el,a:+d.a,l:+d.l,d:+d.d,loc:d.loc||'',leg:+d.leg||0,mode:d.mode||'',title:d.title||'',
      det:$('details.evd',el),legEl:$('.leg',el),bn:$('.bd-now',el),bx:$('.bd-next',el),st:null};
  });
  evs.forEach(function(e){var D=days[e.d-1];if(e.a<D.first)D.first=e.a;if(e.l>D.last)D.last=e.l;});

  var cd=$('#countdown'),bar=$('#livebar'),lbA=$('#lb-a'),lbB=$('#lb-b'),lbR=$('#lb-r'),lastAct=-2,scrolled=false;
  var wasLive=false;

  function sunInfo(n){
    var idx=Math.floor(n/1440);if(idx<0||idx>4)return null;
    var s=days[idx].stats;if(!s)return null;
    return {idx:idx,rise:+s.dataset.rise,set:+s.dataset.set,dusk:+s.dataset.dusk};
  }
  function updateSun(n){
    days.forEach(function(D,i){
      var s=D.stats;if(!s)return;
      var tile=$('.st-sun',s),bar2=$('.dl-bar',s),fill=$('.dl-bar i',s),txt=$('.dl-t',s);
      var rise=+s.dataset.rise,set=+s.dataset.set,dusk=+s.dataset.dusk;
      var today=Math.floor(n/1440)===i;
      tile.classList.toggle('live',today);
      if(!today){
        if(!D.sunStatic)D.sunStatic=txt.textContent;
        bar2.hidden=true;txt.textContent=D.sunStatic;return;
      }
      bar2.hidden=false;
      if(n<rise){fill.style.width='0%';txt.textContent='Iki saulėtekio liko '+dur(rise-n);}
      else if(n<dusk){
        fill.style.width=Math.max(2,Math.min(100,(n-rise)/(dusk-rise)*100))+'%';
        txt.textContent='Iki sutemų liko '+dur(dusk-n)+(n<set?' (saulė leisis po '+dur(set-n)+')':' (saulė jau nusileido)');
      }else{fill.style.width='100%';txt.textContent='Jau sutemo. Saulė nusileido '+hhmm(set)+', sutemo '+hhmm(dusk)+'.';}
    });
  }

  function mark(loc,cls){if(!loc)return;$$('.lp[data-loc="'+loc+'"]').forEach(function(el){el.classList.add(cls);});}

  function nbJS(x){return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g,' ');}
  function updProgress(n){
    var P=$('#progress');if(!P)return;
    var carT=+P.dataset.carkm,wkT=+P.dataset.wk,stT=+P.dataset.steps,wkmT=+P.dataset.walkkm,st=+P.dataset.start,en=+P.dataset.end;
    var carD=0,wkD=0;
    $$('li.ev[data-a]').forEach(function(el){var d=el.dataset;if(+d.a<=n){carD+=+d.km||0;wkD+=+d.wk||0;}});
    var pct=carT?Math.min(1,carD/carT):0;
    $('#p-fill').style.width=(pct*100).toFixed(1)+'%';
    var stD=wkT?stT*wkD/wkT:0;
    $('#p-det').textContent='Automobiliu nuvažiuota '+Math.round(carD)+' iš '+Math.round(carT)+' km (liko '+Math.round(Math.max(0,carT-carD))+' km) · pėsčiomis ~'+nbJS(stD)+' iš ~'+nbJS(stT)+' žingsnių';
    var line=n<st?'Kelionė prasidės: liko '+dur(st-n)+'.':(n>=en?'Kelionė baigta.':'Kelionė vyksta: liko '+dur(en-n)+' iki pabaigos.');
    $('#p-line').textContent=line;
  }
  function update(){
    updProgress(nowAbs());
    var n=nowAbs();
    // countdown (Italy date)
    if(cd){
      if(n<0){var k=-Math.floor(n/1440);cd.textContent=k===1?'Išvykstate rytoj':'Iki išvykimo – '+dienos(k);}
      else if(n<days[4].last){cd.textContent='Kelionė vyksta, šiandien – '+(Math.floor(n/1440)+1)+' diena';}
      else cd.textContent='Kelionė baigėsi. Iki kitos!';
    }
    var live=n>=days[0].first-180&&n<days[4].last+120;
    var act=-1;
    if(live)days.forEach(function(D,i){if(n>=D.first-180)act=i;});
    var cur=-1,nxt=-1;
    evs.forEach(function(e,i){
      var st='';
      if(live)st=n>=e.l?'past':(n>=e.a?'cur':'fut');
      e.stNow=st;
      if(st==='cur')cur=i;
      if(st==='fut'&&nxt<0)nxt=i;
    });
    var trav=live&&cur<0&&nxt>0&&evs[nxt].leg>0&&evs[nxt-1].d===evs[nxt].d&&n>=evs[nxt-1].l;
    evs.forEach(function(e,i){
      var st=e.stNow;
      e.el.classList.toggle('is-past',st==='past');
      e.el.classList.toggle('is-cur',st==='cur');
      e.el.classList.toggle('is-next',live&&i===nxt);
      if(e.st!==st){e.st=st;if(e.det)e.det.open=(st!=='past');}
      if(e.bn)e.bn.hidden=(st!=='cur');
      if(e.bx){
        var show=live&&i===nxt&&!trav;
        e.bx.hidden=!show;
        if(show)e.bx.textContent=(e.a-n>=1)?'Toliau · po '+dur(e.a-n):'Toliau';
      }
      if(e.legEl){
        var tr=trav&&i===nxt;
        e.legEl.classList.toggle('on',tr);
        var lv=$('.lg-live',e.legEl);
        if(lv){lv.hidden=!tr;if(tr)lv.textContent='liko '+dur(e.a-n);}
      }
    });
    // days
    if(act!==lastAct){
      lastAct=act;
      days.forEach(function(D,i){D.el.open=(i===act);});
      syncAll();
    }
    days.forEach(function(D,i){
      var isT=i===act;
      D.el.classList.toggle('is-today',isT);
      D.el.classList.toggle('is-done',live&&i<act);
      if(D.badge){D.badge.hidden=!(live&&(isT||i<act));D.badge.textContent=isT?'Šiandien':'Praėjo';}
    });
    var nt=$('#nav-today');
    if(nt){nt.hidden=act<0;if(act>=0)nt.setAttribute('href','#d'+(act+1));}
    $$('.pin').forEach(function(p){p.classList.toggle('is-today',act>=0&&+da(p,'day')===act+1);});
    // maps
    $$('.lp.cur,.lp.nxt').forEach(function(el){el.classList.remove('cur','nxt');});
    if(live){
      if(cur>=0)mark(evs[cur].loc,'cur');
      else if(nxt>=0)mark(evs[nxt].loc,'nxt');
    }
    if(act>=0&&!userPicked&&selDay!==act+1)selectDay(act+1,true);
    if(!live&&!userPicked&&selDay!==0&&wasLive)selectDay(0,true);
    // sun
    updateSun(n);
    // live bar
    if(!live){bar.hidden=true;document.body.classList.remove('has-bar');}
    else{
      var a1='',b1='';
      var e=cur>=0?evs[cur]:null;
      if(e){
        a1='Dabar: '+e.title;
        var nx=evs[cur+1];
        if(nx&&nx.d===e.d){
          b1='Iki '+hhmm(e.l)+' · toliau: '+nx.title+' '+hhmm(nx.a)+(nx.leg?' (kelionė ~'+dur(nx.leg)+')':'');
        }else b1='Iki '+hhmm(e.l)+' · tai paskutinis šios dienos punktas';
      }else if(trav){
        var t2=evs[nxt];
        a1=(t2.mode==='walk'?'Einate: ':(t2.mode==='cable'?'Keltuvas ir ėjimas: ':'Važiuojate: '))+t2.title;
        b1='Atvykimas '+hhmm(t2.a)+' · liko '+dur(t2.a-n);
      }else if(nxt>=0){
        var t3=evs[nxt],rytoj=Math.floor(t3.a/1440)>Math.floor(n/1440);
        a1=nxt===0?'Kelionė prasideda netrukus':'Dienos planas baigtas';
        b1='Toliau: '+t3.title+' · '+(rytoj?'rytoj ':'')+hhmm(t3.a);
      }else{a1='Kelionė baigėsi';b1='Laimingo kelio namo!';}
      lbA.textContent='';
      var dot=document.createElement('span');dot.className='lb-dot';lbA.appendChild(dot);
      lbA.appendChild(document.createTextNode(a1));
      lbB.textContent=b1;
      var si=sunInfo(n),rt='';
      lbR.textContent='';
      var c1=document.createElement('b');c1.textContent='Italijoje '+hhmm(n);lbR.appendChild(c1);
      if(si){
        var c2=document.createElement('span');
        if(n<si.rise)c2.textContent='saulė teka po '+dur(si.rise-n);
        else if(n<si.dusk)c2.textContent='iki sutemų '+dur(si.dusk-n);
        else c2.textContent='jau sutemo';
        lbR.appendChild(c2);
      }
      if(preview!==null){var x=document.createElement('a');x.href=location.pathname;x.textContent='Išjungti peržiūrą';lbR.appendChild(x);}
      bar.hidden=false;document.body.classList.add('has-bar');
      bar._target=cur>=0?evs[cur]:(nxt>=0?evs[nxt]:null);
      if(!scrolled&&!location.hash&&bar._target){
        scrolled=true;
        var tg=bar._target;
        setTimeout(function(){tg.el.scrollIntoView({block:'center'});},400);
      }
    }
    wasLive=live;
  }

  // ---- day accordion
  var btn=$('#toggle-all');
  function syncAll(){
    var all=days.every(function(D){return D.el.open;});
    btn.textContent=all?'Suskleisti visas':'Išskleisti visas';
    btn.setAttribute('aria-expanded',all?'true':'false');
  }
  btn.addEventListener('click',function(){
    var all=days.every(function(D){return D.el.open;});
    days.forEach(function(D){D.el.open=!all;});
    syncAll();
  });
  days.forEach(function(D){D.el.addEventListener('toggle',syncAll);});

  function openDay(n,scroll){
    var el=document.getElementById('d'+n);if(!el)return;
    el.open=true;
    if(scroll)requestAnimationFrame(function(){el.scrollIntoView();});
  }
  function fromHash(){
    var id=location.hash.slice(1);if(!id)return;
    var el=document.getElementById(id);
    if(el&&el.matches('details.day')){el.open=true;requestAnimationFrame(function(){el.scrollIntoView();});}
  }
  window.addEventListener('hashchange',fromHash);

  // ---- sky: the sun's arc for today (or for the selected trip day)
  var sky=$('#sky'),skyKey='';
  var MON=['sausio','vasario','kovo','balandžio','gegužės','birželio','liepos','rugpjūčio','rugsėjo','spalio','lapkričio','gruodžio'];
  function lastSun(y,m){var d=new Date(Date.UTC(y,m+1,0));return d.getUTCDate()-d.getUTCDay();}
  function romeOff(y,m,d){if(m<2||m>9)return 1;if(m>2&&m<9)return 2;if(m===2)return d>=lastSun(y,2)?2:1;return d>=lastSun(y,9)?1:2;}
  function sunUT(doy,lat,lon,zen,rising){  // NOAA (tas pats algoritmas kaip generatoriuje)
    var r=Math.PI/180,lh=lon/15,t=doy+((rising?6:18)-lh)/24,M=0.9856*t-3.289;
    var L=((M+1.916*Math.sin(M*r)+0.020*Math.sin(2*M*r)+282.634)%360+360)%360;
    var RA=((Math.atan(0.91764*Math.tan(L*r))/r)%360+360)%360;
    RA=(RA+Math.floor(L/90)*90-Math.floor(RA/90)*90)/15;
    var sd=0.39782*Math.sin(L*r),cd=Math.cos(Math.asin(sd));
    var ch=(Math.cos(zen*r)-sd*Math.sin(lat*r))/(cd*Math.cos(lat*r));
    if(ch>1||ch<-1)return null;
    var H=Math.acos(ch)/r;H=(rising?360-H:H)/15;
    return ((H+RA-0.06571*t-6.622-lh)%24+24)%24;
  }
  function sunDay(i){  // i – dienos nuo 2026-10-29 (Italijos data); minutės nuo vietos vidurnakčio
    if(i>=0&&i<=4&&days[i]&&days[i].stats){var q=days[i].stats.dataset,o=i*1440;return {rise:+q.rise-o,set:+q.set-o,dusk:+q.dusk-o};}
    var dt=new Date(T0+i*864e5),y=dt.getUTCFullYear(),m=dt.getUTCMonth(),d=dt.getUTCDate();
    var doy=Math.round((Date.UTC(y,m,d)-Date.UTC(y,0,0))/864e5),tz=romeOff(y,m,d);
    function mm(h){return Math.round(((h+tz)%24)*60);}
    return {rise:mm(sunUT(doy,45.65,10.7,90.833,true)),set:mm(sunUT(doy,45.65,10.7,90.833,false)),dusk:mm(sunUT(doy,45.65,10.7,96,false))};
  }
  function dateLt(i){var dt=new Date(T0+i*864e5);return MON[dt.getUTCMonth()]+' '+dt.getUTCDate()+' d.';}
  function skyRender(){
    if(!sky)return;
    var n=nowAbs(),ti=Math.floor(n/1440),i=(selDay>0)?selDay-1:ti,live=i===ti,m=n-ti*1440;
    var S=sunDay(i),f=.5,ph='day',big,small;
    var title=(live?'Šiandien':(i+1)+' diena')+' · '+dateLt(i);
    if(live){
      if(m<S.rise){f=0;big=dur(S.rise-m);small='iki saulėtekio';ph=S.rise-m<45?'gold':'night';}
      else if(m<S.set){f=(m-S.rise)/(S.set-S.rise);big=dur(S.set-m);small='šviesos liko iki saulėlydžio';ph=(m-S.rise<50||S.set-m<50)?'gold':'day';}
      else if(m<S.dusk){f=1;big=dur(S.dusk-m);small='iki sutemų (saulė nusileido)';ph='gold';}
      else{f=1;big='Sutemo';small='saulėtekis rytoj '+hhmm(sunDay(i+1).rise);ph='night';}
    }else{big=dur(S.set-S.rise);small='šviesus paros metas';}
    var key=[title,big,small,ph,Math.round(f*500)].join('|');
    if(key===skyKey)return;
    skyKey=key;
    sky.className='sky ph-'+ph;
    $('#sky-t').textContent=title;
    $('#sky-big').textContent=big;
    $('#sky-small').textContent=small;
    $('#sky-rise').textContent=hhmm(S.rise);
    $('#sky-set').textContent=hhmm(S.set);
    $('#sky-dusk').textContent='Sutemos '+hhmm(S.dusk);
    var a=Math.PI*f;
    $('#sky-sun').setAttribute('transform','translate('+(170-124*Math.cos(a)).toFixed(1)+' '+(98-74*Math.sin(a)).toFixed(1)+')');
    $('#sky-done').setAttribute('stroke-dasharray',(live?f*100:0).toFixed(2)+' 200');
    $('#sky-sr').textContent=title+': saulėtekis '+hhmm(S.rise)+', saulėlydis '+hhmm(S.set)+', sutemos '+hhmm(S.dusk)+'. '+big+' '+small+'.';
  }
  // animations run only while the element is on screen
  if('IntersectionObserver' in window){
    var fxIO=new IntersectionObserver(function(es){es.forEach(function(e){e.target.classList.toggle('paused',!e.isIntersecting);});});
    $$('.lakemap,.sky').forEach(function(el){fxIO.observe(el);});
  }

  // ---- overview map: day selector
  var selDay=-1,userPicked=false;
  var ov=$('#ovmap'),dbtns=$$('.dbtn'),pinsEl=$$('.pin'),info=$('#dinfo');
  function selectDay(n,auto){
    selDay=n;
    if(!auto)userPicked=true;
    ov.setAttribute('data-sel',n);
    $$('.dl',ov).forEach(function(g){g.classList.toggle('on',n!==0&&+da(g,'day')===n);g.classList.toggle('all',n===0);});
    dbtns.forEach(function(b){b.setAttribute('aria-pressed',+b.dataset.day===n?'true':'false');});
    pinsEl.forEach(function(p){p.classList.toggle('sel',+da(p,'day')===n);});
    var b=n?$('.dbtn[data-day="'+n+'"]'):null;
    if(b){
      $('.di-t',info).textContent=b.dataset.title;
      $('.di-s',info).textContent=b.dataset.sum;
      var go=$('.go',info);go.hidden=false;go.setAttribute('href','#d'+n);go.dataset.day=n;
    }else{
      $('.di-t',info).textContent='Visos 5 dienos';
      $('.di-s',info).textContent='Pasirinkite dieną (skaičių) ir pamatysite maršrutą su atvykimo laikais.';
      $('.go',info).hidden=true;
    }
    skyRender();
  }
  dbtns.forEach(function(b){b.addEventListener('click',function(){selectDay(+b.dataset.day);});});
  pinsEl.forEach(function(p){
    p.addEventListener('click',function(ev){ev.preventDefault();selectDay(+da(p,'day'));});
  });
  $('.go',info).addEventListener('click',function(ev){ev.preventDefault();openDay(+this.dataset.day,true);});

  // ---- live bar click
  $('.lb-main').addEventListener('click',function(){
    var t=bar._target;if(!t)return;
    var D=days[t.d-1];D.el.open=true;
    t.el.scrollIntoView({block:'center'});
  });

  // ---- pins from print
  window.addEventListener('beforeprint',function(){
    days.forEach(function(D){D.el.open=true;});
    evs.forEach(function(e){if(e.det)e.det.open=true;});
  });

  // ---- photos (Wikipedia REST API, loaded in the browser only for opened days)
  var PKEY='garda-ph-2',pcache={},pjobs={},pdone={};
  try{pcache=JSON.parse(localStorage.getItem(PKEY)||'{}');}catch(e){pcache={};}
  function psave(){try{localStorage.setItem(PKEY,JSON.stringify(pcache));}catch(e){}}
  function pone(c){
    var i=c.indexOf(':'),lang=c.slice(0,i),title=c.slice(i+1);
    var url='https://'+lang+'.wikipedia.org/api/rest_v1/page/summary/'+encodeURIComponent(title.replace(/ /g,'_'));
    var opts={},t=null;
    if(window.AbortController){var ac=new AbortController();opts.signal=ac.signal;t=setTimeout(function(){ac.abort();},7000);}
    return fetch(url,opts).then(function(r){
      if(t)clearTimeout(t);
      if(r.status===404)return {none:true};
      if(!r.ok)return {err:true};
      return r.json().then(function(j){
        if(!j||j.type==='disambiguation'||!j.thumbnail||!/\.jpe?g(\?|$)/i.test(j.thumbnail.source))return {none:true};
        return {v:{src:j.thumbnail.source,page:(j.content_urls&&j.content_urls.desktop&&j.content_urls.desktop.page)||''}};
      });
    }).catch(function(){if(t)clearTimeout(t);return {err:true};});
  }
  function presolve(key){
    if(pjobs[key])return pjobs[key];
    var c=pcache[key];
    if(c&&Date.now()-c.t<(c.v?14:1)*864e5)return (pjobs[key]=Promise.resolve(c.v));
    var err=false;
    return (pjobs[key]=key.split('|').reduce(function(p,cd){
      return p.then(function(r){
        if(r)return r;
        return pone(cd).then(function(x){if(x.err)err=true;return x.v||null;});
      });
    },Promise.resolve(null)).then(function(v){
      if(v||!err){pcache[key]={t:Date.now(),v:v};psave();}else{delete pjobs[key];}
      return v;
    }));
  }
  function photosFor(D){
    if(pdone[D.i]||!window.fetch)return;
    pdone[D.i]=1;
    $$('.ph[data-wp]',D.el).forEach(function(slot){
      presolve(slot.getAttribute('data-wp')).then(function(v){
        if(!v){slot.classList.add('no');return;}
        var im=new Image();
        im.onload=function(){
          $('img',slot).src=v.src;slot.classList.add('ok');
          var li=slot.closest('li'),cred=li&&$('.cred',li);
          if(cred&&v.page){cred.href=v.page;cred.hidden=false;}
        };
        im.onerror=function(){slot.classList.add('no');};
        im.src=v.src;
      });
    });
  }
  days.forEach(function(D){D.el.addEventListener('toggle',function(){if(D.el.open)photosFor(D);});});

  // ---- orai (Open-Meteo, kraunama naršyklėje; kol nėra – momentinė kopija iš HTML)
  var WXKEY='garda-wx-1',WXAPI='https://api.open-meteo.com/v1/forecast';
  var WXLOC={
    sir:{n:'Sirmione apylinkės',la:45.4912,lo:10.6076},
    lim:{n:'Limone sul Garda',la:45.8138,lo:10.7922},
    mal:{n:'Malcesine',la:45.7647,lo:10.8085},
    bal:{n:'Monte Baldo viršuje (~1 750 m)',la:45.745,lo:10.84,el:1750},
    ten:{n:'Tenno (~570 m)',la:45.895,lo:10.762,el:570}
  };
  var WXTXT={0:['Giedra','sun'],1:['Daugiausia giedra','sun'],2:['Dalinai debesuota','part'],3:['Debesuota','cloud'],
    45:['Rūkas','fog'],48:['Šerkšnas ir rūkas','fog'],51:['Dulksna','rain'],53:['Dulksna','rain'],55:['Stipri dulksna','rain'],
    56:['Šalta dulksna','rain'],57:['Šalta dulksna','rain'],61:['Silpnas lietus','rain'],63:['Lietus','rain'],65:['Smarkus lietus','rain'],
    66:['Šaltas lietus','rain'],67:['Šaltas lietus','rain'],71:['Silpnas sniegas','snow'],73:['Sniegas','snow'],75:['Smarkus sniegas','snow'],
    77:['Sniego kruopos','snow'],80:['Trumpi lietūs','rain'],81:['Liūtys','rain'],82:['Smarkios liūtys','rain'],85:['Sniego pūgos','snow'],
    86:['Smarkios sniego pūgos','snow'],95:['Perkūnija','storm'],96:['Perkūnija su kruša','storm'],99:['Perkūnija su kruša','storm']};
  function wxIco(code,cls,sz){
    var t=WXTXT[code];if(!t)return '';
    return '<svg class="'+cls+'" width="'+sz+'" height="'+sz+'" aria-hidden="true" focusable="false"><use href="#i-wx-'+t[1]+'"/></svg>';
  }
  function wxNum(x){return String(x).replace('.',',');}
  function wxN(x){x=Math.round(x);return (x<0?'\u2212':'')+Math.abs(x);}
  function wxT(a,b){var x=Math.round(a),y=Math.round(b);return (x===y?wxN(x):wxN(x)+(x<0||y<0?'…':'–')+wxN(y))+'\u00a0°C';}
  function wxAdvice(o,altMax,altGust,cable){
    var a=[];
    if(o.pp!=null){
      if(o.pp>=60||(o.mm!=null&&o.mm>=5))a.push('Tikėtinas lietus: pasiimkite lietpaltį ar skėtį.');
      else if(o.pp>=30)a.push('Galimas lietus: lietpaltis ar skėtis neprošal.');
      else a.push('Daugiausia sausa.');
    }
    if(altMax!=null&&altMax<=8)a.push('Aukštai kalnuose šalta: striukė, kepurė, pirštinės.');
    else if(o.max<=8)a.push('Šalta: šilti drabužiai, kepurė ir pirštinės.');
    else if(o.max<15)a.push('Vėsu: sluoksniuoti drabužiai ir striukė.');
    else a.push('Švelnu: lengva striukė vakarui.');
    var g=o.gust;
    if(cable&&altGust!=null&&(g==null||altGust>g))g=altGust;
    if(g!=null){
      if(g>=50)a.push('Stiprūs vėjo gūsiai (iki '+Math.round(g)+' km/h): '+(cable?'Monte Baldo keltuvas gali nevažiuoti, patikrinkite prieš vykdami.':'atsargiai kalnų keliuose ir prie vandens.'));
      else if(g>=35)a.push('Gūsingas vėjas (iki '+Math.round(g)+' km/h).');
    }
    return a.join(' ');
  }
  function wxPick(src,date){
    // src: Open-Meteo atsakymas vienai vietai -> dienos objektas
    if(!src||!src.daily||!src.daily.time)return null;
    var i=src.daily.time.indexOf(date);if(i<0)return null;
    var d=src.daily;function g(k){return d[k]?d[k][i]:null;}
    var o={min:g('temperature_2m_min'),max:g('temperature_2m_max'),pp:g('precipitation_probability_max'),mm:g('precipitation_sum'),
      code:g('weather_code'),wind:g('wind_speed_10m_max'),gust:g('wind_gusts_10m_max'),hrs:{}};
    if(o.code==null)o.code=g('weathercode');
    if(o.min==null||o.max==null)return null;
    var h=src.hourly;
    if(h&&h.time){
      for(var hh=6;hh<=23;hh++){
        var k=h.time.indexOf(date+'T'+(hh<10?'0':'')+hh+':00');
        if(k>=0)o.hrs[hh]={t:h.temperature_2m?h.temperature_2m[k]:null,pp:h.precipitation_probability?h.precipitation_probability[k]:null,
          code:h.weather_code?h.weather_code[k]:(h.weathercode?h.weathercode[k]:null)};
      }
      var dc=wxDayCode(o);if(dc!=null)o.code=dc;
    }
    return o;
  }
  function wxDayCode(o){
    // dienos būklė pagal šviesias valandas (8–20 val.), o ne pagal blogiausią parą (pvz. ryto rūkas)
    var cnt={},n=0,wet={},nw=0,th=0,c,h,k,q;
    for(h=8;h<=20;h++){
      q=o.hrs[h];if(!q||q.code==null)continue;
      c=q.code;n++;
      if(c>=95)th=Math.max(th,c);
      else if(c>=51){nw++;wet[c]=(wet[c]||0)+1;}
      else cnt[c]=(cnt[c]||0)+1;
    }
    if(!n)return null;
    if(th)return th;
    function top(m){var b=null,bn=0;Object.keys(m).map(Number).sort(function(x,y){return x-y;}).forEach(function(k2){if(m[k2]>bn){b=k2;bn=m[k2];}});return b;}
    if(nw>=3)return top(wet);
    var dry=top(cnt);
    return dry!=null?dry:top(wet);
  }
  function wxAge(t){
    var m=Math.round((Date.now()-t)/6e4);
    if(m<2)return 'ką tik';
    if(m<60)return 'prieš '+m+' min.';
    if(m<48*60)return 'prieš '+Math.round(m/60)+' val.';
    return 'prieš '+Math.round(m/1440)+' d.';
  }
  function wxRender(tile,data,t,failed){
    var key=tile.getAttribute('data-wx'),date=tile.getAttribute('data-date');
    var live=data?wxPick(data[key],date):null;
    var o,loc,altTxt='',altMax=null,altGust=null,cable=!!tile.getAttribute('data-alt');
    if(live){
      o=live;loc=WXLOC[key].n;
      var ak=tile.getAttribute('data-alt'),ao=ak&&data?wxPick(data[ak],date):null;
      if(ao){altMax=ao.max;altGust=ao.gust;altTxt='<span class="sr">Aukštai: </span>'+tile.getAttribute('data-alt-n')+': '+wxT(ao.min,ao.max)+(ao.gust!=null?', vėjo gūsiai iki '+Math.round(ao.gust)+' km/h':'');}
    }else{
      o={min:+tile.getAttribute('data-min'),max:+tile.getAttribute('data-max'),pp:+tile.getAttribute('data-pp'),mm:null,code:null,wind:null,gust:null,hrs:{}};
      loc=tile.getAttribute('data-snaploc');
      var dh=+tile.getAttribute('data-alt-dh');
      if(dh){altMax=o.max-dh*0.0065;altTxt=tile.getAttribute('data-alt-n')+': apie '+wxN(altMax)+'\u00a0°C dieną (įvertis pagal aukštį)';}
    }
    $('.wx-loc',tile).textContent=loc;
    var cond=live&&WXTXT[o.code]?WXTXT[o.code][0]:'';
    $('.wx-main',tile).innerHTML=(live?wxIco(o.code,'wico',34):'')+'<b class="wx-temp">'+wxT(o.min,o.max)+'</b><span class="wx-cond">'+cond+'</span>';
    var m='';
    if(o.pp!=null&&!isNaN(o.pp))m+='<span>'+'<svg class="ico" width="16" height="16" aria-hidden="true" focusable="false"><use href="#i-wx-drop"/></svg>Lietaus tikimybė: '+Math.round(o.pp)+' %'+(live&&o.mm!=null&&o.mm>=0.1?' · '+wxNum(Math.round(o.mm*10)/10)+' mm':'')+'</span>';
    if(live&&o.wind!=null)m+='<span><svg class="ico" width="16" height="16" aria-hidden="true" focusable="false"><use href="#i-wx-wind"/></svg>Vėjas iki '+Math.round(o.wind)+' km/h'+(o.gust!=null?', gūsiai iki '+Math.round(o.gust):'')+'</span>';
    $('.wx-meta',tile).innerHTML=m;
    // valandų juosta
    var hr=$('.wx-hrs',tile),hs=(tile.getAttribute('data-hours')||'').split(','),cells='',n=0;
    if(live)hs.forEach(function(x){
      var q=o.hrs[+x];if(!q||q.t==null)return;n++;
      cells+='<span class="wx-h"><i>'+(x<10?'0':'')+x+':00</i>'+wxIco(q.code,'ico',24)+'<b>'+Math.round(q.t)+'°</b><small>'+(q.pp!=null?Math.round(q.pp)+' %':'')+'</small></span>';
    });
    hr.innerHTML=cells;hr.hidden=!n;hr.style.setProperty('--n',n||4);
    var alt=$('.wx-alt',tile);
    if(altTxt){
      if(!alt){alt=document.createElement('p');alt.className='wx-alt';tile.insertBefore(alt,$('.wx-adv',tile));}
      alt.innerHTML=altTxt;
    }else if(alt)alt.parentNode.removeChild(alt);
    $('.wx-adv',tile).textContent=wxAdvice(o,altMax,altGust,cable);
    var ag=live?wxAge(t):'';
    $('.wx-src',tile).textContent=live?'Prognozė: Open-Meteo, atnaujinta '+ag+(/\.$/.test(ag)?'':'.')
      :(failed?'Prognozė, 2026 m. spalio 26 d. (šviežios gauti nepavyko).':'Prognozė, 2026 m. spalio 26 d.');
  }
  var lastSc=0;
  window.addEventListener('scroll',function(){lastSc=Date.now();},{passive:true});
  function wxApply(data,t,failed){
    // išlaikome tą vietą, į kurią žiūri lankytojas, nors plytelės pakeičia aukštį
    var a=document.elementFromPoint(window.innerWidth/2,window.innerHeight*0.4),t0=a?a.getBoundingClientRect().top:0;
    $$('.st-wx').forEach(function(tile){wxRender(tile,data,t,failed);});
    if(a){
      var dy=a.getBoundingClientRect().top-t0;
      if(Math.abs(dy)>1&&Date.now()-lastSc>250){try{window.scrollBy({top:dy,left:0,behavior:'instant'});}catch(e){window.scrollBy(0,dy);}}
    }
  }
  function wxOne(key,mode){
    var L=WXLOC[key],u=WXAPI+'?latitude='+L.la+'&longitude='+L.lo+(L.el?'&elevation='+L.el:'')+
      '&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max&timezone=Europe%2FRome'+
      (mode===1?'&forecast_days=16&past_days=7':'&start_date=2026-10-29&end_date=2026-11-02');
    var opts={},tm=null;
    if(window.AbortController){var ac=new AbortController();opts.signal=ac.signal;tm=setTimeout(function(){ac.abort();},9000);}
    return fetch(u,opts).then(function(r){
      if(tm)clearTimeout(tm);
      if(r.ok)return r.json();
      if(mode!==1)return wxOne(key,1);
      return null;
    }).catch(function(){if(tm)clearTimeout(tm);return null;});
  }
  var wxBusy=false;
  function wxLoad(){
    if(wxBusy||!window.fetch||!window.Promise)return;
    var c=null;try{c=JSON.parse(localStorage.getItem(WXKEY)||'null');}catch(e){c=null;}
    if(c&&c.d&&c.t)wxApply(c.d,c.t);
    if(c&&c.d&&Date.now()-c.t<3*36e5)return;
    wxBusy=true;
    var keys=Object.keys(WXLOC),got={},ok=0;
    Promise.all(keys.map(function(k){return wxOne(k,0).then(function(j){if(j&&j.daily){got[k]=j;ok++;}});})).then(function(){
      wxBusy=false;
      if(!ok){if(!(c&&c.d))wxApply(null,0,true);return;}
      var d=(c&&c.d)||{};keys.forEach(function(k){if(got[k])d[k]=got[k];});
      var t=Date.now();
      try{localStorage.setItem(WXKEY,JSON.stringify({t:t,d:d}));}catch(e){}
      wxApply(d,t);
    });
  }
  wxApply(null,0);
  wxLoad();
  document.addEventListener('visibilitychange',function(){if(!document.hidden)wxLoad();});

  selectDay(0,true);
  update();skyRender();
  fromHash();
  days.forEach(function(D){if(D.el.open)photosFor(D);});
  setInterval(function(){if(!document.hidden){update();skyRender();}},15000);
  document.addEventListener('visibilitychange',function(){if(!document.hidden){update();skyRender();}});

  // ---- offline support
  if('serviceWorker' in navigator&&/^https?:$/.test(location.protocol)){
    window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});
  }
})();
'''

def summary_html():
    car = sum(e['km_e'] for d in DAYS for e in d['evs'])
    carmin = sum(d['drive_min'] for d in DAYS)
    wk_total = sum(e['wk_e'] for d in DAYS for e in d['evs'])
    steps = sum(d['steps'] for d in DAYS)
    walkkm = sum(d['walk_km'] for d in DAYS)
    starts = [e['a'] for d in DAYS for e in d['evs']]
    ends = [e['l'] for d in DAYS for e in d['evs']]
    rows = ''.join(
        f'<tr><th scope="row">{d["n"]} d.</th><td>{d["drive_km"]:.0f} km</td>'
        f'<td>{d["walk_km"]:.1f} km</td><td>~{nb(d["steps"])}</td></tr>' for d in DAYS)
    return (f'<section class="sec" id="suvestine"><div class="wrap">'
            f'<h2>Kelionės suvestinė</h2>'
            f'<div class="sum-grid">'
            f'<div class="sum-card"><span class="sk">Automobiliu</span><b>{car:.0f} km</b>'
            f'<small>~{dur_txt(carmin)} be sustojimų</small></div>'
            f'<div class="sum-card"><span class="sk">Pėsčiomis</span><b>{walkkm:.1f} km</b>'
            f'<small>~{nb(steps)} žingsnių</small></div></div>'
            f'<table class="sum-t"><thead><tr><th>Diena</th><th>Automobiliu</th><th>Pėsčiomis</th><th>Žingsniai</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
            f'<div class="prog" id="progress" data-carkm="{car:.3f}" data-wk="{wk_total}" data-steps="{steps}" '
            f'data-walkkm="{walkkm:.3f}" data-start="{min(starts)}" data-end="{max(ends)}">'
            f'<h3>Progresas</h3><div class="pbar"><div class="pfill" id="p-fill"></div></div>'
            f'<p class="pline" id="p-line">Kelionė dar neprasidėjo.</p><p class="pdet" id="p-det"></p></div>'
            f'</div></section>')


PAGE = r'''<!doctype html>
<html lang="lt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#34401F">
<title>Gardos Ežeras 2026 | Kelionės Vadovas</title>
<meta name="description" content="Gardos ežero kelionės vadovas: 2026 m. spalio 29 d. – lapkričio 2 d., skrydžiai, nakvynė, 5 dienų maršrutas su laikais, žemėlapiais ir gyvu režimu.">
<meta property="og:type" content="website">
<meta property="og:locale" content="lt_LT">
<meta property="og:site_name" content="Garda 2026">
<meta property="og:url" content="https://italija.tingek.lt/">
<meta property="og:title" content="Gardos Ežeras 2026 | Kelionės Vadovas">
<meta property="og:description" content="Skrydžiai, nakvynė ir 5 dienų maršrutas aplink Gardos ežerą su laikais, žemėlapiais ir gyvu režimu.">
<meta property="og:image" content="https://italija.tingek.lt/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Gardos ežero schema su penkių dienų maršrutais">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://italija.tingek.lt/">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%2334401F'/%3E%3Cpath d='M17 5c4 6 7 9 7 13a7 7 0 0 1-14 0c0-4 3-7 7-13z' fill='%2380BCDA'/%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="preconnect" href="https://api.open-meteo.com" crossorigin>
<link rel="preload" href="fonts/inter.woff" as="font" type="font/woff" crossorigin>
<link rel="preload" href="fonts/literata.woff" as="font" type="font/woff" crossorigin>
<script>document.documentElement.className+=' js'</script>
<style>%%CSS%%</style>
</head>
<body>
%%SPRITE%%
<a class="skip" href="#marsrutas">Pereiti prie maršruto</a>
<header class="nav"><div class="nav-in">
  <a class="nav-brand" href="#top">Garda 2026</a>
  <a id="nav-today" href="#marsrutas" hidden>Šiandien</a>
  <a href="#logistika">Logistika</a>
  <a href="#marsrutas">Maršrutas</a>
  <a href="#patarimai">Patarimai</a>
</div></header>
<main id="top">
<section class="hero"><div class="hero-in">
  <div class="hero-head">
    <p class="countdown" id="countdown">Iki išvykimo – spalio 29 d.</p>
    <h1><span class="h1-main">Gardos Ežeras 2026</span><span class="h1-sub">Kelionės Vadovas</span></h1>
  </div>
  <div class="mapbox">
    %%SKY%%
    %%MAP%%
    <div class="dsel" role="group" aria-label="Pasirinkite dieną">%%BTNS%%</div>
    <div class="dinfo" id="dinfo" aria-live="polite"><p class="di-t">Visos 5 dienos</p><p class="di-s">Pasirinkite dieną (skaičių) ir pamatysite maršrutą su atvykimo laikais.</p><a class="go" href="#d1" hidden>Atidaryti dieną ↓</a></div>
    <ul class="legend">
      <li class="l1"><i></i>Pietų bazė (Moniga)</li>
      <li class="l2"><i></i>Persikėlimo diena</li>
      <li class="l3"><i></i>Šiaurės bazė (Riva)</li>
    </ul>
    <p class="mapnote">Schema, ne mastelio. Laikai – Italijos.</p>
  </div>
  <div class="hero-facts">
    <ul class="facts">
      <li>2026 m. spalio 29 d. – lapkričio 2 d.</li>
      <li>8 keliautojai (5 suaugę, 3 vaikai)</li>
      <li>2 automobiliai</li>
    </ul>
    <p class="stats"><span><b>5</b>dienos</span><span><b>2</b>nakvynės bazės</span></p>
    <p class="tagline">Kalnai, tarpekliai ir senamiesčiai.</p>
  </div>
</div></section>

<section class="sec" id="logistika"><div class="wrap">
  <h2>Logistika ir skrydžiai</h2>
  <div class="logi">
    <div class="card flights"><h3>Skrydžiai (Wizz Air)</h3>%%FLIGHTS%%</div>
    <div class="card car"><h3>Automobilių nuoma</h3>
      <p class="big">„Centauro“, MXP oro uostas</p>
      <p>2 automobiliai</p>
      <dl><dt>Atsiėmimas</dt><dd>spalio 29 d., apie 20:30</dd><dt>Grąžinimas</dt><dd>iki lapkričio 2 d. 20:00</dd></dl>
      <p style="margin-top:14px">%%CARLINK%%</p>
    </div>
    <div class="card stays"><h3>Nakvynės vietos</h3><div class="stays-in">%%STAYS%%</div></div>
  </div>
</div></section>

<section class="sec sec-days" id="marsrutas"><div class="wrap">
  <div class="head-row"><h2>Maršrutas diena po dienos</h2><button class="btn" id="toggle-all" type="button" aria-expanded="false">Išskleisti visas</button></div>
  <p class="daynote">Laikai – siūlomas orientacinis grafikas (Italijos laiku). Kelionės trukmė ir atstumai – automobiliu be spūsčių, suapvalinta aukštyn; kalnų keliams pridėta atsarga. Kelionės metu puslapis pats paryškina tai, kas vyksta dabar, o praėjusius punktus suskleidžia.</p>
  <div class="days">%%DAYS%%</div>
</div></section>

<section class="sec" id="patarimai"><div class="wrap">
  <h2>Svarbūs patarimai</h2>
  <div class="tips">
    <article class="tip">
      <h3><span aria-hidden="true">⚠️</span>Monte Baldo keltuvas</h3>
      <p>Lapkričio 1 d. yra paskutinė šio sezono darbo diena. Nuo lapkričio 2 d. prasideda techninė profilaktika (oficialiai iki gruodžio 25 d.), todėl bilietus būtina turėti iš anksto.</p>
      <p>Rudens grafikas pagal oficialią svetainę: kilimas nuo 9:00, paskutinis kilimas 15:45, paskutinis nusileidimas 17:00. Lapkričio 1 d. Italijoje yra Visų šventųjų diena (valstybinė šventė), tad tikėkitės eilių.</p>
      <p><a href="https://funiviedelbaldo.it/en/" target="_blank" rel="noopener">funiviedelbaldo.it: bilietai ir grafikas</a></p>
    </article>
    <article class="tip">
      <h3><span aria-hidden="true">🚗</span>Strada della Forra</h3>
      <p>Siauras kelias uolose: kai kuriuose ruožuose eismas vienpusis pakaitomis, reguliuojamas šviesoforu. Vasaros sezono metu (10:00–19:00) dalyje kelio leidžiama važiuoti tik aukštyn, nuo ežero link Tremosine; ne sezono metu taisyklės gali skirtis, todėl sekite kelio ženklus.</p>
      <p>Kelias kartais uždaromas dėl uolų nuošliaužų, todėl prieš išvykdami patikrinkite, ar jis atviras.</p>
      <p><a href="https://www.gardavisit.it/strada-della-forra/" target="_blank" rel="noopener">gardavisit.it: apie Strada della Forra</a></p>
    </article>
    <article class="tip wide">
      <h3><span aria-hidden="true">🌅</span>Šviesa ir sutemos</h3>
      <p>Saulė leidžiasi apie %%SUNRNG%%, sutemos baigiasi apie %%DUSKRNG%%. Skaičiuota atviram horizontui prie ežero; tarp kalnų (Riva, Limone, Malcesine, Tenno) saulė už viršukalnių pasislepia gerokai anksčiau, o kalnų keliai sutemus būna tamsūs. Lauko vietas planuokite iki ~16:00.</p>
      <p>Spalio 25 d. pereita prie žiemos laiko: Italija atsilieka nuo Lietuvos 1 val. Visi laikai puslapyje – Italijos, išskyrus skrydžius (jie nurodyti vietiniu laiku).</p>
    </article>
  </div>
</div></section>
%%SUMMARY%%
</main>
<div class="livebar" id="livebar" hidden><div class="lb-in">
  <button class="lb-main" type="button" aria-label="Rodyti dabartinį punktą"><span class="lb-a" id="lb-a"></span><span class="lb-b" id="lb-b"></span></button>
  <div class="lb-r" id="lb-r"></div>
</div></div>
<footer>
  <p>Informacija patikrinta 2026 m. spalio 23 d. Darbo laikus ir kelių būklę dar kartą patikrinkite prieš išvykdami. Cascata Varone lapkritį dirba 10:00–17:00.</p>
  <p>Trukmės: OSRM maršrutų skaičiavimas (be spūsčių), suapvalinta aukštyn. Ėjimas ir žingsniai – apytikslis įvertis (~100 žingsnių per minutę). Saulės laikai – astronominis skaičiavimas. Orų prognozė – Open-Meteo (atnaujinama atidarius puslapį; aukštai kalnuose temperatūra gali skirtis). Nuotraukos įkeliamos iš Wikipedia / Wikimedia Commons (laisvos licencijos, autoriai nurodyti šaltinio puslapyje).</p>
  <p>Gyvo režimo peržiūra: <a href="?t=2026-10-30T11:20">2 d. 11:20</a> · <a href="?t=2026-10-31T12:10">3 d. 12:10</a> · <a href="?t=2026-11-01T09:50">4 d. 09:50</a> · <a href="?t=2026-11-02T16:30">5 d. 16:30</a></p>
</footer>
<script>%%JS%%</script>
</body>
</html>
'''

html_out = (PAGE
            .replace('%%SPRITE%%', SPRITE_SVG)
            .replace('%%CSS%%', CSS)
            .replace('%%JS%%', JS)
            .replace('%%SKY%%', sky_html())
            .replace('%%MAP%%', overview_svg())
            .replace('%%BTNS%%', day_buttons())
            .replace('%%FLIGHTS%%', FLIGHTS)
            .replace('%%STAYS%%', STAYS)
            .replace('%%CARLINK%%', mlink('Centauro Rent a Car Malpensa Airport', 'Centauro MXP'))
            .replace('%%SUNRNG%%', sun_rng)
            .replace('%%DUSKRNG%%', dusk_rng)
            .replace('%%SUMMARY%%', summary_html())
            .replace('%%DAYS%%', ''.join(day_html(d) for d in DAYS))
            .replace('/*%%FXCSS%%*/', boats_css() + flow_css()))

(OUT / 'index.html').write_text(html_out, encoding='utf-8')
(OUT / 'CNAME').write_text('italija.tingek.lt\n', encoding='utf-8')
(OUT / '.nojekyll').write_text('', encoding='utf-8')

# ---- web manifest + service worker (offline support)
import hashlib, json as _json
manifest = {
    "name": "Gardos ežeras 2026 | Kelionės vadovas",
    "short_name": "Garda 2026",
    "description": "Skrydžiai, nakvynė ir 5 dienų maršrutas aplink Gardos ežerą.",
    "lang": "lt", "dir": "ltr",
    "start_url": "./", "scope": "./", "id": "./",
    "display": "standalone",
    "background_color": "#EFE4CC", "theme_color": "#34401F",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(OUT / 'manifest.webmanifest').write_text(_json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

_assets = ['./', 'index.html', 'manifest.webmanifest',
           'fonts/inter.woff', 'fonts/literata.woff', 'fonts/literata-italic.woff',
           'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png']
for _a in _assets:
    if _a != './':
        assert (OUT / _a).exists(), 'missing precache asset ' + _a
_ver = hashlib.sha1(html_out.encode('utf-8')).hexdigest()[:10]
SW = """/* Garda 2026: service worker (generuojamas build.py). Versija: %%VER%% */
'use strict';
var CACHE = 'garda-%%VER%%';
var PRECACHE = %%LIST%%;

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return Promise.all(PRECACHE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k.indexOf('garda-') === 0 && k !== CACHE; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

function timeout(ms) {
  return new Promise(function (_, rej) { setTimeout(function () { rej(new Error('timeout')); }, ms); });
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;           // Wikipedia ir kt.: tiesiai į tinklą

  if (req.mode === 'navigate') {                              // puslapis: pirma tinklas, jei lėtas ar nėra ryšio: talpykla
    e.respondWith(
      Promise.race([fetch(req), timeout(5000)]).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put('index.html', copy); });
        }
        return res;
      }).catch(function () {
        return caches.match('index.html').then(function (r) { return r || fetch(req); });
      })
    );
    return;
  }

  e.respondWith(                                              // šriftai, ikonos: pirma talpykla
    caches.match(req).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
""".replace('%%VER%%', _ver).replace('%%LIST%%', _json.dumps(_assets))
(OUT / 'sw.js').write_text(SW, encoding='utf-8')

# summary printout
for d in DAYS:
    print(d['n'], 'drive', dur_txt(d['drive_min']), km_txt(d['drive_km']), '| walk', dur_txt(d['walk_min']), d['steps'],
          f"{d['walk_km']:.1f}km | sun {fm(d['rise'])} {fm(d['set'])} dusk {fm(d['dusk'])}")
    for e in d['evs']:
        print('   ', fm(e['a']), fm(e['l']), e['title'][:48])
print('ok', len(html_out), 'bytes')
