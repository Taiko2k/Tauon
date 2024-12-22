from pathlib import Path


def find_msys64_path() -> Path:
	"""Check common paths for MSYS2 installations"""
	potential_paths = [
		# This is the path the GitHub CI msys action uses
		Path("D:\\a\\_temp\\msys64"),
		# This is default Windows path
		Path("C:\\msys64"),
	]
	for path in potential_paths:
		if path.exists():
			return path
	raise FileNotFoundError("MSYS2 base path not found in common locations")

msys64_path = find_msys64_path()
print(f"Found msys64 path: {msys64_path}")

a = Analysis(
	["src/tauon/__main__.py"],
	pathex=[],
	binaries=[
		(str(Path(msys64_path) / "mingw64" / "bin" / "libFLAC.dll"),         "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libmpg123-0.dll"),     "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libogg-0.dll"),        "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libopenmpt-0.dll"),    "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libopus-0.dll"),       "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libopusfile-0.dll"),   "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libsamplerate-0.dll"), "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libvorbis-0.dll"),     "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libvorbisfile-3.dll"), "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libwavpack-1.dll"),    "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "SDL2.dll"),            "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "SDL2_image.dll"),      "."),
		(str(Path(msys64_path) / "mingw64" / "bin" / "libgme.dll"),          "."),
	],
	datas=[
		("src/tauon/assets", "assets"),
		("src/tauon/locale", "locale"),
		("src/tauon/theme", "theme"),
		("src/tauon/templates", "templates"),
		# This could only have SDL2.framework and SDL2_image.framework to save space...
		(".venv/lib/python3.12/site-packages/sdl2dll/dll", "sdl2dll/dll"),
	],
	hiddenimports=[
		"pylast",
		"tekore",
		"phazor",
		# Zeroconf is hacked until this issue is resolved: https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/840
		"zeroconf._utils.ipaddress",
		"zeroconf._handlers.answers",
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