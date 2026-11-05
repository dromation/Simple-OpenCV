# SimpleOpenCV — third-party licenses and attribution

SimpleOpenCV was previously called SimpleMotocam. Project-authored application
code, explanations and synthetic teaching scenes are MIT licensed: see [LICENSE](LICENSE).
The original 2023 Dromation attribution and 2026 mech-id-x/contributor attribution
are retained. Renaming the application does not relicense third-party materials.

Open **About → Licenses and attribution** in the application for the project
story and complete offline license texts. Original notice files and their sources
and SHA-256 hashes are in [the notice manifest](docs/licenses/simpleopencv/manifest.json).
Notices are reproduced unchanged; the HTML display escapes markup only.

## Components in the HTML / WebAssembly edition

| Component | Terms and original text |
| --- | --- |
| OpenCV 2.4.13.7, primary engine | [3-clause BSD notice](docs/licenses/simpleopencv/browser/OpenCV-2.4.13.7.txt); source commit `51cfa519249c89d24035b3f96315ad997deb300f`, core/imgproc operations. |
| OpenCV.js 4.13.0, optional engine | [Apache-2.0](docs/licenses/simpleopencv/browser/OpenCV-4.13.0.txt); official single-file browser build, identified by its pinned checksum in `deploy/static/vendor/SOURCE.json`. |
| zlib 1.2.7 / 1.3.1 | [2.4 build notice](docs/licenses/simpleopencv/browser/zlib-1.2.7.txt), [4.13 build notice](docs/licenses/simpleopencv/browser/zlib-1.3.1.txt). |
| Protobuf 3.19.1 | [Original notice](docs/licenses/simpleopencv/browser/Protobuf-3.19.1.txt), reported by the OpenCV 4.13 build. |
| FlatBuffers 25.9.23 | [Apache-2.0 text](docs/licenses/simpleopencv/browser/FlatBuffers-25.9.23.txt), reported by the OpenCV 4.13 build. |
| FLANN and SoftFloat source components | [FLANN notice](docs/licenses/simpleopencv/browser/FLANN.txt), [SoftFloat notice](docs/licenses/simpleopencv/browser/SoftFloat.txt), retained from the corresponding OpenCV 4.13 source. |
| Emscripten and C/C++ runtime notices | [MIT/UIUC](docs/licenses/simpleopencv/browser/Emscripten.txt), [musl](docs/licenses/simpleopencv/browser/musl.txt), [libc++](docs/licenses/simpleopencv/browser/libcxx.txt), [libc++abi](docs/licenses/simpleopencv/browser/libcxxabi.txt), [compiler-rt](docs/licenses/simpleopencv/browser/compiler-rt.txt). The 2.4 engine uses Emscripten 3.1.74; this is not a claim about the compiler SDK version of the prebuilt 4.13 engine. |

The actual 4.13 binary's [build inventory](docs/licenses/simpleopencv/browser/OpenCV-4.13-build-information.txt)
records its included modules and reported dependencies. Browser capture/decoding
uses browser APIs, not a bundled FFmpeg server. The application includes no
frontend CDN, analytics or runtime translation service.

## Desktop environment and optional translation tools

The downloadable portable launchers embed the Go 1.27.3 runtime. Its original
[BSD license](docs/licenses/simpleopencv/portable/Go-1.27.3-LICENSE.txt) and
[patent grant](docs/licenses/simpleopencv/portable/Go-1.27.3-PATENTS.txt) are included.
Go itself does not need to be installed by application users. This launcher is
separate from the optional Python developer environment described below.

The notice collection also records the installed NumPy 2.2.6 and opencv-python
4.14.0.94 wheel licenses, including their supplied third-party notices. These
Python libraries are **not shipped in the HTML ZIP**. Different installed versions
or platforms have their own accompanying license files.

Optional translation tooling includes CTranslate2 4.8.3, Transformers 4.57.6,
PyTorch 2.14.1, SentencePiece 0.2.2, safetensors 0.8.0, tokenizers 0.22.2 and
huggingface-hub 0.36.2. The manifest links their collected license texts, including
the third-party notices shipped with the installed PyTorch wheel. The M2M100 model
is identified as MIT by its [official model card](https://huggingface.co/facebook/m2m100_418M);
the upstream fairseq MIT notice is included for reference. Model weights and these
tool libraries are **not included in the HTML application**. Their license texts
are supplied to document the project's development tools, not to imply that every
listed dependency is executed by the browser. See `tools/doc_translate/README.md`.

## Manuals, books, examples and project history

Official OpenCV 2.4 PDF manuals remain unchanged with their original notices;
their download sources and checksums are in `docs/opencv-2.4-manuals/sources.json`.
Project-authored mathematical explanations, detection sequences and synthetic
images are separate MIT materials. Howse and Trucco–Verri books are cited as
references; their PDFs, scans and full listings are not redistributed.

Historical snapshots of `mech-id-x/ComputerVision-MachineVision` and
`SI_Eksperimenti_Strojnega_Vida` had no license at the recorded revisions. They
are linked and inventoried as references; the application MIT license does not
automatically cover that historical material. See `external/README.md` and the
source manifests before reusing individual external examples.

SimpleCV is credited as inspiration for the author's channel experiments. The
SimpleCV library is not bundled. SimpleOpenCV is not an official or endorsed
distribution of SimpleCV or OpenCV. Third-party names identify their respective
projects; this application does not claim their authorship.
