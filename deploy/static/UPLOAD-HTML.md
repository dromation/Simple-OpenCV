# SimpleOpenCV HTML — addon domena / File Manager

To je samostojna brskalniška izdaja. **Ne potrebuje Python aplikacije, Django,
Flask, Passengerja, Node.js ali API strežnika.** Vstopna datoteka je `index.html`.

1. V cPanel → Domains poglej **Document Root** svoje addon domene.
2. V File Managerju odpri TO mapo. Najprej shrani varnostno kopijo obstoječega
   spletnega mesta. Če je mapa namenjena drugim datotekam, uporabi novo podmapo.
3. Naloži **SimpleOpenCV-HTML.zip** in klikni Extract. `index.html`, `app.js`,
   `browser-worker.js`, `vendor/` in `manuals/` morajo biti v isti mapi, kot so v
   ZIP-u. Naloži **celoten paket**, ne samo index.html. Ne potrebuješ starega
   cPanel/Python paketa ali njegovega `.htaccess` z `Require all denied`.
4. Odpri `https://tvoja-domena.si/` oziroma podmapo, v katero si razširil ZIP.
   Če je ostal stari `index.php` ali stari index.html, po varnostni kopiji odstrani
   oziroma preimenuj samo stare vstopne datoteke, ki bi imele prednost.
5. Osveži s Ctrl+F5. Pogon 2.4 je priložen lokalno; dodatni OpenCV 4.13 se naloži šele ob izbiri.

## Kaj deluje

- Sestavljanje in preurejanje 28 vrst blokov; formule, parametri, RGB, A in Δ.
- Lokalni demo, slike, videi v kodekih, ki jih podpira brskalnik, ter kamera.
  Kamera potrebuje HTTPS in izrecno dovoljenje. Zvok se ne zajema.
- Iskalnik, kategorije, dodatni algoritmi, lastni shranjeni bloki in učilnica.
- Obstoječih 21 jezikov vmesnika in učna dokumentacija; obvestilo o tej izdaji
  je slovensko/angleško. Primeri Python/C/C++/Java v učilnici ostajajo razlage.
- JavaScript lastna koda v ločenem Workerju z omejitvijo izvajanja. Python,
  C/C++ in Java se lahko hranijo kot izključeni osnutki; **tu se ne prevajajo**.
- Shranjevanje projektov v IndexedDB tega brskalnika in prenos stanja kot JSON.
  Drug računalnik nima teh podatkov: prenesi JSON in ponovno izberi svoje medije.
  Brisanje podatkov spletnega mesta izbriše lokalne projekte; delaj JSON kopije.
- **Izvozi JavaScript** prenese datoteko algoritma. Uporabi jo skupaj s
  `browser-worker.js`, `browser-engine.js`, `browser-opencv24.js` in mapo `vendor/` na spletni strani;
  uvozi `processFrame(imageData)` iz modula. Izvoz ne vsebuje Python strežnika.

## Različica OpenCV in primerjava rezultatov

Privzeti pogon je **pravi OpenCV 2.4.13.7**, preveden iz preverjene izvirne C++
kode v WebAssembly. Ni preimenovani OpenCV 4. V glavi aplikacije lahko izbereš
še priloženi **OpenCV.js 4.13.0**. Izbira se ohrani v shranjenem projektu in
izvoženem JavaScript modulu. Preklop počisti zgodovino časovnih razlik.

Pogon 2.4 vključuje modula **core in imgproc**, ki izvajata 19 obstoječih
OpenCV blokov. RGB, razlike, algebra kanalov in lastna JavaScript koda se
izvajajo v skupnem brskalniškem sloju. To ni prenos vseh modulov OpenCV 2.4;
zajem kamere in videa izvaja brskalnik. Učilnica ohrani svoje primere za 2.4.

Že shranjeni projekti iz prejšnje izdaje ohranijo svojo izbiro 4.13; za delo
z 2.4 izberi **OpenCV 2.4.13.7** zgoraj. Novi projekti se začnejo z 2.4.
Pri uvozu neizvedljiva Python/C/C++/Java koda ostane izključen osnutek;
izvirna datoteka se ne spreminja. Prevajanje lastne C/C++/Java kode je še
vedno funkcija namizne/strežniške izdaje.

Matematične definicije in float32 kanali ostajajo ohranjeni; rezultati OpenCV
med različicami niso nujno bitno enaki. Preview omeji daljšo stran na 960 px.
Spletni videi se vzorčijo s korakom 1/30 s, zato prikaz ni merilo dejanskega
FPS izvirnega posnetka. Prva sličica po spremembi algoritma ima ničelne razlike.
Alfa A ostaja izpeljana ocena nasičenja, ne merjena prosojnost ali verjetnost.

## Zasebnost in lastna koda

Obdelava, slike in projekti ostanejo v brskalniku. Aplikacija ne pošilja medijev
na strežnik in ne kliče `/api`. Povezave do izvirnih repozitorijev in uradne
dokumentacije odpreš samo po lastni izbiri. Uporabljaj le zaupanja vredno lastno
JavaScript kodo: Worker in časovna omejitev preprečujeta zamrznitev vmesnika,
nista varnostni peskovnik za zlonamerno kodo.

## Če se stran ne naloži

- Uporabi spletni naslov HTTP(S), ne dvoklika na lokalni `file://index.html`.
- Preveri, da je razširjen celoten ZIP in poti ohranijo velike/male črke.
- `vendor/opencv24/opencv24.js` in `vendor/opencv.js` morata biti prisotna. Vse knjižnice so v ZIP-u; CDN ni potreben.
- Če gostovanje dodaja strogo Content-Security-Policy, mora dovoliti lokalne
  Workerje in WebAssembly; izvajanje lastne kode zahteva JavaScript eval v Workerju.
- Če ostaja stara stran, odstrani predpomnilnik in preveri Document Root ter
  morebitni prednostni index.php. Ne prepisuj drugih spletnih mest.
- Gumb Reset current workspace obnovi samo trenutno delovno stanje; shranjene
  projekte in medije ohrani.

OpenCV 2.4: https://github.com/opencv/opencv/tree/2.4.13.7 (BSD, licenca v vendor/opencv24/).
OpenCV.js 4.13: https://docs.opencv.org/4.13.0/ (Apache 2.0, priložena licenca v vendor/).
SimpleOpenCV: MIT, glej LICENSE. Arhivski priročniki imajo svoje izvirne licence.

## O aplikaciji in licence

Gumb **O aplikaciji** spodaj odpre zgodbo projekta in licence v isti aplikaciji.
Priloženi so `LICENSE`, `THIRD_PARTY_NOTICES.md`, mapa `licenses/` z izvirnimi
besedili in njihovimi kontrolnimi vsotami ter pregled `about.html`.
Pri nadgradnji uporabi isto domeno in isto pot, da ohraniš projekte v brskalniku.
Ime aplikacije je zdaj SimpleOpenCV; notranji ključi shrambe ostajajo združljivi.
