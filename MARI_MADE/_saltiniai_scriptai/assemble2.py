# v2: standardised DXFs, A3 1:50 sheets (plans split in 4), no colours, standard axes, centred ceiling discs, PDFs
import sys, os, json, math, ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44, Vec3
from ezdxf.enums import TextEntityAlignment as TA
S = sys.argv[1]; STAMP = sys.argv[2] == 'stamp'; OUT = sys.argv[3]
sys.path.insert(0, S + '/scripts')
from dxf_common import *
os.makedirs(OUT, exist_ok=True)
NSHEETS = 9
INFO = dict(objektas='Prekybos centras GO9, Gedimino pr. 9, Vilnius', patalpa='Parduotuvė MARI MADE – interjero projektas',
            uzsakovas='Vilniaus dizaino kolegija', stadija='Interjero projektas', atliko='Gabrielė Meilūnaitė',
            tikrino='', data='2026-11', mastelis='1:50', lapu=NSHEETS)
META = json.load(open(S + '/geo2_meta.json'))
LW = {'Esamos sienos': 50, 'Langai': 25, 'asys': 18, 'Durys': 25, 'kolonos': 50, 'stiklas': 13, 'evakuacija': 35,
      'konturas': 25, 'Pertvaros': 50, 'Textas bendras': 25, 'Sienu haxas': 13, 'HACAS': 13, '0.5': 25,
      '0-statramsciai': 25, '_Metalines konstr': 35, 'A-73----E--': 18, 'A-43CB--E-N': 35, 'A-45CE--E--': 18,
      'A-45CE--E-N': 18, 'a-scianki': 25, 'B-HATCH': 13, 'Sutartiniai žymėjimai.': 50, '0': 25, 'GRIAUNAMA': 35, '000': 13, '00': 13}
TYPO = {'IEJIMAS': 'ĮĖJIMAS', 'IĖJIMAS': 'ĮĖJIMAS', 'ĮEJIMAS': 'ĮĖJIMAS', 'ILEIDŽIAMI': 'ĮLEIDŽIAMI', 'LAUKO DURIS': 'LAUKO DURYS',
        'GIPSINE SIENA': 'GIPSINĖ SIENA', 'GIPSO KARTONOS': 'GIPSO KARTONO', 'Į PATALPA': 'Į PATALPĄ', 'TŪRĖKLAS': 'TURĖKLAS'}
GRAYS = {8, 9, 250, 251, 252, 253, 254, 255}
def fix(s):
    for a, b in TYPO.items(): s = s.replace(a, b)
    return s

def decolour(doc):
    for l in doc.layers:
        if l.color not in GRAYS: l.color = 7
        if l.dxf.hasattr('true_color'): l.dxf.discard('true_color')
    for lay in [doc.modelspace()] + list(doc.blocks):
        for e in lay:
            if e.dxf.hasattr('true_color'): e.dxf.discard('true_color')
            if e.dxftype() == 'HATCH':
                if e.has_solid_fill:
                    c = e.dxf.get('color', 256)
                    e.dxf.color = c if (c in GRAYS or c in (0, 7, 256)) else 254
                else: e.dxf.color = 256
            elif e.dxf.hasattr('color') and e.dxf.color not in (0, 256) and e.dxf.color not in GRAYS:
                e.dxf.color = 256
            if e.dxftype() == 'MTEXT':
                import re
                e.text = re.sub(r'\\C\d+;', '', re.sub(r'\\c\d+;', '', e.text))

def standardise(doc):
    setup(doc)
    for n, lw in LW.items():
        if n in doc.layers: doc.layers.get(n).dxf.lineweight = lw
    for l in doc.layers:
        if l.dxf.lineweight == -3: l.dxf.lineweight = 25
    for lay in [doc.modelspace()] + [b for b in doc.blocks if not b.name.lower().startswith('*paper')]:
        inblock = lay is not doc.modelspace()
        for e in lay:
            if e.dxf.hasattr('lineweight') and e.dxf.lineweight != -1: e.dxf.lineweight = -1
            if inblock and e.dxftype() == 'ARC': e.dxf.lineweight = 13      # door swing arcs: thin (ISO 7519)
            if e.dxftype() == 'MTEXT': e.text = fix(e.text)
            if e.dxftype() == 'TEXT': e.dxf.text = fix(e.dxf.text)
    decolour(doc)
    doc.header['$LWDISPLAY'] = 1

AXMAP = {'1E': '1', '1': '2', '2': '3', '3': '4', 'AE': 'A', 'A': 'B', 'B': 'C'}
def fix_axes(msp):
    """rename axes (digits L->R, letters bottom->top), uniform bubbles Ø10 mm, ISO chain lines"""
    seen = set()
    for a in list(msp.query('ARC[layer=="asys"]')):
        msp.add_circle(a.dxf.center, 384, dxfattribs={'layer': 'asys'}); msp.delete_entity(a)
    circles = [e for e in msp.query('CIRCLE[layer=="asys"]')]
    for t in list(msp.query('TEXT[layer=="asys"]')):
        old = t.dxf.text.strip()
        if old not in AXMAP: continue
        c = min(circles, key=lambda c: (c.dxf.center - t.dxf.insert).magnitude) if circles else None
        if c is None or (c.dxf.center - t.dxf.insert).magnitude > 800: continue
        key = (round(c.dxf.center.x), round(c.dxf.center.y))
        if key in seen: msp.delete_entity(t); continue
        seen.add(key)
        t.dxf.text = AXMAP[old]; t.dxf.height = 5*SCALE; t.dxf.style = TXT; t.dxf.layer = 'A-TEKSTAS'
        t.set_placement(c.dxf.center, align=TA.MIDDLE_CENTER)
        c.dxf.radius = 5*SCALE; c.dxf.layer = 'A-ASYS-ZYM'
    for e in msp.query('LINE[layer=="asys"]'):
        e.dxf.linetype = 'A-ASIS'; e.dxf.ltscale = 1.0

def add_axes(msp, ax_v, ax_h, ybub, xbub, ytop, xright):
    if 'A-ASYS' not in msp.doc.layers: msp.doc.layers.add('A-ASYS', color=7, lineweight=18, linetype='A-ASIS')
    if 'A-ASYS-ZYM' not in msp.doc.layers: msp.doc.layers.add('A-ASYS-ZYM', color=7, lineweight=25)
    for e in list(msp.query('LINE[layer=="asys"]')): msp.delete_entity(e)
    r = 5*SCALE
    for lab, x in ax_v.items():
        msp.add_line((x, ybub+r), (x, ytop), dxfattribs={'layer': 'A-ASYS'})
        msp.add_circle((x, ybub), r, dxfattribs={'layer': 'A-ASYS-ZYM'})
        t = msp.add_text(lab, height=5*SCALE, dxfattribs={'layer': 'A-TEKSTAS', 'style': TXT}); t.set_placement((x, ybub), align=TA.MIDDLE_CENTER)
    for lab, y in ax_h.items():
        msp.add_line((xbub+r, y), (xright, y), dxfattribs={'layer': 'A-ASYS'})
        msp.add_circle((xbub, y), r, dxfattribs={'layer': 'A-ASYS-ZYM'})
        t = msp.add_text(lab, height=5*SCALE, dxfattribs={'layer': 'A-TEKSTAS', 'style': TXT}); t.set_placement((xbub, y), align=TA.MIDDLE_CENTER)

def in_box(e, x0, y0, x1, y1):
    b = bbox.extents([e], fast=True)
    return b.has_data and b.extmin.x >= x0 and b.extmax.x <= x1 and b.extmin.y >= y0 and b.extmax.y <= y1
def collect(msp, box): return [e for e in msp if in_box(e, *box)]
def is_text(e): return e.dxftype() in ('TEXT', 'MTEXT')

def to_paper(psp, ents, cx, cy, maxw, maxh):
    b = bbox.extents(ents, fast=True)
    w, h = b.size.x or 1, b.size.y or 1
    s = min(maxw/w, maxh/h, 1/SCALE*1.6)
    m = Matrix44.translate(-b.center.x, -b.center.y, 0) @ Matrix44.scale(s, s, s) @ Matrix44.translate(cx, cy, 0)
    for e in ents:
        try:
            c = e.copy(); c.transform(m); psp.add_entity(c)
            try: c.dxf.ltscale = e.dxf.get('ltscale', 1.0) * s
            except Exception: pass
        except Exception as ex: print('skip', e.dxftype(), ex)

def table(psp, x, ytop, title, header, rows, colw, rowh=9.0):
    W = sum(colw); y = ytop
    Ln = lambda a, b, lay='A-LENTELES': psp.add_line(a, b, dxfattribs={'layer': lay})
    def put(s, xx, yy, h=2.5, al=TA.MIDDLE_LEFT):
        t = psp.add_text(s, height=h, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((xx, yy), align=al)
    put(title, x+2, y-5, 3.5); y -= 10; Ln((x, y), (x+W, y), 'A-LENTELES-REMAS')
    xs = [x]; [xs.append(xs[-1]+c) for c in colw]
    for i, hd in enumerate(header): put(hd, xs[i]+2, y-3.75, 2.5)
    y -= 7.5; Ln((x, y), (x+W, y), 'A-LENTELES-REMAS')
    for r in rows:
        sym, desc = r[0], r[1]
        nl = desc.count('\n') + 1; rh = max(rowh, 4.6*nl + 3.4); cy = y - rh/2
        if isinstance(sym, str): put(sym, xs[0]+colw[0]/2, cy, 2.5, TA.MIDDLE_CENTER)
        else: to_paper(psp, sym, xs[0]+colw[0]/2, cy, colw[0]*0.8, rh*0.65)
        for k, line in enumerate(desc.split('\n')): put(line, xs[1]+2, cy + (nl-1)*2.3 - k*4.6, 2.5)
        for j, extra in enumerate(r[2:]): put(str(extra), xs[2+j]+colw[2+j]/2, cy, 2.5, TA.MIDDLE_CENTER)
        y -= rh; Ln((x, y), (x+W, y))
    for xx in xs[1:-1]: Ln((xx, ytop-10), (xx, y))
    psp.add_lwpolyline([(x, ytop), (x+W, ytop), (x+W, y), (x, y)], close=True, dxfattribs={'layer': 'A-LENTELES-REMAS'})
    return y

def sheet(doc, name, lapas, title, vps, tables_fn=None, sub_titles=None, extra=None, fmt='A3', own_stamp=False):
    psp = new_layout(doc, name, fmt)
    for old in ('Layout1', 'Layout2'):
        if old in doc.layouts.names():
            try: doc.layouts.delete(old)
            except Exception: pass
    frame(psp, fmt)
    for (cx, cy, w, h, mcx, mcy) in vps: viewport(psp, cx, cy, w, h, mcx, mcy)
    if STAMP and not own_stamp: title_block(psp, fmt, dict(INFO, brezinys=title, lapas=lapas))
    elif own_stamp: pass
    else:
        t = psp.add_text(f'{lapas}', height=3.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((PAPER[fmt][0]-14, 14), align=TA.MIDDLE_CENTER)
    for (x, y, s) in (sub_titles or []): sheet_title(psp, x, y, s)
    if tables_fn: tables_fn(psp)
    if extra: extra(psp)
    return psp

def ext_of(msp, flt=lambda e: True):
    es = [e for e in msp if flt(e)]
    return bbox.extents([e for e in es if bbox.extents([e], fast=True).has_data], fast=True)

SHEETS = []
# =============================================================== 1-8  GRIOVIMO / NAUJAS : 4 x A3 each
def plan_A1(fn, lap, title, sut_rows, eks_rows, sut_box, eks_box, outname):
    doc = ezdxf.readfile(f'{S}/dxf_in/{fn}.dxf'); msp = doc.modelspace(); standardise(doc)
    for n, (c, lw, lt) in {'A-ASYS': (7, 18, 'A-ASIS'), 'A-ASYS-ZYM': (7, 25, 'Continuous')}.items():
        if n not in doc.layers: doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
    if fn == 'GRIOVIMO_PLANAS':
        # demolished / dismantled elements (dashed) -> own layer 0.35, clearly heavier than stair treads (0.18)
        if 'A-GRIAUNAMA' not in doc.layers: doc.layers.add('A-GRIAUNAMA', color=7, lineweight=35)
        nd = 0
        for e in msp:
            lt = e.dxf.get('linetype', 'BYLAYER')
            if lt in ('DASHED', 'DASHDOT', 'DGN Style 3') and e.dxf.layer not in ('asys', 'A-ASYS'):
                e.dxf.layer = 'A-GRIAUNAMA'; nd += 1
        print('demolition entities', nd)
    fix_axes(msp)
    sut_all = collect(msp, sut_box[:4]); eks_all = collect(msp, eks_box[:4])
    srows = []
    for (y0, y1, text) in sut_rows:
        sym = [e.copy() for e in sut_all if y0 <= bbox.extents([e], fast=True).center.y <= y1 and bbox.extents([e], fast=True).extmax.x < sut_box[4]]
        srows.append((sym, text))
    for e in sut_all + eks_all:
        if e.is_alive: msp.delete_entity(e)
    E = ext_of(msp, lambda e: bbox.extents([e], fast=True).has_data and 100000 < bbox.extents([e], fast=True).extmin.x and bbox.extents([e], fast=True).extmax.x < 140000
               and 40000 < bbox.extents([e], fast=True).extmin.y and bbox.extents([e], fast=True).extmax.y < 70000)
    vw, vh = E.size.x/SCALE + 10, E.size.y/SCALE + 10
    VX, VY = 25 + vw/2, 297 + 10
    def tabs(psp):
        tx = 841 - 10 - 8 - 250
        y = table(psp, tx, 576, 'SUTARTINIAI ŽYMĖJIMAI', ['Žymėjimas', 'Aprašymas'], srows, [40, 210], rowh=11)
        y = table(psp, tx, y-10, 'EKSPLIKACIJA', ['Nr.', 'Pavadinimas'], eks_rows, [16, 234], rowh=9)
        if STAMP: title_block(psp, 'A1', dict(INFO, brezinys=title, lapas=lap), y0=y-12-TB_H, x0=tx, w=250)
        else:
            t = psp.add_text(f'{lap}', height=3.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((841-14, 14), align=TA.MIDDLE_CENTER)
    sheet(doc, f'{lap:02d}_{title}', lap, title, [(VX, VY, vw, vh, E.center.x, E.center.y)], tabs,
          sub_titles=[(25, VY - vh/2 - 14, title)], fmt='A1', own_stamp=True)
    p = f'{OUT}/{outname}.dxf'; doc.saveas(p); SHEETS.append((p, f'{lap:02d}_{title}'))

plan_A1('GRIOVIMO_PLANAS', 1, 'GRIOVIMO PLANAS',
    [(63000, 63350, 'ESAMOS SIENOS IR LAIKANČIOS KONSTRUKCIJOS'),
     (62350, 62700, 'UŽDAROMAS VIDINIS ĮĖJIMAS'), (61750, 62100, 'DEMONTUOJAMOS STIKLINĖS PERTVAROS'), (61200, 61600, 'DEMONTUOJAMI LAIPTAI'),
     (60350, 60950, 'ESAMAS ĮĖJIMAS'), (59400, 60250, 'ESAMOS LAUKO DURYS'), (58550, 59100, 'GRINDŲ ALTITUDĖ')],
    [('1', 'ESAMI LAIPTAI'), ('2', 'ESAMAS LIFTAS'), ('3', 'ESAMA VENTILIACIJOS ŠACHTA'), ('4', 'ESAMAS TURĖKLAS / BALKONAS'),
     ('5', 'ESAMA STIKLO VIDINĖ VITRINA / DEMONTUOJAMA'), ('6', 'ESAMOS LAUKO DURYS'), ('7', 'ESAMAS VIDINIS ĮĖJIMAS / DEMONTUOJAMAS')],
    (135400, 58400, 149000, 65200, 140800), (135400, 51500, 149000, 57500), 'GRIOVIMO_PLANAS')
plan_A1('NAUJAS_PLANAVIMAS', 2, 'NAUJAS IŠPLANAVIMAS',
    [(62000, 63300, 'PASIRINKTA ERDVĖ'), (61300, 61800, 'NAUJOS PERTVAROS'), (60600, 61100, 'UŽDAROMAS ĮĖJIMAS / VIENTISA GIPSO KARTONO SIENA'),
     (59700, 60400, 'ĮĖJIMAI Į PATALPĄ'), (58800, 59500, 'GRINDŲ ALTITUDĖ')],
    [('1', 'NAUJA PERTVARA / ATSKIRIAMOS PATALPOS'), ('2', 'UŽDAROMAS VIDINIS ĮĖJIMAS / MONTUOJAMA GIPSINĖ SIENA')],
    (134300, 58700, 146000, 65000, 137450), (134300, 55500, 146000, 58300), 'NAUJAS_ISPLANAVIMAS')

# =============================================================== helpers for store plans (LUBU / SVIESTUVU)
def m2d(xm, ym, X0, Y0):   # model metres -> drawing mm (translation only)
    return ((xm-1.839)*1000 + X0, (ym-1.694)*1000 + Y0)
TB = META['tables']; R_DISC = 825
def recentre_discs(msp, X0, Y0):
    """move the 3 dropped-ceiling circles (and their hatch islands / pendant symbols) over the table centres, Ø1650"""
    new = [m2d(*TB[n], X0, Y0) for n in ['Staliukas3_1', 'Staliukas2_1', 'Staliukas1_1']]
    circ = sorted([c for c in msp.query('CIRCLE') if 900 < c.dxf.radius < 1200], key=lambda c: c.dxf.center.x)
    oldc = [Vec3(c.dxf.center) for c in circ]
    for c, (x, y) in zip(circ, new): c.dxf.center = (x, y); c.dxf.radius = R_DISC
    def nearest(p):
        i = min(range(len(oldc)), key=lambda i: (oldc[i]-p).magnitude); return i
    # pendant rectangles (LWPOLYLINE ~934 long) -> move by the same delta as their circle
    for pl in msp.query('LWPOLYLINE'):
        b = bbox.extents([pl], fast=True)
        if 800 < b.size.x < 1100 and b.size.y < 200 and oldc:
            i = nearest(b.center)
            if (oldc[i]-b.center).magnitude < 1200:
                dx, dy = new[i][0]-oldc[i].x, new[i][1]-oldc[i].y; pl.translate(dx, dy, 0)
    for h in list(msp.query('HATCH')):
        changed = False
        for path in h.paths:
            if hasattr(path, 'edges'):
                for ed in path.edges:
                    if ed.type == 2 and 900 < ed.radius < 1200 and oldc:   # ArcEdge (circle island)
                        i = nearest(Vec3(ed.center)); ed.center = new[i]; ed.radius = R_DISC; changed = True
            elif hasattr(path, 'vertices'):
                b = [Vec3(v[0], v[1]) for v in path.vertices]
                if b:
                    xs = [v.x for v in b]; ys = [v.y for v in b]
                    if 800 < max(xs)-min(xs) < 1100 and max(ys)-min(ys) < 200:
                        cc = Vec3((max(xs)+min(xs))/2, (max(ys)+min(ys))/2); i = nearest(cc)
                        if (oldc[i]-cc).magnitude < 1200:
                            dx, dy = new[i][0]-oldc[i].x, new[i][1]-oldc[i].y
                            path.vertices = [(v[0]+dx, v[1]+dy, *v[2:]) for v in path.vertices]
    return new

def remove_lines(msp, segs):
    n = 0
    for e in list(msp.query('LINE')):
        a, b = e.dxf.start, e.dxf.end
        for p0, p1 in segs:
            if (abs(a.x-p0[0]) < 3 and abs(a.y-p0[1]) < 3 and abs(b.x-p1[0]) < 3 and abs(b.y-p1[1]) < 3) or \
               (abs(b.x-p0[0]) < 3 and abs(b.y-p0[1]) < 3 and abs(a.x-p1[0]) < 3 and abs(a.y-p1[1]) < 3):
                msp.delete_entity(e); n += 1; break
    return n

def fixture_dims(msp, pts, X0, Y0, top_y, right_x, discs=None):
    """locate fixtures: chain along the top (x) and on the right (y), from inner wall faces"""
    xl, xr = m2d(2.833, 0, X0, Y0)[0], m2d(17.886, 0, X0, Y0)[0]
    yf, yb = m2d(0, 2.708, X0, Y0)[1], m2d(0, 7.955, X0, Y0)[1]
    xs = sorted(set(round(p[0]/5)*5 for p in pts)); ys = sorted(set(round(p[1]/5)*5 for p in pts))
    dl = {'layer': 'A-MATMENYS'}
    if top_y is not None:
        msp.add_multi_point_linear_dim(base=(0, top_y), points=[(x, yb) for x in [xl]+xs+[xr]], angle=0, dimstyle='ISO-50', dxfattribs=dl)
    if discs:
        dx = sorted(set(round(p[0]/5)*5 for p in discs))
        msp.add_multi_point_linear_dim(base=(0, m2d(0, 3.20, X0, Y0)[1]), points=[(x, yf) for x in [xl]+dx+[xr]], angle=0, dimstyle='ISO-50', dxfattribs=dl)
    msp.add_multi_point_linear_dim(base=(m2d(17.45, 0, X0, Y0)[0], 0), points=[(xr, y) for y in [yf]+ys+[yb]], angle=90, dimstyle='ISO-50', dxfattribs=dl)

def store_axes(msp, X0, Y0):
    AXV = {'1': 1.770, '2': 4.917, '3': 12.917}; AXH = {'A': 1.684, 'B': 8.791}
    av = {k: m2d(v, 0, X0, Y0)[0] for k, v in AXV.items()}; ah = {k: m2d(0, v, X0, Y0)[1] for k, v in AXH.items()}
    yb = Y0 - 2300; xb = X0 - 2200
    add_axes(msp, av, ah, yb, xb, ah['B'] + 300, m2d(18.3, 0, X0, Y0)[0])
    dl = {'layer': 'A-MATMENYS'}
    msp.add_multi_point_linear_dim(base=(0, yb + 700), points=[(av[k], ah['A']) for k in '123'], angle=0, dimstyle='ISO-50', dxfattribs=dl)
    msp.add_linear_dim(base=(xb + 700, 0), p1=(av['1'], ah['A']), p2=(av['1'], ah['B']), angle=90, dimstyle='ISO-50', dxfattribs=dl).render()

# =============================================================== 9 LUBU
doc = ezdxf.readfile(f'{S}/dxf_in/LUBU_PLANAS.dxf'); msp = doc.modelspace(); standardise(doc)
for n, (c, lw, lt) in {'A-ASYS': (7, 18, 'A-ASIS'), 'A-ASYS-ZYM': (7, 25, 'Continuous')}.items():
    if n not in doc.layers: doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
X0, Y0 = 2060.8, 1413.3
for e in list(msp.query('MTEXT')):
    if 'PLANAS' in e.plain_text(): msp.delete_entity(e)
for e in list(msp.query('MULTILEADER')): msp.delete_entity(e)
remove_lines(msp, [((10800, 7374), (17809, 7381)), ((10800, 7374), (10800, 7674)), ((17780, 2396), (18080, 2399)), ((17780, 2396), (17809, 7381))])
discs = recentre_discs(msp, X0, Y0)
hatches = [e for e in msp.query('HATCH') if e.dxf.layer == '0']
def hatch_sample(h):
    c = h.copy(); c.paths.clear(); x, y = -50000, -50000
    c.paths.add_polyline_path([(x, y), (x+1500, y), (x+1500, y+700), (x, y+700)], is_closed=True)
    r = ezdxf.entities.LWPolyline.new(dxfattribs={'layer': 'A-LENTELES'}); r.set_points([(x, y), (x+1500, y), (x+1500, y+700), (x, y+700)]); r.closed = True
    return [c, r]
smp = [hatch_sample(h) for h in sorted(hatches, key=lambda h: -bbox.extents([h]).size.x)]
store_axes(msp, X0, Y0)
fixture_dims(msp, discs, X0, Y0, None, None, discs=discs)
E = ext_of(msp, lambda e: bbox.extents([e], fast=True).has_data and abs(bbox.extents([e], fast=True).center.x) < 30000 and abs(bbox.extents([e], fast=True).center.y) < 30000)
def tabs9(psp):
    rows = [(smp[0], 'DAŽYTOS LUBOS, RAL 1013 OYSTER WHITE, h=+4,000'), (smp[1], 'NULEISTOS LUBOS – APVALŪS ELEMENTAI\nØ1650, STORIS 150, h=+3,850')]
    table(psp, 25, 58, 'SUTARTINIAI ŽYMĖJIMAI', ['Žymėjimas', 'Aprašymas'], rows, [28, 170], rowh=11)
vw, vh = E.size.x/SCALE + 6, E.size.y/SCALE + 6
sheet(doc, '03_LUBU PLANAS', 3, 'LUBŲ PLANAS', [(215, 284-vh/2, vw, vh, E.center.x, E.center.y)], tabs9, sub_titles=[(25, 63, 'LUBŲ PLANAS')])
print('LUBU vp', round(vw), round(vh))
p = f'{OUT}/LUBU_PLANAS.dxf'; doc.saveas(p); SHEETS.append((p, '03_LUBU PLANAS'))

# =============================================================== 10 SVIESTUVU
doc = ezdxf.readfile(f'{S}/dxf_in/VIESTUVU_PLANAS.dxf'); msp = doc.modelspace(); standardise(doc)
for n, (c, lw, lt) in {'A-ASYS': (7, 18, 'A-ASIS'), 'A-ASYS-ZYM': (7, 25, 'Continuous'), 'E-SVIESTUVAI': (7, 25, 'Continuous')}.items():
    if n not in doc.layers: doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
X0, Y0 = 3523.7, 2191.2
remove_lines(msp, [((12263, 8152), (12263, 8452)), ((12263, 8152), (19272, 8159)), ((19243, 3174), (19543, 3177)), ((19243, 3174), (19272, 8159))])
leg = collect(msp, (6900, -3900, 13200, 1400))
pick = lambda y0, y1: [e.copy() for e in leg if not is_text(e) and y0 < bbox.extents([e]).center.y < y1 and bbox.extents([e]).extmax.x < 8500]
sym1, sym2, sym3 = pick(-800, -50), pick(-1600, -1300), pick(-2800, -2550)
for e in leg: msp.delete_entity(e)
for e in list(msp.query('MTEXT')):
    if 'PLANAS' in e.plain_text(): msp.delete_entity(e)
discs = recentre_discs(msp, X0, Y0)
for e in msp:
    if e.dxf.layer == '0' and e.dxftype() in ('CIRCLE', 'HATCH', 'LWPOLYLINE'): e.dxf.layer = 'E-SVIESTUVAI'
down = [Vec3(c.dxf.center) for c in msp.query('CIRCLE') if 450 < c.dxf.radius < 550]
track = [Vec3(c.dxf.center) for c in msp.query('CIRCLE') if 100 < c.dxf.radius < 140 and c.dxf.center.y > 7000]
store_axes(msp, X0, Y0)
fixture_dims(msp, [(p.x, p.y) for p in down] + ([(track[len(track)//2].x, track[len(track)//2].y)] if track else []) + discs,
             X0, Y0, m2d(0, 8.058, X0, Y0)[1] + 800, None, discs=discs)
E = ext_of(msp, lambda e: bbox.extents([e], fast=True).has_data and abs(bbox.extents([e], fast=True).center.x) < 30000 and abs(bbox.extents([e], fast=True).center.y) < 30000)
def tabs10(psp):
    rows = [(sym1, 'PAGRINDINIS APŠVIETIMAS,\nĮLEIDŽIAMI ŠVIESTUVAI', f'{len(down)} vnt.'),
            (sym2, 'AKCENTINIS APŠVIETIMAS,\nKRYPTINIAI ŠVIESTUVAI ANT BĖGIO', '1 bėg. / 3 vnt.'),
            (sym3, 'FUNKCINIS APŠVIETIMAS – PAKABINAMI\nŠVIESTUVAI VIRŠ STALŲ, h=+0,500', '3 vnt.')]
    table(psp, 25, 64, 'EKSPLIKACIJA', ['Žymėjimas', 'Pavadinimas', 'Kiekis'], rows, [26, 140, 32], rowh=12)
vw, vh = E.size.x/SCALE + 6, E.size.y/SCALE + 6
sheet(doc, '04_SVIESTUVU PLANAS', 4, 'ŠVIESTUVŲ PLANAS', [(215, 284-vh/2, vw, vh, E.center.x, E.center.y)], tabs10, sub_titles=[(25, 69, 'ŠVIESTUVŲ PLANAS')])
print('SV vp', round(vw), round(vh))
p = f'{OUT}/SVIESTUVU_PLANAS.dxf'; doc.saveas(p); SHEETS.append((p, '04_SVIESTUVU PLANAS'))

# =============================================================== 11-14 MODEL DRAWINGS
doc = ezdxf.readfile(f'{S}/out/model_drw2.dxf'); msp = doc.modelspace(); VW = json.load(open(f'{S}/views2.json'))
def extent_box(x0, y0, x1, y1):
    return bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and x0 <= bbox.extents([e], fast=True).center.x <= x1 and y0 <= bbox.extents([e], fast=True).center.y <= y1], fast=True)
Ep = extent_box(-5000, -3000, 25000, 12000)
vw, vh = Ep.size.x/SCALE + 4, Ep.size.y/SCALE + 4
sheet(doc, '05_BALDU PLANAS', 5, 'BALDŲ IŠDĖSTYMO PLANAS', [(215, 284-vh/2, vw, vh, Ep.center.x, Ep.center.y)], sub_titles=[(25, 284-vh-10, 'BALDŲ IŠDĖSTYMO PLANAS')])
for lap, k, nm in [(6, 'A', 'PJŪVIS 1-1'), (7, 'B', 'PJŪVIS 2-2')]:
    oy = VW[k]['oy']; Es = extent_box(-6000, oy-3000, 26000, oy+7500)
    vw, vh = Es.size.x/SCALE + 4, Es.size.y/SCALE + 4
    sheet(doc, f'{lap:02d}_{nm}', lap, nm, [(215, 284-vh/2, vw, vh, Es.center.x, Es.center.y)], sub_titles=[(25, 284-vh-10, nm)])
oy = VW['C']['oy']
Ec = extent_box(-6000, oy-3000, VW['D']['ox'] + VW['D']['umin']*1000 - 2500, oy+7500)
Ed = extent_box(VW['D']['ox'] + VW['D']['umin']*1000 - 2500, oy-3000, 30000, oy+7500)
wc, hc = Ec.size.x/SCALE + 4, Ec.size.y/SCALE + 4; wd, hd = Ed.size.x/SCALE + 4, Ed.size.y/SCALE + 4
gap = (385 - wc - wd)
sheet(doc, '08_PJUVIAI 3-3 4-4', 8, 'PJŪVIAI 3-3 IR 4-4',
      [(25+wc/2, 284-hc/2, wc, hc, Ec.center.x, Ec.center.y), (25+wc+gap+wd/2, 284-hd/2, wd, hd, Ed.center.x, Ed.center.y)],
      sub_titles=[(25, 284-max(hc, hd)-10, 'PJŪVIS 3-3'), (25+wc+gap, 284-max(hc, hd)-10, 'PJŪVIS 4-4')])
p = f'{OUT}/BALDU_PLANAS_IR_PJUVIAI.dxf'; doc.saveas(p)
for n in ['05_BALDU PLANAS', '06_PJŪVIS 1-1', '07_PJŪVIS 2-2', '08_PJUVIAI 3-3 4-4']: SHEETS.append((p, n))
for lay in ['11_BALDU PLANAS', '12_PJŪVIS 1-1', '13_PJŪVIS 2-2', '14_PJUVIAI 3-3 4-4']: pass

# =============================================================== PDF
import pymupdf as fz
book_a3 = fz.open(); book_orig = fz.open(); cache = {}
for path, lay in SHEETS:
    d = cache.get(path) or ezdxf.readfile(path); cache[path] = d
    tmp = f'{OUT}/_tmp.pdf'; export_pdf(d, [lay], tmp); src = fz.open(tmp)
    book_orig.insert_pdf(src)
    pg = src[0]; W, H = pg.rect.width, pg.rect.height
    if W > 1500:   # A1 -> 4 x A3 tiles (2 x 2), print at 100 %
        for (cx, cy) in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            np_ = book_a3.new_page(width=W/2, height=H/2)
            np_.show_pdf_page(np_.rect, src, 0, clip=fz.Rect(cx*W/2, cy*H/2, (cx+1)*W/2, (cy+1)*H/2))
    else: book_a3.insert_pdf(src)
os.remove(f'{OUT}/_tmp.pdf')
for b_ in (book_a3, book_orig):
    if os.path.exists(f'{OUT}/VITRINOS_ISKLOTINE.pdf'): b_.insert_pdf(fz.open(f'{OUT}/VITRINOS_ISKLOTINE.pdf'))
tag = "su_stampu" if STAMP else "be_stampo"
book_a3.save(f'{OUT}/MARI_MADE_breziniai_{tag}_spausdinimui_A3.pdf'); book_orig.save(f'{OUT}/MARI_MADE_breziniai_{tag}_A1_A3.pdf')
print('PDF pages A3-print', len(book_a3), 'original', len(book_orig))
