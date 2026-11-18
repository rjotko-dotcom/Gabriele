# MARI MADE – parduotuvė prekybos centre GO9 (Gedimino pr. 9, Vilnius)

Interjero projekto brėžiniai. Atliko Gabrielė Meilūnaitė, Vilniaus dizaino kolegija, 2026-11.

## Failai

| Aplankas / failas | Kas tai |
|---|---|
| `01_Breziniai_su_stampu/…_spausdinimui_A3.pdf` | **Spausdinti A3 lapuose.** 15 A3 puslapių: lapai 1 ir 2 (A1) supjaustyti į 4 A3 dalis |
| `01_Breziniai_su_stampu/…_A1_A3.pdf` | 9 lapai originaliais formatais (1–2 lapai A1, kiti A3), spaudai spaustuvėje |
| `01_Breziniai_su_stampu/*.dxf` | DXF failai su paruoštais layoutais. AutoCAD'e: atidaryti → *Save As* → DWG |
| `02_Breziniai_be_stampo/` | Tas pats be štampo |
| `ChatGPT_promptai.md` | Promptai vizualizacijoms iš SketchUp ekrano nuotraukų |
| `_saltiniai_scriptai/` | Skriptai, kuriais sugeneruoti brėžiniai |

## Lapai (visi 1:50)

| Nr. | Lapas | Formatas |
|---|---|---|
| 1 | Griovimo planas | A1 (= 4 × A3) |
| 2 | Naujas išplanavimas | A1 (= 4 × A3) |
| 3 | Lubų planas | A3 |
| 4 | Šviestuvų planas | A3 |
| 5 | Baldų išdėstymo planas | A3 |
| 6 | Pjūvis 1-1 | A3 |
| 7 | Pjūvis 2-2 | A3 |
| 8 | Pjūviai 3-3 ir 4-4 | A3 |
| 9 | Fasado vitrinų išklotinė (1:50) ir logotipo plėvelė (1:10) | A3 |

**A1 lapų spausdinimas A3 popieriuje.** PDF'e A1 lapas supjaustytas į 4 A3 dalis tokia tvarka: viršus kairė, viršus dešinė, apačia kairė, apačia dešinė. Spausdinkite **100 % (Actual size)** be „Fit to page" ir sudėkite 2×2. Jei spausdintuvas nespausdina iki krašto, prie sujungimų gali dingti po kelis milimetrus. Tokiu atveju geriausia lapus 1 ir 2 atsispausdinti A1 formatu spaustuvėje iš failo `…_A1_A3.pdf`.

## Langai ir durys pagal tikrą fasadą (VITRINOS_ISKLOTINE2)

- **Langai:** 1370 × 3165 mm. Palangė -0,945, viršus +2,219. Virš ir po langu mūras, skersinio nėra.
- **Įėjimo durys:** arkinė anga 1550 mm. Varčios 934 + 416 mm su 200 mm statramsčiu, durų viršus +0,665, virš jų skersinis ir arkinis viršlangis iki +1,965.
- **Kur atnaujinta:** baldų plane (angos ir durų simboliai) ir pjūviuose 2-2, 3-3, 4-4.
- **Lapas 9:** padarytas iš Gabrielės fasado brėžinio. Pridėti standartiniai linijų storiai, MARI MADE logotipas ant langų, matmenys ir altitudės.
- **Gabrielės rankiniai pataisymai** (kairiosios durys, šviestuvai pjūviuose, užrašų vietos ir kt.) perkelti į naują versiją automatiškai.

## Standartai

- **Linijų storiai** pagal LST EN ISO 128 (linijų grupė 0,5):

  | Elementas | Storis, mm |
  |---|---|
  | Rėmelis | 0,70 |
  | Pjaunamos sienos | 0,50 |
  | Pjaunami baldai; griaunami ir demontuojami elementai (brūkšninė, sluoksnis `A-GRIAUNAMA`) | 0,35 |
  | Matomi kontūrai, langai, durys | 0,25 |
  | Toli matomi kontūrai, laiptų pakopos, matmenys, ašys | 0,18 |
  | Stiklas, užtušavimai, durų atidarymo lankai, fasado rustika | 0,13 |

  Visos linijos juodos, sienų pjūviai užpildyti pilkai.
- **Ašys.** Vertikalios ašys žymimos skaičiais iš kairės į dešinę (1, 2, 3, 4), horizontalios raidėmis iš apačios į viršų (A, B, C). Senos ašys pervadintos: 1E→1, 1→2, 2→3, 3→4, AE→A, A→B, B→C. Burbulai Ø10 mm, linijos brūkšninės taškinės. Ašys su matmenimis pridėtos ir lubų, šviestuvų, baldų planuose bei pjūviuose.
- **Langai ir durys** pavaizduoti pagal ISO 7519:
  - plane langas yra anga su rėmu ir stiklu, durys turi 90° atidarymo lanką;
  - pjūviuose langai su rėmais, skersiniu ir stiklo žymėjimu.
- **Altitudės.** Pastato ±0,000 atžvilgiu: grindys -2,000, pakyla prie įėjimo -1,700. Pjūviuose aukščių žymos dedamos kraštuose.
- **Tekstas** ne mažesnis nei 2,5 mm. Plane virš pjūvio esantys elementai (nuleistos lubos, šviestuvai, medžio laja) rodomi punktyru.

## Projekto pataisymai (pagal pastabas)

1. **Pakyla** prie įėjimo dabar 300 mm (-1,700), su laipteliais 2 × 150 mm.
2. **Stelažų gylis** 400 mm.
3. **Alyvmedis** perkeltas į kampą tarp fotelių ir sumažintas iki 2,8 m. Visa laja yra patalpos viduje.
4. **Nuleistos lubos** yra Ø1650 mm, 150 mm storio diskai, pritvirtinti prie lubų (+3,850) ir centruoti tiksliai virš prekių stalų. Po jais ant trosų kabo linijiniai šviestuvai (apačia +0,500, t. y. 2,5 m nuo grindų). Diskų padėtys pataisytos ir lubų bei šviestuvų planuose.
5. **Pjūvių plokštumos** perkeltos taip, kad kirstų prekių stalus. Virš stalų matosi šviestuvai.
6. **Lentynos** pašalintos šviestuvų ir lubų planuose, nes jos nesiekia lubų.
7. **Vitrina:** paliktas tik MARI MADE logotipas ant stiklo (aukso spalvos metalizuota plėvelė). Logotipo dydis ir aukštis nurodyti lape 9.
8. **Pastabos** pašalintos iš visų lapų, **spalvos** pašalintos iš visų linijų.
9. **Rašyba** pataisyta lentelėse (ĮĖJIMAS, ĮLEIDŽIAMI, DURYS, GIPSINĖ ir kt.).

## Liko patikrinti

- Griovimo plano lentelėje buvo dvi vienodos eilutės „ESAMOS SIENOS IR LAIKANČIOS KONSTRUKCIJOS". Palikta viena, su 0,50 mm simboliu, kaip brėžiamos esamos sienos.
- SketchUp modelyje ant sienos parašyta „MARY MADE". Brėžiniuose naudotas teisingas prekės ženklas „MARI MADE".
