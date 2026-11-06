# SimpleOpenCV desktop downloads

The downloadable applications use a small native Go launcher. It embeds the
complete studio, classroom, licenses and both WebAssembly engines, listens only
on `127.0.0.1:8767` and opens the user's default browser. OpenCV 2.4.13.7 is the
primary engine. No Python, Node.js, Go installation or internet connection is
required to run the extracted application; a modern browser is required.

| Download | Executable | Target |
| --- | --- | --- |
| Windows AMD64 ZIP | `SimpleOpenCV.exe` | Windows 10/11, Intel/AMD x64 |
| Linux AMD64 ZIP | `SimpleOpenCV` | Linux desktop, Intel/AMD x64 |
| Linux ARM64 ZIP | `SimpleOpenCV` | Linux desktop, ARM64 |
| macOS AMD64 ZIP | `SimpleOpenCV.app` | macOS 13+, Intel |
| macOS ARM64 ZIP | `SimpleOpenCV.app` | macOS 13+, Apple Silicon |

Extract before opening. On Linux, preserve the executable bit (or run
`chmod +x SimpleOpenCV` after extraction). Keep the launcher running while using
the application. Use **Quit desktop app** in the footer to stop the server, or
Ctrl+C in the launcher terminal. If automatic browser opening is unavailable,
visit its printed local URL. `--no-browser`, `--port`, `--version` and `--check`
are supported. The binaries are unsigned; macOS bundles are not notarized.

## Project persistence

Projects stay in IndexedDB at the same browser origin. The default port remains
stable between launches. If occupied, the launcher reports the problem rather
than silently selecting another port and appearing to lose projects. A website
and the local application use different browser storage: export/import JSON and
reselect media to transfer a project. Export backups before clearing site data.

This package executes custom JavaScript blocks. Custom Python/C/C++/Java execution
still belongs to the separate developer/server edition with the required runtimes.
No camera is accessed until explicitly selected and permitted.

## Build and distribution

Use Python with the project dependencies and the pinned Go 1.27.3 toolchain:

```sh
python tools/package_static.py
python tools/package_portable.py --go /path/to/go
```

The packager verifies the static asset manifest, runs the Go serving-boundary
tests, cross-compiles with `CGO_ENABLED=0`, creates the five platform ZIPs in
`dist/releases/0.6.0/`, records SHA-256 checksums, and creates
`dist/SimpleOpenCV-Website.zip`. That website ZIP has `index.html` at its root and
includes the downloadable archives behind the **Download app** button. Its size
is larger because it includes all five downloads. The smaller HTML ZIP uses the
GitHub release links instead. Portable executables embed only the app, not the
other platform archives, so there is no recursive packaging.

The launcher only serves embedded files; it has no file-upload or arbitrary
filesystem endpoint. Host checks and an origin/token-protected shutdown endpoint
restrict access. Go runtime LICENSE/PATENTS and upstream engine notices are
included in the offline license collection. Full source stays in this repository.
