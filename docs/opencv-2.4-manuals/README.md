# OpenCV 2.4 — navodila za učence

**[Odpri večjezični učni vodič](learning/index.html)** — 21 jezikov razlage,
Python/C++/C/Java, enačbe, številčni primeri in interaktivni računski preizkusi.
Vodič vsebuje osem izbranih tem; ni prevod celotnih uradnih priročnikov.
Slovenščina in angleščina sta avtorski; drugih 19 jezikov je označenih kot
strojni prevod za nadaljnji pregled. V vodiču lahko prikažeš angleški izvirnik.
Podrobnosti: [SL](learning/README.sl.md) · [EN](learning/README.en.md).

Ta mapa vsebuje uradno dokumentacijo **OpenCV 2.4.13.7** v angleščini.
PDF-je lahko odprete brez internetne povezave. Ta slovenski uvod je dodatek
projekta SimpleMotocam in ni uradni prevod priročnikov.

## Katero datoteko odprem?

| Dokument | Kdaj ga uporabim? |
| --- | --- |
| [Učbenik z vajami — OpenCV Tutorials](opencv_tutorials.pdf) | Ko se učim s primeri in želim razumeti postopek obdelave slike. Začni tukaj. |
| [Uporabniški vodič — OpenCV User Guide](opencv_user.pdf) | Ko potrebujem kratek pregled izbranih postopkov in uporabe knjižnice. |
| [Referenčni priročnik — OpenCV Reference Manual](opencv2refman.pdf) | Ko iščem določeno funkcijo, njene parametre, dovoljene podatke in rezultat. To je priročnik za iskanje, ne zaporedni učbenik. |

## Kaj je OpenCV?

OpenCV je knjižnica za obdelavo slik in računalniški vid. Slika je polje števil:
vsak piksel vsebuje vrednosti, barvna slika pa ima več kanalov. Funkcije knjižnice
omogočajo zajem, računanje s kanali, filtriranje, zaznavanje robov, sledenje in
kalibracijo kamer.

V projektu hranimo različico 2.4 kot izvorno gradivo in omogočamo izbiro
pravega pogona OpenCV 2.4.13.7 ali nameščenega sodobnega OpenCV.
Glej [namestitev in omejitve](../OPENCV_BACKENDS.md). Primeri iz dokumentacije 2.4 zato niso
nujno neposredno izvedljivi v novem okolju. Ime Python modula `cv2` samo po sebi
ne pove, katera različica OpenCV je nameščena.

## Predlagani vrstni red učenja

1. **Slika in piksel:** višina, širina, podatkovni tip in vrednost piksla.
2. **Barvni kanali:** R, G in B; OpenCV pri običajnem branju barvnih slik uporablja
   vrstni red BGR. V priročniku poišči `split`, `merge` in `mixChannels`.
3. **Računanje s slikami:** seštevanje, `subtract` in `absdiff`. Predznačena
   razlika in absolutna razlika nista ista stvar. Upoštevaj podatkovni tip:
   pri primerjanju sprememb želimo ohraniti tudi negativne vrednosti.
4. **Filtri:** poišči `GaussianBlur` in `filter2D`; preveri, kaj spremenita širina
   jedra in njegova vsebina.
5. **Robovi:** poišči `Sobel`, `Scharr` in `Canny`; primerjaj njihove rezultate.
6. **Segmentacija:** pragovi (`threshold`), erozija in dilatacija.
7. **Geometrija:** kalibracija kamere in preslikave. Meritev v pikslih še ni
   meritev v milimetrih; potrebujemo ustrezno kalibracijo ali merilo.

## Kako berem opis funkcije?

Pri vsakem primeru odgovori na pet vprašanj:

- Kakšen vhod funkcija pričakuje: barvno ali sivinsko sliko, koliko kanalov in
  kakšen podatkovni tip?
- Kaj pomeni vsak parameter in katere vrednosti so dovoljene?
- Kaj funkcija izračuna in kakšen izhod vrne?
- Kaj se zgodi, če spremenim samo en parameter?
- Kako lahko preverim rezultat z majhnim, znanim primerom?

Za iskanje uporabljaj Ctrl+F in izvirno ime funkcije. Dokumenti vsebujejo
različne programske vmesnike; vedno preveri, ali bereš primer za C++, C ali Python.

## Prvi poskus v SimpleMotocam

V korenski mapi projekta odpri `Start-SimpleMotocam.cmd`. Privzeto prikaže
ustvarjene testne slike, zato kamera ni potrebna. Opazuj R, G, B in dR:
premikajoči se pravokotnik spreminja samo rdeči kanal. Primerjaj trenutno sliko
z razliko med zaporednima slikama.

Kanal **A** v našem jedru pomeni izračunano utež zanesljivosti. To je dogovor
našega projekta, ne dodatni merilni kanal RGB kamere. Prosojnost iz datoteke
RGBA se obravnava ločeno.

## Izvor in nadaljnje branje

- Uradna spletna dokumentacija: https://docs.opencv.org/2.4.13.7/
- Izvorna koda v projektu: `external/opencv-2.4.13.7/`.
- Pregled pomembnih izvornih modulov: `docs/opencv-2.4-reference.md`.
- Naslovi prenosa, različica in kontrolne vsote so zapisani v `sources.json`.

Uradni PDF-ji so preneseni nespremenjeni. Slovenski uvod je dodan 21. 10. 2026.
