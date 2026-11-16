# Kasos baldo detalizacija

Aksesuarų parduotuvės kasos baldas. Darbuotojo zonoje padarytas įgilinimas su darbo stalviršiu ir spintele su atšokančiomis durimis (push-to-open).

## Failai

| Aplankas | Kas viduje |
|---|---|
| `Breziniai/` | 2D brėžiniai **DXF** formatu (AutoCAD 2018). Atsidaro AutoCAD, DraftSight, LibreCAD ir SketchUp programose; norint `.dwg`, AutoCAD'e: *Save As → DWG*. |
| `Breziniai/PDF_perziura/` | Tų pačių brėžinių PDF peržiūra |
| `Renderiai/` | 4 vaizdai baltame fone (2 iš kliento, 2 iš darbuotojo pusės) + mazgo vaizdas |
| `3D_modelis/` | `Kasos_baldas_SketchUp.zip` (DAE + medžio tekstūra – išarchyvuoti ir importuoti į SketchUp), `.obj`, `.blend` (tekstūros įpakuotos) |
| `scripts/` | Skriptai, kurie viską sugeneruoja (`params.py` – visi matmenys vienoje vietoje) |

### Brėžiniai
1. `01_Vaizdas_is_virsaus_M1-50` – vaizdas iš viršaus
2. `02_Vaizdas_is_priekio_M1-50` – vaizdas iš priekio (kliento pusė)
3. `03_Vaizdas_is_galo_M1-50` – vaizdas iš galo (darbuotojo pusė)
4. `04_Mazgas_TIP-ON_pjuvis_A-A_M1-2` – mazgas: horizontalus pjūvis per atšokimo mechanizmą, rodyklėmis parodytas veikimas
5. `05_Mazgas_dureles_vyriai_TIP-ON_M1-10` – durelės vidinė pusė: kur gręžti vyrių taureles, kur dėti TIP-ON plokštelę; furnitūros sąrašas

Brėžiniai nubraižyti mastelyje 1:1 (mm). Matmenų stilius pritaikytas spausdinti nurodytu masteliu.

## Pagrindiniai sprendimai

**Pagrindinis modelis – `3D_modelis/Kasos_baldas.blend`** (Blender 4.5, su Gabrielės pakeitimais). Renderiai, SketchUp eksportas ir brėžinių vaizdo iš viršaus kontūrai daromi tiesiai iš jo.

| Elementas | Sprendimas |
|---|---|
| Bendri matmenys | 2159 × 767 mm (su iškyšuliais išpjovos galuose – 785 mm), aukštis 1141 mm |
| Kliento atrama | Viršutinis stalviršis (medis, 40 mm, h = 1141) su **laisvos formos išpjova** darbuotojo pusėje: per vidurį atrama 438 mm gylio, išpjovos plotis ties galiniu kraštu ~1279 mm, galuose – suapvalinti iškyšuliai (+18 mm). Kreivės koordinatės – brėžinyje 01 |
| Darbuotojo zona | Lenkta niša (juoda matinė), 201 mm aukščio. Darbo stalviršis h = **900 mm** (medis, 40 mm), 1342 mm pločio, galiniai kampai R28 |
| Po darbo stalviršiu | **Kairėje** (žiūrint darbuotojui) – stalčių blokas 400 mm, 3 stalčiai (328 / 260 / 160) su metalinėmis 200 mm rankenėlėmis ir Blum MOVENTO kreipiančiosiomis. **Per vidurį** – 542 mm vieta kojoms su galine panele. **Dešinėje** – spintelė 400 mm su lentyna ir viena atšokančia durele |
| Atšokimo mechanizmas | Blum TIP-ON, ant spintelės šono prie vietos kojoms, 70 mm nuo durelės viršaus. Vyriai Blum CLIP top 110° **be spyruoklės** |
| Kliento pusė | Rievės (40 vnt., vyno spalvos) įleistos į ~14 mm gylio, ~1210 mm pločio nišą su R10 kampais |
| Kabelių angos | Ø60, 2 vnt. darbo stalviršyje |
| Medžiagos | Medis – Wood060 tekstūra; korpusas – dekoratyvinis tinkas (pudrinė rožinė); rievės – vyno spalvos; fasadai, durelė, kojų panelė – antracito sp. matinis laminatas; niša – juoda matinė; cokolis – tamsiai rudas |
| Pagrindas | Korpusui – cokolis 40 mm. Spintelėms – kojelės h = 100 su 60 mm įtrauktu cokoliu |

Tekstūros: [ambientCG](https://ambientcg.com) (CC0) – Wood060, Plaster001.

## Kaip sugeneruoti iš naujo (Blender 4.5)
```bash
pip install ezdxf matplotlib shapely
blender -b 3D_modelis/Kasos_baldas.blend -P scripts/extract_sections.py -- scripts/sections.json
python3 scripts/gen_dxf.py Breziniai
blender -b 3D_modelis/Kasos_baldas.blend -P scripts/render_blend.py -- <renderiu_aplankas>
MODE=detail blender -b 3D_modelis/Kasos_baldas.blend -P scripts/render_blend.py -- <renderiu_aplankas>
python3 scripts/finish_renders.py <renderiu_aplankas> Renderiai
blender -b 3D_modelis/Kasos_baldas.blend -P scripts/export_sketchup.py -- 3D_modelis
```
`build_blender.py` – pradinis parametrinis modelis (ankstesnė versija).
