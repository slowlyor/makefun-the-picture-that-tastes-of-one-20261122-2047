#!/usr/bin/env python3
"""Draw a steaming bowl of ramen and write it to /output/entry.png.

Pure Python 3.13, standard library only, fully deterministic, no network.
Run:  python3 main.py
"""
import math
import os
import struct
import zlib

W, H = 900, 900
OUT = os.environ.get("OUT_PATH", "/output/entry.png")

# ---------------------------------------------------------------- canvas --
img = [bytearray(W * 3) for _ in range(H)]


def hspan(y, x0, x1, rgb):
    """Fill a horizontal span of pixels (clipped) with an RGB tuple."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x1 < x0:
        return
    row = img[y]
    r, g, b = rgb
    for x in range(x0, x1 + 1):
        i = x * 3
        row[i] = r
        row[i + 1] = g
        row[i + 2] = b


def hspan_blend(y, x0, x1, rgb, alpha):
    """Fill a horizontal span, blending over what is already there."""
    if y < 0 or y >= H or alpha <= 0:
        return
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x1 < x0:
        return
    row = img[y]
    r, g, b = rgb
    a = alpha
    ia = 1.0 - a
    for x in range(x0, x1 + 1):
        i = x * 3
        row[i] = int(r * a + row[i] * ia)
        row[i + 1] = int(g * a + row[i + 1] * ia)
        row[i + 2] = int(b * a + row[i + 2] * ia)


def fill_ellipse(cx, cy, rx, ry, rgb, alpha=1.0):
    for dy in range(-int(ry), int(ry) + 1):
        t = dy / ry
        if abs(t) > 1.0:
            continue
        dx = rx * math.sqrt(1.0 - t * t)
        if alpha >= 1.0:
            hspan(cy + dy, cx - dx, cx + dx, rgb)
        else:
            hspan_blend(cy + dy, cx - dx, cx + dx, rgb, alpha)


def fill_circle(cx, cy, r, rgb, alpha=1.0):
    fill_ellipse(cx, cy, r, r, rgb, alpha)


def disc(x, y, r, rgb, alpha=1.0):
    fill_circle(int(x), int(y), int(r), rgb, alpha)


def poly(points, rgb, alpha=1.0):
    """Scanline-fill a polygon given as [(x, y), ...]."""
    ys = [p[1] for p in points]
    y0, y1 = int(min(ys)), int(max(ys))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = points[i]
            x1, yy1 = points[(i + 1) % n]
            if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                t = (y - yy0) / (yy1 - yy0)
                xs.append(x0 + t * (x1 - x0))
        if len(xs) >= 2:
            xs.sort()
            if alpha >= 1.0:
                hspan(y, xs[0], xs[-1], rgb)
            else:
                hspan_blend(y, xs[0], xs[-1], rgb, alpha)


def thick_line(x0, y0, x1, y1, w, rgb):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L == 0:
        disc(x0, y0, w / 2, rgb)
        return
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
          (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], rgb)
    disc(x0, y0, w / 2, rgb)
    disc(x1, y1, w / 2, rgb)


def inside_ellipse(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


# ------------------------------------------------------------------ palette --
CREAM = (250, 238, 211)
CREAM2 = (244, 226, 190)
TABLE = (178, 126, 74)
TABLE_DARK = (150, 102, 58)
TABLE_LINE = (132, 88, 50)
INDIGO = (30, 38, 92)
INDIGO_DARK = (20, 26, 66)
INDIGO_LIGHT = (56, 68, 146)
INDIGO_HI = (96, 110, 190)
BROTH = (216, 160, 64)
BROTH_LIGHT = (238, 190, 96)
BROTH_DARK = (188, 128, 44)
NOODLE = (246, 216, 132)
NOODLE_DARK = (204, 152, 62)
EGG_WHITE = (252, 248, 238)
YOLK = (234, 142, 38)
YOLK_DARK = (206, 110, 22)
YOLK_HI = (255, 196, 110)
CHASHU = (198, 122, 92)
CHASHU_DARK = (152, 80, 58)
CHASHU_LIGHT = (222, 158, 128)
NORI = (26, 50, 32)
NORI_HI = (52, 92, 58)
ONION = (96, 176, 84)
ONION_DARK = (58, 128, 52)
CHILLI = (204, 62, 22)
CHOP = (122, 74, 34)
CHOP_DARK = (96, 56, 24)
STEAM = (255, 255, 255)

# ------------------------------------------------------------- background --
for y in range(H):
    # warm cream wall, gently darkening toward the table
    t = y / H
    r = int(250 - 6 * t)
    g = int(238 - 10 * t)
    b = int(211 - 12 * t)
    hspan(y, 0, W - 1, (r, g, b))

# wooden table surface
for y in range(600, H):
    t = (y - 600) / (H - 600)
    r = int(178 - 22 * t)
    g = int(126 - 18 * t)
    b = int(74 - 12 * t)
    hspan(y, 0, W - 1, (r, g, b))
for px in (150, 300, 450, 600, 750):
    for y in range(600, H):
        hspan(y, px, px + 2, TABLE_LINE)
for y in (660, 740, 830):
    hspan(y, 0, W - 1, TABLE_DARK)

# soft shadow under the bowl
fill_ellipse(450, 800, 330, 42, (90, 58, 28), alpha=0.35)

# ------------------------------------------------------------------- bowl --
# bowl body (indigo), slightly squat
fill_ellipse(450, 560, 330, 235, INDIGO)
# darker lower shading
fill_ellipse(450, 640, 300, 150, INDIGO_DARK, alpha=0.55)
# foot ring
fill_ellipse(450, 782, 120, 26, INDIGO_DARK)
fill_ellipse(450, 776, 104, 20, INDIGO_LIGHT)
# rim highlight on the left edge
fill_ellipse(180, 560, 26, 190, INDIGO_HI, alpha=0.35)
# rim ring
fill_ellipse(450, 520, 322, 108, INDIGO_LIGHT)
# golden broth
fill_ellipse(450, 520, 296, 92, BROTH)
fill_ellipse(450, 512, 260, 70, BROTH_LIGHT, alpha=0.65)
# broth sheen
fill_ellipse(340, 492, 130, 26, (250, 214, 130), alpha=0.55)

# ----------------------------------------------------------------- noodles --
# wavy noodle strands, clipped to the broth ellipse
for strand in range(9):
    yb = 462 + strand * 9
    amp = 7 + (strand % 3) * 3
    ph = strand * 1.3
    for x in range(170, 731, 3):
        y = yb + amp * math.sin((x - 170) / 46.0 + ph)
        if inside_ellipse(x, y, 450, 520, 292, 90):
            disc(x, y, 5, NOODLE)
            disc(x, y + 3, 2, NOODLE_DARK)
# a few noodle curls poking up
for cx, cy, r in ((300, 470, 26), (600, 478, 24), (470, 452, 20)):
    for k in range(28):
        a = k / 28 * 2 * math.pi
        x = cx + r * math.cos(a)
        y = cy + r * 0.45 * math.sin(a)
        if inside_ellipse(x, y, 450, 520, 292, 90):
            disc(x, y, 5, NOODLE)

# ------------------------------------------------------------------ chashu --
for cx, cy, s in ((452, 566, 1.0), (540, 540, 0.82)):
    fill_ellipse(cx, cy, int(58 * s), int(48 * s), CHASHU)
    fill_ellipse(cx, cy, int(40 * s), int(32 * s), CHASHU_LIGHT, alpha=0.8)
    for k in range(20):
        a = k / 20 * 2 * math.pi
        x = cx + 24 * s * math.cos(a)
        y = cy + 18 * s * math.sin(a)
        disc(x, y, 4, CHASHU_DARK)
    disc(cx - 14 * s, cy - 12 * s, 8, (240, 190, 160), alpha=0.8)

# -------------------------------------------------------------------- eggs --
for cx, cy in ((318, 498), (586, 496)):
    fill_ellipse(cx, cy, 58, 44, EGG_WHITE)
    fill_ellipse(cx, cy, 30, 26, YOLK)
    fill_ellipse(cx - 4, cy - 3, 22, 18, YOLK_DARK, alpha=0.45)
    disc(cx - 10, cy - 10, 7, YOLK_HI, alpha=0.9)   # glossy yolk highlight
    disc(cx + 16, cy + 12, 4, YOLK_HI, alpha=0.6)

# -------------------------------------------------------------------- nori --
# dark green sheet standing at the back-right edge of the bowl
poly([(618, 396), (668, 402), (660, 500), (612, 494)], NORI)
for k in range(6):
    y = 410 + k * 14
    thick_line(620, y, 664, y + 5, 2, NORI_HI)

# ------------------------------------------------------- green onion + oil --
import random
rng = random.Random(7)
for _ in range(26):
    x = rng.randint(200, 700)
    y = rng.randint(448, 590)
    if not inside_ellipse(x, y, 450, 520, 288, 88):
        continue
    disc(x, y, 7, ONION_DARK)
    disc(x, y, 4, ONION)
for _ in range(14):
    x = rng.randint(210, 690)
    y = rng.randint(452, 585)
    if not inside_ellipse(x, y, 450, 520, 288, 88):
        continue
    disc(x, y, 5, CHILLI, alpha=0.9)
    disc(x - 1, y - 1, 2, (255, 120, 60), alpha=0.9)

# -------------------------------------------------------------- chopsticks --
# resting diagonally across the rim, tips over the broth
thick_line(150, 396, 700, 470, 13, CHOP)
thick_line(158, 424, 706, 496, 13, CHOP_DARK)
disc(158, 424, 7, (150, 98, 48))
disc(150, 396, 7, (150, 98, 48))

# -------------------------------------------------------------------- steam --
# two layered wisp columns so the steam reads clearly above the bowl
for sx, ph, amp in ((330, 0.0, 16), (450, 1.4, 20), (570, 2.6, 15)):
    for y in range(110, 440, 4):
        t = (440 - y) / 330.0
        x = sx + amp * math.sin(y / 55.0 + ph) * t
        r = 8 + 10 * t
        disc(x, y, r, STEAM, alpha=0.24)
    for y in range(180, 440, 4):
        t = (440 - y) / 260.0
        x = sx + 10 + amp * 0.7 * math.sin(y / 47.0 + ph + 0.9) * t
        r = 5 + 7 * t
        disc(x, y, r, STEAM, alpha=0.20)

# ------------------------------------------------------- final highlights --
# glossy rim highlight
fill_ellipse(300, 448, 120, 14, (255, 255, 255), alpha=0.28)
# broth sparkle
disc(400, 500, 5, (255, 236, 170), alpha=0.8)
disc(520, 552, 4, (255, 236, 170), alpha=0.7)

# -------------------------------------------------------------------- PNG --
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


raw = bytearray()
for row in img:
    raw.append(0)  # filter: none
    raw.extend(row)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
png += chunk(b"IEND", b"")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(png)
print(f"wrote {OUT}: {W}x{H}, {len(png)} bytes")
