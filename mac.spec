import os
import subprocess

block_cipher = None

# Should resolve as /opt/homebrew
prefix = subprocess.run(["brew", "--prefix"], capture_output=True, text=True).stdout.strip()

libs = [
	"libpangocairo-1.0.0.dylib",
	"libharfbuzz.0.dylib",
	"libgobject-2.0.0.dylib",
	"libgio-2.0.0.dylib",
]

lib_paths = [(f"{prefix}/lib/{lib}", ".") for lib in libs]

a = Analysis(
	["src/tauon/__main__.py"],
	binaries=[
		*lib_paths,
		(f"{prefix}/Cellar/ffmpeg@5", "."),
	],
	datas=[
		("src/tauon/assets", "assets"),
		("src/tauon/theme", "theme"),
		("src/tauon/templates", "templates"),
	],
	hiddenimports=["sdl2", "pylast"],
	hookspath=["extra/pyinstaller-hooks"],
	hooksconfig={},
	runtime_hooks=[],
	excludes=[],
	win_no_prefer_redirects=False,
	win_private_assemblies=False,
	cipher=block_cipher,
	noarchive=False)

pyz = PYZ(
	a.pure,
	a.zipped_data,
	cipher=block_cipher)

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
	target_arch=None,
	codesign_identity=None,
	entitlements_file=None,
	icon="src/tauon/assets/tau-mac.icns")

coll = COLLECT(
	exe,
	a.binaries,
	a.zipfiles,
	a.datas,
	strip=False,
	upx=True,
	upx_exclude=[],
	name="TauonMusicBox")

app = BUNDLE(
	coll,
	name="TauonMusicBox.app",
	icon="src/tauon/assets/tau-mac.icns",
	bundle_identifier=None,
	info_plist={
		"LSEnvironment": {
			"LANG": "en_US.UTF-8",
			"LC_CTYPE": "en_US.UTF-8",
			# Set DYLD_LIBRARY_PATH to ensure the app can locate dynamic libraries
#			"DYLD_LIBRARY_PATH": f"{prefix}/lib",
			}})

for lib in lib_paths:
	lib_name, _ = lib
	os.system(f'install_name_tool -add_rpath "@executable_path/." "{lib_name}"')
