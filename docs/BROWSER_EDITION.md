# SimpleOpenCV browser edition

SimpleOpenCV processes images locally in your browser. It includes genuine
OpenCV 2.4.13.7 as the default engine and OpenCV.js 4.13.0 as an optional engine.
A Python server is not required. New workspaces start in English.

## Use the studio

Choose the demonstration, an image, a video or a camera as the input. Camera
access requires browser permission and a secure context (HTTPS or localhost).
Add blocks from the library, adjust their parameters and inspect the results.
The classroom opens inside the studio and explains the algorithms and mathematics.

Save useful configurations as projects and export JSON backups. Projects and
media are stored in this browser at the application's origin. Export and import
JSON to transfer a project, then reselect its media on the destination device.

The **Download app** button offers standalone launchers for Windows, Linux and
macOS. See [desktop startup instructions](PORTABLE.md).

## Engines and custom code

The OpenCV 2.4 WebAssembly build exposes the core/imgproc operations used by the
studio's blocks. It does not expose every upstream OpenCV module. The browser
handles camera and video capture. Switching engines clears temporal history.

Custom JavaScript blocks run in a Worker after Apply / Run. Use only code you
trust: the execution timeout prevents an unresponsive interface, but is not a
security sandbox. Python/C/C++/Java blocks can be retained as disabled drafts;
executing them requires the separately configured developer/server edition.

RGB, per-channel differences and synthetic channel algebra are available in
both engines. The A channel is a derived confidence weight, not a physical
camera measurement. Numerical results can differ slightly between engine versions.

## About and licenses

The About panel describes the project's experimental origins and links to the
bundled licenses. SimpleOpenCV project code is MIT licensed; OpenCV and other
included components retain their own licenses. See [third-party notices](../THIRD_PARTY_NOTICES.md).
