"""Plokščių kontūrų geometrija (shapely) -> geometry.json. Naudoja Blender ir DXF skriptai.

  python3 geom.py
"""
import json, math, os
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from params import *  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))


def stadium(L, D, seg=96):
    r, a = D / 2, (L - D) / 2
    pts = [(a + r * math.cos(-math.pi / 2 + math.pi * i / seg), r * math.sin(-math.pi / 2 + math.pi * i / seg))
           for i in range(seg + 1)]
    pts += [(-a + r * math.cos(math.pi / 2 + math.pi * i / seg), r * math.sin(math.pi / 2 + math.pi * i / seg))
            for i in range(seg + 1)]
    return Polygon(pts)


def rounded_rect(x0, y0, x1, y1, r, res=24):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, resolution=res)


Q = 24
top_st = stadium(L_TOP, D_TOP)
# išpjova: apačios kampai R250, viršus toli už stalviršio
cut = rounded_rect(-CUT_HALF, CUT_Y0, CUT_HALF, D_TOP + 2 * CUT_R, CUT_R, Q)
top = top_st.difference(cut)
# suapvalinti išorinius (įėjimo) kampus
top = top.buffer(-CUT_FILLET, resolution=Q).buffer(CUT_FILLET, resolution=Q)

body = stadium(L_BODY, D_BODY)
niche = rounded_rect(-CAV_HALF, CUT_Y0 + WALL_SETBACK, CAV_HALF, D_TOP + 2 * CUT_R, CUT_R + WALL_SETBACK, Q) \
    .buffer(0)
niche = niche.intersection(box(-CAV_HALF, -1000, CAV_HALF, 1000))
work = rounded_rect(-CAV_HALF, Y_INNER_FRONT - 2 * WORK_CORNER_R, CAV_HALF, WORK_Y1, WORK_CORNER_R, Q)
work = work.intersection(box(-CAV_HALF, Y_INNER_FRONT, CAV_HALF, WORK_Y1))
flute_niche = rounded_rect(-FLUTE_HALF - 5, Y_FRONT - 50, FLUTE_HALF + 5, Y_FRONT + FLUTE_NICHE_DEPTH,
                           FLUTE_NICHE_R, Q)
niche_in = niche.intersection(box(-CAV_HALF, -1000, CAV_HALF, Y_BACK))
inner = unary_union([niche_in.buffer(-8, resolution=Q), box(-CAV_HALF + 8, 200, CAV_HALF - 8, Y_BACK + 10)])
niche_shell = niche_in.difference(inner)
led = top.buffer(-15, resolution=Q).difference(top.buffer(-25, resolution=Q))
base = stadium(L_BODY - 2 * BASE_SETBACK, D_BODY - 2 * BASE_SETBACK)


def coords(p):
    if p.geom_type == "MultiPolygon":
        p = max(p.geoms, key=lambda g: g.area)
    return {"ext": [[round(x, 2), round(y, 2)] for x, y in p.exterior.coords[:-1]],
            "holes": [[[round(x, 2), round(y, 2)] for x, y in h.coords[:-1]] for h in p.interiors]}


data = {k: coords(v) for k, v in {
    "top": top, "body": body, "niche": niche, "work": work, "flute_niche": flute_niche,
    "led": led, "base": base, "niche_shell": niche_shell}.items()}
json.dump(data, open(os.path.join(HERE, "geometry.json"), "w"))
print("geometry.json OK", {k: len(v["ext"]) for k, v in data.items()},
      "top bounds", [round(b, 1) for b in top.bounds])
