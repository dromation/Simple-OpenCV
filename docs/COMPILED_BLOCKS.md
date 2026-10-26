# Lastna koda C, C++ in Java

1. Dodaj **Prazen blok · lastna koda** ali odpri **Napiši / uredi kodo** na kartici.
2. Izberi **C**, **C++** ali **Java** in klikni **Vstavi začetno funkcijo**.
3. Spremeni funkcijo in izberi **Uporabi in izvedi kodo**. Napake prevajalnika
   ali programa se prikažejo pod urejevalnikom.
4. Izhodni kanal uporabi v naslednjem bloku: na primer lastna razlika R−G →
   Gauss → prag → filtriranje območij. Operacije OpenCV uporabijo izbrani pogon,
   vključno z glavnim OpenCV 2.4.13.7.

Vsi trije izvajalniki so vključeni v aplikacijo. Potrebujejo lokalni prevajalnik:

| Jezik | Podprta orodja | Pogodba |
| --- | --- | --- |
| C | MSVC s podporo C11 ali GCC/Clang | `void process(const SmContext *ctx, float *out)` |
| C++ | MSVC, G++ ali Clang++ s podporo C++17 | `void process(const SmContext& ctx, float *out)` |
| Java | JDK z ukazoma `javac` in `java`; preverjeno z JDK 11 | metoda `public static float[] process(Map<String,float[]> channels, Params p)` |

Windows samodejno poišče Visual Studio C++ Build Tools prek `vswhere` in uporabi
okolje za x64 brez globalnega spreminjanja PATH. GCC/Clang ter JDK morajo biti
na PATH. Prevladni prevajalnik C/C++ lahko določiš z `SIMPLEMOTOCAM_CC` oziroma
`SIMPLEMOTOCAM_CXX` (pot do programa, brez argumentov). Po namestitvi orodij
ponovno zaženi strežnik. Brez orodij je kodo še vedno mogoče pisati in shraniti
kot izključen osnutek; aplikacija je ne izvede v drugem jeziku.

## C: predznačena barvna razlika

```c
void process(const SmContext *ctx, float *out) {
    const float *r = sm_channel(ctx, "R");
    const float *g = sm_channel(ctx, "G");
    for (int i = 0; i < ctx->rows * ctx->cols; ++i) {
        out[i] = (r[i] - g[i]) * (float)ctx->gain;
    }
}
```

## C++: enak izračun z referenco na kontekst

```cpp
void process(const SmContext& ctx, float *out) {
    const float *r = sm_channel(&ctx, "R");
    const float *g = sm_channel(&ctx, "G");
    for (int i = 0; i < ctx.rows * ctx.cols; ++i) {
        out[i] = (r[i] - g[i]) * static_cast<float>(ctx.gain);
    }
}
```

V C/C++ aplikacija pripravi `SmContext`, pomožno funkcijo `sm_channel`, vhod in
izhod ter `main`. Pišeš funkcijo `process` in poljubne pomožne funkcije, ne
lastnega `main`. `ctx.input` (v C `ctx->input`) je ime kanala iz izbirnika.
`rows`, `cols`, `gain` in `backend` so podatki trenutne sličice. Pri manjkajočem
kanalu `sm_channel` izpiše napako. C++ podpira tudi standardne knjižnice;
vključeni so `<vector>`, `<algorithm>` in `<stdexcept>`.

## Java: metoda v pripravljenem razredu

```java
public static float[] process(Map<String, float[]> channels, Params p) {
    float[] r = channels.get("R");
    float[] g = channels.get("G");
    float[] out = new float[p.rows * p.cols];
    for (int i = 0; i < out.length; ++i) {
        out[i] = (r[i] - g[i]) * (float)p.gain;
    }
    return out;
}
```

Metode se vstavijo v generirani razred `UserBlock`; ne ovijaj jih še v lasten
razred `UserBlock` in ne dodajaj `package` ali `import` vrstic. Na voljo so
`java.util.*`, `java.nio.*` in `java.nio.file.*`; druge razrede lahko nasloviš s
polnim imenom. `p.input`, `p.rows`, `p.cols`, `p.gain`, `p.backend` imajo enak
pomen kot kontekst C/C++. Java uporablja največ 256 MB pomnilnika za kopico.

## Podatki, prevajanje in izvoz

- Kanali so sploščeni float32 po vrsticah: indeks `y * cols + x`. Na voljo so
  RGB, izpeljani A in vsi predhodni kanali. Predznačene vrednosti ostanejo
  predznačene. `gain` je parameter kode, ne ojačanje prikaza.
- Zapiši oziroma vrni natanko H × W končnih vrednosti. C/C++ izhod se pred
  izvajanjem napolni z NaN, zato neizpisani elementi povzročijo vidno napako.
- Prvi izrecni zagon prevede kodo, z omejitvijo 30 sekund. Naslednje sličice
  uporabljajo preveden program. Sprememba vhodnih podatkov, dimenzij ali `gain`
  ne sproži nove gradnje. Sprememba kode ali poti do prevajalnika jo sproži.
  Strežnik hrani največ 32 uspešnih gradenj v začasnem predpomnilniku.
- Časovna omejitev bloka velja za izvajanje prevedenega programa. Vsaka sličica
  dobi svež proces; statične spremenljivke ne hranijo zgodovine med sličicami.
  Napake ne premaknejo zgodovine sličic.
- Shranjeni projekt hrani izvorno kodo in jezik. Izvoz Python vsebuje tudi
  adapterje in kodo; na drugem računalniku potrebuje iste odvisnosti ter ustrezen
  prevajalnik/JDK. Prevedenih programov ne vključi v projekt.

Ti adapterji izvajajo lastne operacije nad kanali. Ne dodajajo neposredne
povezave z vsemi knjižnicami C/C++/Java OpenCV ali samodejnega uvoza učbeniških
programov z `main`. Za operacije OpenCV uporabi naslednje oziroma predhodne
bloke izbranega pogona. Izvajanje lastne kode ima pravice lokalnega uporabnika;
ni varnostni peskovnik. Običajna standardna izhodna sporočila se ne prikazujejo;
ob neuspelem procesu se prikaže diagnostični izhod stderr.
