This directory contains the non-Python code needed for menuinst.

# Windows

`winshortcut.cpp` and `resource.h` are needed to generate a C extension to interact with the Windows API and create the shortcuts.
Compilation happens via `setup.py`.

# MacOS

`osx_launcher.c` will build a script launcher on MacOS.
It will find a shell script next to itself (executable name + `-script`) and launch it with `/bin/sh`.
It only depends on the standard library. It is bundled as part of the `menuinst.data`.
If it changes, recompile using these steps:

1. Install the conda-forger compilers: `conda create -n cf-compilers compilers`.
2. Get oldest 10.9 SDK (Intel) or 11.0 SDK (Apple Silicon) from https://github.com/phracker/MacOSX-SDKs
   and install it to a known location (e.g. `~/opt/`).
3. Compile with:

```bash
SDK_PATH=~/opt/MacOSX11.0.sdk  # replace as appropriate
for target in "x86_64-apple-macos10.9" "arm64-apple-macos11.0"; do
    arch_suffix="${target%%-*}"
    clang src/osx_launcher.c -o menuinst/data/osx_launcher_${arch_suffix} -target $target -isysroot "$SDK_PATH"
done
```

`appkit-launcher` is yet another launcher for macOS that is used to recieve
Apple Events and dispatch them as command line arguments.

```bash
for arch in "x86_64" "arm64"; do
    swift build -c release --arch $arch --package-path ./appkit-launcher
    cp $(swift build -c release --arch $arch --package-path ./appkit-launcher --show-bin-path)/appkit-launcher "../menuinst/data/appkit_launcher_$arch"
done
```
