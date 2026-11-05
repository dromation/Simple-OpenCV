"""Verify and execute the matching published archive on a native CI runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import urllib.request
import zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tag',default='v0.6.0');args=parser.parse_args()
    if not args.tag.startswith('v') or any(c not in 'v0123456789.-' for c in args.tag):parser.error('Invalid release tag')
    system={'Windows':'windows','Linux':'linux','Darwin':'macos'}[platform.system()]
    arch={'x86_64':'amd64','AMD64':'amd64','aarch64':'arm64','arm64':'arm64'}[platform.machine()]
    base='https://github.com/dromation/Simple-OpenCV/releases/download/'+args.tag+'/'
    manifest=json.load(urllib.request.urlopen(base+'manifest.json'))
    asset=next(a for a in manifest['assets'] if a['platform']==system and a['arch']==arch)
    if '/' in asset['filename'] or '\\' in asset['filename']:raise RuntimeError('Invalid filename')
    with tempfile.TemporaryDirectory(prefix='simpleopencv-release-') as folder:
        root=Path(folder).resolve();archive=root/'download.zip';urllib.request.urlretrieve(base+asset['filename'],archive)
        assert hashlib.sha256(archive.read_bytes()).hexdigest()==asset['sha256']
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                target=(root/item.filename).resolve();assert target.is_relative_to(root)
                z.extract(item,root)
                if os.name!='nt' and not item.is_dir():target.chmod((item.external_attr>>16)&0o777 or 0o644)
        binary=root/('SimpleOpenCV.exe' if system=='windows' else 'SimpleOpenCV.app/Contents/MacOS/SimpleOpenCV' if system=='macos' else 'SimpleOpenCV')
        subprocess.run([str(binary),'--check'],check=True)
        subprocess.run([str(binary),'--version'],check=True)
        process=subprocess.Popen([str(binary),'--no-browser','--port','9877'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        try:
            base='http://127.0.0.1:9877/'
            for _ in range(100):
                try:
                    html=urllib.request.urlopen(base,timeout=1).read().decode();break
                except OSError:
                    if process.poll() is not None:raise RuntimeError(process.stdout.read().decode())
                    time.sleep(.1)
            else:raise RuntimeError('Launcher startup timed out')
            assert 'SimpleOpenCV' in html
            js=urllib.request.urlopen(base+'portable-host.js').read().decode()
            config=json.loads(js.removeprefix('window.SimpleOpenCVHost=').removesuffix(';'))
            assert config['portable'] and config['platform']==('darwin' if system=='macos' else system)+'/'+arch
            request=urllib.request.Request(base+'__simpleopencv/quit',data=b'',method='POST',headers={'Origin':base.rstrip('/'),'X-SimpleOpenCV-Token':config['shutdownToken']})
            assert urllib.request.urlopen(request).status==204
            assert process.wait(timeout=10)==0
            print('PASS published archive:',system,arch,'checksum, embedded assets, native launch, HTTP and clean shutdown')
        finally:
            if process.poll() is None:process.terminate();process.wait(timeout=10)

if __name__=='__main__':main()
