# Zunanje zbirke za SimpleMotocam

Velike referenčne mape so lokalne in izključene iz Git objave. Ta README in
manifesti dokumentirajo njihove izvore. Na novem računalniku lahko pripete
različice preneseš brez prepisovanja obstoječih map:

```sh
python tools/fetch_references.py opencv-2.4.13.7
python tools/fetch_references.py ComputerVision-MachineVision
python tools/fetch_references.py SI_Eksperimenti_Strojnega_Vida
```

Orodje ustvari plitve Git checkoute pri točno navedenih commitih. Pri zbirki
ComputerVision-MachineVision prenese celoten repozitorij; zahtevani primeri so
v podmapi `samples_code/`. Spodnji zapis opisuje prvotne lokalne posnetke.

Dodano 2026-10-21. Datoteke so nespremenjeni posnetki izvornih datotek Git.
Imena, kodiranja in prelomi vrstic so ohranjeni. Zbirki nimata vgnezdene mape
`.git`; vključeni sta kot običajni projektni mapi.
Različice izvora in SHA-256 vseh 50 datotek so v
`../docs/external-sources.json`.

| Zbirka | Vsebina | Izvorna različica |
| --- | --- | --- |
| [ComputerVision-MachineVision](https://github.com/mech-id-x/ComputerVision-MachineVision/tree/2054108d00b46f3ee3070ed733d67a016b1ed918/samples_code) | `ComputerVision-MachineVision/samples_code/`: vseh 21 primerov iz zahtevane mape; dodan tudi izvorni README | `2054108d00b46f3ee3070ed733d67a016b1ed918`, veja master |
| [SI_Eksperimenti_Strojnega_Vida](https://github.com/mech-id-x/SI_Eksperimenti_Strojnega_Vida/tree/33ac150c0cf2205313dd91ce3eab511e12c38fe7) | `SI_Eksperimenti_Strojnega_Vida/`: celoten repozitorij, 28 datotek, od tega 12 slik PNG | `33ac150c0cf2205313dd91ce3eab511e12c38fe7`, veja master |

## OpenCV 2.4.13.7

Dodana je tudi celotna izvorna koda uradne izdaje v `opencv-2.4.13.7/`:
4209 datotek, približno 192 MiB, commit
`51cfa519249c89d24035b3f96315ad997deb300f`. Izvorne licence so ohranjene.
Knjižnica ni prevedena ali nameščena v razvojno okolje.
Pregled modulov je v `../docs/opencv-2.4-reference.md`, vse kontrolne vsote pa
v `../docs/opencv-2.4.13.7-manifest.json`. Zapis je dodan tudi v skupni katalog
`../docs/external-sources.json`.

## Povezava z novim jedrom

| Tema | Primeri | Mesto za poznejši prenos |
| --- | --- | --- |
| Barvna razdalja in segmentacija | `color_distance`, `color_distance_2`, `krneki2`, `Whitescreen` | `simplemotocam.algebra`, novi filtri in segmentacija |
| Razlika med zajetima slikama | `Test_za_podatke_While_Loop`, `Line_position` | `simplemotocam.channels`, `simplemotocam.pipeline` |
| Zaznavanje in primerjava objektov | `Blob_*`, `Blob`, `BlobsMatch`, `BlobstoDetect` | Poznejše značilke in segmentacija |
| Sledenje | `CamSHIFT`, `krneki3` | Poznejši modul za sledenje |
| Črte in položaji | `Line_allocation`, `Line_position`, `LinesScan3`, `Pozicioniranje` | `simplemotocam.geometry` |
| Razdalje in merjenje | `distance_calculation`, `distance_measurment.py`, `SimpleMcam`, `SM_Static` | `simplemotocam.metrology` po kalibraciji |
| Zajem in uporabniški vnos | `Camera_sets`, `Input_test`, `Image_select`, `Slike_v_listo` | Zajem in prihodnji uporabniški vmesnik |
| Komunikacija in procesi | `Echo_Server`, `Process_main`, `Processing` | Poznejši ločeni adapterji |

Zbirki sta referenčno gradivo; primeri še niso preneseni v sodobni Python/OpenCV.
Vsebujeta sintakso Python 2, SimpleCV 1.3, stare odvisnosti ter deloma
nedokončane poskuse. Nekateri primeri potrebujejo predloge slik ali lokalne module,
ki niso vključeni v zahtevani obseg. Navedene povezave z jedrom so načrt prenosa,
ne trditev, da so funkcije že integrirane.

Izvorne skripte niso bile zagnane, njihove odvisnosti niso bile dodane v `.venv`.
Novi testi ostajajo omejeni na `tests_core/`, namestitev paketa pa na `src/`.
Enajst identičnih datotek se pojavlja v obeh zbirkah; namenoma so ohranjene v obeh.
Oba pregledana repozitorija v teh različicah nimata datoteke z licenco;
licenca osnovnega Simple-OpenCV se ni pripisala tem zbirkam.

## Nadaljnje spremembe

Nove prenose algoritmov dodajamo v `src/simplemotocam/` in demonstracije v
`experiments/`, s sklicem na izvorni primer. Izvorne zbirke naj ostanejo primerjalna
osnova. Posodobitev zbirke pomeni pregled novega izvora, primerjavo datotek in
posodobitev manifesta; ni samodejne sinhronizacije z GitHubom.
