"""Iš .blend failo ištraukia horizontalių pjūvių kontūrus (mm) brėžiniams.

  blender -b modelis.blend -P extract_sections.py -- sections.json
"""
import bpy, bmesh, sys, json
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1]
dg = bpy.context.evaluated_depsgraph_get()


def section(names, z):
    loops = []
    for name in names:
        ob = bpy.data.objects.get(name)
        if not ob:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.evaluated_get(dg).to_mesh())
        bm.transform(ob.matrix_world)
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                                     plane_co=Vector((0, 0, z / 1000)), plane_no=Vector((0, 0, 1)))
        cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        # sujungti briaunas į grandines
        adj = {}
        for e in cut:
            a, b = e.verts
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        seen = set()
        for start in adj:
            if start in seen:
                continue
            ends = [v for v in adj if len(adj[v]) == 1 and v not in seen]
            s = start
            chain = [s]
            seen.add(s)
            cur = s
            while True:
                nxt = [v for v in adj[cur] if v not in seen]
                if not nxt:
                    break
                cur = nxt[0]
                seen.add(cur)
                chain.append(cur)
            closed = len(chain) > 2 and chain[0] in adj[chain[-1]]
            loops.append({"obj": name, "closed": closed,
                          "pts": [[round(v.co.x * 1000, 2), round(v.co.y * 1000, 2)] for v in chain]})
        bm.free()
    return loops


body = [o.name for o in bpy.data.objects if o.name.startswith("Korpusas_tinkuotas")]
data = {
    "top_1141": section(["Stalvirsis_virsutinis_azuolas"], 1140.0),
    "work_900": section(["Stalvirsis_darbo_900_azuolas"], 899.0),
    "body_1000": section(body, 1000.0),
    "body_500": section(body, 500.0),
    "flutes_500": section(["Rieveta_panele"], 500.0),
    "plinth_20": section(["Cokolis_bronza"], 20.0),
}
bb = {}
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ev = ob.evaluated_get(dg)
        cs = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        bb[ob.name] = [[round(min(c[i] for c in cs) * 1000, 1) for i in range(3)],
                       [round(max(c[i] for c in cs) * 1000, 1) for i in range(3)]]
data["bbox"] = bb
json.dump(data, open(OUT, "w"))
print("SECTIONS_OK", {k: len(v) for k, v in data.items() if k != "bbox"})
