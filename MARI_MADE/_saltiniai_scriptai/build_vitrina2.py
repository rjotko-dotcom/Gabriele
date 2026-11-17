# Facade window elevation 1:50 with MARI MADE logo vinyl only + logo detail 1:10
import sys, json, math, ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.fonts import fonts
S = sys.argv[1]; STAMP = sys.argv[2] == 'stamp'; OUT = sys.argv[3]
sys.path.insert(0, S + '/scripts')
from dxf_common import *
META = json.load(open(S + '/geo2_meta.json'))
doc = ezdxf.new('R2018', setup=True); setup(doc); msp = doc.modelspace()
for n, (c, lw, lt) in {'A-LANGAI': (7, 25, 'Continuous'), 'A-DURYS': (7, 25, 'Continuous'), 'A-LOGO': (7, 25, 'Continuous'),
                       'A-RUSTIKA': (7, 13, 'Continuous')}.items():
    doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
L = lambda l: {'layer': l}
mm = lambda x: x*1000
SW = 0.30                                   # sidewalk / entrance level (-1,700)
X0, X1, ZT = 1.839, 17.937, 6.15
def rect(x0, z0, x1, z1, lay):
    msp.add_lwpolyline([(mm(x0), mm(z0)), (mm(x1), mm(z0)), (mm(x1), mm(z1)), (mm(x0), mm(z1))], close=True, dxfattribs=L(lay))
# facade outline + sidewalk + break line on top
msp.add_lwpolyline([(mm(X0), mm(SW)), (mm(X0), mm(ZT)), (mm(X1), mm(ZT)), (mm(X1), mm(SW))], dxfattribs=L('A-PJUVIS-SIENOS'))
msp.add_line((mm(X0-1.0), mm(SW)), (mm(X1+1.0), mm(SW)), dxfattribs=L('A-PJUVIS-SIENOS'))
h = msp.add_hatch(color=7, dxfattribs=L('A-PERDANGA-UZP')); h.set_pattern_fill('ANSI31', scale=25)
h.paths.add_polyline_path([(mm(X0-1.0), mm(SW-0.25)), (mm(X1+1.0), mm(SW-0.25)), (mm(X1+1.0), mm(SW)), (mm(X0-1.0), mm(SW))], is_closed=True)
openings = [(a, b, 0.90, 6.0, 'w') for a, b, _, _ in META['windows']] + [(3.56, 5.31, SW, 6.0, 'd')]
# rustication courses on piers (every 400 mm) – clipped at openings
edges = sorted([X0] + [v for a, b, *_ in openings for v in (a, b)] + [X1])
for z in [SW + 0.4*i for i in range(1, 15) if SW + 0.4*i < ZT - 0.05]:
    xs = [X0]
    for a, b, z0, z1, _ in sorted(openings):
        if z0 <= z <= z1: xs += [a, b]
    xs.append(X1)
    for i in range(0, len(xs), 2): msp.add_line((mm(xs[i]), mm(z)), (mm(xs[i+1]), mm(z)), dxfattribs=L('A-RUSTIKA'))
for a, b, z0, z1, kind in openings:
    rect(a, z0, b, z1, 'A-LANGAI'); t = 0.06
    rect(a+t, z0+t, b-t, z1-t, 'A-LANGAI')
    if kind == 'w':
        msp.add_line((mm(a+t), mm(3.60)), (mm(b-t), mm(3.60)), dxfattribs=L('A-LANGAI')); msp.add_line((mm(a+t), mm(3.66)), (mm(b-t), mm(3.66)), dxfattribs=L('A-LANGAI'))
        for zc in (4.7,):
            for dd in (0, 0.12): msp.add_line((mm(a+0.25+dd), mm(zc-0.25)), (mm(a+0.57+dd), mm(zc+0.15)), dxfattribs={'layer': 'A-LANGAI', 'lineweight': 13})
    else:   # double glass door 2400 + transom
        top = SW + 2.40; mid = (a+b)/2
        msp.add_line((mm(a+t), mm(top)), (mm(b-t), mm(top)), dxfattribs=L('A-DURYS')); msp.add_line((mm(a+t), mm(top+t)), (mm(b-t), mm(top+t)), dxfattribs=L('A-DURYS'))
        msp.add_line((mm(mid), mm(SW)), (mm(mid), mm(top)), dxfattribs=L('A-DURYS'))
        for hx in (mid-0.08, mid+0.08): msp.add_line((mm(hx), mm(SW+0.95)), (mm(hx), mm(SW+1.25)), dxfattribs={'layer': 'A-DURYS', 'lineweight': 35})
        # opening direction marks (inward) – dashed triangles
        for (x0, x1) in ((a+t, mid), (mid, b-t)):
            hinge = x0 if x0 == a+t else x1
            far = x1 if hinge == x0 else x0
            msp.add_lwpolyline([(mm(far), mm(SW)), (mm(hinge), mm((SW+top)/2)), (mm(far), mm(top))], dxfattribs={'layer': 'A-VIRS-PJUVIO', 'ltscale': 0.6})
# logo vinyl on every window glass (eye level ≈ 1600 above sidewalk)
font = fonts.make_font('LiberationSans-Regular.ttf', 1.0)
LOGO_Z = SW + 1.55                       # bottom of 'MADE' line
CAP_M, CAP_S, W_M, W_S = 0.160, 0.045, 1.30, 1.60
def logo(cx, z0, sc=1.0, lay='A-LOGO'):
    t = msp.add_text('MARI', height=mm(CAP_M)*sc, dxfattribs={'layer': lay, 'style': TXT, 'width': W_M}); t.set_placement((mm(cx), mm(z0+0.075)*1 if sc == 1 else z0+0.075*1000*sc), align=TA.BOTTOM_CENTER)
    t2 = msp.add_text('MADE', height=mm(CAP_S)*sc, dxfattribs={'layer': lay, 'style': TXT, 'width': W_S}); t2.set_placement((mm(cx), mm(z0) if sc == 1 else z0), align=TA.BOTTOM_CENTER)
for a, b, *_ in META['windows']: logo((a+b)/2, LOGO_Z)
logo_w = font.text_width('MARI')*CAP_M*W_M*1.05
# dimensions
dl = L('A-MATMENYS')
msp.add_multi_point_linear_dim(base=(0, mm(SW-0.85)), points=[(mm(x), mm(SW)) for x in [X0, 3.56, 5.31] + [v for a, b, *_ in META['windows'] for v in (a, b)] + [X1]], angle=0, dimstyle='ISO-50', dxfattribs=dl)
msp.add_linear_dim(base=(0, mm(SW-1.35)), p1=(mm(X0), mm(SW)), p2=(mm(X1), mm(SW)), angle=0, dimstyle='ISO-50', dxfattribs=dl).render()
a, b = META['windows'][-1][:2]
msp.add_multi_point_linear_dim(base=(mm(X1+0.9), 0), points=[(mm(b), mm(z)) for z in [SW, 0.90, LOGO_Z, LOGO_Z+0.075+CAP_M, 3.60, 6.0]], angle=90, dimstyle='ISO-50', dxfattribs=dl)
# level marks on the left edge
def level(z, desc):
    s = SCALE; x, y = mm(X0-0.35), mm(z); h_ = 2.5*s; w = 1.45*s
    msp.add_lwpolyline([(x, y), (x-w, y+h_), (x+w, y+h_)], close=True, dxfattribs=L('A-ALTITUDES'))
    hh = msp.add_hatch(color=7, dxfattribs=L('A-ALTITUDES')); hh.paths.add_polyline_path([(x, y), (x, y+h_), (x-w, y+h_)], is_closed=True)
    msp.add_line((x, y), (x-16*s, y), dxfattribs=L('A-ALTITUDES')); msp.add_line((x+w, y+h_), (x-16*s, y+h_), dxfattribs=L('A-ALTITUDES'))
    for txt_, yy, al in [(fmt_level(z), y+h_+0.7*s, TA.BOTTOM_RIGHT), (desc, y-0.7*s, TA.TOP_RIGHT)]:
        t = msp.add_text(txt_, height=2.5*s, dxfattribs={'layer': 'A-TEKSTAS', 'style': TXT}); t.set_placement((x-(w+0.6*s), yy), align=al)
for z, d_ in [(SW, 'šaligatvis'), (3.60, 'skersinis'), (6.0, 'lubos')]: level(z, d_)
X0 -= 1.0; level(0.90, 'palangė'); X0 += 1.0
# ---------- logo detail 1:10 (drawn at 5x in model space far away so that a 1:50 viewport shows it at 1:10)
DX, DZ, K = 40000, 0, 5.0
cx = DX
w_glass = (b-a-0.12)
msp.add_lwpolyline([(cx-mm(w_glass/2)*K, DZ), (cx+mm(w_glass/2)*K, DZ), (cx+mm(w_glass/2)*K, DZ+mm(0.55)*K), (cx-mm(w_glass/2)*K, DZ+mm(0.55)*K)], close=True, dxfattribs={'layer': 'A-LANGAI', 'linetype': 'A-BRUKSNINE'})
t = msp.add_text('MARI', height=mm(CAP_M)*K, dxfattribs={'layer': 'A-LOGO', 'style': TXT, 'width': W_M}); t.set_placement((cx, DZ+mm(0.12)*K), align=TA.BOTTOM_CENTER)
t = msp.add_text('MADE', height=mm(CAP_S)*K, dxfattribs={'layer': 'A-LOGO', 'style': TXT, 'width': W_S}); t.set_placement((cx, DZ+mm(0.045)*K), align=TA.BOTTOM_CENTER)
ds10 = doc.dimstyles.duplicate_entry('ISO-50', 'ISO-50-D10'); ds10.dxf.dimlfac = 1/K
wM = font.text_width('MARI')*mm(CAP_M)*W_M*K; wS = font.text_width('MADE')*mm(CAP_S)*W_S*K
msp.add_linear_dim(base=(0, DZ+mm(0.12+CAP_M)*K+600), p1=(cx-wM/2, DZ+mm(0.12+CAP_M)*K), p2=(cx+wM/2, DZ+mm(0.12+CAP_M)*K), dimstyle='ISO-50-D10', dxfattribs=dl).render()
msp.add_linear_dim(base=(0, DZ-600), p1=(cx-wS/2, DZ+mm(0.045)*K), p2=(cx+wS/2, DZ+mm(0.045)*K), dimstyle='ISO-50-D10', dxfattribs=dl).render()
msp.add_multi_point_linear_dim(base=(cx+mm(w_glass/2)*K+700, 0), points=[(cx+wM/2, DZ+mm(z)*K) for z in [0.045, 0.045+CAP_S, 0.12, 0.12+CAP_M]], angle=90, dimstyle='ISO-50-D10', dxfattribs=dl)
# ---------- sheet
psp = new_layout(doc, '09_FASADO VITRINOS', 'A3')
if 'Layout1' in doc.layouts.names(): doc.layouts.delete('Layout1')
frame(psp, 'A3')
from ezdxf import bbox
Ef = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and bbox.extents([e], fast=True).center.x < 30000], fast=True)
vw, vh = Ef.size.x/SCALE + 6, Ef.size.y/SCALE + 6
viewport(psp, 215, 284-vh/2, vw, vh, Ef.center.x, Ef.center.y)
sheet_title(psp, 25, 284-vh-12, 'FASADO VITRINŲ IŠKLOTINĖ', 'M 1:50')
DT = 284-vh-34
Ed = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and bbox.extents([e], fast=True).center.x >= 30000], fast=True)
dw, dh = Ed.size.x/SCALE + 8, Ed.size.y/SCALE + 8
viewport(psp, 25+dw/2, DT-6-dh/2, dw, dh, Ed.center.x, Ed.center.y)
sheet_title(psp, 25, DT, 'LOGOTIPO PLĖVELĖ', 'M 1:10')
t = psp.add_text('Aukso spalvos metalizuota plėvelė, klijuojama stiklo vidinėje pusėje.', height=2.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((25, 18), align=TA.BOTTOM_LEFT)
if STAMP:
    title_block(psp, 'A3', dict(objektas='Prekybos centras GO9, Gedimino pr. 9, Vilnius', patalpa='Parduotuvė MARI MADE – interjero projektas',
                uzsakovas='Vilniaus dizaino kolegija', stadija='Interjero projektas', atliko='Gabrielė Meilūnaitė', tikrino='', data='2026-11',
                mastelis='1:50; 1:10', lapas=9, lapu=9, brezinys='FASADO VITRINŲ IŠKLOTINĖ'))
else:
    t = psp.add_text('9', height=3.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((406, 14), align=TA.MIDDLE_CENTER)
doc.saveas(f'{OUT}/VITRINOS_ISKLOTINE.dxf'); export_pdf(doc, ['09_FASADO VITRINOS'], f'{OUT}/VITRINOS_ISKLOTINE.pdf')
print('vitrina ok', round(vw), round(vh), round(dw), round(dh))
