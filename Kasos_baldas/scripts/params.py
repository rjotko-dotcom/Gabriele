"""Kasos baldo parametrai (mm). Bendri 3D modeliui ir brėžiniams.

Koordinatės: X – ilgis (centras 0), Y – gylis (-Y = kliento pusė / priekis,
+Y = darbuotojo pusė / galas), Z – aukštis nuo grindų.
"""

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
FLUTE_HALF = 596.0      # zona x = ±596
FLUTE_N = 40
FLUTE_R = (2 * FLUTE_HALF) / FLUTE_N / 2   # 14.9
FLUTE_Z0 = 20.0

# --- Darbuotojo zona (įgilinimas) ---
NICHE_HALF = 650.0      # anga x = ±650 (plotis 1300)
LEDGE_DEPTH = 300.0     # kliento atramos (viršutinio stalviršio) gylis išpjovos vietoje
NOTCH_Y0 = -D_TOP / 2 + LEDGE_DEPTH   # -83.5
T_FRONTWALL = 18.0
Y_INNER_FRONT = Y_FRONT + T_FRONTWALL      # -335.5

WORK_TOP_Z = 900.0      # darbo stalviršio viršus
T_WORK = 40.0
WORK_Y1 = Y_BACK + OVERHANG                # 383.5 (30 mm iškyša)

GROMMET_D = 60.0
GROMMETS_WORK = [(-450.0, -20.0), (450.0, -20.0)]     # darbo stalviršyje (už atramos)
GROMMETS_LEDGE = [(450.0, -233.5)]                    # kliento atramoje (mokėjimo terminalui)

# --- Spintelė ---
T = 18.0                # LMDP storis
SIDE_X0 = NICHE_HALF - T          # 632
LEG_H = 100.0           # reguliuojamos kojelės / cokolis
BOTTOM_Z0 = LEG_H                 # 100
BOTTOM_Z1 = LEG_H + T             # 118
TOPRAIL_Z1 = WORK_TOP_Z - T_WORK  # 860
TOPRAIL_Z0 = TOPRAIL_Z1 - T       # 842
PLINTH_SETBACK = 60.0
T_PLINTH = 16.0

GAP = 3.0               # tarpas tarp durų / viršuje
DOOR_Z0 = BOTTOM_Z0 + GAP          # 103
DOOR_Z1 = TOPRAIL_Z1 - GAP         # 857
DOOR_X_OUT = NICHE_HALF - 1.5      # 648.5
DOOR_X_IN = GAP / 2                # 1.5
DOOR_Y1 = Y_BACK                   # durų išorė lygi su korpusu
DOOR_Y0 = Y_BACK - T               # 335.5

SHELF_Z0 = 470.0
SHELF_BACK_GAP = 20.0
SHELF_DEPTH = 600.0

# Vyriai (Blum CLIP top 110°, be spyruoklės – TIP-ON variantui)
HINGE_FROM_EDGE = 100.0   # nuo durų viršaus/apačios iki vyrio ašies
CUP_D = 35.0
CUP_DEPTH = 13.0
CUP_C = 4.0               # gręžimo atstumas nuo durų krašto iki taurelės krašto

# TIP-ON (Blum, durims) – montuojamas į vidurinės pertvaros šoną
TIPON_LEN = 76.0
TIPON_W = 20.0
TIPON_H = 26.0
TIPON_FROM_TOP = 70.0     # nuo durų viršaus iki TIP-ON ašies
TIPON_Z = DOOR_Z1 - TIPON_FROM_TOP     # 787
TIPON_X = T / 2 + TIPON_W / 2           # 19 – TIP-ON ašis nuo baldo centro (abiem pusėm)


def door_width():
    return DOOR_X_OUT - DOOR_X_IN


def door_height():
    return DOOR_Z1 - DOOR_Z0
