# Shared CAD standards: ISO 128 line weights, ISO 5457 frame, ISO 7200 title block, A3/A2 layouts 1:50, PDF export
import ezdxf, math
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

SCALE = 50
TXT = 'ISO_ARIAL'
# name: (aci color, lineweight 1/100 mm, linetype, plot)
LAYERS = {
    'A-PJUVIS-SIENOS':      (7, 50, 'Continuous', True),   # cut walls / structure
    'A-PJUVIS-SIENOS-UZP':  (8, 13, 'Continuous', True),   # poche fill of cut walls
    'A-PJUVIS-BALDAI':      (7, 35, 'Continuous', True),   # cut furniture / joinery
    'A-MATOMOS-ARTI':       (7, 25, 'Continuous', True),   # visible edges, near
    'A-MATOMOS-TOLI':       (7, 18, 'Continuous', True),   # visible edges, background
    'A-VIRS-PJUVIO':        (7, 18, 'A-BRUKSNINE', True),  # elements above cut plane (dashed)
    'A-AUGALAI':            (7, 18, 'Continuous', True),
    'A-PERDANGA-UZP':       (8, 13, 'Continuous', True),   # slab / ground hatch
    'A-MATMENYS':           (7, 18, 'Continuous', True),
    'A-ALTITUDES':          (7, 18, 'Continuous', True),
    'A-TEKSTAS':            (7, 25, 'Continuous', True),
    'A-PJUVIO-ZYMES':       (7, 50, 'Continuous', True),
    'A-LENTELES':           (7, 18, 'Continuous', True),   # table inner lines
    'A-LENTELES-REMAS':     (7, 50, 'Continuous', True),   # table outer frame
    'S-RAMELIS':            (7, 70, 'Continuous', True),   # ISO 5457 drawing frame
    'S-STAMPAS':            (7, 25, 'Continuous', True),
    'S-STAMPAS-REMAS':      (7, 50, 'Continuous', True),
    'S-TEKSTAS':            (7, 25, 'Continuous', True),
    'S-VIEWPORT':           (8, 13, 'Continuous', False),  # non-plotting viewport frames
}

def setup(doc):
    doc.header['$INSUNITS'] = 4
    doc.header['$MEASUREMENT'] = 1
    doc.header['$LWDISPLAY'] = 1
    doc.header['$LTSCALE'] = 1.0
    doc.header['$PSLTSCALE'] = 0
    if TXT not in doc.styles:
        doc.styles.new(TXT, dxfattribs={'font': 'arial.ttf'})
    # linetypes defined for 1:50 (model units)
    if 'A-BRUKSNINE' not in doc.linetypes:
        doc.linetypes.add('A-BRUKSNINE', pattern=[225, 150, -75], description='Bruksnine __ __ __')
    if 'A-ASIS' not in doc.linetypes:
        doc.linetypes.add('A-ASIS', pattern=[750, 600, -75, 0, -75], description='Asine __ . __ .')
    for n, (c, lw, lt, plot) in LAYERS.items():
        if n not in doc.layers:
            l = doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
        else:
            l = doc.layers.get(n); l.color = c; l.dxf.lineweight = lw; l.dxf.linetype = lt
        l.dxf.plot = 1 if plot else 0
    setup_dimstyle(doc)

def setup_dimstyle(doc):
    name = 'ISO-50'
    if name in doc.dimstyles: return name
    ds = doc.dimstyles.new(name)
    ds.dxf.dimscale = SCALE
    ds.dxf.dimtxt = 2.5; ds.dxf.dimasz = 2.0; ds.dxf.dimtsz = 0
    ds.set_arrows(blk='ARCHTICK')
    ds.dxf.dimexe = 1.5; ds.dxf.dimexo = 1.0; ds.dxf.dimgap = 0.8
    ds.dxf.dimdec = 0; ds.dxf.dimtad = 1; ds.dxf.dimtih = 0; ds.dxf.dimtoh = 0
    ds.dxf.dimtxsty = TXT; ds.dxf.dimlunit = 2; ds.dxf.dimzin = 8
    ds.dxf.dimclrd = 256; ds.dxf.dimclre = 256; ds.dxf.dimclrt = 256
    ds.dxf.dimlwd = 18; ds.dxf.dimlwe = 18; ds.dxf.dimdle = 1.5
    return name

def text(space, s, x, y, h_paper, layer='A-TEKSTAS', align=TextEntityAlignment.LEFT, rot=0, scale=SCALE, bold=False):
    t = space.add_text(s, height=h_paper*scale, dxfattribs={'layer': layer, 'style': TXT, 'rotation': rot})
    t.set_placement((x, y), align=align)
    return t

def level_mark(space, x, y, value, side='R', lead=1400, layer='A-ALTITUDES', s=SCALE):
    """ISO 4067 / LST style level mark: triangle apex on level line, leader, value above."""
    h = 2.6*s; w = 1.5*s
    space.add_lwpolyline([(x, y), (x-w, y+h), (x+w, y+h), (x, y)], close=True, dxfattribs={'layer': layer})
    space.add_hatch(color=7, dxfattribs={'layer': layer}).paths.add_polyline_path([(x, y), (x, y+h), (x+w, y+h)], is_closed=True)
    d = 1 if side == 'R' else -1
    space.add_line((x-d*w*0.0, y+h), (x+d*lead, y+h), dxfattribs={'layer': layer})
    tx = x + d*(w+0.6*s)
    text(space, value, tx, y+h+0.6*s, 2.5, layer='A-TEKSTAS',
         align=TextEntityAlignment.BOTTOM_LEFT if d > 0 else TextEntityAlignment.BOTTOM_RIGHT)

def fmt_level(z_rel_floor, floor_abs=-2.0):
    v = round(z_rel_floor + floor_abs, 3)
    s = f'{abs(v):.3f}'.replace('.', ',')
    if abs(v) < 0.0005: return '±0,000'
    return ('+' if v > 0 else '-') + s

PAPER = {'A3': (420, 297), 'A2': (594, 420), 'A1': (841, 594)}

def frame(psp, fmt):
    W, H = PAPER[fmt]
    psp.add_lwpolyline([(0, 0), (W, 0), (W, H), (0, H)], close=True, dxfattribs={'layer': 'S-STAMPAS', 'lineweight': 13})
    psp.add_lwpolyline([(20, 10), (W-10, 10), (W-10, H-10), (20, H-10)], close=True, dxfattribs={'layer': 'S-RAMELIS'})
    # centring marks (ISO 5457)
    for (a, b) in [((W/2, 0), (W/2, 10)), ((W/2, H-10), (W/2, H)), ((0, H/2), (20, H/2)), ((W-10, H/2), (W, H/2))]:
        psp.add_line(a, b, dxfattribs={'layer': 'S-RAMELIS'})

TB_W, TB_H = 180, 56
def title_block(psp, fmt, info):
    W, H = PAPER[fmt]
    x0, y0 = W-10-TB_W, 10
    L = lambda a, b: psp.add_line(a, b, dxfattribs={'layer': 'S-STAMPAS'})
    psp.add_lwpolyline([(x0, y0), (x0+TB_W, y0), (x0+TB_W, y0+TB_H), (x0, y0+TB_H)], close=True, dxfattribs={'layer': 'S-STAMPAS-REMAS'})
    rows = [7, 7, 7, 7, 14, 7, 7]   # bottom -> top
    ys = [y0]
    for r in rows: ys.append(ys[-1]+r)
    for yy in ys[1:-1]: L((x0, yy), (x0+TB_W, yy))
    c1, c2, c3 = x0+24, x0+110, x0+132
    L((c1, y0), (c1, y0+TB_H))
    for k in range(0, 4): L((c2, ys[k]), (c2, ys[k+1])); L((c3, ys[k]), (c3, ys[k+1]))
    def put(s, x, y, h=2.5, lay='S-TEKSTAS'):
        t = psp.add_text(s, height=h, dxfattribs={'layer': lay, 'style': TXT}); t.set_placement((x, y), align=TextEntityAlignment.MIDDLE_LEFT)
    def lab(s, x, y): put(s, x+1.5, y, 1.8)
    mid = lambda k: (ys[k]+ys[k+1])/2
    # bottom rows
    lab('Data', x0, mid(0)); put(info['data'], c1+2, mid(0)); lab('Lapas', c2, mid(0)); put(f"{info['lapas']} / {info['lapu']}", c3+2, mid(0))
    lab('Tikrino', x0, mid(1)); put(info.get('tikrino', ''), c1+2, mid(1)); lab('Formatas', c2, mid(1)); put(fmt, c3+2, mid(1))
    lab('Atliko', x0, mid(2)); put(info['atliko'], c1+2, mid(2)); lab('Mastelis', c2, mid(2)); put(info['mastelis'], c3+2, mid(2))
    lab('Užsakovas', x0, mid(3)); put(info['uzsakovas'], c1+2, mid(3)); lab('Stadija', c2, mid(3)); put(info['stadija'], c3+2, mid(3), 2.2)
    lab('Brėžinys', x0, mid(4)); put(info['brezinys'], c1+2, mid(4), 4.0)
    lab('Patalpa', x0, mid(5)); put(info['patalpa'], c1+2, mid(5))
    lab('Objektas', x0, mid(6)); put(info['objektas'], c1+2, mid(6))

def sheet_title(psp, x, y, s, scale_txt='M 1:50'):
    t = psp.add_text(s, height=5.0, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t.set_placement((x, y), align=TextEntityAlignment.BOTTOM_LEFT)
    from ezdxf.fonts import fonts
    tw = fonts.make_font('LiberationSans-Regular.ttf', 5.0).text_width(s)*1.02
    psp.add_line((x, y-1.2), (x+tw, y-1.2), dxfattribs={'layer': 'S-STAMPAS-REMAS'})
    t2 = psp.add_text(scale_txt, height=3.5, dxfattribs={'layer': 'S-TEKSTAS', 'style': TXT}); t2.set_placement((x+tw+4, y), align=TextEntityAlignment.BOTTOM_LEFT)

def new_layout(doc, name, fmt):
    if name in doc.layouts.names(): doc.layouts.delete(name)
    W, H = PAPER[fmt]
    lay = doc.layouts.new(name)
    lay.page_setup(size=(W, H), margins=(0, 0, 0, 0), units='mm', scale=(1, 1))
    return lay

def viewport(psp, cx, cy, w, h, mcx, mcy):
    vp = psp.add_viewport(center=(cx, cy), size=(w, h), view_center_point=(mcx, mcy), view_height=h*SCALE,
                          dxfattribs={'layer': 'S-VIEWPORT'})
    vp.dxf.flags = vp.dxf.flags | 16384  # display locked
    return vp

def export_pdf(doc, layout_names, out_pdf):
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing import pymupdf, layout as dlayout
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LineweightPolicy, HatchPolicy, LinePolicy
    import pymupdf as fz
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR,
                        lineweight_policy=LineweightPolicy.ABSOLUTE, min_lineweight=0.09, line_policy=LinePolicy.ACCURATE)
    out = fz.open()
    for n in layout_names:
        psp = doc.layouts.get(n)
        be = pymupdf.PyMuPdfBackend()
        ctx = RenderContext(doc); ctx.set_current_layout(psp)
        Frontend(ctx, be, config=cfg).draw_layout(psp, finalize=True)
        W, H = psp.dxf_layout.dxf.paper_width, psp.dxf_layout.dxf.paper_height
        page = dlayout.Page(W, H, dlayout.Units.mm, margins=dlayout.Margins.all(0))
        data = be.get_pdf_bytes(page, settings=dlayout.Settings(fit_page=False, scale=1))
        out.insert_pdf(fz.open('pdf', data))
    out.save(out_pdf)
