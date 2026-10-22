# OpenCV 2.4 za pregled in eksperimente

Prenesena je celotna izvorna koda uradne izdaje **2.4.13.7**:

- Mapa: `D:\Dromation\org\apps\betas\SimpleMotocam\external\opencv-2.4.13.7`
- Izvor: https://github.com/opencv/opencv/tree/2.4.13.7
- Commit: `51cfa519249c89d24035b3f96315ad997deb300f`
- Obseg: 4209 datotek, 201.195.756 bajtov (približno 192 MiB).
- Uvoz: 2026-10-21. Vse datoteke so preverjene proti izvornim objektom Git;
  seznam SHA-256 je v `docs/opencv-2.4.13.7-manifest.json`.
- Ohranjeni so `LICENSE` ter licence priloženih knjižnic v izvornih mapah.
- Iz te izvorne kode lahko zgradimo ločen pogon za dejansko obdelavo v OpenCV 2.4; ne zamenja paketa v `.venv`. Glej [namestitev pogonov](OPENCV_BACKENDS.md).

## Kje začeti

Poti v tabeli so relativne glede na mapo `external/opencv-2.4.13.7/`.

| Namen | Izvorna datoteka ali mapa |
| --- | --- |
| Razcep, združevanje in prevezovanje kanalov: split, merge, mixChannels | `modules/core/src/convert.cpp` |
| Odštevanje, absolutna razlika in druga aritmetika | `modules/core/src/arithm.cpp` |
| Barvne pretvorbe | `modules/imgproc/src/color.cpp` |
| Sobel in Scharr | `modules/imgproc/src/deriv.cpp` |
| Canny | `modules/imgproc/src/canny.cpp` |
| Filtriranje s poljubnimi jedri | `modules/imgproc/src/filter.cpp` |
| GaussianBlur in glajenje | `modules/imgproc/src/smooth.cpp` |
| Zajem slike in videa | `modules/highgui/src/` |
| Kalibracija in geometrija | `modules/calib3d/` |
| Python povezave stare izdaje | `modules/python/src2/` |
| Primeri in izvorna dokumentacija | `samples/`, `doc/` |

Dokumentacija izdaje: https://docs.opencv.org/2.4.13.7/index.html

Za učence so uradni PDF-priročniki preneseni v `docs/opencv-2.4-manuals/`.
Začnite s slovenskim uvodom `docs/opencv-2.4-manuals/README.md`; v isti mapi so
učbenik z vajami, uporabniški vodič in referenčni priročnik za branje brez spleta.

Ta posnetek omogoča pregled starih implementacij ob novih modulih v
`src/simplemotocam/`. Ni bil samodejno povezan s starimi skriptami SimpleCV;
njihov zagon zahteva posebej pripravljeno združljivo okolje.
