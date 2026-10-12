"""
Raktų dėžutė (Nissan / Fakto Auto) – parametrinis Blender modelis 3D spausdinimui.

Paleidimas:
  * Blender GUI:  Scripting -> Open -> raktu_deze.py -> Run Script
                  (sukuria kolekciją "Raktu_deze"; senus jos objektus ištrina)
  * Komandinė eilutė (sugeneruoja .blend + STL):
      blender -b -P raktu_deze.py -- --out ../
    arba su pip paketu "bpy":  python raktu_deze.py --out ../

Visi matmenys milimetrais (1 Blender vienetas = 1 mm).
Ašys: X = ilgis (22 cm), Y = plotis (18 cm, priekis -Y pusėje), Z = aukštis.
"""

import math
import os
import struct
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# PARAMETRAI – keisk čia
# ---------------------------------------------------------------------------
LENGTH = 220.0          # dėžutės ilgis (X)
WIDTH = 180.0           # dėžutės plotis (Y)
HEIGHT = 70.0           # dėžutės aukštis (Z)
WALL = 5.0              # sienelės storis
FLOOR = 8.0             # dugno storis (storas – kad tilptų M3 įvoržės iš apačios)
R_OUT = 16.0            # išorinių kampų spindulys (vaizdas iš viršaus)
R_TOP_OUT = 2.0         # viršutinės išorinės briaunos apvalinimas
R_TOP_IN = 1.5          # viršutinės vidinės briaunos apvalinimas
R_FLOOR = 8.0           # vidinis dugno apvalinimas (lengva išsemti raktus)
BOTTOM_CHAMFER = 0.6    # apatinė nuožula (prieš "elephant foot")

# Priekinė įduba (scoop) – kaip nuotraukoje
SCOOP_BOTTOM_Z = 42.0   # žemiausias įdubos taškas
SCOOP_FLAT_HALF = 35.0  # pusė plokščios dalies pločio
SCOOP_HALF = 72.0       # pusė viso įdubos pločio
SCOOP_EDGE_R = 1.5      # įdubos briaunų apvalinimas

# Etiketės kišenė priekyje
LABEL_W = 100.0         # kišenės ilgis
LABEL_H = 26.0          # kišenės aukštis
LABEL_Z = 22.0          # kišenės centro aukštis
LABEL_DEPTH = 2.2       # kišenės gylis (rėmelis 1.6 + 0.6 popieriui/plėvelei)
LABEL_R = 3.0           # kišenės kampų spindulys
LABEL_CLEAR = 0.2       # tarpas tarp rėmelio ir kišenės (iš visų pusių)
FRAME_T = 1.6           # rėmelio / plokštelės storis
WINDOW_W = 88.0         # rėmelio langelio ilgis
WINDOW_H = 17.0         # rėmelio langelio aukštis
SNAP_R = 0.5            # spragtelėjimo griovelio spindulys kišenėje
SNAP_RIDGE_R = 0.4      # rėmelio iškilimo spindulys
SNAP_LEN = 56.0         # spragtelėjimo iškilimo ilgis

# Etiketės plokštelė su tekstu (variantas be popieriaus)
LABEL_NUMBER = "01"
LABEL_TEXT = "ATSARGINIAI RAKTAI"
TEXT_RAISE = 0.6        # teksto aukštis virš plokštelės (spalvos keitimui)

# M3 tvirtinimas iš apačios (į spintelės lentyną)
M3_HOLE_D = 4.0         # 4.0 = M3 įlydoma įvorė (heat-set); 2.6 = tiesiai įsukamas varžtas
M3_HOLE_DEPTH = 6.0     # gylis (dugnas 8 mm -> lieka 2 mm, iš vidaus nesimato)
M3_POSITIONS = [(sx * 80.0, sy * 60.0) for sx in (-1, 1) for sy in (-1, 1)]

# Dovetail (kregždės uodegos) jungtys šonuose – dėžutės jungiasi tarpusavyje
DT_SURFACE_W = 8.0      # griovelio plotis ties paviršiumi
DT_INNER_W = 11.0       # griovelio plotis gilumoje
DT_DEPTH = 2.4          # griovelio gylis sienelėje
DT_HEIGHT = 45.0        # griovelio aukštis nuo apačios (atviras apačioje)
DT_POSITIONS_Y = (-45.0, 45.0)
DT_CLEAR = 0.15         # tarpas jungčiai (vienai pusei)

SEG = 12                # segmentų skaičius kampo lankui
COLLECTION = "Raktu_deze"


# ---------------------------------------------------------------------------
# Geometrijos pagalbinės funkcijos
# ---------------------------------------------------------------------------
def rrect(l, w, r, n=SEG):
    """Suapvalinto stačiakampio kontūras (CCW), 2D taškai."""
    r = max(0.3, min(r, l / 2 - 0.01, w / 2 - 0.01))
    cx, cy = l / 2 - r, w / 2 - r
    pts = []
    for (ox, oy, a0) in ((cx, -cy, -90), (cx, cy, 0), (-cx, cy, 90), (-cx, -cy, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def circle(r, n=32):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def loft(name, rings):
    """Uždaras kūnas iš žiedų (vienodas taškų skaičius) + dangteliai galuose."""
    bm = bmesh.new()
    vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vrings[:-1], vrings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(vrings[0])))
    bm.faces.new(vrings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def prism_z(name, pts2d, z0, z1):
    return loft(name, [[(x, y, z0) for x, y in pts2d], [(x, y, z1) for x, y in pts2d]])


def rounded_box(name, l, w, r, profile):
    """profile = [(z, inset), ...] iš apačios į viršų."""
    rings = []
    for z, inset in profile:
        rings.append([(x, y, z) for x, y in rrect(l - 2 * inset, w - 2 * inset, r - inset)])
    return loft(name, rings)


def new_obj(name, me, coll):
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def boolean(target, cutters, op="DIFFERENCE"):
    """Pritaiko boolean operaciją su kiekvienu įrankiu ir ištrina įrankius."""
    for c in cutters:
        mod = target.modifiers.new("bool", "BOOLEAN")
        mod.operation = op
        mod.object = c
        try:
            mod.solver = "MANIFOLD"
        except TypeError:
            mod.solver = "EXACT"
        c.hide_viewport = True
        c.hide_render = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    old = target.data
    target.modifiers.clear()
    target.data = me
    bpy.data.meshes.remove(old)
    for c in cutters:
        m = c.data
        bpy.data.objects.remove(c)
        bpy.data.meshes.remove(m)


def material(name, rgb, rough=0.55):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    return mat


# ---------------------------------------------------------------------------
# Dalys
# ---------------------------------------------------------------------------
def build_tray(coll):
    # Išorė: apatinė nuožula + viršutinis apvalinimas
    prof = [(0.0, BOTTOM_CHAMFER), (BOTTOM_CHAMFER, 0.0), (HEIGHT - R_TOP_OUT, 0.0)]
    for i in range(1, SEG + 1):
        a = math.radians(90 * i / SEG)
        prof.append((HEIGHT - R_TOP_OUT + R_TOP_OUT * math.sin(a), R_TOP_OUT * (1 - math.cos(a))))
    tray = new_obj("Deze", rounded_box("Deze", LENGTH, WIDTH, R_OUT, prof), coll)

    # Vidus: dugno apvalinimas + viršutinės vidinės briaunos apvalinimas
    il, iw, ir = LENGTH - 2 * WALL, WIDTH - 2 * WALL, R_OUT - WALL
    prof = []
    for i in range(SEG + 1):
        a = math.radians(90 * i / SEG)
        prof.append((FLOOR + R_FLOOR * (1 - math.cos(a)), R_FLOOR * (1 - math.sin(a))))
    for i in range(SEG + 1):
        a = math.radians(90 * i / SEG)
        prof.append((HEIGHT - R_TOP_IN + R_TOP_IN * math.sin(a), -R_TOP_IN * (1 - math.cos(a))))
    prof.append((HEIGHT + 5, -R_TOP_IN))
    cutters = [new_obj("cut_inner", rounded_box("cut_inner", il, iw, ir, prof), coll)]

    # Priekinė įduba su suapvalintomis briaunomis
    cutters.append(new_obj("cut_scoop", scoop_cutter(), coll))

    # Etiketės kišenė + spragtelėjimo grioveliai + nago įpjova
    yf = -WIDTH / 2
    pocket = rrect(LABEL_W, LABEL_H, LABEL_R)
    cutters.append(new_obj("cut_label", loft("cut_label", [
        [(x, yf - 1, LABEL_Z + z) for x, z in pocket],
        [(x, yf + LABEL_DEPTH, LABEL_Z + z) for x, z in pocket]]), coll))
    ymid = yf + FRAME_T / 2
    for zs in (LABEL_Z + LABEL_H / 2, LABEL_Z - LABEL_H / 2):
        ring = [(ymid + y, zs + z) for y, z in circle(SNAP_R, 24)]
        cutters.append(new_obj("cut_snap", loft("cut_snap", [
            [(-SNAP_LEN / 2 - 2, y, z) for y, z in ring],
            [(SNAP_LEN / 2 + 2, y, z) for y, z in ring]]), coll))
    notch = [(LABEL_W / 2 + x, LABEL_Z + z) for x, z in circle(3.5, 32)]
    cutters.append(new_obj("cut_notch", loft("cut_notch", [
        [(x, yf - 1, z) for x, z in notch],
        [(x, yf + LABEL_DEPTH + 0.6, z) for x, z in notch]]), coll))

    # M3 skylės iš apačios (su 0.6 mm nuožula)
    rh = M3_HOLE_D / 2
    for px, py in M3_POSITIONS:
        rings = []
        for z, r in ((-1.0, rh + 1.6), (0.6, rh), (M3_HOLE_DEPTH, rh)):
            rings.append([(px + x, py + y, z) for x, y in circle(r, 32)])
        cutters.append(new_obj("cut_m3", loft("cut_m3", rings), coll))

    # Dovetail grioveliai abiejuose šonuose (atviri apačioje, iš vidaus nesimato)
    for side in (-1, 1):
        x0 = side * LENGTH / 2
        for py in DT_POSITIONS_Y:
            poly = [
                (x0 + side * 1.0, py - DT_SURFACE_W / 2 - 1.0 * 0.625),
                (x0 - side * DT_DEPTH, py - DT_INNER_W / 2),
                (x0 - side * DT_DEPTH, py + DT_INNER_W / 2),
                (x0 + side * 1.0, py + DT_SURFACE_W / 2 + 1.0 * 0.625),
            ]
            if side < 0:
                poly.reverse()
            cutters.append(new_obj("cut_dt", prism_z("cut_dt", poly, -1.0, DT_HEIGHT), coll))

    boolean(tray, cutters)
    return tray


def scoop_cutter():
    """Įdubos įrankis: profilis XZ plokštumoje, ištemptas per sienelę Y kryptimi.
    Ties sienelės paviršiais profilis išplečiamas -> briaunos suapvalinamos."""
    a, b, z0 = SCOOP_FLAT_HALF, SCOOP_HALF, SCOOP_BOTTOM_Z
    amp = (HEIGHT - z0) / 0.9
    ztop = HEIGHT + 15
    path = [(-b, ztop)]
    n = 90
    for i in range(n + 1):
        x = -b + 2 * b * i / n
        t = min(1.0, max(0.0, (abs(x) - a) / (b - a)))
        path.append((x, z0 + amp * (1 - math.cos(math.pi * t)) / 2))
    path.append((b, ztop))
    # normalės (į medžiagą) kiekviename taške
    normals = []
    for i, p in enumerate(path):
        segs = []
        if i > 0:
            segs.append((path[i - 1], p))
        if i < len(path) - 1:
            segs.append((p, path[i + 1]))
        if i in (0, len(path) - 1):
            segs = [segs[0]]
        nx = nz = 0.0
        for (x1, z1), (x2, z2) in segs:
            dx, dz = x2 - x1, z2 - z1
            ln = math.hypot(dx, dz)
            nx += dz / ln
            nz += -dx / ln
        ln = math.hypot(nx, nz)
        normals.append((nx / ln, nz / ln))

    rr = SCOOP_EDGE_R
    yo, yi = -WIDTH / 2, -WIDTH / 2 + WALL
    ys = [(yo - 3, rr)]
    for k in range(9):
        d = rr * (1 - k / 8)
        ys.append((yo + rr - d, rr - math.sqrt(max(0.0, rr * rr - d * d))))
    for k in range(9):
        d = rr * k / 8
        ys.append((yi - rr + d, rr - math.sqrt(max(0.0, rr * rr - d * d))))
    ys.append((yi + 3, rr))
    rings = []
    for y, off in ys:
        rings.append([(x + nx * off, y, z + nz * off) for (x, z), (nx, nz) in zip(path, normals)])
    return loft("cut_scoop", rings)


def label_base(name, coll):
    """Rėmelio / plokštelės pagrindas su spragtelėjimo iškilimais (vietinės koord.:
    priekinis paviršius viršuje z=FRAME_T, spausdinama gulint)."""
    fw, fh = LABEL_W - 2 * LABEL_CLEAR, LABEL_H - 2 * LABEL_CLEAR
    ob = new_obj(name, prism_z(name, rrect(fw, fh, LABEL_R - LABEL_CLEAR), 0.0, FRAME_T), coll)
    ridges = []
    for ys in (fh / 2, -fh / 2):
        ring = [(ys + y, FRAME_T / 2 + z) for y, z in circle(SNAP_RIDGE_R, 24)]
        ridges.append(new_obj("ridge", loft("ridge", [
            [(-SNAP_LEN / 2, y, z) for y, z in ring],
            [(SNAP_LEN / 2, y, z) for y, z in ring]]), coll))
    boolean(ob, ridges, "UNION")
    return ob


def build_frame(coll):
    ob = label_base("Etiketes_remelis", coll)
    win = new_obj("cut_win", prism_z("cut_win", rrect(WINDOW_W, WINDOW_H, 1.5), -1, FRAME_T + 1), coll)
    boolean(ob, [win])
    return ob


def make_text(body, size, x, coll, max_w=None):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = (TEXT_RAISE + 0.1) / 2
    tmp = bpy.data.objects.new("txt", cu)
    coll.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    xs = [v.co.x for v in me.vertices]
    w = max(xs) - min(xs)
    s = min(1.0, max_w / w) if max_w else 1.0
    me.transform(Matrix.Translation((x, 0, FRAME_T + TEXT_RAISE / 2 - 0.05)) @ Matrix.Scale(s, 4))
    return me


def build_plate(coll):
    plate = label_base("Etiketes_plokstele", coll)
    fw = LABEL_W - 2 * LABEL_CLEAR
    bm = bmesh.new()
    for me in (
        make_text(LABEL_NUMBER, 7.0, -fw / 2 + 9, coll),
        make_text(LABEL_TEXT, 6.5, 8.0, coll, max_w=fw - 26),
    ):
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    # skiriamasis brūkšnys
    bar = prism_z("bar", rrect(0.6, 14, 0.25, 2), FRAME_T - 0.05, FRAME_T + TEXT_RAISE)
    bar.transform(Matrix.Translation((-fw / 2 + 17, 0, 0)))
    bm.from_mesh(bar)
    bpy.data.meshes.remove(bar)
    me = bpy.data.meshes.new("Etiketes_tekstas")
    bm.to_mesh(me)
    bm.free()
    text = new_obj("Etiketes_tekstas", me, coll)
    return plate, text


def build_connector(coll):
    """Dvigubas dovetail ("peteliškė") – sujungia dvi gretimas dėžutes iš apačios."""
    d = DT_DEPTH - 0.2
    ws = (DT_SURFACE_W - 2 * DT_CLEAR) / 2
    wi = (DT_INNER_W - 2 * DT_CLEAR) / 2
    poly = [(-d, -wi), (0, -ws), (d, -wi), (d, wi), (0, ws), (-d, wi)]
    poly.reverse()
    ln = DT_HEIGHT - 1.0
    return new_obj("Jungtis", prism_z("Jungtis", poly, 0.0, ln), coll)


# ---------------------------------------------------------------------------
# Eksportas
# ---------------------------------------------------------------------------
def write_stl(path, objs, matrix=Matrix()):
    tris = []
    for ob in objs:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        for f in bm.faces:
            tris.append([matrix @ v.co for v in f.verts])
        bm.free()
    with open(path, "wb") as fh:
        fh.write(b"raktu_deze".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            n = (b - a).cross(c - a)
            n = n.normalized() if n.length > 0 else Vector((0, 0, 0))
            fh.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    print("STL:", path, len(tris), "trikampiai")


def main(out_dir=None):
    coll = bpy.data.collections.get(COLLECTION)
    if coll:
        for ob in list(coll.objects):
            bpy.data.objects.remove(ob)
    else:
        coll = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(coll)

    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"

    tray = build_tray(coll)
    frame = build_frame(coll)
    plate, text = build_plate(coll)
    conn = build_connector(coll)

    # Spausdinimo orientacijos (lokalios koordinatės) -> STL
    if out_dir:
        stl = os.path.join(out_dir, "stl")
        os.makedirs(stl, exist_ok=True)
        write_stl(os.path.join(stl, "deze_220x180x70.stl"), [tray])
        write_stl(os.path.join(stl, "etiketes_remelis.stl"), [frame])
        write_stl(os.path.join(stl, "etiketes_plokstele_su_tekstu.stl"), [plate, text])
        write_stl(os.path.join(stl, "etiketes_plokstele_be_teksto.stl"), [plate])
        write_stl(os.path.join(stl, "etiketes_tekstas_tik_spalva.stl"), [text])
        # jungtis spausdinama gulint ant plokščio šono
        write_stl(os.path.join(stl, "jungtis_dovetail.stl"), [conn],
                  Matrix.Rotation(math.radians(90), 4, "Y") @ Matrix.Translation((0, 0, 0)))

    # Scenos išdėstymas: rėmelis kišenėje, plokštelė ir jungtis šalia
    place = Matrix.Translation((0, -WIDTH / 2 + FRAME_T, LABEL_Z)) @ Matrix.Rotation(math.radians(90), 4, "X")
    frame.matrix_world = place
    plate.matrix_world = text.matrix_world = Matrix.Translation((0, -WIDTH / 2 - 40, 0)) @ place
    plate.hide_viewport = text.hide_viewport = False
    conn.location = (LENGTH / 2 + 30, -45, 0)

    m_box = material("Deze_juoda", (0.025, 0.025, 0.028), 0.45)
    m_lbl = material("Etikete_balta", (0.80, 0.80, 0.78), 0.4)
    m_txt = material("Tekstas_juodas", (0.02, 0.02, 0.02), 0.5)
    for ob, m in ((tray, m_box), (frame, m_lbl), (plate, m_lbl), (text, m_txt), (conn, m_box)):
        ob.data.materials.clear()
        ob.data.materials.append(m)
        for p in ob.data.polygons:
            p.use_smooth = False
    return dict(tray=tray, frame=frame, plate=plate, text=text, conn=conn)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = None
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
    elif bpy.data.filepath:
        out = os.path.dirname(bpy.data.filepath)
    main(out)
    if out and bpy.app.background:
        os.makedirs(os.path.join(out, "blender"), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "blender", "raktu_deze.blend"))
