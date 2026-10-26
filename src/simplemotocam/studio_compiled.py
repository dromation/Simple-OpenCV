"""Local C/C++/Java custom-block adapters; no implicit OpenCV linkage.

Compilation occurs only on explicit execution. A bounded process-local cache
keeps successful builds; data/parameters travel separately for every frame.
"""
import functools
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import threading

import numpy as np

COMPILED_STARTERS = {
    "c": '''void process(const SmContext *ctx, float *out) {
    const float *input = sm_channel(ctx, ctx->input);
    for (int i = 0; i < ctx->rows * ctx->cols; ++i) {
        out[i] = input[i] * (float)ctx->gain;
    }
}
''',
    "cpp": '''void process(const SmContext& ctx, float *out) {
    const float *input = sm_channel(&ctx, ctx.input);
    for (int i = 0; i < ctx.rows * ctx.cols; ++i) {
        out[i] = input[i] * static_cast<float>(ctx.gain);
    }
}
''',
    "java": '''public static float[] process(Map<String, float[]> channels, Params p) {
    float[] input = channels.get(p.input);
    float[] out = new float[p.rows * p.cols];
    for (int i = 0; i < out.length; ++i) {
        out[i] = input[i] * (float)p.gain;
    }
    return out;
}
''',
}


@functools.lru_cache(maxsize=1)
def msvc_environment():
    """Discover VS without logging environment values or changing the host."""
    if os.name != "nt":
        return None
    locator = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    if not locator.is_file():
        return None
    try:
        location = subprocess.check_output(
            [str(locator), "-latest", "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
            text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).strip()
        if not location:
            return None
        setup = Path(location) / "VC/Auxiliary/Build/vcvars64.bat"
        with tempfile.TemporaryDirectory(prefix="motocam-toolchain-") as folder:
            batch = Path(folder) / "environment.cmd"
            batch.write_text('@echo off\ncall "' + str(setup) + '" >nul\nif errorlevel 1 exit /b 1\nset\n', encoding="utf-8")
            output = subprocess.check_output(["cmd.exe", "/d", "/c", str(batch)], text=True,
                errors="replace", timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        env = {key.upper(): value for key, value in os.environ.items()}
        for line in output.splitlines():
            if "=" in line and not line.startswith("="):
                key, value = line.split("=", 1)
                env[key.upper()] = value
        compiler = shutil.which("cl", path=env.get("PATH"))
        return (compiler, env) if compiler else None
    except (OSError, subprocess.SubprocessError):
        return None


def compiled_toolchain(language):
    override = os.environ.get("SIMPLEMOTOCAM_CC" if language == "c" else "SIMPLEMOTOCAM_CXX")
    return _discover_toolchain(language, os.environ.get("PATH", ""), override)


@functools.lru_cache(maxsize=12)
def _discover_toolchain(language, search_path, override):
    # Discovery is independent of frames. A PATH/override change invalidates it;
    # restart after installing new tools into an unchanged PATH.
    if language == "java":
        compiler, runner = shutil.which("javac", path=search_path), shutil.which("java", path=search_path)
        return (compiler, runner, None) if compiler and runner else None
    if language not in ("c", "cpp"):
        return None
    if override:
        compiler = shutil.which(override, path=search_path)
        return (compiler, "native", None) if compiler else None
    for name in (("gcc", "clang", "cl") if language == "c" else ("g++", "clang++", "cl")):
        compiler = shutil.which(name, path=search_path)
        if compiler:
            return compiler, "native", None
    msvc = msvc_environment()
    return (msvc[0], "native", msvc[1]) if msvc else None


C_HEADER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
typedef struct {
    int rows, cols, count;
    double gain;
    const char *input;
    const char *backend;
    char (*names)[32];
    float **planes;
} SmContext;
static const float *sm_channel(const SmContext *ctx, const char *name) {
    for (int i=0; i<ctx->count; ++i) if (!strcmp(ctx->names[i], name)) return ctx->planes[i];
    fprintf(stderr, "Unknown input channel: %s\n", name);
    exit(3);
}
'''
C_MAIN = r'''
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    uint32_t endian=1;
    if (*(unsigned char*)&endian != 1) { fprintf(stderr,"Requires a little-endian host"); return 2; }
    FILE *f=fopen(argv[1],"rb");
    if (!f) return 2;
    uint32_t h[6]; SmContext ctx;
    if (fread(h,4,6,f)!=6 || h[0]!=0x534d4331 || !h[1] || !h[2] || h[3]>64 || h[4]>=h[3]) return 2;
    ctx.rows=(int)h[1]; ctx.cols=(int)h[2]; ctx.count=(int)h[3];
    ctx.backend=h[5] ? "opencv24" : "current";
    if (fread(&ctx.gain,8,1,f)!=1) return 2;
    size_t size=(size_t)ctx.rows * ctx.cols;
    ctx.names=(char (*)[32])calloc(h[3],32);
    ctx.planes=(float**)calloc(h[3],sizeof(float*));
    if (!ctx.names || !ctx.planes) return 2;
    for (int c=0;c<ctx.count;++c) {
        ctx.planes[c]=(float*)malloc(size*sizeof(float));
        if (!ctx.planes[c] || fread(ctx.names[c],1,32,f)!=32 || fread(ctx.planes[c],4,size,f)!=size) return 2;
        ctx.names[c][31]=0;
    }
    fclose(f); ctx.input=ctx.names[h[4]];
    float *out=(float*)malloc(size*sizeof(float));
    if (!out) return 2;
    for (size_t i=0;i<size;++i) out[i]=NAN;
    CALL_USER
    f=fopen(argv[2],"wb");
    if (!f || fwrite(out,4,size,f)!=size) return 2;
    fclose(f); free(out);
    for (int c=0;c<ctx.count;++c) free(ctx.planes[c]);
    free(ctx.planes); free(ctx.names);
    return 0;
}
'''
JAVA_HEADER = r'''
import java.util.*;
import java.nio.*;
import java.nio.file.*;
public class UserBlock {
    public static final class Params {
        public final int rows, cols;
        public final String input, backend;
        public final double gain;
        Params(int rows,int cols,String input,double gain,String backend) {
            this.rows=rows;this.cols=cols;this.input=input;this.gain=gain;this.backend=backend;
        }
    }
'''
JAVA_MAIN = r'''
    public static void main(String[] args) throws Exception {
        ByteBuffer b=ByteBuffer.wrap(Files.readAllBytes(Paths.get(args[0]))).order(ByteOrder.LITTLE_ENDIAN);
        if(b.getInt()!=0x534d4331) throw new IllegalArgumentException("Invalid channel packet");
        int rows=b.getInt(),cols=b.getInt(),count=b.getInt(),input=b.getInt(),backend=b.getInt();
        double gain=b.getDouble();
        Map<String,float[]> channels=new LinkedHashMap<>();
        String selected=null;
        for(int c=0;c<count;c++) {
            byte[] name=new byte[32];b.get(name);int n=0;while(n<32 && name[n]!=0)n++;
            String key=new String(name,0,n,java.nio.charset.StandardCharsets.US_ASCII);
            if(c==input)selected=key;
            float[] values=new float[rows*cols];for(int i=0;i<values.length;i++)values[i]=b.getFloat();
            channels.put(key,values);
        }
        float[] out=process(channels,new Params(rows,cols,selected,gain,backend!=0?"opencv24":"current"));
        if(out==null || out.length!=rows*cols)throw new IllegalArgumentException("Return H * W values with the input shape");
        ByteBuffer result=ByteBuffer.allocate(out.length*4).order(ByteOrder.LITTLE_ENDIAN);
        for(float v:out)result.putFloat(v);
        Files.write(Paths.get(args[1]),result.array());
    }
}
'''


class CompiledBlock:
    def __init__(self, temporary, command):
        self.temporary = temporary  # Holds the cache directory until eviction/process exit.
        self.command = command


_compile_lock = threading.RLock()


@functools.lru_cache(maxsize=32)
def compile_block(language, code, compiler, runner):
    temporary = tempfile.TemporaryDirectory(prefix="simplemotocam-compiled-")
    root = Path(temporary.name)
    toolchain = compiled_toolchain(language)
    if not toolchain or toolchain[:2] != (compiler, runner):
        raise ValueError("Compiler configuration changed; run the block again")
    env = toolchain[2]
    if language == "java":
        source = root / "UserBlock.java"
        source.write_text(JAVA_HEADER + code + "\n" + JAVA_MAIN, encoding="utf-8")
        command = [compiler, "-encoding", "UTF-8", "-d", str(root), str(source)]
        execute = [runner, "-Xmx256m", "-cp", str(root), "UserBlock"]
    else:
        suffix = "c" if language == "c" else "cpp"
        source = root / ("user_block." + suffix)
        call = "process(&ctx,out);" if language == "c" else 'try {process(ctx,out);} catch(const std::exception& e){fprintf(stderr,"%s",e.what());return 3;}'
        extra = "" if language == "c" else "#include <vector>\n#include <algorithm>\n#include <stdexcept>\n"
        source.write_text(C_HEADER + extra + '\n#line 1 "user_block.' + suffix + '"\n' + code +
                          '\n#line 1 "adapter_main"\n' + C_MAIN.replace("CALL_USER", call), encoding="utf-8")
        binary = root / ("block.exe" if os.name == "nt" else "block")
        if Path(compiler).stem.lower() == "cl":
            command = [compiler, "/nologo", "/O2", "/utf-8", "/std:c11" if language == "c" else "/std:c++17",
                       "/TC" if language == "c" else "/TP", "/EHsc", str(source), "/Fe:" + str(binary), "/Fo:" + str(root / "block.obj")]
        else:
            command = [compiler, "-O2", "-std=c11" if language == "c" else "-std=c++17", str(source), "-o", str(binary), "-lm"]
        execute = [str(binary)]
    try:
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=30,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Compilation exceeded 30 seconds") from exc
    if result.returncode:
        detail = (result.stdout + result.stderr).decode("utf-8", errors="replace")[-5000:]
        raise ValueError(language + " compilation: " + detail)
    return CompiledBlock(temporary, execute)


def run_compiled(language, code, values, params, timeout, backend):
    toolchain = compiled_toolchain(language)
    if not toolchain:
        raise ValueError("Install a compiler/JDK for " + language)
    with _compile_lock:
        program = compile_block(language, code, *toolchain[:2])
    shape = values["R"].shape
    names = list(values)
    with tempfile.TemporaryDirectory(prefix="simplemotocam-compiled-frame-") as folder:
        root = Path(folder)
        packet, output, errors = root / "input.bin", root / "out.bin", root / "error.txt"
        with packet.open("wb") as handle:
            handle.write(struct.pack("<6Id", 0x534d4331, *shape, len(names), names.index(params["input"]),
                                     int(backend == "opencv24"), params["gain"]))
            for name, plane in values.items():
                handle.write(name.encode("ascii").ljust(32, b"\0"))
                handle.write(np.asarray(plane, dtype="<f4").tobytes())
        try:
            with errors.open("wb") as error_stream:
                result = subprocess.run([*program.command, str(packet), str(output)], cwd=root,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=error_stream,
                    timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired as exc:
            raise ValueError(f"Custom {language} block exceeded {timeout:g} s") from exc
        if result.returncode:
            with errors.open("rb") as handle:
                handle.seek(max(0, errors.stat().st_size - 3000))
                detail = handle.read(3000).decode("utf-8", errors="replace")
            raise ValueError(f"Custom {language}: " + (detail or f"worker exit {result.returncode}"))
        if not output.is_file() or output.stat().st_size != int(np.prod(shape)) * 4:
            raise ValueError("Custom block returned an invalid output size")
        plane = np.fromfile(output, dtype="<f4").reshape(shape)
        if not np.isfinite(plane).all():
            raise ValueError("Custom block returned nonfinite or unwritten values")
        return plane
