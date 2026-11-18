# Sheet 9: the real facade elevation drawn by the user (VITRINOS_ISKLOTINE2.dxf) + standard line weights,
# MARI MADE logo vinyl on the windows, dimensions, level marks, logo detail 1:10
import sys, ezdxf
from ezdxf import bbox
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment as TA
from ezdxf.fonts import fonts
S = sys.argv[1]; STAMP = sys.argv[2] == 'stamp'; OUT = sys.argv[3]; SRC = sys.argv[4]
sys.path.insert(0, S + '/scripts')
from dxf_common import *
src = ezdxf.readfile(SRC)
doc = ezdxf.new('R2018', setup=True); setup(doc); msp = doc.modelspace()
LAY = {'F-KONTURAI': 35, 'F-DETALES': 18, 'F-LANGAI': 25, 'F-DURYS': 25, 'A-LOGO': 25}
for n, lw in LAY.items(): doc.layers.add(n, color=7, lineweight=lw)
imp = Importer(src, doc)
ents = [e for e in src.modelspace() if e.dxf.layer != 'Defpoints']
imp.import_entities(ents, msp); imp.finalize()
for e in msp:
    L, t = e.dxf.layer, e.dxftype()
    if L == '00': e.dxf.layer = 'F-KONTURAI' if t in ('LWPOLYLINE', 'ARC') else 'F-DETALES'
    elif L == '000': e.dxf.layer = 'F-LANGAI'
    elif L == '_Metalines konstr': e.dxf.layer = 'F-DURYS'
    else: e.dxf.layer = 'F-DETALES'
    e.dxf.color = 256
    if e.dxf.hasattr('lineweight'): e.dxf.lineweight = -1
for n in ('00', '000', '_Metalines konstr'):
    if n in doc.layers:
        try: doc.layers.remove(n)
        except Exception: pass
# --- facade geometry (elevation units = mm; z_store = y/1000 - 0.149)
zf = lambda y: y/1000 - 0.149
SW_Y, WIN_Y0, WIN_Y1 = 449, 1204, 4368
WINS = [(5266, 6636), (8056, 9426), (10836, 12206), (13736, 15106)]
DOOR = (2366, 3916); ARCH_TOP, LEAF_TOP = 4114, 2814
XL, XR = 747, 16446
# --- logo vinyl on each window, eye level 1550 above the sidewalk
CAP_M, CAP_S, W_M, W_S = 160, 45, 1.30, 1.60
LOGO_Y = SW_Y + 1550
for a, b in WINS:
    c = (a+b)/2
    t = msp.add_text('MARI', height=CAP_M, dxfattribs={'layer': 'A-LOGO', 'style': TXT, 'width': W_M}); t.set_placement((c, LOGO_Y+75), align=TA.BOTTOM_CENTER)
    t = msp.add_text('MADE', height=CAP_S, dxfattribs={'layer': 'A-LOGO', 'style': TXT, 'width': W_S}); t.set_placement((c, LOGO_Y), align=TA.BOTTOM_CENTER)
# --- dimensions
dl = {'layer': 'A-MATMENYS'}; E0 = bbox.extents(msp)
yb = E0.extmin.y
pts = [XL, DOOR[0], DOOR[1]] + [v for w in WINS for v in w] + [XR]
msp.add_multi_point_linear_dim(base=(0, yb-650), points=[(x, SW_Y) for x in pts], angle=0, dimstyle='ISO-50', dxfattribs=dl)
msp.add_linear_dim(base=(0, yb-1200), p1=(XL, SW_Y), p2=(XR, SW_Y), angle=0, dimstyle='ISO-50', dxfattribs=dl).render()
a, b = WINS[-1]
msp.add_multi_point_linear_dim(base=(XR+900, 0), points=[(b, y) for y in [SW_Y, WIN_Y0, LOGO_Y, LOGO_Y+75+CAP_M, WIN_Y1]], angle=90, dimstyle='ISO-50', dxfattribs=dl)
msp.add_linear_dim(base=(0, WIN_Y1+500), p1=(a, WIN_Y1), p2=(b, WIN_Y1), angle=0, dimstyle='ISO-50', dxfattribs=dl).render()
msp.add_linear_dim(base=(0, ARCH_TOP+640), p1=(DOOR[0], ARCH_TOP), p2=(DOOR[1], ARCH_TOP), angle=0, dimstyle='ISO-50', dxfattribs=dl).render()
# --- level marks at the left edge (staggered where close)
def level(y, desc, col=0):
    s = SCALE; x = E0.extmin.x - 250 - col*1100; h_ = 2.5*s; w = 1.45*s
    msp.add_lwpolyline([(x, y), (x-w, y+h_), (x+w, y+h_)], close=True, dxfattribs={'layer': 'A-ALTITUDES'})
    hh = msp.add_hatch(color=7, dxfattribs={'layer': 'A-ALTITUDES'}); hh.paths.add_polyline_path([(x, y), (x, y+h_), (x-w, y+h_)], is_closed=True)
    msp.add_line((x, y), (x-16*s, y), dxfattribs={'layer': 'A-ALTITUDES'}); msp.add_line((x+w, y+h_), (x-16*s, y+h_), dxfattribs={'layer': 'A-ALTITUDES'})
    for txt_, yy, al in [(fmt_level(zf(y)), y+h_+0.7*s, TA.BOTTOM_RIGHT), (desc, y-0.7*s, TA.TOP_RIGHT)]:
        t = msp.add_text(txt_, height=2.5*s, dxfattribs={'layer': 'A-TEKSTAS', 'style': TXT}); t.set_placement((x-(w+0.6*s), yy), align=al)
level(SW_Y, 'šaligatvis'); level(WIN_Y0, 'palangė', 1); level(LEAF_TOP, 'durys'); level(ARCH_TOP, 'arka', 1); level(WIN_Y1, 'langų v.')
# --- logo detail 1:10 (drawn x5 far away so a 1:50 viewport shows it at 1:10)
font = fonts.make_font('LiberationSans-Regular.ttf', 1.0)
DX, K = 60000, 5.0
wM = font.text_width('MARI')*CAP_M*W_M*K; wS = font.text_width('MADE')*CAP_S*W_S*K
gw = 1284*K/2
msp.add_lwpolyline([(DX-gw, 0), (DX+gw, 0), (DX+gw, 550*K), (DX-gw, 550*K)], close=True, dxfattribs={'layer': 'F-LANGAI', 'linetype': 'A-BRUKSNINE'})
t = msp.add_text('MARI', height=CAP_M*K, dxfattribs={'layer': 'A-LOGO', 'style': TXT, 'width': W_M}); t.set_placement((DX, 120*K), align=TA.BOTTOM_CENTER)
t = msp.add_text('MADE', height=CAP_S*K, dxfattribs={'layer': 'A-LOGO', 'style': TXT, 'width': W_S}); t.set_placement((DX, 45*K), align=TA.BOTTOM_CENTER)
ds10 = doc.dimstyles.duplicate_entry('ISO-50', 'ISO-50-D10'); ds10.dxf.dimlfac = 1/K
msp.add_linear_dim(base=(0, (120+CAP_M)*K+600), p1=(DX-wM/2, (120+CAP_M)*K), p2=(DX+wM/2, (120+CAP_M)*K), dimstyle='ISO-50-D10', dxfattribs=dl).render()
msp.add_linear_dim(base=(0, -600), p1=(DX-wS/2, 45*K), p2=(DX+wS/2, 45*K), dimstyle='ISO-50-D10', dxfattribs=dl).render()
msp.add_multi_point_linear_dim(base=(DX+gw+700, 0), points=[(DX+wM/2, z*K) for z in [45, 45+CAP_S, 120, 120+CAP_M]], angle=90, dimstyle='ISO-50-D10', dxfattribs=dl)
# --- sheet
psp = new_layout(doc, '09_FASADO VITRINOS', 'A3')
if 'Layout1' in doc.layouts.names(): doc.layouts.delete('Layout1')
frame(psp, 'A3')
Ef = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and bbox.extents([e], fast=True).center.x < 40000], fast=True)
vw, vh = Ef.size.x/SCALE + 3, Ef.size.y/SCALE + 6
viewport(psp, 215, 284-vh/2, vw, vh, Ef.center.x, Ef.center.y)
sheet_title(psp, 25, 284-vh-12, 'FASADO VITRINŲ IŠKLOTINĖ', 'M 1:50')
Ed = bbox.extents([e for e in msp if bbox.extents([e], fast=True).has_data and bbox.extents([e], fast=True).center.x >= 40000], fast=True)
dw, dh = Ed.size.x/SCALE + 8, Ed.size.y/SCALE + 8
DT = 284-vh-34
viewport(psp, 25+dw/2, DT-6-dh/2, dw, dh, Ed.center.x, Ed.center.y)
sheet_title(psp, 25, DT, 'LOGOTIPO PLĖVELĖ', 'M 1:10')
t = psp.add_text('Aukso spalvos metalizuota plėvelė, klijuojama stiklo vidinėje pusėje.', height=2.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((25, DT-12-dh), align=TA.BOTTOM_LEFT)
if STAMP:
    title_block(psp, 'A3', dict(objektas='Prekybos centras GO9, Gedimino pr. 9, Vilnius', patalpa='Parduotuvė MARI MADE – interjero projektas',
                uzsakovas='Vilniaus dizaino kolegija', stadija='Interjero projektas', atliko='Gabrielė Meilūnaitė', tikrino='', data='2026-11',
                mastelis='1:50; 1:10', lapas=9, lapu=9, brezinys='FASADO VITRINŲ IŠKLOTINĖ'))
else:
    t = psp.add_text('9', height=3.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((406, 14), align=TA.MIDDLE_CENTER)
doc.saveas(f'{OUT}/VITRINOS_ISKLOTINE.dxf'); export_pdf(doc, ['09_FASADO VITRINOS'], f'{OUT}/VITRINOS_ISKLOTINE.pdf')
print('vitrina3 ok', round(vw), round(vh), round(dw), round(dh))
