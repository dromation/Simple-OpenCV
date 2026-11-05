# SimpleMotocam HTML — addon domena / File Manager

To je samostojna brskalniška izdaja. **Ne potrebuje Python aplikacije, Django,
Flask, Passengerja, Node.js ali API strežnika.** Vstopna datoteka je `index.html`.

1. V cPanel → Domains poglej **Document Root** svoje addon domene.
2. V File Managerju odpri TO mapo. Najprej shrani varnostno kopijo obstoječega
   spletnega mesta. Če je mapa namenjena drugim datotekam, uporabi novo podmapo.
3. Naloži **SimpleMotocam-HTML.zip** in klikni Extract. `index.html`, `app.js`,
   `browser-worker.js`, `vendor/` in `manuals/` morajo biti v isti mapi, kot so v
   ZIP-u. Naloži **celoten paket**, ne samo index.html. Ne potrebuješ starega
   cPanel/Python paketa ali njegovega `.htaccess` z `Require all denied`.
4. Odpri `https://tvoja-domena.si/` oziroma podmapo, v katero si razširil ZIP.
   Če je ostal stari `index.php` ali stari index.html, po varnostni kopiji odstrani
   oziroma preimenuj samo stare vstopne datoteke, ki bi imele prednost.
5. Osveži s Ctrl+F5. Prvi zagon naloži približno 11 MB lokalnega OpenCV.js.

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
  `browser-worker.js`, `browser-engine.js` in mapo `vendor/` na spletni strani;
  uvozi `processFrame(imageData)` iz modula. Izvoz ne vsebuje Python strežnika.

## Različica OpenCV in primerjava rezultatov

Ta izdaja uporablja lokalno priloženi **OpenCV.js 4.13.0 / WebAssembly**.
**Ni isti pogon kot izvirni OpenCV 2.4.13.7.** Stara namizna in Python izdaja
ostajata na voljo ločeno. Uvoz projekta iz drugega pogona zahteva potrditev;
izvirna datoteka ostane nespremenjena, pripravi se brskalniška kopija. Lastna
koda v neizvedljivem jeziku se pri uvozu izključi in ostane osnutek.

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
- `vendor/opencv.js` mora biti prisoten. Vse knjižnice so v ZIP-u; CDN ni potreben.
- Če gostovanje dodaja strogo Content-Security-Policy, mora dovoliti lokalne
  Workerje in WebAssembly; izvajanje lastne kode zahteva JavaScript eval v Workerju.
- Če ostaja stara stran, odstrani predpomnilnik in preveri Document Root ter
  morebitni prednostni index.php. Ne prepisuj drugih spletnih mest.
- Gumb Reset current workspace obnovi samo trenutno delovno stanje; shranjene
  projekte in medije ohrani.

OpenCV.js: https://docs.opencv.org/4.13.0/ (Apache 2.0, priložena licenca v vendor/).
SimpleMotocam: MIT, glej LICENSE. Arhivski priročniki imajo svoje izvirne licence.
