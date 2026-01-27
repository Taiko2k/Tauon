#!/usr/bin/env bash

set -euo pipefail

win_build() {
	rm -rf dist/tauon
	# Had to do Windows Security -> Virus & thread protection*2 -> Manage settings -> Windows Real-time protection: off

	pyinstaller --log-level=DEBUG windows.spec

	mkdir -p dist/TauonMusicBox/etc
#	mkdir -p dist/TauonMusicBox/tekore
#	cp C:/msys64/mingw64/lib/python3.13/site-packages/tekore/VERSION dist/tauon/tekore/VERSION
	#mkdir fonts
	#curl -L -o fonts/NotoSans-ExtraCondensed.ttf     https://github.com/notofonts/notofonts.github.io/raw/refs/heads/main/fonts/NotoSans/full/ttf/NotoSans-ExtraCondensed.ttf # 800KB
	#curl -L -o fonts/NotoSans-ExtraCondensedBold.ttf https://github.com/notofonts/notofonts.github.io/raw/refs/heads/main/fonts/NotoSans/full/ttf/NotoSans-ExtraCondensedBold.ttf # 800KB
	#curl -L -o fonts/NotoSans-Bold.ttf               https://github.com/notofonts/notofonts.github.io/raw/refs/heads/main/fonts/NotoSans/full/ttf/NotoSans-Bold.ttf # 800KB
	#curl -L -o fonts/NotoSans-Medium.ttf             https://github.com/notofonts/notofonts.github.io/raw/refs/heads/main/fonts/NotoSans/full/ttf/NotoSans-Medium.ttf # 800KB
	#curl -L -o fonts/NotoSans-Regular.ttf            https://github.com/notofonts/notofonts.github.io/raw/refs/heads/main/fonts/NotoSans/full/ttf/NotoSans-Regular.ttf # 800KB
	#curl -L -o fonts/NotoSansCJKjp-Bold.otf          https://github.com/notofonts/noto-cjk/raw/refs/heads/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf # 16MB
	#curl -L -o fonts/NotoSansCJKjp-Medium.otf        https://github.com/notofonts/noto-cjk/raw/refs/heads/main/Sans/OTF/Japanese/NotoSansCJKjp-Medium.otf # 16MB
	#curl -L -o fonts/NotoSansCJKjp-Regular.otf       https://github.com/notofonts/noto-cjk/raw/refs/heads/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf # 16MB
	rm -rf dist/tauon/share/{icons,locale,tcl/tzdata} dist/TauonMusicBox/tcl/tzdata
	cp -r fonts dist/tauon/ || echo 'fonts directory is not present!'
	cp -r /mingw64/etc/fonts dist/TauonMusicBox/etc # TODO(Martin): Why is this here?
	if [[ -e librespot.exe ]]; then
		cp librespot.exe dist/TauonMusicBox/
	else
		echo 'librespot.exe is not present!'
	fi
	if [[ -e TaskbarLib.tlb ]]; then
		cp TaskbarLib.tlb dist/TauonMusicBox/
	else
		echo 'TaskbarLib.tlb is not present!'
	fi
	echo -e "Packaged to dist/TauonMusicBox"
}

python_check() {
	if ! command -v python >/dev/null; then
		echo -e "python executable not found? Is python installed? Debian(-based) distributions may need python-is-python3 installed via apt."
		exit 1
	fi
}

dirty_venv_run() {
	python_check
	# Ensure correct cwd, for example: ~/Projects/Tauon
	cd "$(dirname "${0}")"
	export PYTHONPATH=".":"${PYTHONPATH-}"
	source .venv/bin/activate
	tauonmb # "${@}" # Passing args is broken atm
}

clean_venv_run() {
	python_check
	# Ensure correct cwd, for example: ~/Projects/Tauon
	cd "$(dirname "${0}")"
	export PYTHONPATH=".":"${PYTHONPATH-}"

	rm -rf .venv build dist tauon_music_box.egg-info src/phazor/{kissfft,miniaudio}
	mkdir -p src/phazor/{kissfft,miniaudio}

	_kissfftver=131.1.0
	_miniaudiocommit=4a5b74bef029b3592c54b6048650ee5f972c1a48

	[[ ! -e kissfft.tar.gz ]] && curl -L -o kissfft.tar.gz "https://github.com/mborgerding/kissfft/archive/refs/tags/${_kissfftver}.tar.gz"
	[[ ! -e miniaudio.tar.gz ]] && curl -L -o miniaudio.tar.gz "https://github.com/mackron/miniaudio/archive/${_miniaudiocommit}.tar.gz"

	tar --strip-components=1 -xvf kissfft.tar.gz -C ./src/phazor/kissfft/
	tar --strip-components=1 -xvf miniaudio.tar.gz -C ./src/phazor/miniaudio/

	python -m venv .venv
	source .venv/bin/activate
#	python -m pip install -U pip
	# Necessary for Windows (MINGW64) if compiling things like Pillow
	export CFLAGS="-I/mingw64/include"
#	export LDFLAGS="-L/mingw64/lib"
	pip install -r requirements.txt -r requirements_devel.txt build
	python -m compile_translations
	python -m build --wheel
	pip install --prefix ".venv" dist/*.whl --force-reinstall
	tauonmb # "${@}" # Passing args is broken atm
}

compile_phazor() {
	outFile="build/libphazor.so"
	python_link_flags=""
	if [[ "$(uname -s)" == "Darwin" ]]; then
		outFile="build/libphazor.dylib"
    # Allow unresolved Py* symbols at link time; they resolve from the host process.
		python_link_flags="-Wl,-undefined,dynamic_lookup"
	fi
	mkdir -p build
	# Homebrew's opusfile installs headers under include/opus/opusfile.h, but the code uses <opus/opusfile.h>.
	# Ensure the parent include dir (the one containing the `opus/` folder) is on the include path.
	opusfile_root_include=""
	if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists opusfile 2>/dev/null; then
		opusfile_incdir="$(pkg-config --variable=includedir opusfile 2>/dev/null || true)"
		if [ -n "${opusfile_incdir}" ]; then
			# `includedir` is typically `<prefix>/include`, which should contain `opus/opusfile.h`.
			opusfile_root_include="-I${opusfile_incdir}"
		fi
	fi
	gcc \
		src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
		${opusfile_root_include} \
		$(pkg-config --cflags --libs python3 samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme) \
		${python_link_flags} \
		-shared -o ${outFile} -fPIC -Wall -O3 -g
	echo "Compiled as ${outFile}!"
}

compile_phazor_pipewire() {
	compile_phazor
	outFile="build/libphazor-pw.so"
	mkdir -p build
	gcc \
		src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
		$(pkg-config --cflags --libs python3 samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme libpipewire-0.3) \
		-shared -o ${outFile} -fPIC -Wall -O3 -g -DPIPE
	echo "Compiled as ${outFile}!"
}

show_menu() {
	PS3="Select a script to run: "
	select yn in "${answer_options[@]}"; do
		process_answer
	done
}

process_answer() {
	if [ -n "${yn-}" ]; then
		answer="${yn},${REPLY}"
	else
		answer="${1}"
	fi
	case "${answer}" in
		"Clean venv run,1" | "1" ) # TODO(Martin): restore ability to pass args if necessary
			clean_venv_run; exit ;;
		"Dirty venv run,2" | "2" )
			dirty_venv_run; exit ;;
		"Windows build,3" | "3" )
			win_build; exit ;;
		"Compile phazor,4" | "4" )
			compile_phazor; exit ;;
		"Compile phazor with PipeWire support,5" | "5" )
			compile_phazor_pipewire; exit ;;
		* )
			echo "Wrong option supplied! Options were: "
			answer_num=1
			for answer in "${answer_options[@]}"; do
				echo "${answer_num}) ${answer}"
				answer_num=$((answer_num + 1))
			done
			exit 1;;
	esac
}

answer_options=(
	"Clean venv run"
	"Dirty venv run"
	"Windows build"
	"Compile phazor"
	"Compile phazor with PipeWire support")

if [[ ${#} -eq 0 ]]; then
	show_menu
else
	process_answer "${1}"
fi
