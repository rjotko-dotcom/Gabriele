"""Generuoja 2D brėžinius (DXF, AutoCAD 2018) + PDF peržiūras.

  python3 gen_dxf.py <out_dir>
"""
import os, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment
from params import *  # noqa

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

A = A_STRAIGHT          # 696
RT = R_TOP              # 383.5
HB = L_BODY / 2         # 1049.5
HT = L_TOP / 2          # 1079.5
DW = door_width()       # 647
DH = door_height()      # 754


def new_doc(scale_main):
    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.styles.add("LT", font="arial.ttf")
    lay = doc.layers
    lay.add("KONTURAI", color=7, lineweight=50)
    lay.add("MATOMOS", color=8, lineweight=25)
    lay.add("NEMATOMOS", color=8, linetype="DASHED", lineweight=18)
    lay.add("ASYS", color=1, linetype="CENTER", lineweight=13)
    lay.add("MATMENYS", color=5, lineweight=13)
    lay.add("TEKSTAS", color=7, lineweight=18)
    lay.add("FURNITURA", color=3, lineweight=25)
    lay.add("PJUVIS", color=7, lineweight=50)
    for sc in sorted({scale_main, 2, 5, 10, 50}):
        ds = doc.dimstyles.new(f"M1_{sc}")
        ds.dxf.dimtxsty = "LT"
        ds.dxf.dimtxt = 1.8
        ds.dxf.dimasz = 1.5
        ds.dxf.dimscale = sc
        ds.dxf.dimexe = 1.5
        ds.dxf.dimexo = 1.0
        ds.dxf.dimgap = 0.8
        ds.dxf.dimdec = 1
        ds.dxf.dimtad = 1
        ds.dxf.dimtih = 0
        ds.dxf.dimtoh = 0
        ds.dxf.dimblk = "ARCHTICK"
        ds.dxf.dimclrd = 5
        ds.dxf.dimclre = 5
        ds.dxf.dimclrt = 7
        ds.dxf.dimzin = 8
        ds.dxf.dimlunit = 2
        ds.dxf.dimdsep = ord(",")
    doc.header["$LTSCALE"] = scale_main / 2
    return doc


class Sheet:
    def __init__(self, scale):
        self.sc = scale
        self.doc = new_doc(scale)
        self.msp = self.doc.modelspace()

    # --- primitives
    def line(self, p1, p2, layer="KONTURAI"):
        self.msp.add_line(p1, p2, dxfattribs={"layer": layer})

    def rect(self, x0, y0, x1, y1, layer="KONTURAI"):
        self.msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                                dxfattribs={"layer": layer})

    def poly(self, pts, layer="KONTURAI", close=True):
        self.msp.add_lwpolyline(pts, format="xyb", close=close, dxfattribs={"layer": layer})

    def circle(self, c, r, layer="KONTURAI"):
        self.msp.add_circle(c, r, dxfattribs={"layer": layer})

    def text(self, s, p, h=1.8, align=TextEntityAlignment.LEFT, layer="TEKSTAS", sc=None):
        sc = sc or self.sc
        t = self.msp.add_text(s, height=h * sc, dxfattribs={"layer": layer, "style": "LT"})
        t.set_placement(p, align=align)

    def mtext(self, s, p, h=1.8, width=None, sc=None):
        sc = sc or self.sc
        m = self.msp.add_mtext(s, dxfattribs={"layer": "TEKSTAS", "style": "LT",
                                              "char_height": h * sc})
        m.dxf.insert = p
        m.dxf.attachment_point = 1
        if width:
            m.dxf.width = width * sc

    def hdim(self, x1, x2, y, base_y, sc=None, text="<>"):
        sc = sc or self.sc
        d = self.msp.add_linear_dim(base=(x1, base_y), p1=(x1, y), p2=(x2, y), angle=0,
                                    dimstyle=f"M1_{sc}", text=text,
                                    dxfattribs={"layer": "MATMENYS"})
        d.render()

    def vdim(self, z1, z2, x, base_x, sc=None, text="<>"):
        sc = sc or self.sc
        d = self.msp.add_linear_dim(base=(base_x, z1), p1=(x, z1), p2=(x, z2), angle=90,
                                    dimstyle=f"M1_{sc}", text=text,
                                    dxfattribs={"layer": "MATMENYS"})
        d.render()

    def rdim(self, center, r, angle, sc=None):
        sc = sc or self.sc
        d = self.msp.add_radius_dim(center=center, radius=r, angle=angle,
                                    dimstyle=f"M1_{sc}", dxfattribs={"layer": "MATMENYS"})
        d.render()

    def ddim(self, center, r, angle, sc=None):
        sc = sc or self.sc
        d = self.msp.add_diameter_dim(center=center, radius=r, angle=angle,
                                      dimstyle=f"M1_{sc}", dxfattribs={"layer": "MATMENYS"})
        d.render()

    def leader(self, pts, s, sc=None, h=1.8):
        sc = sc or self.sc
        self.msp.add_leader(pts, dimstyle=f"M1_{sc}", dxfattribs={"layer": "MATMENYS"})
        end = pts[-1]
        right = pts[-1][0] >= pts[-2][0]
        self.text(s, (end[0] + (1 if right else -1) * 1.0 * sc, end[1] + 0.6 * sc), h=h, sc=sc,
                  align=TextEntityAlignment.LEFT if right else TextEntityAlignment.RIGHT)

    def arrow(self, p1, p2, sc=None, layer="FURNITURA"):
        """Rodyklė p1 -> p2 (užpildyta)."""
        import math
        sc = sc or self.sc
        self.line(p1, p2, layer)
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        L, W = 3.5 * sc, 1.2 * sc
        b = (p2[0] - L * math.cos(ang), p2[1] - L * math.sin(ang))
        n = (-math.sin(ang) * W, math.cos(ang) * W)
        self.msp.add_solid([p2, (b[0] + n[0], b[1] + n[1]), (b[0] - n[0], b[1] - n[1])],
                           dxfattribs={"layer": layer})

    def title(self, s, sub, p):
        self.text(s, p, h=5)
        self.text(sub, (p[0], p[1] - 7.5 * self.sc), h=3)

    def save(self, name):
        path = os.path.join(OUT, name + ".dxf")
        self.doc.saveas(path)
        return path


# ======================================================================
# Pagalbinės: matmenų eilės per 7 mm popieriuje
ROW = 7.0
LFT = TextEntityAlignment.LEFT
RGT = TextEntityAlignment.RIGHT
CTR = TextEntityAlignment.MIDDLE_CENTER


def label(s, anchor, txt_pt, text):
    """Išnaša: rodyklė į anchor, horizontali lentynėlė iki txt_pt."""
    sc = s.sc
    right = txt_pt[0] > anchor[0]
    shelf = (txt_pt[0] - (1 if right else -1) * 3 * sc, txt_pt[1])
    s.msp.add_leader([anchor, shelf, txt_pt], dimstyle=f"M1_{sc}", dxfattribs={"layer": "MATMENYS"})
    s.text(text, (txt_pt[0] + (1 if right else -1) * 0.8 * sc, txt_pt[1] + 0.4 * sc),
           align=LFT if right else RGT)


# 1. VAIZDAS IŠ VIRŠAUS ===================================================
def plan():
    s = Sheet(50)
    r = ROW * s.sc
    ny = NOTCH_Y0
    s.poly([(-A, -RT, 0), (A, -RT, 1), (A, RT, 0), (NICHE_HALF, RT, 0), (NICHE_HALF, ny, 0),
            (-NICHE_HALF, ny, 0), (-NICHE_HALF, RT, 0), (-A, RT, 1)])
    s.poly([(-NICHE_HALF, ny, 0), (-NICHE_HALF, WORK_Y1, 0), (NICHE_HALF, WORK_Y1, 0),
            (NICHE_HALF, ny, 0)], close=False)
    s.line((-NICHE_HALF, Y_INNER_FRONT), (NICHE_HALF, Y_INNER_FRONT), "NEMATOMOS")
    s.line((-NICHE_HALF, Y_INNER_FRONT), (-NICHE_HALF, ny), "NEMATOMOS")
    s.line((NICHE_HALF, Y_INNER_FRONT), (NICHE_HALF, ny), "NEMATOMOS")
    RB = R_BODY
    s.poly([(-NICHE_HALF, RB, 0), (-A, RB, 1), (-A, -RB, 0), (A, -RB, 1), (A, RB, 0),
            (NICHE_HALF, RB, 0)], "NEMATOMOS", close=False)
    for (x, y) in GROMMETS_WORK + GROMMETS_LEDGE:
        s.circle((x, y), GROMMET_D / 2)
        s.circle((x, y), GROMMET_D / 2 - 6, "MATOMOS")
        s.line((x - 50, y), (x + 50, y), "ASYS")
        s.line((x, y - 50), (x, y + 50), "ASYS")
    s.line((0, -RT - 100), (0, RT + 100), "ASYS")
    s.line((-HT - 100, 0), (HT + 100, 0), "ASYS")

    # apačioje
    s.hdim(-HT, -A, -RT, -RT - r)
    s.hdim(-A, A, -RT, -RT - r)
    s.hdim(A, HT, -RT, -RT - r)
    s.hdim(-HT, HT, -RT, -RT - 2 * r)
    # viršuje
    gx = [g[0] for g in GROMMETS_WORK]
    s.hdim(-NICHE_HALF, gx[0], RT, RT + r)
    s.hdim(gx[0], gx[1], RT, RT + r)
    s.hdim(gx[1], NICHE_HALF, RT, RT + r)
    s.hdim(-HT, -NICHE_HALF, RT, RT + 2 * r)
    s.hdim(-NICHE_HALF, NICHE_HALF, RT, RT + 2 * r)
    s.hdim(NICHE_HALF, HT, RT, RT + 2 * r)
    # kairėje
    s.vdim(-RT, ny, -NICHE_HALF, -HT - r)
    s.vdim(ny, WORK_Y1, -NICHE_HALF, -HT - r)
    s.vdim(-RT, RT, -HT, -HT - 2 * r)
    # dešinėje – angų padėtis
    s.rdim((A, 0), RT, 60)
    s.ddim(GROMMETS_WORK[0], GROMMET_D / 2, 225)

    s.text("KLIENTO PUSĖ (priekis)", (0, -RT - 2 * r - 6 * s.sc), align=CTR)
    s.text("DARBUOTOJO PUSĖ (galas)", (0, RT + 2 * r + 9 * s.sc), align=CTR)
    X = HT + 8 * s.sc
    s.text("Kabelių angų centrai: darbo stalviršyje – 63,5 mm nuo kliento atramos krašto; "
           "atramoje – 150 mm nuo priekinio krašto, 450 mm nuo ašies.",
           (-HT - 2 * r, -RT - 2 * r - 11 * s.sc))
    label(s, (-900, -250), (X, -RT - 60), "Viršutinis stalviršis (kliento atrama) h=1141, medis 40 mm")
    label(s, (-250, 250), (X, 180), "Darbo stalviršis h=900, medis 40 mm")
    label(s, GROMMETS_LEDGE[0], (X, -RT + 120), "Kabelių anga Ø60 (mokėjimo terminalui)")
    label(s, (GROMMETS_WORK[1][0] + 21, GROMMETS_WORK[1][1] + 21), (X, 60),
          "Kabelių anga Ø60, 2 vnt. (kasos aparatui, monitoriui)")
    s.title("VAIZDAS IŠ VIRŠAUS", "M 1:50   |   matmenys mm", (-HT - 2 * r, -RT - 2 * r - 20 * s.sc))
    return s.save("01_Vaizdas_is_virsaus_M1-50")


# 2. VAIZDAS IŠ PRIEKIO ====================================================
def front():
    s = Sheet(50)
    r = ROW * s.sc
    s.rect(-HT, H_BODY, HT, H_TOTAL)
    s.poly([(-HB, H_BODY, 0), (-HB, 0, 0), (HB, 0, 0), (HB, H_BODY, 0)], close=False)
    s.line((-A, 0), (-A, H_BODY), "MATOMOS")
    s.line((A, 0), (A, H_BODY), "MATOMOS")
    s.rect(-FLUTE_HALF, FLUTE_Z0, FLUTE_HALF, H_BODY)
    for i in range(1, FLUTE_N):
        x = -FLUTE_HALF + i * 2 * FLUTE_R
        s.line((x, FLUTE_Z0), (x, H_BODY), "MATOMOS")
    s.rect(-NICHE_HALF, WORK_TOP_Z - T_WORK, NICHE_HALF, WORK_TOP_Z, "NEMATOMOS")
    s.line((-HT - 150, 0), (HT + 150, 0))

    s.hdim(-HB, -FLUTE_HALF, 0, -r)
    s.hdim(-FLUTE_HALF, FLUTE_HALF, 0, -r)
    s.hdim(FLUTE_HALF, HB, 0, -r)
    s.hdim(-HB, HB, 0, -2 * r)
    s.hdim(-HT, HT, H_TOTAL, H_TOTAL + r)
    s.vdim(0, FLUTE_Z0, -HT, -HT - r)
    s.vdim(FLUTE_Z0, H_BODY, -HT, -HT - r)
    s.vdim(0, H_BODY, HT, HT + r)
    s.vdim(H_BODY, H_TOTAL, HT, HT + r)
    s.vdim(0, H_TOTAL, HT, HT + 2 * r)

    X = HT + 2 * r + 6 * s.sc
    label(s, (900, 500), (X, 700), "Aksomo apmušalas (rožinis)")
    label(s, (300, 300), (X, 450), "Rievėta panelė: 40 rievių po 29,8 mm (vyno sp. aksomas)")
    label(s, (700, H_TOTAL - 20), (X, 1000), "Stalviršis – medis, 40 mm")
    label(s, (500, WORK_TOP_Z - 20), (X, 200), "Darbo stalviršis už priekio (nematomas)")
    s.title("VAIZDAS IŠ PRIEKIO (kliento pusė)", "M 1:50   |   matmenys mm", (-HT - r, -2 * r - 15 * s.sc))
    return s.save("02_Vaizdas_is_priekio_M1-50")


# 3. VAIZDAS IŠ GALO ======================================================
def back():
    s = Sheet(50)
    r = ROW * s.sc
    s.rect(-HT, H_BODY, HT, H_TOTAL)
    s.poly([(-HB, H_BODY, 0), (-HB, 0, 0), (-NICHE_HALF, 0, 0), (-NICHE_HALF, H_BODY, 0)], close=False)
    s.poly([(HB, H_BODY, 0), (HB, 0, 0), (NICHE_HALF, 0, 0), (NICHE_HALF, H_BODY, 0)], close=False)
    s.line((-A, 0), (-A, H_BODY), "MATOMOS")
    s.line((A, 0), (A, H_BODY), "MATOMOS")
    s.rect(-NICHE_HALF, WORK_TOP_Z - T_WORK, NICHE_HALF, WORK_TOP_Z)
    for sgn in (-1, 1):
        x0, x1 = sorted((sgn * DOOR_X_IN, sgn * DOOR_X_OUT))
        s.rect(x0, DOOR_Z0, x1, DOOR_Z1)
        hx, ex = sgn * DOOR_X_OUT, sgn * DOOR_X_IN
        s.poly([(ex, DOOR_Z1, 0), (hx, (DOOR_Z0 + DOOR_Z1) / 2, 0), (ex, DOOR_Z0, 0)], "NEMATOMOS",
               close=False)
        s.circle((sgn * 60, TIPON_Z), 15, "FURNITURA")
    s.rect(-SIDE_X0, 0, SIDE_X0, LEG_H - 3, "MATOMOS")
    for sgn in (-1, 1):
        x0, x1 = sorted((sgn * (T / 2 + 1), sgn * (SIDE_X0 - 1)))
        s.line((x0, SHELF_Z0 + T / 2), (x1, SHELF_Z0 + T / 2), "NEMATOMOS")
    s.line((0, BOTTOM_Z1), (0, TOPRAIL_Z0), "NEMATOMOS")
    s.line((-HT - 150, 0), (HT + 150, 0))

    s.hdim(-HT, -NICHE_HALF, H_TOTAL, H_TOTAL + r)
    s.hdim(-NICHE_HALF, NICHE_HALF, H_TOTAL, H_TOTAL + r)
    s.hdim(NICHE_HALF, HT, H_TOTAL, H_TOTAL + r)
    s.hdim(-HT, HT, H_TOTAL, H_TOTAL + 2 * r)
    s.hdim(-DOOR_X_OUT, -DOOR_X_IN, 0, -r)
    s.hdim(DOOR_X_IN, DOOR_X_OUT, 0, -r)
    s.vdim(0, LEG_H, -HT, -HT - r)
    s.vdim(DOOR_Z0, DOOR_Z1, -HT, -HT - r)
    s.vdim(WORK_TOP_Z - T_WORK, WORK_TOP_Z, -HT, -HT - r)
    s.vdim(0, WORK_TOP_Z, HT, HT + r)
    s.vdim(WORK_TOP_Z, H_TOTAL, HT, HT + r)
    s.vdim(0, H_TOTAL, HT, HT + 2 * r)

    X = HT + 2 * r + 6 * s.sc
    XL = -HT - 2 * r - 2 * s.sc
    label(s, (75, TIPON_Z + 10), (X, 1050), "Spaudimo vieta (Blum TIP-ON), durys be rankenų")
    label(s, (-300, 1000), (X, 1250), "Atvira niša po kliento atrama, aukštis 201 mm")
    label(s, (300, 880), (X, 880), "Darbo stalviršis h=900, medis 40 mm")
    label(s, (420, SHELF_Z0 + 9), (X, 520), "Reguliuojama lentyna, po 1 kiekvienoje pusėje")
    label(s, (-250, 250), (X, 300), "Durys LMDP 18 mm, 2 vnt., atsidaro į šonus")
    label(s, (300, 50), (X, 60), "Cokolis įtrauktas 60 mm (vieta pėdoms), kojelės h=100")
    s.text("Tarpas tarp durų 3 mm", (0, -2 * r), align=CTR)
    s.title("VAIZDAS IŠ GALO (darbuotojo pusė)", "M 1:50   |   matmenys mm", (XL, -2 * r - 15 * s.sc))
    return s.save("03_Vaizdas_is_galo_M1-50")


# 4. MAZGAS: PJŪVIS A-A per TIP-ON (M 1:2) =================================
def detail_section():
    s = Sheet(2)
    r = ROW * s.sc
    y_cut = DOOR_Y0 - 160  # pertvaros nutraukimas
    W = 140                # rodomas durų plotis nuo centro
    pp = [(-T / 2, y_cut), (T / 2, y_cut), (T / 2, DOOR_Y0), (-T / 2, DOOR_Y0)]
    s.poly([(x, y, 0) for x, y in pp], "PJUVIS")
    h = s.msp.add_hatch(color=8, dxfattribs={"layer": "PJUVIS"})
    h.set_pattern_fill("ANSI31", scale=0.25)
    h.paths.add_polyline_path(pp, is_closed=True)
    for sgn in (-1, 1):
        x0, x1 = sorted((sgn * DOOR_X_IN, sgn * W))
        dp = [(x0, DOOR_Y0), (x1, DOOR_Y0), (x1, DOOR_Y1), (x0, DOOR_Y1)]
        s.poly([(x, y, 0) for x, y in dp], "PJUVIS")
        h = s.msp.add_hatch(color=8, dxfattribs={"layer": "PJUVIS"})
        h.set_pattern_fill("ANSI31", scale=0.25, angle=90)
        h.paths.add_polyline_path(dp, is_closed=True)
        # adapterinė plokštelė 2 mm + TIP-ON korpusas
        ax0, ax1 = sorted((sgn * T / 2, sgn * (T / 2 + 2)))
        s.rect(ax0, DOOR_Y0 - 2 - TIPON_LEN - 6, ax1, DOOR_Y0 - 8, "FURNITURA")
        tx0, tx1 = sorted((sgn * (T / 2 + 2), sgn * (T / 2 + 2 + TIPON_W - 2)))
        s.rect(tx0, DOOR_Y0 - 2 - TIPON_LEN, tx1, DOOR_Y0 - 6, "FURNITURA")
        # stūmoklis su magnetu
        cx = sgn * TIPON_X
        s.rect(cx - 5, DOOR_Y0 - 6, cx + 5, DOOR_Y0, "FURNITURA")
        # atsitrenkimo plokštelė
        s.rect(cx - 12, DOOR_Y0 - 1.5, cx + 12, DOOR_Y0, "FURNITURA")
        s.line((cx, DOOR_Y0 - TIPON_LEN - 20), (cx, DOOR_Y1 + 12), "ASYS")
        # nutraukimo linija
        s.poly([(sgn * W, DOOR_Y0 - 6, 0), (sgn * W, DOOR_Y1 + 6, 0)], "MATOMOS", close=False)
    s.poly([(-25, y_cut, 0), (-8, y_cut, 0), (-3, y_cut + 5, 0), (3, y_cut - 5, 0), (8, y_cut, 0),
            (25, y_cut, 0)], "MATOMOS", close=False)

    # matmenys
    s.hdim(-T / 2, T / 2, y_cut, y_cut - r)
    s.hdim(-DOOR_X_IN, DOOR_X_IN, DOOR_Y1, DOOR_Y1 + r)
    s.hdim(DOOR_X_IN, TIPON_X, DOOR_Y1, DOOR_Y1 + 2 * r)
    s.hdim(-T / 2 - TIPON_W, -T / 2, DOOR_Y0 - 2 - TIPON_LEN, DOOR_Y0 - TIPON_LEN - 2 - r)
    s.vdim(DOOR_Y0 - 2 - TIPON_LEN, DOOR_Y0, -W, -W - r)
    s.vdim(DOOR_Y0, DOOR_Y1, -W, -W - r)

    # veikimas
    s.arrow((80, DOOR_Y1 + 45), (80, DOOR_Y1 + 4))
    s.text("1. Paspausti duris (~2 mm)", (86, DOOR_Y1 + 32))
    s.arrow((-80, DOOR_Y1 + 4), (-80, DOOR_Y1 + 45))
    s.text("2. TIP-ON išstumia duris", (-86, DOOR_Y1 + 32), align=RGT)
    s.text("DARBUOTOJO PUSĖ", (0, DOOR_Y1 + 70), align=CTR)
    s.text("spintelės vidus", (60, y_cut + 20))

    X = W + 2 * r
    label(s, (T / 2 + 12, DOOR_Y0 - 45), (X, DOOR_Y0 - 30), "Blum TIP-ON durims (stūmoklis su magnetu)")
    label(s, (T / 2 + 1, DOOR_Y0 - 70), (X, DOOR_Y0 - 60), "Adapterinė plokštelė, prisukama prie pertvaros")
    label(s, (TIPON_X + 10, DOOR_Y0 - 0.8), (X, DOOR_Y0 + 5), "Metalinė atsitrenkimo plokštelė ant durų")
    label(s, (110, DOOR_Y0 + 9), (X, DOOR_Y1 + 20), "Durys LMDP 18 mm")
    label(s, (0, y_cut + 40), (X, y_cut + 30), "Vidurinė pertvara LMDP 18 mm")
    s.title("MAZGAS. PJŪVIS A-A per TIP-ON (horizontalus, h = 787 mm)",
            "M 1:2   |   matmenys mm   |   abi durys – simetriškai", (-W - 2 * r, y_cut - 2 * r - 12 * s.sc))
    return s.save("04_Mazgas_TIP-ON_pjuvis_A-A_M1-2")


# 5. MAZGAS: durų vidinė pusė – vyrių ir TIP-ON padėtis (M 1:10) ==============
def detail_door():
    s = Sheet(10)
    r = ROW * s.sc
    bx, by = 0.0, 0.0
    s.rect(bx, by, bx + DW, by + DH)
    cx = bx + CUP_C + CUP_D / 2
    for hz in (DH - HINGE_FROM_EDGE, HINGE_FROM_EDGE):
        s.circle((cx, by + hz), CUP_D / 2, "FURNITURA")
        s.rect(cx + CUP_D / 2, by + hz - 9, cx + CUP_D / 2 + 25, by + hz + 9, "FURNITURA")
        s.line((cx - 30, by + hz), (cx + 30, by + hz), "ASYS")
        s.line((cx, by + hz - 30), (cx, by + hz + 30), "ASYS")
    tz = by + DH - TIPON_FROM_TOP
    tx = bx + DW - (TIPON_X - DOOR_X_IN)
    s.rect(tx - 12, tz - 16, tx + 12, tz + 16, "FURNITURA")
    s.line((tx - 30, tz), (tx + 30, tz), "ASYS")
    s.line((tx, tz - 30), (tx, tz + 30), "ASYS")
    # A-A pjūvio žymė
    for xx, d in ((bx - 2 * r - 60, 1), (bx + DW + r + 60, -1)):
        s.line((xx, tz), (xx + d * 25, tz), "PJUVIS")
        s.text("A", (xx, tz + 15), align=CTR, h=3)

    s.vdim(by + DH - HINGE_FROM_EDGE, by + DH, bx, bx - r)
    s.vdim(by + HINGE_FROM_EDGE, by + DH - HINGE_FROM_EDGE, bx, bx - r)
    s.vdim(by, by + HINGE_FROM_EDGE, bx, bx - r)
    s.vdim(by, by + DH, bx, bx - 2 * r)
    s.vdim(tz, by + DH, bx + DW, bx + DW + r)
    s.hdim(bx, cx, by + DH, by + DH + r)
    s.hdim(tx, bx + DW, by + DH, by + DH + r)
    s.hdim(bx, bx + DW, by + DH, by + DH + 2 * r)
    s.ddim((cx, by + HINGE_FROM_EDGE), CUP_D / 2, 45)

    X = bx + DW + 2 * r
    label(s, (cx + 10, by + DH - HINGE_FROM_EDGE - 10), (X, by + DH - 230),
          "Vyris Blum CLIP top 110° BE spyruoklės, 2 vnt.")
    s.text("Taurelė Ø35, gylis 13 mm, C = 4 mm nuo krašto", (X + 0.8 * s.sc, by + DH - 260))
    label(s, (tx + 12, tz - 10), (X, tz - 110), "Atsitrenkimo plokštelė (TIP-ON)")
    s.text("vyrių pusė", (bx + 15, by + DH / 2), h=1.8)
    s.text("atidarymo kraštas", (bx + DW - 15, by + DH / 2), align=RGT)

    notes = (
        "VEIKIMAS\\P"
        "1. Durys be rankenų. Lengvai paspaudus durų kraštą (~2 mm), TIP-ON stūmoklis "
        "išstumia duris, toliau jos atidaromos ranka.\\P"
        "2. Uždaroma pastumiant iki galo – magnetinis stūmoklis prilaiko duris.\\P"
        "MONTAVIMAS\\P"
        "3. TIP-ON – spintelės viduje, į vidurinės pertvaros šoną (per adapterinę plokštelę), "
        "70 mm nuo durų viršaus, prie atidarymo krašto. Ant durų – metalinė plokštelė.\\P"
        "4. Vyriai TIK be spyruoklės ir be BLUMOTION, kitaip durys neatšoks.\\P"
        "5. Tarpas tarp durų 3 mm; TIP-ON stūmoklio ilgis reguliuojamas.\\P"
        "FURNITŪRA (2 durims)\\P"
        "Blum TIP-ON durims – 2 vnt.; adapterinė plokštelė – 2 vnt.; atsitrenkimo plokštelė – "
        "2 vnt.; vyris CLIP top 110° be spyruoklės – 4 vnt.; montavimo plokštelė – 4 vnt.; "
        "lentynų laikiklis Ø5 – 8 vnt.; reguliuojama kojelė h=100 – 6 vnt.; kabelių anga Ø60 – 3 vnt."
    )
    s.mtext(notes, (X, by + 380), width=95)
    s.title("MAZGAS. DURŲ VIDINĖ PUSĖ – vyrių ir TIP-ON padėtis",
            "M 1:10   |   matmenys mm   |   dešinės durys (žiūrint iš darbuotojo pusės); kitos – veidrodiškai",
            (bx - 2 * r, by - 15 * s.sc))
    return s.save("05_Mazgas_duru_vyriai_TIP-ON_M1-10")


def to_pdf(path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    doc = ezdxf.readfile(path)
    fig = plt.figure(figsize=(16.54, 11.69))  # A3
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE,
                        color_policy=ColorPolicy.BLACK, lineweight_scaling=1.2)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace())
    ax.set_aspect("equal")
    ax.axis("off")
    pdf = path.replace(".dxf", ".pdf")
    fig.savefig(pdf)
    fig.savefig(path.replace(".dxf", ".png"), dpi=110)
    plt.close(fig)
    return pdf


if __name__ == "__main__":
    for f in (plan, front, back, detail_section, detail_door):
        p = f()
        print(p, to_pdf(p))
