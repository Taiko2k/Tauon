import sys

import certifi

python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

a = Analysis(
	["src/tauon/__main__.py"],
	pathex=[],
	binaries=[],
	datas=[
		(certifi.where(), "certifi"),
		("/usr/lib/x86_64-linux-gnu/gtk-3.0/modules/libcolorreload-gtk-module.so", "lib/gtk-3.0/modules"),
		("/usr/lib/x86_64-linux-gnu/gtk-3.0/modules/libwindow-decorations-gtk-module.so", "lib/gtk-3.0/modules"),
		("/usr/lib/x86_64-linux-gnu/gtk-3.0/modules/libcanberra-gtk-module.so", "lib/gtk-3.0/modules"),
		("/usr/lib/x86_64-linux-gnu/gtk-3.0/modules/libcanberra-gtk3-module.so", "lib/gtk-3.0/modules"),
		("src/tauon/assets", "assets"),
		("src/tauon/locale", "locale"),
		("src/tauon/theme", "theme"),
		("src/tauon/templates", "templates"),
	],
	hiddenimports=[
		"pylast",
		"phazor",
		"phazor-pw",
		# Zeroconf is hacked until this issue is resolved: https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/840
		"zeroconf._utils.ipaddress",
		"zeroconf._handlers.answers",
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
