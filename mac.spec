import os
import subprocess
import certifi
import sys

python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
python_ver_dotless = f"{sys.version_info.major}{sys.version_info.minor}"
block_cipher = None
# default PATH=/usr/bin:/bin:/usr/sbin:/sbin:/Applications/TauonMusicBox.app/Contents/Frameworks

# Should resolve as /opt/homebrew
prefix = subprocess.run(["brew", "--prefix"], capture_output=True, text=True).stdout.strip()

libs = [
	"libpangocairo-1.0.0.dylib",
	"libharfbuzz.0.dylib",
	"libgobject-2.0.0.dylib",
	"libgio-2.0.0.dylib",
	"librsvg-2.2.dylib",
	"libgdk-3.0.dylib",
]

lib_paths = [(f"{prefix}/lib/{lib}", ".") for lib in libs]
phazor_path = f"build/lib.macosx-14.0-arm64-cpython-{python_ver_dotless}/phazor.cpython-{python_ver_dotless}-darwin.so"

a = Analysis(
	["src/tauon/__main__.py"],
	binaries=[
		*lib_paths,
		(phazor_path, "."),
		(f"{prefix}/bin/ffmpeg", "."),
	],
	datas=[
		(certifi.where(), "certifi"),
		("src/tauon/assets", "assets"),
		("src/tauon/locale", "locale"),
		("src/tauon/theme", "theme"),
		("src/tauon/templates", "templates"),
		# This could only have SDL2.framework and SDL2_image.framework to save space...
		(f".venv/lib/python{python_ver}/site-packages/sdl2dll/dll", "sdl2dll/dll"),
#		(f".venv/lib/python{python_ver}/site-packages/sdl2dll/dll/SDL2.framework", "sdl2dll/dll/SDL2.framework"),
#		(f".venv/lib/python{python_ver}/site-packages/sdl2dll/dll/SDL2_image.framework", "sdl2dll/dll/SDL2_image.framework"),
	],
	hiddenimports=[
		"sdl2",
		"phazor",
		"pylast",
		# Zeroconf is hacked until this issue is resolved: https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/840
		"zeroconf._utils.ipaddress",
		"zeroconf._handlers.answers",
	],
	# TODO(Martin): Rsvg hooks are a hack until pyinstaller releases something newer than 6.11.1 - https://github.com/pyinstaller/pyinstaller/releases
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
			}})

for lib in lib_paths:
	lib_name, _ = lib
	os.system(f'install_name_tool -add_rpath "@executable_path/." "{lib_name}"')
	os.system(f'install_name_tool -add_rpath "@executable_path/." "{phazor_path}"')
