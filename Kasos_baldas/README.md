# Kasos baldo detalizacija

Aksesuarų parduotuvės kasos baldas. Darbuotojo zonoje padarytas įgilinimas su darbo stalviršiu ir spintele su atšokančiomis durimis (push-to-open).

## Failai

| Aplankas | Kas viduje |
|---|---|
| `Breziniai/` | 2D brėžiniai **DXF** formatu (AutoCAD 2018). Atsidaro AutoCAD, DraftSight, LibreCAD ir SketchUp programose; norint `.dwg`, AutoCAD'e: *Save As → DWG*. |
| `Breziniai/PDF_perziura/` | Tų pačių brėžinių PDF peržiūra |
| `Renderiai/` | 4 vaizdai baltame fone (2 iš kliento, 2 iš darbuotojo pusės) + mazgo vaizdas |
| `3D_modelis/` | Pakoreguotas modelis: `Kasos_baldas.dae` (importuoti į SketchUp), `.obj`, `.blend` |
| `scripts/` | Skriptai, kurie viską sugeneruoja (`params.py` – visi matmenys vienoje vietoje) |

### Brėžiniai
1. `01_Vaizdas_is_virsaus_M1-50` – vaizdas iš viršaus
2. `02_Vaizdas_is_priekio_M1-50` – vaizdas iš priekio (kliento pusė)
3. `03_Vaizdas_is_galo_M1-50` – vaizdas iš galo (darbuotojo pusė)
4. `04_Mazgas_TIP-ON_pjuvis_A-A_M1-2` – mazgas: horizontalus pjūvis per atšokimo mechanizmą, rodyklėmis parodytas veikimas
5. `05_Mazgas_duru_vyriai_TIP-ON_M1-10` – durų vidinė pusė: kur gręžti vyrių taureles, kur dėti TIP-ON plokštelę; furnitūros sąrašas

Brėžiniai nubraižyti mastelyje 1:1 (mm). Matmenų stilius pritaikytas spausdinti nurodytu masteliu.

## Pagrindiniai sprendimai

| Elementas | Sprendimas |
|---|---|
| Bendri matmenys | 2159 × 767 mm, aukštis 1141 mm (kaip modelyje) |
| Kliento atrama | Viršutinis stalviršis (medis, 40 mm, h = 1141). Darbuotojo zonoje jis išpjautas, kliento pusėje lieka 300 mm gylio atrama |
| Darbuotojo zona (įgilinimas) | Anga 1300 mm pločio. Darbo stalviršis h = **900 mm** (medis, 40 mm), už korpuso iškištas 30 mm |
| Niša po atrama | 201 mm aukščio, popieriams, čekių spausdintuvui ir pan. |
| Kabelių angos | Ø60, 3 vnt.: 2 darbo stalviršyje (kasos aparatui, monitoriui), 1 atramoje (mokėjimo terminalui) |
| Spintelė | Po darbo stalviršiu, per visą angos plotį. Su vidurine pertvara ir 1 reguliuojama lentyna kiekvienoje pusėje. Korpusas LMDP 18 mm |
| Durys | 2 vnt., 647 × 754 mm, LMDP 18 mm, be rankenų, atsidaro į šonus. Tarpas tarp jų 3 mm |
| Atšokimo mechanizmas | Blum TIP-ON durims, prisuktas prie vidurinės pertvaros šono, 70 mm nuo durų viršaus. Vyriai Blum CLIP top 110° **be spyruoklės** |
| Pagrindas | Reguliuojamos kojelės h = 100 mm. Cokolis įtrauktas 60 mm, kad stovint būtų vietos pėdoms |

## Kaip sugeneruoti iš naujo
```bash
pip install ezdxf matplotlib
python3 scripts/gen_dxf.py Breziniai
blender -b -P scripts/build_blender.py -- <renderiu_aplankas> scripts/tex          # vaizdai
MODE=detail blender -b -P scripts/build_blender.py -- <renderiu_aplankas> scripts/tex
MODE=export blender -b -P scripts/build_blender.py -- 3D_modelis scripts/tex
python3 scripts/finish_renders.py <renderiu_aplankas> Renderiai
```
