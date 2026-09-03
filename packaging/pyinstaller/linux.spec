import sys

import certifi
from pathlib import Path

SPEC_DIR = Path(globals().get("SPECPATH", Path.cwd() / "packaging/pyinstaller")).resolve()
REPO_ROOT = SPEC_DIR.parents[1]

python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

ubuntu_x64_lib_path = "/usr/lib/x86_64-linux-gnu"
ubuntu_arm64_lib_path = "/usr/lib/aarch64-linux-gnu"
arch_lib_path = "/usr/lib"
if Path(ubuntu_x64_lib_path).exists():
	lib_path = ubuntu_x64_lib_path
elif Path(ubuntu_arm64_lib_path).exists():
	lib_path = ubuntu_arm64_lib_path
else:
	lib_path = arch_lib_path

a = Analysis(
	[str(REPO_ROOT / "src/tauon/__main__.py")],
	pathex=[],
	binaries=[],
	datas=[
		(certifi.where(), "certifi"),
		(f"{lib_path}/gtk-3.0/modules/libcolorreload-gtk-module.so", "lib/gtk-3.0/modules"),
		(f"{lib_path}/gtk-3.0/modules/libwindow-decorations-gtk-module.so", "lib/gtk-3.0/modules"),
		(f"{lib_path}/gtk-3.0/modules/libcanberra-gtk-module.so", "lib/gtk-3.0/modules"),
		(f"{lib_path}/gtk-3.0/modules/libcanberra-gtk3-module.so", "lib/gtk-3.0/modules"),
		(f"{lib_path}/girepository-1.0/Notify-0.7.typelib", "gi_typelibs"),
		(str(REPO_ROOT / ".venv/lib/python3.14/site-packages/sdl3/bin/libSDL3.so"), "."),
		(str(REPO_ROOT / ".venv/lib/python3.14/site-packages/sdl3/bin/libSDL3_image.so"), "."),
		#(str(REPO_ROOT / ".venv/lib/python3.14/site-packages/sdl3/bin/libSDL3_net.so"), "."),
		#(str(REPO_ROOT / ".venv/lib/python3.14/site-packages/sdl3/bin/libSDL3_ttf.so"), "."),
		#(str(REPO_ROOT / ".venv/lib/python3.14/site-packages/sdl3/bin/libSDL3_rtf.so"), "."),
		#(str(REPO_ROOT / ".venv/lib/python3.14/site-packages/sdl3/bin/libSDL3_mixer.so"), "."),
		(str(REPO_ROOT / "src/tauon/assets"), "assets"),
		(str(REPO_ROOT / "src/tauon/locale"), "locale"),
		(str(REPO_ROOT / "src/tauon/theme"), "theme"),
		(str(REPO_ROOT / "src/tauon/templates"), "templates"),
		(str(REPO_ROOT / "lrclib-solver"), "."),
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
	hookspath=[str(REPO_ROOT / "packaging/pyinstaller/hooks")],
	hooksconfig={},
	runtime_hooks=[],
	excludes=[
		"OpenSSL",
		"cryptography",
	],
	noarchive=False,
	optimize=0,
)
# Remove libpipewire-0.3.so to use the host's PipeWire installation so library and SPA modules match
# without having to weirdly include both and possibly also set SPA_PLUGIN_DIR
a.binaries = [
	entry
	for entry in a.binaries
	if not Path(entry[0]).name.startswith("libpipewire-0.3.so")
]
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
