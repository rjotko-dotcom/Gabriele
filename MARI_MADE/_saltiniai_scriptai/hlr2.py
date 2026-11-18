# Hidden-line drawing engine v2 (corrected geometry): cut lines + visible edges + silhouettes per view
import sys, json, numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image, ImageDraw
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
S = sys.argv[sys.argv.index('--')+1]; which = sys.argv[sys.argv.index('--')+2:]
g = np.load(S+'/geo2.npz'); V = g['V'].astype(float); T = g['T']; O = g['O']; names = np.array(g['names'])
on = names[O]
cat = np.full(len(T), 'obj', dtype=object)
cat[np.isin(on, ['a1_erdve1', 'Lubos1', 'G_1_variantas_sienele1']) | np.char.startswith(on.astype(str), 'Siena_uzpildas')] = 'shell'
cat[np.char.startswith(on.astype(str), 'Langas_')] = 'win'
cat[np.char.startswith(on.astype(str), 'Durys_')] = 'door'
cat[np.isin(on, ['Olive_Tree____Plant1', 'ARRANJO_VASOS_05_1'])] = 'blob'
cat[np.char.startswith(on.astype(str), 'Nuleistos_lubos_') | np.char.startswith(on.astype(str), 'Pakabinamas_') | np.char.startswith(on.astype(str), 'Trosas_')] = 'above'
skip_edge = (on == 'MARY_MADE_1_1')
key = np.round(V/0.0005).astype(np.int64)
_, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
VW = np.zeros((inv.max()+1, 3)); VW[inv] = V; TW = inv[T]
P = VW[TW]; N = np.cross(P[:, 1]-P[:, 0], P[:, 2]-P[:, 0]); A = np.linalg.norm(N, axis=1); ok = A > 1e-10
N[ok] /= A[ok, None]
def make_bvh(mask):
    idx = np.where(mask & ok)[0]
    return BVHTree.FromPolygons([tuple(v) for v in VW], [tuple(t) for t in TW[idx]], epsilon=0.0)
E = np.concatenate([TW[:, [0, 1]], TW[:, [1, 2]], TW[:, [2, 0]]]); F = np.tile(np.arange(len(TW)), 3)
good = ok[F]; E = E[good]; F = F[good]
E.sort(1); o_ = np.lexsort((E[:, 1], E[:, 0])); E = E[o_]; F = F[o_]
brk = np.r_[True, (np.diff(E, axis=0) != 0).any(1)]; gid = np.cumsum(brk)-1
UE = E[brk]; first = F[brk]; second = np.full(gid.max()+1, -1); second[gid[~brk]] = F[~brk]
VIEWS = {
 'PLAN': dict(axis=2, sign=-1, cut=1.2, u=lambda p: p[..., 0], v=lambda p: p[..., 1]),
 'A': dict(axis=1, sign=+1, cut=4.62, u=lambda p: p[..., 0], v=lambda p: p[..., 2]),
 'B': dict(axis=1, sign=-1, cut=4.90, u=lambda p: -p[..., 0], v=lambda p: p[..., 2]),
 'C': dict(axis=0, sign=-1, cut=4.60, u=lambda p: p[..., 1], v=lambda p: p[..., 2]),
 'D': dict(axis=0, sign=+1, cut=15.39, u=lambda p: -p[..., 1], v=lambda p: p[..., 2]),
}
def outline(tris_uv, r=0.01, dil=1, minlen=10):
    """rasterise projected triangles, return outer contour polylines"""
    if len(tris_uv) == 0: return []
    flat = tris_uv.reshape(-1, 2); mn = flat.min(0)-0.05; mx = flat.max(0)+0.05
    W, H = (((mx-mn)/r).astype(int)+2)
    img = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(img)
    for t in tris_uv:
        q = [((x-mn[0])/r, (y-mn[1])/r) for x, y in t]; dr.polygon(q, fill=255, outline=255)
    a = np.array(img) > 0
    from scipy import ndimage
    a = ndimage.binary_closing(ndimage.binary_dilation(a, iterations=dil), iterations=2)
    a = ndimage.binary_fill_holes(a)
    cs = plt.contour(np.arange(W)*r+mn[0], np.arange(H)*r+mn[1], a.astype(float), levels=[0.5])
    out = [p[::2].tolist() for p in cs.allsegs[0] if len(p) > minlen]; plt.close('all'); return out
def run(name, vw):
    ax, sg, c = vw['axis'], vw['sign'], vw['cut']
    depth = lambda p: (p[..., ax]-c)*sg
    out = {'cut_shell': [], 'cut_obj': [], 'cut_win': [], 'vis': [], 'vis_win': [], 'blob': [], 'blob_dash': [], 'above': []}
    plan = name == 'PLAN'
    occl = ok.copy()
    if plan: occl &= ~np.isin(cat, ['blob', 'above', 'door'])
    bvh = make_bvh(occl)
    d = depth(P); s = np.sign(d); cross = (s.min(1) < 0) & (s.max(1) > 0) & ok
    for ti in np.where(cross)[0]:
        ct = cat[ti]
        if ct in ('blob',) or (plan and ct in ('door', 'above')): continue
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            da, db = d[ti, a], d[ti, b]
            if (da < 0) != (db < 0): t = da/(da-db); pts.append(P[ti, a]+(P[ti, b]-P[ti, a])*t)
        if len(pts) == 2:
            pp = np.array(pts); seg = np.c_[vw['u'](pp), vw['v'](pp)].tolist()
            out['cut_shell' if ct == 'shell' else 'cut_win' if ct in ('win', 'door') else 'cut_obj'].append(seg)
    viewdir = np.zeros(3); viewdir[ax] = sg
    f1 = first; f2 = second
    n1 = N[f1]; n2 = np.where((f2 >= 0)[:, None], N[np.maximum(f2, 0)], 0)
    dih = np.einsum('ij,ij->i', n1, n2); bnd = f2 < 0
    crease = (~bnd) & (dih < np.cos(np.radians(28)))
    sil = (~bnd) & (np.sign(n1 @ viewdir) != np.sign(n2 @ viewdir)) & (dih < np.cos(np.radians(6)))
    ec = cat[f1]
    sel = (bnd | crease | sil) & (ec != 'blob') & ~skip_edge[f1]
    if plan: sel &= ~np.isin(ec, ['door', 'above'])
    EE = UE[sel]; ecs = ec[sel]
    p0 = VW[EE[:, 0]]; p1 = VW[EE[:, 1]]; d0 = depth(p0); d1 = depth(p1)
    keep = (d0 > -1e-6) | (d1 > -1e-6)
    p0, p1, d0, d1, ecs = p0[keep], p1[keep], d0[keep], d1[keep], ecs[keep]
    t = np.clip(np.where(d0 < 0, d0/(d0-d1+1e-15), 0), 0, 1); q0 = p0+(p1-p0)*t[:, None]
    t = np.clip(np.where(d1 < 0, d1/(d1-d0+1e-15), 0), 0, 1); q1 = p1+(p0-p1)*t[:, None]
    L = np.linalg.norm(q1-q0, axis=1); nz = L > 1e-4; q0, q1, L, ecs = q0[nz], q1[nz], L[nz], ecs[nz]
    toview = Vector(tuple(-viewdir)); step = 0.006
    for a, b, l, ct in zip(q0, q1, L, ecs):
        n = max(2, int(l/step)+1); ts = np.linspace(0, 1, n); pts = a+(b-a)*ts[:, None]
        vis = np.empty(n, bool)
        for k, p in enumerate(pts):
            dd = (p[ax]-c)*sg; hit = bvh.ray_cast(Vector(p)+toview*0.002, toview, max(dd-0.002, 0)); vis[k] = hit[0] is None
        k = 0
        while k < n:
            if vis[k]:
                j = k
                while j+1 < n and vis[j+1]: j += 1
                if j > k:
                    seg = np.array([pts[k], pts[j]])
                    out['vis_win' if ct in ('win', 'door') else 'vis'].append([np.c_[vw['u'](seg), vw['v'](seg)].tolist(), float(np.mean(depth(seg)))])
                k = j+1
            else: k += 1
    # silhouettes of plants / flowers
    for bn in ['Olive_Tree____Plant1', 'ARRANJO_VASOS_05_1']:
        m = (on == bn) & ok
        tr = P[m]
        if plan:
            uv = np.stack([vw['u'](tr), vw['v'](tr)], -1)
            if bn.startswith('Olive'):
                zb = tr[:, :, 2].min(); pot = tr[:, :, 2].max(1) < zb+0.55
                out['blob_dash'] += outline(uv[~pot], 0.012, 2)      # canopy above the cut -> dashed
                out['blob'] += outline(uv[pot], 0.006, 1)            # pot -> solid
            else: out['blob'] += outline(uv, 0.006, 1)
        else:
            tr = tr[(depth(tr) > 0).all(1)]
            uv = np.stack([vw['u'](tr), vw['v'](tr)], -1); out['blob'] += outline(uv, 0.01, 1)
    if plan:
        out['outline'] = []
        for bn in ['Armchair__4_1', 'Armchair__4_2']:
            tr = P[(on == bn) & ok]; uv = np.stack([vw['u'](tr), vw['v'](tr)], -1); out['outline'] += outline(uv, 0.006, 1)
        from scipy.spatial import ConvexHull
        for nm in np.unique(on[cat == 'above']):
            if str(nm).startswith('Trosas'): continue
            pts = VW[np.unique(TW[(on == nm)].ravel())][:, :2]; h = ConvexHull(pts)
            out['above'].append(pts[h.vertices].tolist()+[pts[h.vertices[0]].tolist()])
    json.dump(out, open(f'{S}/draw2_{name}.json', 'w'))
    print(name, {k: len(v) for k, v in out.items()}, flush=True)
for nm, vw in VIEWS.items():
    if not which or nm in which: run(nm, vw)
