# Lokalni prevajalnik učnih navodil / Local documentation translator

Prevajalnik ustvari shranjene prevode razlag, opisov parametrov in besedila ob
matematičnih primerih. Učenci za branje potrebujejo samo brskalnik; model in
Python sta potrebna le pri tvorjenju novih prevodov. Navodila se ne pošiljajo
zunanji storitvi. Prva namestitev prenese model in programske pakete.

## Jeziki

Slovenščina in angleščina ostaneta avtorski besedili. Generirani prevodi:
japonščina, kitajščina (poenostavljena pisava), nemščina, hrvaščina, srbščina,
ruščina, hindi, španščina, arabščina, korejščina, italijanščina, francoščina,
poljščina, švedščina, portugalščina, indonezijščina, tajščina, bengalščina,
nepalščina. Hrvaščina in srbščina imata ločeni izbiri; arabščina uporablja RTL.
`languages.json` določa imena, kode, oblikovanje števil in smer pisanja.
Kitajski model uporablja kodo `zh`, ne ločenega govornega modela za mandarinščino.

## Zakaj M2M100 in CTranslate2

- [M2M100 418M](https://huggingface.co/facebook/m2m100_418M) podpira vse naštete
  jezike in ima licenco MIT. Pripeta izdaja modela:
  `55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636`.
- [CTranslate2](https://opennmt.net/CTranslate2/guides/transformers.html)
  izvaja model lokalno na CPU v obliki int8; njegova licenca je MIT.
- [Argos Translate](https://github.com/argosopentech/argos-translate) in
  [LibreTranslate](https://docs.libretranslate.com/) sta uporabni alternativi,
  vendar je treba preveriti konkretne nameščene jezikovne pare. Ta projekt
  uporablja en model, ki pokrije celoten zahtevani izbor.

To so **strojni osnutki, ki še potrebujejo strokovni in jezikovni pregled**.
Zaščita simbolov ne zagotavlja pravilnega pomena prevoda. Posebej preveri
zanikanje, merske enote, predpostavke in razlage negotovosti. V vodiču je ob
prevodu privzeto razprt angleški izvirnik. Uradni angleški PDF-priročniki se ne
prevajajo; ta postopek pokriva naš učni dodatek z osmimi temami.

## Prva priprava (PowerShell, korenska mapa projekta)

```powershell
python -m venv .venv-translation
.\.venv-translation\Scripts\python.exe -m pip install -r tools/doc_translate/requirements-lock.txt
.\.venv-translation\Scripts\python.exe tools/doc_translate/setup_model.py
.\Update-Learning-Translations.cmd
```

Potrebna sta Python 3.10+ in Node.js za izvoz obstoječega vodiča. Prvi prenos
modela je velik približno 2 GB; pretvorjena kopija, okolje in predpomnilnik
potrebujejo dodaten prostor. Osnovno okolje OpenCV ostane ločeno.
Datoteke `.translation-models/` in `.venv-translation/` so izključene iz Gita.
Pripete različice v `requirements-lock.txt` so bile nameščene na Windows/Python
3.10; za drug sistem je morda potrebna nova preverjena kombinacija različic.

## Posodobitev ob spremembi učne snovi

1. Uredi izvirni slovenski/angleški besedili v `lessons.js` oziroma `TEXT`
   v `app.js`. Nove teme dodaj v isti strukturi; število tem v obstoječem UI
   je za zdaj še nastavljeno na osem.
2. Nove simbole, tehnična imena in cele enačbe v besedilu dodaj v
   `protected.json`. Kodo in polje `formula` izvoz že izloči.
3. Zaženi `Update-Learning-Translations.cmd`. Izvozi izvirnika, prevede
   spremenjene vnose in sestavi `translations.js` za branje brez interneta.
4. Preglej prevedene JSON-datoteke in vodič. `protectedFallbackKeys` označuje
   besedila, kjer je prevajalnik pokvaril nadomestne oznake, zato so bili
   prevedeni posamezni odseki med ohranjenimi izrazi; ti so lahko manj tekoči.
   Odstavki se prevajajo po stavkih, ker je začetni preizkus prevajanja celih
   odstavkov pokazal izpuščanje stavkov. Če model ponavlja besedilo do omejitve
   dolžine, sledi en ponovni poskus z omejenim ponavljanjem; ob ponovnem neuspehu
   se postopek ustavi, namesto da bi objavil odrezan prevod. To še ne zagotavlja
   pomenske pravilnosti.

Predpomnilnik je vezan na besedilo, ciljni jezik, izdajo modela in različico
postopka. Katalog hrani tudi zgoščeno vrednost celotnega izvirnika in slovarja;
sestavljanje zavrne nepopolne ali zastarele prevode. Ob uspešni izdelavi shrani
prevode v `docs/opencv-2.4-manuals/learning/i18n/`. Starih, že naloženih strani
brskalnik ne spremeni: vodič znova naloži.

## Uporaba za druga navodila

Ustvari JSON s ploščatim slovarjem besedil, npr.:

```json
{"strings":{"intro.title":"Camera calibration","intro.text":"Measure the reference length."}}
```

```powershell
.\.venv-translation\Scripts\python.exe tools/doc_translate/translate.py --input work/my-instructions.json --output work/translations --languages ja de ar --no-bundle
```

`--glossary` sprejme lasten JSON z `{"terms":["RGB","L = s * p"]}`.
Zaščitene izraze lahko v besedilu označiš tudi z obratnimi narekovaji.
Vnos naj vsebuje samo razlago; to ni prevajalnik poljubnih datotek Python,
PDF ali Markdown. Dolge odstavke razdeli na krajše stabilno poimenovane vnose.
Po začetni pripravi prevajanje uporablja izključno lokalni model.

## Preverjanje

```powershell
.\.venv-translation\Scripts\python.exe -m unittest discover -s tools/doc_translate -p test_translate.py -v
.\.venv-translation\Scripts\python.exe tools/doc_translate/translate.py --bundle-only
```

Samodejni preizkusi varujejo simbole in zavračajo zastarele/nepopolne kataloge.
Ne ocenjujejo jezikovne kakovosti. Popravke shrani ločeno v
`corrections/<jezik>.json`, ne v generirani katalog. Struktura je
`{"status":"opis pregleda","entries":{"ključ":{"source":"točen angleški izvirnik","translation":"popravljeno besedilo"}}}`.
Sestavljanje te popravke uporabi v brskalniškem paketu in zavrne popravek, če se
je izvirnik spremenil. Regeneracija jih ohrani. Nemški paket vsebuje izrecne
popravke napak, opaženih pri preizkusu, in je še vedno označen kot osnutek.

## English summary

Local, optional M2M100/CTranslate2 tooling translates English prose catalogs.
It excludes lesson code, formula fields and URLs from the extraction step;
protected inline spans are copied exactly. Generated translations are labelled
machine-unreviewed, with English comparison in the guide. The original PDF
manuals remain in English. No translation service or API key is required.
The language registry and flat catalog CLI are reusable for future instructions.

## Studio interface catalogs

`src/simplemotocam/studio_ui/i18n/en.json` and `sl.json` are authored interface catalogs. Run `Update-Studio-Translations.cmd` to translate the other 19 languages locally and rebuild `studio_ui/i18n.js`. Equations and user-entered channel identifiers are never translated. `studio-corrections/` preserves targeted terminology corrections (for example, the software meanings of “save state” and “run”); the bundle rejects stale corrections. These remain machine drafts pending native technical review. No translation model is needed to run the application.
