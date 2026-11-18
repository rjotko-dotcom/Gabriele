# Furniture plan + sections 1-1..4-4 (corrected model) -> DXF model space (mm)
import sys, json, math, numpy as np, ezdxf
from ezdxf.enums import TextEntityAlignment as TA, MTextEntityAlignment as MA
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union, linemerge
S = sys.argv[1]; OUTDXF = sys.argv[2]
sys.path.insert(0, S + '/scripts')
from dxf_common import *
g = np.load(S + '/geo2.npz'); V = g['V']; T = g['T']; O = g['O']; NAMES = list(g['names'])
META = json.load(open(S + '/geo2_meta.json'))
def bb(name):
    p = V[T[O == NAMES.index(name)]].reshape(-1, 3); return p.min(0), p.max(0)
def bbp(prefix):
    idx = [i for i, n in enumerate(NAMES) if n.startswith(prefix)]
    p = V[T[np.isin(O, idx)]].reshape(-1, 3); return p.min(0), p.max(0)

doc = ezdxf.new('R2018', setup=True); setup(doc); msp = doc.modelspace()
for n, (c, lw, lt) in {'A-LANGAI': (7, 25, 'Continuous'), 'A-DURYS': (7, 25, 'Continuous'), 'A-ASYS': (7, 18, 'A-ASIS'),
                       'A-ASYS-ZYM': (7, 25, 'Continuous')}.items():
    if n not in doc.layers: doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
# proper ISO chain line for 1:50 : 12 mm dash, 3 mm gap, dot, 3 mm gap (paper)
FLOOR_ABS = -2.0; PODIUM = META['podium']
AXV = {'1': 1.770, '2': 4.917, '3': 12.917}          # vertical axes (model x)
AXH = {'A': 1.684, 'B': 8.791}                       # horizontal axes (model y)
VIEWS = {'PLAN': dict(ox=0, oy=0), 'A': dict(oy=-14000), 'B': dict(oy=-26000), 'C': dict(oy=-38000), 'D': dict(oy=-38000)}
D = {k: json.load(open(f'{S}/draw2_{k}.json')) for k in VIEWS}
for k in 'ABCD':
    us = [p[0] for s in D[k]['cut_shell'] for p in s]; VIEWS[k]['umin'] = min(us); VIEWS[k]['umax'] = max(us)
VIEWS['A']['ox'] = 2000 - VIEWS['A']['umin']*1000; VIEWS['B']['ox'] = 2000 - VIEWS['B']['umin']*1000
VIEWS['C']['ox'] = 2000 - VIEWS['C']['umin']*1000; VIEWS['D']['ox'] = 14000 - VIEWS['D']['umin']*1000
def P(k, u, v): return (u*1000 + VIEWS[k]['ox'], v*1000 + VIEWS[k]['oy'])
L = lambda lay: {'layer': lay}

def add_lines(k, segs, layer, merge=True):
    if not segs: return
    ls = [LineString([tuple(np.round(np.array(P(k, *a)), 1)), tuple(np.round(np.array(P(k, *b)), 1))]) for a, b in segs if math.hypot(a[0]-b[0], a[1]-b[1]) > 1e-4]
    if not ls: return
    u_ = unary_union(ls)
    geom = u_ if u_.geom_type == 'LineString' else linemerge(u_)
    for p in (geom.geoms if hasattr(geom, 'geoms') else [geom]):
        c = list(p.coords)
        if len(c) >= 2: msp.add_lwpolyline(c, dxfattribs=L(layer))

def poche(k, segs):
    u = unary_union([LineString([P(k, *a), P(k, *b)]) for a, b in segs])
    for pg in polygonize(u):
        if 2*pg.area/max(pg.length, 1) < 1250 and pg.area > 2000:
            pg = pg.simplify(1.0)
            h = msp.add_hatch(color=7, dxfattribs=L('A-PJUVIS-SIENOS-UZP')); h.set_solid_fill(color=7, rgb=(150, 150, 150))
            h.paths.add_polyline_path(list(pg.exterior.coords), is_closed=True, flags=1)
            for it in pg.interiors: h.paths.add_polyline_path(list(it.coords), is_closed=True, flags=0)
    add_lines(k, segs, 'A-PJUVIS-SIENOS')

def mtext(s, x, y, h=2.5, layer='A-TEKSTAS', att=MA.MIDDLE_CENTER, mask=True, rot=0):
    m = msp.add_mtext(s, dxfattribs={'layer': layer, 'style': TXT, 'char_height': h*SCALE, 'rotation': rot})
    m.set_location((x, y), attachment_point=att)
    if mask: m.set_bg_color('canvas', scale=1.2)
    return m

def dot(x, y, r=0.6):
    h = msp.add_hatch(color=7, dxfattribs=L('A-MATMENYS')); h.paths.add_edge_path().add_arc((x, y), r*SCALE, 0, 360)

def level(k, u, z, desc, side, col=0):
    """level mark at the edge of a section; column offset `col` (m) away from the drawing"""
    s = SCALE; d = 1 if side == 'R' else -1
    x, y = P(k, u + d*col, z)
    h = 2.5*s; w = 1.45*s
    msp.add_lwpolyline([(x, y), (x-w, y+h), (x+w, y+h)], close=True, dxfattribs=L('A-ALTITUDES'))
    hh = msp.add_hatch(color=7, dxfattribs=L('A-ALTITUDES')); hh.paths.add_polyline_path([(x, y), (x, y+h), (x+d*w, y+h)], is_closed=True)
    val = fmt_level(z, FLOOR_ABS)
    lead = 16*s
    msp.add_line((x, y), (x+d*lead, y), dxfattribs=L('A-ALTITUDES'))
    msp.add_line((x-d*w, y+h), (x+d*lead, y+h), dxfattribs=L('A-ALTITUDES'))
    mtext(val, x+d*(w+0.6*s), y+h+0.7*s, 2.5, att=MA.BOTTOM_LEFT if d > 0 else MA.BOTTOM_RIGHT, mask=False)
    if desc: mtext(desc, x+d*(w+0.6*s), y-0.7*s, 2.5, att=MA.TOP_LEFT if d > 0 else MA.TOP_RIGHT, mask=False)

def axis_bubble(x, y, label, lx0, ly0, lx1, ly1):
    msp.add_line((lx0, ly0), (lx1, ly1), dxfattribs=L('A-ASYS'))
    msp.add_circle((x, y), 5*SCALE, dxfattribs=L('A-ASYS-ZYM'))
    t = msp.add_text(label, height=5*SCALE, dxfattribs={'layer': 'A-TEKSTAS', 'style': TXT}); t.set_placement((x, y), align=TA.MIDDLE_CENTER)

DS = 'ISO-50'
def hdim(k, y, xs, v=0.0):   # horizontal chain at model-y `y` measured between points (x, v)
    msp.add_multi_point_linear_dim(base=P(k, 0, y), points=[P(k, x, v) for x in xs], angle=0, dimstyle=DS, dxfattribs=L('A-MATMENYS'))
def vdim(k, x, ys, u=0.0):
    msp.add_multi_point_linear_dim(base=P(k, x, 0), points=[P(k, u, y) for y in ys], angle=90, dimstyle=DS, dxfattribs=L('A-MATMENYS'))

# =============================================================== PLAN
k = 'PLAN'; d = D[k]
poche(k, d['cut_shell'])
add_lines(k, d['cut_obj'], 'A-PJUVIS-BALDAI')
add_lines(k, d['cut_win'] + [s for s, _ in d['vis_win']], 'A-LANGAI')
add_lines(k, [s for s, dep in d['vis'] if dep < 1.17], 'A-MATOMOS-ARTI')
add_lines(k, [s for s, dep in d['vis'] if dep >= 1.17], 'A-MATOMOS-TOLI')
for b in d['blob']: msp.add_lwpolyline([P(k, *p) for p in b], close=True, dxfattribs=L('A-AUGALAI'))
for b in d['blob_dash']: msp.add_lwpolyline([P(k, *p) for p in b], close=True, dxfattribs={'layer': 'A-VIRS-PJUVIO'})
for a in d['above']: msp.add_lwpolyline([P(k, *p) for p in a], close=True, dxfattribs=L('A-VIRS-PJUVIO'))
for a in d.get('outline', []): msp.add_lwpolyline([P(k, *p) for p in a], close=True, dxfattribs=L('A-MATOMOS-ARTI'))
# doors (ISO 7519 simplified: leaf at 90° + swing arc)
def door_double(hinges, closed_dir, open_dir, leaf):
    for (hx, hy), cd in zip(hinges, closed_dir):
        cx, cy = P(k, hx, hy); ox, oy = open_dir; px, py = cd
        msp.add_line((cx, cy), (cx+ox*leaf*1000, cy+oy*leaf*1000), dxfattribs=L('A-DURYS'))
        a0 = math.degrees(math.atan2(py, px)); a1 = math.degrees(math.atan2(oy, ox))
        s0, s1 = (a0, a1) if (a1-a0) % 360 < 180 else (a1, a0)
        msp.add_arc((cx, cy), leaf*1000, s0, s1, dxfattribs={'layer': 'A-DURYS', 'lineweight': 13})
fd = [x for x in META['doors'] if x['kind'] == 'facade'][0]; ld = [x for x in META['doors'] if x['kind'] == 'left'][0]
fl, fr = fd['leaves'][0]-0.05, fd['leaves'][1]-0.05
door_double([(fd['x0']+0.05, fd['y']+0.035)], [(1, 0)], (0, 1), fl)
door_double([(fd['x1']-0.05, fd['y']+0.035)], [(-1, 0)], (0, 1), fr)
lf2 = (ld['y1']-ld['y0']-0.12)/2
door_double([(ld['x']+0.035, ld['y0']+0.06), (ld['x']+0.035, ld['y1']-0.06)], [(0, 1), (0, -1)], (1, 0), lf2)
# room / furniture labels (2.5 mm)
TB = META['tables']
for n, (cx, cy) in TB.items(): mtext('Prekių stalas\n1620×810', *P(k, cx, cy), 2.5)
for s_, x, y in [('Recepcija', 8.70, 6.17), ('Drabužių pakaba', 8.65, 3.90), ('Drabužių pakaba', 11.44, 3.90), ('Drabužių pakaba', 14.32, 3.90),
                 ('Stelažas, gylis 400', 14.10, 7.20), ('Akcentinė siena', 8.58, 7.62), ('Kilimas', 4.10, 3.25)]:
    mtext(s_, *P(k, x, y), 2.5)
mtext('PREKYBOS SALĖ', *P(k, 13.30, 4.30), 3.5)
mtext('POILSIO ZONA', *P(k, 4.10, 4.55), 3.5)
def leader(s_, tx, ty, lx, ly, side='L'):
    X0, Y0 = P(k, tx, ty); X1, Y1 = P(k, lx, ly)
    msp.add_line((X0, Y0), (X1, Y1), dxfattribs=L('A-MATMENYS')); dot(X0, Y0)
    mtext(s_, X1 + (0.08 if side == 'L' else -0.08)*1000, Y1, 2.5, att=MA.MIDDLE_LEFT if side == 'L' else MA.MIDDLE_RIGHT)
tree = META['tree']
leader('Fotelis', 4.74, 7.30, 5.70, 7.35)
leader('Fotelis', 3.31, 6.10, 3.31, 5.40, side='L')
leader('Alyvmedis vazone', tree['x'], tree['y'], 5.70, 6.80)
leader('Kavos staliukai', 4.30, 6.55, 5.70, 6.25)
leader('Veidrodis Ø1000', 17.30, 5.35, 16.20, 5.95, side='R')
def lvl_box(val, x, y):
    X, Y = P(k, x, y); w = len(val)*2.5*0.62*SCALE + 2.0*SCALE; h = 2.5*SCALE + 2.0*SCALE
    msp.add_lwpolyline([(X-w/2, Y-h/2), (X+w/2, Y-h/2), (X+w/2, Y+h/2), (X-w/2, Y+h/2)], close=True, dxfattribs=L('A-ALTITUDES'))
    mtext(val, X, Y, 2.5)
lvl_box('-2,000', 13.30, 3.90 + 0.0) if False else None
lvl_box('-2,000', 13.30, 3.95); lvl_box(fmt_level(PODIUM, FLOOR_ABS), 4.10, 4.10); lvl_box('-2,000', 7.10, 5.20)
mtext('2×150', *P(k, 5.74, 4.95), 2.5, rot=90)
# dimensions (inside -> out), axes outermost
hdim(k, 1.10, [1.839, META['door']['x0'], META['door']['x1']] + [v for w in META['windows'] for v in w[:2]] + [17.937], 1.75)
hdim(k, 0.60, [AXV['1'], AXV['2'], AXV['3'], 17.937], 1.75)
hdim(k, 8.45, [2.833, 5.53, 5.949, 6.785, 10.366, 17.886], 7.955)
hdim(k, 8.95, [2.833, 17.886], 7.955)
vdim(k, 1.40, [1.694, 2.708, 3.326, 5.078, 7.955, 8.058], 1.839)
vdim(k, 1.00, [AXH['A'], AXH['B']], 1.839)
# axes: bubbles bottom + left, chain lines through the plan
for lab, x in AXV.items():
    X, Y = P(k, x, -0.05); axis_bubble(X, Y, lab, X, Y+5*SCALE, X, P(k, 0, 9.15)[1])
for lab, y in AXH.items():
    X, Y = P(k, 0.45, y); axis_bubble(X, Y, lab, X+5*SCALE, Y, P(k, 18.30, 0)[0], Y)
# section markers (outermost)
def sec_marker(num, horiz, c, direction):
    s = SCALE
    ends = [(-0.20, c), (18.50, c)] if horiz else [(c, -0.65), (c, 9.45)]
    dv = (0, direction) if horiz else (direction, 0)
    for (x, y) in ends:
        X, Y = P(k, x, y)
        if horiz: msp.add_line((X-4*s, Y), (X+4*s, Y), dxfattribs=L('A-PJUVIO-ZYMES'))
        else: msp.add_line((X, Y-4*s), (X, Y+4*s), dxfattribs=L('A-PJUVIO-ZYMES'))
        ax_, ay_ = X+dv[0]*5*s, Y+dv[1]*5*s
        msp.add_line((X, Y), (ax_, ay_), dxfattribs=L('A-PJUVIO-ZYMES'))
        px, py = -dv[1], dv[0]
        hd = msp.add_hatch(color=7, dxfattribs=L('A-PJUVIO-ZYMES'))
        hd.paths.add_polyline_path([(ax_+dv[0]*2*s, ay_+dv[1]*2*s), (ax_+px*1.1*s, ay_+py*1.1*s), (ax_-px*1.1*s, ay_-py*1.1*s)], is_closed=True)
        tx, ty = X+dv[0]*9.5*s, Y+dv[1]*9.5*s
        t = msp.add_text(num, height=5*s, dxfattribs={'layer': 'A-TEKSTAS', 'style': TXT}); t.set_placement((tx, ty), align=TA.MIDDLE_CENTER)
sec_marker('1', True, 4.62, +1); sec_marker('2', True, 4.90, -1); sec_marker('3', False, 4.60, -1); sec_marker('4', False, 15.39, +1)

# =============================================================== SECTIONS
SHORT = {'top': 'viršus', 'bot': 'apačia'}
LEV = {   # (object or prefix, top/bot, short description)
 'A': [('Recepcijos_stalvir_is1', 'top', 'recepcija'), ('Staliukas1_1', 'top', 'stalai'), ('G_1variantas_lentyna1', 'top', 'stelažas'),
       ('Nuleistos_lubos_1', 'bot', 'nul. lubos'), ('Pakabinamas_sviestuvas_1', 'bot', 'šviestuvai'), ('MARY_MADE_1_1', 'bot', 'logotipas'),
       ('Olive_Tree____Plant1', 'top', 'alyvmedis')],
 'B': [('Componente1', 'top', 'pakabos'), ('Staliukas1_1', 'top', 'stalai'), ('Nuleistos_lubos_1', 'bot', 'nul. lubos'),
       ('Pakabinamas_sviestuvas_1', 'bot', 'šviestuvai'), ('G_1variantas_lentyna1', 'top', 'stelažas'), ('Langas_remas_0', 'transom', 'langų virš.')],
 'C': [('Olive_Tree____Plant1', 'top', 'alyvmedis'), ('Armchair__4_2', 'top', 'fotelis'), ('Durys_staktos_0', 'door', 'durys'), ('Durys_vitrina_0', 'arch', 'arka')],
 'D': [('G_1variantas_lentyna1', 'top', 'stelažas'), ('G_82716_Mirror_Curve_Round_Copper_100cm1', 'bot', 'veidrodis'),
       ('Staliukas1_1', 'top', 'stalas'), ('Nuleistos_lubos_1', 'bot', 'nul. lubos'), ('Pakabinamas_sviestuvas_1', 'bot', 'šviestuvai')],
}
UAX = {'A': (0, 1), 'B': (0, -1), 'C': (1, 1), 'D': (1, -1)}
def urange(k, mn, mx):
    ax, sg = UAX[k]
    return (mn[ax], mx[ax]) if sg > 0 else (-mx[ax], -mn[ax])
for k in 'ABCD':
    d = D[k]; u0, u1 = VIEWS[k]['umin'], VIEWS[k]['umax']
    if k == 'B':   # facade seen from inside: masonry above/below openings is flush -> clip reveal corner lines to the opening height
        clips = [(-(sum(w[:2])/2+0.76), -(sum(w[:2])/2-0.76), META['win_z'][0], META['win_z'][1]) for w in META['windows']]
        clips.append((-(META['door']['x1']+0.16), -(META['door']['x0']-0.16), PODIUM, META['door']['spring']))
        def clipv(lst):
            out = []
            for item in lst:
                seg, dep = item
                (u1, v1), (u2, v2) = seg
                if abs(u1-u2) < 1e-3:
                    hit = [c for c in clips if c[0] <= u1 <= c[1]]
                    if hit:
                        _, _, z0, z1 = hit[0]; lo, hi = max(min(v1, v2), z0), min(max(v1, v2), z1)
                        if hi - lo > 0.005: out.append([[[u1, lo], [u1, hi]], dep])
                        continue
                out.append(item)
            return out
        d['vis'] = clipv(d['vis']); d['vis_win'] = clipv(d['vis_win'])
    poche(k, d['cut_shell']); add_lines(k, d['cut_obj'], 'A-PJUVIS-BALDAI')
    add_lines(k, d['cut_win'], 'A-LANGAI'); add_lines(k, [s for s, _ in d['vis_win']], 'A-LANGAI')
    add_lines(k, [s for s, dep in d['vis'] if dep < 2.6], 'A-MATOMOS-ARTI')
    add_lines(k, [s for s, dep in d['vis'] if dep >= 2.6], 'A-MATOMOS-TOLI')
    for b in d['blob']: msp.add_lwpolyline([P(k, *p) for p in b], close=True, dxfattribs=L('A-AUGALAI'))
    if k == 'A':
        t = msp.add_text('MARI', height=300, dxfattribs={'layer': 'A-MATOMOS-ARTI', 'style': TXT, 'width': 1.25}); t.set_placement(P(k, 8.73, 1.985), align=TA.MIDDLE_CENTER)
        t = msp.add_text('MADE', height=85, dxfattribs={'layer': 'A-MATOMOS-ARTI', 'style': TXT, 'width': 1.5}); t.set_placement(P(k, 8.73, 1.795), align=TA.MIDDLE_CENTER)
    if k == 'B':   # glass indication on window panes (two short diagonals)
        for (a, b, _, _) in META['windows']:
            for zc in (1.9, 3.5):
                for dd in (0, 0.12):
                    msp.add_line(P(k, -b+0.30+dd, zc-0.25), P(k, -b+0.62+dd, zc+0.15), dxfattribs={'layer': 'A-LANGAI', 'lineweight': 13})
    (x0, y0), (x1, y1) = P(k, u0, -0.30), P(k, u1, 0.0)
    h = msp.add_hatch(color=7, dxfattribs=L('A-PERDANGA-UZP')); h.set_pattern_fill('ANSI31', scale=25)
    h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs=L('A-PJUVIS-SIENOS'))
    # ---- levels at the edges
    marks = [(0.0, 'grindys', 'L'), (6.0, 'lubos', 'L')]
    if k in 'AC': marks.append((PODIUM, 'pakyla', 'L'))
    if k == 'B': marks.append((META['win_z'][0], 'palangė', 'L'))
    mid = (u0+u1)/2
    for nm, which, desc in LEV[k]:
        try: mn, mx = bb(nm)
        except ValueError: mn, mx = bbp(nm)
        a, b = urange(k, mn, mx)
        if b < u0 or a > u1: continue
        z = mx[2] if which == 'top' else mn[2]
        if which == 'transom': z = META['win_z'][1]
        if which == 'door': z = META['door']['leaf_top']
        if which == 'arch': z = META['door']['top']
        side = 'L' if (a+b)/2 < mid else 'R'
        if which == 'transom': side = 'L'
        marks.append((z, desc, side))
    for side in 'LR':
        cols = []
        for z, desc, sd in sorted([m for m in marks if m[2] == side]):
            for ci, last in enumerate(cols):
                if z - last >= 0.42: cols[ci] = z; break
            else: cols.append(z); ci = len(cols)-1
            edge = u0 if side == 'L' else u1
            level(k, edge + (-1 if side == 'L' else 1)*0.25, z, desc, side, col=ci*0.95)
    # ---- dimensions + axes
    hdim(k, -0.80, [u0, u1], 0.0)
    if k in 'AB':
        axs = [(lab, (x if k == 'A' else -x)) for lab, x in AXV.items()]
    else:
        axs = [(lab, (y if k == 'C' else -y)) for lab, y in AXH.items()]
    axs = [(lab, u) for lab, u in axs if u0-0.4 <= u <= u1+0.4 or True]
    for lab, u in axs:
        X, Y = P(k, u, -1.75)
        axis_bubble(X, Y, lab, X, Y+5*SCALE, X, P(k, 0, 6.35)[1])
    if len(axs) > 1:
        msp.add_multi_point_linear_dim(base=P(k, 0, -1.25), points=[P(k, u, 0) for _, u in sorted(axs, key=lambda a: a[1])], angle=0, dimstyle=DS, dxfattribs=L('A-MATMENYS'))
doc.saveas(OUTDXF)
json.dump({k: dict(VIEWS[k]) for k in VIEWS}, open(S + '/views2.json', 'w'))
print('saved', OUTDXF)
