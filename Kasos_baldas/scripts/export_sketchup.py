"""Eksportas SketchUp'ui: UV (kubinė projekcija) + paprastos medžiagos su tekstūra.

  blender -b 3D_modelis/Kasos_baldas.blend -P scripts/export_sketchup.py -- 3D_modelis
"""
import os, sys, shutil
import bpy

OUT = sys.argv[sys.argv.index("--") + 1]
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")

# 1. UV visiems tinklams
for ob in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=0.8, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')

# 2. medžiagos
FLAT = {
    "Tinkas_pudrinis": (0.50, 0.26, 0.25),
    "Dazytas_MDF_rieves": (0.36, 0.15, 0.16),
    "Laminatas_matinis_pudrinis": (0.50, 0.27, 0.26),
    "Laminatas_baltas_vidus": (0.80, 0.78, 0.75),
    "Bronza_cokolis": (0.48, 0.32, 0.18),
    "Plienas": (0.78, 0.78, 0.80),
    "TIP-ON_pilkas": (0.45, 0.46, 0.48),
    "Kabeliu_anga": (0.03, 0.03, 0.03),
}
shutil.copy(os.path.join(TEX, "medis_Color.jpg"), os.path.join(OUT, "medis.jpg"))
img = bpy.data.images.load(os.path.join(OUT, "medis.jpg"))
for m in bpy.data.materials:
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            nt.nodes.remove(n)
    p = nt.nodes["Principled BSDF"]
    if m.name.startswith("Azuolas"):
        it = nt.nodes.new("ShaderNodeTexImage")
        it.image = img
        nt.links.new(it.outputs["Color"], p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = (*FLAT.get(m.name, (0.6, 0.6, 0.6)), 1)
    m.diffuse_color = p.inputs["Base Color"].default_value

bpy.ops.wm.collada_export(filepath=os.path.join(OUT, "Kasos_baldas.dae"), apply_modifiers=True,
                          triangulate=False, use_texture_copies=False, export_global_up_selection='Z',
                          export_global_forward_selection='Y', apply_global_orientation=False)
bpy.ops.wm.obj_export(filepath=os.path.join(OUT, "Kasos_baldas.obj"), export_materials=True,
                      path_mode='RELATIVE', apply_modifiers=True)
print("EXPORT_OK")
