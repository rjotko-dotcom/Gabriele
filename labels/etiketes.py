"""
Popierinės etiketės raktų dėžutei – A4 PDF (20 vnt. lape, 98 × 23 mm).

  pip install reportlab
  python labels/etiketes.py                                  # pavyzdinis lapas
  python labels/etiketes.py "01:ATSARGINIAI RAKTAI" "02:SERVISAS" "03:"
  python labels/etiketes.py --csv sarasas.csv                # eilutės: numeris;tekstas
  python labels/etiketes.py --crop --out x.pdf "01:X-TRAIL"  # tik kampų žymekliai, kitas failo vardas

Matoma dalis (rėmelio langelis) – 92 × 19 mm, todėl tekstas laikomas jos viduje.
Spausdink 100 % mastelio (be "Fit to page"), kirpk pagal pilkas linijas.
"""
import csv
import os
import sys

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

LABEL_W, LABEL_H = 98 * mm, 23 * mm      # popieriaus dydis
WINDOW_W, WINDOW_H = 92 * mm, 19 * mm    # matoma dalis
COLS, ROWS = 2, 10
GAP_X, GAP_Y = 4 * mm, 3 * mm

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "blender", "fonts", "Inter-SemiBold.ttf")
pdfmetrics.registerFont(TTFont("Inter", FONT))

INK = Color(0.08, 0.08, 0.09)
MUTED = Color(0.45, 0.45, 0.47)
CUT = Color(0.80, 0.80, 0.80)

EXAMPLE = [
    ("01", "ATSARGINIAI RAKTAI"),
    ("02", "SERVISAS"),
    ("03", "BANDOMIEJI VAŽIAVIMAI"),
    ("04", "PARUOŠTI ATIDUOTI"),
    ("05", "NAUDOTI AUTOMOBILIAI"),
    ("06", "NAUJI AUTOMOBILIAI"),
]


def text_spaced(c, x, y, text, size, spacing=0.12):
    """Tekstas su platesniais tarpais tarp raidžių; grąžina plotį."""
    t = c.beginText(x, y)
    t.setFont("Inter", size)
    t.setCharSpace(size * spacing)
    t.textOut(text)
    c.drawText(t)
    return pdfmetrics.stringWidth(text, "Inter", size) + size * spacing * max(0, len(text) - 1)


def width_spaced(text, size, spacing=0.12):
    return pdfmetrics.stringWidth(text, "Inter", size) + size * spacing * max(0, len(text) - 1)


CROP = False  # True -> vietoj rėmelio tik maži kampų žymekliai už etiketės ribų


def draw_cut(c, x, y):
    c.setStrokeColor(CUT)
    if not CROP:
        c.setLineWidth(0.25)
        c.rect(x, y, LABEL_W, LABEL_H)
        return
    # minimalūs kirpimo žymekliai: 1.5 mm brūkšneliai kampuose, 0.5 mm nuo etiketės krašto
    c.setLineWidth(0.3)
    g, l = 0.5 * mm, 1.5 * mm
    for cx, sx in ((x, -1), (x + LABEL_W, 1)):
        for cy, sy in ((y, -1), (y + LABEL_H, 1)):
            c.line(cx + sx * g, cy, cx + sx * (g + l), cy)
            c.line(cx, cy + sy * g, cx, cy + sy * (g + l))


def draw_label(c, x, y, num, text):
    draw_cut(c, x, y)
    wx = x + (LABEL_W - WINDOW_W) / 2
    wy = y + 3.5 * mm  # popierius stovi ant kišenės dugno -> langelis prasideda 3.5 mm nuo apačios
    cy = wy + WINDOW_H / 2
    pad = 5 * mm
    # numeris
    c.setFillColor(MUTED)
    size_n = 9
    text_spaced(c, wx + pad, cy - size_n * 0.36, num, size_n, 0.05)
    # skiriamasis brūkšnys
    bar_x = wx + pad + 10 * mm
    c.setStrokeColor(MUTED)
    c.setLineWidth(0.6)
    c.line(bar_x, cy - 4.5 * mm, bar_x, cy + 4.5 * mm)
    # pagrindinis tekstas – centruotas likusioje dalyje, mažinamas jei per ilgas
    if text:
        left, right = bar_x + 4 * mm, wx + WINDOW_W - pad
        size = 11
        while width_spaced(text, size) > right - left and size > 6:
            size -= 0.25
        w = width_spaced(text, size)
        c.setFillColor(INK)
        text_spaced(c, left + (right - left - w) / 2, cy - size * 0.36, text, size)


def main(items, out):
    c = canvas.Canvas(out, pagesize=A4)
    c.setTitle("Raktų dėžutės etiketės")
    pw, ph = A4
    grid_w = COLS * LABEL_W + (COLS - 1) * GAP_X
    grid_h = ROWS * LABEL_H + (ROWS - 1) * GAP_Y
    x0, y0 = (pw - grid_w) / 2, (ph + grid_h) / 2
    per_page = COLS * ROWS
    for i, (num, text) in enumerate(items):
        if i and i % per_page == 0:
            c.showPage()
        k = i % per_page
        col, row = k % COLS, k // COLS
        draw_label(c, x0 + col * (LABEL_W + GAP_X), y0 - (row + 1) * LABEL_H - row * GAP_Y, num, text)
    c.save()
    print("PDF:", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    out_name = "etiketes_A4.pdf"
    if "--crop" in args:
        CROP = True
        GAP_X, GAP_Y = 6 * mm, 6 * mm  # daugiau vietos, kad žymekliai nesusilietų
        args.remove("--crop")
    if "--out" in args:
        i = args.index("--out")
        out_name = args[i + 1]
        del args[i:i + 2]
    if "--csv" in args:
        with open(args[args.index("--csv") + 1], newline="", encoding="utf-8") as f:
            items = [(r[0].strip(), r[1].strip().upper() if len(r) > 1 else "") for r in csv.reader(f, delimiter=";") if r]
    elif args:
        items = [(a.split(":", 1)[0], a.split(":", 1)[1].upper() if ":" in a else "") for a in args]
    else:
        items = EXAMPLE + [(f"{n:02d}", "") for n in range(len(EXAMPLE) + 1, 21)]
    main(items, os.path.join(HERE, out_name))
