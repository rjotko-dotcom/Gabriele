# MARI MADE – parduotuvė prekybos centre GO9 (Gedimino pr. 9, Vilnius)

Interjero projekto paketas. Atliko Gabrielė Meilūnaitė, Vilniaus dizaino kolegija, 2026-11.

## Turinys

| Aplankas | Kas viduje |
|---|---|
| `01_Breziniai_su_stampu/` | 9 lapų PDF ir DXF failai su layoutais ir štampu |
| `02_Breziniai_be_stampo/` | Tas pats komplektas be štampo (tik rėmelis ir lapo numeris) |
| `03_Vizualizacijos/` | Reference renderiai iš Blender (tiksli geometrija, medžiagos, šviesa): 4 interjero ir 2 fasado/vitrinos vaizdai. Juos įkelkite į ChatGPT ir naudokite su promptais iš `ChatGPT_promptai.md` |
| `04_Vitrina/` | Vitrinos koncepcija (PDF) ir vitrinų išklotinės |
| `ChatGPT_promptai.md` | Promptai vizualizacijoms tobulinti ChatGPT ar kitais AI įrankiais |
| `_saltiniai_scriptai/` | Skriptai, kuriais viskas sugeneruota (kad būtų galima pakartoti ar pataisyti) |

## Lapų sąrašas

| Nr. | Lapas | Formatas | Mastelis | DXF failas |
|---|---|---|---|---|
| 1 | Griovimo planas | A1 | 1:50 | `GRIOVIMO_PLANAS.dxf` |
| 2 | Naujas išplanavimas | A1 | 1:50 | `NAUJAS_ISPLANAVIMAS.dxf` |
| 3 | Lubų planas | A3 | 1:50 | `LUBU_PLANAS.dxf` |
| 4 | Šviestuvų planas | A3 | 1:50 | `SVIESTUVU_PLANAS.dxf` |
| 5 | Baldų išdėstymo planas | A3 | 1:50 | `BALDU_PLANAS_IR_PJUVIAI.dxf` |
| 6 | Pjūvis 1-1 | A3 | 1:50 | `BALDU_PLANAS_IR_PJUVIAI.dxf` |
| 7 | Pjūvis 2-2 | A3 | 1:50 | `BALDU_PLANAS_IR_PJUVIAI.dxf` |
| 8 | Pjūviai 3-3 ir 4-4 | A3 | 1:50 | `BALDU_PLANAS_IR_PJUVIAI.dxf` |
| 9 | Vitrinų išklotinės | A3 | 1:50 | `VITRINOS_ISKLOTINES.dxf` |

**Kaip atidaryti AutoCAD'e:** atidarykite `.dxf` failą, tada *Save As → DWG (2018)*. Kiekvienas lapas yra atskiras layoutas, paruoštas spausdinti į PDF mastelyje 1:1. Brėžinys viewporte yra 1:50.

## Linijų storiai (LST EN ISO 128, linijų grupė 0,5)

| Elementas | Storis, mm |
|---|---|
| ISO 5457 rėmelis | 0,70 |
| Pjaunamos sienos, kolonos, naujos pertvaros; lentelių ir štampo išorinis rėmas | 0,50 |
| Pjaunami baldai, metalinės konstrukcijos, evakuacija | 0,35 |
| Matomi kontūrai, langai, durys, tekstas, šviestuvai | 0,25 |
| Tolimi kontūrai, matmenys, altitudės, ašys (brūkšninis taškinis), lentelių vidinės linijos | 0,18 |
| Stiklas, užtušavimai | 0,13 |

Storiai valdomi per sluoksnius (*ByLayer*), o objektų individualūs storiai išvalyti.

## Ką pakeičiau jūsų brėžiniuose

- Visų sluoksnių linijų storiai suvienodinti pagal lentelę viršuje.
- Eksplikacijos ir sutartiniai žymėjimai perdaryti į tikras lenteles su rėmeliais. Jos perkeltos į lapą, tekstas 2,5 mm.
- Šviestuvų eksplikacijoje pridėtas stulpelis „Kiekis".
- Šviestuvų plane pašalintos pradėtos braižyti lentynos (L formos kontūras palei galinę ir dešiniąją sienas).
- Lubų plane pašalintos dvi nuorodos su lyderiais, kurios siekė 22,5 m į dešinę ir netilpo į lapą. Jų tekstas perkeltas į naują sutartinių žymėjimų lentelę.
- Pataisyta rašyba: ŠVIESTUVŲ, LUBŲ, ĮĖJIMAS, ĮLEIDŽIAMI, LAUKO DURYS, GIPSINĖ, GIPSO KARTONO, Į PATALPĄ, TURĖKLAS.

## Reikia jūsų dėmesio

1. **Prekės ženklo pavadinimas.** SketchUp modelyje ant sienos parašyta „MARY MADE", o prekės ženklas yra „MARI MADE" (mari.lt). Brėžiniuose ir vizualizacijose naudota „MARI MADE".
2. **Pakylos aukštis.** DWG plane įėjimo zonos altitudė yra -1,70, t. y. 300 mm virš grindų. SketchUp modelyje pakyla yra 450 mm aukščio (-1,550). Pjūviai sudaryti pagal modelį, todėl patikrinkite, kuris variantas teisingas.
3. **Griovimo plano lentelė.** Eilutė „ESAMOS SIENOS IR LAIKANČIOS KONSTRUKCIJOS" kartojasi du kartus su skirtingais simboliais. Galbūt antroji turėjo būti „GRIAUNAMOS SIENOS".
4. **Pasimetęs objektas.** Griovimo plano failo modelio erdvėje, apie 25 m nuo brėžinio, yra pasimetęs kolonos objektas. Jo neištryniau.
5. **Lapų formatas.** Griovimo ir naujo išplanavimo planai su ašimis ir lentelėmis 1:50 mastelyje užima ~500 × 370 mm, todėl jiems naudotas A1 formatas.
