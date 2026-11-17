# Furniture plan + sections 1-1..4-4 from the SketchUp model -> DXF model space (mm)
import sys, json, numpy as np, ezdxf
from ezdxf.enums import TextEntityAlignment as TA, MTextEntityAlignment as MA
from shapely.geometry import MultiLineString, LineString
from shapely.ops import polygonize, unary_union, linemerge
sys.path.insert(0, sys.argv[1] + '/scripts')
from dxf_common import *

S = sys.argv[1]; OUTDXF = sys.argv[2]
g = np.load(S + '/geo.npz'); V = g['V']; T = g['T']; O = g['O']; NAMES = list(g['names'])
def bb(name):
    P = V[T[O == NAMES.index(name)]].reshape(-1, 3); return P.min(0), P.max(0)

doc = ezdxf.new('R2018', setup=True); setup(doc); msp = doc.modelspace()
FLOOR_ABS = -2.0
# view placement: model-space mm = (u*1000+ox, v*1000+oy)
VIEWS = {
    'PLAN': dict(ox=0, oy=0, name='BALDŲ IŠDĖSTYMO PLANAS'),
    'A': dict(oy=-14000, name='PJŪVIS 1-1', num='1'),
    'B': dict(oy=-26000, name='PJŪVIS 2-2', num='2'),
    'C': dict(oy=-38000, name='PJŪVIS 3-3', num='3'),
    'D': dict(oy=-38000, name='PJŪVIS 4-4', num='4'),
}
D = {k: json.load(open(f'{S}/draw_{k}.json')) for k in VIEWS}
for k in 'ABCD':
    us = [p[0] for s in D[k]['cut_shell'] for p in s]
    VIEWS[k]['umin'] = min(us); VIEWS[k]['umax'] = max(us)
VIEWS['A']['ox'] = 2000 - VIEWS['A']['umin']*1000
VIEWS['B']['ox'] = 2000 - VIEWS['B']['umin']*1000
VIEWS['C']['ox'] = 2000 - VIEWS['C']['umin']*1000
VIEWS['D']['ox'] = 14000 - VIEWS['D']['umin']*1000
def P(k, u, v): return (u*1000 + VIEWS[k]['ox'], v*1000 + VIEWS[k]['oy'])

def add_lines(k, segs, layer, merge=True):
    if not segs: return
    ls = [LineString([tuple(np.round(np.array(P(k, *a)), 1)), tuple(np.round(np.array(P(k, *b)), 1))]) for a, b in segs if np.hypot(a[0]-b[0], a[1]-b[1]) > 1e-4]
    geom = linemerge(unary_union(ls)) if merge else MultiLineString(ls)
    parts = geom.geoms if hasattr(geom, 'geoms') else [geom]
    for p in parts:
        c = list(p.coords)
        if len(c) >= 2: msp.add_lwpolyline(c, dxfattribs={'layer': layer})

def poche(k, segs):
    ls = [LineString([P(k, *a), P(k, *b)]) for a, b in segs]
    u = unary_union(ls)
    polys = list(polygonize(u))
    for pg in polys:
        th = 2*pg.area/max(pg.length, 1)
        if th < 650 and pg.area > 2000:   # wall-like (thin) polygons only
            pg = pg.simplify(1.0)
            h = msp.add_hatch(color=7, dxfattribs={'layer': 'A-PJUVIS-SIENOS-UZP'})
            h.set_solid_fill(color=7, rgb=(150, 150, 150))
            h.paths.add_polyline_path(list(pg.exterior.coords), is_closed=True, flags=1)
            for it in pg.interiors: h.paths.add_polyline_path(list(it.coords), is_closed=True, flags=0)
    add_lines(k, segs, 'A-PJUVIS-SIENOS')

def mtext(s, x, y, h=2.5, layer='A-TEKSTAS', att=MA.MIDDLE_CENTER, mask=True, width=None, rot=0):
    m = msp.add_mtext(s, dxfattribs={'layer': layer, 'style': TXT, 'char_height': h*SCALE, 'rotation': rot})
    m.set_location((x, y), attachment_point=att)
    if width: m.dxf.width = width
    if mask: m.set_bg_color('canvas', scale=1.25)
    return m

def lvl(k, u, z, desc='', side='R', lead=None):
    """level mark at view coords (u, z-model-metres)"""
    x, y = P(k, u, z)
    s = SCALE; h = 2.6*s; w = 1.5*s
    msp.add_lwpolyline([(x, y), (x-w, y+h), (x+w, y+h)], close=True, dxfattribs={'layer': 'A-ALTITUDES'})
    hh = msp.add_hatch(color=7, dxfattribs={'layer': 'A-ALTITUDES'}); hh.paths.add_polyline_path([(x, y), (x, y+h), (x+w if side == 'R' else x-w, y+h)], is_closed=True)
    d = 1 if side == 'R' else -1
    val = fmt_level(z, FLOOR_ABS)
    L = lead or (len(val)*2.5*0.75 + 2.5)*s
    msp.add_line((x, y+h), (x+d*L, y+h), dxfattribs={'layer': 'A-ALTITUDES'})
    mtext(val, x+d*(w*0.4), y+h+0.5*s, 2.5, att=MA.BOTTOM_LEFT if d > 0 else MA.BOTTOM_RIGHT, mask=True)
    if desc: mtext(desc, x+d*(w+0.4*s), y+h-0.6*s, 1.8, att=MA.TOP_LEFT if d > 0 else MA.TOP_RIGHT, mask=True)

# ---------------------------------------------------------------- PLAN
k = 'PLAN'; d = D[k]
poche(k, d['cut_shell'])
add_lines(k, d['cut_obj'], 'A-PJUVIS-BALDAI')
near = [s for s, dep in d['vis'] if dep < 1.17]; far = [s for s, dep in d['vis'] if dep >= 1.17]
add_lines(k, near, 'A-MATOMOS-ARTI'); add_lines(k, far, 'A-MATOMOS-TOLI')
for b in d['blob']: msp.add_lwpolyline([P(k, *p) for p in b], close=True, dxfattribs={'layer': 'A-AUGALAI'})
for a in d['above']: msp.add_lwpolyline([P(k, *p) for p in a], close=True, dxfattribs={'layer': 'A-VIRS-PJUVIO'})
# labels
lab = [
    ('Recepcija', 8.70, 6.20), ('Prekių stalas\n1620×810', 15.39, 4.82), ('Prekių stalas\n1620×810', 13.13, 5.90), ('Prekių stalas\n1620×810', 11.20, 4.70),
    ('Drabužių pakaba', 8.65, 3.85), ('Drabužių pakaba', 11.44, 3.85), ('Drabužių pakaba', 14.32, 3.85),
    ('Stelažas su arkinėmis nišomis h=3060', 14.30, 7.15), ('Veidrodis Ø1000\nir lentyna', 16.55, 5.35),
    ('Kavos staliukai', 4.38, 6.02), ('Kilimas', 4.10, 3.30), ('Akcentinė siena\n(bordo tinkas)', 8.60, 7.60),
]
for s_, x, y in lab: mtext(s_, *P(k, x, y), 2.2)
def leader(s_, lx, ly, tx, ty, att=MA.MIDDLE_LEFT):
    msp.add_line(P(k, tx, ty), P(k, lx, ly), dxfattribs={'layer': 'A-MATMENYS'})
    c = msp.add_circle(P(k, tx, ty), radius=0.5*SCALE, dxfattribs={'layer': 'A-MATMENYS'})
    hh = msp.add_hatch(color=7, dxfattribs={'layer': 'A-MATMENYS'}); hh.paths.add_edge_path().add_arc(P(k, tx, ty), 0.5*SCALE, 0, 360)
    off = 0.06 if att == MA.MIDDLE_LEFT else -0.06
    mtext(s_, *P(k, lx+off, ly), 2.2, att=att)
leader('Fotelis', 3.05, 5.52, 3.31, 5.95, MA.MIDDLE_LEFT)
leader('Fotelis', 5.62, 7.62, 5.05, 7.62, MA.MIDDLE_LEFT)
leader('Alyvmedis vazone', 5.62, 7.15, 3.80, 7.20, MA.MIDDLE_LEFT)
mtext('PREKYBOS SALĖ', *P(k, 13.25, 4.70), 3.5)
mtext('POILSIO ZONA\nANT PAKYLOS', *P(k, 4.10, 4.75), 3.5)
def lvl_box(val, x, y):
    X, Y = P(k, x, y); w = len(val)*2.5*0.62*SCALE + 1.6*SCALE; h = 2.5*SCALE + 1.6*SCALE
    msp.add_lwpolyline([(X-w/2, Y-h/2), (X+w/2, Y-h/2), (X+w/2, Y+h/2), (X-w/2, Y+h/2)], close=True, dxfattribs={'layer': 'A-ALTITUDES'})
    mtext(val, X, Y, 2.5, mask=True)
lvl_box('-2,000', 13.25, 4.25); lvl_box('-1,550', 4.10, 4.25); lvl_box('-2,000', 7.00, 5.20)
mtext('Laipteliai 3×150', *P(k, 5.74, 4.6), 1.8, rot=90)
# dimensions
ds = 'ISO-50'; dl = {'layer': 'A-MATMENYS'}
fac = [1.839, 3.560, 5.310, 6.665, 7.857, 9.465, 10.654, 12.263, 13.465, 15.128, 16.303, 17.937]
msp.add_multi_point_linear_dim(base=P(k, 0, 0.95), points=[P(k, x, 1.75) for x in fac], angle=0, dimstyle=ds, dxfattribs=dl)
msp.add_linear_dim(base=P(k, 0, 0.45), p1=P(k, 1.839, 1.75), p2=P(k, 17.937, 1.75), angle=0, dimstyle=ds, dxfattribs=dl).render()
msp.add_linear_dim(base=P(k, 0, 8.75), p1=P(k, 2.833, 7.955), p2=P(k, 17.886, 7.955), angle=0, dimstyle=ds, dxfattribs=dl).render()
msp.add_multi_point_linear_dim(base=P(k, 0, 8.40), points=[P(k, x, 7.955) for x in [2.833, 5.53, 6.34, 6.785, 10.366, 17.886]], angle=0, dimstyle=ds, dxfattribs=dl)
msp.add_linear_dim(base=P(k, 18.75, 0), p1=P(k, 17.886, 2.646), p2=P(k, 17.886, 7.955), angle=90, dimstyle=ds, dxfattribs=dl).render()
msp.add_multi_point_linear_dim(base=P(k, 1.15, 0), points=[P(k, 1.839, y) for y in [1.694, 2.708, 8.058]], angle=90, dimstyle=ds, dxfattribs=dl)
# section markers
def sec_marker(num, horiz, c, direction):
    s = SCALE
    if horiz:
        ends = [(0.75, c), (19.0, c)]; dv = (0, direction)
    else:
        ends = [(c, 0.55), (c, 9.25)]; dv = (direction, 0)
    for (x, y) in ends:
        X, Y = P(k, x, y)
        if horiz: msp.add_line((X-4*s, Y), (X+4*s, Y), dxfattribs={'layer': 'A-PJUVIO-ZYMES'})
        else: msp.add_line((X, Y-4*s), (X, Y+4*s), dxfattribs={'layer': 'A-PJUVIO-ZYMES'})
        ax, ay = X+dv[0]*6*s, Y+dv[1]*6*s
        msp.add_line((X, Y), (ax, ay), dxfattribs={'layer': 'A-MATMENYS'})
        px, py = -dv[1], dv[0]
        hd = msp.add_hatch(color=7, dxfattribs={'layer': 'A-PJUVIO-ZYMES'})
        hd.paths.add_polyline_path([(ax+dv[0]*1.8*s, ay+dv[1]*1.8*s), (ax+px*1.0*s, ay+py*1.0*s), (ax-px*1.0*s, ay-py*1.0*s)], is_closed=True)
        tx, ty = X+dv[0]*3*s + (px*3.2*s if horiz else 0), Y+dv[1]*3*s + (0 if horiz else py*3.2*s)
        if horiz: tx = X + (-3.5*s if x < 5 else 3.5*s)
        else: ty = Y + (-3.5*s if y < 5 else 3.5*s)
        mtext(num, tx, ty, 5.0, layer='A-PJUVIO-ZYMES', mask=False)
sec_marker('1', True, 5.35, +1); sec_marker('2', True, 4.00, -1); sec_marker('3', False, 6.00, -1); sec_marker('4', False, 14.25, +1)
mtext('h pjūvio = 1200 mm nuo grindų', *P(k, 2.0, 9.25), 1.8, att=MA.MIDDLE_LEFT, mask=False)

# ---------------------------------------------------------------- SECTIONS
SEC_LEVELS = {   # (object, top/bot, description, side of object where the mark goes)
 'A': [('Recepcijos_stalvir_is1','top','recepcijos stalviršis','R'), ('Staliukas1_1','top','prekių stalai','R'), ('G_1variantas_lentyna1','top','stelažo viršus','L'),
       ('Nuleidimas1_1','bot','nuleistų lubų el. apačia','R'), ('Neleidimas3_1','bot','nuleistų lubų el. apačia','R'), ('MARY_MADE_1_1','bot','logotipo apačia','R'),
       ('Olive_Tree____Plant1','top','alyvmedžio viršus','R')],
 'B': [('Componente1','top','pakabų viršus','R'), ('Nuleidimas1_1','bot','nuleistų lubų el. apačia','R'), ('Nuleidimas1_1','top','nuleistų lubų el. viršus','L'),
       ('G_1variantas_lentyna1','top','stelažo viršus','L')],
 'C': [('Olive_Tree____Plant1','top','alyvmedžio viršus','L'), ('Armchair__4_2','top','fotelio atlošas','R')],
 'D': [('G_1variantas_lentyna1','top','stelažo viršus','L'), ('G_82716_Mirror_Curve_Round_Copper_100cm1','bot','veidrodžio apačia','L'), ('Staliukas1_1','top','prekių stalas','R'), ('Neleidimas3_1','bot','nuleistų lubų el. apačia','R')],
}
def urange(k, mn, mx):
    if k == 'A': return mn[0], mx[0]
    if k == 'B': return -mx[0], -mn[0]
    if k == 'C': return mn[1], mx[1]
    return -mx[1], -mn[1]
for k in 'ABCD':
    d = D[k]
    poche(k, d['cut_shell']); add_lines(k, d['cut_obj'], 'A-PJUVIS-BALDAI')
    add_lines(k, [s for s, dep in d['vis'] if dep < 2.6], 'A-MATOMOS-ARTI')
    add_lines(k, [s for s, dep in d['vis'] if dep >= 2.6], 'A-MATOMOS-TOLI')
    for b in d['blob']: msp.add_lwpolyline([P(k, *p) for p in b], close=True, dxfattribs={'layer': 'A-AUGALAI'})
    u0, u1 = VIEWS[k]['umin'], VIEWS[k]['umax']
    (x0, y0), (x1, y1) = P(k, u0, -0.30), P(k, u1, 0.0)
    h = msp.add_hatch(color=7, dxfattribs={'layer': 'A-PERDANGA-UZP'}); h.set_pattern_fill('ANSI31', scale=25)
    h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={'layer': 'A-PJUVIS-SIENOS'})
    main = [(0.0, 'grindys'), (6.0, 'lubos')]
    if k in 'AC': main.insert(1, (0.45, 'pakyla'))
    if k == 'B': main.insert(1, (0.90, 'palangė'))
    for z, ds_ in main: lvl(k, u0-0.20, z, ds_, side='L')
    for nm, which, desc, side in SEC_LEVELS[k]:
        mn, mx = bb(nm); z = mx[2] if which == 'top' else mn[2]
        a, b = urange(k, mn, mx)
        if a > u1 or b < u0: continue
        a, b = max(a, u0), min(b, u1)
        lvl(k, (b + 0.06) if side == 'R' else (a - 0.06), z, desc, side=side)
    if k == 'A':
        t = msp.add_text('MARI', height=300, dxfattribs={'layer': 'A-MATOMOS-ARTI', 'style': TXT, 'width': 1.25}); t.set_placement(P(k, 8.73, 1.98), align=TA.MIDDLE_CENTER)
        t = msp.add_text('MADE', height=85, dxfattribs={'layer': 'A-MATOMOS-ARTI', 'style': TXT, 'width': 1.5}); t.set_placement(P(k, 8.73, 1.72), align=TA.MIDDLE_CENTER)
    dl = {'layer': 'A-MATMENYS'}
    msp.add_linear_dim(base=P(k, 0, -0.85), p1=P(k, u0, 0), p2=P(k, u1, 0), angle=0, dimstyle='ISO-50', dxfattribs=dl).render()

doc.saveas(OUTDXF)
json.dump({k: {kk: v for kk, v in VIEWS[k].items()} for k in VIEWS}, open(S + '/views.json', 'w'))
print('saved', OUTDXF)
