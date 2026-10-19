#!/usr/bin/env bash

set -euo pipefail

win_build() {
	# Rebuilds the native code and installs Tauon into the venv, then stages a bundle
	CMAKE_PREFIX_PATH="${MSYSTEM_PREFIX}" .venv/bin/python -m pip install --no-deps --force-reinstall .
	.venv/bin/python tools/package_bundle.py \
		--platform windows \
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

# Editable install: Python changes apply on the next launch, native code is
# rebuilt incrementally in build/editable whenever this runs
install_dev() {
	pip install --no-build-isolation -C build-dir=build/editable -e "${@}"
}

dirty_venv_run() {
	python_check
	# Ensure correct cwd, for example: ~/Projects/Tauon
	cd "$(dirname "${0}")"
	source .venv/bin/activate
	install_dev . --no-deps
	.venv/bin/tauon
}

clean_venv_run() {
	python_check
	# Ensure correct cwd, for example: ~/Projects/Tauon
	cd "$(dirname "${0}")"

	rm -rf .venv build dist src/phazor/{kissfft,miniaudio}
	mkdir -p src/phazor/{kissfft,miniaudio}

	_kissfftver=131.1.0
	_miniaudiocommit=9634bedb5b5a2ca38c1ee7108a9358a4e233f14d

	[[ ! -e kissfft.tar.gz ]] && curl -L -o kissfft.tar.gz "https://github.com/mborgerding/kissfft/archive/refs/tags/${_kissfftver}.tar.gz"
	[[ ! -e miniaudio.tar.gz ]] && curl -L -o miniaudio.tar.gz "https://github.com/mackron/miniaudio/archive/${_miniaudiocommit}.tar.gz"

	tar --strip-components=1 -xvf kissfft.tar.gz -C ./src/phazor/kissfft/
	tar --strip-components=1 -xvf miniaudio.tar.gz -C ./src/phazor/miniaudio/

	python -m venv .venv
	source .venv/bin/activate
#	python -m pip install -U pip
	# Necessary for Windows (MSYS2) if compiling things like Pillow
	if [[ -n "${MSYSTEM_PREFIX-}" ]]; then
		export CFLAGS="-I${MSYSTEM_PREFIX}/include"
	fi
	pip install scikit-build-core
	install_dev ".[all,dev]"
	.venv/bin/tauon
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
	"Windows build")

if [[ ${#} -eq 0 ]]; then
	show_menu
else
	process_answer "${1}"
fi
