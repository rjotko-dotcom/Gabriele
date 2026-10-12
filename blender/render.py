"""
Peržiūros renderiai (Cycles). Paleidimas po raktu_deze.py:
  blender -b blender/raktu_deze.blend -P blender/render.py -- --out renders
  arba: python blender/render.py --out renders
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.abspath(argv[argv.index("--out") + 1]) if "--out" in argv else os.path.join(here, "..", "renders")
os.makedirs(out, exist_ok=True)
if not bpy.data.filepath:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(here, "raktu_deze.blend"))

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 96
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

world = bpy.data.worlds.new("Studija")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.92, 0.88, 0.83, 1)
bg.inputs[1].default_value = 0.35


def mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    build(m.node_tree)
    return m


def wood(nt):
    n = nt.nodes
    bsdf = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.004, 0.06, 0.004)
    wave = n.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 2.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.50, 0.33, 0.18, 1)
    ramp.color_ramp.elements[1].color = (0.70, 0.50, 0.31, 1)
    l = nt.links
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], wave.inputs["Vector"])
    l.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5


bpy.ops.mesh.primitive_plane_add(size=4000)
floor = bpy.context.object
floor.data.materials.append(mat("Medis", wood))

# plastikui – matinė, šiek tiek "PLA" tekstūros
box_mat = bpy.data.materials.get("Deze_juoda")
if box_mat:
    b = box_mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Base Color"].default_value = (0.018, 0.018, 0.02, 1)
    nt = box_mat.node_tree
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 0.0  # pakeičiam per mapping žemiau
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mathn = nt.nodes.new("ShaderNodeMath")
    mathn.operation = "SINE"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 31.4159  # 0.2 mm sluoksniai
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mathn.inputs[0])
    nt.links.new(mathn.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])


def area(name, loc, size, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.size = size
    ld.energy = energy
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    d = Vector((0, 0, 30)) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


area("Key", (-450, -500, 650), 500, 2.2e6, (1.0, 0.96, 0.9))
area("Fill", (650, -250, 300), 400, 6e5, (0.9, 0.95, 1.0))
area("Rim", (100, 650, 500), 300, 1.2e6)

cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.clip_end = 20000
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 8


def shot(name, pos, target, lens=60):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.focus_distance = (Vector(target) - Vector(pos)).length
    sc.render.filepath = os.path.join(out, name)
    bpy.ops.render.render(write_still=True)


shot("priekis.png", (-300, -620, 360), (15, -25, 20))
shot("is_virsaus.png", (0, -260, 700), (0, -10, 20), 50)
floor.hide_render = True
shot("apacia.png", (300, 330, -420), (0, 0, 20), 50)
