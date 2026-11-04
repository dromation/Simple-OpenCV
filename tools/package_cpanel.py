"""Create a File Manager ZIP from an explicit allowlist; never include secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(destination, include_worker=True):
    files = {}
    def add(source, name=None):
        source = ROOT/source
        if not source.is_file():
            raise FileNotFoundError(source)
        files[name or source.relative_to(ROOT).as_posix()] = source
    for relative in ('src/simplemotocam', 'docs/opencv-2.4-manuals', 'contrib/presets', 'tools/native_opencv24'):
        for path in (ROOT/relative).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                add(path.relative_to(ROOT))
    for relative in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'docs/opencv-2.4.13.7-manifest.json',
                     'tools/fetch_references.py', 'tools/build_opencv24_linux.py'):
        add(relative)
    for path in (ROOT/'deploy/cpanel').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            add(path.relative_to(ROOT), path.relative_to(ROOT/'deploy/cpanel').as_posix())
    if include_worker:
        folder = '.motocam/backends/opencv24/'
        for name in ('simplemotocam_opencv24','build-info-linux.json','OpenCV-LICENSE.txt','SimpleMotocam-LICENSE.txt','zlib-LICENSE.txt'):
            add(folder+name)
    forbidden = {'hosting.json', '.env', '.git', 'private', '.venv', 'work', 'node_modules'}
    assert all(not forbidden.intersection(Path(name).parts) and not name.endswith('.exe') for name in files)
    manifest = {'format':1, 'edition':'cpanel-wsgi', 'default_backend':'opencv24', 'files':{
        name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(files.items())}}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name,path in sorted(files.items()):
            info = zipfile.ZipInfo(name)
            info.create_system=3
            executable = name.endswith('/simplemotocam_opencv24')
            info.external_attr=((0o100755 if executable else 0o100644)<<16)
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr('PACKAGE-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for name,digest in manifest['files'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix('.zip.sha256').write_text(digest+'  '+destination.name+'\n')
    print(f'{destination}: {len(files)} files, {destination.stat().st_size/1024/1024:.1f} MB; verified hashes and no private data.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist/SimpleMotocam-cPanel.zip')
    parser.add_argument('--without-worker',action='store_true')
    args=parser.parse_args()
    package(args.output,not args.without_worker)
