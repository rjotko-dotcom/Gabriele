# Window display (vitrina) elevations 1:20 - two window variants, vinyl wordmark placement, dimensions
import sys, math, ezdxf
from ezdxf.enums import TextEntityAlignment as TA
S = sys.argv[1]; STAMP = sys.argv[2] == 'stamp'; OUT = sys.argv[3]
sys.path.insert(0, S + '/scripts')
from dxf_common import *
doc = ezdxf.new('R2018', setup=True); setup(doc); msp = doc.modelspace()
LYR = lambda l: {'layer': l}
SW = 300          # sidewalk above store floor (mm)
def rect(x0, y0, x1, y1, l):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs=LYR(l))
def arch(cx, y0, w, h, l, close=True):
    r = w/2; pts = [(cx-r, y0)] + [(cx-r*math.cos(math.pi*k/48), y0+h-r+r*math.sin(math.pi*k/48)) for k in range(49)] + [(cx+r, y0)]
    return msp.add_lwpolyline(pts, close=close, dxfattribs=LYR(l))
def txt(s, x, y, h, l='A-TEKSTAS', al=TA.MIDDLE_CENTER, width=1.0):
    t = msp.add_text(s, height=h, dxfattribs={'layer': l, 'style': TXT, 'width': width}); t.set_placement((x, y), align=al); return t

def window(ox, variant):
    W = 1192; H0 = 900; H1 = 6000; pier = 1300
    # facade piers (rusticated stone), sidewalk
    for x0 in (ox-pier, ox+W):
        rect(x0, 0, x0+pier, H1+400, 'A-PJUVIS-SIENOS')
        h = msp.add_hatch(color=7, dxfattribs=LYR('A-PERDANGA-UZP')); h.set_pattern_fill('LINE', scale=130, angle=0)   # rustication courses
        h.paths.add_polyline_path([(x0, 0), (x0+pier, 0), (x0+pier, H1+400), (x0, H1+400)], is_closed=True)
    rect(ox, 0, ox+W, H0, 'A-PJUVIS-SIENOS')                                         # parapet below window
    msp.add_line((ox-pier-600, -SW+SW), (ox+W+pier+600, 0), dxfattribs=LYR('A-PJUVIS-SIENOS'))
    # frame + glass
    rect(ox, H0, ox+W, H1, 'A-MATOMOS-ARTI'); rect(ox+50, H0+50, ox+W-50, H1-50, 'A-MATOMOS-ARTI')
    msp.add_line((ox+50, 3600), (ox+W-50, 3600), dxfattribs=LYR('A-MATOMOS-ARTI')); msp.add_line((ox+50, 3650), (ox+W-50, 3650), dxfattribs=LYR('A-MATOMOS-ARTI'))
    # arch backdrop panel + LED halo
    aw = W-260; ah = 2750
    arch(ox+W/2, H0, aw, ah, 'A-MATOMOS-ARTI'); arch(ox+W/2, H0, aw+40, ah+20, 'A-VIRS-PJUVIO', close=False).dxf.ltscale = 0.4
    # plinths (travertine cylinders) Ø400 h650, Ø480 h400, Ø340 h220
    for (h, d, dx) in [(650, 400, -220), (400, 480, 180), (220, 340, -20)]:
        rect(ox+W/2+dx-d/2, H0, ox+W/2+dx+d/2, H0+h, 'A-PJUVIS-BALDAI')
    if variant == 'B':   # giant gold hoop earring Ø720 suspended on steel wire
        cy = H0+2250; msp.add_circle((ox+W/2, cy), 360, dxfattribs=LYR('A-PJUVIS-BALDAI')); msp.add_circle((ox+W/2, cy), 328, dxfattribs=LYR('A-PJUVIS-BALDAI'))
        msp.add_line((ox+W/2, cy+360), (ox+W/2, H1-50), dxfattribs=LYR('A-MATOMOS-TOLI'))
    # vinyl wordmark on glass (gold metallic film), eye level from sidewalk
    yv = 2150
    txt('MARI', ox+W/2, yv, 160, 'A-PJUVIS-BALDAI', width=1.35); txt('MADE', ox+W/2, yv-130, 45, 'A-PJUVIS-BALDAI', width=1.6)
    # dimensions
    ds = 'ISO-50'; dl = LYR('A-MATMENYS')
    msp.add_linear_dim(base=(0, H1+900), p1=(ox, H1), p2=(ox+W, H1), dimstyle=ds, dxfattribs=dl).render()
    msp.add_linear_dim(base=(0, H1+600), p1=(ox+W/2-aw/2, H0+ah), p2=(ox+W/2+aw/2, H0+ah), dimstyle=ds, dxfattribs=dl).render()
    msp.add_multi_point_linear_dim(base=(ox-pier-500, 0), points=[(ox, 0), (ox, H0), (ox, H0+ah), (ox, H1)], angle=90, dimstyle=ds, dxfattribs=dl)
    msp.add_multi_point_linear_dim(base=(ox+W+pier+450, 0), points=[(ox+W, 0), (ox+W, yv-160), (ox+W, yv+120)] + ([(ox+W, H0+2250-360), (ox+W, H0+2250+360)] if variant == 'B' else []),
                                   angle=90, dimstyle=ds, dxfattribs=dl)
    # callouts
    notes = [(H0+ah-300, 'Arkinė panelė, aksomas ' + ('bordo' if variant == 'A' else 'nude')), (H0+ah+40, 'LED aureolė 2700K'), (yv, 'Aukso plėvelė „MARI MADE"'),
             (H0+500, 'Travertino podiumai')] + ([(H0+2250, 'Auskaras-žiedas Ø720, žalvaris')] if variant == 'B' else [])
    for y, s in notes:
        x1 = ox+W+pier+1250
        msp.add_line((ox+W/2+150, y), (x1-60, y), dxfattribs=LYR('A-MATMENYS')); txt(s, x1, y, 2.2*50, al=TA.MIDDLE_LEFT)
window(1700, 'A'); window(1700+6400, 'B')
txt('Atskaitos linija – parduotuvės grindų lygis -2,000. Šaligatvio lygį ir vitrinų stiklo matmenis tikslinti vietoje.', 400, -2400, 2.2*50, al=TA.MIDDLE_LEFT)
txt('Plėvelė – metalizuota aukso spalvos lipni plėvelė stiklo vidinėje pusėje, šriftas pagal MARI MADE logotipą.', 400, -2750, 2.2*50, al=TA.MIDDLE_LEFT)
txt('VARIANTAS A', 1700+596, -1300, 3.5*50); txt('bordo arka, prekės ženklas ant stiklo', 1700+596, -1700, 2.5*50)
txt('VARIANTAS B', 8100+596, -1300, 3.5*50); txt('nude arka, auksinis auskaras-žiedas', 8100+596, -1700, 2.5*50)
psp = new_layout(doc, '09_VITRINOS ISKLOTINES', 'A3')
for old in ('Layout1',):
    if old in doc.layouts.names(): doc.layouts.delete(old)
frame(psp, 'A3')
from ezdxf import bbox as _bb
E = _bb.extents(msp); vw, vh = E.size.x/50+10, E.size.y/50+10
vp = psp.add_viewport(center=(25+vw/2, 75+vh/2), size=(vw, vh), view_center_point=(E.center.x, E.center.y), view_height=vh*50, dxfattribs={'layer': 'S-VIEWPORT'})
if STAMP:
    title_block(psp, 'A3', dict(objektas='Prekybos centras GO9, Gedimino pr. 9, Vilnius', patalpa='Parduotuvė MARI MADE – vitrinos koncepcija',
                uzsakovas='Vilniaus dizaino kolegija', stadija='Koncepcija', atliko='Gabrielė Meilūnaitė', tikrino='', data='2026-11',
                mastelis='1:50', lapas=9, lapu=9, brezinys='VITRINŲ IŠKLOTINĖS'))
sheet_title(psp, 25, 40, 'VITRINŲ IŠKLOTINĖS', 'M 1:50')
p = f'{OUT}/VITRINOS_ISKLOTINES.dxf'; doc.saveas(p)
export_pdf(doc, ['09_VITRINOS ISKLOTINES'], f'{OUT}/VITRINOS_ISKLOTINES.pdf'); print('ok')
