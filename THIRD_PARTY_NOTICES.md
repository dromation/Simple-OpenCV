# Third-party material and license boundaries

The new SimpleMotocam application, project-authored lessons and supporting code are MIT licensed. The original Simple-OpenCV MIT notice and Dromation attribution are retained. This license permits use, modification, redistribution and commercial use with the notice, without warranty; it does not relicense third-party material.

| Material | Origin / terms |
| --- | --- |
| OpenCV 4 Python runtime | [OpenCV](https://github.com/opencv/opencv), Apache-2.0 for modern OpenCV; binary wheels include additional dependency notices. See installed `opencv-python` distribution. |
| NumPy | [NumPy](https://github.com/numpy/numpy), BSD-3-Clause and bundled dependency notices. |
| OpenCV 2.4.13.7 source and English manuals | [OpenCV 2.4.13.7](https://github.com/opencv/opencv/tree/2.4.13.7), original BSD-style notices retained in `docs/licenses/OpenCV-2.4-LICENSE.txt`; PDFs remain unmodified. Documentation download URLs and SHA-256 hashes are in `docs/opencv-2.4-manuals/sources.json`. |
| Optional translation model | M2M100 418M, MIT; CTranslate2, MIT; SentencePiece, Apache-2.0. See `docs/opencv-2.4-manuals/learning/MODEL.md` and each upstream package's notices. Model weights are not committed. |
| Legacy external examples | `mech-id-x/ComputerVision-MachineVision` and historical `SI_Eksperimenti_Strojnega_Vida` snapshots had no license file at the recorded revisions. They are linked, inventoried and locally retained as references, not redistributed under an assumed MIT license. |

The `external/README.md` and source manifests record optional local reference snapshots. Large source trees and translation models are excluded from Git. Contributors must check licenses before porting or redistributing external examples.

The studio has no external frontend CDN, analytics or remote translation dependency at runtime. Its screenshots use the project's synthetic demo, not camera recordings.

The optional Windows OpenCV 2.4 worker statically links upstream `core`, `imgproc` and bundled zlib 1.2.7. Its build output includes OpenCV BSD-style, zlib and SimpleMotocam MIT notices plus source revision and binary hash. These dependencies retain their own licenses.

The detection classroom cites locally consulted Howse and Trucco–Verri books and official OpenCV 2.4 tutorials. The explanations, sequence configurations and synthetic test images are project-authored. Book PDFs, scans and listings are not redistributed; their rights remain with their respective holders. Bibliographic page references are recorded in `docs/DETECTION_SEQUENCES.md`.
