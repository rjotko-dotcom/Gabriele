"""MARI MADE kasos baldas (v4): modelis, renderiai, eksportas.

  blender -b -P build_v4.py -- <out_dir> [preview]
  MODE=views | detail | export      PROPS=1 (daiktai, kėdė) | 0
"""
import sys, os, math, json
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import *  # noqa

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
PREVIEW = len(argv) > 1 and argv[1] == "preview"
MODE = os.environ.get("MODE", "views")
PROPS = os.environ.get("PROPS", "1") == "1"
S = 0.001
TEX = os.path.join(HERE, "tex")
GEO = json.load(open(os.path.join(HERE, "geometry.json")))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'


# ============================================================ MEDŽIAGOS
def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]


def _img(nt, fname, vec, noncolor=False):
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(os.path.join(TEX, fname), check_existing=True)
    if noncolor:
        im.image.colorspace_settings.name = 'Non-Color'
    im.projection = 'BOX'
    im.projection_blend = 0.2
    nt.links.new(vec, im.inputs["Vector"])
    return im


def mat_tex(name, color_f, scale, rough_f=None, normal_f=None, height_f=None, rough_mul=1.0,
            coat=0.0, val=1.0, export_color=(0.6, 0.6, 0.6)):
    m, nt, p = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    v = mp.outputs["Vector"]
    col = _img(nt, color_f, v)
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Value"].default_value = val
    nt.links.new(col.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], p.inputs["Base Color"])
    if rough_f:
        rg = _img(nt, rough_f, v, True)
        mr = nt.nodes.new("ShaderNodeMath")
        mr.operation = 'MULTIPLY'
        mr.inputs[1].default_value = rough_mul
        nt.links.new(rg.outputs["Color"], mr.inputs[0])
        nt.links.new(mr.outputs[0], p.inputs["Roughness"])
    if normal_f:
        nm = _img(nt, normal_f, v, True)
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = 0.6
        nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], p.inputs["Normal"])
    if height_f:
        hm = _img(nt, height_f, v, True)
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25
        bump.inputs["Distance"].default_value = 0.0005
        nt.links.new(hm.outputs["Color"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Coat Weight"].default_value = coat
    m["export_tex"] = os.path.join(TEX, color_f)
    m.diffuse_color = (*export_color, 1)
    return m


def mat(name, color, rough=0.4, metal=0.0, coat=0.0, emit=0.0, alpha=1.0, trans=0.0):
    m, nt, p = _new(name)
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emit
    if trans:
        p.inputs["Transmission Weight"].default_value = trans
    m.diffuse_color = (*color, 1)
    return m


M_STONE = mat_tex("Akmuo_kreminis", "akmuo_Color.jpg", 1.2, "akmuo_Roughness.jpg", "akmuo_NormalGL.jpg",
                  rough_mul=0.7, coat=0.2, val=1.05, export_color=(0.78, 0.72, 0.63))
M_PINK = mat_tex("Rozinis_mikrotekstura", "rozinis_BaseColor.jpg", 1.2, "rozinis_Roughness.jpg",
                 height_f="rozinis_Height.jpg", export_color=(0.40, 0.14, 0.17))
BURG = (0.05, 0.005, 0.011)
M_BURG = mat("Bordo_matinis_laminatas", BURG, rough=0.42)
M_FLUTE = mat("Bordo_rieves", (0.045, 0.004, 0.009), rough=0.5)
M_BRASS = mat("Zalvaris", (0.62, 0.38, 0.15), rough=0.28, metal=1.0)
M_LED = mat("LED_juosta", (1.0, 0.72, 0.42), rough=0.5, emit=25.0)
M_BLACK = mat("Juodas_plastikas", (0.02, 0.02, 0.022), rough=0.35)
M_GREY = mat("Pilkas_plastikas", (0.10, 0.10, 0.11), rough=0.4)
M_METAL = mat("Plienas", (0.78, 0.78, 0.80), rough=0.25, metal=1.0)
M_TIPON = mat("TIP-ON_pilkas", (0.45, 0.46, 0.48), rough=0.4)
M_WHITE = mat("Balta", (0.85, 0.84, 0.82), rough=0.5)
M_PAPER_B = mat("Popierius_bordo", (0.08, 0.009, 0.017), rough=0.5, coat=0.3)
M_PAPER_P = mat("Popierius_rozinis", (0.80, 0.50, 0.50), rough=0.7)
M_PAPER_C = mat("Popierius_kreminis", (0.80, 0.70, 0.58), rough=0.7)
M_SCREEN = mat("Ekranas", (0.18, 0.015, 0.03), rough=0.2, emit=1.0)
M_SCREEN2 = mat("Ekranas_terminalo", (0.10, 0.25, 0.45), rough=0.2, emit=1.5)
M_GLASS = mat("Stiklas_gintarinis", (0.45, 0.25, 0.08), rough=0.05, trans=0.8)
M_VASE = mat("Vaza_bordo", (0.09, 0.008, 0.018), rough=0.08, coat=1.0)
M_FLOWER1 = mat("Gele_rozine", (0.55, 0.10, 0.18), rough=0.7)
M_FLOWER2 = mat("Gele_bordo", (0.18, 0.01, 0.03), rough=0.7)
M_STEM = mat("Gelės_kotas", (0.06, 0.12, 0.03), rough=0.6)
M_LEAF = mat("Gelės_lapas", (0.05, 0.14, 0.04), rough=0.5)
M_LAMPSH = mat("Lempos_vidus", (1.0, 0.85, 0.6), rough=0.5, emit=6.0)
M_FABRIC = mat_tex("Kedes_audinys", "rozinis_BaseColor.jpg", 4.0, height_f="rozinis_Height.jpg",
                   val=1.1, export_color=(0.45, 0.22, 0.22))

COLL = bpy.data.collections.new("Baldas")
scene.collection.children.link(COLL)
PCOLL = bpy.data.collections.new("Rekvizitas_ir_kede")
scene.collection.children.link(PCOLL)
CUR = [COLL]


def link(ob):
    CUR[0].objects.link(ob)
    return ob


# ============================================================ GEOMETRIJOS PAGALBA
def mesh_obj(name, bm, m):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(m)
    return link(ob)


def bevel(ob, w=1.0, seg=2, angle=40):
    mod = ob.modifiers.new("Bevel", 'BEVEL')
    mod.width = w * S
    mod.segments = seg
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(angle)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, m, bev=1.0):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = ((x0 if v.co.x < 0 else x1) - cx) * S
        v.co.y = ((y0 if v.co.y < 0 else y1) - cy) * S
        v.co.z = ((z0 if v.co.z < 0 else z1) - cz) * S
    ob = mesh_obj(name, bm, m)
    ob.location = (cx * S, cy * S, cz * S)
    if bev:
        bevel(ob, bev, 2)
    return ob


def cbox(name, cx, cy, cz, sx, sy, sz, m, bev=1.0):
    return box(name, cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2, m, bev)


def prism(name, pts, z0, z1, m):
    bm = bmesh.new()
    vs = [bm.verts.new((x * S, y * S, z0 * S)) for x, y in pts]
    f = bm.faces.new(vs)
    if f.normal.z > 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=(0, 0, (z1 - z0) * S))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m)


def apply_mod(ob, mod):
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def cut(ob, cutter):
    mod = ob.modifiers.new("cut", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_mod(ob, mod)
    bpy.data.objects.remove(cutter, do_unlink=True)


def smooth(ob, angle=35):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def _adopt(ob, name, m):
    ob.name = name
    for c in ob.users_collection:
        c.objects.unlink(ob)
    link(ob)
    if m:
        ob.data.materials.append(m)
    return ob


def cyl(name, x, y, z0, z1, r, m, verts=32, axis='Z', r2=None):
    depth = (z1 - z0) * S
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * S, depth=depth)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r * S, radius2=r2 * S, depth=depth)
    ob = _adopt(bpy.context.active_object, name, m)
    c = (z0 + z1) / 2 * S
    if axis == 'Z':
        ob.location = (x * S, y * S, c)
    elif axis == 'X':      # x,y -> (y, z) koordinatės; z0..z1 – išilgai X
        ob.rotation_euler = (0, math.radians(90), 0)
        ob.location = (c, x * S, y * S)
    elif axis == 'Y':      # x,y -> (x, z); z0..z1 – išilgai Y
        ob.rotation_euler = (math.radians(90), 0, 0)
        ob.location = (x * S, c, y * S)
    smooth(ob)
    return ob


def sphere(name, x, y, z, r, m, sx=1, sy=1, sz=1, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r * S,
                                         location=(x * S, y * S, z * S))
    ob = _adopt(bpy.context.active_object, name, m)
    ob.scale = (sx, sy, sz)
    smooth(ob)
    return ob


def text(name, s, x, y, z, h, m, spacing=1.25, depth=3.0):
    font = bpy.data.fonts.load("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", check_existing=True)
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = s
    cu.font = font
    cu.size = h * S * 1.38
    cu.space_character = spacing
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.extrude = depth / 2 * S
    ob = bpy.data.objects.new(name, cu)
    link(ob)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = (x * S, y * S, z * S)
    ob.data.materials.append(m)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return bpy.context.active_object


def g(key, ring="ext"):
    return GEO[key][ring]


# ============================================================ BALDAS
body = prism("Korpusas", g("body"), BASE_H, H_BODY, M_PINK)
cut(body, box("c", -CAV_HALF, CAV_HALF, Y_INNER_FRONT, Y_BACK + 60, BASE_H - 5, WORK_TOP_Z, M_PINK, 0))
cut(body, prism("c", g("niche"), WORK_TOP_Z - 1, H_BODY + 5, M_PINK))
cut(body, prism("c", g("flute_niche"), BASE_H - 5, H_BODY + 5, M_PINK))
smooth(body)
# nišos apdaila – bordo (8 mm sluoksnis ant lenktos sienelės)
shell = prism("Nisos_apdaila_bordo", g("niche_shell"), WORK_TOP_Z, H_BODY, M_BURG)
smooth(shell)

top = prism("Stalvirsis_akmuo", g("top"), H_BODY, H_TOTAL, M_STONE)
bevel(top, 8, 4, 30)
smooth(top)

led = prism("LED_po_stalvirsiu", g("led"), H_BODY - 3, H_BODY - 0.2, M_LED)
cut(led, prism("c", g("led", "holes")[0] if GEO["led"]["holes"] else [], H_BODY - 10, H_BODY + 10, M_LED)) \
    if GEO["led"]["holes"] else None

base = prism("Cokolis_zalvaris", g("base"), 0, BASE_H, M_BRASS)
cut(base, box("c", -CAV_HALF, CAV_HALF, Y_INNER_FRONT, Y_BACK + 60, -5, BASE_H + 5, M_BRASS, 0))
smooth(base)

work = prism("Stalvirsis_darbo_900", g("work"), WORK_TOP_Z - T_WORK, WORK_TOP_Z, M_STONE)
bevel(work, 3, 3, 30)
for i, (x, y) in enumerate(GROMMETS_WORK):
    cyl(f"Kabeliu_anga_{i}", x, y, WORK_TOP_Z - 0.5, WORK_TOP_Z + 1.5, GROMMET_D / 2, M_BRASS)

# rievės + logotipas
fy = Y_FRONT + FLUTE_NICHE_DEPTH
fl = []
for i in range(FLUTE_N):
    x = -FLUTE_HALF + FLUTE_R + i * 2 * FLUTE_R
    fl.append(cyl(f"Rieve_{i}", x, fy, BASE_H, H_BODY, FLUTE_R * 0.97, M_FLUTE, verts=20))
bpy.ops.object.select_all(action='DESELECT')
for f in fl:
    f.select_set(True)
bpy.context.view_layer.objects.active = fl[0]
bpy.ops.object.join()
fl[0].name = "Rieves"
logo_y = fy - FLUTE_R - 6
text("Logotipas_MARI", "MARI", 0, logo_y, LOGO_Z, LOGO_H1, M_BRASS, spacing=1.3, depth=6)
text("Logotipas_MADE", "MADE", 0, logo_y, LOGO_Z - LOGO_H1 * 0.5 - 70, LOGO_H2, M_BRASS, spacing=1.6, depth=6)


# ---- korpusai po darbo stalviršiu
def carcass(name, x0, x1, inner_parts=True):
    box(f"{name}_sonas_a", x0, x0 + T, CARC_Y0, FRONT_Y1 if not inner_parts else FRONT_Y0, CARC_Z0, TOPRAIL_Z1, M_BURG)
    box(f"{name}_sonas_b", x1 - T, x1, CARC_Y0, FRONT_Y1 if not inner_parts else FRONT_Y0, CARC_Z0, TOPRAIL_Z1, M_BURG)
    box(f"{name}_dugnas", x0 + T, x1 - T, CARC_Y0, FRONT_Y0 if inner_parts else FRONT_Y1, CARC_Z0, CARC_Z0 + T, M_BURG)
    box(f"{name}_virsus", x0 + T, x1 - T, CARC_Y0, FRONT_Y0 if inner_parts else FRONT_Y1,
        TOPRAIL_Z1 - T, TOPRAIL_Z1, M_BURG)
    box(f"{name}_galas", x0 + T, x1 - T, CARC_Y0, CARC_Y0 + 8, CARC_Z0 + T, TOPRAIL_Z1 - T, M_BURG, 0)
    box(f"{name}_cokolis", x0, x1, CARC_Y0, FRONT_Y1 - BASE_SETBACK, 0, PLINTH_H, M_BRASS)


carcass("Stalciu_blokas", PED_X0, PED_X1)
for i, (z0, z1) in enumerate(drawer_fronts()):
    n = i + 1
    box(f"Stalcius_{n}_fasadas", PED_X0 + 1.5, PED_X1 - 1.5, FRONT_Y0, FRONT_Y1, z0, z1, M_BURG)
    hz = z1 - HANDLE_FROM_TOP
    cx = (PED_X0 + PED_X1) / 2
    h = cyl(f"Stalcius_{n}_rankenele", 0, 0, 0, HANDLE_W, HANDLE_D / 2, M_BRASS, 16)
    h.rotation_euler = (0, math.radians(90), 0)
    h.location = (cx * S, (FRONT_Y1 + HANDLE_PROJ) * S, hz * S)
    for dx in (-HANDLE_W / 2 + 15, HANDLE_W / 2 - 15):
        st = cyl(f"Stalcius_{n}_atrama", 0, 0, 0, HANDLE_PROJ, 4, M_BRASS, 12)
        st.rotation_euler = (math.radians(90), 0, 0)
        st.location = ((cx + dx) * S, (FRONT_Y1 + HANDLE_PROJ / 2) * S, hz * S)
    # dėžė
    bx0, bx1 = PED_X0 + T + 6, PED_X1 - T - 6
    by0, by1 = FRONT_Y0 - DRAWER_LEN, FRONT_Y0
    bz0, bz1 = z0 + 12, z1 - 25
    for nm, a in (("sonas_a", (bx0, bx0 + 12, by0, by1)), ("sonas_b", (bx1 - 12, bx1, by0, by1)),
                  ("galas", (bx0 + 12, bx1 - 12, by0, by0 + 12))):
        box(f"Stalcius_{n}_{nm}", *a, bz0, bz1, M_BURG, 0)
    box(f"Stalcius_{n}_dugnas", bx0 + 12, bx1 - 12, by0 + 12, by1, bz0, bz0 + 8, M_BURG, 0)
# spynelė viršutiniame stalčiuje
zt0, zt1 = drawer_fronts()[-1]
lk = cyl("Stalcius_5_spynele", 0, 0, 0, 6, LOCK_D / 2, M_BRASS, 24)
lk.rotation_euler = (math.radians(90), 0, 0)
lk.location = ((PED_X0 + PED_X1) / 2 * S, (FRONT_Y1 + 3) * S, (zt1 - 18) * S)

# vieta kojoms – galinė panelė
box("Koju_panele", KNEE_X0, KNEE_X1, KNEE_PANEL_Y1 - T, KNEE_PANEL_Y1, 0, TOPRAIL_Z1, M_BURG)

# dešinysis blokas
box("Bloko_sonas_isorinis", BLK_X0, BLK_X0 + T, CARC_Y0, FRONT_Y1, CARC_Z0, TOPRAIL_Z1, M_BURG)
box("Bloko_pertvara", MID_X0, MID_X1, CARC_Y0, FRONT_Y1, CARC_Z0, TOPRAIL_Z1, M_BURG)
box("Bloko_sonas_prie_koju", BLK_X1 - T, BLK_X1, CARC_Y0, FRONT_Y1, CARC_Z0, TOPRAIL_Z1, M_BURG)
box("Bloko_dugnas", BLK_X0 + T, BLK_X1 - T, CARC_Y0, FRONT_Y1, CARC_Z0, CARC_Z0 + T, M_BURG)
box("Bloko_virsus", BLK_X0 + T, BLK_X1 - T, CARC_Y0, FRONT_Y1, TOPRAIL_Z1 - T, TOPRAIL_Z1, M_BURG)
box("Bloko_galas", BLK_X0 + T, BLK_X1 - T, CARC_Y0, CARC_Y0 + 8, CARC_Z0 + T, TOPRAIL_Z1 - T, M_BURG, 0)
box("Bloko_cokolis", BLK_X0, BLK_X1, CARC_Y0, FRONT_Y1 - BASE_SETBACK, 0, PLINTH_H, M_BRASS)
box("Kasos_nisos_lentyna", MID_X1, BLK_X1 - T, CARC_Y0, FRONT_Y1, CUBBY_SHELF_Z0, CUBBY_SHELF_Z0 + T, M_BURG)
box("Lentyna_uz_dureles", MID_X1 + 1, BLK_X1 - T - 1, CARC_Y0 + SHELF_BACK_GAP,
    CARC_Y0 + SHELF_BACK_GAP + SHELF_DEPTH, SHELF_Z0, SHELF_Z0 + T, M_BURG)
for i, z in enumerate(R2_SHELVES):
    box(f"Atvira_lentyna_{i + 1}", BLK_X0 + T, MID_X0, CARC_Y0, FRONT_Y1, z, z + T, M_BURG)

# durelė + vyriai + TIP-ON + spynelė
door = box("Dureles", DOOR_X_OUT, DOOR_X_IN, FRONT_Y0, FRONT_Y1, DOOR_Z0, DOOR_Z1, M_BURG)
door_parts = [door]
plate = box("TIP-ON_plokstele", TIPON_X - 12, TIPON_X + 12, FRONT_Y0 - 1.5, FRONT_Y0, TIPON_Z - 16,
            TIPON_Z + 16, M_METAL, 0)
door_parts.append(plate)
dl = cyl("Dureliu_spynele", 0, 0, 0, 6, LOCK_D / 2, M_BRASS, 24)
dl.rotation_euler = (math.radians(90), 0, 0)
dl.location = ((DOOR_X_IN - LOCK_FROM_EDGE) * S, (FRONT_Y1 + 3) * S, (DOOR_Z1 - LOCK_FROM_TOP) * S)
door_parts.append(dl)
for hz in (DOOR_Z1 - HINGE_FROM_EDGE, DOOR_Z0 + HINGE_FROM_EDGE):
    cx = DOOR_X_OUT + CUP_C + CUP_D / 2
    cp = cyl("Vyrio_taurele", 0, 0, 0, 3, CUP_D / 2, M_METAL, 24)
    cp.rotation_euler = (math.radians(90), 0, 0)
    cp.location = (cx * S, (FRONT_Y0 - 1.5) * S, hz * S)
    door_parts.append(cp)
    box("Vyrio_petys", MID_X1, MID_X1 + 14, FRONT_Y0 - 95, FRONT_Y0 - 3, hz - 9, hz + 9, M_METAL, 0)
tx1 = BLK_X1 - T
box("TIP-ON_adapteris", tx1 - 2, tx1, FRONT_Y0 - 2 - TIPON_LEN - 6, FRONT_Y0 - 8,
    TIPON_Z - TIPON_H / 2 - 6, TIPON_Z + TIPON_H / 2 + 6, M_METAL, 0)
tip = box("TIP-ON_korpusas", tx1 - 2 - TIPON_W, tx1 - 2, FRONT_Y0 - 2 - TIPON_LEN, FRONT_Y0 - 6,
          TIPON_Z - TIPON_H / 2, TIPON_Z + TIPON_H / 2, M_TIPON, 1.0)
box("TIP-ON_stumoklis", TIPON_X - 5, TIPON_X + 5, FRONT_Y0 - 6, FRONT_Y0 - 0.2, TIPON_Z - 5, TIPON_Z + 5,
    M_METAL, 0.5)

# LED nišoje (po atramos kraštu) jau yra LED žiede; papildomai – po darbo stalviršio kraštu
box("LED_po_darbo_stalvirsiu", KNEE_X0, KNEE_X1, WORK_Y1 - 30, WORK_Y1 - 20, WORK_TOP_Z - T_WORK - 3,
    WORK_TOP_Z - T_WORK - 0.5, M_LED, 0)


# ============================================================ DAIKTAI IR KĖDĖ
def props():
    CUR[0] = PCOLL
    W = WORK_TOP_Z
    TT = H_TOTAL
    # monitorius
    mx, my = 120, 70
    # ekranas žiūri į darbuotoją (+Y); stovas – UŽ ekrano
    cbox("Monitorius_pagrindas", mx, my - 15, W + 5, 230, 180, 10, M_BLACK, 2)
    cbox("Monitorius_kojele", mx, my - 25, W + 150, 50, 22, 280, M_BLACK, 2)
    cbox("Monitorius_laikiklis", mx, my - 5, W + 300, 90, 18, 90, M_BLACK, 2)
    cbox("Monitorius_korpusas", mx, my + 15, W + 330, 540, 22, 320, M_BLACK, 3)
    cbox("Monitorius_ekranas", mx, my + 26.5, W + 335, 520, 1, 290, M_SCREEN, 0)
    t = text("Ekrano_logotipas", "MARI", mx, my + 28, W + 345, 32, M_BRASS, 1.3, 0.6)
    t.rotation_euler = (math.radians(90), 0, math.radians(180))
    t2 = text("Ekrano_logotipas_2", "MADE", mx, my + 28, W + 310, 12, M_BRASS, 1.6, 0.6)
    t2.rotation_euler = (math.radians(90), 0, math.radians(180))
    # kilimėlis, klaviatūra, pelė
    cbox("Kilimelis", 40, 230, W + 1.5, 620, 280, 3, M_PAPER_B, 1)
    cbox("Klaviatura", 100, 225, W + 12, 440, 135, 18, M_GREY, 3)
    cbox("Klaviatura_klavisai", 100, 225, W + 21.5, 420, 115, 2, M_BLACK, 0)
    sphere("Pele", -170, 235, W + 15, 32, M_BLACK, 1.0, 1.8, 0.55)
    # čekių spausdintuvas (kairėje nuo monitoriaus)
    cbox("Ceku_spausdintuvas", 390, 60, W + 70, 145, 195, 140, M_BLACK, 8)
    cbox("Ceku_popierius", 390, 140, W + 140, 80, 20, 4, M_WHITE, 0)
    # skeneris ant stovo
    cyl("Skenerio_stovas", -230, 60, W, W + 15, 45, M_BLACK)
    sc = cbox("Skeneris_rankena", -230, 60, W + 95, 38, 48, 150, M_BLACK, 8)
    sc.rotation_euler = (math.radians(-15), 0, 0)
    cbox("Skeneris_galva", -230, 85, W + 185, 70, 95, 55, M_BLACK, 10)
    # kortelių terminalas
    cbox("Terminalo_stovas", -380, 50, W + 20, 70, 70, 40, M_BLACK, 4)
    term = cbox("Korteliu_terminalas", -380, 60, W + 105, 80, 35, 165, M_GREY, 6)
    term.rotation_euler = (math.radians(-20), 0, 0)
    sc2 = cbox("Terminalo_ekranas", -380, 78, W + 140, 60, 2, 55, M_SCREEN2, 0)
    sc2.rotation_euler = (math.radians(-20), 0, 0)
    # antras spausdintuvas (etikečių)
    cbox("Etikeciu_spausdintuvas", -540, 60, W + 55, 125, 175, 110, M_BLACK, 8)
    # difuzorius
    cyl("Difuzorius_buteliukas", -660, 120, W, W + 90, 32, M_GLASS)
    for k in range(7):
        st = cyl(f"Difuzorius_lazdele_{k}", 0, 0, 0, 260, 1.5, M_PAPER_C, 6)
        a = k * 2 * math.pi / 7
        st.location = ((-660 + 8 * math.cos(a)) * S, (120 + 8 * math.sin(a)) * S, (W + 190) * S)
        st.rotation_euler = (math.radians(10 * math.sin(a)), math.radians(10 * math.cos(a)), 0)
    # dėžučių kalnelis
    cbox("Dezute_1", -860, 60, W + 45, 280, 200, 90, M_PAPER_B, 3)
    cbox("Dezute_2", -860, 60, W + 135, 240, 170, 90, M_PAPER_B, 3)
    cbox("Dezute_3", -860, 230, W + 40, 220, 120, 80, M_PAPER_B, 3)
    # pakavimo popieriaus laikiklis
    cbox("Popieriaus_laikiklio_pagrindas", 760, 60, W + 8, 420, 150, 16, M_BRASS, 3)
    for i, (yy, zz) in enumerate(((20, W + 70), (110, W + 160))):
        for xx in (560, 960):
            cyl(f"Laikiklio_stovas_{i}_{xx}", xx, yy, W + 16, zz, 6, M_BRASS, 12)
        cyl(f"Popieriaus_ritinys_{i}", yy, zz, 560, 960, 40, M_PAPER_P, 32, 'X')
    cyl("Pieštukine", 590, 220, W, W + 100, 38, M_PAPER_B)
    for k in range(4):
        st = cyl(f"Pieštukas_{k}", 590 + 12 * math.cos(k * 1.6), 220 + 12 * math.sin(k * 1.6), W + 60,
                 W + 200, 3.5, M_BRASS, 8)
        st.rotation_euler = (math.radians(6 * math.sin(k)), math.radians(6 * math.cos(k)), 0)
    # ant atramos: maišelis, lempa, vaza su gėlėmis, dėžutė
    def bag(name, x, y, z, w, d, h, rot=0, tissue=False):
        b = cbox(name, x, y, z + h / 2, w, d, h, M_PAPER_B, 2)
        b.rotation_euler = (0, 0, math.radians(rot))
        for s in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_radius=w * 0.22 * S, minor_radius=2.5 * S,
                                             major_segments=32, minor_segments=8)
            hd = _adopt(bpy.context.active_object, f"{name}_rankena", M_BRASS)
            hd.rotation_euler = (math.radians(90), 0, math.radians(rot))
            hd.location = (x * S, (y + s * d * 0.25) * S, (z + h) * S)
        t = text(f"{name}_logo", "MARI", x, y - d / 2 - 1, z + h * 0.55, h * 0.09, M_BRASS, 1.3, 0.5)
        t.rotation_euler = (math.radians(90), 0, math.radians(rot))
        if tissue:
            for k in range(5):
                c = cyl(f"{name}_popierius_{k}", x + (k - 2) * w * 0.12, y, z + h - 20, z + h + 90, 40,
                        M_PAPER_P, 4, r2=2)
                c.rotation_euler = (math.radians(15 * (k % 2 - 0.5)), math.radians(12 * (k - 2)), 0)
    bag("Maisas_ant_atramos", 820, -230, TT, 280, 120, 320, 0, tissue=True)
    # lempa
    cyl("Lempa_pagrindas", -760, -230, TT, TT + 18, 70, M_BRASS)
    cyl("Lempa_kojele", -760, -230, TT + 18, TT + 300, 12, M_BRASS, 16)
    sh = sphere("Lempa_gaubtas", -760, -230, TT + 290, 140, M_BRASS, 1, 1, 0.6)
    cutter = cbox("c", -760, -230, TT + 200, 400, 400, 180, M_BRASS, 0)
    mod = sh.modifiers.new("cut", 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cutter
    apply_mod(sh, mod); bpy.data.objects.remove(cutter, do_unlink=True)
    cyl("Lempa_sviesa", -760, -230, TT + 288, TT + 291, 125, M_LAMPSH)
    bpy.ops.object.light_add(type='POINT', location=(-0.76, -0.23, (TT + 250) * S))
    lt = _adopt(bpy.context.active_object, "Lempos_sviesa", None)
    lt.data.energy = 15
    lt.data.color = (1, 0.8, 0.55)
    # vaza su hortenzijomis
    sphere("Vaza", -1060, -200, TT + 150, 130, M_VASE, 1, 1, 1.25)
    cyl("Vazos_kaklelis", -1060, -200, TT + 290, TT + 330, 60, M_VASE)
    import random
    random.seed(4)
    vx, vy, vz = -1060, -200, TT + 330          # vazos kaklelio viršus
    cz = TT + 500                                # žiedų „debesies“ centras
    # kotai iš vazos į žiedynus
    heads = []
    for k in range(9):
        a = k * 2 * math.pi / 9 + random.uniform(-0.2, 0.2)
        rr = random.uniform(60, 150)
        heads.append((vx + rr * math.cos(a), vy + rr * math.sin(a) * 0.8, cz + random.uniform(-40, 60)))
    for k, (hx, hy, hz) in enumerate(heads):
        x0, y0 = vx + (hx - vx) * 0.15, vy + (hy - vy) * 0.15
        dx, dy, dz = hx - x0, hy - y0, hz - 60 - (vz - 120)
        L = math.sqrt(dx * dx + dy * dy + dz * dz)
        st = cyl(f"Gelės_kotas_{k}", 0, 0, 0, L, 5, M_STEM, 8)
        st.location = ((x0 + dx / 2) * S, (y0 + dy / 2) * S, (vz - 120 + dz / 2) * S)
        st.rotation_euler = Vector((dx, dy, dz)).to_track_quat('Z', 'Y').to_euler()
    # lapai prie kotų
    for k in range(8):
        a = k * 2 * math.pi / 8
        lf = sphere(f"Gelės_lapas_{k}", vx + 90 * math.cos(a), vy + 90 * math.sin(a), vz + 70, 55, M_LEAF,
                    1.0, 0.45, 0.12, 12)
        lf.rotation_euler = (math.radians(25 * math.sin(a)), math.radians(-25 * math.cos(a)), a)
    # hortenzijų žiedynai – žiedų kekės ant kotų viršūnių
    n = 0
    for (hx, hy, hz) in heads:
        for j in range(9):
            a, b = random.uniform(0, 2 * math.pi), random.uniform(0, 1.6)
            r = 75
            sphere(f"Ziedas_{n}", hx + r * math.sin(b) * math.cos(a), hy + r * math.sin(b) * math.sin(a),
                   hz + r * 0.8 * math.cos(b), random.uniform(32, 48),
                   M_FLOWER1 if n % 3 else M_FLOWER2, seg=12)
            n += 1
    cbox("Dezute_ant_atramos", -560, -250, TT + 35, 210, 120, 70, M_PAPER_B, 3)
    # kasos stalčius nišelėje
    cx = (MID_X1 + BLK_X1 - T) / 2
    cbox("Kasos_pinigu_staliukas", cx, 120, CUBBY_SHELF_Z0 + T + 55, 410, 420, 110, M_BLACK, 4)
    kl = cyl("Kasos_spynele", 0, 0, 0, 4, 9, M_BRASS, 16)
    kl.rotation_euler = (math.radians(90), 0, 0)
    kl.location = (cx * S, 332 * S, (CUBBY_SHELF_Z0 + T + 75) * S)
    # atviros lentynos: maišai ir dėžutės
    x2 = (BLK_X0 + T + MID_X0) / 2
    bag("Maisas_lentynoje_1", x2 - 100, 150, R2_SHELVES[0] + T, 190, 100, 230, 0)
    bag("Maisas_lentynoje_2", x2 + 100, 160, R2_SHELVES[0] + T, 190, 100, 230, 0)
    cbox("Dezute_apacioje_1", x2, 150, CARC_Z0 + T + 50, 330, 260, 100, M_PAPER_C, 3)
    cbox("Dezute_apacioje_2", x2 + 60, 150, CARC_Z0 + T + 130, 200, 200, 60, M_PAPER_B, 3)
    cbox("Dezute_virsuje_1", x2 - 90, 150, R2_SHELVES[1] + T + 40, 170, 160, 80, M_PAPER_B, 3)
    cbox("Dezute_virsuje_2", x2 + 95, 150, R2_SHELVES[1] + T + 40, 170, 160, 80, M_PAPER_B, 3)
    cbox("Dezute_virsuje_3", x2 + 95, 150, R2_SHELVES[1] + T + 115, 150, 140, 70, M_PAPER_B, 3)
    # kėdė (padidinto aukščio – 900 mm stalviršiui)
    kx, ky = 150, 760
    for k in range(5):
        a = math.radians(90 + k * 72)
        leg = cbox(f"Kede_koja_{k}", kx + 160 * math.cos(a), ky + 160 * math.sin(a), 75, 330, 40, 18, M_BRASS, 4)
        leg.rotation_euler = (0, 0, a)
        sphere(f"Kede_ratukas_{k}", kx + 320 * math.cos(a), ky + 320 * math.sin(a), 28, 28, M_BLACK, seg=12)
    cyl("Kede_stovas", kx, ky, 80, 560, 25, M_BRASS)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.008, major_segments=48)
    ring = _adopt(bpy.context.active_object, "Kede_koju_ziedas", M_BRASS)
    ring.location = (kx * S, ky * S, 0.40)
    for k in range(3):
        a = math.radians(90 + k * 120)
        sp = cbox(f"Kede_ziedo_laikiklis_{k}", kx + 110 * math.cos(a), ky + 110 * math.sin(a), 400, 220, 12, 12,
                  M_BRASS, 2)
        sp.rotation_euler = (0, 0, a)
    cbox("Kede_sedyne", kx, ky, 610, 500, 470, 90, M_FABRIC, 40)
    # apvalus „tub“ atlošas: storas lankas
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=48, radius=0.25)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.27, depth=0.34,
                                        location=(kx * S, (ky + 10) * S, 0.83))
    bk = _adopt(bpy.context.active_object, "Kede_atlosas", M_FABRIC)
    bm.free()
    cutter = cbox("c", kx, ky - 200, 830, 700, 420, 500, M_FABRIC, 0)
    inner = cyl("c2", kx, ky + 10, 600, 1100, 220, M_FABRIC, 48)
    for c in (cutter, inner):
        mod = bk.modifiers.new("cut", 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = c
        apply_mod(bk, mod)
        bpy.data.objects.remove(c, do_unlink=True)
    bevel(bk, 15, 3, 30)
    CUR[0] = COLL


if PROPS:
    props()

# ============================================================ SCENA
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (1, 1, 1, 1)
bg.inputs["Strength"].default_value = 0.35
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32 if PREVIEW else 128
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 960 if PREVIEW else 1920
scene.render.resolution_y = 600 if PREVIEW else 1200
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -0.7

bpy.ops.mesh.primitive_plane_add(size=40)
floor = bpy.context.active_object
floor.is_shadow_catcher = True


def area(loc, rot, energy, size):
    bpy.ops.object.light_add(type='AREA', location=loc)
    lt = bpy.context.active_object
    lt.data.energy = energy
    lt.data.size = size
    lt.rotation_euler = [math.radians(a) for a in rot]


area((-3.5, -3.5, 3.8), (45, 0, -45), 1500, 3.5)
area((4.0, 3.0, 3.2), (55, 0, 125), 800, 4.0)
area((0, 0.6, 4.2), (0, 0, 0), 700, 5.0)
area((3.0, -3.5, 2.2), (65, 0, 35), 400, 2.5)
area((-3.0, 3.5, 2.5), (60, 0, -140), 500, 3.0)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def render(name, loc, target, lens=40):
    cam.location = Vector(loc)
    look_at(cam, target)
    cam_data.lens = lens
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


def project(p_mm):
    bpy.context.view_layer.update()
    co = world_to_camera_view(scene, cam, Vector([c * S for c in p_mm]))
    return (co.x * scene.render.resolution_x, (1 - co.y) * scene.render.resolution_y)


def center(ob):
    bpy.context.view_layer.update()
    c = sum((ob.matrix_world @ Vector(v) for v in ob.bound_box), Vector()) / 8
    return tuple(x / S for x in c)


if MODE == "views":
    render("01_kliento_puse_kampu", (-3.4, -4.4, 1.9), (0, 0, 0.62), 40)
    render("02_kliento_puse_tiesiai", (0.0, -5.2, 1.35), (0, 0, 0.62), 42)
    render("03_darbuotojo_puse_kampu", (3.1, 4.4, 2.2), (0, 0.1, 0.7), 40)
    render("04_darbuotojo_puse_tiesiai", (0.0, 5.0, 1.75), (0, 0, 0.72), 40)
elif MODE == "detail":
    for o in list(PCOLL.objects):
        if o.name.startswith("Kede"):
            o.hide_render = True
    pivot = Vector((DOOR_X_OUT * S, FRONT_Y1 * S, 0))
    M = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(100), 4, 'Z') @ Matrix.Translation(-pivot)
    bpy.context.view_layer.update()
    for o in door_parts:
        o.matrix_world = M @ o.matrix_world
    scene.render.resolution_x = 1000 if PREVIEW else 1800
    scene.render.resolution_y = 1000 if PREVIEW else 1800
    render("05_mazgas_TIP-ON", (0.05, 1.55, 1.15), (-0.40, 0.25, 0.45), 30)
    c = center(tip)
    pts = {"tipon": project((c[0], c[1], c[2] + TIPON_H / 2)),
           "hinge_top": project((MID_X1 + 7, FRONT_Y0 - 50, DOOR_Z1 - HINGE_FROM_EDGE + 9)),
           "shelf": project((-420, 150, SHELF_Z0 + T)),
           "plate": project(center(plate))}
    json.dump(pts, open(os.path.join(OUT, "05_mazgas_points.json"), "w"))
elif MODE == "export":
    bpy.data.objects.remove(floor, do_unlink=True)
    for ob in list(scene.objects):
        if ob.type == 'LIGHT' and not ob.name.startswith("Lempos"):
            bpy.data.objects.remove(ob, do_unlink=True)
    cam.location = Vector((3.1, 4.4, 2.2))
    look_at(cam, (0, 0.1, 0.7))
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Kasos_baldas.blend"))
    print("SAVED_BLEND")
