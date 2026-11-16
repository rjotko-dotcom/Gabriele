"""Eksportas SketchUp'ui: UV (kubinė projekcija) + paprastos medžiagos (tekstūra arba spalva).

  blender -b 3D_modelis/Kasos_baldas.blend -P scripts/export_sketchup.py -- <aplankas>
"""
import os, sys, shutil
import bpy

OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(OUT, exist_ok=True)

for ob in [o for o in bpy.context.scene.objects if o.type == 'LIGHT' or o.type == 'CAMERA']:
    bpy.data.objects.remove(ob, do_unlink=True)

# UV visiems tinklams + modifikatorių pritaikymas
for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=0.6, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')

copied = {}
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        continue
    linked = p.inputs["Base Color"].is_linked
    color = tuple(m.diffuse_color)[:3] if linked else tuple(p.inputs["Base Color"].default_value)[:3]
    tex = m.get("export_tex")
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            nt.nodes.remove(n)
    for inp in ("Emission Strength", "Transmission Weight", "Coat Weight"):
        if inp in p.inputs:
            p.inputs[inp].default_value = 0.0
    if tex and os.path.exists(tex):
        fn = os.path.basename(tex)
        if fn not in copied:
            shutil.copy(tex, os.path.join(OUT, fn))
            copied[fn] = bpy.data.images.load(os.path.join(OUT, fn))
        it = nt.nodes.new("ShaderNodeTexImage")
        it.image = copied[fn]
        nt.links.new(it.outputs["Color"], p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = (*color, 1)
    m.diffuse_color = (*color, 1)

bpy.ops.wm.collada_export(filepath=os.path.join(OUT, "Kasos_baldas.dae"), apply_modifiers=True,
                          triangulate=False, use_texture_copies=False)
bpy.ops.wm.obj_export(filepath=os.path.join(OUT, "Kasos_baldas.obj"), export_materials=True,
                      path_mode='STRIP', apply_modifiers=True)
# DAE: tekstūrų keliai – santykiniai
p = os.path.join(OUT, "Kasos_baldas.dae")
s = open(p, encoding="utf-8").read()
for fn in copied:
    s = s.replace(os.path.join(OUT, fn), fn)
open(p, "w", encoding="utf-8").write(s)
print("EXPORT_OK", list(copied))
