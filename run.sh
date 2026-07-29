#!/usr/bin/env bash

set -euo pipefail

win_build() {
	cmake -S . -B build/native -G Ninja \
		-DCMAKE_BUILD_TYPE=Release \
		-DCMAKE_PREFIX_PATH=/mingw64 \
		-DPython3_EXECUTABLE="${PWD}/.venv/bin/python" \
		-DTAUON_DEVELOPMENT_BUILD=OFF
	cmake --build build/native --parallel
	.venv/bin/python tools/package_bundle.py \
		--platform windows \
		--native build/native/tauon-native.exe \
		--output dist/package \
		--portable
	echo -e "Packaged to dist/package/TauonMusicBox"
}

python_check() {
	if ! command -v python >/dev/null; then
		echo -e "python executable not found? Is python installed? Debian(-based) distributions may need python-is-python3 installed via apt."
		exit 1
	fi
}

build_native_dev() {
	cmake -S . -B build/native \
		-DCMAKE_BUILD_TYPE=Debug \
		-DPython3_EXECUTABLE="${PWD}/.venv/bin/python" \
		-DTAUON_DEVELOPMENT_BUILD=ON
	cmake --build build/native --parallel
}

dirty_venv_run() {
	python_check
	# Ensure correct cwd, for example: ~/Projects/Tauon
	cd "$(dirname "${0}")"
	export PYTHONPATH=".":"${PYTHONPATH-}"
	source .venv/bin/activate
	build_native_dev
	build/native/tauon-native
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
	python -m tools.i18n.compile_translations
	python -m build --wheel
	pip install --no-deps --force-reinstall dist/*.whl
	build_native_dev
	build/native/tauon-native
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
