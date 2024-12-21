def find_msys64_path():
	"""Check common paths for MSYS2 installations"""
	potential_paths = [
		"C:\\msys64",
		"D:\\a\\_temp\\msys64",
	]
	for path in potential_paths:
		if os.path.exists(path):
			return path
	raise FileNotFoundError("MSYS2 base path not found in common locations")

msys64_path = find_msys64_path()

a = Analysis(
	["src/tauon/__main__.py"],
	pathex=[],
	binaries=[
		(os.path.join(msys64_path, "\\mingw64\\bin\\libFLAC.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libmpg123-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libogg-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libopenmpt-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libopus-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libopusfile-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libsamplerate-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libvorbis-0.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libvorbisfile-3.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libwavpack-1.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\SDL2.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\SDL2_image.dll"), "."),
		(os.path.join(msys64_path, "\\mingw64\\bin\\libgme.dll"), "."),
	],
	datas=[],
	hiddenimports=[
		"infi.systray",
		"pylast",
		"tekore",
		"phazor",
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
	icon=["src/tauon/assets/icon.ico"],
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
