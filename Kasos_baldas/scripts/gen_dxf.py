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


# 1. VAIZDAS IŠ VIRŠAUS (kontūrai – iš 3D modelio pjūvių) ===================
import json as _json
from shapely.geometry import Polygon, LineString, MultiLineString

SECTIONS = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sections.json")))


def _loops(key, closed_only=False):
    return [l["pts"] + ([l["pts"][0]] if l["closed"] else []) for l in SECTIONS[key]
            if (l["closed"] or not closed_only) and len(l["pts"]) > 2]


def _lines(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [list(geom.coords)]
    if hasattr(geom, "geoms"):
        out = []
        for g in geom.geoms:
            out += _lines(g)
        return out
    return []


def top_polygon():
    loops = _loops("top_1141")
    return Polygon(max(loops, key=len))


def cut_curve_y(poly, x):
    """Išpjovos kreivės y ties x (žemiausias kontūro taškas virš y=-300)."""
    ln = LineString([(x, -300), (x, 500)])
    inter = poly.boundary.intersection(ln)
    ys = [p.y for p in getattr(inter, "geoms", [inter]) if hasattr(p, "y")]
    return min(ys)


def plan():
    s = Sheet(50)
    r = ROW * s.sc
    tp = top_polygon()
    s.poly([(x, y, 0) for x, y in tp.exterior.coords])
    # kitos linijos: matoma dalis – už stalviršio, nematoma – po juo
    for key in ("work_900", "body_1000", "body_500"):
        for pts in _loops(key):
            ln = LineString(pts)
            for seg in _lines(ln.difference(tp)):
                s.poly([(x, y, 0) for x, y in seg], "KONTURAI" if key == "work_900" else "MATOMOS", close=False)
            for seg in _lines(ln.intersection(tp)):
                s.poly([(x, y, 0) for x, y in seg], "NEMATOMOS", close=False)
    s.rect(PED_X0, CARC_Y0, PED_X1, FRONT_Y1, "NEMATOMOS")
    s.rect(CAB_X0, CARC_Y0, CAB_X1, FRONT_Y1, "NEMATOMOS")
    for (x, y) in GROMMETS_WORK:
        s.circle((x, y), GROMMET_D / 2)
        s.circle((x, y), GROMMET_D / 2 - 6, "MATOMOS")
        s.line((x - 50, y), (x + 50, y), "ASYS")
        s.line((x, y - 50), (x, y + 50), "ASYS")
    s.line((0, -RT - 100), (0, RT + 100), "ASYS")
    s.line((-HT - 100, 0), (HT + 100, 0), "ASYS")

    minx, miny, maxx, maxy = tp.bounds
    minx, maxx, miny = -HT, HT, -RT          # vardiniai išoriniai matmenys
    apex = cut_curve_y(tp, 0.0)
    # išpjovos plotis ties y = RT
    inter = tp.boundary.intersection(LineString([(-A, RT), (A, RT)]))
    xs = sorted(p.x for p in getattr(inter, "geoms", [inter]) if hasattr(p, "x"))
    cutx = max(abs(xs[0]), abs(xs[-1])) if xs else 650.0
    lip = [p for p in tp.exterior.coords if abs(p[0]) > cutx and abs(p[0]) < A + 60]
    lipx, lipy = max(lip, key=lambda p: p[1]) if lip else (680, maxy)
    lipx = abs(lipx)

    s.hdim(minx, -A, miny, miny - r)
    s.hdim(-A, A, miny, miny - r)
    s.hdim(A, maxx, miny, miny - r)
    s.hdim(minx, maxx, miny, miny - 2 * r)
    s.hdim(-cutx, cutx, RT, maxy + r)
    s.hdim(cutx, lipx, maxy, maxy + r)
    s.hdim(-NICHE_HALF if False else -CAV_HALF, CAV_HALF, WORK_Y1, maxy + 2 * r)
    s.vdim(miny, apex, 0, -HT - r)
    s.vdim(apex, RT, 0, -HT - r)
    s.vdim(miny, RT, minx, -HT - 2 * r)
    s.vdim(RT, maxy, lipx, HT + r)
    s.vdim(miny, maxy, maxx, HT + 2 * r)
    s.rdim((A, 0), RT, -60)

    # išpjovos kreivės koordinatės (nuo stalviršio galinio krašto y = RT)
    rows = []
    for x in (0, 100, 200, 300, 400, 500, 600):
        try:
            rows.append((x, RT - cut_curve_y(tp, x)))
        except ValueError:
            pass
    tx, ty = -HT - 2 * r, miny - 2 * r - 9 * s.sc
    s.text("Išpjovos kreivė (simetriška): atstumas nuo stalviršio galinio krašto, mm", (tx, ty))
    s.text("x nuo ašies:  " + "   ".join(f"{x:>4}" for x, _ in rows), (tx, ty - 3.5 * s.sc))
    s.text("gylis:          " + "   ".join(f"{v:>5.0f}" for _, v in rows), (tx, ty - 7 * s.sc))

    s.text("KLIENTO PUSĖ (priekis)", (0, miny - 2 * r - 4 * s.sc), align=CTR)
    s.text("DARBUOTOJO PUSĖ (galas)", (0, maxy + 2 * r + 9 * s.sc), align=CTR)
    X = HT + 2 * r + 6 * s.sc
    label(s, (-800, -250), (X, -RT - 40), "Viršutinis stalviršis h=1141, medis 40 mm")
    label(s, (150, 300), (X, 260), "Darbo stalviršis h=900, medis 40 mm, kampai R28")
    label(s, (GROMMETS_WORK[1][0] + 21, GROMMETS_WORK[1][1] + 21), (X, 120),
          "Kabelių angos Ø60, 2 vnt.")
    label(s, (lipx - 5, maxy - 3), (X, 400), "Suapvalintas iškyšulys išpjovos gale")
    label(s, (0, -200), (X, -150), "Lenkta niša (nematoma po atrama)")
    s.title("VAIZDAS IŠ VIRŠAUS", "M 1:50   |   matmenys mm   |   kontūrai pagal 3D modelį",
            (-HT - 2 * r, miny - 2 * r - 27 * s.sc))
    return s.save("01_Vaizdas_is_virsaus_M1-50")


# 2. VAIZDAS IŠ PRIEKIO ====================================================
def front():
    s = Sheet(50)
    r = ROW * s.sc
    s.rect(-HT, H_BODY, HT, H_TOTAL)
    s.poly([(-HB, H_BODY, 0), (-HB, BASE_H, 0), (HB, BASE_H, 0), (HB, H_BODY, 0)], close=False)
    s.rect(-HB + 10, 0, HB - 10, BASE_H)
    s.line((-A, BASE_H), (-A, H_BODY), "MATOMOS")
    s.line((A, BASE_H), (A, H_BODY), "MATOMOS")
    # rievių niša
    s.rect(-FLUTE_NICHE_HALF - 5, BASE_H, FLUTE_NICHE_HALF + 5, H_BODY)
    s.rect(-FLUTE_HALF, BASE_H, FLUTE_HALF, H_BODY, "MATOMOS")
    for i in range(1, FLUTE_N):
        x = -FLUTE_HALF + i * 2 * FLUTE_R
        s.line((x, BASE_H), (x, H_BODY), "MATOMOS")
    s.rect(-CAV_HALF, WORK_TOP_Z - T_WORK, CAV_HALF, WORK_TOP_Z, "NEMATOMOS")
    s.line((-HT - 150, 0), (HT + 150, 0))

    nh = FLUTE_NICHE_HALF + 5
    s.hdim(-HB, -nh, 0, -r)
    s.hdim(-nh, nh, 0, -r)
    s.hdim(nh, HB, 0, -r)
    s.hdim(-HB, HB, 0, -2 * r)
    s.hdim(-HT, HT, H_TOTAL, H_TOTAL + r)
    s.vdim(0, BASE_H, -HT, -HT - r)
    s.vdim(BASE_H, H_BODY, -HT, -HT - r)
    s.vdim(0, H_BODY, HT, HT + r)
    s.vdim(H_BODY, H_TOTAL, HT, HT + r)
    s.vdim(0, H_TOTAL, HT, HT + 2 * r)

    X = HT + 2 * r + 6 * s.sc
    label(s, (900, 500), (X, 700), "Korpusas – dekoratyvinis tinkas, pudrinė rožinė")
    label(s, (300, 300), (X, 450), "Rievės: 40 vnt. Ø29, vyno sp., įleistos į 14 mm nišą (R10 kampai)")
    label(s, (700, H_TOTAL - 20), (X, 1000), "Stalviršis – medis, 40 mm")
    label(s, (-300, 20), (X, 120), "Cokolis – tamsiai rudas, h=40, įtrauktas 10 mm")
    s.title("VAIZDAS IŠ PRIEKIO (kliento pusė)", "M 1:50   |   matmenys mm", (-HT - r, -2 * r - 15 * s.sc))
    return s.save("02_Vaizdas_is_priekio_M1-50")


# 3. VAIZDAS IŠ GALO (darbuotojo pusė; brėžinio x = -X) =====================
def back():
    s = Sheet(50)
    r = ROW * s.sc
    m = lambda x: -x  # noqa
    s.rect(-HT, H_BODY, HT, H_TOTAL)
    for sg in (-1, 1):
        s.poly([(sg * HB, H_BODY, 0), (sg * HB, BASE_H, 0), (sg * CAV_HALF, BASE_H, 0),
                (sg * CAV_HALF, H_BODY, 0)], close=False)
        s.rect(sg * (HB - 10), 0, sg * CAV_HALF, BASE_H)
    s.line((-A, BASE_H), (-A, H_BODY), "MATOMOS")
    s.line((A, BASE_H), (A, H_BODY), "MATOMOS")
    s.rect(-CAV_HALF, WORK_TOP_Z - T_WORK, CAV_HALF, WORK_TOP_Z)
    px0, px1 = sorted((m(PED_X0), m(PED_X1)))
    s.line((px0, 0), (px0, TOPRAIL_Z1))
    s.line((px1, 0), (px1, TOPRAIL_Z1))
    hx0, hx1 = sorted((m(HANDLE_X0), m(HANDLE_X1)))
    for (z0, z1) in drawer_fronts():
        s.rect(px0 + 1.5, z0, px1 - 1.5, z1)
        s.rect(hx0, z1 - HANDLE_FROM_TOP - HANDLE_H, hx1, z1 - HANDLE_FROM_TOP, "FURNITURA")
    s.rect(px0 + T, 0, px1 - T, LEG_H - 2, "MATOMOS")
    cx0, cx1 = sorted((m(CAB_X0), m(CAB_X1)))
    s.line((cx0, 0), (cx0, TOPRAIL_Z1))
    s.line((cx1, 0), (cx1, TOPRAIL_Z1))
    dx0, dx1 = sorted((m(DOOR_X_OUT), m(DOOR_X_IN)))
    s.rect(dx0, FRONT_Z0, dx1, FRONT_Z1)
    s.poly([(dx0, FRONT_Z1, 0), (dx1, (FRONT_Z0 + FRONT_Z1) / 2, 0), (dx0, FRONT_Z0, 0)], "NEMATOMOS",
           close=False)
    s.circle((dx0 + 50, TIPON_Z), 15, "FURNITURA")
    s.rect(cx0 + T, 0, cx1 - T, LEG_H - 2, "MATOMOS")
    s.line((cx0 + T + 1, SHELF_Z0 + T / 2), (cx1 - T - 1, SHELF_Z0 + T / 2), "NEMATOMOS")
    s.line((px1, 0), (cx0, 0))
    s.line((-HT - 150, 0), (HT + 150, 0))

    s.hdim(-HT, -CAV_HALF, H_TOTAL, H_TOTAL + r)
    s.hdim(-CAV_HALF, CAV_HALF, H_TOTAL, H_TOTAL + r)
    s.hdim(CAV_HALF, HT, H_TOTAL, H_TOTAL + r)
    s.hdim(-HT, HT, H_TOTAL, H_TOTAL + 2 * r)
    s.hdim(px0, px1, 0, -r)
    s.hdim(px1, cx0, 0, -r)
    s.hdim(cx0, cx1, 0, -r)
    s.hdim(hx0, hx1, 0, -2 * r)
    fr = drawer_fronts()
    s.vdim(0, LEG_H, -HT, -HT - 2 * r)
    s.vdim(fr[0][0], fr[0][1], -HT, -HT - r)
    s.vdim(fr[1][0], fr[1][1], -HT, -HT - 2 * r)
    s.vdim(fr[2][0], fr[2][1], -HT, -HT - r)
    s.vdim(0, WORK_TOP_Z, HT, HT + r)
    s.vdim(WORK_TOP_Z, H_TOTAL, HT, HT + r)
    s.vdim(0, H_TOTAL, HT, HT + 2 * r)

    X = HT + 2 * r + 6 * s.sc
    label(s, (dx0 + 60, TIPON_Z + 10), (X, 760), "Spaudimo vieta – durelė be rankenos (Blum TIP-ON)")
    label(s, (0, 1000), (X, 1250), "Lenkta niša po kliento atrama, h 201 mm, juoda matinė")
    label(s, (450, 880), (X, 1000), "Darbo stalviršis h=900, medis 40 mm")
    label(s, (450, SHELF_Z0 + 9), (X, 520), "Reguliuojama lentyna")
    label(s, (500, 300), (X, 300), "Fasadai – antracito sp. matinis laminatas, 18 mm")
    label(s, (0, 400), (X, 160), "Vieta kojoms 542 mm, su galine panele")
    label(s, ((hx0 + hx1) / 2, fr[2][1] - 17), (X, 1120), "Metalinės rankenėlės 200 mm, išsikišusios 12 mm")
    label(s, (cx0 + 100, 50), (X, 30), "Įtrauktas cokolis 60 mm, kojelės h=100")
    s.text("Stalčių blokas – darbuotojo kairėje, spintelė – dešinėje", (0, -3 * r), align=CTR)
    s.title("VAIZDAS IŠ GALO (darbuotojo pusė)", "M 1:50   |   matmenys mm",
            (-HT - 2 * r - 2 * s.sc, -3 * r - 15 * s.sc))
    return s.save("03_Vaizdas_is_galo_M1-50")


# 4. MAZGAS: PJŪVIS A-A per TIP-ON (M 1:2) =================================
def detail_section():
    s = Sheet(2)
    r = ROW * s.sc
    sx0, sx1 = CAB_X1 - T, CAB_X1          # spintelės vidinis šonas (-289..-271)
    y_cut = FRONT_Y0 - 160
    xl, xr = sx0 - 130, sx1 + 90           # rodoma sritis
    pp = [(sx0, y_cut), (sx1, y_cut), (sx1, FRONT_Y0), (sx0, FRONT_Y0)]
    s.poly([(x, y, 0) for x, y in pp], "PJUVIS")
    h = s.msp.add_hatch(color=8, dxfattribs={"layer": "PJUVIS"})
    h.set_pattern_fill("ANSI31", scale=0.25)
    h.paths.add_polyline_path(pp, is_closed=True)
    dp = [(xl, FRONT_Y0), (DOOR_X_IN, FRONT_Y0), (DOOR_X_IN, FRONT_Y1), (xl, FRONT_Y1)]
    s.poly([(x, y, 0) for x, y in dp], "PJUVIS")
    h = s.msp.add_hatch(color=8, dxfattribs={"layer": "PJUVIS"})
    h.set_pattern_fill("ANSI31", scale=0.25, angle=90)
    h.paths.add_polyline_path(dp, is_closed=True)
    s.line((xl, FRONT_Y0 - 6), (xl, FRONT_Y1 + 6), "MATOMOS")
    s.poly([(sx0 - 10, y_cut, 0), (sx0 + 3, y_cut + 5, 0), (sx1 - 3, y_cut - 5, 0), (sx1 + 10, y_cut, 0)],
           "MATOMOS", close=False)
    # adapteris + TIP-ON + stūmoklis + plokštelė
    s.rect(sx0 - 2, FRONT_Y0 - 2 - TIPON_LEN - 6, sx0, FRONT_Y0 - 8, "FURNITURA")
    s.rect(sx0 - 2 - TIPON_W, FRONT_Y0 - 2 - TIPON_LEN, sx0 - 2, FRONT_Y0 - 6, "FURNITURA")
    s.rect(TIPON_X - 5, FRONT_Y0 - 6, TIPON_X + 5, FRONT_Y0, "FURNITURA")
    s.rect(TIPON_X - 12, FRONT_Y0 - 1.5, TIPON_X + 12, FRONT_Y0, "FURNITURA")
    s.line((TIPON_X, FRONT_Y0 - TIPON_LEN - 20), (TIPON_X, FRONT_Y1 + 12), "ASYS")

    s.hdim(sx0, sx1, y_cut, y_cut - r)
    s.hdim(TIPON_X, DOOR_X_IN, FRONT_Y1, FRONT_Y1 + r)
    s.hdim(DOOR_X_IN, sx1, FRONT_Y1, FRONT_Y1 + r)
    s.hdim(sx0 - 2 - TIPON_W, sx0, FRONT_Y0 - 2 - TIPON_LEN, FRONT_Y0 - TIPON_LEN - 2 - r)
    s.vdim(FRONT_Y0 - 2 - TIPON_LEN, FRONT_Y0, xl, xl - r)
    s.vdim(FRONT_Y0, FRONT_Y1, xl, xl - r)

    s.arrow((DOOR_X_IN - 60, FRONT_Y1 + 45), (DOOR_X_IN - 60, FRONT_Y1 + 4))
    s.text("1. Paspausti (~2 mm)", (DOOR_X_IN - 54, FRONT_Y1 + 32))
    s.arrow((xl + 25, FRONT_Y1 + 4), (xl + 25, FRONT_Y1 + 45))
    s.text("2. Durelė atšoka", (xl + 31, FRONT_Y1 + 32))
    s.text("DARBUOTOJO PUSĖ", ((xl + xr) / 2, FRONT_Y1 + 75), align=CTR)
    s.text("spintelės vidus", (xl + 5, y_cut + 15))
    s.text("vieta kojoms", (sx1 + 10, y_cut + 15))

    X = xr + 2 * r
    label(s, (sx0 - 12, FRONT_Y0 - 45), (X, FRONT_Y0 - 30), "Blum TIP-ON durims (stūmoklis su magnetu)")
    label(s, (sx0 - 1, FRONT_Y0 - 70), (X, FRONT_Y0 - 60), "Adapterinė plokštelė, prisukama prie šono")
    label(s, (TIPON_X + 10, FRONT_Y0 - 0.8), (X, FRONT_Y0 + 5), "Metalinė atsitrenkimo plokštelė ant durelės")
    label(s, (DOOR_X_IN - 40, FRONT_Y0 + 9), (X, FRONT_Y1 + 22), "Durelė LMDP 18 mm")
    label(s, (sx0 + 9, y_cut + 40), (X, y_cut + 30), "Spintelės šonas LMDP 18 mm")
    s.title("MAZGAS. PJŪVIS A-A per TIP-ON (horizontalus, h = 787 mm)",
            "M 1:2   |   matmenys mm", (xl - 2 * r, y_cut - 2 * r - 12 * s.sc))
    return s.save("04_Mazgas_TIP-ON_pjuvis_A-A_M1-2")


# 5. MAZGAS: durelės vidinė pusė (M 1:10) ===================================
def detail_door():
    s = Sheet(10)
    r = ROW * s.sc
    DW, DH = door_width(), door_height()
    bx, by = 0.0, 0.0
    s.rect(bx, by, bx + DW, by + DH)
    cx = bx + CUP_C + CUP_D / 2
    for hz in (DH - HINGE_FROM_EDGE, HINGE_FROM_EDGE):
        s.circle((cx, by + hz), CUP_D / 2, "FURNITURA")
        s.rect(cx + CUP_D / 2, by + hz - 9, cx + CUP_D / 2 + 25, by + hz + 9, "FURNITURA")
        s.line((cx - 30, by + hz), (cx + 30, by + hz), "ASYS")
        s.line((cx, by + hz - 30), (cx, by + hz + 30), "ASYS")
    tz = by + DH - TIPON_FROM_TOP
    tx = bx + DW - (DOOR_X_IN - TIPON_X)
    s.rect(tx - 12, tz - 16, tx + 12, tz + 16, "FURNITURA")
    s.line((tx - 30, tz), (tx + 30, tz), "ASYS")
    s.line((tx, tz - 30), (tx, tz + 30), "ASYS")
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
    s.text("vyrių pusė", (bx + 15, by + DH / 2))
    s.text("atidarymo kraštas", (bx + DW - 15, by + DH / 2), align=RGT)

    notes = (
        "VEIKIMAS\\P"
        "1. Durelė be rankenos. Lengvai paspaudus jos kraštą (~2 mm), TIP-ON stūmoklis "
        "išstumia durelę, toliau ji atidaroma ranka.\\P"
        "2. Uždaroma pastumiant iki galo – magnetinis stūmoklis prilaiko durelę.\\P"
        "MONTAVIMAS\\P"
        "3. TIP-ON – spintelės viduje, ant šono prie vietos kojoms (per adapterinę plokštelę), "
        "70 mm nuo durelės viršaus, prie atidarymo krašto. Ant durelės – metalinė plokštelė.\\P"
        "4. Vyriai TIK be spyruoklės ir be BLUMOTION, kitaip durelė neatšoks.\\P"
        "5. Tarpai aplink durelę 1,5–3 mm; TIP-ON stūmoklio ilgis reguliuojamas.\\P"
        "FURNITŪRA\\P"
        "Blum TIP-ON durims – 1 vnt.; adapterinė plokštelė – 1; atsitrenkimo plokštelė – 1; "
        "vyris CLIP top 110° be spyruoklės – 2; montavimo plokštelė – 2; lentynos laikiklis Ø5 – 4; "
        "stalčių kreipiančiosios Blum MOVENTO 500 mm su BLUMOTION – 3 kompl.; stalčių rankenėlė 200 mm – 3; "
        "reguliuojama kojelė h=100 – 8; kabelių anga Ø60 – 2."
    )
    s.mtext(notes, (X, by + 380), width=95)
    s.title("MAZGAS. DURELĖS VIDINĖ PUSĖ – vyrių ir TIP-ON padėtis",
            "M 1:10   |   matmenys mm   |   spintelės durelė (darbuotojo dešinėje)",
            (bx - 2 * r, by - 15 * s.sc))
    return s.save("05_Mazgas_dureles_vyriai_TIP-ON_M1-10")


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
