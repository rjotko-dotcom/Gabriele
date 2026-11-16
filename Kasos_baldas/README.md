# Kasos baldas „MARI MADE“

Aksesuarų parduotuvės kasos baldas (v4). Kliento pusėje – bordo rievės su žalvariniu logotipu. Darbuotojo pusėje:
- įgilinta darbo zona su 900 mm aukščio stalviršiu;
- stalčių blokas (5 stalčiai);
- vieta kojoms;
- nišelė kasos stalčiui;
- spintelė su atšokančia (push-to-open) durele;
- atviros lentynos.

## Failai

| Aplankas | Kas viduje |
|---|---|
| `Breziniai/` | 2D brėžiniai **DXF** formatu (AutoCAD 2018) – **tik pats baldas** (be kompiuterio, maišelių, kėdės). AutoCAD'e: *Save As → DWG* |
| `Breziniai/PDF_perziura/` | Tų pačių brėžinių PDF |
| `3D_modelis/Kasos_baldas.dae` | **SketchUp'ui** – baldas su visais daiktais ir kėde (+ `akmuo_Color.jpg`, `rozinis_BaseColor.jpg` tame pačiame aplanke) |
| `3D_modelis/Kasos_baldas.blend` | Blender 4.5 modelis (tekstūros įpakuotos) |
| `Renderiai/` | 4 vaizdai + mechanizmo vaizdas |
| `scripts/` | Skriptai, kurie viską sugeneruoja; matmenys – `params.py` |

### Brėžiniai
1. `01_Vaizdas_is_virsaus_M1-50`
2. `02_Vaizdas_is_priekio_M1-50` (kliento pusė)
3. `03_Vaizdas_is_galo_M1-50` (darbuotojo pusė)
4. `04_Vaizdas_is_sono_M1-50`
5. `05_Mazgas_TIP-ON_pjuvis_A-A_M1-2` – atšokančios durelės mechanizmas, pjūvis, veikimas
6. `06_Mazgas_dureles_vyriai_TIP-ON_M1-10` – vyrių, TIP-ON ir spynelės padėtis; furnitūros sąrašas

## Pagrindiniai matmenys ir sprendimai

| Elementas | Sprendimas |
|---|---|
| Bendri matmenys | **3000 × 767 mm, aukštis 1141 mm** (ilgis – pagal pavyzdinį vaizdą) |
| Stalviršis | Kreminis akmuo (kvarcas), 50 mm, suapvalinta briauna, apačioje LED juosta. Darbuotojo pusėje išpjova 2100 mm, kliento atrama 300 mm, kampai R250 / R30 |
| Darbo stalviršis | h = **900 mm**, tas pats akmuo 40 mm, 2160 mm pločio. Niša po atrama – 191 mm su LED |
| Po darbo stalviršiu (žiūrint darbuotojui) | **Kairėje** – stalčių blokas 600 mm, 5 stalčiai, žalvarinės rankenėlės 250 mm, spynelė viršutiniame. **Viduryje** – vieta kojoms 660 mm. **Dešinėje** – 450 mm: nišelė kasos pinigų stalčiui ir durelė su TIP-ON bei spynele; dar 450 mm – atviros lentynos |
| Mechanizmas | Blum TIP-ON ant spintelės šono prie vietos kojoms, 70 mm nuo durelės viršaus; vyriai CLIP top 110° be spyruoklės |
| Medžiagos | Galai – pudrinės rožinės mikrotekstūros apdaila; rievės, fasadai, korpusai – bordo matinis laminatas; cokolis, rankenėlės, logotipas – žalvaris |
| Cokolis | Žalvarinis, 80 mm, įtrauktas 10 mm |

Kėdė – padidinto aukščio (sėdynė ~650 mm su kojų žiedu), nes darbo stalviršis yra 900 mm.

Tekstūros: [ambientCG](https://ambientcg.com) (CC0) – Marble020; rožinė – iš Gabrielės modelio. Šriftas: Liberation Sans.

## Kaip sugeneruoti iš naujo (Blender 4.5)
```bash
pip install ezdxf matplotlib shapely
cd scripts && python3 geom.py && cd ..
python3 scripts/gen_dxf.py Breziniai
blender -b -P scripts/build_v4.py -- <renderiai>                 # 4 vaizdai
MODE=detail blender -b -P scripts/build_v4.py -- <renderiai>     # mechanizmas
python3 scripts/finish_renders.py <renderiai> Renderiai
MODE=export blender -b -P scripts/build_v4.py -- 3D_modelis       # .blend
blender -b 3D_modelis/Kasos_baldas.blend -P scripts/export_sketchup.py -- 3D_modelis
```
Senesnių versijų skriptai (`build_blender.py`, `render_blend.py`, `extract_sections.py`) palikti istorijai.
