"""Build self-contained Windows/Linux/macOS launchers and a cPanel download site.

No external Go modules. Supply Go 1.27.3 with --go; no system installation needed.
Build static HTML first. Each executable embeds only that application, never the
other platform executables. The website ZIP then includes the platform downloads.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.6.0'
TARGETS=[('windows','amd64','Windows · Intel / AMD 64-bit'),('linux','amd64','Linux · Intel / AMD 64-bit'),('linux','arm64','Linux · ARM64'),('darwin','amd64','macOS · Intel'),('darwin','arm64','macOS · Apple Silicon')]

def checksum(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def zip_bytes(archive,name,data,executable=False):
    info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=(0o100755 if executable else 0o100644)<<16
    archive.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--go',default='go');args=parser.parse_args()
    go=str(Path(args.go).resolve()) if Path(args.go).is_file() else args.go
    version=subprocess.check_output([go,'version'],text=True).strip()
    if 'go1.27.3 ' not in version:raise RuntimeError('Use pinned Go 1.27.3; found '+version)
    site=ROOT/'dist/SimpleOpenCV-HTML';manifest=json.loads((site/'PACKAGE-MANIFEST.json').read_text())
    for name,digest in manifest.items():
        if checksum(site/name)!=digest:raise RuntimeError('Static package changed: '+name)
    release=ROOT/'dist/releases'/VERSION;release.mkdir(parents=True,exist_ok=True)
    assets=[];logs=ROOT/'work/portable-build.log';logs.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='simpleopencv-portable-',dir=ROOT/'work') as folder:
        build=Path(folder)
        for source in (ROOT/'tools/portable').glob('*'):
            if source.is_file():shutil.copy2(source,build/source.name)
        for name in [*manifest,'PACKAGE-MANIFEST.json']:
            target=build/'site'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(site/name,target)
        env={**os.environ,'CGO_ENABLED':'0','GOTOOLCHAIN':'local','GOCACHE':str(ROOT/'work/go-build-cache')}
        with logs.open('w') as log:
            subprocess.run([go,'test','./...'],cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            for system,arch,label in TARGETS:
                platform='macos' if system=='darwin' else system
                filename=f'SimpleOpenCV-{VERSION}-{platform}-{arch}.zip'
                binary=build/('SimpleOpenCV.exe' if system=='windows' else 'SimpleOpenCV')
                print('Building '+label,flush=True)
                subprocess.run([go,'build','-trimpath','-ldflags=-s -w -X main.version='+VERSION,'-o',str(binary),'.'],cwd=build,env={**env,'GOOS':system,'GOARCH':arch},stdout=log,stderr=subprocess.STDOUT,check=True)
                target=release/filename
                with zipfile.ZipFile(target,'w') as archive:
                    executable='SimpleOpenCV.exe' if system=='windows' else 'SimpleOpenCV'
                    if system=='darwin':
                        executable='SimpleOpenCV.app/Contents/MacOS/SimpleOpenCV'
                        info={'CFBundleName':'SimpleOpenCV','CFBundleDisplayName':'SimpleOpenCV','CFBundleIdentifier':'org.dromation.simpleopencv','CFBundleExecutable':'SimpleOpenCV','CFBundleVersion':VERSION,'CFBundleShortVersionString':VERSION,'CFBundlePackageType':'APPL','LSMinimumSystemVersion':'13.0','LSUIElement':True}
                        zip_bytes(archive,'SimpleOpenCV.app/Contents/Info.plist',plistlib.dumps(info))
                    zip_bytes(archive,executable,binary.read_bytes(),True)
                    readme=f'''SimpleOpenCV {VERSION} — {label}

Extract the entire ZIP, then open {"SimpleOpenCV.app" if system=="darwin" else executable}.
Linux: run ./SimpleOpenCV (use chmod +x SimpleOpenCV if your extractor loses permissions).
The launcher opens http://127.0.0.1:8767/ in your default browser.
No Python, Node.js or Go installation is required. Keep the launcher running.
Use Quit desktop app in the studio footer (or Ctrl+C in its terminal) to stop.
If the browser does not open, visit the printed local URL yourself.

OpenCV 2.4.13.7 is the default; OpenCV.js 4.13.0 is optional. Image processing
runs in browser WebAssembly. Custom executable blocks use JavaScript here.
Python/C/C++/Java custom compilation belongs to the separate developer edition.
Camera capture requires browser permission. No audio is captured.

Windows: Windows 10/11 x64. macOS: 13+ on the selected CPU. Linux: a modern
64-bit desktop distribution and browser. A current browser with WebAssembly is required.
The executables are unsigned; macOS applications are not notarized.

Projects remain in this browser's storage. Keep the same host and port between
runs. Website and local app storage are separate; transfer projects via JSON
and reselect their media. Closing the launcher does not delete saved projects.

Flags: --version, --check, --no-browser, --port 8767.
The server binds only to 127.0.0.1 and serves embedded application assets.
Licenses and the project history are available in About, offline.
Source: https://github.com/dromation/Simple-OpenCV
'''
                    zip_bytes(archive,'START-HERE.txt',readme.encode())
                    for name in ('LICENSE','THIRD_PARTY_NOTICES.md','about.html'):
                        zip_bytes(archive,name,(site/name).read_bytes())
                    for name in manifest:
                        if name.startswith('licenses/'):zip_bytes(archive,name,(site/name).read_bytes())
                assets.append({'platform':platform,'arch':arch,'label':label,'filename':filename,'size':target.stat().st_size,'sha256':checksum(target),'url':f'https://github.com/dromation/Simple-OpenCV/releases/download/v{VERSION}/{filename}'})
    downloads={'version':VERSION,'assets':assets}
    (release/'manifest.json').write_text(json.dumps(downloads,indent=2)+'\n')
    (release/'SHA256SUMS.txt').write_text(''.join(item['sha256']+'  '+item['filename']+'\n' for item in assets))
    website=ROOT/'dist/SimpleOpenCV-Website';website.mkdir(exist_ok=True)
    if any(website.iterdir()) and not (website/'STATIC-EDITION.txt').exists():raise RuntimeError('Refusing to overwrite unrelated website directory')
    for name in [*manifest,'PACKAGE-MANIFEST.json']:
        target=website/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(site/name,target)
    (website/'downloads').mkdir(exist_ok=True)
    for item in assets:
        shutil.copy2(release/item['filename'],website/'downloads'/item['filename']);item['url']='downloads/'+item['filename']
    (website/'downloads/manifest.json').write_text(json.dumps(downloads,indent=2)+'\n')
    names=sorted(set([*manifest,'downloads/manifest.json',*['downloads/'+i['filename'] for i in assets]]))
    (website/'PACKAGE-MANIFEST.json').write_text(json.dumps({name:checksum(website/name) for name in names},indent=2)+'\n')
    names.append('PACKAGE-MANIFEST.json')
    archive=ROOT/'dist/SimpleOpenCV-Website.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in names:z.write(website/name,name)
    archive.with_suffix('.zip.sha256').write_text(checksum(archive)+'  '+archive.name+'\n')
    print('Prepared 5 executable downloads and '+str(archive),flush=True)

if __name__=='__main__':main()
