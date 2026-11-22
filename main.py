#!/usr/bin/env python3
"""Steaming bowl of ramen — one ingredient, drawn in pure stdlib Python.

Writes /output/entry.png (override with ENTRY_PNG env var for local tests).
Deterministic: fixed seed, no randomness at runtime, no network.
"""
import os
import struct
import zlib

W, H = 900, 900
OUT = os.environ.get("ENTRY_PNG", "/output/entry.png")

# --- pixel buffer -----------------------------------------------------------
buf = bytearray(W * H * 3)


def px(x, y):
    return (y * W + x) * 3


def set_px(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = px(x, y)
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend(x, y, r, g, b, a):
    """Alpha-blend a colour over the pixel (a in 0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = px(x, y)
        buf[i] = int(buf[i] * (1 - a) + r * a)
        buf[i + 1] = int(buf[i + 1] * (1 - a) + g * a)
        buf[i + 2] = int(buf[i + 2] * (1 - a) + b * a)


def fill_rect(x0, y0, x1, y1, col):
    r, g, b = col
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            set_px(x, y, r, g, b)


def fill_ellipse(cx, cy, rx, ry, col, a=1.0):
    r, g, b = col
    for y in range(max(0, int(cy - ry)), min(H, int(cy + ry) + 1)):
        dy = (y - cy) / ry
        dx = rx * (1 - dy * dy) ** 0.5
        for x in range(max(0, int(cx - dx)), min(W, int(cx + dx) + 1)):
            if a >= 1.0:
                set_px(x, y, r, g, b)
            else:
                blend(x, y, r, g, b, a)


def ring(cx, cy, rx, ry, thick, col):
    """Ellipse outline."""
    for t in range(thick):
        fill_ellipse(cx, cy, rx - t, ry - t, col)


def disc(cx, cy, rad, col, a=1.0):
    fill_ellipse(cx, cy, rad, rad, col, a)


def line(x0, y0, x1, y1, col, thick=1):
    r, g, b = col
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    rad = thick // 2
    for i in range(steps + 1):
        t = i / max(steps, 1)
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t)
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if dx * dx + dy * dy <= rad * rad + rad:
                    set_px(x + dx, y + dy, r, g, b)


def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# --- background: warm cream gradient + soft vignette ------------------------
top = (253, 238, 214)
mid = (247, 214, 178)
bot = (232, 184, 138)
for y in range(H):
    t = y / H
    c = lerp(top, mid, t) if t < 0.55 else lerp(mid, bot, (t - 0.55) / 0.45)
    for x in range(W):
        set_px(x, y, *c)
# vignette: darken corners gently
for y in range(H):
    for x in range(W):
        d = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
        if d > 0.9:
            a = min(0.22, (d - 0.9) * 0.35)
            blend(x, y, 120, 70, 30, a)

# --- wooden table -----------------------------------------------------------
for y in range(640, H):
    t = (y - 640) / (H - 640)
    c = lerp((176, 124, 74), (150, 100, 55), t)
    for x in range(W):
        set_px(x, y, *c)
# plank seams + grain
for gx in (150, 430, 720):
    line(gx, 640, gx + 18, H, (120, 78, 40), 3)
for gy in (700, 780, 850):
    for x in range(0, W, 7):
        blend(x, gy + ((x * 7) % 3) - 1, 140, 92, 48, 0.35)

# soft shadow under bowl
fill_ellipse(450, 700, 300, 42, (90, 55, 25), 0.28)

# --- chopsticks (resting across the bowl rim) --------------------------------
line(500, 448, 820, 350, (122, 72, 32), 13)
line(515, 478, 835, 382, (122, 72, 32), 13)
line(782, 362, 820, 350, (196, 130, 70), 13)
line(797, 394, 835, 382, (196, 130, 70), 13)

# --- bowl body --------------------------------------------------------------
# dark indigo ceramic bowl, rounded profile (ellipse below the rim line)
for y in range(500, 760):
    t = (y - 500) / 260
    c = lerp((52, 66, 110), (28, 34, 66), t)
    frac = 1 - ((y - 500) / 258.0) ** 2
    half = 305 * (frac ** 0.5) if frac > 0 else 0
    half = max(half, 0)
    for x in range(max(0, int(450 - half)), min(W, int(450 + half) + 1)):
        set_px(x, y, *c)
# bowl foot
fill_ellipse(450, 745, 120, 26, (24, 28, 56))
fill_ellipse(450, 740, 120, 24, (40, 48, 88))
# rim highlight on bowl body
for y in range(520, 700):
    t = (y - 520) / 180
    x = int(450 - 285 * (1 - 0.3 * t))
    blend(x, y, 150, 165, 220, 0.25)

# --- rim --------------------------------------------------------------------
fill_ellipse(450, 500, 305, 92, (38, 46, 84))
fill_ellipse(450, 498, 292, 84, (238, 226, 205))
fill_ellipse(450, 498, 278, 76, (196, 118, 52))  # broth edge
# broth surface
fill_ellipse(450, 500, 268, 70, (214, 138, 58))
# broth sheen: lighter swirl top-left
fill_ellipse(380, 478, 120, 30, (240, 178, 92), 0.7)
fill_ellipse(520, 520, 90, 22, (190, 110, 40), 0.6)

# --- noodles: wavy strands across the broth ----------------------------------
import math

NOODLE = [(244, 214, 130), (238, 200, 110), (250, 226, 150)]
for s in range(26):
    y0 = 452 + (s * 37) % 92
    amp = 6 + (s % 5) * 2
    ph = s * 1.7
    col = NOODLE[s % 3]
    for x in range(200, 700):
        y = y0 + int(amp * math.sin(x * 0.045 + ph))
        # clip strictly inside the broth ellipse
        if ((x - 450) / 262) ** 2 + ((y - 500) / 66) ** 2 > 0.98:
            continue
        for dy in range(-2, 3):
            shade = 0.85 if dy > 0 else 1.0
            set_px(x, y + dy, int(col[0] * shade), int(col[1] * shade), int(col[2] * shade))
# noodle lift: a small mound of noodles piled centre-left
for s in range(8):
    y0 = 470 + s * 4
    for x in range(300, 430):
        y = y0 + int(5 * math.sin(x * 0.08 + s))
        set_px(x, y, 250, 226, 150)
        set_px(x, y + 1, 230, 196, 105)

# --- chashu pork slices ------------------------------------------------------
for (cx, cy) in [(560, 480), (610, 505)]:
    fill_ellipse(cx, cy, 62, 46, (196, 122, 104))
    fill_ellipse(cx, cy, 48, 34, (226, 168, 146))
    fill_ellipse(cx, cy, 30, 20, (240, 196, 172))
    fill_ellipse(cx - 12, cy - 10, 12, 7, (255, 220, 200), 0.8)

# --- halved ajitama egg ------------------------------------------------------
for (cx, cy) in [(330, 490), (400, 530)]:
    fill_ellipse(cx, cy, 52, 40, (252, 244, 226))          # white
    fill_ellipse(cx, cy, 52, 40, (0, 0, 0), 0)             # no-op keep
    disc(cx, cy, 24, (232, 146, 42))                       # yolk
    disc(cx - 6, cy - 7, 9, (255, 196, 90))                # yolk highlight
    # browned edge ring on white
    for ang in range(0, 360, 4):
        a = math.radians(ang)
        blend(int(cx + 46 * math.cos(a)), int(cy + 34 * math.sin(a)), 190, 150, 110, 0.5)

# --- nori sheet -------------------------------------------------------------
fill_rect(480, 440, 540, 500, (28, 46, 30))
for x in range(484, 540, 6):
    blend(x, 470, 60, 90, 55, 0.5)

# --- green onion rings -------------------------------------------------------
for (cx, cy) in [(300, 460), (350, 455), (480, 540), (540, 545), (430, 555), (620, 460)]:
    disc(cx, cy, 10, (46, 128, 60))
    disc(cx, cy, 5, (150, 210, 110))

# --- sesame seeds ------------------------------------------------------------
for (sx, sy) in [(280, 500), (520, 470), (380, 560), (590, 530), (250, 470)]:
    disc(sx, sy, 3, (250, 240, 210))

# --- chilli oil droplets ------------------------------------------------------
for (cx, cy) in [(470, 470), (350, 510), (560, 520)]:
    disc(cx, cy, 7, (178, 44, 20), 0.85)

# --- steam: soft rising wisps ------------------------------------------------
for w in range(3):
    cx0 = 360 + w * 90
    for y in range(180, 460):
        t = (460 - y) / 280
        sway = int(26 * math.sin(y * 0.03 + w * 2.1) * t)
        width = int(20 + 34 * t)
        a = 0.30 * (1 - t * 0.45)
        for dx in range(-width, width + 1):
            fall = 1 - abs(dx) / width
            blend(cx0 + sway + dx, y, 255, 250, 240, a * fall * fall)

# --- rim gloss ----------------------------------------------------------------
fill_ellipse(330, 470, 90, 14, (255, 255, 255), 0.35)

# --- PNG encode (zlib + struct, stdlib only) ---------------------------------
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


raw = bytearray()
for y in range(H):
    raw.append(0)  # filter: none
    raw += buf[y * W * 3:(y + 1) * W * 3]

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
png += chunk(b"IEND", b"")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(png)
print(f"wrote {OUT}: {W}x{H}, {len(png)} bytes")
