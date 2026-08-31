"""Force equal green half-overlap stripes on TOP/BOTTOM/LEFT/RIGHT arms."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "logo"
OUT.mkdir(exist_ok=True)

Y = (255, 212, 50, 160)
B = (70, 165, 255, 160)
G = (30, 195, 75, 190)
TEXT = (17, 17, 17, 255)


def colorize(mask: Image.Image, rgba) -> Image.Image:
    r, g, b, a = rgba
    lay = Image.new("RGBA", mask.size, (r, g, b, 0))
    lay.putalpha(mask.point(lambda p: int(p * a / 255)))
    return lay


def render_symbol(size: int = 1000) -> Image.Image:
    cx = cy = size // 2
    tip = int(size * 0.42)
    th = int(size * 0.15)
    # Mid green band thickness; each color bar is sized to half-overlap by this band
    band = max(th // 2, 18)
    bar_w = (th + band) // 2  # each half-bar
    r = bar_w // 2
    bend = int(th * 1.45)

    def blank():
        return Image.new("L", (size, size), 0)

    def vbar(m, x, y0, y1):
        d = ImageDraw.Draw(m)
        d.rounded_rectangle((x - r, y0, x + r, y1), radius=r, fill=255)

    def hbar(m, y, x0, x1):
        d = ImageDraw.Draw(m)
        d.rounded_rectangle((x0, y - r, x1, y + r), radius=r, fill=255)

    def bend_arc(m, hx, vy):
        d = ImageDraw.Draw(m)
        acx = cx + hx * (th * 0.32)
        acy = cy + vy * (th * 0.32)
        if hx < 0 and vy < 0:
            angs = [270 - i * (90 / 72) for i in range(73)]
        elif hx > 0 and vy < 0:
            angs = [270 + i * (90 / 72) for i in range(73)]
        elif hx < 0 and vy > 0:
            angs = [90 + i * (90 / 72) for i in range(73)]
        else:
            angs = [90 - i * (90 / 72) for i in range(73)]
        rr = r
        for deg in angs:
            a = math.radians(deg)
            x = acx + bend * math.cos(a)
            y = acy + bend * math.sin(a)
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)

    # Offset of each half-bar from centerline so mid-overlap width ≈ band
    off = (bar_w - band) // 2  # = (th-band)/4 roughly
    # Simpler: place centers at ± band/2 so overlap = bar_w - band
    # Want overlap == band → bar_w - separation = band → separation = bar_w - band
    # centers at ± separation/2 from cx
    sep = bar_w - band
    off = max(sep // 2, 1)

    # TL yellow: top-left + left-top
    tl = blank()
    vbar(tl, cx - off, cy - tip, cy + th // 3)  # TOP left strip FULL tip→past hub
    hbar(tl, cy - off, cx - tip, cx + th // 3)
    bend_arc(tl, -1, -1)

    # TR blue: top-right + right-top  — SAME vertical span as TL for equal top green
    tr = blank()
    vbar(tr, cx + off, cy - tip, cy + th // 3)  # TOP right strip SAME length
    hbar(tr, cy - off, cx - th // 3, cx + tip)
    bend_arc(tr, +1, -1)

    # BL blue
    bl = blank()
    vbar(bl, cx - off, cy - th // 3, cy + tip)
    hbar(bl, cy + off, cx - tip, cx + th // 3)
    bend_arc(bl, -1, +1)

    # BR yellow
    br = blank()
    vbar(br, cx + off, cy - th // 3, cy + tip)
    hbar(br, cy + off, cx - th // 3, cx + tip)
    bend_arc(br, +1, +1)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img = Image.alpha_composite(img, colorize(tl, Y))
    img = Image.alpha_composite(img, colorize(tr, B))
    img = Image.alpha_composite(img, colorize(bl, B))
    img = Image.alpha_composite(img, colorize(br, Y))

    green = Image.new("L", (size, size), 0)
    for a, b in ((tl, tr), (bl, br), (tl, bl), (tr, br)):
        green = ImageChops.lighter(green, ImageChops.multiply(a, b))
    img = Image.alpha_composite(img, colorize(green, G))
    return img


def main():
    sym = render_symbol(1000)
    sb = sym.getbbox()
    pad = 48
    sym = sym.crop((sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad))
    sym.save(OUT / "mc-tech-symbol.png")

    w, h = 1700, 720
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    fk = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 156)
    fe = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 54)
    kr, en = "엠씨테크", "MC TECH"
    kr_w = draw.textbbox((0, 0), kr, font=fk)[2]
    en_w = draw.textbbox((0, 0), en, font=fe)[2]
    left, kry = 60, 200
    draw.text((left, kry), kr, font=fk, fill=TEXT)
    draw.text((left + (kr_w - en_w) // 2, kry + 172), en, font=fe, fill=TEXT)
    th = 430
    sym2 = sym.resize((int(sym.width * th / sym.height), th), Image.Resampling.LANCZOS)
    canvas.alpha_composite(sym2, (left + kr_w + 40, (h - sym2.height) // 2))
    bb = canvas.getbbox()
    pad = 36
    canvas = canvas.crop(
        (max(0, bb[0] - pad), max(0, bb[1] - pad), min(w, bb[2] + pad), min(h, bb[3] + pad))
    )
    canvas.save(OUT / "mc-tech-logo.png")
    print("saved", OUT / "mc-tech-logo.png", canvas.size)
    print("saved", OUT / "mc-tech-symbol.png", sym.size)


if __name__ == "__main__":
    main()
