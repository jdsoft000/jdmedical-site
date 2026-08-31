"""
MC TECH symbol: upright axis-aligned plus (+) from 4 overlapping soft L/boomerangs.
  TL yellow · TR blue · BL blue · BR yellow
  Overlaps = green. Soft bends. No white gaps. NO diagonal/tilt look.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent / "logo"
OUT_DIR.mkdir(exist_ok=True)

YELLOW = (255, 215, 55, 155)
BLUE = (80, 160, 255, 155)
GREEN = (40, 195, 80, 180)
TEXT = (17, 17, 17, 255)


def find_font(size: int):
    for path in (
        r"C:\Windows\Fonts\malgunbd.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def colorize(mask: Image.Image, rgba) -> Image.Image:
    r, g, b, a = rgba
    layer = Image.new("RGBA", mask.size, (r, g, b, 0))
    layer.putalpha(mask.point(lambda p: int(p * a / 255)))
    return layer


def capsule_v(d, cx, y0, y1, thick):
    r = thick // 2
    if y1 < y0:
        y0, y1 = y1, y0
    d.rounded_rectangle((cx - r, y0, cx + r, y1), radius=r, fill=255)


def capsule_h(d, cy, x0, x1, thick):
    r = thick // 2
    if x1 < x0:
        x0, x1 = x1, x0
    d.rounded_rectangle((x0, cy - r, x1, cy + r), radius=r, fill=255)


def soft_bend(d, cx, cy, hx, vy, thick, bend):
    """Soft quarter-circle at the plus crook (quadrant)."""
    r = thick / 2
    acx = cx + hx * (thick * 0.38)
    acy = cy + vy * (thick * 0.38)
    if hx < 0 and vy < 0:
        angs = [270 - i * (90 / 60) for i in range(61)]
    elif hx > 0 and vy < 0:
        angs = [270 + i * (90 / 60) for i in range(61)]
    elif hx < 0 and vy > 0:
        angs = [90 + i * (90 / 60) for i in range(61)]
    else:
        angs = [90 - i * (90 / 60) for i in range(61)]
    for deg in angs:
        a = math.radians(deg)
        x = acx + bend * math.cos(a)
        y = acy + bend * math.sin(a)
        d.ellipse((x - r, y - r, x + r, y + r), fill=255)


def piece_mask(size, which, tip, thick):
    """
    Axis-aligned L: bars ON the plus midlines with tiny offset,
    extending deep past center so they half-overlap neighbors with zero gap.
    """
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    cx = cy = size // 2
    # Tiny shift = bars almost co-axial → heavy overlap, no white seam
    shift = max(thick // 8, 2)
    past = int(tip * 0.55)  # deep past mid
    bend = int(thick * 1.25)

    if which == "tl":
        capsule_v(d, cx - shift, cy - tip, cy + past, thick)
        capsule_h(d, cy - shift, cx - tip, cx + past, thick)
        soft_bend(d, cx, cy, -1, -1, thick, bend)
    elif which == "tr":
        capsule_v(d, cx + shift, cy - tip, cy + past, thick)
        capsule_h(d, cy - shift, cx - past, cx + tip, thick)
        soft_bend(d, cx, cy, +1, -1, thick, bend)
    elif which == "bl":
        capsule_v(d, cx - shift, cy - past, cy + tip, thick)
        capsule_h(d, cy + shift, cx - tip, cx + past, thick)
        soft_bend(d, cx, cy, -1, +1, thick, bend)
    else:  # br
        capsule_v(d, cx + shift, cy - past, cy + tip, thick)
        capsule_h(d, cy + shift, cx - past, cx + tip, thick)
        soft_bend(d, cx, cy, +1, +1, thick, bend)
    return m


def render_symbol(size: int = 900) -> Image.Image:
    tip = int(size * 0.40)
    thick = int(size * 0.16)

    pieces = [
        ("tl", YELLOW),
        ("tr", BLUE),
        ("bl", BLUE),
        ("br", YELLOW),
    ]
    masks = {}
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for which, color in pieces:
        masks[which] = piece_mask(size, which, tip, thick)
        img = Image.alpha_composite(img, colorize(masks[which], color))

    # Green only yellow∩blue neighbor pairs (axis-aligned overlaps)
    green_m = Image.new("L", (size, size), 0)
    for a, b in (("tl", "tr"), ("bl", "br"), ("tl", "bl"), ("tr", "br")):
        green_m = ImageChops.lighter(
            green_m, ImageChops.multiply(masks[a], masks[b])
        )
    img = Image.alpha_composite(img, colorize(green_m, GREEN))
    return img


def render_logo() -> None:
    w, h = 1800, 720
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font_kr = find_font(168)
    font_en = find_font(58)
    kr, en = "엠씨테크", "MC TECH"
    kr_w = draw.textbbox((0, 0), kr, font=font_kr)[2]
    en_w = draw.textbbox((0, 0), en, font=font_en)[2]
    left, kr_y = 70, 210
    draw.text((left, kr_y), kr, font=font_kr, fill=TEXT)
    draw.text((left + (kr_w - en_w) // 2, kr_y + 180), en, font=font_en, fill=TEXT)

    symbol = render_symbol(620)
    canvas.alpha_composite(symbol, (left + kr_w + 45, (h - symbol.height) // 2))
    bbox = canvas.getbbox()
    if bbox:
        pad = 40
        canvas = canvas.crop(
            (
                max(0, bbox[0] - pad),
                max(0, bbox[1] - pad),
                min(w, bbox[2] + pad),
                min(h, bbox[3] + pad),
            )
        )
    canvas.save(OUT_DIR / "mc-tech-logo.png", "PNG")
    print("saved", OUT_DIR / "mc-tech-logo.png", canvas.size)

    sym = render_symbol(900)
    sb = sym.getbbox()
    if sb:
        pad = 48
        sym = sym.crop((sb[0] - pad, sb[1] - pad, sb[2] + pad, sb[3] + pad))
    sym.save(OUT_DIR / "mc-tech-symbol.png", "PNG")
    print("saved", OUT_DIR / "mc-tech-symbol.png", sym.size)


def write_svgs() -> None:
    tip, thick, past, shift, op = 100, 40, 55, 5, 0.55
    bend = 50
    r = thick / 2

    def piece(which, color):
        if which == "tl":
            return "\n".join(
                [
                    f'<rect x="{-shift - r}" y="{-tip}" width="{thick}" height="{tip + past}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                    f'<rect x="{-tip}" y="{-shift - r}" width="{tip + past}" height="{thick}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                    f'<path d="M {-shift},{-thick * 0.35} A {bend} {bend} 0 0 0 {-thick * 0.35},{-shift}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="{thick}" stroke-linecap="round"/>',
                ]
            )
        if which == "tr":
            return "\n".join(
                [
                    f'<rect x="{shift - r}" y="{-tip}" width="{thick}" height="{tip + past}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                    f'<rect x="{-past}" y="{-shift - r}" width="{tip + past}" height="{thick}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                    f'<path d="M {shift},{-thick * 0.35} A {bend} {bend} 0 0 1 {thick * 0.35},{-shift}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="{thick}" stroke-linecap="round"/>',
                ]
            )
        if which == "bl":
            return "\n".join(
                [
                    f'<rect x="{-shift - r}" y="{-past}" width="{thick}" height="{tip + past}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                    f'<rect x="{-tip}" y="{shift - r}" width="{tip + past}" height="{thick}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                    f'<path d="M {-shift},{thick * 0.35} A {bend} {bend} 0 0 1 {-thick * 0.35},{shift}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="{thick}" stroke-linecap="round"/>',
                ]
            )
        return "\n".join(
            [
                f'<rect x="{shift - r}" y="{-past}" width="{thick}" height="{tip + past}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                f'<rect x="{-past}" y="{shift - r}" width="{tip + past}" height="{thick}" rx="{r}" fill="{color}" fill-opacity="{op}"/>',
                f'<path d="M {shift},{thick * 0.35} A {bend} {bend} 0 0 0 {thick * 0.35},{shift}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="{thick}" stroke-linecap="round"/>',
            ]
        )

    body = "\n".join(
        [
            piece("tl", "#FFD737"),
            piece("tr", "#50A0FF"),
            piece("bl", "#50A0FF"),
            piece("br", "#FFD737"),
        ]
    )
    logo = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 340" role="img" aria-label="엠씨테크 MC TECH">
  <g fill="#111111">
    <text x="40" y="155" font-family="'Black Han Sans', 'Noto Sans KR', 'Malgun Gothic', sans-serif" font-size="118" font-weight="700" letter-spacing="-2">엠씨테크</text>
    <text x="178" y="230" font-family="'Montserrat', 'Noto Sans KR', Arial, sans-serif" font-size="42" font-weight="600" letter-spacing="6">MC TECH</text>
  </g>
  <g transform="translate(700 170)">
{body}
  </g>
</svg>
"""
    (OUT_DIR / "mc-tech-logo.svg").write_text(logo, encoding="utf-8")
    (OUT_DIR / "mc-tech-symbol.svg").write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 260" role="img" aria-label="MC TECH symbol">
  <g transform="translate(130 130)">
{body}
  </g>
</svg>
""",
        encoding="utf-8",
    )
    (OUT_DIR / "mc-tech-logo-onDark.svg").write_text(
        logo.replace('fill="#111111"', 'fill="#FFFFFF"'), encoding="utf-8"
    )
    print("saved svgs")


if __name__ == "__main__":
    write_svgs()
    render_logo()
