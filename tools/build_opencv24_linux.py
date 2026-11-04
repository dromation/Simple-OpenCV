"""Build the genuine pinned OpenCV 2.4 engine on a Linux hosting/build machine.

Requires Python 3.10+, a C++ compiler, make and CMake 3.20-3.31 (not CMake 4).
No root access, system install or sudo is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cmake', default='cmake')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if os.name == 'nt':
        parser.error('Use this script on Linux; use build_opencv24.py on Windows.')
    if not 1 <= args.jobs <= 16:
        parser.error('--jobs must be between 1 and 16')
    source = ROOT/'external/opencv-2.4.13.7'
    manifest = json.loads((ROOT/'docs/opencv-2.4.13.7-manifest.json').read_text())
    if not source.is_dir():
        raise RuntimeError('Run python tools/fetch_references.py opencv-2.4.13.7 first.')
    for item in manifest['files']:
        path = source/item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('Pinned source verification failed: '+item['path'])
    build = ROOT/'work/opencv24-linux-build'
    worker_build = ROOT/'work/opencv24-linux-worker'
    destination = ROOT/'.motocam/backends/opencv24'
    build.parent.mkdir(exist_ok=True)
    flags = ['-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=OFF', '-DBUILD_ZLIB=ON',
             '-DENABLE_PRECOMPILED_HEADERS=OFF', '-DBUILD_TESTS=OFF', '-DBUILD_PERF_TESTS=OFF',
             '-DBUILD_EXAMPLES=OFF', '-DBUILD_DOCS=OFF', '-DBUILD_opencv_apps=OFF',
             '-DCMAKE_CXX_FLAGS=-std=c++11 -Wno-error=narrowing']
    flags += ['-D'+name+'=OFF' for name in set(re.findall(r'OCV_OPTION\((WITH_\w+)', (source/'CMakeLists.txt').read_text()))]
    flags += ['-DBUILD_opencv_'+p.name+'='+('ON' if p.name in ('core','imgproc') else 'OFF') for p in (source/'modules').iterdir() if p.is_dir()]
    commands = [
        [args.cmake, '-S', str(source), '-B', str(build), *flags],
        [args.cmake, '--build', str(build), '--target', 'opencv_core', 'opencv_imgproc', '--parallel', str(args.jobs)],
        [args.cmake, '-S', str(ROOT/'tools/native_opencv24'), '-B', str(worker_build), '-DCMAKE_BUILD_TYPE=Release', '-DOPENCV24_SOURCE='+str(source), '-DOPENCV24_BUILD='+str(build)],
        [args.cmake, '--build', str(worker_build), '--parallel', str(args.jobs)],
    ]
    log = ROOT/'work/opencv24-linux-build.log'
    with log.open('w') as output:
        for command in commands:
            print('OpenCV 2.4: '+('configure' if '-S' in command else 'compile'), flush=True)
            result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
            output.flush()
            if result.returncode:
                raise RuntimeError('Build failed. Inspect '+str(log))
    worker = worker_build/'simplemotocam_opencv24'
    if subprocess.check_output([str(worker), '--version'], text=True).strip() != '2.4.13.7':
        raise RuntimeError('Wrong worker version')
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(worker, destination/worker.name)
    shutil.copy2(source/'LICENSE', destination/'OpenCV-LICENSE.txt')
    shutil.copy2(ROOT/'LICENSE', destination/'SimpleMotocam-LICENSE.txt')
    zlib = (source/'3rdparty/zlib/zlib.h').read_text()
    (destination/'zlib-LICENSE.txt').write_text(zlib[:zlib.index('*/')+2]+'\n')
    (destination/'build-info-linux.json').write_text(json.dumps({
        'opencv':'2.4.13.7', 'protocol':2, 'source_commit':manifest['commit'],
        'platform':os.uname().sysname+' '+os.uname().machine,
        'worker_sha256':hashlib.sha256(worker.read_bytes()).hexdigest(),
        'modules':['core','imgproc'],
    }, indent=2)+'\n')
    print('Installed genuine OpenCV 2.4.13.7: '+str(destination/worker.name), flush=True)


if __name__ == '__main__':
    main()
