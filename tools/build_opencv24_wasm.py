"""Build genuine OpenCV 2.4.13.7 core/imgproc for static hosting (Linux/WSL).

Activate Emscripten 3.1.74 first; CMake 3.x and make are required. No system install.
The original pinned source is verified and never modified. Output is a single JS
file containing WebAssembly, so ordinary addon-domain hosting needs no WASM MIME
configuration, cross-origin isolation headers or Python server.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path,default=ROOT/'work/opencv24-wasm-build')
    parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args()
    if os.name=='nt':parser.error('Run inside Linux/WSL with the emsdk environment activated.')
    if not 1<=args.jobs<=16:parser.error('--jobs must be between 1 and 16')
    version=subprocess.check_output(['emcc','--version'],text=True).splitlines()[0]
    if '3.1.74' not in version:raise RuntimeError('Use pinned Emscripten 3.1.74: '+version)
    source=ROOT/'external/opencv-2.4.13.7'
    manifest=json.loads((ROOT/'docs/opencv-2.4.13.7-manifest.json').read_text())
    for item in manifest['files']:
        path=source/item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise RuntimeError('Pinned source verification failed: '+item['path'])
    build=args.build_dir.resolve();build.mkdir(parents=True,exist_ok=True)
    destination=ROOT/'deploy/static/vendor/opencv24';destination.mkdir(parents=True,exist_ok=True)
    flags=['-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DBUILD_ZLIB=ON',
           '-DBUILD_TESTS=OFF','-DBUILD_PERF_TESTS=OFF','-DBUILD_EXAMPLES=OFF',
           '-DBUILD_DOCS=OFF','-DBUILD_opencv_apps=OFF',
           '-DCMAKE_CXX_FLAGS=-std=c++11 -sDISABLE_EXCEPTION_CATCHING=0 -Wno-error=narrowing',
           '-DCMAKE_C_FLAGS=-sDISABLE_EXCEPTION_CATCHING=0']
    options=(source/'CMakeLists.txt').read_text()
    flags+=['-D'+name+'=OFF' for name in sorted(set(re.findall(r'OCV_OPTION\(((?:WITH_|ENABLE_)\w+)',options)))]
    flags+=['-DBUILD_opencv_'+p.name+'='+('ON' if p.name in ('core','imgproc') else 'OFF') for p in sorted((source/'modules').iterdir()) if p.is_dir()]
    commands=[['emcmake','cmake','-S',str(source),'-B',str(build),*flags],
              ['cmake','--build',str(build),'--target','opencv_core','opencv_imgproc','--parallel',str(args.jobs)],
              ['em++','-O3','-std=c++11','-sDISABLE_EXCEPTION_CATCHING=0',
               '-I'+str(source/'modules/core/include'),'-I'+str(source/'modules/imgproc/include'),'-I'+str(build),
               str(ROOT/'tools/native_opencv24/wasm.cpp'),str(build/'lib/libopencv_imgproc.a'),
               str(build/'lib/libopencv_core.a'),str(build/'3rdparty/lib/libzlib.a'),
               '-sMODULARIZE=1','-sEXPORT_NAME=OpenCV24Module','-sSINGLE_FILE=1',
               '-sALLOW_MEMORY_GROWTH=1','-sMAXIMUM_MEMORY=536870912','-sSTACK_SIZE=5242880',
               '-sENVIRONMENT=worker,node','-sEXPORTED_FUNCTIONS=["_sm_version","_sm_error","_sm_process","_malloc","_free"]',
               '-sEXPORTED_RUNTIME_METHODS=["UTF8ToString","stringToUTF8","lengthBytesUTF8"]',
               '-o',str(build/'opencv24.js')]]
    with (build/'build.log').open('w') as log:
        for command in commands:
            print('OpenCV 2.4 WASM: '+command[0],flush=True)
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
            log.flush()
            if result.returncode:raise RuntimeError('Build failed; inspect '+str(build/'build.log'))
    # Verify the compiled binary's version, not a label in the host application.
    probe='require('+json.dumps(str(build/'opencv24.js'))+')().then(m=>console.log(m.UTF8ToString(m._sm_version())))'
    if subprocess.check_output(['node','-e',probe],text=True).strip()!='2.4.13.7':
        raise RuntimeError('Unexpected compiled engine version')
    shutil.copy2(build/'opencv24.js',destination/'opencv24.js')
    shutil.copy2(source/'LICENSE',destination/'OpenCV-LICENSE.txt')
    shutil.copy2(Path(shutil.which('emcc')).resolve().parent/'LICENSE',destination/'Emscripten-LICENSE.txt')
    zlib=(source/'3rdparty/zlib/zlib.h').read_text()
    (destination/'zlib-LICENSE.txt').write_text(zlib[:zlib.index('*/')+2]+'\n')
    (destination/'SOURCE.json').write_text(json.dumps({
        'version':'2.4.13.7','source':'https://github.com/opencv/opencv/tree/2.4.13.7',
        'commit':manifest['commit'],'emscripten':'3.1.74','modules':['core','imgproc'],
        'sha256':hashlib.sha256((destination/'opencv24.js').read_bytes()).hexdigest(),
        'build':'tools/build_opencv24_wasm.py','license':'BSD-3-Clause',
    },indent=2)+'\n')
    print('Built and verified genuine OpenCV 2.4.13.7 WebAssembly: '+str(destination),flush=True)


if __name__=='__main__':main()
