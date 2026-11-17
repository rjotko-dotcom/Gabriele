# Professional corrections of the SketchUp geometry -> geo2.npz
import sys, numpy as np
S = sys.argv[1]
g = np.load(S + '/geo.npz')
V = g['V'].copy(); T = g['T'].copy(); O = g['O'].copy(); M = g['M'].copy()
names = list(g['names']); mats = list(g['mats'])
oid = lambda n: names.index(n)
def verts_of(n):
    return np.unique(T[O == oid(n)].ravel())

# ---------------------------------------------------------------- 1. podium 450 -> 300 mm (entrance level -1,70), 2 steps x 150
sh = verts_of('a1_erdve1')
tall = np.unique(T[(O == oid('a1_erdve1')) & (V[T][:, :, 2].max(1) > 0.5)].ravel())
v = V[sh]
m = (np.abs(v[:, 0]-6.34) < 0.012) & (v[:, 2] < 0.2) & (v[:, 1] > 2.6) & (v[:, 1] < 8.0) & ~np.isin(sh, tall)
v[m, 0] = 5.949                                                    # remove 3rd tread
m = (v[:, 0] < 6.0) & (v[:, 2] > 0.1) & (v[:, 2] < 0.47)
v[m, 2] = np.maximum(0.0, v[m, 2]-0.15)
V[sh] = v
for n in ['Armchair__4_1', 'Armchair__4_2', 'table_basse1', 'table_basse2', 'Serengueti_Rose_white_120x160_1', 'Olive_Tree____Plant1']:
    V[verts_of(n), 2] -= 0.15
PODIUM = 0.30

# ---------------------------------------------------------------- 2. shelving depth 400 mm
sv = verts_of('G_1variantas_lentyna1'); v = V[sv]
back = v[:, 1] > 7.35; right = v[:, 0] > 17.15
v[back, 1] = 7.924 - (7.924 - v[back, 1]) * (0.40/0.494)
v[right, 0] = 17.761 - (17.761 - v[right, 0]) * (0.40/0.567)
V[sv] = v
for n in ['Lentyna_maza']:
    lv = verts_of(n); V[lv, 0] = np.maximum(V[lv, 0], 17.361)

# ---------------------------------------------------------------- 3. olive tree: scale/rotate so the canopy stays inside the room
tv = verts_of('Olive_Tree____Plant1'); tp = V[tv].copy()
base = np.array([3.63, 7.20]); zb = tp[:, 2].min()
rel = tp[:, :2] - base
BOX = (2.95, 5.40, 2.85, 7.87)
OBST = [(4.27, 7.03, 5.21, 7.95), (2.85, 5.81, 3.78, 6.74), (3.96, 6.29, 4.38, 6.71), (4.48, 6.55, 4.81, 6.89)]   # chairs, tables
best = None
for th in np.radians(np.arange(0, 360, 10)):
    c, s_ = np.cos(th), np.sin(th); r = rel @ np.array([[c, s_], [-s_, c]])
    mn, mx = r.min(0), r.max(0)
    for px in np.arange(3.05, 5.35, 0.05):
        for py in np.arange(6.9, 7.65, 0.05):
            if any(a-0.33 < px < b+0.33 and c_-0.33 < py < d+0.33 for a, c_, b, d in OBST): continue
            sc = min(0.9, (px-BOX[0])/-mn[0], (BOX[1]-px)/mx[0], (py-BOX[2])/-mn[1], (BOX[3]-py)/mx[1])
            if best is None or sc > best[0]: best = (sc, th, px, py)
sc, th, px, py = best
c, s_ = np.cos(th), np.sin(th)
r = (rel @ np.array([[c, s_], [-s_, c]])) * sc
V[tv, 0] = r[:, 0] + px; V[tv, 1] = r[:, 1] + py
V[tv, 2] = zb + (tp[:, 2]-zb) * sc
print('tree scale %.2f rot %d pot (%.2f, %.2f) height %.2f' % (sc, np.degrees(th), px, py, V[tv, 2].max()))

# ---------------------------------------------------------------- helpers to remove / add geometry
keep = np.ones(len(T), bool)
def drop_object(n): keep[O == oid(n)] = False
NEW = []   # (name, verts, tris)
def box(name, x0, x1, y0, y1, z0, z1):
    p = np.array([[x, y, z] for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    NEW.append((name, p, np.array(f)))
def cyl(name, cx, cy, r, z0, z1, n=64):
    a = np.linspace(0, 2*np.pi, n, endpoint=False)
    ring = np.c_[cx+r*np.cos(a), cy+r*np.sin(a)]
    p = np.vstack([np.c_[ring, np.full(n, z0)], np.c_[ring, np.full(n, z1)], [[cx, cy, z0], [cx, cy, z1]]])
    f = []
    for i in range(n):
        j = (i+1) % n
        f += [(i, j, n+j), (i, n+j, n+i), (2*n, j, i), (2*n+1, n+i, n+j)]
    NEW.append((name, p, np.array(f)))

# ---------------------------------------------------------------- 4. dropped-ceiling discs (150 mm) centred on tables + linear pendants on cables
for n in ['Nuleidimas1_1', 'Nuleidimas2_1', 'Neleidimas3_1']: drop_object(n)
TABLES = {}
for n in ['Staliukas1_1', 'Staliukas2_1', 'Staliukas3_1']:
    p = V[verts_of(n)]; TABLES[n] = ((p[:, 0].min()+p[:, 0].max())/2, (p[:, 1].min()+p[:, 1].max())/2)
CEIL = 6.0; DISC = 0.15; PEND_Z = 2.50
for i, (n, (cx, cy)) in enumerate(TABLES.items()):
    cyl(f'Nuleistos_lubos_{i+1}', cx, cy, 0.825, CEIL-DISC, CEIL)
    box(f'Pakabinamas_sviestuvas_{i+1}', cx-0.467, cx+0.467, cy-0.057, cy+0.057, PEND_Z, PEND_Z+0.06)
    for dx in (-0.40, 0.40): box(f'Trosas_{i+1}', cx+dx-0.002, cx+dx+0.002, cy-0.002, cy+0.002, PEND_Z+0.06, CEIL-DISC)
print('tables', {k: tuple(round(x, 3) for x in v) for k, v in TABLES.items()})

# ---------------------------------------------------------------- 5. windows: remove opaque infill, add frames + glass + transom
WX = [(6.665, 7.857, 1.986, 2.115), (9.465, 10.654, 1.986, 2.115), (12.263, 13.465, 1.986, 2.115), (15.128, 16.303, 1.946, 2.13)]
P = V[T]; nrm = np.cross(P[:, 1]-P[:, 0], P[:, 2]-P[:, 0]); nl = np.linalg.norm(nrm, axis=1)+1e-12; ny = nrm[:, 1]/nl
infill = (O == oid('a1_erdve1')) & (np.abs(ny) > 0.9) & (P[:, :, 1].min(1) > 1.93) & (P[:, :, 1].max(1) < 2.14) & (P[:, :, 2].min(1) > 0.85) & (np.ptp(P[:, :, 2], 1) > 3)
keep &= ~infill
for i, (a, b, y0, y1) in enumerate(WX):
    yc = (y0+y1)/2; t = 0.06; z0, z1 = 0.90, 6.0
    box(f'Langas_remas_{i}', a, a+t, yc-0.035, yc+0.035, z0, z1); box(f'Langas_remas_{i}', b-t, b, yc-0.035, yc+0.035, z0, z1)
    box(f'Langas_remas_{i}', a, b, yc-0.035, yc+0.035, z0, z0+t); box(f'Langas_remas_{i}', a, b, yc-0.035, yc+0.035, z1-t, z1)
    box(f'Langas_remas_{i}', a, b, yc-0.035, yc+0.035, 3.60, 3.66)
    box(f'Langas_stiklas_{i}', a+t, b-t, yc-0.006, yc+0.006, z0+t, z1-t)
# ---------------------------------------------------------------- 6. doors: street entrance (facade) and side entrance (left wall), glass double doors + transom
DOORS = [dict(axis='y', a=3.56, b=5.31, plane=1.80, z0=PODIUM, h=2.40),     # facade, opening x 3.56-5.31
         dict(axis='x', a=3.326, b=5.078, plane=1.92, z0=PODIUM, h=2.40)]   # left wall, opening y 3.33-5.08
for i, d in enumerate(DOORS):
    a, b, pl, z0, h = d['a'], d['b'], d['plane'], d['z0'], d['h']; t = 0.06
    def bx(nm, u0, u1, w0, w1, zz0, zz1):
        if d['axis'] == 'y': box(nm, u0, u1, w0, w1, zz0, zz1)
        else: box(nm, w0, w1, u0, u1, zz0, zz1)
    for (u0, u1) in [(a, a+t), (b-t, b), ((a+b)/2-0.03, (a+b)/2+0.03)]:
        bx(f'Durys_staktos_{i}', u0, u1, pl-0.035, pl+0.035, z0, z0+h)
    bx(f'Durys_staktos_{i}', a, b, pl-0.035, pl+0.035, z0+h, z0+h+t)
    bx(f'Durys_vitrina_{i}', a, b, pl-0.035, pl+0.035, 6.0-t, 6.0)
    bx(f'Durys_vitrina_{i}', a+t, b-t, pl-0.006, pl+0.006, z0+h+t, 6.0-t)
DOORS_2D = [dict(kind='facade', x0=3.56, x1=5.31, y=1.80, inward=+1), dict(kind='left', y0=3.326, y1=5.078, x=1.92, inward=+1)]

# ---------------------------------------------------------------- assemble
T2 = T[keep]; O2 = O[keep]; M2 = M[keep]; Vn = [V]; off = len(V)
names2 = list(names)
Tn, On, Mn = [T2], [O2], [M2]
for nm, p, f in NEW:
    if nm not in names2: names2.append(nm)
    Vn.append(p); Tn.append(f+off); On.append(np.full(len(f), names2.index(nm))); Mn.append(np.zeros(len(f), int)); off += len(p)
np.savez_compressed(S + '/geo2.npz', V=np.vstack(Vn), T=np.vstack(Tn), O=np.concatenate(On), M=np.concatenate(Mn), names=np.array(names2), mats=np.array(mats))
import json
json.dump(dict(tables=TABLES, podium=PODIUM, pend_z=PEND_Z, ceil=CEIL, disc=DISC, tree=dict(scale=sc, x=px, y=py), doors=DOORS_2D, windows=WX),
          open(S + '/geo2_meta.json', 'w'), indent=1)
print('saved geo2', off)
