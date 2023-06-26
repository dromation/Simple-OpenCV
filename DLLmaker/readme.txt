Write the source code for your function or library and save it in a file with a .cpp extension.
Compile the source code into an object file (.obj) using a C++ compiler like Visual Studio or GCC.
Link the object file with a DLL export definition file (.def) using a linker like Visual Studio or GCC.
Create the DLL file by running the linker with appropriate options and settings.

Open Visual Studio and create a new C++ project.
Choose "DLL" as the project type and "Empty Project" as the project template.
Add "mylib.cpp" to the project by right-clicking the project in the Solution Explorer, choosing "Add" > "Existing Item", and selecting "mylib.cpp".
Build the project by choosing "Build" > "Build Solution" from the main menu.
The resulting DLL file will be located in the "Debug" or "Release" subdirectory of your project directory, depending on your build settings.