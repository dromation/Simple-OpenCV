"""Build a complete index.html deployment with locally bundled OpenCV.js."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from simplemotocam.studio_catalog import library_catalog
from simplemotocam.studio_engine import KINDS,default_state


def main():
    vendor=ROOT/'deploy/static/vendor'
    provenance=json.loads((vendor/'SOURCE.json').read_text(encoding='utf-8'))
    if hashlib.sha256((vendor/'opencv.js').read_bytes()).hexdigest()!=provenance['sha256']:
        raise RuntimeError('OpenCV.js differs from its pinned checksum')
    output=ROOT/'dist/SimpleMotocam-HTML'
    if output.exists() and any(output.iterdir()) and not (output/'STATIC-EDITION.txt').exists():
        raise RuntimeError('Refusing to overwrite an unrelated output folder')
    output.mkdir(parents=True,exist_ok=True)
    included={}
    def write(relative,data):
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data if isinstance(data,bytes) else data.encode('utf-8'));included[relative]=target
    def copy(source,relative):write(relative,source.read_bytes())
    for relative in ('style.css','app.js'):
        copy(ROOT/'src/simplemotocam/studio_ui'/relative,relative)
    for source in (ROOT/'docs/opencv-2.4-manuals').rglob('*'):
        if source.is_file():copy(source,'manuals/'+source.relative_to(ROOT/'docs/opencv-2.4-manuals').as_posix())
    for source in (ROOT/'deploy/static').rglob('*'):
        if source.is_file():copy(source,source.relative_to(ROOT/'deploy/static').as_posix())
    copy(ROOT/'LICENSE','LICENSE');copy(ROOT/'THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md')
    source=(ROOT/'src/simplemotocam/studio_ui/i18n.js').read_text(encoding='utf-8')
    catalogs=json.loads(source.split('window.STUDIO_I18N = ',1)[1].rstrip(';\n'))
    translations={'sl':'Izvozi JavaScript','en':'Export JavaScript','de':'JavaScript exportieren','fr':'Exporter JavaScript','es':'Exportar JavaScript','it':'Esporta JavaScript','pt':'Exportar JavaScript','hr':'Izvezi JavaScript','sr':'Извези JavaScript','ru':'Экспорт JavaScript','pl':'Eksportuj JavaScript','sv':'Exportera JavaScript','ja':'JavaScript をエクスポート','zh':'导出 JavaScript','ko':'JavaScript 내보내기','hi':'JavaScript निर्यात करें','ar':'تصدير JavaScript','id':'Ekspor JavaScript','th':'ส่งออก JavaScript','bn':'JavaScript রপ্তানি করুন','ne':'JavaScript निर्यात गर्नुहोस्'}
    for locale,item in catalogs.items():
        item['strings']['export']=translations[locale]
        item['strings']['exported']=('JavaScript algoritem je izvožen. Uporabi ga s priloženimi brskalniškimi datotekami.' if locale=='sl' else 'JavaScript algorithm exported. Use it with the included browser runtime files.')
        item['strings']['codeContract']=('JavaScript: process(channels, params, shape) → H × W vrednosti. Drugi jeziki ostanejo osnutki. params.gain je nastavljiv.' if locale=='sl' else 'JavaScript: process(channels, params, shape) → H × W values. Other languages remain drafts. params.gain is adjustable.')
        item['strings']['codeHint']=('Lastna koda se izvede v brskalniškem Workerju po Uporabi / Zaženi. Uporabljaj samo zaupanja vredno kodo. Prazen blok prepusti vhod.' if locale=='sl' else 'Custom code runs in a browser Worker after Apply / Run. Run only code you trust. An empty block passes its input through.')
        item['strings']['browserNotice']=('Brskalniška izdaja · OpenCV.js 4.13.0 · brez strežnika Python · ni OpenCV 2.4' if locale=='sl' else 'Browser edition · OpenCV.js 4.13.0 · no Python server · not OpenCV 2.4')
    write('i18n.js','window.STUDIO_I18N = '+json.dumps(catalogs,ensure_ascii=False)+';\n')
    with tempfile.TemporaryDirectory() as folder:
        catalog=library_catalog(folder)
    catalog['entries']=[e for e in catalog['entries'] if e['type']!='api']
    write('browser-data.js','window.STATIC_DATA = '+json.dumps({'blocks':KINDS,'state':default_state(),'catalog':catalog,'apiFunctions':[]},ensure_ascii=False)+';\n')
    html=(ROOT/'src/simplemotocam/studio_ui/index.html').read_text(encoding='utf-8')
    html=html.replace('<title>','<link rel="icon" href="data:," />\n    <title>',1)
    html=html.replace('<body>','''<body>
    <div id="staticLoading" role="status" style="position:fixed;inset:0;z-index:1000;background:#f5faf9;display:grid;place-content:center;padding:32px;max-width:100vw">
      <h1>SimpleMotocam · HTML</h1><p>Nalagam lokalni pogon OpenCV.js … / Loading browser engine …</p>
      <button id="staticReset" hidden>Reset current workspace (keep saved projects)</button>
      <noscript>Za uporabo omogoči JavaScript. / Enable JavaScript to use this application.</noscript>
    </div>''')
    html=html.replace('<div class="toolbar">','<div class="toolbar" style="flex-wrap:wrap"><small data-i18n="browserNotice" style="flex-basis:100%"></small>')
    html=html.replace('accept=".png,.jpg,.jpeg,.bmp,.webp,.avi,.mp4,.mov,.mkv"','accept=".png,.jpg,.jpeg,.bmp,.webp,.avi,.mp4,.webm,.mov,.mkv"')
    html=html.replace('<script src="app.js"></script>','<script src="browser-data.js"></script>\n    <script src="browser-engine.js"></script>\n    <script src="browser-studio.js"></script>\n    <script src="app.js"></script>')
    write('index.html',html)
    write('STATIC-EDITION.txt','SimpleMotocam static HTML edition. Upload ALL files into the addon domain document root. No Python, Passenger or /api server. Open via HTTPS, not file://. OpenCV.js 4.13.0.\n')
    manifest={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(included.items())}
    write('PACKAGE-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    archive=ROOT/'dist/SimpleMotocam-HTML.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as package:
        for name,path in included.items():package.write(path,name)
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert not any(name.endswith(('.py','.exe','.sqlite3')) for name in package.namelist())
    archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    print(f'{archive}: {len(included)} files, {archive.stat().st_size/1024/1024:.1f} MB. index.html is at the ZIP root.')


if __name__=='__main__':main()
