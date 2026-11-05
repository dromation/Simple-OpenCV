"""Build the offline About/licensing page from authored text and verified notices."""
import hashlib
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def build():
    folder=ROOT/'docs/licenses/simpleopencv'
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    groups={}
    for item in manifest:
        path=folder/item['file'];data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise RuntimeError('License checksum mismatch: '+item['file'])
        source=html.escape(item['source'])
        if item['source'].startswith('https://'):source=f'<a href="{source}" target="_blank" rel="noopener">{source}</a>'
        entry=f'<details><summary>{html.escape(item["component"])} · {html.escape(item["file"])}</summary><p>{source}</p><pre>{html.escape(data.decode("utf-8"))}</pre></details>'
        groups.setdefault(item['group'],[]).append(entry)
    parts=[]
    labels={'browser':('Vključeno v HTML / WebAssembly','Included in HTML / WebAssembly'),
            'desktop':('Namizno okolje · ni vključeno v HTML','Desktop environment · not bundled in HTML'),
            'tooling':('Orodja za pripravo prevodov · niso vključena v HTML','Translation build tools · not bundled in HTML'),
            'evidence':('Podatki o prevedenem pogonu','Compiled engine inventory')}
    for key,(sl,en) in labels.items():
        parts.append(f'<h3><span data-lang="sl">{sl}</span><span data-lang="en">{en}</span></h3>'+''.join(groups.get(key,[])))
    project=html.escape((ROOT/'LICENSE').read_text(encoding='utf-8'))
    template='''<!doctype html><html lang="sl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SimpleOpenCV · About &amp; licenses</title>
<style>body{margin:0;background:#f5faf9;color:#203735;font:16px/1.65 system-ui,sans-serif}main{max-width:920px;margin:auto;padding:28px clamp(16px,4vw,48px) 60px}h1{font-size:clamp(28px,5vw,44px);line-height:1.15}h2{margin-top:2em}h3{margin-top:2em}.eyebrow{color:#00877f;letter-spacing:.13em;font-size:12px}.lead{font-size:20px}a{color:#007c75;overflow-wrap:anywhere}.flow,pre{background:#e9f3ef;border:1px solid #cce4db;padding:16px;border-radius:10px;white-space:pre-wrap;overflow-wrap:anywhere}pre{font-size:12px}details{background:white;border:1px solid #d8e5e1;border-radius:10px;margin:10px 0;padding:14px}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}nav{display:flex;gap:20px;flex-wrap:wrap}section{scroll-margin-top:16px}[hidden]{display:none!important}.note{padding:14px;background:#fff6de;border-radius:10px}</style></head><body><main>
<nav><a href="#story"><span data-lang="sl">O aplikaciji</span><span data-lang="en">About</span></a><a href="#licenses"><span data-lang="sl">Licence in avtorstvo</span><span data-lang="en">Licenses and attribution</span></a></nav>
<section id="story"><article data-lang="sl">@@SL@@</article><article data-lang="en">@@EN@@</article></section>
<section id="licenses"><h2><span data-lang="sl">Licence in avtorstvo</span><span data-lang="en">Licenses and attribution</span></h2>
<p data-lang="sl">SimpleOpenCV: MIT. OpenCV 2.4.13.7: BSD s tremi določili. OpenCV 4.13.0: Apache 2.0. Spodaj so izvirna besedila; preimenovanje aplikacije ne spreminja licenc drugih avtorjev.</p>
<p data-lang="en">SimpleOpenCV: MIT. OpenCV 2.4.13.7: 3-clause BSD. OpenCV 4.13.0: Apache 2.0. Original texts follow; renaming the application does not change third-party licensing.</p>
<details><summary>SimpleOpenCV · MIT</summary><pre>@@MIT@@</pre></details>
<p data-lang="sl" class="note">Navedeni namizni paketi in orodja za prevajanje so dokumentirani zaradi razvoja projekta; njihove knjižnice in modeli niso del HTML paketa. Licence za namizne pakete se nanašajo na navedene nameščene različice. Pri drugih različicah preveri njihove priložene licence.</p>
<p data-lang="en" class="note">Desktop packages and translation tools are documented for the project build; their libraries and model weights are not part of the HTML package. Desktop notices describe the specified installed versions. Other versions carry their own notices.</p>
@@LICENSES@@
<h3><span data-lang="sl">Priročniki, knjige in primeri</span><span data-lang="en">Manuals, books and examples</span></h3>
<p data-lang="sl">Priloženi uradni priročniki OpenCV 2.4 ostajajo nespremenjeni in ohranijo svoja obvestila. Razlage, sintetične učne slike in zaporedja tega projekta so avtorsko delo projekta. Knjige Howse in Trucco–Verri so navedene kot literatura; njihovih skenov ali celotnih besedil ne prilagamo. Zgodovinski zbirki zunanjih primerov brez licence na zabeleženem posnetku nista samodejno zajeti z MIT licenco aplikacije. SimpleCV je omenjen kot navdih; njegova knjižnica ni vključena.</p>
<p data-lang="en">Bundled official OpenCV 2.4 manuals remain unchanged with their original notices. Explanations, synthetic teaching images and sequences are project-authored. Howse and Trucco–Verri books are cited as references; their scans and full texts are not bundled. Historical external example snapshots without a license are not automatically covered by the application's MIT license. SimpleCV is credited as inspiration; its library is not bundled.</p>
</section></main><script>
function language(locale){const lang=locale==='sl'?'sl':'en';document.documentElement.lang=lang;document.querySelectorAll('[data-lang]').forEach(e=>e.hidden=e.dataset.lang!==lang);}
language(new URLSearchParams(location.search).get('lang')||'sl');
addEventListener('message',e=>{if(e.source===parent&&e.origin===location.origin&&e.data?.type==='about-locale')language(e.data.locale)});
addEventListener('keydown',e=>{if(e.key==='Escape'&&parent!==self)parent.postMessage({type:'about-close'},location.origin)});
</script></body></html>'''
    for token,value in {'SL':(ROOT/'docs/about/sl.html').read_text(encoding='utf-8'),'EN':(ROOT/'docs/about/en.html').read_text(encoding='utf-8'),'MIT':project,'LICENSES':''.join(parts)}.items():
        template=template.replace('@@'+token+'@@',value)
    (ROOT/'src/simplemotocam/studio_ui/about.html').write_text(template,encoding='utf-8')
    print('Built SimpleOpenCV About page with',len(manifest),'verified notice/evidence files.')

if __name__=='__main__':build()
