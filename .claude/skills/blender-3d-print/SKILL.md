---
name: blender-3d-print
description: Use when designing functional, modern-looking parts for FDM 3D printing in Blender (boxes, trays, organizers, cabinets, holders, brackets) – parametric bpy/bmesh scripts, print tolerances, joints (dovetails, snap-fits, M3 screws / heat-set inserts), label holders, STL export, validation and preview renders.
---

# Blender → 3D spausdinimas (FDM)

Projekto pavyzdys: `blender/raktu_deze.py` (generatorius) ir `blender/render.py` (peržiūros renderiai).
Naujus modelius daryk tuo pačiu stiliumi.

## Darbo eiga
1. **Matmenys ir paskirtis pirmiausia.** Išsiaiškink išorinius matmenis, spausdintuvo lauką
   (dažniausiai 220–256 mm), medžiagą (PLA/PETG), kaip detalė tvirtinama ir kas turi nesimatyti.
2. **Parametrinis skriptas, ne rankinis modeliavimas.** Visi matmenys – konstantos failo viršuje (mm,
   1 Blender vienetas = 1 mm, `scene.unit_settings.scale_length = 0.001`).
3. **Geometrija iš žiedų (loft).** Suapvalinti stačiakampiai + profiliai `(z, inset)` duoda švarius
   apvalinimus be Bevel modifikatoriaus. Iškirtimai – atskiri "cutter" kūnai, boolean su
   `solver = "MANIFOLD"` (atsarginis – `"EXACT"`), pritaikoma per `new_from_object(evaluated)`
   (veikia ir be GUI konteksto).
4. **Eksportas.** Kiekviena dalis – atskiras STL jau spausdinimo orientacija. Tekstas dviem
   spalvoms – atskiras STL.
5. **Patikra prieš atiduodant:** `trimesh` → `is_watertight == True`, `extents` = norimi matmenys;
   Cycles renderis iš priekio ir iš apačios, peržiūrėk akimis.

## Modernaus vaizdo taisyklės
- Dideli kampų spinduliai iš viršaus (R 12–20 mm), sienelės 4–6 mm, pilnai apvalus viršutinis kraštas
  (išorinis + vidinis apvalinimas ≈ sienelės storis).
- Vidinis dugno apvalinimas 6–10 mm (lengva išimti daiktus, lengva valyti).
- Minkštos S formos įdubos (cos kreivė) vietoj aštrių iškirpimų; jų briaunas apvalink 1.5–2 mm.
- Etiketė – įleista, lygiai su paviršiumi, 0.4 mm nuožula; šriftas Inter SemiBold, didžiosios
  raidės, `space_character ≈ 1.1`.
- Funkcinės detalės (varžtai, jungtys) – iš apačios arba ten, kur nesimato.
- **Nedėk funkcijų, kurių neprašė** (skylių, griovelių, jungčių) – vartotojas nori lygių, švarių paviršių.
  Pasiūlyk žodžiu, modeliuok tik patvirtinus.
- Matmenis visada susiek su etikete / priekiu („ilgis nuo etiketės iki galo“), patikrink, kuri
  sienelė yra priekis, prieš pradėdamas modeliuoti.
- Keičiama etiketė: liežuvėlis viršuje į paslėptą plyšį + spragtelėjimas apačioje + nago įpjova
  (žr. `blender/raktu_deze.py`, `label_base`). Patikrink pjūviu (`trimesh.section`) ir ar
  rėmelis nesikerta su dėžute (`trimesh.boolean.intersection`, tūris = 0).

## Tolerancijos (FDM, 0.4 mm antgalis)
| Kas | Reikšmė |
|---|---|
| Slankioji jungtis (dovetail) | 0.15 mm vienai pusei |
| Spragtelėjimas (snap) | iškilimas r 0.4 į griovelį r 0.5 |
| Įstatoma dalis į kišenę | 0.2 mm iš visų pusių |
| M3 įlydoma įvorė (M3×5.7) | skylė Ø4.0, gylis 6 mm, ≥2 mm likusi sienelė |
| M3 tiesiai į plastiką | Ø2.6 |
| M3 laisva skylė | Ø3.4 |
| Apatinė nuožula (elephant foot) | 0.5–0.8 mm |

## Spausdinimo taisyklės
- Iškyšos ≤ 45°; tiltai ≤ ~15 mm be atramų; venk didelių uždarų lubų (spausdinti be atramų).
- Dovetail kampas ~30° nuo vertikalės – spausdinasi be atramų.
- Ilgos plonos dalys – gulint.

## Komandos
```bash
python blender/raktu_deze.py --out .        # pip install bpy  (arba: blender -b -P ... -- --out .)
python blender/render.py --out renders
```
