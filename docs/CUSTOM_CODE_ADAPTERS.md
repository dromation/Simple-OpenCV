# Prazen blok in poljubni programski jeziki

V knjižnici klikni **Prazen blok · lastna koda**. V urejevalniku izberi jezik
ali vpiši njegovo oznako, na primer `rust`, `java`, `cpp`, `csharp`, `julia` ali
`lua`, in klikni **Izberi jezik**. Vsak jezik ima svoj osnutek; preklop jezika
ohrani prejšnjo kodo. Jezik ne spremeni izbranega pogona OpenCV.

**Ohrani kodo kot osnutek** sprejme tudi nedokončano kodo brez izvajanja in
izključi blok. Blok takrat nespremenjeno prepušča izbrani vhod. Nato uporabi
**Shrani stanje**, da shraniš projekt z vsemi jezikovnimi osnutki na disk.
Osnutek lahko shraniš tudi v zbirko dodatnih algoritmov z gumbom za shranjevanje
bloka. Uvoz in odpiranje projekta kode ne izvedeta.

**Uporabi in izvedi kodo** je omogočen samo ob združljivem nameščenem adapterju;
vključi blok in preveri dejanski rezultat. Python in JavaScript imata vgrajena
izvajalnika (JavaScript zahteva Node.js). Python pri OpenCV 2.4 uporablja NumPy
in omejeni most `cv24.run`. Vpis drugega jezika sam po sebi ne namesti njegovega
prevajalnika in ne prevede kode iz prejšnjega jezika.

## Dodajanje izvajalnika brez spreminjanja aplikacije

Lokalna konfiguracija je določena z okoljsko spremenljivko
`SIMPLEMOTOCAM_RUNTIME_CONFIG`, ki vsebuje absolutno pot do datoteke JSON.
Adapter ima poljubno oznako jezika, prikazno ime, pripono in ukaz kot seznam
argumentov. Ukaz se izvede brez lupine. Uporabi absolutne poti do izvajalnika
in skripte. Konfiguracija je lokalna; ukazov ni mogoče dodati z uvozom projekta.

Ta delujoči primer registrira referenčni adapter `python-file`:

```json
{
  "api": 1,
  "adapters": {
    "python-file": {
      "name": "Python file · reference adapter",
      "extension": ".py",
      "command": [
        "D:/Dromation/org/apps/betas/SimpleMotocam/.venv/Scripts/python.exe",
        "D:/Dromation/org/apps/betas/SimpleMotocam/contrib/runtime-adapters/python_file_adapter.py"
      ],
      "backends": ["opencv24", "current"]
    }
  }
}
```

V PowerShellu nastavi pot in zaženi aplikacijo iz istega okolja:

```powershell
$env:SIMPLEMOTOCAM_RUNTIME_CONFIG = 'D:\pot\runtime-adapters.json'
.venv\Scripts\python.exe -m simplemotocam.studio
```

Ob spremembi konfiguracije osveži brskalnik. Izvajalnik preveri konfiguracijo
ponovno tudi pri obdelavi. `backends` določa združljive profile; ta deklaracija
ni dokaz uporabljene različice OpenCV. Adapter mora sam poskrbeti za pravilne
knjižnice. Vgrajenih imen `python` in `javascript` ni mogoče prepisati.

## Pogodba adapterja v1

Aplikacija ukazu doda dva argumenta: absolutno pot do začasne delovne mape in
absolutno pot do UTF-8 datoteke `source.<pripona>` z uporabniško kodo.
Delovna mapa vsebuje:

- `request.json`: `api: 1`, `language`, `dtype: "<f4"`, `shape: [H,W]`,
  urejen seznam imen `channels`, `params` (`input`, `output`, `gain`, `timeout`,
  `code`), izvorno `code` in `backend` (`opencv24` ali `current`).
- `in0.bin`, `in1.bin`, … v enakem vrstnem redu kot `channels`: H × W števil
  IEEE754 float32, little endian, po vrsticah. Vključeni so RGB, izpeljani A in
  predhodno izračunani kanali.
- Adapter zapiše `out.bin`: natanko H × W končnih float32 vrednosti iste oblike.
  Vrednosti niso omejene na [0,1], zato so možne predznačene razlike in odvodi.
- Ob napaki zapiše UTF-8 `error.txt` in vrne neničelno izhodno kodo.

Adapter za C, C++, Java, Rust ali drug jezik lahko najprej prevede `source`,
nato požene program in pretvori njegov izhod v to pogodbo. Prevajanje in
izvajanje sta vključena v časovno omejitev bloka (do 30 sekund).
Takšni izvajalniki niso vključeni zgolj z izbiro njihovega imena v meniju.
Referenčni adapter in testi prikazujejo tudi napake ob napačni velikosti,
nekončnih številih, neuspelem procesu in časovni prekoračitvi.

Koda se izvaja s pravicami lokalnega uporabnika. Ločen proces ni varnostni
peskovnik. Adapterji naj poskrbijo za zaključevanje svojih podprocesov.
Samostojni izvoz algoritma ohrani izbrani jezik in osnutke; pri izvajanju
potrebuje enako lokalno konfiguracijo ter nameščen izvajalnik. Ukazi in
računalniške poti iz lokalne konfiguracije se ne kopirajo v projekt ali izvoz.
