#!/bin/bash
rm -rf dist/tauon
pyinstaller --hidden-import 'infi.systray' --hidden-import 'pylast' --add-binary 'C:\msys64\mingw64\lib\girepository-1.0\Rsvg-2.0.typelib;gi_typelibs' --add-binary 'lib/libphazor.so;lib' --add-binary 'C:\msys64\mingw64\bin\libao-4.dll;.' --add-binary 'C:\msys64\mingw64\bin\libFLAC.dll;.' --add-binary 'C:\msys64\mingw64\bin\libmpg123-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libogg-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libopenmpt-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libopus-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libopusfile-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libsamplerate-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libssp-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libvorbis-0.dll;.' --add-binary 'C:\msys64\mingw64\bin\libvorbisfile-3.dll;.' --add-binary 'C:\msys64\mingw64\bin\libwavpack-1.dll;.' --add-binary 'C:\msys64\mingw64\bin\SDL2.dll;.' --add-binary 'C:\msys64\mingw64\bin\SDL2_image.dll;.' --hidden-import 'packaging.requirements' --hidden-import 'pkg_resources.py2_warn' tauon.py -w -i assets/icon.ico
cp -r theme dist/tauon/
cp -r assets dist/tauon/
cp -r templates dist/tauon/
cp -r lib dist/tauon/
cp input.txt dist/tauon/
rm -rf dist/tauon/share/icons
rm -rf dist/tauon/share/locale
rm -rf dist/tauon/share/tcl/tzdata
rm -rf dist/tauon/tcl/tzdata
mkdir dist/tauon/etc
cp -r fonts dist/tauon/
cp -r C:/msys64/mingw64/etc/fonts dist/tauon/etc
cp TaskbarLib.tlb dist/tauon/
