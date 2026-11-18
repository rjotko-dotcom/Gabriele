import sys, ezdxf
from ezdxf import bbox
p = sys.argv[1]; d = ezdxf.readfile(p); n = 0
for e in list(d.modelspace().query('*[layer=="A-DURYS"]')):
    b = bbox.extents([e], fast=True)
    if b.extmax.x < 3000 and abs(b.extmin.x-1955) < 15 and (abs(b.extmin.y-3386) < 15 or abs(b.extmax.y-5018) < 15 or abs(b.extmin.y-4202) < 15):
        d.modelspace().delete_entity(e); n += 1
d.saveas(p); print('removed old equal-leaf door symbol entities:', n)
