# Process the 4 existing DXF plans + model drawings -> standardised DXFs with A1/A3 layouts (1:50) and PDFs
import sys, os, json, ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44
from ezdxf.enums import TextEntityAlignment as TA
S = sys.argv[1]; STAMP = sys.argv[2] == 'stamp'; OUT = sys.argv[3]
sys.path.insert(0, S + '/scripts')
from dxf_common import *
os.makedirs(OUT, exist_ok=True)

INFO = dict(objektas='Prekybos centras GO9, Gedimino pr. 9, Vilnius', patalpa='Parduotuvė MARI MADE – interjero projektas',
            uzsakovas='Vilniaus dizaino kolegija', stadija='Interjero projektas', atliko='Gabrielė Meilūnaitė',
            tikrino='', data='2026-11', mastelis='1:50', lapu=9)

# existing layer standardisation (ISO 128, line group 0.5)
LW = {'Esamos sienos': 50, 'Langai': 25, 'asys': 18, 'Durys': 25, 'kolonos': 50, 'stiklas': 13, 'evakuacija': 35,
      'konturas': 25, 'Pertvaros': 50, 'Textas bendras': 25, 'Sienu haxas': 13, 'HACAS': 13, '0.5': 25,
      '0-statramsciai': 25, '_Metalines konstr': 35, 'A-73----E--': 25, 'A-43CB--E-N': 35, 'A-45CE--E--': 18,
      'A-45CE--E-N': 18, 'a-scianki': 25, 'B-HATCH': 13, 'Sutartiniai žymėjimai.': 50, '0': 25, 'GRIAUNAMA': 35}
TYPO = {'IEJIMAS': 'ĮĖJIMAS', 'IĖJIMAS': 'ĮĖJIMAS', 'ĮEJIMAS': 'ĮĖJIMAS', 'ILEIDŽIAMI': 'ĮLEIDŽIAMI', 'LAUKO DURIS': 'LAUKO DURYS',
        'GIPSINE SIENA': 'GIPSINĖ SIENA', 'GIPSO KARTONOS': 'GIPSO KARTONO', 'Į PATALPA': 'Į PATALPĄ', 'TŪRĖKLAS': 'TURĖKLAS'}
def fix(s):
    for a, b in TYPO.items(): s = s.replace(a, b)
    return s

def standardise(doc):
    setup(doc)
    for n, lw in LW.items():
        if n in doc.layers: doc.layers.get(n).dxf.lineweight = lw
    if 'asys' in doc.layers: doc.layers.get('asys').dxf.linetype = 'A-ASIS'
    for l in doc.layers:
        if l.dxf.lineweight == -3: l.dxf.lineweight = 25      # 'Default' -> explicit 0.25
    for lay in [doc.modelspace()] + [b for b in doc.blocks if not b.name.lower().startswith('*paper')]:
        for e in lay:
            if e.dxf.hasattr('lineweight') and e.dxf.lineweight not in (-1,):
                e.dxf.lineweight = -1                        # ByLayer -> controlled by layer table
            if e.dxftype() == 'MTEXT': e.text = fix(e.text)
            if e.dxftype() == 'TEXT': e.dxf.text = fix(e.dxf.text)
    doc.header['$LWDISPLAY'] = 1
    for name in list(doc.layouts.names()):
        if name != 'Model':
            try: doc.layouts.delete(name)
            except Exception: pass

def in_box(e, x0, y0, x1, y1):
    b = bbox.extents([e], fast=True)
    return b.has_data and b.extmin.x >= x0 and b.extmax.x <= x1 and b.extmin.y >= y0 and b.extmax.y <= y1

def collect(msp, box):
    return [e for e in msp if in_box(e, *box)]

def is_text(e): return e.dxftype() in ('TEXT', 'MTEXT')

def to_paper(psp, ents, cx, cy, maxw, maxh):
    """copy model-space symbol entities into paper space, fitted into a cell centred at (cx,cy)"""
    b = bbox.extents(ents, fast=True)
    w, h = b.size.x or 1, b.size.y or 1
    s = min(maxw/w, maxh/h, 1/SCALE*1.6)
    m = Matrix44.translate(-b.center.x, -b.center.y, 0) @ Matrix44.scale(s, s, s) @ Matrix44.translate(cx, cy, 0)
    for e in ents:
        try:
            c = e.copy(); c.transform(m); psp.add_entity(c)
            if c.dxf.hasattr('ltscale') or True:
                try: c.dxf.ltscale = (e.dxf.get('ltscale', 1.0)) * s
                except Exception: pass
        except Exception as ex: print('skip', e.dxftype(), ex)

def table(psp, x, ytop, title, header, rows, colw, rowh=9.0, numcol=False):
    """rows: list of (symbol_entities_or_text, description[, extra])"""
    W = sum(colw); y = ytop
    L = lambda a, b, lay='A-LENTELES': psp.add_line(a, b, dxfattribs={'layer': lay})
    def put(s, xx, yy, h=2.5, al=TA.MIDDLE_LEFT):
        t = psp.add_text(s, height=h, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((xx, yy), align=al)
    # title row
    put(title, x+2, y-5, 3.5); y -= 10; L((x, y), (x+W, y), 'A-LENTELES-REMAS')
    # header
    xs = [x]; [xs.append(xs[-1]+c) for c in colw]
    for i, hd in enumerate(header): put(hd, xs[i]+2, y-3.5, 2.0)
    y -= 7; L((x, y), (x+W, y), 'A-LENTELES-REMAS')
    for r in rows:
        sym, desc = r[0], r[1]
        nlines = desc.count('\n') + 1; rh = max(rowh, 5.0*nlines + 3)
        cy = y - rh/2
        if isinstance(sym, str): put(sym, xs[0]+colw[0]/2, cy, 2.5, TA.MIDDLE_CENTER)
        else: to_paper(psp, sym, xs[0]+colw[0]/2, cy, colw[0]*0.8, rh*0.7)
        for k, line in enumerate(desc.split('\n')):
            put(line, xs[1]+2, cy + (nlines-1)*2.5 - k*5.0, 2.5)
        for j, extra in enumerate(r[2:]): put(str(extra), xs[2+j]+colw[2+j]/2, cy, 2.5, TA.MIDDLE_CENTER)
        y -= rh; L((x, y), (x+W, y))
    for xx in xs[1:-1]: L((xx, ytop-10), (xx, y))
    psp.add_lwpolyline([(x, ytop), (x+W, ytop), (x+W, y), (x, y)], close=True, dxfattribs={'layer': 'A-LENTELES-REMAS'})
    return y

def sheet(doc, name, fmt, lapas, title, vps, tables_fn=None, notes=None, sub_titles=None):
    psp = new_layout(doc, name, fmt)
    for old in ('Layout1', 'Layout2'):
        if old in doc.layouts.names():
            try: doc.layouts.delete(old)
            except Exception: pass
    frame(psp, fmt)
    W, H = PAPER[fmt]
    for (cx, cy, w, h, mcx, mcy) in vps: viewport(psp, cx, cy, w, h, mcx, mcy)
    if STAMP:
        title_block(psp, fmt, dict(INFO, brezinys=title, lapas=lapas))
    else:
        t = psp.add_text(f'{lapas}', height=3.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((W-14, 14), align=TA.MIDDLE_CENTER)
    if sub_titles:
        for (x, y, s) in sub_titles: sheet_title(psp, x, y, s)
    if tables_fn: tables_fn(psp)
    if notes:
        y = notes[1]
        for line in notes[2]:
            t = psp.add_text(line, height=2.5 if line.isupper() else 2.2, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((notes[0], y), align=TA.BOTTOM_LEFT); y -= 4.6
    return psp

NOTES = ['PASTABOS', '1. Matmenys nurodyti milimetrais.', '2. Altitudės nurodytos pastato ±0,000 atžvilgiu.',
         '3. Brėžinio linijų storiai pagal LST EN ISO 128 (linijų grupė 0,5).', '4. Prieš gamybą matmenis patikrinti vietoje.']
SHEETS = []   # (dxf path, layout name) in sheet order

# =============================================================== 1-2 GRIOVIMO / NAUJAS (A1)
def plan_A1(fn, lapas, title, sut_rows, eks_rows, sut_box, eks_box, outname):
    doc = ezdxf.readfile(f'{S}/dxf_in/{fn}.dxf'); msp = doc.modelspace()
    standardise(doc)
    # gather legend entities, then delete them from model space
    sut_all = collect(msp, sut_box[:4]); eks_all = collect(msp, eks_box[:4])
    def rows_from(all_ents, spec, symx_max):
        rows = []
        for (y0, y1, text) in spec:
            sym = [e for e in all_ents if (not is_text(e) or bbox.extents([e]).extmax.x < symx_max) and
                   y0 <= bbox.extents([e], fast=True).center.y <= y1 and bbox.extents([e], fast=True).extmax.x < symx_max]
            rows.append(([e.copy() for e in sym], text))
        return rows
    srows = rows_from(sut_all, sut_rows, sut_box[4] if len(sut_box) > 4 else 1e9)
    erows = [(n, t) for (n, t) in eks_rows]
    for e in sut_all + eks_all: msp.delete_entity(e) if e.is_alive else None
    sut_box = sut_box[:4]
    # plan extents (exclude far stray objects)
    ext = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and bbox.extents([e], fast=True).extmax.x < 140000
                        and bbox.extents([e], fast=True).extmin.x > 100000 and bbox.extents([e], fast=True).extmin.y > 40000
                        and bbox.extents([e], fast=True).extmax.y < 70000], fast=True)
    mcx, mcy = ext.center.x, ext.center.y
    vw, vh = ext.size.x/SCALE + 16, ext.size.y/SCALE + 16
    def tabs(psp):
        y = table(psp, 600, 572, 'SUTARTINIAI ŽYMĖJIMAI', ['Žymėjimas', 'Aprašymas'], srows, [40, 190], rowh=11)
        table(psp, 600, y-12, 'EKSPLIKACIJA', ['Nr.', 'Pavadinimas'], erows, [16, 214], rowh=8)
    sheet(doc, f'{lapas:02d}_{title}', 'A1', lapas, title, [(25+vw/2+4, 80+vh/2, vw, vh, mcx, mcy)], tabs,
          notes=(600, 150, NOTES), sub_titles=[(25, 50, title)])
    p = f'{OUT}/{outname}.dxf'; doc.saveas(p); SHEETS.append((p, f'{lapas:02d}_{title}'))

plan_A1('GRIOVIMO_PLANAS', 1, 'GRIOVIMO PLANAS',
        [(63600, 63950, 'ESAMOS SIENOS IR LAIKANČIOS KONSTRUKCIJOS'), (63000, 63350, 'ESAMOS SIENOS IR LAIKANČIOS KONSTRUKCIJOS'),
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

# =============================================================== 3 LUBU (A3)
doc = ezdxf.readfile(f'{S}/dxf_in/LUBU_PLANAS.dxf'); msp = doc.modelspace(); standardise(doc)
for e in list(msp.query('MTEXT')):
    if 'LUBU PLANAS' in e.plain_text() or 'LUBŲ PLANAS' in e.plain_text(): msp.delete_entity(e)
for e in list(msp.query('MULTILEADER')): msp.delete_entity(e)
hatches = [e for e in msp.query('HATCH') if e.dxf.layer == '0']
def hatch_sample(h):
    c = h.copy(); c.paths.clear()
    b = bbox.extents([h], fast=True); x, y = b.extmin.x, b.extmin.y
    c.paths.add_polyline_path([(x, y), (x+1500, y), (x+1500, y+700), (x, y+700)], is_closed=True)
    r = msp.add_lwpolyline([(x, y), (x+1500, y), (x+1500, y+700), (x, y+700)], close=True, dxfattribs={'layer': 'A-LENTELES'})
    tmp = [c, r]; return tmp
smp = [hatch_sample(h) for h in sorted(hatches, key=lambda h: -bbox.extents([h]).size.x)]
ext = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and abs(bbox.extents([e], fast=True).center.x) < 30000 and abs(bbox.extents([e], fast=True).center.y) < 30000 and e.dxftype() != 'MULTILEADER'], fast=True)
def tabs3(psp):
    rows = [(smp[0], 'DAŽYTOS LUBOS, RAL 1013 OYSTER WHITE'), (smp[1], 'NULEISTOS LUBOS (APVALŪS ELEMENTAI)')]
    table(psp, 25, 82, 'SUTARTINIAI ŽYMĖJIMAI', ['Žymėjimas', 'Aprašymas'], rows, [30, 165], rowh=11)
vp_w, vp_h = 380, 185
sheet(doc, '03_LUBU PLANAS', 'A3', 3, 'LUBŲ PLANAS', [(215, 190, vp_w, vp_h, ext.center.x+1200, ext.center.y)], tabs3,
      sub_titles=[(25, 88, 'LUBŲ PLANAS')])
for pair in smp:   # the sample hatches were only needed for the legend
    for e in pair:
        if e.is_alive and e.dxf.owner == msp.layout_key: msp.delete_entity(e)
p = f'{OUT}/LUBU_PLANAS.dxf'; doc.saveas(p); SHEETS.append((p, '03_LUBU PLANAS'))

# =============================================================== 4 SVIESTUVU (A3)
doc = ezdxf.readfile(f'{S}/dxf_in/VIESTUVU_PLANAS.dxf'); msp = doc.modelspace(); standardise(doc)
# remove the started-but-unfinished shelving outline (L-shape along back & right wall, layer 0)
SHELF = [((12263, 8152), (12263, 8452)), ((12263, 8152), (19272, 8159)), ((19243, 3174), (19543, 3177)), ((19243, 3174), (19272, 8159))]
removed = 0
for e in list(msp.query('LINE[layer=="0"]')):
    a, b = e.dxf.start, e.dxf.end
    for p0, p1 in SHELF:
        if (abs(a.x-p0[0]) < 3 and abs(a.y-p0[1]) < 3 and abs(b.x-p1[0]) < 3 and abs(b.y-p1[1]) < 3) or \
           (abs(b.x-p0[0]) < 3 and abs(b.y-p0[1]) < 3 and abs(a.x-p1[0]) < 3 and abs(a.y-p1[1]) < 3):
            msp.delete_entity(e); removed += 1; break
print('shelf lines removed', removed)
leg = collect(msp, (6900, -3900, 13200, 1400))
sym1 = [e.copy() for e in leg if not is_text(e) and -800 < bbox.extents([e]).center.y < -50 and bbox.extents([e]).extmax.x < 8500]
sym2 = [e.copy() for e in leg if not is_text(e) and -1600 < bbox.extents([e]).center.y < -1300 and bbox.extents([e]).extmax.x < 8500]
sym3 = [e.copy() for e in leg if not is_text(e) and -2800 < bbox.extents([e]).center.y < -2550 and bbox.extents([e]).extmax.x < 8500]
for e in leg: msp.delete_entity(e)
for e in list(msp.query('MTEXT')):
    if 'PLANAS' in e.plain_text(): msp.delete_entity(e)
# move lighting symbols from layer 0 to a dedicated layer
if 'E-SVIESTUVAI' not in doc.layers: doc.layers.add('E-SVIESTUVAI', color=7, lineweight=25)
for e in msp:
    if e.dxf.layer == '0' and e.dxftype() in ('CIRCLE', 'HATCH', 'LWPOLYLINE'): e.dxf.layer = 'E-SVIESTUVAI'
ext = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and abs(bbox.extents([e], fast=True).center.x) < 30000 and abs(bbox.extents([e], fast=True).center.y) < 30000], fast=True)
def tabs4(psp):
    rows = [(sym1, 'PAGRINDINIS APŠVIETIMAS,\nĮLEIDŽIAMI ŠVIESTUVAI', '6 vnt.'),
            (sym2, 'AKCENTINIS APŠVIETIMAS,\nKRYPTINIAI ŠVIESTUVAI ANT BĖGIO', '1 bėg. / 3 vnt.'),
            (sym3, 'FUNKCINIS APŠVIETIMAS / NULEISTOS\nLUBOS, PAKABINAMI ŠVIESTUVAI', '3 vnt.')]
    table(psp, 25, 82, 'EKSPLIKACIJA', ['Žymėjimas', 'Pavadinimas', 'Kiekis'], rows, [26, 140, 30], rowh=12)
sheet(doc, '04_SVIESTUVU PLANAS', 'A3', 4, 'ŠVIESTUVŲ PLANAS', [(215, 190, 380, 185, ext.center.x, ext.center.y)], tabs4,
      sub_titles=[(25, 88, 'ŠVIESTUVŲ PLANAS')])
p = f'{OUT}/SVIESTUVU_PLANAS.dxf'; doc.saveas(p); SHEETS.append((p, '04_SVIESTUVU PLANAS'))

# =============================================================== 5-8 MODEL DRAWINGS (A3)
doc = ezdxf.readfile(f'{S}/out/model_drw.dxf'); VW = json.load(open(f'{S}/views.json'))
def vc(k, u0, u1, v0, v1):
    ox, oy = VW[k]['ox'], VW[k]['oy']
    return ((u0+u1)/2*1000+ox, (v0+v1)/2*1000+oy)
pc = vc('PLAN', 0.55, 19.55, 0.2, 9.6)
sheet(doc, '05_BALDU PLANAS', 'A3', 5, 'BALDŲ IŠDĖSTYMO PLANAS', [(215, 190, 384, 194, *pc)],
      notes=(25, 74, NOTES + ['5. Pjūvio plokštuma plane – 1200 mm nuo grindų.', '6. Parduotuvės grindų altitudė -2,000.']),
      sub_titles=[(25, 82, 'BALDŲ IŠDĖSTYMO PLANAS')])
for lap, k, nm in [(6, 'A', 'PJŪVIS 1-1'), (7, 'B', 'PJŪVIS 2-2')]:
    u0, u1 = VW[k]['umin'], VW[k]['umax']
    c = vc(k, u0-1.9, u1+1.9, -1.4, 6.6)
    sheet(doc, f'{lap:02d}_{nm}', 'A3', lap, nm, [(215, 180, (u1-u0+3.8)*20, 8.0*20, *c)],
          notes=(25, 62, NOTES[:3]), sub_titles=[(25, 82, nm)])
cs = []
for k in 'CD':
    u0, u1 = VW[k]['umin'], VW[k]['umax']; cs.append((vc(k, u0-1.75, u1+0.95, -1.4, 6.6), (u1-u0+2.7)*20))
sheet(doc, '08_PJUVIAI 3-3 4-4', 'A3', 8, 'PJŪVIAI 3-3 IR 4-4',
      [(25+cs[0][1]/2, 180, cs[0][1], 160, *cs[0][0]), (25+cs[0][1]+12+cs[1][1]/2, 180, cs[1][1], 160, *cs[1][0])],
      notes=(25, 62, NOTES[:3]), sub_titles=[(25, 88, 'PJŪVIS 3-3'), (25+cs[0][1]+12, 88, 'PJŪVIS 4-4')])
p = f'{OUT}/BALDU_PLANAS_IR_PJUVIAI.dxf'; doc.saveas(p)
for n in ['05_BALDU PLANAS', '06_PJŪVIS 1-1', '07_PJŪVIS 2-2', '08_PJUVIAI 3-3 4-4']: SHEETS.append((p, n))

# =============================================================== PDF
import pymupdf as fz
book = fz.open()
for path, lay in SHEETS:
    d = ezdxf.readfile(path); tmp = f'{OUT}/_tmp.pdf'
    export_pdf(d, [lay], tmp); book.insert_pdf(fz.open(tmp))
os.remove(f'{OUT}/_tmp.pdf')
if os.path.exists(f'{OUT}/VITRINOS_ISKLOTINES.pdf'): book.insert_pdf(fz.open(f'{OUT}/VITRINOS_ISKLOTINES.pdf'))
book.save(f'{OUT}/MARI_MADE_breziniai_{"su_stampu" if STAMP else "be_stampo"}.pdf')
print('PDF pages', len(book))
