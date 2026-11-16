"""Kasos baldo parametrai (mm). Bendri 3D modeliui ir brėžiniams.

Koordinatės: X – ilgis (centras 0), Y – gylis (-Y = kliento pusė / priekis,
+Y = darbuotojo pusė / galas), Z – aukštis nuo grindų.
Žiūrint iš darbuotojo pusės: +X yra KAIRĖJE, -X – DEŠINĖJE.
"""
import math

# --- Bendri matmenys (pagal SketchUp modelį) ---
L_TOP = 2159.0          # stalviršio ilgis
D_TOP = 767.0           # stalviršio plotis (gylis)
T_TOP = 40.0            # stalviršio storis
H_TOTAL = 1141.0        # bendras aukštis su stalviršiu
OVERHANG = 30.0         # stalviršio iškyša virš korpuso

L_BODY = L_TOP - 2 * OVERHANG      # 2099
D_BODY = D_TOP - 2 * OVERHANG      # 707
H_BODY = H_TOTAL - T_TOP           # 1101
R_BODY = D_BODY / 2                # 353.5
R_TOP = D_TOP / 2                  # 383.5
A_STRAIGHT = (L_BODY - D_BODY) / 2  # 696 – tiesios dalies pusė

Y_FRONT = -D_BODY / 2   # -353.5 korpuso priekis (klientas)
Y_BACK = D_BODY / 2     # +353.5 korpuso galas (darbuotojas)

# --- Rievėta (fliutuota) priekio panelė ---
FLUTE_HALF = 596.0
FLUTE_N = 40
FLUTE_R = (2 * FLUTE_HALF) / FLUTE_N / 2   # 14.9
BASE_H = 40.0           # tamsiai rudas cokolis apačioje (įtrauktas 10 mm)
FLUTE_Z0 = BASE_H

# --- Darbuotojo zona: lenkta išpjova viršutiniame stalviršyje ---
ARC_HALF = 650.0                 # lanko galai stalviršio gale: x = ±650
LEDGE_DEPTH = 300.0              # kliento atramos gylis per vidurį
ARC_APEX_Y = -D_TOP / 2 + LEDGE_DEPTH          # -83.5
_s = R_TOP - ARC_APEX_Y                         # lanko aukštis (467)
R_ARC_TOP = (ARC_HALF ** 2 + _s ** 2) / (2 * _s)  # ~685.9
ARC_CY = ARC_APEX_Y + R_ARC_TOP                 # lanko centras y (~602.4)
ARC_BULGE = _s / ARC_HALF                       # DXF bulge
WALL_SETBACK = 30.0                             # atrama išsikiša virš lenktos sienelės
R_ARC_WALL = R_ARC_TOP + WALL_SETBACK           # lenkta vidinė sienelė
CAV_HALF = round(math.sqrt(R_ARC_WALL ** 2 - (ARC_CY - Y_BACK) ** 2))  # 671 – angos pusė korpuse

T_FRONTWALL = 18.0
Y_INNER_FRONT = Y_FRONT + T_FRONTWALL      # -335.5

WORK_TOP_Z = 900.0      # darbo stalviršio viršus
T_WORK = 40.0
WORK_Y1 = Y_BACK + OVERHANG                # 383.5 (30 mm iškyša)


def arc_wall_y(x):
    """Lenktos sienelės y koordinatė ties x."""
    return ARC_CY - math.sqrt(R_ARC_WALL ** 2 - x ** 2)


def arc_top_y(x):
    return ARC_CY - math.sqrt(R_ARC_TOP ** 2 - x ** 2)


GROMMET_D = 60.0
GROMMETS_WORK = [(-350.0, 80.0), (350.0, 80.0)]       # darbo stalviršyje
GROMMETS_LEDGE = []                                   # (pašalinta pagal pakeistą modelį)

# --- Po darbo stalviršiu ---
T = 18.0                # LMDP storis
LEG_H = 100.0           # reguliuojamos kojelės, cokolis
PLINTH_SETBACK = 60.0
T_PLINTH = 16.0
BOTTOM_Z0 = LEG_H                 # 100
BOTTOM_Z1 = LEG_H + T             # 118
TOPRAIL_Z1 = WORK_TOP_Z - T_WORK  # 860
GAP = 3.0
FRONT_Z0 = BOTTOM_Z0 + GAP        # 103
FRONT_Z1 = TOPRAIL_Z1 - GAP       # 857
FRONT_Y1 = Y_BACK                 # fasadai lygūs su korpusu
FRONT_Y0 = Y_BACK - T             # 335.5
CARC_Y0 = Y_INNER_FRONT           # korpusų galas

# Stalčių blokas – darbuotojo KAIRĖJE (+X)
PED_W = 400.0
PED_X0 = CAV_HALF - PED_W         # ~271
PED_X1 = CAV_HALF
DRAWER_H = [328.0, 260.0, 160.0]  # fasadų aukščiai nuo apačios
DRAWER_LEN = 500.0                # kreipiančiųjų ilgis

# Spintelė – darbuotojo DEŠINĖJE (-X), viena durelė, lentyna
CAB_W = 400.0
CAB_X0 = -CAV_HALF
CAB_X1 = -CAV_HALF + CAB_W        # ~-271
SHELF_Z0 = 470.0
SHELF_BACK_GAP = 20.0
SHELF_DEPTH = 560.0

# Vieta kojoms tarp blokų, su galine (kojų) panele
KNEE_PANEL_Y1 = -150.0
KNEE_PANEL_Y0 = KNEE_PANEL_Y1 - T

# Durelė
DOOR_X_OUT = CAB_X0 + 1.5          # vyrių pusė (prie korpuso)
DOOR_X_IN = CAB_X1 - 1.5           # atidarymo kraštas (prie kojų vietos)

# Vyriai (Blum CLIP top 110°, be spyruoklės – TIP-ON variantui)
HINGE_FROM_EDGE = 100.0
CUP_D = 35.0
CUP_DEPTH = 13.0
CUP_C = 4.0

# TIP-ON (Blum, durims) – į spintelės vidinio šono (prie kojų vietos) vidų
TIPON_LEN = 76.0
TIPON_W = 20.0
TIPON_H = 26.0
TIPON_FROM_TOP = 70.0
TIPON_Z = FRONT_Z1 - TIPON_FROM_TOP          # 787
TIPON_X = CAB_X1 - T - 2 - TIPON_W / 2       # ašis (spintelės viduje)


def door_width():
    return DOOR_X_IN - DOOR_X_OUT


def door_height():
    return FRONT_Z1 - FRONT_Z0


def drawer_fronts():
    """[(z0, z1), ...] nuo apačios."""
    out, z = [], FRONT_Z0
    for h in DRAWER_H:
        out.append((z, z + h))
        z += h + GAP
    return out


# --- Pakeitimai pagal Kasos_baldas.blend (v3) ---
FLUTE_NICHE_HALF = 600.0     # rievių niša priekyje: ~1200 pločio (R10 kampai)
FLUTE_NICHE_DEPTH = 14.0     # nišos gylis
HANDLE_W = 200.0             # stalčių rankenėlės (metalinės, išsikišusios)
HANDLE_H = 10.0
HANDLE_PROJ = 12.0           # išsikišimas nuo fasado
HANDLE_X0, HANDLE_X1 = 371.0, 571.0
HANDLE_FROM_TOP = 12.0       # nuo stalčiaus fasado viršaus iki rankenėlės viršaus
WORK_CORNER_R = 28.4         # darbo stalviršio galiniai kampai
