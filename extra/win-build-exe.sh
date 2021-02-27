#!/bin/bash
rm -rf dist/tauon
pyinstaller --hidden-import 'infi.systray' --hidden-import 'pylast' --hidden-import 'packaging.requirements' --hidden-import 'pkg_resources.py2_warn' tauon.py -w -i icon.ico
cp -r theme dist/tauon/
cp -r assets dist/tauon/
cp -r templates dist/tauon/
cp -r lib dist/tauon/
cp input.txt dist/tauon/
cp TaskbarLib.tlb dist/tauon/
rm -rf dist/tauon/share/icons
rm -rf dist/tauon/share/locale
rm -rf dist/tauon/share/tcl/tzdata
rm -rf dist/tauon/tcl/tzdata
