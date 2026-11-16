"""Kasos baldo parametrai, v4 (MARI MADE dizainas). Visi matmenys mm.

Koordinatės: X – ilgis (centras 0), Y – gylis (-Y = kliento pusė / priekis,
+Y = darbuotojo pusė / galas), Z – aukštis nuo grindų.
Žiūrint iš darbuotojo pusės: +X yra KAIRĖJE, -X – DEŠINĖJE.
"""

# --- Bendri ---
L_TOP = 3000.0
D_TOP = 767.0
T_TOP = 50.0              # akmens stalviršis
H_TOTAL = 1141.0
OVERHANG = 30.0

L_BODY = L_TOP - 2 * OVERHANG       # 2940
D_BODY = D_TOP - 2 * OVERHANG       # 707
H_BODY = H_TOTAL - T_TOP            # 1091
R_BODY = D_BODY / 2                 # 353.5
R_TOP = D_TOP / 2                   # 383.5
A_STRAIGHT = (L_BODY - D_BODY) / 2  # 1116.5
Y_FRONT = -D_BODY / 2
Y_BACK = D_BODY / 2

BASE_H = 80.0             # žalvarinis cokolis (įtrauktas 10 mm)
BASE_SETBACK = 10.0

# --- Kliento pusė: rievės nišoje + logotipas ---
FLUTE_HALF = 950.0
FLUTE_N = 63
FLUTE_R = (2 * FLUTE_HALF) / FLUTE_N / 2       # ~15.08
FLUTE_NICHE_DEPTH = 14.0
FLUTE_NICHE_R = 10.0
LOGO_Z = 640.0            # „MARI“ centras
LOGO_H1 = 150.0           # „MARI“ raidžių aukštis
LOGO_H2 = 60.0            # „MADE“

# --- Darbuotojo zona ---
CUT_HALF = 1050.0         # stalviršio išpjova x = ±1050 (plotis 2100)
LEDGE_DEPTH = 300.0       # kliento atrama
CUT_Y0 = -D_TOP / 2 + LEDGE_DEPTH      # -83.5
CUT_R = 250.0             # vidiniai išpjovos kampai
CUT_FILLET = 30.0         # išoriniai (įėjimo) kampai
WALL_SETBACK = 30.0       # atrama išsikiša virš nišos sienelės
CAV_HALF = CUT_HALF + WALL_SETBACK     # 1080 – anga korpuse
Y_INNER_FRONT = Y_FRONT + 18.0         # -335.5

WORK_TOP_Z = 900.0
T_WORK = 40.0
WORK_Y1 = Y_BACK + OVERHANG            # 383.5
WORK_CORNER_R = 30.0
NICHE_TOP_Z = H_BODY                   # 1091 (nišos aukštis 191)

GROMMET_D = 60.0
GROMMETS_WORK = [(300.0, 20.0), (-450.0, 20.0)]

# --- Po darbo stalviršiu ---
T = 18.0
PLINTH_H = 80.0           # žalvarinis cokolis po spintelėmis
GAP = 3.0
CARC_Z0 = PLINTH_H                     # dugno apačia
TOPRAIL_Z1 = WORK_TOP_Z - T_WORK       # 860
FRONT_Z0 = PLINTH_H + GAP              # 83
FRONT_Z1 = TOPRAIL_Z1 - GAP            # 857
FRONT_Y1 = Y_BACK
FRONT_Y0 = Y_BACK - T                  # 335.5
CARC_Y0 = Y_INNER_FRONT

# Stalčių blokas – darbuotojo kairėje (+X)
PED_X1 = CAV_HALF                      # 1080
PED_X0 = CAV_HALF - 600.0              # 480
N_DRAWERS = 5
DRAWER_LEN = 500.0
HANDLE_W = 250.0
HANDLE_D = 12.0           # žalvarinio strypo skersmuo
HANDLE_PROJ = 30.0        # išsikišimas
HANDLE_FROM_TOP = 45.0    # rankenėlės ašis nuo fasado viršaus

# Vieta kojoms
KNEE_X0, KNEE_X1 = -180.0, PED_X0      # 660
KNEE_PANEL_Y1 = -150.0

# Dešinysis blokas (-X): R1 – nišelė kasos stalčiui + durelė, R2 – atviros lentynos
BLK_X0, BLK_X1 = -CAV_HALF, KNEE_X0    # -1080 .. -180
MID_X0, MID_X1 = -639.0, -621.0        # vidurinė pertvara
CUBBY_SHELF_Z0 = 659.0                 # lentyna virš durelės
R2_SHELVES = [400.0, 659.0]
DOOR_X_OUT = MID_X0 + 10.5             # vyrių pusė (-628.5)
DOOR_X_IN = BLK_X1 - 1.5               # atidarymo kraštas (-181.5)
DOOR_Z0 = FRONT_Z0
DOOR_Z1 = CUBBY_SHELF_Z0 - GAP         # 656
SHELF_Z0 = 370.0                       # lentyna už durelės
SHELF_BACK_GAP = 20.0
SHELF_DEPTH = 560.0

# Vyriai ir TIP-ON (durelė)
HINGE_FROM_EDGE = 100.0
CUP_D = 35.0
CUP_DEPTH = 13.0
CUP_C = 4.0
TIPON_LEN = 76.0
TIPON_W = 20.0
TIPON_H = 26.0
TIPON_FROM_TOP = 70.0
TIPON_Z = DOOR_Z1 - TIPON_FROM_TOP     # 586
TIPON_X = BLK_X1 - T - 2 - TIPON_W / 2  # -210

LOCK_D = 20.0
LOCK_FROM_TOP = 160.0     # durelės spynelė (žemiau TIP-ON plokštelės)
LOCK_FROM_EDGE = 45.0


def door_width():
    return DOOR_X_IN - DOOR_X_OUT


def door_height():
    return DOOR_Z1 - DOOR_Z0


def drawer_fronts():
    h = (FRONT_Z1 - FRONT_Z0 - (N_DRAWERS - 1) * GAP) / N_DRAWERS
    return [(FRONT_Z0 + i * (h + GAP), FRONT_Z0 + i * (h + GAP) + h) for i in range(N_DRAWERS)]
