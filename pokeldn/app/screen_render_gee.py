"""The GEE board's screen drawn in Python: a frame-for-frame mirror of the 320x240 pages in
firmware GEE's scene_gee.c/screen_gee.c (status, exchange and opening), with the 128x64 scene.c
pages scaled into the same canvas the way display_gee.c's blit_small does. The Session panel
shows this instead of the original 128x64 mirror. docs/hardware_esp32.md, The screen.
"""
import math

from pokeldn.app import screen_render as base

W, H = 320, 240
STRIDE = W // 8
BYTES = STRIDE * H
FONT = base.FONT


def clear(fb: bytearray) -> None:
    fb[:] = b"\0" * BYTES


def pixel(fb: bytearray, x: int, y: int, on: bool = True) -> None:
    if 0 <= x < W and 0 <= y < H:
        i = y * STRIDE + (x >> 3)
        bit = 1 << (7 - (x & 7))
        if on:
            fb[i] |= bit
        else:
            fb[i] &= ~bit & 0xFF


def fill(fb, x, y, w, h, on=True):
    for j in range(y, y + h):
        for i in range(x, x + w):
            pixel(fb, i, j, on)


def rect(fb, x, y, w, h):
    fill(fb, x, y, w, 1)
    fill(fb, x, y + h - 1, w, 1)
    fill(fb, x, y, 1, h)
    fill(fb, x + w - 1, y, 1, h)


def line(fb, x0, y0, x1, y1):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pixel(fb, x0, y0)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(fb, cx, cy, r, filled, on):
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            d = x * x + y * y
            if d <= r * r + r and (filled or d >= r * r - r):
                pixel(fb, cx + x, cy + y, on)


def text(fb, x, y, s: bytes, scale=1):
    for c in s:
        g = (c - 0x20 if 0x20 <= c <= 0x7E else ord("?") - 0x20) * 5
        for col in range(5):
            bits = FONT[g + col]
            for row in range(7):
                if bits >> row & 1:
                    fill(fb, x + col * scale, y + row * scale, scale, scale, True)
        x += 6 * scale
    return x


def text_width(s: bytes, scale=1):
    return (6 * len(s) - 1) * scale if s else 0


def text_centered(fb, y, s, scale=1):
    text(fb, (W - text_width(s, scale)) // 2, y, s, scale)


def poke_ball(fb, cx, cy, r):
    rim = r // 9 if r // 9 > 0 else 1
    band = 2 * rim
    inner = r - rim
    button = r // 3 + 1 if r > 5 else 1
    circle(fb, cx, cy, r + rim, True, False)
    circle(fb, cx, cy, r, True, True)
    circle(fb, cx, cy, inner, True, False)
    for y in range(cy - inner, cy):
        for x in range(cx - inner, cx + inner + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= inner * inner + inner:
                pixel(fb, x, y, True)
    for y in range(cy - band // 2 + 1, cy - band // 2 + 1 + band):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                pixel(fb, x, y, True)
    circle(fb, cx, cy, button, True, True)
    circle(fb, cx, cy, button - rim, True, False)


def poke_ball_tilted(fb, cx, cy, r, tilt):
    rim = r // 9 if r // 9 > 0 else 1
    band = 2 * rim
    inner = r - rim
    button = r // 3 + 1 if r > 5 else 1
    s, c = math.sin(tilt), math.cos(tilt)
    fcx, fcy = cx + r * s, cy + r * (1 - c)
    for y in range(int(math.floor(fcy)) - r - 1, int(math.ceil(fcy)) + r + 2):
        for x in range(int(math.floor(fcx)) - r - 1, int(math.ceil(fcx)) + r + 2):
            dx, dy = x - fcx, y - fcy
            d = dx * dx + dy * dy
            if d > r * r + r:
                continue
            if d > inner * inner + inner:
                on = True
            else:
                on = (-dx * s + dy * c) <= band * 0.5
            if d <= button * button + button:
                on = d > (button - rim) * (button - rim) + (button - rim)
            pixel(fb, x, y, on)


def wobble_ball(fb, now):
    """The roly-poly wobble shared by the idle and joining pages: three +/-8 degree tilts,
    then upright."""
    t = now % 3000
    k = 0.0
    if t < 1800:
        osc = t % 600
        if osc < 150:
            k = osc / 150.0
        elif osc < 300:
            k = 1.0 - (osc - 150) / 150.0
        elif osc < 450:
            k = -(osc - 300) / 150.0
        else:
            k = -1.0 + (osc - 450) / 150.0
    poke_ball_tilted(fb, 160, 120, 34, (8.0 * math.pi / 180.0) * k)


def console_icon(fb, x, y, s):
    fill(fb, x, y + s, 4 * s, 10 * s, True)
    fill(fb, x + 18 * s, y + s, 4 * s, 10 * s, True)
    fill(fb, x, y + s, s, s, False)
    fill(fb, x + 21 * s, y + s, s, s, False)
    fill(fb, x, y + 10 * s, s, s, False)
    fill(fb, x + 21 * s, y + 10 * s, s, s, False)
    fill(fb, x + s, y + 4 * s, s, s, False)
    fill(fb, x + 20 * s, y + 7 * s, s, s, False)
    fill(fb, x + 4 * s, y, 14 * s, 12 * s, True)
    fill(fb, x + 5 * s, y + s, 12 * s, 10 * s, False)
    fill(fb, x + 6 * s, y + 2 * s, 10 * s, 8 * s, True)


def bit_glyph(fb, x, y, one, s):
    rows = (7, 5, 5, 5, 7) if one else (2, 6, 2, 2, 7)
    for r in range(5):
        for c in range(3):
            if rows[r] >> (2 - c) & 1:
                fill(fb, x + c * s, y + r * s, s, s, True)


def cable(fb, x0, x1, y, rx, tx, now):
    for x in range(x0, x1 + 1, 12):
        fill(fb, x, y, 5, 3, True)
    for i in range(3):
        p = (now // 6 + i * 37) % 100
        bit_glyph(fb, x0 + (x1 - x0) * p // 100, y - 20, (rx >> i) & 1, 2)
        bit_glyph(fb, x0 + (x1 - x0) * (100 - p) // 100, y + 10, (tx >> i) & 1, 2)


def header(fb, left: bytes, right: bytes | None):
    text(fb, 16, 12, left, 3)
    if right:
        text(fb, W - 16 - text_width(right, 2), 16, right, 2)
    fill(fb, 16, 46, W - 32, 2, True)


def status(fb, mode, stations, rx, tx, now, version: bytes):
    linked = mode == base.JOINED or (mode == base.HOSTING and stations)
    if linked:
        header(fb, b"joined" if mode == base.JOINED else b"hosting", b"linked")
        console_icon(fb, 26, 102, 3)
        poke_ball(fb, 268, 120, 24)
        cable(fb, 113, 222, 120, rx, tx, now)
        text_centered(fb, 190, b"trade or gift", 2)
        return
    if mode in (base.JOINING, base.HOSTING):
        header(fb, b"pokeldn", b"joining" if mode == base.JOINING else b"hosting")
        wobble_ball(fb, now)
        text_centered(fb, 190, b"looking for a console" if mode == base.JOINING
                      else b"waiting for a console", 2)
        return
    header(fb, b"pokeldn", b"sniffing" if mode == base.SNIFFING else b"idle")
    wobble_ball(fb, now)
    if mode == base.SNIFFING:
        text_centered(fb, 170, b"sniffing", 3)
        text_centered(fb, 205, b"%d frames" % rx, 2)
    else:
        text_centered(fb, 163, b"radio ready", 3)
        text_centered(fb, 195, b"start a trade or gift", 2)
        v = b"v" + version
        text(fb, W - 16 - text_width(v, 1), 228, v, 1)


def trading(fb, mode, rx, tx, now):
    header(fb, b"joined" if mode == base.JOINED else b"hosting", b"linked")
    console_icon(fb, 26, 102, 3)
    poke_ball(fb, 268, 120, 24)
    cable(fb, 113, 222, 120, rx, tx, now)
    text_centered(fb, 190, b"trading...", 2)


def opening(fb, progress):
    r = 10 + progress * 210 // 1000
    circle(fb, 160, 120, r, True, True)
    if r > 14:
        circle(fb, 160, 120, r - 14, True, False)


def blit_small(fb, frame: bytes):
    rows = base.pixels(frame)
    for y in range(157):
        sy = y * 64 // 157
        for x in range(304):
            if rows[sy][x * 128 // 304]:
                pixel(fb, 8 + x, 41 + y, True)


def pixels(frame: bytes):
    """The 320x240 frame as rows of pixels; the GEE canvas is MSB-first, row-major."""
    return [[bool(frame[y * STRIDE + (x >> 3)] >> (7 - (x & 7)) & 1) for x in range(W)]
            for y in range(H)]


class Scene:
    """scene_gee.c's pages over screen_render.Scene's scene.c state; one per board."""

    def __init__(self):
        self.base = base.Scene()
        self.fb = bytearray(BYTES)

    def command(self, p: bytes, now_ms: int) -> bool:
        return self.base.command(p, now_ms)

    def reset(self) -> None:
        self.base.reset()

    def draw(self, mode: int, stations: int, rx: int, tx: int, presses: int, now_ms: int):
        frame, power = self.base.draw(mode, stations, rx, tx, presses, now_ms)
        clear(self.fb)
        show = self.base.now.show
        t = self.base.elapsed(now_ms)
        reveal = self.base.reveal
        if show == base.AUTO:
            status(self.fb, mode, stations, rx, tx, now_ms, self.base.version)
        elif show == base.TRADED and base.LEAVE_MS <= t < reveal:
            trading(self.fb, mode, rx, tx, now_ms)
        elif (show == base.TRADED
              and reveal + 1000 <= t < reveal + base.REVEAL_MS):
            opening(self.fb, (t - reveal - 1000) * 1000 // (base.REVEAL_MS - 1000))
        else:
            blit_small(self.fb, frame)
        return bytes(self.fb), power
