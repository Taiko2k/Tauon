a = Analysis(
	["src/tauon/__main__.py"],
	pathex=[],
	binaries=[
		("lib/libphazor.so", "lib"),
		("C:\\msys64\\mingw64\\bin\\libFLAC.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libmpg123-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libogg-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libopenmpt-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libopus-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libopusfile-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libsamplerate-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libvorbis-0.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libvorbisfile-3.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libwavpack-1.dll", "."),
		("C:\\msys64\\mingw64\\bin\\SDL2.dll", "."),
		("C:\\msys64\\mingw64\\bin\\SDL2_image.dll", "."),
		("C:\\msys64\\mingw64\\bin\\libgme.dll", "."),
	],
	datas=[],
	hiddenimports=[
		"infi.systray",
		"pylast",
		"tekore",
		"pip",
		"packaging.requirements",
		"pkg_resources.py2_warn",
		"requests",
		],
	hookspath=["extra\\pyinstaller-hooks"],
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
	name="__main__",
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
	icon=["assets/icon.ico"],
)
coll = COLLECT(
	exe,
	a.binaries,
	a.datas,
	strip=False,
	upx=True,
	upx_exclude=[],
	name="__main__",
)
