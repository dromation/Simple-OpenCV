# Večjezični učni vodič SimpleMotocam

Odpri **index.html** v običajnem spletnem brskalniku. Vodič ne potrebuje strežnika,
internetne povezave ali dodatne namestitve. Izberi enega od 21 jezikov razlage
in neodvisno programski jezik (Python, C++, C ali Java).

Vključenih je osem tem: RGB, predznačene razlike, algebra kanalov, izračunana
zanesljivost, jedra filtrov, prostorski odvodi, pragovi in merilo. Vsaka tema ima
enačbo, razlago spremenljivk, številčni primer, predpostavke in programski izsek.
Drsniki preračunajo učne vrednosti v brskalniku; ne spreminjajo aplikacije ali kode.

Slovensko in angleško besedilo sta avtorska. Preostalih 19 jezikov tvorijo
označeni strojni prevodi, ki še potrebujejo strokovni in jezikovni pregled.
Pri samodejnem prevodu je angleški izvirnik privzeto razprt. Arabščina uporablja pisanje
od desne proti levi, enačbe in koda pa ohranijo običajno smer.
Uradni PDF-priročniki ostanejo v angleščini. Programski primeri in enačbe so
skupni vsem jezikom. Orodje za nove prevode je v `tools/doc_translate/`
v korenu projekta; za posodobitev uporabi `Update-Learning-Translations.cmd`.

## Programska okolja

- **Python:** prikazani primeri so samostojne skripte Python 3, numerično preverjene
  v projektu z NumPy 2.2.6 in OpenCV 4.14.0. Iz gumba »Shrani primer« dobiš `.py`.
  Zaženi jo s projektovim `.venv\Scripts\python.exe`. Niso bile preizkušene z
  OpenCV 2.4 ali Python 2.
- **C++:** izseki uporabljajo API OpenCV 2.4. Običajno potrebujejo
  `#include <opencv2/opencv.hpp>` in `#include <vector>`, vhodne matrike `cv::Mat`
  ter povezavo s prevedeno knjižnico. Skalarne teme dodatno uporabljajo standardne
  glave, navedene v kodi. Izseki niso samostojni programi in niso bili prevedeni.
- **C:** stari API `CvMat*` / `CvArr*` iz OpenCV 2.4; glavi
  `opencv2/core/core_c.h` in `opencv2/imgproc/imgproc_c.h`. Poskrbi za alokacijo
  navedenih ciljnih matrik in jih po uporabi sprosti s `cvReleaseMat`.
  Skalarni primeri uporabljajo C99. Izseki niso bili prevedeni.
- **Java:** izseki ciljajo povezave OpenCV 2.4; potrebujejo uvoze
  `org.opencv.core.*`, `org.opencv.imgproc.Imgproc`, `java.util.*`, ustrezno
  knjižnico JAR in nativno knjižnico. Pred uporabo OpenCV se pokliče
  `System.loadLibrary(Core.NATIVE_LIBRARY_NAME)`.
  Pri 2.4 so uporabljene konstante robov v `Imgproc`; v novejših izdajah jih
  poišči v `Core`. Izseki niso bili prevedeni ali izvedeni.

Prenosi C/C++/Java imajo končnico `.txt`, ker so učni izseki, ki potrebujejo
okoliški program. Izbira jezika ne zagotavlja samodejnega prevajanja med API-ji.

## Matematične predpostavke

Slike za aritmetiko pretvorimo v float32. Razlika je predznačena; magnitude ne
zamenjujemo z odvodom na sekundo. `filter2D` uporablja korelacijo, zato je smer
asimetričnega jedra pomembna. Kanal A je projektna hevristika, opisana v `MODEL.md`.
Enostavno merilo mm/piksel velja samo ob ustrezni geometriji; modul za meroslovje
v aplikaciji še ni izveden.

Viri za API so povezani pri vsaki temi. `verification.json` navaja izvedeno
preverjanje in njegove omejitve.

## Detection sequences / Zaporedja zaznavanja

The classroom also contains six complete OpenCV 2.4 detection exercises with ordered blocks, mathematics, parameters, failure cases and book/web references. Load an exercise and its synthetic scene directly into the studio. The sequence orchestrator is Python; the four-language examples above describe the original foundation topics. See [sources and verification](../../DETECTION_SEQUENCES.md).
