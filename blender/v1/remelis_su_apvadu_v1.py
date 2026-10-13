"""
Rėmelis SU APVADU jau atspausdintai v1 dėžutei (liežuvėlis viršuje, "klik" apačioje).
Apvadas (3.5 mm aplink, 1.2 mm storio) užeina ant dėžutės priekio ir uždengia
nelygią vietą virš kišenės bei nušlifuotus kišenės kraštus. Dėžutės perspausdinti nereikia.

  python blender/v1/remelis_su_apvadu_v1.py      ->  stl/v1_remelis_su_apvadu.stl
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("v1", os.path.join(HERE, "raktu_deze_v1.py"))
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)

import bpy  # noqa: E402

BEZEL = 3.5        # kiek apvadas užeina ant dėžutės priekio iš kiekvienos pusės
BEZEL_T = 1.2      # apvado storis (kiek išsikiša virš dėžutės paviršiaus)
BEZEL_CH = 0.3     # apvado išorinės briaunos nuožula (vos vos)
BEZEL_R = 1.5      # apvado kampų spindulys – toks pat kaip langelio
WIN_CH = 0.3       # langelio briaunos nuožula


def build():
    coll = bpy.data.collections.get("Apvadas") or bpy.data.collections.new("Apvadas")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    ob = v1.label_base("V1_remelis_su_apvadu", coll)
    bw = v1.LABEL_W + 2 * BEZEL
    bh = v1.LABEL_H + 2 * BEZEL
    r = BEZEL_R
    T = v1.FRAME_T
    rings = []
    for z, ins in ((T, 0.0), (T + BEZEL_T - BEZEL_CH, 0.0), (T + BEZEL_T, BEZEL_CH)):
        rings.append([(x, y, z) for x, y in v1.rrect(bw - 2 * ins, bh - 2 * ins, r - ins)])
    bez = v1.new_obj("bezel", v1.loft("bezel", rings), coll)
    v1.boolean(ob, [bez], "UNION")
    c = WIN_CH
    zt = T + BEZEL_T
    win = v1.new_obj("cut_win", v1.loft("cut_win", [
        [(x, y, z) for x, y in v1.rrect(v1.WINDOW_W + 2 * ins, v1.WINDOW_H + 2 * ins, 1.5 + ins)]
        for z, ins in ((-1, 0), (zt - c, 0), (zt, c), (zt + 1, c))]), coll)
    v1.boolean(ob, [win])
    return ob


if __name__ == "__main__":
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    ob = build()
    out = os.path.join(HERE, "..", "..", "stl", "v1_remelis_su_apvadu.stl")
    # spausdinama VEIDU ŽEMYN (apvadas ant pagrindo), kad apvadas nekabėtų ore
    import math
    from mathutils import Matrix
    v1.write_stl(os.path.abspath(out), [ob], Matrix.Rotation(math.radians(180), 4, "X"))
