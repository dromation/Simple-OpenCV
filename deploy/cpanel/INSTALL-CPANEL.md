# SimpleMotocam na lastni domeni prek cPanela

Ta paket vsebuje delujočo Python/WSGI različico studia za **Setup Python App**
(CloudLinux) oziroma **Application Manager** (Passenger). Flask in Django nista
potrebna. **Samo PHP in File Manager ne zadoščata za izvajanje OpenCV.**

## 1. Preveri gostovanje

- Python 3.10–3.12, možnost namestitve paketov pip, Passenger/WSGI in HTTPS.
- Linux x86_64 za priloženi Linux pogon, če je prisoten. Na drugih arhitekturah
  pogon zgradi na strežniku. Preverjanje združljivosti je opisano spodaj.
- Za gradnjo OpenCV 2.4: g++, make in CMake 3.20–3.31; približno 1–2 GB prostega
  prostora in dovolj procesorskega časa. Gostitelj lahko gradnjo opravi zate.
- Gostovanje mora dovoliti zagon podprocesov. CPU/RAM omejitve deljenega
  gostovanja določajo hitrost; to ni storitev za veliko sočasnih video tokov.

## 2. Naloži ZIP s File Managerjem

1. V domači mapi računa ustvari novo mapo **simplemotocam**. Primer:
   `/home/UPORABNIK/simplemotocam`. Naj bo **zunaj `public_html`**.
2. Vanjo naloži in razširi `SimpleMotocam-cPanel.zip`. Datoteki
   `passenger_wsgi.py` in `hosting.example.json` morata biti neposredno v tej mapi.
3. Datoteko `hosting.example.json` kopiraj v `hosting.json` in jo uredi:
   - `allowed_hosts`: tvoja domena, npr. `["vision.mojadomena.si"]`.
     Če uporabljaš tudi `www`, dodaj oba dejanska naslova.
   - `access_key`: tvoje novo naključno geslo z vsaj 24 znaki. Privzeto besedilo
     `CHANGE_...` ne omogoči zagona. `username` je privzeto `studio`.
   - `base_path`: `""` za koren domene ali `"/vision"` za podmapo. Ta vrednost
     mora ustrezati Application URL spodaj.
4. `hosting.json` vsebuje prijavne podatke: ne nalagaj ga v javno mapo,
   repozitorij ali javno priponko. Z dovoljenji File Managerja omeji dostop
   na račun gostovanja (običajno 600). Mapa `private/` je prav tako zasebna.

Priloženi korenski `.htaccess` zavrne neposreden spletni dostop do zasebne
mape, če bi jo pomotoma nastavil kot javno. Aplikacijo poveži prek Passengerja;
ne odstranjuj te zaščite, da bi objavil izvorne datoteke.

## 3. Setup Python App

V **Setup Python App → Create Application** nastavi:

| Nastavitev | Vrednost |
| --- | --- |
| Python version | 3.10, 3.11 ali 3.12 |
| Application root | `simplemotocam` |
| Application URL | izbrana domena; za podmapo še `/vision` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |
| Passenger log | zasebna pot, npr. `/home/UPORABNIK/simplemotocam/passenger.log` |

Shrani aplikacijo. Če cPanel ustvari svojo začetno datoteko passenger_wsgi.py,
jo zamenjaj z istoimensko datoteko iz našega ZIP-a. V nastavitvi odvisnosti izberi
**requirements.txt → Run Pip Install**, če gostitelj ponuja ta gumb.
Druga možnost je cPanel Terminal/SSH: najprej aktiviraj okolje z ukazom,
ki ga izpiše Setup Python App, nato v mapi aplikacije izvedi:

```sh
python -m pip install -r requirements.txt
```

Uporablja se `opencv-python-headless`, ker strežnik nima namiznega prikaza.
**Ne nameščaj hkrati navadnega opencv-python.** Ne nameščaj korenskega
arhivskega requirements.txt iz stare namizne aplikacije ali `pip install -e .`.

V **Application Manager** registriraj isto mapo, domeno, osnovni URL in
produkcijsko okolje. Izbiro interpreterja ter Python odvisnosti po potrebi
uredi gostitelj; to ni enak uporabniški vmesnik kot CloudLinux Python Selector.
Javni document root naj vsebuje samo javne datoteke, nikoli `hosting.json`.

## 4. Pravi OpenCV 2.4 na Linuxu

Glavni profil ostane **OpenCV 2.4.13.7**. Hostov Python paket `cv2` služi
dekodiranju, prikazu in izbirnemu trenutnemu pogonu; stari algoritmi uporabljajo
ločen, pravi Linux program iz modulov core/imgproc. Windows `.exe` ni uporaben.

Če ZIP vsebuje `.motocam/backends/opencv24/simplemotocam_opencv24`, mu v File
Managerju nastavi dovoljenje **755**. Nato v aktivnem okolju zaženi:

```sh
python check_hosting.py
```

Če Setup Python App ponuja **Execute Python Script**, lahko `check_hosting.py`
zaženeš tudi tam, brez Terminala. Ta pregled ne spreminja nastavitev in ne izpiše gesla.

Priložena binarna datoteka ni univerzalna za vse Linux distribucije. Poročilo
`LINUX-BUILD.txt`, kadar je vključeno, navede preverjeno okolje. Če dobiš
napako GLIBC/GLIBCXX, napačne arhitekture ali manjkajoče datoteke, zgradi pogon
na ciljnem strežniku oziroma združljivem Linux sistemu:

```sh
python tools/fetch_references.py opencv-2.4.13.7
python -m pip install 'cmake>=3.20,<4'
python tools/build_opencv24_linux.py --jobs 2
python check_hosting.py
```

Git in dostop do GitHuba sta potrebna za prenos točno določene izvorne revizije.
Če gostitelj ne dovoljuje Git/gradnje, naj izvor in združljivo binarno datoteko
pripravi skrbnik. Gradnja ne potrebuje `sudo`. Izvorni manifest se preveri s
SHA-256; neuspešna gradnja ne spremeni profila ali samodejno izbere OpenCV 4.

Če **izrecno želiš trenutni OpenCV**, v `hosting.json` nastavi
`"backend": "current"`. To omogoči uporabo brez gradnje starega pogona in jasno
prikaže nameščeno različico. To ni OpenCV 2.4. Obstoječe shranjene seje ohranijo
svoj profil; v aplikaciji ga nato spremeni z izbirnikom.

## 5. Domena, HTTPS in prijava

V cPanel Domains poveži domeno/poddomeno z računom ter uredi DNS pri svojem
ponudniku. V SSL/TLS Status omogoči veljavno potrdilo (AutoSSL, če je na voljo).
V Setup Python App klikni **Restart**, nato odpri `https://vision.mojadomena.si/`
oziroma `https://mojadomena.si/vision/`. Brskalnik zahteva uporabniško ime
`studio` in geslo `access_key`. Dostop HTTP je privzeto zavrnjen; v cPanelu
vključi preusmeritev HTTP → HTTPS. Samovoljnih X-Forwarded-* glav aplikacija
ne zaupa; če je pred Apache posrednik, mora gostitelj pravilno nastaviti HTTPS.

## Kaj omogoča gostovana različica

- Isti sestavljalnik blokov, formule, parametri, 21 jezikov in učilnica.
- Demo posnetki, naložene slike in videi; privzeta omejitev datoteke 20 MB.
- Stanje in časovna zgodovina po brskalnikih, shranjevanje ter Python izvoz.
  SQLite zagotovi usklajenost tudi med več Passenger procesi.
- Sejni piškotek velja 30 dni. Shranjeni projekti so pod `private/sessions/`;
  za drug brskalnik prenesi JSON in ga ponovno odpri. Piškotek ne pomeni
  ločenega uporabniškega računa; to je zasebni studio z enim skupnim geslom.
- USB kamera na tvojem računalniku ni kamera strežnika: ta izdaja uporablja
  naložene posnetke. Zajem brskalniške kamere/WebRTC še ni implementiran.
- Videi se med zahtevami ponovno odprejo in poiščejo naslednjo sličico; hitrost
  je odvisna od kodeka in gostovanja. Za natančne primerjave uporabi slike ali
  lokalno izdajo. To ni zagotovilo predvajanja videa v realnem času.
- Lastno kodo lahko shraniš kot izključen osnutek in izvoziš. Njeno izvajanje
  ter prevajalniki so privzeto izključeni. Če gostitelj to dovoljuje in studio
  uporabljajo samo zaupanja vredne osebe, v zasebni nastavitvi vključi
  `allow_code_execution` in po potrebi `allow_compilers`, namesti ustrezne
  prevajalnike/JDK in ponovno zaženi aplikacijo. Koda ima pravice računa
  gostovanja; gesla ne deli z nezaupanja vrednimi uporabniki.

## Posodobitev in odpravljanje težav

Pred posodobitvijo prenesi varnostno kopijo `hosting.json`, `private/` in lastnega
Linux pogona. Posodobi samo programske datoteke in klikni Restart. Namestitveni
ZIP ne vsebuje `hosting.json` ali tvojih projektov in jih ne prepisuje.
Stare sej­ne mape lahko po varnostni kopiji odstraniš v File Managerju, ko jih
ne potrebuješ; s tem izbrišeš njihove projekte in medije. Samodejnega brisanja ni.

- **503 / setup incomplete:** preglej zasebni Passenger log, Python okolje,
  odvisnosti in hosting.json; po popravku Restart.
- **OpenCV worker missing:** opravi korak 4. Preveri pot in dovoljenja 755.
- **403:** preveri allowed_hosts, HTTPS, base_path in ujemanje domene.
- **401 / prijava:** uporabi username/access_key iz svoje zasebne datoteke.
- **404 za JS/API/učilnico:** Application URL in base_path se morata ujemati;
  podmapo odpri s končnim `/`.
- **Limit/timeout:** zmanjša­j posnetek, število blokov ali hitrost izvajanja.
  Omejitve RAM/CPU/upload pri gostitelju lahko veljajo dodatno.

Uradna navodila:
[cPanel Python WSGI](https://docs.cpanel.net/knowledge-base/web-services/how-to-install-a-python-wsgi-application/),
[Application Manager](https://docs.cpanel.net/cpanel/software/application-manager/),
[Python Selector](https://support.cpanel.net/hc/en-us/articles/360057849753-How-to-register-an-application-with-Python-Selector).
