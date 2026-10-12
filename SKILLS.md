# Claude skills / įrankiai 3D modeliavimui ir spausdinimui

## Jau šiame projekte (veikia automatiškai, kai Claude dirba su šia repozitorija)
| Skill | Kam |
|---|---|
| `.claude/skills/blender-3d-print` | Mūsų taisyklės: parametriniai Blender skriptai, tolerancijos, jungtys, M3, modernus dizainas, patikra |
| `.claude/skills/cli-anything-blender` | Blender valdymas per komandinę eilutę be GUI (HKUDS/CLI-Anything, Apache-2.0). Reikia `pip install cli-anything-blender` |
| `.claude/skills/blender-motion-state-inspection` | `.blend` failų analizė: rigai, kaulai, pozos (iš affaan-m/ECC, MIT). Naudinga tik animacijai |
| `.mcp.json` → **MCP for Blender** | Claude valdo tavo atidarytą Blender'į (ahujasid/blender-mcp). Telemetrija išjungta |

## Įsidiek savo kompiuteryje (vieną kartą)
1. **MCP for Blender** (Blender addon + serveris):
   ```bash
   uvx mcp-for-blender setup          # arba: uvx mcp-for-blender install-addon
   ```
   Blender'yje: Edit → Preferences → Add-ons → įjunk **MCP for Blender**. Projekto `.mcp.json`
   jau turi serverio aprašą – atidarius projektą Claude Code paklaus, ar jį įjungti.
2. **superpowers** (planavimas, testai, debugging – obra/superpowers). Claude Code'e:
   ```
   /plugin marketplace add obra/superpowers-marketplace
   /plugin install superpowers@superpowers-marketplace
   ```
3. **kevinbadi/blender-skills** (blender-toolkit, product-polish, turntable video, PolyHaven studija):
   ```bash
   ./tools/install-blender-skills.sh
   ```
4. **Claude pluginai** iš katalogo: **SpeakCAD Slicer** (slicer'io nustatymai tavo spausdintuvui),
   **3D CAD Converter** (STEP/STL/3MF konvertavimas, Windows).
5. **Blender priedai:** *3D Print Toolbox* (Extensions – sienelių storio ir manifold patikra),
   *Bool Tool*, *CAD Sketcher*. Slicer: **OrcaSlicer** arba **Bambu Studio**.

## Ko nediegiau ir kodėl
- **Tripo / Meshy / Alpha3D (AI 3D generavimas)** – reikia mokamų API raktų. Modeliai netikslūs
  (tinka dekorui, ne funkcinėms detalėms su varžtais). `kevinbadi` `image-to-3d` skillai juos naudoja,
  jei prireiks – įsidiek atskirai su savo Meshy raktu.
