import sys

import certifi
from pathlib import Path

python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

ubuntu_lib_path="/usr/lib/x86_64-linux-gnu"
arch_lib_path="/usr/lib"
lib_path = ubuntu_lib_path if Path(ubuntu_lib_path).exists() else arch_lib_path

a = Analysis(
	["src/tauon/__main__.py"],
	pathex=[],
	binaries=[],
	datas=[
		(certifi.where(), "certifi"),
		(f"{lib_path}/gtk-3.0/modules/libcolorreload-gtk-module.so",        "lib/gtk-3.0/modules"),
		(f"{lib_path}/gtk-3.0/modules/libwindow-decorations-gtk-module.so", "lib/gtk-3.0/modules"),
		(f"{lib_path}/gtk-3.0/modules/libcanberra-gtk-module.so",           "lib/gtk-3.0/modules"),
		(f"{lib_path}/gtk-3.0/modules/libcanberra-gtk3-module.so",          "lib/gtk-3.0/modules"),
		(f"{lib_path}/girepository-1.0/Notify-0.7.typelib", "gi_typelibs"),
		(".venv/lib/python3.13/site-packages/sdl3/bin/libSDL3.so",       "."),
		(".venv/lib/python3.13/site-packages/sdl3/bin/libSDL3_image.so", "."),
		#(".venv/lib/python3.13/site-packages/sdl3/bin/libSDL3_net.so",   "."),
		#(".venv/lib/python3.13/site-packages/sdl3/bin/libSDL3_ttf.so",   "."),
		#(".venv/lib/python3.13/site-packages/sdl3/bin/libSDL3_rtf.so",   "."),
		#(".venv/lib/python3.13/site-packages/sdl3/bin/libSDL3_mixer.so", "."),
		("src/tauon/assets", "assets"),
		("src/tauon/locale", "locale"),
		("src/tauon/theme", "theme"),
		("src/tauon/templates", "templates"),
		("lrclib-solver", "."),
	],
	hiddenimports=[
		"pylast",
		"phazor",
		"phazor-pw",
		# Zeroconf is hacked until this issue is resolved: https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/840
		"zeroconf._utils.ipaddress",
		"zeroconf._handlers.answers",
		"OpenGL.platform.egl",
	],
	hookspath=["extra/pyinstaller-hooks"],
	hooksconfig={},
	runtime_hooks=[],
	excludes=[],
	noarchive=False,
	optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
	pyz,
	a.scripts,
	[],
	exclude_binaries=True,
	name="Tauon Music Box",
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	console=False,
	disable_windowed_traceback=False,
	argv_emulation=False,
	target_arch=None,
	codesign_identity=None,
	entitlements_file=None,
)
coll = COLLECT(
	exe,
	a.binaries,
	a.datas,
	strip=False,
	upx=True,
	upx_exclude=[],
	name="TauonMusicBox",
)
