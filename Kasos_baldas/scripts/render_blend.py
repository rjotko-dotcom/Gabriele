"""Renderiuoja vaizdus tiesiai iš .blend modelio (pagrindinis modelis – 3D_modelis/Kasos_baldas.blend).

  blender -b 3D_modelis/Kasos_baldas.blend -P scripts/render_blend.py -- <out_dir> [preview]
  MODE=views|detail
"""
import os, sys, math, json
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import CAB_X0, FRONT_Y1, TIPON_Z, TIPON_H, FRONT_Y0, T, FRONT_Z1, HINGE_FROM_EDGE, SHELF_Z0  # noqa

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
PREVIEW = len(argv) > 1 and argv[1] == "preview"
MODE = os.environ.get("MODE", "views")
S = 0.001
scene = bpy.context.scene

# senos šviesos / kameros lauk
for ob in list(scene.objects):
    if ob.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(ob, do_unlink=True)


def split_handles():
    """Rankenėlių objektą išskaido į atskiras dalis (kad stalčių būtų galima atidaryti)."""
    ob = bpy.data.objects.get("Stalcius_1_griovelis")
    if not ob:
        return {}
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    parts = {}
    for o in bpy.context.selected_objects:
        zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
        parts[o.name] = sum(zs) / len(zs)
    return parts


handles = split_handles()
top_handle = max(handles, key=handles.get) if handles else None

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
scene.render.resolution_percentage = 100
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


area((-3.0, -3.0, 3.5), (45, 0, -45), 1200, 3.0)
area((3.5, 2.5, 3.0), (55, 0, 125), 600, 3.5)
area((0, 0.5, 4.0), (0, 0, 0), 500, 4.0)
area((2.5, -3.0, 2.0), (65, 0, 35), 300, 2.0)

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


def center(ob):
    bpy.context.view_layer.update()
    c = sum((ob.matrix_world @ Vector(v) for v in ob.bound_box), Vector()) / 8
    return tuple(x / S for x in c)


if MODE == "views":
    render("01_kliento_puse_kaire", (-2.7, -3.3, 1.7), (0, 0, 0.55), 42)
    render("02_kliento_puse_desine", (2.9, -3.0, 1.45), (0, 0, 0.55), 42)
    render("04_darbuotojo_puse_tiesiai", (0.35, 3.7, 1.6), (0, 0, 0.6), 40)
    moving = [o for o in scene.objects if o.name.startswith("Stalcius_3_")]
    if top_handle:
        moving.append(bpy.data.objects[top_handle])
    for o in moving:
        o.location.y += 0.26
    render("03_darbuotojo_puse_kaire", (2.3, 3.1, 1.9), (0, 0.1, 0.58), 40)
elif MODE == "detail":
    door_parts = [o for o in scene.objects if o.name.startswith(("Spinteles_durys", "TIP-ON_plokstele",
                                                                    "Vyrio_taurele"))]
    pivot = Vector(((CAB_X0 + 1.5) * S, FRONT_Y1 * S, 0))
    M = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(100), 4, 'Z') @ Matrix.Translation(-pivot)
    bpy.context.view_layer.update()
    for o in door_parts:
        o.matrix_world = M @ o.matrix_world
    scene.render.resolution_x = 1000 if PREVIEW else 1800
    scene.render.resolution_y = 1000 if PREVIEW else 1800
    render("05_mazgas_TIP-ON", (-0.10, 1.35, 1.15), (-0.40, 0.20, 0.55), 30)
    tip = bpy.data.objects["TIP-ON_korpusas"]
    c = center(tip)
    pts = {
        "tipon": project((c[0], c[1], c[2] + TIPON_H / 2)),
        "hinge_top": project((CAB_X0 + T + 7, FRONT_Y0 - 50, FRONT_Z1 - HINGE_FROM_EDGE + 9)),
        "shelf": project((-480, 150, SHELF_Z0 + T)),
        "plate": project(center(bpy.data.objects["TIP-ON_plokstele"])),
    }
    with open(os.path.join(OUT, "05_mazgas_points.json"), "w") as f:
        json.dump(pts, f)
