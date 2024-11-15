#!/usr/bin/env bash
set -euo pipefail

# Ensure correct cwd, for example: ~/Projects/Tauon
cd "$(dirname "$0")"

export PYTHONPATH=".":"${PYTHONPATH-}"

rm -rf .env build dist ./src/phazor/kissfft/* ./src/phazor/miniaudio/*

_kissfftver=131.1.0
_miniaudiocommit=4a5b74bef029b3592c54b6048650ee5f972c1a48
if [[ ! -e kissfft.tar.gz ]]; then
	curl -L -o kissfft.tar.gz   "https://github.com/mborgerding/kissfft/archive/refs/tags/${_kissfftver}.tar.gz"
fi
if [[ ! -e miniaudio.tar.gz ]]; then
	curl -L -o miniaudio.tar.gz "https://github.com/mackron/miniaudio/archive/${_miniaudiocommit}.tar.gz"
fi

tar --strip-components=1 -xvf kissfft.tar.gz   -C ./src/phazor/kissfft/
tar --strip-components=1 -xvf miniaudio.tar.gz -C ./src/phazor/miniaudio/

python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install build
python -m compile_translations
python -m build --wheel
#python -m installer --destdir=".env" dist/*.whl
pip install --prefix ".env" dist/*.whl --force-reinstall

./extra/tauonmb.sh "$@"
