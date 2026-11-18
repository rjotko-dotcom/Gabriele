# Re-apply a user's manual edits (diff edited-vs-base model space) onto a regenerated drawing
import sys, collections, ezdxf
from ezdxf import bbox
from ezdxf.addons import Importer
base_p, edited_p, target_p = sys.argv[1:4]
def sig(e):
    b = bbox.extents([e], fast=True)
    if not b.has_data: return None
    return (e.dxftype(), e.dxf.layer, round(b.extmin.x/10), round(b.extmin.y/10), round(b.extmax.x/10), round(b.extmax.y/10))
def index(doc):
    d = collections.defaultdict(list)
    for e in doc.modelspace():
        s = sig(e)
        if s: d[s].append(e)
    return d
base, ed, tgt = ezdxf.readfile(base_p), ezdxf.readfile(edited_p), ezdxf.readfile(target_p)
B, E, T = index(base), index(ed), index(tgt)
deleted = {s: len(v) - len(E.get(s, [])) for s, v in B.items() if len(v) > len(E.get(s, []))}
added = [e for s, v in E.items() for e in v[len(B.get(s, [])):]]
nd = 0
for s, n in deleted.items():
    for e in T.get(s, [])[:n]: tgt.modelspace().delete_entity(e); nd += 1
imp = Importer(ed, tgt); imp.import_entities(added, tgt.modelspace()); imp.finalize()
tgt.saveas(target_p)
print(f'user edits: deleted {sum(deleted.values())} (applied {nd}), added {len(added)}')
