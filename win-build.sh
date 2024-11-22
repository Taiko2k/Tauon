#!/usr/bin/env bash
set -euo pipefail

rm -rf dist/tauon

pyinstaller \
	--additional-hooks-dir='extra\pyinstaller-hooks' \
	--hidden-import 'infi.systray' \
	--hidden-import 'pylast' \
	--hidden-import 'tekore' \
	--add-binary 'C:\msys64\mingw64\lib\girepository-1.0\Rsvg-2.0.typelib;gi_typelibs' \
	--add-binary 'lib/libphazor.so;lib' \
	--add-binary 'C:\msys64\mingw64\bin\libFLAC.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libmpg123-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libogg-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libopenmpt-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libopus-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libopusfile-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libsamplerate-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libvorbis-0.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libvorbisfile-3.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libwavpack-1.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\SDL2.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\SDL2_image.dll;.' \
	--add-binary 'C:\msys64\mingw64\bin\libgme.dll;.' \
	--hidden-import 'pip' \
	--hidden-import 'packaging.requirements' \
	--hidden-import 'pkg_resources.py2_warn' \
	--hidden-import 'requests' \
	src/tauon/tauon.py \
	-w -i assets/icon.ico

mkdir -p dist/tauon/tekore

#cp C:/msys64/mingw64/lib/python3.13/site-packages/tekore/VERSION dist/tauon/tekore/VERSION

cp -r src/tauon/theme     dist/tauon/
cp -r src/tauon/assets    dist/tauon/
cp -r src/tauon/locale    dist/tauon/
cp -r src/tauon/templates dist/tauon/
cp -r src/tauon/lib       dist/tauon/

rm -rf dist/tauon/share/icons
rm -rf dist/tauon/share/locale
rm -rf dist/tauon/share/tcl/tzdata
rm -rf dist/tauon/tcl/tzdata

mkdir dist/tauon/etc
cp -r fonts dist/tauon/ 2>/dev/null || echo 'Fonts are not present!'
cp -r /mingw64/etc/fonts dist/tauon/etc
cp librespot.exe dist/tauon/
cp TaskbarLib.tlb dist/tauon/ 2>/dev/null || echo 'TLB is not present!'
