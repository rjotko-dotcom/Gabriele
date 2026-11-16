"""Blender skriptas: sukuria kasos baldą, renderiuoja vaizdus ir eksportuoja 3D modelį.

Paleidimas:
  blender -b -P build_blender.py -- <out_dir> <tex_dir> [preview]
"""
import sys, os, math, json
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *  # noqa

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
TEX = argv[1]
PREVIEW = len(argv) > 2 and argv[2] == "preview"
S = 0.001  # mm -> m

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'


# ------------------------------------------------------------------ materials
def mat_principled(name, color, rough=0.5, sheen=0.0, tex=None, tex_scale=1.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if sheen:
        p.inputs["Sheen Weight"].default_value = sheen
        p.inputs["Sheen Roughness"].default_value = 0.4
        p.inputs["Sheen Tint"].default_value = (1, 0.85, 0.9, 1)
    if tex:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (tex_scale,) * 3
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(tex)
        im.projection = 'BOX'
        im.projection_blend = 0.3
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], im.inputs["Vector"])
        nt.links.new(im.outputs["Color"], p.inputs["Base Color"])
    return m


M_VELVET = mat_principled("Aksomas_rozinis", (0.62, 0.36, 0.40), rough=0.9, sheen=0.3,
                          tex=os.path.join(TEX, "velvet.jpg"), tex_scale=1.2)
M_FLUTE = mat_principled("Aksomas_vyno", (0.16, 0.035, 0.06), rough=0.8, sheen=0.25)
M_WOOD = mat_principled("Medis_azuolas", (0.45, 0.36, 0.28), rough=0.45,
                        tex=os.path.join(TEX, "wood.jpg"), tex_scale=0.6)
M_LMDP = mat_principled("LMDP_pudrinis", (0.42, 0.20, 0.23), rough=0.55)
M_CARCASS = mat_principled("LMDP_korpusas_baltas", (0.88, 0.86, 0.84), rough=0.6)
M_METAL = mat_principled("Metalas", (0.75, 0.75, 0.77), rough=0.25, metal=1.0)
M_TIPON = mat_principled("TIP-ON_pilkas", (0.55, 0.56, 0.58), rough=0.4)
M_BLACK = mat_principled("Kabeliu_anga", (0.05, 0.05, 0.05), rough=0.4)
M_PLINTH = mat_principled("Cokolis", (0.30, 0.18, 0.20), rough=0.7)

COLLECTION = bpy.data.collections.new("Kasos_baldas")
scene.collection.children.link(COLLECTION)


def link(obj):
    COLLECTION.objects.link(obj)
    return obj


def mesh_obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat)
    return link(ob)


def box(name, x0, x1, y0, y1, z0, z1, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = (x0 if v.co.x < 0 else x1) * S
        v.co.y = (y0 if v.co.y < 0 else y1) * S
        v.co.z = (z0 if v.co.z < 0 else z1) * S
    return mesh_obj(name, bm, mat)


def stadium_pts(L, D, seg=48):
    r = D / 2
    a = (L - D) / 2
    pts = []
    for i in range(seg + 1):
        t = -math.pi / 2 + math.pi * i / seg
        pts.append((a + r * math.cos(t), r * math.sin(t)))
    for i in range(seg + 1):
        t = math.pi / 2 + math.pi * i / seg
        pts.append((-a + r * math.cos(t), r * math.sin(t)))
    return pts


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


def boolean_cut(ob, cutter):
    mod = ob.modifiers.new("cut", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def smooth(ob, angle=35):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def cyl(name, x, y, z0, z1, r, mat, axis='Z', verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * S, depth=(z1 - z0) * S)
    ob = bpy.context.active_object
    ob.name = name
    if axis == 'Z':
        ob.location = (x * S, y * S, (z0 + z1) / 2 * S)
    elif axis == 'Y':
        ob.rotation_euler = (math.radians(90), 0, 0)
        ob.location = (x * S, (z0 + z1) / 2 * S, y * S)  # here y=z-centre, z0..z1 = y range
    for c in ob.users_collection:
        c.objects.unlink(ob)
    link(ob)
    ob.data.materials.append(mat)
    smooth(ob)
    return ob


# ------------------------------------------------------------------ geometry
# Korpusas (aksomas)
body = prism("Korpusas", stadium_pts(L_BODY, D_BODY), 0, H_BODY, M_VELVET)
cut = box("cut", -NICHE_HALF, NICHE_HALF, Y_INNER_FRONT, Y_BACK + 50, -5, H_BODY + 5, M_VELVET)
boolean_cut(body, cut)
smooth(body)

# Viršutinis stalviršis su išpjova darbuotojo pusėje
top = prism("Stalvirsis_virsutinis", stadium_pts(L_TOP, D_TOP), H_BODY, H_TOTAL, M_WOOD)
cut = box("cut", -NICHE_HALF, NICHE_HALF, NOTCH_Y0, D_TOP, H_BODY - 5, H_TOTAL + 5, M_WOOD)
boolean_cut(top, cut)
smooth(top)

# Rievėta panelė priekyje
flutes = []
for i in range(FLUTE_N):
    x = -FLUTE_HALF + FLUTE_R + i * 2 * FLUTE_R
    flutes.append(cyl(f"Rieve_{i}", x, Y_FRONT, FLUTE_Z0, H_BODY, FLUTE_R * 0.98, M_FLUTE, verts=20))
bpy.ops.object.select_all(action='DESELECT')
for f in flutes:
    f.select_set(True)
bpy.context.view_layer.objects.active = flutes[0]
bpy.ops.object.join()
flutes[0].name = "Rievėta_panele"

# Darbo stalviršis (900 mm)
work = box("Stalvirsis_darbo_900", -NICHE_HALF, NICHE_HALF, Y_INNER_FRONT, WORK_Y1,
           WORK_TOP_Z - T_WORK, WORK_TOP_Z, M_WOOD)

# Kabelių angos
for i, (x, y) in enumerate(GROMMETS_WORK):
    cyl(f"Anga_darbo_{i}", x, y, WORK_TOP_Z - 0.5, WORK_TOP_Z + 1.5, GROMMET_D / 2, M_BLACK)
for i, (x, y) in enumerate(GROMMETS_LEDGE):
    cyl(f"Anga_atramos_{i}", x, y, H_TOTAL - 0.5, H_TOTAL + 1.5, GROMMET_D / 2, M_BLACK)

# Spintelės korpusas
for sgn in (-1, 1):
    x0, x1 = sorted((sgn * SIDE_X0, sgn * NICHE_HALF))
    box(f"Sonas_{sgn}", x0, x1, Y_INNER_FRONT, DOOR_Y0, 0, TOPRAIL_Z1, M_LMDP)
box("Dugnas", -SIDE_X0, SIDE_X0, Y_INNER_FRONT, DOOR_Y0, BOTTOM_Z0, BOTTOM_Z1, M_CARCASS)
box("Virsutine_pertvara", -SIDE_X0, SIDE_X0, Y_INNER_FRONT, DOOR_Y0, TOPRAIL_Z0, TOPRAIL_Z1, M_CARCASS)
box("Vidurine_pertvara", -T / 2, T / 2, Y_INNER_FRONT, DOOR_Y0, BOTTOM_Z1, TOPRAIL_Z0, M_CARCASS)
box("Galine_sienele", -SIDE_X0, SIDE_X0, Y_INNER_FRONT - 0.1, Y_INNER_FRONT + 0.5,
    BOTTOM_Z1, TOPRAIL_Z0, M_CARCASS)
for sgn in (-1, 1):
    x0, x1 = sorted((sgn * (T / 2 + 1), sgn * (SIDE_X0 - 1)))
    box(f"Lentyna_{sgn}", x0, x1, Y_INNER_FRONT + SHELF_BACK_GAP,
        Y_INNER_FRONT + SHELF_BACK_GAP + SHELF_DEPTH, SHELF_Z0, SHELF_Z0 + T, M_CARCASS)

# Cokolis + kojelės
py1 = DOOR_Y1 - PLINTH_SETBACK
box("Cokolis", -SIDE_X0, SIDE_X0, py1 - T_PLINTH, py1, 2, LEG_H - 2, M_PLINTH)
for x in (-560, 0, 560):
    for y in (-250, py1 - T_PLINTH - 40):
        cyl("Kojele", x, y, 0, LEG_H, 15, M_METAL, verts=16)

# Durys + vyriai + TIP-ON
OPEN_LEFT_DEG = float(os.environ.get("OPEN_LEFT", "0"))
door_objs = {}
for sgn in (-1, 1):
    x0, x1 = sorted((sgn * DOOR_X_IN, sgn * DOOR_X_OUT))
    d = box(f"Durys_{'kaire' if sgn < 0 else 'desine'}", x0, x1, DOOR_Y0, DOOR_Y1,
            DOOR_Z0, DOOR_Z1, M_LMDP)
    door_objs[sgn] = d
    # TIP-ON atsitrenkimo plokštelė ant durų vidaus
    sx = sgn * (T / 2 + TIPON_W / 2)
    box(f"Plokstele_{sgn}", sx - 12, sx + 12, DOOR_Y0 - 1.5, DOOR_Y0, TIPON_Z - 16, TIPON_Z + 16, M_METAL)
    # Vyrių taurelės (ant durų) + petys/plokštelė ant šono
    for hz in (DOOR_Z1 - HINGE_FROM_EDGE, DOOR_Z0 + HINGE_FROM_EDGE):
        cx = sgn * (DOOR_X_OUT - CUP_C - CUP_D / 2)
        cup = cyl("Vyrio_taurele", cx, DOOR_Y0, DOOR_Y0 - 3, DOOR_Y0 + 0.5, CUP_D / 2, M_METAL)
        cup.rotation_euler = (math.radians(90), 0, 0)
        cup.location = (cx * S, (DOOR_Y0 - 1.25) * S, hz * S)
        ax0, ax1 = sorted((sgn * (SIDE_X0 - 14), sgn * SIDE_X0))
        box("Vyrio_petys", ax0, ax1, DOOR_Y0 - 95, DOOR_Y0 - 3, hz - 9, hz + 9, M_METAL)
        # parent cup to door for opening
        cup.parent = d
        cup.matrix_parent_inverse = d.matrix_world.inverted()

    # TIP-ON korpusas ant vidurinės pertvaros šono
    tx0, tx1 = sorted((sgn * T / 2, sgn * (T / 2 + TIPON_W)))
    box(f"TIP-ON_{sgn}", tx0, tx1, DOOR_Y0 - 2 - TIPON_LEN, DOOR_Y0 - 2,
        TIPON_Z - TIPON_H / 2, TIPON_Z + TIPON_H / 2, M_TIPON)
    tp = cyl(f"TIP-ON_stumoklis_{sgn}", sgn * (T / 2 + TIPON_W / 2), 0, 0, 1, 6, M_METAL, verts=16)
    tp.rotation_euler = (math.radians(90), 0, 0)
    tp.scale = (1, 1, 2 / 1)  # 2 mm ilgio
    tp.location = (sgn * (T / 2 + TIPON_W / 2) * S, (DOOR_Y0 - 1.5) * S, TIPON_Z * S)

# plokštelės prie durų
for sgn in (-1, 1):
    pl = bpy.data.objects[f"Plokstele_{sgn}"]
    pl.parent = door_objs[sgn]
    pl.matrix_parent_inverse = door_objs[sgn].matrix_world.inverted()


def open_door(sgn, deg):
    """Pasuka duris (su vyrių taurelėmis ir plokštele) apie vyrių ašį."""
    from mathutils import Matrix
    d = door_objs[sgn]
    pivot = Vector((sgn * DOOR_X_OUT * S, DOOR_Y1 * S, 0))
    M = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg) * (-sgn), 4, 'Z') \
        @ Matrix.Translation(-pivot)
    bpy.context.view_layer.update()
    objs = [d] + list(d.children)
    mws = {o: o.matrix_world.copy() for o in objs}
    for o in objs:
        o.parent = None
    for o in objs:
        o.matrix_world = M @ mws[o]


# ------------------------------------------------------------------ world / render
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (1, 1, 1, 1)
bg.inputs["Strength"].default_value = 0.35

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24 if PREVIEW else 96
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = 960 if PREVIEW else 1920
scene.render.resolution_y = 720 if PREVIEW else 1440
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'

# grindys – šešėlių gaudyklė
bpy.ops.mesh.primitive_plane_add(size=20)
floor = bpy.context.active_object
floor.is_shadow_catcher = True

# šviesos
bpy.ops.object.light_add(type='AREA', location=(-2.5, -3.0, 3.2))
key = bpy.context.active_object
key.data.energy = 700
key.data.size = 2.5
key.rotation_euler = (math.radians(50), 0, math.radians(-40))
bpy.ops.object.light_add(type='AREA', location=(3.0, 2.5, 2.8))
fill = bpy.context.active_object
fill.data.energy = 450
fill.data.size = 3
fill.rotation_euler = (math.radians(55), 0, math.radians(130))
bpy.ops.object.light_add(type='AREA', location=(0, 0, 3.5))
topl = bpy.context.active_object
topl.data.energy = 250
topl.data.size = 3

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
    co = world_to_camera_view(scene, cam, Vector([c * S for c in p_mm]))
    return (co.x * scene.render.resolution_x, (1 - co.y) * scene.render.resolution_y)


MODE = os.environ.get("MODE", "views")
if MODE == "views":
    render("01_kliento_puse_kaire", (-2.6, -3.3, 1.75), (0, 0, 0.55), 42)
    render("02_kliento_puse_desine", (2.9, -3.0, 1.45), (0, 0, 0.55), 42)
    render("03_darbuotojo_puse_kaire", (-2.4, 3.2, 1.9), (0, 0, 0.6), 42)
    render("04_darbuotojo_puse_tiesiai", (0.5, 3.6, 1.55), (0, 0, 0.62), 40)
elif MODE == "detail":
    open_door(-1, 100)
    scene.render.resolution_x = 1000 if PREVIEW else 1800
    scene.render.resolution_y = 1000 if PREVIEW else 1800
    loc = (-0.30, 1.30, 1.10)
    tgt = (-0.42, 0.22, 0.52)
    render("05_mazgas_TIP-ON", loc, tgt, 30)
    pts = {
        "tipon": project((-(T / 2 + TIPON_W / 2), DOOR_Y0 - 40, TIPON_Z + TIPON_H / 2)),
        "plate": None,
        "hinge_top": project((-(SIDE_X0 - 7), DOOR_Y0 - 50, DOOR_Z1 - HINGE_FROM_EDGE + 9)),
        "hinge_bot": project((-(SIDE_X0 - 7), DOOR_Y0 - 50, DOOR_Z0 + HINGE_FROM_EDGE + 9)),
        "shelf": project((-320, 200, SHELF_Z0 + T)),
        "partition": project((-T / 2, 150, 650)),
        "door_r": project((300, DOOR_Y1, 500)),
        "push_r": project((60, DOOR_Y1, TIPON_Z)),
    }
    pl = bpy.data.objects["Plokstele_-1"]
    bpy.context.view_layer.update()
    c = pl.matrix_world @ (sum((Vector(b) for b in pl.bound_box), Vector()) / 8)
    pts["plate"] = project(tuple(v / S for v in c))
    with open(os.path.join(OUT, "05_mazgas_points.json"), "w") as f:
        json.dump(pts, f)
elif MODE == "export":
    bpy.data.objects.remove(floor, do_unlink=True)
    for ob in list(scene.objects):
        if ob.type in ('LIGHT', 'CAMERA'):
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.wm.collada_export(filepath=os.path.join(OUT, "Kasos_baldas.dae"),
                              apply_modifiers=True, triangulate=False)
    bpy.ops.wm.obj_export(filepath=os.path.join(OUT, "Kasos_baldas.obj"),
                          export_materials=True, path_mode='COPY')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Kasos_baldas.blend"))
