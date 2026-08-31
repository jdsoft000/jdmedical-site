# -*- coding: utf-8 -*-
"""JD MEDICAL 간판/시트지 출력소 제출용 PDF 생성.

- DeviceCMYK
- 모든 글꼴 아웃라인 (PDF에 폰트 미임베드)
- 포맥스 도련 5mm + 재단선/도련 표시
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib.colors import CMYKColor
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(r"d:\JD_MEDICAL")
OUT_DIR = ROOT / "print"
PREVIEW_DIR = OUT_DIR / "preview"
SYMBOL_PNG = ROOT / "logo" / "jd-medical-symbol.png"

PT = 72.0 / 25.4  # mm -> pt


def mm(v: float) -> float:
    return v * PT


# Brand from official artwork (#0B2C5A / #008C8E), print-tuned CMYK
NAVY = CMYKColor(0.96, 0.72, 0.12, 0.40)
TEAL = CMYKColor(0.85, 0.06, 0.30, 0.10)
SAGE = CMYKColor(0.58, 0.10, 0.38, 0.14)
LIQUID = CMYKColor(0.28, 0.02, 0.10, 0.0)
LIQUID_TEAL = CMYKColor(0.62, 0.12, 0.42, 0.12)
LIQUID_NAVY = CMYKColor(0.82, 0.58, 0.20, 0.32)
INK = CMYKColor(0.90, 0.68, 0.15, 0.45)
BLACK = CMYKColor(0, 0, 0, 1)
WHITE = CMYKColor(0, 0, 0, 0)
CHARCOAL = CMYKColor(0.55, 0.45, 0.40, 0.78)
SLUG_INK = CMYKColor(0, 0, 0, 0.85)

RIGHT_LINES = [
    "· 이화학 장비 제조",
    "· 의료기기 장비 제조",
    "· 국내외 F&D 사업",
]


# ---------------------------------------------------------------------------
# Font outlines
# ---------------------------------------------------------------------------
class OutlineFont:
    def __init__(self, path: str, weight: int | None = None):
        font = TTFont(path)
        if weight is not None and "fvar" in font:
            font = instantiateVariableFont(font, {"wght": float(weight)})
        self.font = font
        self.gs = font.getGlyphSet()
        self.cmap = font.getBestCmap() or {}
        self.upem = font["head"].unitsPerEm
        self.ascent = font["hhea"].ascent / self.upem
        self.descent = abs(font["hhea"].descent) / self.upem

    def _adv(self, ch: str, size_pt: float) -> float:
        name = self.cmap.get(ord(ch))
        if not name:
            return 0.0
        return self.gs[name].width / self.upem * size_pt

    def width(self, text: str, size_pt: float, tracking_pt: float = 0.0) -> float:
        if not text:
            return 0.0
        return sum(self._adv(ch, size_pt) for ch in text) + tracking_pt * max(0, len(text) - 1)

    def bbox(self, text: str, tracking_em: float = 0.0) -> tuple[float, float, float, float]:
        tracking_fu = tracking_em * self.upem
        minx = miny = 1e18
        maxx = maxy = -1e18
        x = 0.0
        n = len(text)
        for i, ch in enumerate(text):
            name = self.cmap.get(ord(ch))
            if not name:
                continue
            rec = RecordingPen()
            pen = Qu2CuPen(rec, max_err=max(1.0, self.upem * 0.0004), all_cubic=True)
            self.gs[name].draw(pen)
            for op, pts in rec.value:
                if not pts:
                    continue
                for p in pts:
                    px, py = x + p[0], p[1]
                    minx, maxx = min(minx, px), max(maxx, px)
                    miny, maxy = min(miny, py), max(maxy, py)
            x += self.gs[name].width
            if i < n - 1:
                x += tracking_fu
        if minx > maxx:
            return 0.0, 0.0, 0.0, 0.0
        return minx, miny, maxx, maxy

    def size_pt_for_height(self, text: str, height_mm: float, tracking_em: float = 0.0) -> float:
        _x0, y0, _x1, y1 = self.bbox(text, tracking_em)
        fu_h = max(1.0, y1 - y0)
        return mm(height_mm) * self.upem / fu_h

    def draw(
        self,
        c: pdfcanvas.Canvas,
        text: str,
        x_pt: float,
        y_pt: float,
        size_pt: float,
        color,
        tracking_pt: float = 0.0,
        align: str = "left",
    ) -> float:
        total = self.width(text, size_pt, tracking_pt)
        x = x_pt
        if align == "center":
            x -= total / 2.0
        elif align == "right":
            x -= total
        scale = size_pt / self.upem
        c.setFillColor(color)
        for ch in text:
            name = self.cmap.get(ord(ch))
            if not name:
                x += tracking_pt
                continue
            rec = RecordingPen()
            pen = Qu2CuPen(rec, max_err=max(1.0, self.upem * 0.0004), all_cubic=True)
            self.gs[name].draw(pen)
            path = c.beginPath()
            started = False
            for op, pts in rec.value:
                if op == "moveTo":
                    px, py = pts[0]
                    path.moveTo(x + px * scale, y_pt + py * scale)
                    started = True
                elif op == "lineTo":
                    px, py = pts[0]
                    path.lineTo(x + px * scale, y_pt + py * scale)
                elif op == "curveTo":
                    (x1, y1), (x2, y2), (x3, y3) = pts[0], pts[1], pts[2]
                    path.curveTo(
                        x + x1 * scale,
                        y_pt + y1 * scale,
                        x + x2 * scale,
                        y_pt + y2 * scale,
                        x + x3 * scale,
                        y_pt + y3 * scale,
                    )
                elif op == "closePath":
                    path.close()
            if started:
                c.drawPath(path, stroke=0, fill=1, fillMode=1)
            x += self._adv(ch, size_pt) + tracking_pt
        return total


def load_fonts() -> dict[str, OutlineFont]:
    noto = r"C:\Windows\Fonts\NotoSansKR-VF.ttf"
    gothic = r"C:\Windows\Fonts\GOTHIC.TTF"
    gothicb = r"C:\Windows\Fonts\GOTHICB.TTF"
    segoe_b = r"C:\Windows\Fonts\segoeuib.ttf"
    fonts = {
        "en": OutlineFont(gothic),
        "en_bd": OutlineFont(gothicb),
        "sign": OutlineFont(segoe_b),
        "kr": OutlineFont(noto, 500),
        "kr_bd": OutlineFont(noto, 650),
    }
    return fonts


# ---------------------------------------------------------------------------
# Official JD mark (from logo/jd-medical-symbol.png)
# ---------------------------------------------------------------------------
def load_logo_contours() -> dict:
    arr = np.array(Image.open(SYMBOL_PNG).convert("RGBA"))
    h, w = arr.shape[:2]
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    opaque = a > 128
    navy_m = (opaque & (b.astype(np.int16) > g.astype(np.int16) + 12)).astype(np.uint8) * 255
    teal_m = (opaque & (g.astype(np.int16) >= b.astype(np.int16) - 8) & (g > 50)).astype(np.uint8) * 255
    kernel = np.ones((3, 3), np.uint8)
    navy_m = cv2.morphologyEx(navy_m, cv2.MORPH_CLOSE, kernel)
    teal_m = cv2.morphologyEx(teal_m, cv2.MORPH_CLOSE, kernel)

    def contours_of(mask: np.ndarray) -> list[np.ndarray]:
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cnts = [c for c in cnts if cv2.contourArea(c) > 400]
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        if not cnts:
            return []
        keep = [cnts[0]]
        main_a = cv2.contourArea(cnts[0])
        for c in cnts[1:3]:
            if cv2.contourArea(c) >= main_a * 0.12:
                keep.append(c)
        out = []
        for c in keep:
            approx = cv2.approxPolyDP(c, 0.9, True)
            out.append(approx.reshape(-1, 2).astype(np.float64))
        return out

    j = contours_of(navy_m)
    d = contours_of(teal_m)
    if not j or not d:
        raise RuntimeError(f"Logo contours failed: J={len(j)} D={len(d)}")
    return {"w": float(w), "h": float(h), "j": j, "d": d}


def logo_height_mm(width_mm: float, logo: dict) -> float:
    return width_mm * logo["h"] / logo["w"]


def draw_logo_mark(
    c: pdfcanvas.Canvas,
    x_mm: float,
    y_mm: float,
    width_mm: float,
    logo: dict,
    j_color=NAVY,
    d_color=TEAL,
) -> float:
    """Draw official JD mark. (x_mm, y_mm) = bottom-left. Returns height mm."""
    scale = mm(width_mm) / logo["w"]
    h_mm = logo_height_mm(width_mm, logo)
    ox, oy = mm(x_mm), mm(y_mm)
    img_h = logo["h"]

    def fill_paths(contours, color):
        c.setFillColor(color)
        for pts in contours:
            path = c.beginPath()
            path.moveTo(ox + pts[0, 0] * scale, oy + (img_h - pts[0, 1]) * scale)
            for px, py in pts[1:]:
                path.lineTo(ox + px * scale, oy + (img_h - py) * scale)
            path.close()
            c.drawPath(path, stroke=0, fill=1, fillMode=1)

    fill_paths(logo["j"], j_color)
    fill_paths(logo["d"], d_color)
    return h_mm


def draw_lockup(
    c: pdfcanvas.Canvas,
    fonts: dict,
    cx_mm: float,
    top_mm: float,
    mark_w_mm: float,
    logo: dict,
    word_color,
    kr_color,
    word: str = "JD MEDICAL",
    kr: str = "제이디메디컬",
    mark_j=NAVY,
    mark_d=TEAL,
) -> float:
    """Vertical lockup, top-down from top_mm (page bottom origin). Returns used height mm."""
    mark_h = logo_height_mm(mark_w_mm, logo)
    mark_x = cx_mm - mark_w_mm / 2.0
    mark_y = top_mm - mark_h
    draw_logo_mark(c, mark_x, mark_y, mark_w_mm, logo, j_color=mark_j, d_color=mark_d)

    word_size = mark_w_mm * 0.118
    word_track = word_size * 0.26
    word_pt = mm(word_size)
    word_y = mark_y - word_size * 1.05
    fonts["en"].draw(
        c,
        word,
        mm(cx_mm),
        mm(word_y),
        word_pt,
        word_color,
        tracking_pt=mm(word_track),
        align="center",
    )

    kr_size = mark_w_mm * 0.052
    kr_track = kr_size * 0.42
    kr_y = word_y - kr_size * 2.15
    fonts["kr"].draw(
        c,
        kr,
        mm(cx_mm),
        mm(kr_y),
        mm(kr_size),
        kr_color,
        tracking_pt=mm(kr_track),
        align="center",
    )
    return top_mm - (kr_y - kr_size * 0.35)


# ---------------------------------------------------------------------------
# Lab illustration (vector)
# ---------------------------------------------------------------------------
def _stroke(c, color, w_mm: float):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(mm(w_mm))
    c.setLineCap(1)
    c.setLineJoin(1)


def _line(c, x1, y1, x2, y2):
    c.line(mm(x1), mm(y1), mm(x2), mm(y2))


def _node(c, x, y, r, fill, stroke, sw):
    _stroke(c, stroke, sw)
    c.setFillColor(fill)
    c.circle(mm(x), mm(y), mm(r), stroke=1, fill=1)


def _round_flask(c, cx, cy, s, sw, liquid=LIQUID):
    """Round-bottom flask. cy = bulb center."""
    neck_w = s * 0.18
    neck_h = s * 0.42
    bulb_r = s * 0.42
    _stroke(c, NAVY, sw)
    c.setFillColor(WHITE)
    c.setLineWidth(mm(sw))
    # liquid
    c.saveState()
    clip = c.beginPath()
    clip.circle(mm(cx), mm(cy), mm(bulb_r))
    c.clipPath(clip, stroke=0, fill=0)
    c.setFillColor(liquid)
    c.rect(mm(cx - bulb_r), mm(cy - bulb_r), mm(bulb_r * 2), mm(bulb_r * 0.95), stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw))
    c.circle(mm(cx), mm(cy), mm(bulb_r), stroke=1, fill=0)
    c.setFillColor(WHITE)
    c.rect(mm(cx - neck_w / 2), mm(cy + bulb_r * 0.72), mm(neck_w), mm(neck_h), stroke=1, fill=1)
    # lip
    c.roundRect(
        mm(cx - neck_w / 2 - s * 0.06),
        mm(cy + bulb_r * 0.72 + neck_h - s * 0.05),
        mm(neck_w + s * 0.12),
        mm(s * 0.08),
        mm(s * 0.03),
        stroke=1,
        fill=0,
    )


def _erlenmeyer(c, cx, cy, s, sw, liquid=LIQUID):
    top_y = cy + s * 0.55
    bot_y = cy - s * 0.55
    bot_w = s * 0.85
    neck_w = s * 0.16
    neck_h = s * 0.28
    _stroke(c, NAVY, sw)
    # liquid trapezoid
    liq_y = bot_y + s * 0.42
    p = c.beginPath()
    p.moveTo(mm(cx - bot_w / 2 + s * 0.04), mm(bot_y + sw))
    p.lineTo(mm(cx + bot_w / 2 - s * 0.04), mm(bot_y + sw))
    t = (liq_y - bot_y) / (top_y - bot_y)
    half = (bot_w / 2) * (1 - t) + (neck_w / 2) * t
    p.lineTo(mm(cx + half), mm(liq_y))
    p.lineTo(mm(cx - half), mm(liq_y))
    p.close()
    c.setFillColor(liquid)
    c.drawPath(p, stroke=0, fill=1)
    body = c.beginPath()
    body.moveTo(mm(cx - neck_w / 2), mm(top_y))
    body.lineTo(mm(cx - bot_w / 2), mm(bot_y))
    body.lineTo(mm(cx + bot_w / 2), mm(bot_y))
    body.lineTo(mm(cx + neck_w / 2), mm(top_y))
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw))
    c.drawPath(body, stroke=1, fill=0)
    c.rect(mm(cx - neck_w / 2), mm(top_y), mm(neck_w), mm(neck_h), stroke=1, fill=0)
    c.roundRect(
        mm(cx - neck_w / 2 - s * 0.05),
        mm(top_y + neck_h - s * 0.04),
        mm(neck_w + s * 0.10),
        mm(s * 0.07),
        mm(s * 0.02),
        stroke=1,
        fill=0,
    )


def _test_tube(c, cx, cy, s, sw, liquid=LIQUID):
    w = s * 0.22
    h = s * 1.15
    r = w / 2
    y0 = cy - h / 2
    _stroke(c, NAVY, sw)
    c.setFillColor(liquid)
    c.roundRect(mm(cx - w / 2 + 1), mm(y0 + 1), mm(w - 2), mm(h * 0.42), mm(r * 0.8), stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.roundRect(mm(cx - w / 2), mm(y0), mm(w), mm(h), mm(r), stroke=1, fill=0)


def _sep_funnel(c, cx, cy, s, sw):
    _stroke(c, NAVY, sw)
    p = c.beginPath()
    p.moveTo(mm(cx - s * 0.28), mm(cy + s * 0.15))
    p.lineTo(mm(cx + s * 0.28), mm(cy + s * 0.15))
    p.lineTo(mm(cx + s * 0.04), mm(cy - s * 0.35))
    p.lineTo(mm(cx - s * 0.04), mm(cy - s * 0.35))
    p.close()
    c.setFillColor(LIQUID)
    c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.drawPath(p, stroke=1, fill=0)
    c.rect(mm(cx - s * 0.07), mm(cy + s * 0.15), mm(s * 0.14), mm(s * 0.22), stroke=1, fill=0)
    c.line(mm(cx), mm(cy - s * 0.35), mm(cx), mm(cy - s * 0.62))
    c.circle(mm(cx), mm(cy - s * 0.42), mm(s * 0.045), stroke=1, fill=0)


def _column(c, cx, cy, s, sw):
    _stroke(c, NAVY, sw)
    c.roundRect(mm(cx - s * 0.16), mm(cy - s * 0.55), mm(s * 0.32), mm(s * 1.05), mm(s * 0.04), stroke=1, fill=0)
    c.setFillColor(LIQUID)
    c.rect(mm(cx - s * 0.13), mm(cy - s * 0.48), mm(s * 0.26), mm(s * 0.28), stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    for i in range(3):
        yy = cy - s * 0.05 + i * s * 0.14
        c.line(mm(cx - s * 0.13), mm(yy), mm(cx + s * 0.13), mm(yy))
    c.rect(mm(cx - s * 0.10), mm(cy + s * 0.50), mm(s * 0.20), mm(s * 0.12), stroke=1, fill=0)


def _beaker(c, cx, cy, s, sw):
    _stroke(c, NAVY, sw)
    p = c.beginPath()
    p.moveTo(mm(cx - s * 0.32), mm(cy + s * 0.38))
    p.lineTo(mm(cx - s * 0.28), mm(cy - s * 0.38))
    p.lineTo(mm(cx + s * 0.28), mm(cy - s * 0.38))
    p.lineTo(mm(cx + s * 0.32), mm(cy + s * 0.38))
    c.setFillColor(LIQUID)
    liq = c.beginPath()
    liq.moveTo(mm(cx - s * 0.30), mm(cy - s * 0.02))
    liq.lineTo(mm(cx - s * 0.28), mm(cy - s * 0.38))
    liq.lineTo(mm(cx + s * 0.28), mm(cy - s * 0.38))
    liq.lineTo(mm(cx + s * 0.30), mm(cy - s * 0.02))
    liq.close()
    c.drawPath(liq, stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.drawPath(p, stroke=1, fill=0)
    # spout
    c.line(mm(cx + s * 0.32), mm(cy + s * 0.38), mm(cx + s * 0.42), mm(cy + s * 0.48))


def _arrow(c, x1, y1, x2, y2, sw, color, head=22.0):
    _stroke(c, color, sw)
    c.line(mm(x1), mm(y1), mm(x2), mm(y2))
    ang = math.atan2(y2 - y1, x2 - x1)
    a = 0.42
    p = c.beginPath()
    p.moveTo(mm(x2), mm(y2))
    p.lineTo(mm(x2 - head * math.cos(ang - a)), mm(y2 - head * math.sin(ang - a)))
    p.lineTo(mm(x2 - head * math.cos(ang + a)), mm(y2 - head * math.sin(ang + a)))
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1, fillMode=1)


def _dash_arrow(c, pts, sw, color, head=18.0):
    c.setStrokeColor(color)
    c.setLineWidth(mm(sw))
    c.setDash(6, 5)
    c.setLineCap(1)
    p = c.beginPath()
    p.moveTo(mm(pts[0][0]), mm(pts[0][1]))
    for x, y in pts[1:]:
        p.lineTo(mm(x), mm(y))
    c.drawPath(p, stroke=1, fill=0)
    c.setDash()
    x1, y1 = pts[-2]
    x2, y2 = pts[-1]
    _arrow(c, x1, y1, x2, y2, sw, color, head)


def _sparkle(c, cx, cy, s, color):
    p = c.beginPath()
    pts = []
    for i in range(8):
        ang = math.pi / 2 + i * math.pi / 4
        r = s if i % 2 == 0 else s * 0.32
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    p.moveTo(mm(pts[0][0]), mm(pts[0][1]))
    for x, y in pts[1:]:
        p.lineTo(mm(x), mm(y))
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1, fillMode=1)


def _gel_box(c, cx, cy, s, sw):
    w, h = s * 1.55, s * 0.42
    _stroke(c, NAVY, sw)
    c.setFillColor(WHITE)
    c.roundRect(mm(cx - w / 2), mm(cy - h / 2), mm(w), mm(h), mm(s * 0.08), stroke=1, fill=1)
    c.setFillColor(SAGE)
    c.roundRect(mm(cx - w * 0.22), mm(cy - h * 0.18), mm(w * 0.50), mm(h * 0.36), mm(s * 0.04), stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setFillColor(NAVY)
    plus = s * 0.10
    c.setLineWidth(mm(sw * 0.85))
    c.line(mm(cx - w * 0.38 - plus), mm(cy), mm(cx - w * 0.38 + plus), mm(cy))
    c.line(mm(cx - w * 0.38), mm(cy - plus), mm(cx - w * 0.38), mm(cy + plus))
    tick_y = cy - h / 2
    for i in range(9):
        tx = cx - w * 0.36 + i * (w * 0.08)
        th = s * 0.06 if i % 2 == 0 else s * 0.035
        c.line(mm(tx), mm(tick_y), mm(tx), mm(tick_y + th))


def _pipette(c, cx, cy, s, sw):
    _stroke(c, NAVY, sw)
    c.setFillColor(WHITE)
    c.roundRect(mm(cx - s * 0.16), mm(cy - s * 0.28), mm(s * 0.32), mm(s * 0.55), mm(s * 0.05), stroke=1, fill=1)
    c.setFillColor(SAGE)
    c.circle(mm(cx), mm(cy - s * 0.02), mm(s * 0.07), stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setFillColor(WHITE)
    p = c.beginPath()
    p.moveTo(mm(cx - s * 0.07), mm(cy + s * 0.27))
    p.lineTo(mm(cx + s * 0.07), mm(cy + s * 0.27))
    p.lineTo(mm(cx + s * 0.03), mm(cy + s * 0.52))
    p.lineTo(mm(cx - s * 0.03), mm(cy + s * 0.52))
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    c.setFillColor(SAGE)
    c.circle(mm(cx), mm(cy + s * 0.58), mm(s * 0.055), stroke=1, fill=1)


def _conical(c, cx, cy, s, sw):
    _stroke(c, NAVY, sw)
    p = c.beginPath()
    p.moveTo(mm(cx - s * 0.18), mm(cy + s * 0.22))
    p.lineTo(mm(cx + s * 0.18), mm(cy + s * 0.22))
    p.lineTo(mm(cx + s * 0.03), mm(cy - s * 0.42))
    p.lineTo(mm(cx - s * 0.03), mm(cy - s * 0.42))
    p.close()
    c.setFillColor(WHITE)
    c.drawPath(p, stroke=1, fill=1)
    liq = c.beginPath()
    liq.moveTo(mm(cx - s * 0.11), mm(cy - s * 0.02))
    liq.lineTo(mm(cx + s * 0.11), mm(cy - s * 0.02))
    liq.lineTo(mm(cx + s * 0.03), mm(cy - s * 0.40))
    liq.lineTo(mm(cx - s * 0.03), mm(cy - s * 0.40))
    liq.close()
    c.setFillColor(SAGE)
    c.drawPath(liq, stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.roundRect(mm(cx - s * 0.12), mm(cy + s * 0.22), mm(s * 0.24), mm(s * 0.16), mm(s * 0.03), stroke=1, fill=0)
    c.line(mm(cx + s * 0.12), mm(cy + s * 0.12), mm(cx + s * 0.28), mm(cy + s * 0.12))


def _centrifuge(c, cx, cy, s, sw):
    """Benchtop refrigerated centrifuge — hero equipment."""
    bw, bh = s * 0.95, s * 0.58
    x0, y0 = cx - bw / 2, cy - bh / 2
    _stroke(c, NAVY, sw)
    c.setFillColor(WHITE)
    c.roundRect(mm(x0), mm(y0), mm(bw), mm(bh), mm(s * 0.06), stroke=1, fill=1)
    # lid
    c.setFillColor(NAVY)
    c.roundRect(mm(x0 + s * 0.04), mm(y0 + bh - s * 0.02), mm(bw - s * 0.08), mm(s * 0.11), mm(s * 0.04), stroke=0, fill=1)
    c.setFillColor(SAGE)
    c.roundRect(mm(x0 + s * 0.22), mm(y0 + bh + s * 0.02), mm(bw * 0.38), mm(s * 0.045), mm(s * 0.02), stroke=0, fill=1)
    # rotor window
    rx, ry, rr = x0 + bw * 0.38, y0 + bh * 0.46, s * 0.20
    c.setFillColor(CMYKColor(0.20, 0.04, 0.06, 0.04))
    c.circle(mm(rx), mm(ry), mm(rr), stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw * 1.1))
    c.circle(mm(rx), mm(ry), mm(rr), stroke=1, fill=0)
    c.circle(mm(rx), mm(ry), mm(rr * 0.22), stroke=1, fill=1)
    c.setFillColor(NAVY)
    for i in range(6):
        ang = i * math.pi / 3
        x1 = rx + rr * 0.30 * math.cos(ang)
        y1 = ry + rr * 0.30 * math.sin(ang)
        x2 = rx + rr * 0.82 * math.cos(ang)
        y2 = ry + rr * 0.82 * math.sin(ang)
        c.setLineWidth(mm(sw * 0.9))
        c.line(mm(x1), mm(y1), mm(x2), mm(y2))
        c.circle(mm(x2), mm(y2), mm(s * 0.028), stroke=0, fill=1)
    # control panel
    px = x0 + bw * 0.72
    c.setFillColor(WHITE)
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw))
    c.roundRect(mm(px), mm(y0 + bh * 0.18), mm(bw * 0.22), mm(bh * 0.58), mm(s * 0.03), stroke=1, fill=1)
    c.setFillColor(SAGE)
    c.roundRect(mm(px + s * 0.03), mm(y0 + bh * 0.48), mm(bw * 0.16), mm(bh * 0.18), mm(s * 0.015), stroke=0, fill=1)
    c.setFillColor(NAVY)
    for i in range(3):
        c.circle(mm(px + bw * 0.07 + i * s * 0.055), mm(y0 + bh * 0.30), mm(s * 0.018), stroke=0, fill=1)
    # feet
    c.setFillColor(NAVY)
    c.rect(mm(x0 + s * 0.08), mm(y0 - s * 0.04), mm(s * 0.10), mm(s * 0.05), stroke=0, fill=1)
    c.rect(mm(x0 + bw - s * 0.18), mm(y0 - s * 0.04), mm(s * 0.10), mm(s * 0.05), stroke=0, fill=1)
    # side vent
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw * 0.7))
    for i in range(4):
        c.line(mm(x0 + s * 0.06), mm(y0 + s * 0.10 + i * s * 0.06), mm(x0 + s * 0.16), mm(y0 + s * 0.10 + i * s * 0.06))


def _incubator(c, cx, cy, s, sw):
    """Lab incubator cabinet with glass door and shelves."""
    bw, bh = s * 0.72, s * 1.05
    x0, y0 = cx - bw / 2, cy - bh / 2
    corner = s * 0.06
    header = s * 0.12
    _stroke(c, NAVY, sw)
    c.setFillColor(WHITE)
    c.roundRect(mm(x0), mm(y0), mm(bw), mm(bh), mm(corner), stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.roundRect(mm(x0), mm(y0 + bh - header), mm(bw), mm(header), mm(corner), stroke=0, fill=1)
    c.rect(mm(x0), mm(y0 + bh - header), mm(bw), mm(header - corner), stroke=0, fill=1)
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw))
    c.roundRect(mm(x0), mm(y0), mm(bw), mm(bh), mm(corner), stroke=1, fill=0)
    c.setFillColor(SAGE)
    c.roundRect(mm(x0 + bw * 0.18), mm(y0 + bh - s * 0.095), mm(bw * 0.38), mm(s * 0.07), mm(s * 0.012), stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.circle(mm(x0 + bw * 0.68), mm(y0 + bh - s * 0.06), mm(s * 0.018), stroke=0, fill=1)
    c.circle(mm(x0 + bw * 0.78), mm(y0 + bh - s * 0.06), mm(s * 0.018), stroke=0, fill=1)
    # glass door
    inset = s * 0.07
    c.setFillColor(CMYKColor(0.18, 0.03, 0.08, 0.02))
    c.roundRect(
        mm(x0 + inset),
        mm(y0 + s * 0.10),
        mm(bw - inset * 2),
        mm(bh - s * 0.26),
        mm(s * 0.02),
        stroke=1,
        fill=1,
    )
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw * 0.85))
    inner_l = x0 + inset + s * 0.04
    inner_r = x0 + bw - inset - s * 0.04
    for i in range(3):
        sy = y0 + s * 0.28 + i * s * 0.20
        c.line(mm(inner_l), mm(sy), mm(inner_r), mm(sy))
    # tiny samples on shelves
    c.setFillColor(SAGE)
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw * 0.6))
    c.ellipse(mm(inner_l + s * 0.08), mm(y0 + s * 0.30), mm(inner_l + s * 0.18), mm(y0 + s * 0.42), stroke=1, fill=1)
    c.rect(mm(inner_l + s * 0.28), mm(y0 + s * 0.50), mm(s * 0.08), mm(s * 0.14), stroke=1, fill=1)
    c.ellipse(mm(inner_r - s * 0.22), mm(y0 + s * 0.30), mm(inner_r - s * 0.12), mm(y0 + s * 0.40), stroke=1, fill=1)
    # handle
    c.setFillColor(NAVY)
    c.roundRect(mm(x0 + bw - inset * 0.55), mm(y0 + bh * 0.42), mm(s * 0.04), mm(s * 0.18), mm(s * 0.015), stroke=0, fill=1)
    # vents
    c.setStrokeColor(NAVY)
    c.setLineWidth(mm(sw * 0.7))
    for i in range(5):
        c.line(mm(x0 + bw * 0.18 + i * s * 0.08), mm(y0 + s * 0.04), mm(x0 + bw * 0.18 + i * s * 0.08), mm(y0 + s * 0.08))


def _shaker(c, cx, cy, s, sw):
    """Orbital shaking incubator — flasks sit on the machine."""
    bw, bh = s * 1.35, s * 0.42
    x0, y0 = cx - bw / 2, cy - bh / 2
    _stroke(c, NAVY, sw)
    c.setFillColor(WHITE)
    c.roundRect(mm(x0), mm(y0), mm(bw), mm(bh), mm(s * 0.05), stroke=1, fill=1)
    # platform
    c.setFillColor(SAGE)
    c.roundRect(mm(x0 + s * 0.08), mm(y0 + bh * 0.55), mm(bw - s * 0.16), mm(bh * 0.22), mm(s * 0.02), stroke=1, fill=1)
    # two small flasks on platform
    _erlenmeyer(c, x0 + bw * 0.32, y0 + bh + s * 0.22, s * 0.42, sw * 0.75, LIQUID_TEAL)
    _round_flask(c, x0 + bw * 0.62, y0 + bh + s * 0.18, s * 0.36, sw * 0.75, LIQUID_NAVY)
    # front panel
    c.setFillColor(SAGE)
    c.roundRect(mm(x0 + s * 0.10), mm(y0 + s * 0.08), mm(bw * 0.28), mm(bh * 0.32), mm(s * 0.02), stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.circle(mm(x0 + bw * 0.48), mm(y0 + bh * 0.28), mm(s * 0.045), stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.circle(mm(x0 + bw * 0.48), mm(y0 + bh * 0.28), mm(s * 0.018), stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.circle(mm(x0 + bw * 0.62), mm(y0 + bh * 0.28), mm(s * 0.028), stroke=0, fill=1)
    # feet
    c.rect(mm(x0 + s * 0.08), mm(y0 - s * 0.04), mm(s * 0.08), mm(s * 0.045), stroke=0, fill=1)
    c.rect(mm(x0 + bw - s * 0.16), mm(y0 - s * 0.04), mm(s * 0.08), mm(s * 0.045), stroke=0, fill=1)


def draw_lab_illustration(c: pdfcanvas.Canvas, x: float, y: float, w: float, h: float):
    """장비 중심 구성: 원심분리기·배양기·진탕기를 크게, 유리기구는 보조."""
    sw = max(5.5, w * 0.007)
    unit = min(w, h)

    _centrifuge(c, x + w * 0.30, y + h * 0.74, unit * 0.46, sw)
    _incubator(c, x + w * 0.74, y + h * 0.50, unit * 0.64, sw)
    _shaker(c, x + w * 0.32, y + h * 0.16, unit * 0.38, sw)
    _sparkle(c, x + w * 0.95, y + h * 0.10, max(12.0, w * 0.016), SAGE)


# ---------------------------------------------------------------------------
# Page helpers
# ---------------------------------------------------------------------------
def new_canvas(path: Path, w_mm: float, h_mm: float) -> pdfcanvas.Canvas:
    c = pdfcanvas.Canvas(str(path), pagesize=(mm(w_mm), mm(h_mm)))
    c.setTitle(path.stem)
    c.setAuthor("JD MEDICAL")
    c.setSubject("출력용 · DeviceCMYK · 글꼴 곡선화 · 실사이즈")
    c.setCreator("JD MEDICAL signage generator")
    return c


def draw_crop_and_notes(c, page_w, page_h, slug, bleed, trim_w, trim_h, note: str):
    ox = slug + bleed
    oy = slug + bleed
    mark = 10.0
    c.setStrokeColor(SLUG_INK)
    c.setLineWidth(0.35)
    c.setDash()
    # 4 corners: marks in slug only, aligned to trim
    corners = [
        (ox, oy, -1, -1),
        (ox + trim_w, oy, 1, -1),
        (ox, oy + trim_h, -1, 1),
        (ox + trim_w, oy + trim_h, 1, 1),
    ]
    for tx, ty, dx, dy in corners:
        c.line(mm(tx + dx * (bleed + 1.5)), mm(ty), mm(tx + dx * (bleed + mark)), mm(ty))
        c.line(mm(tx), mm(ty + dy * (bleed + 1.5)), mm(tx), mm(ty + dy * (bleed + mark)))
    # bleed box (dashed)
    c.setDash(1.5, 1.5)
    c.setLineWidth(0.25)
    c.rect(mm(slug), mm(slug), mm(trim_w + bleed * 2), mm(trim_h + bleed * 2), stroke=1, fill=0)
    c.setDash()
    return note


def draw_slug_text(c, fonts, page_w, slug, note: str):
    fonts["kr"].draw(
        c,
        note,
        mm(page_w / 2),
        mm(4.5),
        mm(3.2),
        SLUG_INK,
        tracking_pt=0,
        align="center",
    )


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
def make_sign(fonts, out: Path) -> dict:
    """고무 스카시: JD 대문자 300mm, 소문자 medical 250mm. 1p 시안 / 2p 커팅원고."""
    fnt = fonts["sign"]
    jd, med = "JD", "medical"
    jd_h, med_h = 300.0, 250.0
    side = 90.0
    gap = 50.0
    jd_pt = fnt.size_pt_for_height(jd, jd_h)
    med_pt = fnt.size_pt_for_height(med, med_h)
    _x0, j_miny, _x1, _jmax = fnt.bbox(jd)
    y_base = -j_miny * (jd_pt / fnt.upem)
    board_h = jd_h
    jd_w = fnt.width(jd, jd_pt) / PT
    med_w = fnt.width(med, med_pt) / PT
    group_w = jd_w + gap + med_w
    board_w = float(int(round((group_w + side * 2) / 10.0) * 10))
    x_jd = (board_w - group_w) / 2.0
    x_med = x_jd + jd_w + gap

    c = new_canvas(out, board_w, board_h)

    def paint(color, bg):
        c.setFillColor(bg)
        c.rect(0, 0, mm(board_w), mm(board_h), stroke=0, fill=1)
        fnt.draw(c, jd, mm(x_jd), y_base, jd_pt, color, align="left")
        fnt.draw(c, med, mm(x_med), y_base, med_pt, color, align="left")

    paint(WHITE, CHARCOAL)
    c.showPage()
    paint(BLACK, WHITE)
    c.save()
    return {
        "w": board_w,
        "h": board_h,
        "jd_h": jd_h,
        "med_h": med_h,
        "file": out,
    }


def make_formax(fonts, logo, out: Path) -> dict:
    w = h = 1220.0
    c = new_canvas(out, w, h)

    c.setFillColor(WHITE)
    c.rect(0, 0, mm(w), mm(h), stroke=0, fill=1)

    mark_w = 430.0
    top = h - 70.0
    cx = w / 2.0
    used_h = draw_lockup(c, fonts, cx, top, mark_w, logo, NAVY, NAVY)
    lockup_bottom = top - used_h
    ill_margin_x = 40.0
    ill_margin_b = 40.0
    ill_top_y = lockup_bottom - 16.0
    ill_h = ill_top_y - ill_margin_b
    ill_w = w - ill_margin_x * 2
    draw_lab_illustration(c, ill_margin_x, ill_margin_b, ill_w, ill_h)

    c.save()
    return {"page": (w, h), "trim": (w, h), "bleed": 0.0, "file": out}


def _lockup_size(fonts, logo, mark_w: float) -> tuple[float, float]:
    mark_h = logo_height_mm(mark_w, logo)
    word_size = mark_w * 0.118
    word_track = word_size * 0.26
    word_w = fonts["en"].width("JD MEDICAL", mm(word_size), mm(word_track)) / PT
    kr_size = mark_w * 0.052
    kr_track = kr_size * 0.42
    kr_w = fonts["kr"].width("제이디메디컬", mm(kr_size), mm(kr_track)) / PT
    art_w = max(mark_w, word_w, kr_w)
    art_h = mark_h + word_size * 1.05 + kr_size * 2.15 + kr_size * 0.35
    return art_w, art_h


def make_door(fonts, logo, out: Path) -> dict:
    """문 유리 커팅: 유리 전체(750×1930)가 아니라 로고+글씨 실사이즈."""
    mark_w = 320.0
    pad = 15.0
    art_w, art_h = _lockup_size(fonts, logo, mark_w)
    w = float(int(round(art_w + pad * 2)))
    h = float(int(round(art_h + pad * 2)))
    top = h - pad
    cx = w / 2.0
    c = new_canvas(out, w, h)

    c.setFillColor(CHARCOAL)
    c.rect(0, 0, mm(w), mm(h), stroke=0, fill=1)
    draw_lockup(
        c, fonts, cx, top, mark_w, logo, WHITE, WHITE, mark_j=WHITE, mark_d=WHITE
    )
    c.showPage()

    c.setFillColor(WHITE)
    c.rect(0, 0, mm(w), mm(h), stroke=0, fill=1)
    draw_lockup(
        c, fonts, cx, top, mark_w, logo, BLACK, BLACK, mark_j=BLACK, mark_d=BLACK
    )
    c.save()
    return {"w": w, "h": h, "mark_w": mark_w, "file": out}


def make_right_copy(fonts, out: Path) -> dict:
    """우측 유리 커팅: 유리 전체(1370×2100)가 아니라 문구 실사이즈."""
    size_mm = 78.0
    line_gap = 160.0
    pad = 20.0
    fnt = fonts["kr_bd"]
    size_pt = mm(size_mm)
    scale = size_pt / fnt.upem

    widths = [fnt.width(line, size_pt) / PT for line in RIGHT_LINES]
    bboxes = [fnt.bbox(line) for line in RIGHT_LINES]
    art_w = max(widths)
    left_ext = max(0.0, max(-b[0] * scale / PT for b in bboxes))
    first_maxy = bboxes[0][3]
    last_miny = bboxes[-1][1]
    art_h = (first_maxy - last_miny) * scale / PT + line_gap * (len(RIGHT_LINES) - 1)

    w = float(int(round(art_w + left_ext + pad * 2)))
    h = float(int(round(art_h + pad * 2)))
    x_left = mm(pad + left_ext)
    y_last = mm(pad) - last_miny * scale
    y_first = y_last + mm(line_gap) * (len(RIGHT_LINES) - 1)

    c = new_canvas(out, w, h)

    def paint(color, bg):
        c.setFillColor(bg)
        c.rect(0, 0, mm(w), mm(h), stroke=0, fill=1)
        for i, line in enumerate(RIGHT_LINES):
            y = y_first - i * mm(line_gap)
            fnt.draw(c, line, x_left, y, size_pt, color, align="left")

    paint(WHITE, CHARCOAL)
    c.showPage()
    paint(BLACK, WHITE)
    c.save()
    return {"w": w, "h": h, "file": out}


def strip_unused_fonts(path: Path):
    """reportlab registers Helvetica even when unused — remove so shops see outlined-only."""
    import pikepdf

    tmp = path.with_suffix(".tmp.pdf")
    pdf = pikepdf.open(path)
    for page in pdf.pages:
        res = page.get("/Resources")
        if res is not None and "/Font" in res:
            del res["/Font"]
    pdf.save(tmp)
    pdf.close()
    tmp.replace(path)


def render_preview(pdf_path: Path, stem: str, max_w: int = 900):
    doc = fitz.open(pdf_path)
    info = []
    for i, page in enumerate(doc):
        pw, ph = page.rect.width, page.rect.height
        scale = max_w / pw
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        dest = PREVIEW_DIR / f"{stem}_p{i + 1}.png"
        pix.save(str(dest))
        fonts = page.get_fonts()
        info.append(
            {
                "page": i + 1,
                "pt": (pw, ph),
                "mm": (pw / PT, ph / PT),
                "fonts": fonts,
                "preview": dest,
            }
        )
    doc.close()
    return info


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading fonts…")
    fonts = load_fonts()
    print("Loading official logo…")
    logo = load_logo_contours()
    print(f"  logo px {logo['w']:.0f}×{logo['h']:.0f}  J contours={len(logo['j'])} D={len(logo['d'])}")

    files = {
        "sign": OUT_DIR / "JD_1_간판_고무스카시_1940x300_JD300_medical250.pdf",
        "formax": OUT_DIR / "JD_2_포맥스_1220x1220.pdf",
        "door": OUT_DIR / "JD_3_문유리_로고커팅.pdf",
        "right": OUT_DIR / "JD_4_우측문구_글씨커팅.pdf",
    }

    print("1/4 sign…")
    s = make_sign(fonts, files["sign"])
    print(f"  board {s['w']:.0f}×{s['h']:.0f}mm  JD {s['jd_h']:.0f}mm  medical {s['med_h']:.0f}mm")
    print("2/4 formax…")
    f = make_formax(fonts, logo, files["formax"])
    print(f"  page {f['page'][0]:.0f}×{f['page'][1]:.0f}  trim {f['trim']}")
    print("3/4 door…")
    d = make_door(fonts, logo, files["door"])
    door_final = OUT_DIR / f"JD_3_문유리_로고커팅_{int(round(d['w']))}x{int(round(d['h']))}.pdf"
    files["door"].replace(door_final)
    files["door"] = door_final
    print(f"  artwork {d['w']:.0f}×{d['h']:.0f}mm  mark {d['mark_w']:.0f}mm")
    print("4/4 right copy…")
    r = make_right_copy(fonts, files["right"])
    right_final = OUT_DIR / f"JD_4_우측문구_글씨커팅_{int(round(r['w']))}x{int(round(r['h']))}.pdf"
    files["right"].replace(right_final)
    files["right"] = right_final
    print(f"  artwork {r['w']:.0f}×{r['h']:.0f}mm")

    print("Stripping unused Helvetica…")
    for path in files.values():
        strip_unused_fonts(path)

    print("Previews + checks…")
    all_ok = True
    for key, path in files.items():
        infos = render_preview(path, key)
        for inf in infos:
            font_ok = len(inf["fonts"]) == 0
            if not font_ok:
                all_ok = False
            print(
                f"  {path.name} p{inf['page']}: "
                f"{inf['mm'][0]:.1f}×{inf['mm'][1]:.1f}mm  "
                f"embedded_fonts={len(inf['fonts'])}  "
                f"preview={inf['preview'].name}"
            )
    print("DONE" if all_ok else "DONE WITH FONT WARNINGS")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
