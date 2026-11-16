"""Blender skriptas: sukuria kasos baldą, renderiuoja vaizdus ir eksportuoja 3D modelį.

Paleidimas:
  blender -b -P build_blender.py -- <out_dir> [preview]
  MODE=views|detail|export
"""
import sys, os, math, json
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *  # noqa

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
PREVIEW = len(argv) > 1 and argv[1] == "preview"
MODE = os.environ.get("MODE", "views")
S = 0.001  # mm -> m

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'


# ================================================================== MEDŽIAGOS
def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes["Principled BSDF"]


def _coord(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")


def _img(nt, fname, vec, noncolor=False):
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(os.path.join(TEX, fname), check_existing=True)
    if noncolor:
        im.image.colorspace_settings.name = 'Non-Color'
    im.projection = 'BOX'
    im.projection_blend = 0.15
    nt.links.new(vec, im.inputs["Vector"])
    return im


def mat_pbr(name, prefix, scale, rot_z=0.0, tint=None, sat=1.0, val=1.0, rough_mul=1.0,
            normal_strength=1.0, coat=0.0):
    """PBR medžiaga iš nuotraukinių tekstūrų (ambientCG, CC0)."""
    m, nt, p = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale,) * 3
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot_z))
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    v = mp.outputs["Vector"]
    col = _img(nt, prefix + "_Color.jpg", v)
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = sat
    hsv.inputs["Value"].default_value = val
    nt.links.new(col.outputs["Color"], hsv.inputs["Color"])
    out = hsv.outputs["Color"]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(out, mix.inputs[6])
        out = mix.outputs[2]
    nt.links.new(out, p.inputs["Base Color"])
    rg = _img(nt, prefix + "_Roughness.jpg", v, True)
    mr = nt.nodes.new("ShaderNodeMath")
    mr.operation = 'MULTIPLY'
    mr.inputs[1].default_value = rough_mul
    nt.links.new(rg.outputs["Color"], mr.inputs[0])
    nt.links.new(mr.outputs[0], p.inputs["Roughness"])
    nm = _img(nt, prefix + "_NormalGL.jpg", v, True)
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = normal_strength
    nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.3
    return m


def mat_oak(name, val=1.0):
    return mat_pbr(name, "medis", 1.4, rot_z=0, sat=1.0, val=val, rough_mul=0.85, coat=0.15)


def mat_plaster(name, color):
    return mat_pbr(name, "tinkas", 0.8, tint=tuple(c * 1.25 for c in color), rough_mul=1.0,
                   normal_strength=0.6)


def mat_plain(name, color, rough=0.4, metal=0.0, coat=0.0):
    m, nt, p = _new(name)
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    return m


ROSE = (0.50, 0.26, 0.25)
M_PLASTER = mat_plaster("Tinkas_pudrinis", ROSE)
M_FLUTE = mat_plain("Dazytas_MDF_rieves", (0.36, 0.15, 0.16), rough=0.5)
M_OAK = mat_oak("Azuolas_stalvirsis")
M_OAK_LIGHT = mat_oak("Azuolas_staliai", val=1.25)
M_LAM = mat_plain("Laminatas_matinis_pudrinis", (0.50, 0.27, 0.26), rough=0.38)
M_WHITE = mat_plain("Laminatas_baltas_vidus", (0.80, 0.78, 0.75), rough=0.45)
M_BRONZE = mat_plain("Bronza_cokolis", (0.48, 0.32, 0.18), rough=0.32, metal=1.0)
M_METAL = mat_plain("Plienas", (0.78, 0.78, 0.80), rough=0.25, metal=1.0)
M_TIPON = mat_plain("TIP-ON_pilkas", (0.45, 0.46, 0.48), rough=0.4)
M_BLACK = mat_plain("Kabeliu_anga", (0.03, 0.03, 0.03), rough=0.35)

COLL = bpy.data.collections.new("Kasos_baldas")
scene.collection.children.link(COLL)


# ================================================================== GEOMETRIJA
def link(ob):
    COLL.objects.link(ob)
    return ob


def mesh_obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat)
    return link(ob)


def bevel(ob, w=1.5, seg=3):
    mod = ob.modifiers.new("Bevel", 'BEVEL')
    mod.width = w * S
    mod.segments = seg
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(40)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat, bev=1.0):
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = (x0 if v.co.x < 0 else x1) * S
        v.co.y = (y0 if v.co.y < 0 else y1) * S
        v.co.z = (z0 if v.co.z < 0 else z1) * S
    ob = mesh_obj(name, bm, mat)
    if bev:
        bevel(ob, bev, 2)
    return ob


def stadium_pts(L, D, seg=64):
    r, a = D / 2, (L - D) / 2
    pts = []
    for i in range(seg + 1):
        t = -math.pi / 2 + math.pi * i / seg
        pts.append((a + r * math.cos(t), r * math.sin(t)))
    for i in range(seg + 1):
        t = math.pi / 2 + math.pi * i / seg
        pts.append((-a + r * math.cos(t), r * math.sin(t)))
    return pts


def circle_pts(cx, cy, r, seg=180):
    return [(cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg))
            for i in range(seg)]


def prism(name, pts, z0, z1, mat):
    bm = bmesh.new()
    vs = [bm.verts.new((x * S, y * S, z0 * S)) for x, y in pts]
    f = bm.faces.new(vs)
    if f.normal.z > 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=(0, 0, (z1 - z0) * S))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mat)


def apply_mod(ob, mod):
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def boolean_cut(ob, cutter):
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


def cyl(name, x, y, z0, z1, r, mat, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * S, depth=(z1 - z0) * S,
                                        location=(x * S, y * S, (z0 + z1) / 2 * S))
    ob = bpy.context.active_object
    ob.name = name
    for c in ob.users_collection:
        c.objects.unlink(ob)
    link(ob)
    ob.data.materials.append(mat)
    smooth(ob)
    return ob


# ---- Korpusas (tinkas)
body = prism("Korpusas_tinkuotas", stadium_pts(L_BODY, D_BODY), BASE_H, H_BODY, M_PLASTER)
boolean_cut(body, box("c", -CAV_HALF, CAV_HALF, CARC_Y0, Y_BACK + 50, -5, WORK_TOP_Z, M_PLASTER, 0))
boolean_cut(body, prism("c", circle_pts(0, ARC_CY, R_ARC_WALL), WORK_TOP_Z - 1, H_BODY + 5, M_PLASTER))
smooth(body)

# ---- Viršutinis stalviršis su lenkta išpjova
top = prism("Stalvirsis_virsutinis_azuolas", stadium_pts(L_TOP, D_TOP), H_BODY, H_TOTAL, M_OAK)
boolean_cut(top, prism("c", circle_pts(0, ARC_CY, R_ARC_TOP), H_BODY - 5, H_TOTAL + 5, M_OAK))
smooth(top)
bevel(top, 2.5, 3)

# ---- Rievėta panelė priekyje (dažytas MDF)
flutes = []
for i in range(FLUTE_N):
    x = -FLUTE_HALF + FLUTE_R + i * 2 * FLUTE_R
    flutes.append(cyl(f"Rieve_{i}", x, Y_FRONT, FLUTE_Z0, H_BODY, FLUTE_R * 0.97, M_FLUTE, verts=24))
bpy.ops.object.select_all(action='DESELECT')
for f in flutes:
    f.select_set(True)
bpy.context.view_layer.objects.active = flutes[0]
bpy.ops.object.join()
flutes[0].name = "Rieveta_panele"

# ---- Bronzinis cokolis apačioje aplink korpusą (įtrauktas 10 mm)
plinth = prism("Cokolis_bronza", stadium_pts(L_BODY - 20, D_BODY - 20), 0, BASE_H, M_BRONZE)
boolean_cut(plinth, box("c", -CAV_HALF + 10, CAV_HALF - 10, CARC_Y0, Y_BACK + 50, -5, 60, M_BRONZE, 0))
smooth(plinth)

# ---- Darbo stalviršis 900
work = box("Stalvirsis_darbo_900_azuolas", -CAV_HALF, CAV_HALF, CARC_Y0, WORK_Y1,
           WORK_TOP_Z - T_WORK, WORK_TOP_Z, M_OAK, bev=2.0)

for i, (x, y) in enumerate(GROMMETS_WORK):
    cyl(f"Anga_darbo_{i}", x, y, WORK_TOP_Z - 0.5, WORK_TOP_Z + 1.2, GROMMET_D / 2, M_BLACK)
for i, (x, y) in enumerate(GROMMETS_LEDGE):
    cyl(f"Anga_atramos_{i}", x, y, H_TOTAL - 0.5, H_TOTAL + 1.2, GROMMET_D / 2, M_BLACK)

# ---- Kojų vieta: galinė panelė + šonai (laminatas)
box("Koju_panele", PED_X0 - 0, CAB_X1, KNEE_PANEL_Y0, KNEE_PANEL_Y1, 0, TOPRAIL_Z1, M_LAM)


# ---- Korpusai (stalčių blokas ir spintelė)
def carcass(name, x0, x1):
    box(f"{name}_sonas_1", x0, x0 + T, CARC_Y0, FRONT_Y0, 0, TOPRAIL_Z1, M_LAM)
    box(f"{name}_sonas_2", x1 - T, x1, CARC_Y0, FRONT_Y0, 0, TOPRAIL_Z1, M_LAM)
    box(f"{name}_dugnas", x0 + T, x1 - T, CARC_Y0, FRONT_Y0, BOTTOM_Z0, BOTTOM_Z1, M_WHITE)
    box(f"{name}_virsus", x0 + T, x1 - T, CARC_Y0, FRONT_Y0, TOPRAIL_Z1 - T, TOPRAIL_Z1, M_WHITE)
    box(f"{name}_galas", x0 + T, x1 - T, CARC_Y0, CARC_Y0 + 3, BOTTOM_Z1, TOPRAIL_Z1 - T, M_WHITE, 0)
    py = FRONT_Y1 - PLINTH_SETBACK
    box(f"{name}_cokolis", x0 + T, x1 - T, py - T_PLINTH, py, 0, LEG_H - 2, M_BRONZE)


carcass("Stalciu_blokas", PED_X0, PED_X1)
carcass("Spintele", CAB_X0, CAB_X1)
box("Spinteles_lentyna", CAB_X0 + T + 1, CAB_X1 - T - 1, CARC_Y0 + SHELF_BACK_GAP,
    CARC_Y0 + SHELF_BACK_GAP + SHELF_DEPTH, SHELF_Z0, SHELF_Z0 + T, M_WHITE)

# ---- Stalčiai (fasadas + dėžė)
OPEN_DRAWER = float(os.environ.get("OPEN_DRAWER", "0"))
drawer_objs = []
for i, (z0, z1) in enumerate(drawer_fronts()):
    parts = []
    parts.append(box(f"Stalcius_{i + 1}_fasadas", PED_X0 + 1.5, PED_X1 - 1.5, FRONT_Y0, FRONT_Y1,
                     z0, z1, M_LAM))
    # įfrezuota rankenėlė viršuje (tamsus griovelis)
    parts.append(box(f"Stalcius_{i + 1}_griovelis", PED_X0 + 100, PED_X1 - 100, FRONT_Y1 - 0.5,
                     FRONT_Y1 + 0.3, z1 - 22, z1 - 12, M_BLACK, 0))
    bx0, bx1 = PED_X0 + T + 6, PED_X1 - T - 6
    by0, by1 = FRONT_Y0 - DRAWER_LEN, FRONT_Y0
    bz0, bz1 = z0 + 15, z1 - 30
    t = 12
    parts += [box(f"Stalcius_{i + 1}_sonas_a", bx0, bx0 + t, by0, by1, bz0, bz1, M_OAK_LIGHT, 0.6),
              box(f"Stalcius_{i + 1}_sonas_b", bx1 - t, bx1, by0, by1, bz0, bz1, M_OAK_LIGHT, 0.6),
              box(f"Stalcius_{i + 1}_galas", bx0 + t, bx1 - t, by0, by0 + t, bz0, bz1, M_OAK_LIGHT, 0.6),
              box(f"Stalcius_{i + 1}_dugnas", bx0 + t, bx1 - t, by0 + t, by1, bz0, bz0 + 8, M_OAK_LIGHT, 0)]
    if i == 2:  # viršutinis – su skyreliais
        parts.append(box("Stalcius_3_pertvara", (bx0 + bx1) / 2 - 4, (bx0 + bx1) / 2 + 4,
                         by0 + t, by1, bz0, bz1 - 15, M_OAK_LIGHT, 0.5))
        parts.append(box("Stalcius_3_pertvara_2", bx0 + t, bx1 - t, by0 + 220, by0 + 228,
                         bz0, bz1 - 15, M_OAK_LIGHT, 0.5))
    drawer_objs.append(parts)
if OPEN_DRAWER:
    for ob in drawer_objs[2]:
        ob.location.y += OPEN_DRAWER * S

# ---- Spintelės durelė + vyriai + TIP-ON
door = box("Spinteles_durys", DOOR_X_OUT, DOOR_X_IN, FRONT_Y0, FRONT_Y1, FRONT_Z0, FRONT_Z1, M_LAM)
door_parts = [door]
plate = box("TIP-ON_plokstele", TIPON_X - 12, TIPON_X + 12, FRONT_Y0 - 1.5, FRONT_Y0,
            TIPON_Z - 16, TIPON_Z + 16, M_METAL, 0)
door_parts.append(plate)
for hz in (FRONT_Z1 - HINGE_FROM_EDGE, FRONT_Z0 + HINGE_FROM_EDGE):
    cx = DOOR_X_OUT + CUP_C + CUP_D / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=CUP_D / 2 * S, depth=3 * S,
                                        location=(cx * S, (FRONT_Y0 - 1.5) * S, hz * S),
                                        rotation=(math.radians(90), 0, 0))
    cup = bpy.context.active_object
    cup.name = "Vyrio_taurele"
    cup.data.materials.append(M_METAL)
    door_parts.append(cup)
    box("Vyrio_petys", CAB_X0 + T, CAB_X0 + T + 14, FRONT_Y0 - 95, FRONT_Y0 - 3, hz - 9, hz + 9, M_METAL, 0)
tx1 = CAB_X1 - T
box("TIP-ON_adapteris", tx1 - 2, tx1, FRONT_Y0 - 2 - TIPON_LEN - 6, FRONT_Y0 - 8,
    TIPON_Z - TIPON_H / 2 - 6, TIPON_Z + TIPON_H / 2 + 6, M_METAL, 0)
box("TIP-ON_korpusas", tx1 - 2 - TIPON_W, tx1 - 2, FRONT_Y0 - 2 - TIPON_LEN, FRONT_Y0 - 6,
    TIPON_Z - TIPON_H / 2, TIPON_Z + TIPON_H / 2, M_TIPON, 1.0)
box("TIP-ON_stumoklis", TIPON_X - 5, TIPON_X + 5, FRONT_Y0 - 6, FRONT_Y0 - 0.2,
    TIPON_Z - 5, TIPON_Z + 5, M_METAL, 0.5)

# kojelės
for x in (PED_X0 + 60, PED_X1 - 60, CAB_X0 + 60, CAB_X1 - 60):
    for y in (CARC_Y0 + 60, FRONT_Y1 - PLINTH_SETBACK - T_PLINTH - 40):
        cyl("Kojele", x, y, 0, LEG_H, 14, M_METAL, verts=16)


def open_door(deg):
    pivot = Vector((DOOR_X_OUT * S, FRONT_Y1 * S, 0))
    M = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, 'Z') @ Matrix.Translation(-pivot)
    bpy.context.view_layer.update()
    for o in door_parts:
        o.matrix_world = M @ o.matrix_world


# ================================================================== SCENA
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (1, 1, 1, 1)
bg.inputs["Strength"].default_value = 0.4

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32 if PREVIEW else 128
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 960 if PREVIEW else 1920
scene.render.resolution_y = 720 if PREVIEW else 1440
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -0.8

bpy.ops.mesh.primitive_plane_add(size=30)
floor = bpy.context.active_object
floor.is_shadow_catcher = True


def area(loc, rot, energy, size):
    bpy.ops.object.light_add(type='AREA', location=loc)
    lt = bpy.context.active_object
    lt.data.energy = energy
    lt.data.size = size
    lt.rotation_euler = [math.radians(a) for a in rot]
    return lt


area((-3.0, -3.0, 3.5), (45, 0, -45), 1200, 3.0)    # pagrindinė
area((3.5, 2.5, 3.0), (55, 0, 125), 600, 3.5)       # užpildanti
area((0, 0.5, 4.0), (0, 0, 0), 500, 4.0)            # viršutinė
area((2.5, -3.0, 2.0), (65, 0, 35), 300, 2.0)       # kontūrinė

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def render(name, loc, target, lens=45):
    cam.location = Vector(loc)
    look_at(cam, target)
    cam_data.lens = lens
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


def project(p_mm):
    bpy.context.view_layer.update()
    co = world_to_camera_view(scene, cam, Vector([c * S for c in p_mm]))
    return (co.x * scene.render.resolution_x, (1 - co.y) * scene.render.resolution_y)


if MODE == "views":
    render("01_kliento_puse_kaire", (-2.7, -3.3, 1.7), (0, 0, 0.55), 42)
    render("02_kliento_puse_desine", (2.9, -3.0, 1.45), (0, 0, 0.55), 42)
    render("04_darbuotojo_puse_tiesiai", (0.35, 3.7, 1.6), (0, 0, 0.6), 40)
    for ob in drawer_objs[2]:
        ob.location.y += 260 * S
    render("03_darbuotojo_puse_kaire", (2.3, 3.1, 1.9), (0, 0.1, 0.58), 40)
elif MODE == "detail":
    open_door(100)
    scene.render.resolution_x = 1000 if PREVIEW else 1800
    scene.render.resolution_y = 1000 if PREVIEW else 1800
    render("05_mazgas_TIP-ON", (-0.10, 1.35, 1.15), (-0.40, 0.20, 0.55), 30)
    pts = {
        "tipon": project((TIPON_X, FRONT_Y0 - 40, TIPON_Z + TIPON_H / 2)),
        "hinge_top": project((CAB_X0 + T + 7, FRONT_Y0 - 50, FRONT_Z1 - HINGE_FROM_EDGE + 9)),
        "shelf": project((-480, 150, SHELF_Z0 + T)),
    }
    bpy.context.view_layer.update()
    c = plate.matrix_world @ (sum((Vector(v) for v in plate.bound_box), Vector()) / 8)
    pts["plate"] = project(tuple(x / S for x in c))
    with open(os.path.join(OUT, "05_mazgas_points.json"), "w") as f:
        json.dump(pts, f)
elif MODE == "export":
    bpy.data.objects.remove(floor, do_unlink=True)
    for ob in list(scene.objects):
        if ob.type == 'LIGHT':
            bpy.data.objects.remove(ob, do_unlink=True)
    cam.location = Vector((0.35, 3.7, 1.6))
    look_at(cam, (0, 0, 0.6))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Kasos_baldas.blend"))
    # eksportams – su pritaikytais modifikatoriais
    bpy.ops.wm.collada_export(filepath=os.path.join(OUT, "Kasos_baldas.dae"),
                              apply_modifiers=True, triangulate=False, selected=False)
    bpy.ops.wm.obj_export(filepath=os.path.join(OUT, "Kasos_baldas.obj"),
                          export_materials=True, apply_modifiers=True)
