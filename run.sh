#!/usr/bin/env bash

set -euo pipefail

win_build() {
	rm -rf dist/tauon

	# TODO(Martin): pkg_resources is deprecated, does it still need to be there?
	# https://setuptools.pypa.io/en/latest/pkg_resources.html
	pyinstaller \
		--additional-hooks-dir='extra\pyinstaller-hooks' \
		--hidden-import 'infi.systray' \
		--hidden-import 'pylast' \
		--hidden-import 'tekore' \
		--add-binary 'C:\msys64\mingw64\lib\girepository-1.0\Rsvg-2.0.typelib;gi_typelibs' \
		--add-binary 'lib/libphazor.so;lib' \
		--add-binary 'C:\msys64\mingw64\bin\libFLAC.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libmpg123-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libogg-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libopenmpt-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libopus-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libopusfile-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libsamplerate-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libvorbis-0.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libvorbisfile-3.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libwavpack-1.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\SDL2.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\SDL2_image.dll;.' \
		--add-binary 'C:\msys64\mingw64\bin\libgme.dll;.' \
		--hidden-import 'pip' \
		--hidden-import 'packaging.requirements' \
		--hidden-import 'pkg_resources.py2_warn' \
		--hidden-import 'requests' \
		src/tauon/tauon.py \
		-w -i assets/icon.ico

	mkdir -p dist/tauon/tekore
	mkdir -p dist/tauon/etc

	#cp C:/msys64/mingw64/lib/python3.13/site-packages/tekore/VERSION dist/tauon/tekore/VERSION

	cp -r src/tauon/{theme,assets,locale,templates,lib} dist/tauon/
	rm -rf dist/tauon/share/{icons,locale,tcl/tzdata} dist/tauon/tcl/tzdata
	cp -r fonts dist/tauon/ || echo 'Fonts are not present!'
	cp -r /mingw64/etc/fonts dist/tauon/etc
	cp librespot.exe dist/tauon/
	cp TaskbarLib.tlb dist/tauon/ || echo 'TLB is not present!'
}


clean_venv_run() {
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
	pip install -r requirements.txt -r requirements_optional.txt -r requirements_devel.txt build
	python -m compile_translations
	python -m build --wheel
	pip install --prefix ".venv" dist/*.whl --force-reinstall
	tauonmb # "${@}" # Passing args is broken atm
}


compile_phazor() {
	outFile="build/libphazor.so"
	mkdir -p build
	gcc \
		src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
		$(pkg-config --cflags --libs python3 samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme) \
		-shared -o ${outFile} -fPIC -Wall -O3 -g
	echo "Compiled as ${outFile}!"
}


compile_phazor_pipewire() {
	outFile="build/libphazor-pw.so"
	mkdir -p build
	gcc \
		src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
		$(pkg-config --cflags --libs python3 samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme libpipewire-0.3) \
		-shared -o ${outFile} -fPIC -Wall -O3 -g -DPIPE
	echo "Compiled as ${outFile}!"
}

# Display menu
show_menu() {
	PS3="Select a script to run: "
	select yn in "${answer_options[@]}"; do
		process_answer
	done
}

process_answer() {
	if [[ -v yn ]]; then
		answer="${yn},${REPLY}"
	else
		answer="${1}"
	fi
	case "${answer}" in
		"Clean venv run,1" | "1" ) # TODO(Martin): restore ability to pass args if necessary
			clean_venv_run; exit ;;
		"Windows build,2" | "2" )
			win_build; exit ;;
		"Compile phazor,3" | "3" )
			compile_phazor; exit ;;
		"Compile phazor with PipeWire support,4" | "4" )
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

answer_options=("Clean venv run" "Windows build" "Compile phazor" "Compile phazor with PipeWire support")
if [[ ${#} -eq 0 ]]; then
	show_menu
else
	process_answer "${1}"
fi
